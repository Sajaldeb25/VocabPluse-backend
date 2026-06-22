"""SSLCommerz payment gateway integration (sandbox-first).

The init call is isolated so it can be mocked in tests. When credentials are
not configured we return a mock redirect URL so local flows still work.
"""
from django.conf import settings


def sslcommerz_init(payment, success_url, fail_url, cancel_url):
    """Initialise an SSLCommerz session and return a gateway redirect URL."""
    store_id = settings.SSLCOMMERZ_STORE_ID
    store_password = settings.SSLCOMMERZ_STORE_PASSWORD

    if not store_id or not store_password:
        # No credentials: return a local mock URL for development.
        return {
            "redirect_url": f"{settings.SITE_URL}/api/payments/mock-pay/?tran_id={payment.transaction_id}",
            "mock": True,
        }

    base = (
        "https://sandbox.sslcommerz.com"
        if settings.SSLCOMMERZ_SANDBOX
        else "https://securepay.sslcommerz.com"
    )
    endpoint = f"{base}/gwprocess/v4/api.php"
    data = {
        "store_id": store_id,
        "store_passwd": store_password,
        "total_amount": str(payment.amount),
        "currency": payment.currency,
        "tran_id": payment.transaction_id,
        "success_url": success_url,
        "fail_url": fail_url,
        "cancel_url": cancel_url,
        "cus_name": payment.subscription.user.full_name or payment.subscription.user.email,
        "cus_email": payment.subscription.user.email,
        "product_name": payment.subscription.plan.name,
        "product_category": "subscription",
        "product_profile": "non-physical-goods",
        "shipping_method": "NO",
    }

    import requests

    response = requests.post(endpoint, data=data, timeout=30)
    payload = response.json()
    return {
        "redirect_url": payload.get("GatewayPageURL", ""),
        "raw": payload,
        "mock": False,
    }
