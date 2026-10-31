from .models import Buchung


def offene_anfragen(request):
    if getattr(request, "user", None) and request.user.is_authenticated:
        return {"anzahl_offen": Buchung.objects.offen().count()}
    return {}
