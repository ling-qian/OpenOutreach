from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from webapp.core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("leads/", views.leads, name="leads"),
    path("leads/discover/", views.discover_companies, name="discover_companies"),
    path("leads/<int:company_id>/research/", views.research_company, name="research_company"),
    path("leads/<int:company_id>/brief/", views.generate_opportunity_brief, name="generate_opportunity_brief"),
    path("opportunities/", views.opportunities, name="opportunities"),
    path("settings/", views.settings_page, name="settings"),
]
