from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="kalender:woche", permanent=False)),
    path("admin/", admin.site.urls),
    path("anmelden/", auth_views.LoginView.as_view(), name="login"),
    path("abmelden/", auth_views.LogoutView.as_view(), name="logout"),
    path("kalender/", include("kalender.urls")),
]
