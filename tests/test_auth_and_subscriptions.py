from unittest import mock

from rest_framework.test import APITestCase

from apps.subscriptions.models import Payment, Plan, Subscription
from tests.factories import make_catalog, make_user


class GoogleLoginTests(APITestCase):
    def test_requires_id_token(self):
        res = self.client.post("/api/auth/google/", {})
        self.assertEqual(res.status_code, 400)

    @mock.patch("apps.accounts.views.verify_google_id_token")
    def test_login_creates_user_and_returns_tokens(self, mock_verify):
        mock_verify.return_value = {
            "email": "newuser@gmail.com",
            "name": "New User",
            "sub": "google-sub-123",
        }
        res = self.client.post("/api/auth/google/", {"id_token": "fake"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("access", body)
        self.assertIn("refresh", body)
        self.assertEqual(body["user"]["email"], "newuser@gmail.com")

    @mock.patch("apps.accounts.views.verify_google_id_token")
    def test_invalid_token_rejected(self, mock_verify):
        mock_verify.side_effect = ValueError("bad token")
        res = self.client.post("/api/auth/google/", {"id_token": "fake"})
        self.assertEqual(res.status_code, 401)


class MeViewTests(APITestCase):
    def test_requires_auth(self):
        self.assertEqual(self.client.get("/api/auth/user/").status_code, 401)

    def test_returns_current_user(self):
        user = make_user()
        self.client.force_authenticate(user)
        res = self.client.get("/api/auth/user/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["email"], user.email)
        self.assertFalse(res.json()["has_active_subscription"])


class SubscriptionFlowTests(APITestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name="Pro Monthly", slug="pro-monthly", price="299.00", duration_days=30
        )
        make_catalog()

    def test_plans_public(self):
        res = self.client.get("/api/plans/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)

    def test_checkout_requires_auth(self):
        res = self.client.post("/api/subscriptions/checkout/", {"plan_id": self.plan.id})
        self.assertEqual(res.status_code, 401)

    def test_checkout_and_mock_payment_activates_subscription(self):
        user = make_user()
        self.client.force_authenticate(user)
        checkout = self.client.post(
            "/api/subscriptions/checkout/", {"plan_id": self.plan.id}
        )
        self.assertEqual(checkout.status_code, 201)
        tran_id = checkout.json()["transaction_id"]
        self.assertTrue(checkout.json()["mock"])  # no credentials configured

        self.assertFalse(user.has_active_subscription)

        pay = self.client.get(f"/api/payments/mock-pay/?tran_id={tran_id}")
        self.assertEqual(pay.status_code, 200)
        self.assertEqual(pay.json()["status"], "success")

        user.refresh_from_db()
        self.assertTrue(user.has_active_subscription)
        self.assertEqual(Subscription.objects.get(user=user).status, "active")
        self.assertEqual(Payment.objects.get(transaction_id=tran_id).status, "success")


class ProgressTests(APITestCase):
    def setUp(self):
        self.data = make_catalog()

    def test_progress_requires_auth(self):
        self.assertEqual(self.client.get("/api/progress/").status_code, 401)

    def test_record_progress(self):
        user = make_user()
        self.client.force_authenticate(user)
        word = self.data["easy"]["words"][0]
        res = self.client.post(
            "/api/progress/", {"word": word.id, "status": "learning"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "learning")
        self.assertEqual(res.json()["times_seen"], 1)

        # Posting again increments times_seen.
        res2 = self.client.post(
            "/api/progress/", {"word": word.id, "status": "known"}
        )
        self.assertEqual(res2.json()["times_seen"], 2)
        self.assertEqual(res2.json()["status"], "known")
