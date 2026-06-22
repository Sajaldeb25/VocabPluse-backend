from django.urls import path

from .views import (
    CheckoutView,
    MySubscriptionsView,
    PlanListView,
    mock_pay,
    payment_callback,
)

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plan-list"),
    path("subscriptions/", MySubscriptionsView.as_view(), name="my-subscriptions"),
    path("subscriptions/checkout/", CheckoutView.as_view(), name="checkout"),
    path("payments/callback/<str:outcome>/", payment_callback, name="payment-callback"),
    path("payments/mock-pay/", mock_pay, name="mock-pay"),
]
