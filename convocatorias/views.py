from django.shortcuts import render
from .models import Convocatoria, Fuente


def lista_convocatorias(request):
    convocatorias = Convocatoria.objects.all()

    q = request.GET.get("q", "").strip()
    if q:
        convocatorias = convocatorias.filter(institucion__icontains=q) | convocatorias.filter(area__icontains=q)

    estado = request.GET.get("estado", "")
    if estado:
        convocatorias = convocatorias.filter(estado=estado)

    context = {
        "convocatorias": convocatorias,
        "estados": Convocatoria.ESTADO_CHOICES,
        "q": q,
        "estado_actual": estado,
    }
    return render(request, "convocatorias/lista.html", context)


def lista_fuentes(request):
    fuentes = Fuente.objects.all()
    return render(request, "convocatorias/fuentes.html", {"fuentes": fuentes})
