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
    path("opportunities/", views.opportunities, name="opportunities"),
    path("settings/", views.settings_page, name="settings"),
]
