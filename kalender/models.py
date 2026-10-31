import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Raum(models.Model):
    name = models.CharField(max_length=100, unique=True)
    beschreibung = models.TextField(blank=True)
    kapazitaet = models.PositiveIntegerField("Kapazität (Personen)", null=True, blank=True)
    aktiv = models.BooleanField(
        default=True, help_text="Nur aktive Räume können angefragt und gebucht werden."
    )
    reihenfolge = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["reihenfolge", "name"]
        verbose_name = "Raum"
        verbose_name_plural = "Räume"

    def __str__(self):
        return self.name


class BuchungQuerySet(models.QuerySet):
    def bestaetigt(self):
        return self.filter(status=Buchung.Status.BESTAETIGT)

    def offen(self):
        return self.filter(status=Buchung.Status.ANGEFRAGT)

    def ueberschneidend(self, raum, beginn, ende):
        return self.filter(raum=raum, beginn__lt=ende, ende__gt=beginn)


class Buchung(models.Model):
    class Art(models.TextChoices):
        VERMIETUNG = "vermietung", "Vermietung"
        KONZERT = "konzert", "Konzert"
        LEHRGANG = "lehrgang", "Lehrgang"
        INTERN = "intern", "Intern"

    class Status(models.TextChoices):
        ANGEFRAGT = "angefragt", "Angefragt"
        BESTAETIGT = "bestaetigt", "Bestätigt"
        ABGELEHNT = "abgelehnt", "Abgelehnt"
        STORNIERT = "storniert", "Storniert"

    raum = models.ForeignKey(Raum, on_delete=models.PROTECT, related_name="buchungen")
    titel = models.CharField("Titel / Anlass", max_length=200)
    art = models.CharField(max_length=20, choices=Art.choices, default=Art.VERMIETUNG)
    beginn = models.DateTimeField()
    ende = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ANGEFRAGT)

    # Kontakt (Mieter, Veranstalter, anfragende Person)
    kontakt_name = models.CharField("Name", max_length=200, blank=True)
    kontakt_organisation = models.CharField("Verein / Firma", max_length=200, blank=True)
    kontakt_email = models.EmailField("E-Mail", blank=True)
    kontakt_telefon = models.CharField("Telefon", max_length=50, blank=True)
    nachricht = models.TextField("Nachricht der anfragenden Person", blank=True)

    preis = models.DecimalField(
        "Preis (€)", max_digits=8, decimal_places=2, null=True, blank=True
    )
    notiz_intern = models.TextField("Interne Notiz", blank=True)

    oeffentlich_angefragt = models.BooleanField(default=False, editable=False)
    erstellt_am = models.DateTimeField(auto_now_add=True)
    entschieden_am = models.DateTimeField(null=True, blank=True, editable=False)
    entschieden_von = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        editable=False,
        related_name="+",
    )
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    objects = BuchungQuerySet.as_manager()

    class Meta:
        ordering = ["beginn"]
        verbose_name = "Buchung"
        verbose_name_plural = "Buchungen"

    def __str__(self):
        return f"{self.titel} ({self.raum}, {timezone.localtime(self.beginn):%d.%m.%Y %H:%M})"

    def konflikte(self):
        """Bestätigte Buchungen im selben Raum, die sich zeitlich überschneiden."""
        if not (self.raum_id and self.beginn and self.ende):
            return Buchung.objects.none()
        return (
            Buchung.objects.bestaetigt()
            .ueberschneidend(self.raum_id, self.beginn, self.ende)
            .exclude(pk=self.pk)
        )

    def clean(self):
        if self.beginn and self.ende and self.ende <= self.beginn:
            raise ValidationError({"ende": "Das Ende muss nach dem Beginn liegen."})
        if self.status == self.Status.BESTAETIGT:
            konflikt = self.konflikte().first()
            if konflikt:
                raise ValidationError(
                    f"Der Raum ist in diesem Zeitraum bereits belegt: {konflikt}."
                )

    def freigeben(self, benutzer):
        self.status = self.Status.BESTAETIGT
        self.full_clean()
        self.entschieden_am = timezone.now()
        self.entschieden_von = benutzer
        self.save()

    def ablehnen(self, benutzer):
        self.status = self.Status.ABGELEHNT
        self.entschieden_am = timezone.now()
        self.entschieden_von = benutzer
        self.save()
