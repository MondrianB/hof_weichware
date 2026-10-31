from django.urls import path

from . import views

app_name = "kalender"

urlpatterns = [
    path("", views.woche, name="woche"),
    path("anfragen/", views.anfragen, name="anfragen"),
    path("anfragen/<int:pk>/entscheiden/", views.entscheiden, name="entscheiden"),
    path("buchung/neu/", views.buchung_bearbeiten, name="buchung_neu"),
    path("buchung/<int:pk>/", views.buchung_bearbeiten, name="buchung_bearbeiten"),
    path("google-kalender/", views.abos, name="abos"),
    # Öffentlich
    path("anfrage/", views.anfrage, name="anfrage"),
    path("ics/<str:token>/alle.ics", views.ics_alle, name="ics_alle"),
    path("ics/<str:token>/raum-<int:raum_id>.ics", views.ics_raum, name="ics_raum"),
]
