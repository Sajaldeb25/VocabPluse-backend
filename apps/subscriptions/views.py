import uuid

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .gateways import sslcommerz_init
from .models import Payment, Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer


class PlanListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        plans = Plan.objects.filter(is_active=True)
        return Response(PlanSerializer(plans, many=True).data)


class MySubscriptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subs = request.user.subscriptions.all()
        return Response(SubscriptionSerializer(subs, many=True).data)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan = get_object_or_404(
            Plan, pk=request.data.get("plan_id"), is_active=True
        )
        subscription = Subscription.objects.create(
            user=request.user, plan=plan, status="pending"
        )
        transaction_id = f"VP-{uuid.uuid4().hex[:16]}"
        payment = Payment.objects.create(
            subscription=subscription,
            gateway="sslcommerz",
            transaction_id=transaction_id,
            amount=plan.price,
            currency=plan.currency,
            status="initiated",
        )

        base = settings.SITE_URL
        result = sslcommerz_init(
            payment,
            success_url=f"{base}/api/payments/callback/success/",
            fail_url=f"{base}/api/payments/callback/fail/",
            cancel_url=f"{base}/api/payments/callback/cancel/",
        )
        if result.get("raw"):
            payment.raw_response = result["raw"]
            payment.save(update_fields=["raw_response"])

        return Response(
            {
                "transaction_id": transaction_id,
                "redirect_url": result.get("redirect_url"),
                "mock": result.get("mock", False),
            },
            status=status.HTTP_201_CREATED,
        )


def _finalise(transaction_id, outcome):
    """Apply a payment outcome and activate the subscription on success."""
    try:
        payment = Payment.objects.select_related("subscription").get(
            transaction_id=transaction_id
        )
    except Payment.DoesNotExist:
        return None

    if outcome == "success":
        payment.status = "success"
        payment.save(update_fields=["status"])
        payment.subscription.activate()
    elif outcome == "fail":
        payment.status = "failed"
        payment.save(update_fields=["status"])
        payment.subscription.status = "cancelled"
        payment.subscription.save(update_fields=["status"])
    elif outcome == "cancel":
        payment.status = "cancelled"
        payment.save(update_fields=["status"])
        payment.subscription.status = "cancelled"
        payment.subscription.save(update_fields=["status"])
    return payment


@api_view(["POST", "GET"])
@permission_classes([AllowAny])
def payment_callback(request, outcome):
    """SSLCommerz callback endpoint (success/fail/cancel)."""
    transaction_id = request.data.get("tran_id") or request.query_params.get("tran_id")
    if not transaction_id:
        return Response({"detail": "tran_id missing."}, status=400)
    payment = _finalise(transaction_id, outcome)
    if payment is None:
        return Response({"detail": "Unknown transaction."}, status=404)
    return Response({"transaction_id": transaction_id, "status": payment.status})


@api_view(["GET"])
@permission_classes([AllowAny])
def mock_pay(request):
    """Dev-only: simulate a successful gateway payment when no credentials set."""
    transaction_id = request.query_params.get("tran_id")
    payment = _finalise(transaction_id, "success") if transaction_id else None
    if payment is None:
        return Response({"detail": "Unknown transaction."}, status=404)
    return Response(
        {
            "transaction_id": transaction_id,
            "status": payment.status,
            "message": "Mock payment completed; subscription activated.",
        }
    )
