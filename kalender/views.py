import datetime
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import AnfrageForm, BuchungForm
from .ics import kalender_ics
from .models import Buchung, Raum

WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def _mail(empfaenger, betreff, text):
    if empfaenger:
        send_mail(betreff, text, None, [empfaenger], fail_silently=True)


def _zeitraum(b):
    beginn, ende = timezone.localtime(b.beginn), timezone.localtime(b.ende)
    if beginn.date() == ende.date():
        return f"{beginn:%d.%m.%Y}, {beginn:%H:%M}–{ende:%H:%M} Uhr"
    return f"{beginn:%d.%m.%Y %H:%M} – {ende:%d.%m.%Y %H:%M} Uhr"


# ---------------------------------------------------------------- öffentlich

def anfrage(request):
    if request.method == "POST":
        form = AnfrageForm(request.POST)
        if form.is_valid():
            b = form.speichern()
            _mail(
                settings.BENACHRICHTIGUNG_EMAIL,
                f"Neue Raumanfrage: {b.titel}",
                f"{b.kontakt_name} hat {b.raum} angefragt:\n{_zeitraum(b)}\n\n"
                f"Bitte prüfen: {request.build_absolute_uri(reverse('kalender:anfragen'))}",
            )
            return render(request, "kalender/anfrage_danke.html", {"buchung": b, "zeitraum": _zeitraum(b)})
    else:
        form = AnfrageForm(initial={"raum": request.GET.get("raum")})
    return render(request, "kalender/anfrage.html", {"form": form})


def _token_pruefen(token):
    if not secrets.compare_digest(str(token), settings.KALENDER_FEED_TOKEN):
        raise Http404


def ics_alle(request, token):
    _token_pruefen(token)
    buchungen = Buchung.objects.bestaetigt().select_related("raum")
    return _ics_antwort(kalender_ics(buchungen, "Hof Hesselmann – alle Räume"))


def ics_raum(request, token, raum_id):
    _token_pruefen(token)
    raum = get_object_or_404(Raum, pk=raum_id)
    buchungen = Buchung.objects.bestaetigt().filter(raum=raum).select_related("raum")
    return _ics_antwort(kalender_ics(buchungen, f"Hof Hesselmann – {raum.name}"))


def _ics_antwort(inhalt):
    antwort = HttpResponse(inhalt, content_type="text/calendar; charset=utf-8")
    antwort["Content-Disposition"] = 'inline; filename="kalender.ics"'
    return antwort


# ---------------------------------------------------------------- Mitarbeitende

@login_required
def woche(request):
    try:
        tag = datetime.date.fromisoformat(request.GET.get("datum", ""))
    except ValueError:
        tag = timezone.localdate()
    montag = tag - datetime.timedelta(days=tag.weekday())
    tage = [montag + datetime.timedelta(days=i) for i in range(7)]
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.datetime.combine(montag, datetime.time.min), tz)
    ende = start + datetime.timedelta(days=7)

    buchungen = (
        Buchung.objects.filter(
            status__in=[Buchung.Status.ANGEFRAGT, Buchung.Status.BESTAETIGT],
            beginn__lt=ende,
            ende__gt=start,
        )
        .select_related("raum")
    )
    raeume = list(Raum.objects.filter(aktiv=True))
    raster = {r.pk: {t: [] for t in tage} for r in raeume}
    for b in buchungen:
        if b.raum_id not in raster:
            continue
        b_start = timezone.localtime(b.beginn).date()
        b_ende = timezone.localtime(b.ende - datetime.timedelta(seconds=1)).date()
        for t in tage:
            if b_start <= t <= b_ende:
                raster[b.raum_id][t].append(b)

    zeilen = [{"raum": r, "zellen": [(t, raster[r.pk][t]) for t in tage]} for r in raeume]
    return render(
        request,
        "kalender/woche.html",
        {
            "zeilen": zeilen,
            "tage": [(WOCHENTAGE[i], t) for i, t in enumerate(tage)],
            "heute": timezone.localdate(),
            "vorher": montag - datetime.timedelta(days=7),
            "nachher": montag + datetime.timedelta(days=7),
            "kw": montag.isocalendar().week,
        },
    )


@login_required
def anfragen(request):
    offen = list(Buchung.objects.offen().select_related("raum"))
    for b in offen:
        b.konflikt_liste = list(b.konflikte())
        b.zeitraum = _zeitraum(b)
    return render(request, "kalender/anfragen.html", {"anfragen": offen})


@login_required
@require_POST
def entscheiden(request, pk):
    b = get_object_or_404(Buchung, pk=pk, status=Buchung.Status.ANGEFRAGT)
    if request.POST.get("aktion") == "freigeben":
        try:
            b.freigeben(request.user)
        except ValidationError as fehler:
            messages.error(request, " ".join(fehler.messages))
            return redirect("kalender:anfragen")
        messages.success(request, f"„{b.titel}“ wurde freigegeben.")
        _mail(
            b.kontakt_email,
            f"Ihre Raumanfrage wurde bestätigt: {b.titel}",
            f"Guten Tag {b.kontakt_name},\n\nIhre Anfrage für {b.raum} am {_zeitraum(b)} "
            "wurde bestätigt.\n\nViele Grüße\nHof Hesselmann",
        )
    elif request.POST.get("aktion") == "ablehnen":
        b.ablehnen(request.user)
        messages.info(request, f"„{b.titel}“ wurde abgelehnt.")
        _mail(
            b.kontakt_email,
            f"Ihre Raumanfrage: {b.titel}",
            f"Guten Tag {b.kontakt_name},\n\nleider können wir Ihre Anfrage für {b.raum} am "
            f"{_zeitraum(b)} nicht bestätigen.\n\nViele Grüße\nHof Hesselmann",
        )
    return redirect("kalender:anfragen")


@login_required
def buchung_bearbeiten(request, pk=None):
    b = get_object_or_404(Buchung, pk=pk) if pk else None
    if request.method == "POST":
        form = BuchungForm(request.POST, instance=b)
        if form.is_valid():
            b = form.save()
            messages.success(request, f"„{b.titel}“ wurde gespeichert.")
            datum = timezone.localtime(b.beginn).date().isoformat()
            return redirect(f"{reverse('kalender:woche')}?datum={datum}")
    else:
        initial = {}
        if not b and request.GET.get("datum"):
            initial["beginn"] = f"{request.GET['datum']}T10:00"
            initial["ende"] = f"{request.GET['datum']}T12:00"
        if not b and request.GET.get("raum"):
            initial["raum"] = request.GET["raum"]
        form = BuchungForm(instance=b, initial=initial)
    return render(request, "kalender/buchung_form.html", {"form": form, "buchung": b})


@login_required
def abos(request):
    def url(name, **kw):
        return request.build_absolute_uri(
            reverse(name, kwargs={"token": settings.KALENDER_FEED_TOKEN, **kw})
        )

    return render(
        request,
        "kalender/abos.html",
        {
            "alle": url("kalender:ics_alle"),
            "raeume": [(r, url("kalender:ics_raum", raum_id=r.pk)) for r in Raum.objects.all()],
            "anfrage_url": request.build_absolute_uri(reverse("kalender:anfrage")),
            "token_unsicher": settings.KALENDER_FEED_TOKEN == "entwicklung",
        },
    )
