from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from webapp.core.models import Company, Opportunity, Workspace


class WorkspaceIsolationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="owner", password="test-password")
        self.other_user = user_model.objects.create_user(username="other", password="test-password")
        self.workspace = Workspace.objects.create(name="Owner workspace", owner=self.user)
        self.other_workspace = Workspace.objects.create(name="Other workspace", owner=self.other_user)
        self.company = Company.objects.create(
            workspace=self.workspace,
            name="Example Co",
            website="https://example.com",
        )
        Company.objects.create(
            workspace=self.other_workspace,
            name="Private competitor",
            website="https://private.example",
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_leads_only_show_current_users_workspace(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("leads"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Example Co")
        self.assertNotContains(response, "Private competitor")

    def test_opportunities_are_workspace_scoped(self):
        Opportunity.objects.create(
            workspace=self.workspace,
            company=self.company,
            score=82,
            summary="Missing local landing pages",
        )
        self.client.force_login(self.other_user)
        response = self.client.get(reverse("opportunities"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Missing local landing pages")

    def test_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("login"),
            {"username": "owner", "password": "test-password"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard"))
