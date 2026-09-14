"""
Comando de gestión para cargar/actualizar, de una sola vez, las convocatorias
y fuentes recopiladas manualmente en RECOPILACION.txt.

Uso:
    python manage.py cargar_convocatorias

Es seguro correrlo más de una vez: usa update_or_create sobre "institucion",
así que si vuelves a correrlo después de editar este archivo, actualiza los
registros existentes en vez de duplicarlos.

Nota sobre estados: como muchas de estas convocatorias no traían una fecha
límite exacta, el estado se asignó así:
  - "pendiente"   -> tiene una fecha límite futura confirmada, o está abierta
                     de forma constante.
  - "en_espera"   -> no hay fecha confirmada, o la ventana ya pasó (ej. la
                     de julio-agosto), así que se asume cerrada/standby por
                     ahora.
  - "por_evaluar" -> su próxima edición todavía no abre (ej. arranca en
                     2027) o falta información para decidir.
Ajusta cualquiera desde el admin en cuanto confirmes el dato real.
"""
from django.core.management.base import BaseCommand
from convocatorias.models import Convocatoria, Fuente


CONVOCATORIAS = [
    dict(
        institucion="Decelera Ventures",
        link="https://www.decelera.ventures/our-program",
        area="Emprendimiento",
        monto="300,000 USD",
        estado="por_evaluar",
        notas="Próxima edición: Menorca, España — mayo 2027 (fecha aproximada, aún no abre).",
    ),
    dict(
        institucion="500 LATAM",
        link="https://latam.aplica.500.co/es/sites/latam#terminos-inversion",
        area="Emprendimiento / Tecnológico",
        estado="pendiente",
        notas="Aplicación abierta de forma constante, sin convocatoria puntual.",
    ),
    dict(
        institucion="Catalist ClimateTech LATAM",
        link="https://catalist-initiative.eco/news/launching-the-climate-tech-venture-landscape-report-for-latin-america-the-caribbean",
        area="Emprendimiento / Medio ambiente / Tecnológico",
        estado="en_espera",
        notas="Es un reporte/landscape sobre el ecosistema, no una convocatoria confirmada — revisar si hay un fondo activo asociado.",
    ),
    dict(
        institucion="BIND (Cooperación Internacional Cartagena / SPRI)",
        link="https://bind.spri.eus/application/",
        area="Innovación industrial / Tecnológico",
        fecha_limite="2026-09-04",
        estado="pendiente",
        notas=(
            "Al aplicar hay que elegir un grupo de caso de uso: automatización industrial, "
            "mantenimiento predictivo, ciclo de vida de producto, logística/electrificación, "
            "ciberseguridad, digitalización de procesos, eficiencia energética, gestión de "
            "impacto ambiental (CO2/agua/residuos), energía renovable, forecasting de demanda, "
            "o nuevos modelos de negocio. Revisar el formulario para más detalle."
        ),
    ),
    dict(
        institucion="Sur Futuro (FutureWorks)",
        link="https://www.sur-futuro.org/llamado-propuestas-2026",
        area="Innovación",
        monto="Entre 17,000 y 55,000 CAD",
        estado="en_espera",
        notas="Llamado 2026 sin fecha límite confirmada — revisar en el sitio si sigue abierto.",
    ),
    dict(
        institucion="Future For Nature (FFN)",
        link="https://futurefornature.org/future-for-nature/apply-for-future-for-nature/apply/",
        area="Medio ambiente",
        monto="Hasta 50,000 EUR",
        estado="en_espera",
        notas="Sin fecha límite confirmada — revisar en el sitio si hay convocatoria abierta.",
    ),
    dict(
        institucion="NEXA (Grand Challenges Canada)",
        link="https://www.grandchallenges.ca/funding-opportunity-nexa/",
        area="Innovación / Tecnología / Medio ambiente",
        monto="Entre 250,000 y 2,000,000 USD",
        estado="en_espera",
        notas="La ventana de aplicación era entre julio y agosto — probablemente ya cerró.",
    ),
    dict(
        institucion="Fondation de Luxembourg",
        link="https://www.fdlux.lu/en/submit-a-project",
        area="Social / Medio ambiente",
        monto="A convenir",
        estado="pendiente",
        notas="Convocatoria abierta constantemente.",
    ),
    dict(
        institucion="Agrinnova II",
        link="https://www.growingil.org/agrinnova-ii-es",
        area="Agricultura / Innovación / Emprendimiento / Medio ambiente",
        monto="Hasta 150,000 USD",
        estado="en_espera",
        notas="Sin fecha límite confirmada — revisar en el sitio si hay convocatoria abierta.",
    ),
    dict(
        institucion="Global Innovation Challenge",
        link="https://globalinnovationchallenge.awardsplatform.com/",
        area="Social / Innovación / Medio ambiente",
        monto="Hasta 15,000 USD",
        estado="en_espera",
        notas="Sin fecha límite confirmada — revisar en el sitio si hay convocatoria abierta.",
    ),
    dict(
        institucion="ORIRI — Fondo para la Transformación Social",
        link="https://fondooriri.org/convocatorias/",
        estado="por_evaluar",
        notas="Falta revisar el sitio para confirmar si hay convocatoria abierta y sus detalles (monto, área, fecha límite).",
    ),
    dict(
        institucion="Tech4Good (IEEE HT)",
        link="https://ieeeht.org/get-involved/funding-opportunities/tech4good/",
        area="Emprendimiento / Medio ambiente / Tecnológico",
        monto="Entre 2,500 y 10,000 USD",
        estado="pendiente",
        notas="Cierra en marzo de 2027 (fecha exacta sin confirmar).",
    ),
    dict(
        institucion="GenAI for Good (IEEE HT)",
        link="https://ieeeht.org/get-involved/funding-opportunities/genai-for-good/",
        area="Tecnológico",
        estado="por_evaluar",
        notas="Empieza entre octubre y noviembre de 2026 — todavía no abre.",
    ),
    dict(
        institucion="Travel Elevates",
        link="https://www.travelelevates.org/grant",
        area="Innovación / Emprendimiento / Social",
        monto="Incierto",
        fecha_limite="2026-09-01",
        estado="pendiente",
        notas="Cierra muy pronto — revisar con urgencia.",
    ),
    dict(
        institucion="GFCF (Global Fund for Community Foundations)",
        link="https://globalfundcommunityfoundations.org/",
        area="Social / Emprendimiento",
        monto="Incierto",
        fecha_limite="2026-12-31",
        estado="pendiente",
    ),
    dict(
        institucion="Caribbean Biodiversity Fund (Blue Economy Hub)",
        link="https://caribbeanbiodiversityfund.org/",
        estado="en_espera",
        notas="Sin fecha límite confirmada — revisar en el sitio si hay convocatoria abierta.",
    ),
    dict(
        institucion="Climática Irrazonable",
        link="https://climaticairrazonable.com/",
        area="Social / Innovación / Medio ambiente",
        monto="40,000 USD",
        estado="en_espera",
        notas="Sin fecha límite confirmada — revisar en el sitio si hay convocatoria abierta.",
    ),
]

FUENTES = [
    dict(
        nombre="IEEE HT (Humanitarian Technologies)",
        url="https://ieeeht.org/",
        tipo="portal",
        notas="Portal con varias convocatorias activas (Tech4Good, GenAI for Good, entre otras).",
    ),
]


class Command(BaseCommand):
    help = "Carga o actualiza las convocatorias y fuentes recopiladas manualmente."

    def handle(self, *args, **options):
        creadas_conv, actualizadas_conv = 0, 0
        for data in CONVOCATORIAS:
            institucion = data.pop("institucion")
            obj, created = Convocatoria.objects.update_or_create(
                institucion=institucion, defaults=data
            )
            if created:
                creadas_conv += 1
                self.stdout.write(f"  + {institucion}")
            else:
                actualizadas_conv += 1
                self.stdout.write(f"  ~ {institucion} (actualizada)")

        creadas_fte = 0
        for data in FUENTES:
            nombre = data.pop("nombre")
            obj, created = Fuente.objects.get_or_create(nombre=nombre, defaults=data)
            if created:
                creadas_fte += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nListo: {creadas_conv} convocatorias nuevas, {actualizadas_conv} actualizadas, "
            f"{creadas_fte} fuentes nuevas."
        ))
