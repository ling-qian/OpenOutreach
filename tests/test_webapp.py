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

    def test_service_profile_is_workspace_scoped_and_editable(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("settings"),
            {
                "service_name": "Local SEO",
                "service_description": "Improve local search visibility",
                "ideal_customer_description": "Independent clinics in the United States",
                "target_industries": "Healthcare, Dental",
                "target_locations": "United States",
            },
        )
        self.assertEqual(response.status_code, 302)
        from webapp.core.models import ServiceProfile
        profile = ServiceProfile.objects.get(workspace=self.workspace)
        self.assertEqual(profile.service_name, "Local SEO")
        self.assertEqual(profile.target_industries, ["Healthcare", "Dental"])

    def test_research_analyzer_reports_missing_on_page_seo_fields(self):
        from webapp.core.research import analyze_page
        page = {
            "title": "",
            "meta": {},
            "headings": [],
            "text": "Welcome to our business",
            "links": [],
            "forms": 0,
            "images": 0,
            "images_missing_alt": 0,
        }
        categories = {item["category"] for item in analyze_page(page)}
        self.assertIn("seo", categories)
        self.assertIn("local_seo", categories)
        self.assertIn("conversion", categories)
