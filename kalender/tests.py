import datetime

from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .ics import kalender_ics
from .models import Buchung, Raum


def zeit(tage, stunde):
    tag = timezone.localdate() + datetime.timedelta(days=tage)
    return timezone.make_aware(datetime.datetime.combine(tag, datetime.time(stunde)))


@override_settings(KALENDER_FEED_TOKEN="geheim", BENACHRICHTIGUNG_EMAIL="team@example.org")
class KalenderTests(TestCase):
    def setUp(self):
        self.tenne = Raum.objects.get(name="Tenne")
        self.user = User.objects.create_user("anna", password="pw-sehr-geheim")

    def buchung(self, status=Buchung.Status.BESTAETIGT, von=10, bis=12, titel="Test", **kw):
        return Buchung.objects.create(
            raum=self.tenne, titel=titel, beginn=zeit(3, von), ende=zeit(3, bis), status=status, **kw
        )

    def test_raeume_angelegt(self):
        self.assertEqual(
            list(Raum.objects.values_list("name", flat=True)),
            ["Tenne", "Scheune", "Kaminraum", "Modersohn-Raum", "Upkammer", "Seminarraum 1", "Seminarraum 2"],
        )

    def test_doppelbuchung_wird_verhindert(self):
        self.buchung()
        neu = Buchung(raum=self.tenne, titel="X", beginn=zeit(3, 11), ende=zeit(3, 13), status="bestaetigt")
        with self.assertRaises(ValidationError):
            neu.full_clean()
        # direkt anschließend ist erlaubt
        neu.beginn, neu.ende = zeit(3, 12), zeit(3, 14)
        neu.full_clean()

    def test_oeffentliche_anfrage(self):
        tag = (timezone.localdate() + datetime.timedelta(days=5)).isoformat()
        antwort = self.client.post(reverse("kalender:anfrage"), {
            "raum": self.tenne.pk, "datum": tag, "von": "18:00", "bis": "22:00",
            "titel": "Geburtstag", "art": "vermietung", "kontakt_name": "Max",
            "kontakt_email": "max@example.org",
        })
        self.assertContains(antwort, "Vielen Dank")
        b = Buchung.objects.get()
        self.assertEqual(b.status, Buchung.Status.ANGEFRAGT)
        self.assertTrue(b.oeffentlich_angefragt)
        self.assertEqual(mail.outbox[0].to, ["team@example.org"])

    def test_anfrage_bei_belegtem_raum_abgewiesen(self):
        self.buchung()
        antwort = self.client.post(reverse("kalender:anfrage"), {
            "raum": self.tenne.pk, "datum": zeit(3, 0).date().isoformat(), "von": "11:00", "bis": "13:00",
            "titel": "X", "art": "vermietung", "kontakt_name": "Max", "kontakt_email": "max@example.org",
        })
        self.assertContains(antwort, "bereits belegt")
        self.assertEqual(Buchung.objects.count(), 1)

    def test_spamschutz(self):
        tag = (timezone.localdate() + datetime.timedelta(days=5)).isoformat()
        self.client.post(reverse("kalender:anfrage"), {
            "raum": self.tenne.pk, "datum": tag, "von": "18:00", "bis": "22:00", "titel": "X",
            "art": "vermietung", "kontakt_name": "Bot", "kontakt_email": "bot@example.org",
            "website": "http://spam",
        })
        self.assertEqual(Buchung.objects.count(), 0)

    def test_freigeben_und_ablehnen(self):
        self.client.force_login(self.user)
        a = self.buchung(status="angefragt", kontakt_email="max@example.org")
        self.client.post(reverse("kalender:entscheiden", args=[a.pk]), {"aktion": "freigeben"})
        a.refresh_from_db()
        self.assertEqual(a.status, Buchung.Status.BESTAETIGT)
        self.assertEqual(a.entschieden_von, self.user)
        self.assertIn("bestätigt", mail.outbox[-1].subject)

        b = self.buchung(status="angefragt", von=8, bis=9)
        self.client.post(reverse("kalender:entscheiden", args=[b.pk]), {"aktion": "ablehnen"})
        b.refresh_from_db()
        self.assertEqual(b.status, Buchung.Status.ABGELEHNT)

    def test_freigabe_bei_konflikt_nicht_moeglich(self):
        self.client.force_login(self.user)
        self.buchung()
        a = self.buchung(status="angefragt", von=11, bis=13)
        antwort = self.client.post(reverse("kalender:entscheiden", args=[a.pk]), {"aktion": "freigeben"}, follow=True)
        a.refresh_from_db()
        self.assertEqual(a.status, Buchung.Status.ANGEFRAGT)
        self.assertContains(antwort, "bereits belegt")

    def test_mitarbeiterbereich_erfordert_anmeldung(self):
        for name in ["kalender:woche", "kalender:anfragen", "kalender:buchung_neu", "kalender:abos"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)

    def test_wochenansicht(self):
        self.client.force_login(self.user)
        self.buchung(titel="Hofkonzert")
        antwort = self.client.get(reverse("kalender:woche") + "?datum=" + zeit(3, 0).date().isoformat())
        self.assertContains(antwort, "Hofkonzert")
        self.assertContains(antwort, "Modersohn-Raum")

    def test_buchung_anlegen(self):
        self.client.force_login(self.user)
        tag = zeit(4, 0).date().isoformat()
        self.client.post(reverse("kalender:buchung_neu"), {
            "raum": self.tenne.pk, "titel": "Töpferkurs", "art": "lehrgang",
            "beginn": f"{tag}T09:00", "ende": f"{tag}T16:00", "status": "bestaetigt",
        })
        self.assertEqual(Buchung.objects.get().titel, "Töpferkurs")

    def test_ics_feed(self):
        self.buchung(titel="Hofkonzert, mit Band")
        self.buchung(status="angefragt", titel="Nur angefragt", von=14, bis=15)
        self.assertEqual(self.client.get("/kalender/ics/falsch/alle.ics").status_code, 404)
        antwort = self.client.get(reverse("kalender:ics_alle", args=["geheim"]))
        inhalt = antwort.content.decode()
        self.assertEqual(antwort["Content-Type"], "text/calendar; charset=utf-8")
        self.assertIn("SUMMARY:Hofkonzert\\, mit Band", inhalt)
        self.assertNotIn("Nur angefragt", inhalt)
        self.assertIn("LOCATION:Tenne", inhalt)
        raum = self.client.get(reverse("kalender:ics_raum", args=["geheim", Raum.objects.get(name="Scheune").pk]))
        self.assertNotIn("Hofkonzert", raum.content.decode())

    def test_ics_zeilen_umbruch(self):
        b = self.buchung(titel="Ä" * 100)
        for zeile in kalender_ics([b], "Test").split("\r\n"):
            self.assertLessEqual(len(zeile.encode()), 75)
