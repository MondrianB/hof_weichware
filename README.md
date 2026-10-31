# Hof Weichware

Verwaltungssystem für den **Hof Hesselmann**: Raumvermietung, Konzerte und Lehrgänge.

## Geschäftsbereiche

- **Vermietung**: Räume im Bürgerzentrum vermieten, Belegung und Verfügbarkeit planen
- **Konzerte**: Veranstaltungen planen, Plätze und Gästelisten verwalten
- **Lehrgänge**: Kurse anlegen, Termine planen, Teilnehmende verwalten

## Nutzung

- **Mitarbeitende** bedienen das System (Anmeldung mit Benutzerkonto).
- **Außenstehende** können über ein öffentliches Formular Terminanfragen in den
  Kalender eintragen. Diese Anfragen erscheinen erst nach **Freigabe durch
  Mitarbeitende** als feste Termine.

## Geplante Grundfunktionen

- Gemeinsamer Kalender für alle Räume und Veranstaltungen, ohne Doppelbelegungen
- Öffentliches Anfrageformular mit Freigabe-Workflow (Anfrage, Freigabe oder Ablehnung)
- **Google-Kalender-kompatibel**: Kalender als iCal-Feed (`.ics`), der in Google
  Kalender abonniert werden kann (je Raum oder gesamt)
- Kundenverwaltung (Mieter, Veranstalter, Kursteilnehmende)
- Angebote und Rechnungen
- Übersicht über Einnahmen je Bereich

## Stand der ersten Version

Fertig:

- Wochenkalender aller Räume (Tenne, Scheune, Kaminraum, Modersohn-Raum, Upkammer,
  Seminarraum 1 und 2) mit Farben je Art (Vermietung, Konzert, Lehrgang, Intern)
- Buchungen anlegen, bearbeiten, stornieren; Doppelbelegungen werden verhindert
- Öffentliches Anfrageformular (`/kalender/anfrage/`) mit Spamschutz
- Freigabe oder Ablehnung von Anfragen, auf Wunsch mit E-Mail an die anfragende Person
- Kalender-Links (iCal) zum Abonnieren in Google Kalender, gesamt und je Raum
- Räume und Benutzerkonten pflegen unter „Verwaltung“ (`/admin/`)

Noch offen: Preise und Rechnungen, Konzert-Tickets, Teilnehmerlisten für Lehrgänge,
Zwei-Wege-Abgleich mit Google Kalender, Einrichtung auf einem Server.

## Lokal ausprobieren

Voraussetzung: Python 3.12 oder neuer.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

Danach im Browser <http://127.0.0.1:8000> öffnen und anmelden.

Tests: `.venv/bin/python manage.py test`

## Einstellungen für den Echtbetrieb (Umgebungsvariablen)

| Variable | Bedeutung |
|---|---|
| `DJANGO_SECRET_KEY` | Langer geheimer Zufallswert |
| `DJANGO_DEBUG` | Auf `0` setzen |
| `DJANGO_ALLOWED_HOSTS` | Domain, z. B. `kalender.hof-hesselmann.de` |
| `KALENDER_FEED_TOKEN` | Geheimer Teil der Google-Kalender-Links |
| `BENACHRICHTIGUNG_EMAIL` | Empfänger für Hinweise auf neue Anfragen |
| `DEFAULT_FROM_EMAIL`, `DJANGO_EMAIL_BACKEND` | E-Mail-Versand |
