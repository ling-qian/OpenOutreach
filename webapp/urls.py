from django.urls import path
from webapp.core import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("leads/", views.leads, name="leads"),
    path("opportunities/", views.opportunities, name="opportunities"),
    path("settings/", views.settings_page, name="settings"),
]
