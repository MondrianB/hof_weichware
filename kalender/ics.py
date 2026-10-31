"""Erzeugt iCalendar-Dateien (.ics), die Google Kalender abonnieren kann (RFC 5545)."""

import datetime

from django.utils import timezone


def _escape(text):
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _falten(zeile):
    """Zeilen länger als 75 Byte werden gemäß RFC 5545 umbrochen."""
    roh = zeile.encode("utf-8")
    if len(roh) <= 75:
        return zeile
    teile, aktuell, laenge, grenze = [], "", 0, 75
    for zeichen in zeile:
        b = len(zeichen.encode("utf-8"))
        if laenge + b > grenze:
            teile.append(aktuell)
            aktuell, laenge, grenze = "", 0, 74  # Folgezeilen beginnen mit Leerzeichen
        aktuell += zeichen
        laenge += b
    teile.append(aktuell)
    return "\r\n ".join(teile)


def _utc(dt):
    return dt.astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def kalender_ics(buchungen, kalendername):
    jetzt = _utc(timezone.now())
    zeilen = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Hof Hesselmann//Hof Weichware//DE",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(kalendername)}",
        "X-WR-TIMEZONE:Europe/Berlin",
        "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
        "X-PUBLISHED-TTL:PT1H",
    ]
    for b in buchungen:
        beschreibung = b.get_art_display()
        if b.kontakt_organisation or b.kontakt_name:
            beschreibung += "\n" + (b.kontakt_organisation or b.kontakt_name)
        zeilen += [
            "BEGIN:VEVENT",
            f"UID:{b.uid}@hof-weichware",
            f"DTSTAMP:{jetzt}",
            f"DTSTART:{_utc(b.beginn)}",
            f"DTEND:{_utc(b.ende)}",
            f"SUMMARY:{_escape(b.titel)}",
            f"LOCATION:{_escape(b.raum.name)}",
            f"DESCRIPTION:{_escape(beschreibung)}",
            f"CATEGORIES:{_escape(b.get_art_display())}",
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ]
    zeilen.append("END:VCALENDAR")
    return "\r\n".join(_falten(z) for z in zeilen) + "\r\n"
