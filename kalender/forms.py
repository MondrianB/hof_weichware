import datetime

from django import forms
from django.utils import timezone

from .models import Buchung, Raum


class AnfrageForm(forms.Form):
    """Öffentliches Formular für Terminanfragen von Außenstehenden."""

    raum = forms.ModelChoiceField(queryset=Raum.objects.filter(aktiv=True), empty_label=None)
    datum = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    von = forms.TimeField(label="Von (Uhrzeit)", widget=forms.TimeInput(attrs={"type": "time"}))
    bis = forms.TimeField(label="Bis (Uhrzeit)", widget=forms.TimeInput(attrs={"type": "time"}))
    titel = forms.CharField(label="Anlass / Veranstaltung", max_length=200)
    art = forms.ChoiceField(
        label="Art",
        choices=[c for c in Buchung.Art.choices if c[0] != Buchung.Art.INTERN],
    )
    kontakt_name = forms.CharField(label="Ihr Name", max_length=200)
    kontakt_organisation = forms.CharField(label="Verein / Firma (optional)", max_length=200, required=False)
    kontakt_email = forms.EmailField(label="E-Mail")
    kontakt_telefon = forms.CharField(label="Telefon (optional)", max_length=50, required=False)
    nachricht = forms.CharField(
        label="Nachricht (optional)", widget=forms.Textarea(attrs={"rows": 4}), required=False
    )
    # Unsichtbares Feld gegen Spam-Roboter: Menschen lassen es leer.
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Ungültige Eingabe.")
        return ""

    def clean(self):
        daten = super().clean()
        datum, von, bis = daten.get("datum"), daten.get("von"), daten.get("bis")
        if not (datum and von and bis):
            return daten
        tz = timezone.get_current_timezone()
        beginn = timezone.make_aware(datetime.datetime.combine(datum, von), tz)
        ende = timezone.make_aware(datetime.datetime.combine(datum, bis), tz)
        if ende <= beginn:
            raise forms.ValidationError("Die Endzeit muss nach der Startzeit liegen.")
        if beginn < timezone.now():
            raise forms.ValidationError("Der Termin liegt in der Vergangenheit.")
        raum = daten.get("raum")
        if raum and Buchung.objects.bestaetigt().ueberschneidend(raum, beginn, ende).exists():
            raise forms.ValidationError(
                f"{raum} ist in diesem Zeitraum leider bereits belegt. Bitte wählen Sie eine andere Zeit oder einen anderen Raum."
            )
        daten["beginn"], daten["ende"] = beginn, ende
        return daten

    def speichern(self):
        d = self.cleaned_data
        return Buchung.objects.create(
            raum=d["raum"],
            titel=d["titel"],
            art=d["art"],
            beginn=d["beginn"],
            ende=d["ende"],
            status=Buchung.Status.ANGEFRAGT,
            kontakt_name=d["kontakt_name"],
            kontakt_organisation=d["kontakt_organisation"],
            kontakt_email=d["kontakt_email"],
            kontakt_telefon=d["kontakt_telefon"],
            nachricht=d["nachricht"],
            oeffentlich_angefragt=True,
        )


class DatumZeitInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%dT%H:%M", **kwargs)


class BuchungForm(forms.ModelForm):
    """Formular für Mitarbeitende zum Anlegen und Bearbeiten von Buchungen."""

    class Meta:
        model = Buchung
        fields = [
            "raum", "titel", "art", "beginn", "ende", "status",
            "kontakt_name", "kontakt_organisation", "kontakt_email", "kontakt_telefon",
            "nachricht", "preis", "notiz_intern",
        ]
        widgets = {
            "beginn": DatumZeitInput(),
            "ende": DatumZeitInput(),
            "nachricht": forms.Textarea(attrs={"rows": 3}),
            "notiz_intern": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["raum"].queryset = Raum.objects.filter(aktiv=True) | Raum.objects.filter(
            pk=getattr(self.instance, "raum_id", None)
        )
        self.fields["raum"].empty_label = None
        for name in ("beginn", "ende"):
            self.fields[name].input_formats = ["%Y-%m-%dT%H:%M"]
        if not self.instance.pk:
            self.initial.setdefault("status", Buchung.Status.BESTAETIGT)
