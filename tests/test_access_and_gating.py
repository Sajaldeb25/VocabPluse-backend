from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.models import SiteSetting
from tests.factories import make_catalog, make_subscriber, make_user


class HealthTests(APITestCase):
    def test_health_ok(self):
        res = self.client.get("/api/health/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")


class CatalogAccessTests(APITestCase):
    def setUp(self):
        self.data = make_catalog()

    def test_anonymous_sees_hard_levels_locked(self):
        res = self.client.get("/api/wordsets/")
        self.assertEqual(res.status_code, 200)
        locked = {row["level"]: row["locked"] for row in res.json()}
        self.assertFalse(locked["easy"])
        self.assertFalse(locked["medium"])
        self.assertTrue(locked["hard"])
        self.assertTrue(locked["advanced"])

    def test_subscriber_sees_all_unlocked(self):
        self.client.force_authenticate(make_subscriber())
        res = self.client.get("/api/wordsets/")
        locked = {row["level"]: row["locked"] for row in res.json()}
        self.assertFalse(any(locked.values()))

    def test_anonymous_cards_easy_ok_hard_forbidden(self):
        easy_set = self.data["easy"]["set"]
        hard_set = self.data["hard"]["set"]
        ok = self.client.get(f"/api/wordsets/{easy_set.id}/cards/")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(len(ok.json()), 2)
        forbidden = self.client.get(f"/api/wordsets/{hard_set.id}/cards/")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

    def test_define_respects_level(self):
        easy_word = self.data["easy"]["words"][0]
        hard_word = self.data["hard"]["words"][0]
        ok = self.client.get(f"/api/words/{easy_word.id}/define/")
        self.assertEqual(ok.status_code, 200)
        self.assertIn("simple_definition", ok.json())
        forbidden = self.client.get(f"/api/words/{hard_word.id}/define/")
        self.assertEqual(forbidden.status_code, 403)


class AIExplanationTests(APITestCase):
    def setUp(self):
        self.data = make_catalog()
        self.settings_obj = SiteSetting.load()
        self.settings_obj.anon_ai_limit = 1
        self.settings_obj.free_ai_limit = 2
        self.settings_obj.save()

    def test_anonymous_demo_word_explain_ok(self):
        demo = self.data["easy"]["words"][0]
        res = self.client.post(f"/api/words/{demo.id}/explain/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("content", res.json())

    def test_anonymous_non_demo_word_requires_login(self):
        medium_word = self.data["medium"]["words"][0]  # browsable but not demo
        res = self.client.post(f"/api/words/{medium_word.id}/explain/")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json().get("reason"), "login_required")

    def test_anonymous_limit_enforced(self):
        first = self.data["easy"]["words"][0]
        second = self.data["easy"]["words"][1]
        ok = self.client.post(f"/api/words/{first.id}/explain/")
        self.assertEqual(ok.status_code, 200)
        # anon_ai_limit is 1, so a second distinct demo word is blocked.
        blocked = self.client.post(f"/api/words/{second.id}/explain/")
        self.assertEqual(blocked.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertEqual(blocked.json().get("reason"), "limit_reached")

    def test_cached_explanation_does_not_recount(self):
        demo = self.data["easy"]["words"][0]
        first = self.client.post(f"/api/words/{demo.id}/explain/")
        self.assertFalse(first.json()["cached"])
        second = self.client.post(f"/api/words/{demo.id}/explain/")
        self.assertTrue(second.json()["cached"])

    def test_free_user_limit_then_blocked(self):
        user = make_user()
        self.client.force_authenticate(user)
        w = self.data
        ids = [
            w["easy"]["words"][0].id,
            w["easy"]["words"][1].id,
            w["medium"]["words"][0].id,
        ]
        self.assertEqual(self.client.post(f"/api/words/{ids[0]}/explain/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/words/{ids[1]}/explain/").status_code, 200)
        # free_ai_limit is 2; third distinct word blocked.
        blocked = self.client.post(f"/api/words/{ids[2]}/explain/")
        self.assertEqual(blocked.status_code, 402)

    def test_subscriber_unlimited(self):
        self.client.force_authenticate(make_subscriber())
        for level in ["easy", "medium", "hard", "advanced"]:
            for word in self.data[level]["words"]:
                res = self.client.post(f"/api/words/{word.id}/explain/")
                self.assertEqual(res.status_code, 200)


class ExampleQuestionTests(APITestCase):
    def setUp(self):
        self.data = make_catalog()

    def test_non_subscriber_blocked(self):
        word = self.data["easy"]["words"][0]
        res = self.client.get(f"/api/words/{word.id}/questions/")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json().get("reason"), "subscription_required")

    def test_subscriber_gets_questions(self):
        self.client.force_authenticate(make_subscriber())
        word = self.data["easy"]["words"][0]
        res = self.client.get(f"/api/words/{word.id}/questions/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
