from django.contrib import admin

from .models import Buchung, Raum


@admin.register(Raum)
class RaumAdmin(admin.ModelAdmin):
    list_display = ["name", "kapazitaet", "aktiv", "reihenfolge"]
    list_editable = ["aktiv", "reihenfolge"]


@admin.register(Buchung)
class BuchungAdmin(admin.ModelAdmin):
    list_display = ["titel", "raum", "art", "beginn", "ende", "status", "kontakt_name"]
    list_filter = ["status", "art", "raum"]
    search_fields = ["titel", "kontakt_name", "kontakt_organisation", "kontakt_email"]
    date_hierarchy = "beginn"
