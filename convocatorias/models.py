from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


class Fuente(models.Model):
    TIPO_CHOICES = [
        ("portal", "Portal de convocatorias"),
        ("fundacion", "Fundación / donante"),
        ("newsletter", "Newsletter / boletín"),
        ("red", "Red o alianza"),
        ("otro", "Otro"),
    ]

    nombre = models.CharField("Nombre", max_length=200)
    url = models.URLField("URL", blank=True)
    tipo = models.CharField("Tipo", max_length=20, choices=TIPO_CHOICES, default="otro")
    notas = models.TextField("Notas", blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fuente"
        verbose_name_plural = "Fuentes"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Etiqueta(models.Model):
    nombre = models.CharField("Nombre", max_length=80, unique=True)

    class Meta:
        verbose_name = "Etiqueta"
        verbose_name_plural = "Etiquetas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Proyecto(models.Model):
    nombre = models.CharField("Nombre del proyecto", max_length=255)
    descripcion = models.TextField("Descripción", blank=True)
    activo = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Convocatoria(models.Model):
    ESTADO_CHOICES = [
        ("por_evaluar", "Por evaluar"),
        ("pendiente", "Pendiente"),
        ("en_preparacion", "En preparación"),
        ("aplicada", "Aplicada"),
        ("adjudicada", "Adjudicada"),
        ("en_espera", "En espera (cerrada / standby)"),
        ("no_aplica", "No aplica"),
    ]

    VIABILIDAD_CHOICES = [
        ("por_evaluar", "Por evaluar"),
        ("baja", "Baja"),
        ("media", "Media"),
        ("alta", "Alta"),
    ]

    institucion = models.CharField("Institución / Fuente", max_length=255)
    fuente = models.ForeignKey(
        Fuente, verbose_name="Fuente relacionada", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="convocatorias",
    )
    fecha_limite = models.DateField("Fecha límite", null=True, blank=True)
    area = models.CharField("Área temática", max_length=255, blank=True)
    monto = models.CharField("Monto / Financiamiento", max_length=120, blank=True)
    link = models.URLField("Link", blank=True)
    estado = models.CharField("Estado", max_length=20, choices=ESTADO_CHOICES, default="por_evaluar")
    viabilidad = models.CharField(
        "Viabilidad según el perfil de nuestros proyectos",
        max_length=20, choices=VIABILIDAD_CHOICES, default="por_evaluar",
    )
    notas = models.TextField("Notas", blank=True)
    etiquetas = models.ManyToManyField(
        Etiqueta, verbose_name="Etiquetas", blank=True, related_name="convocatorias"
    )
    proyectos = models.ManyToManyField(
        Proyecto, verbose_name="Proyectos relacionados", blank=True, related_name="convocatorias"
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Convocatoria"
        verbose_name_plural = "Convocatorias"
        ordering = ["fecha_limite"]

    def __str__(self):
        return f"{self.institucion} ({self.get_estado_display()})"

    @property
    def dias_restantes(self):
        if not self.fecha_limite:
            return None
        return (self.fecha_limite - timezone.localdate()).days

    @property
    def es_urgente(self):
        dias = self.dias_restantes
        return dias is not None and 0 <= dias <= 7 and self.estado not in ("aplicada", "adjudicada", "no_aplica", "en_espera")


def ruta_adjunto(instance, filename):
    return f"convocatorias/{instance.convocatoria_id}/{filename}"


class Adjunto(models.Model):
    convocatoria = models.ForeignKey(
        Convocatoria, verbose_name="Convocatoria", on_delete=models.CASCADE, related_name="adjuntos"
    )
    archivo = models.FileField("Archivo", upload_to=ruta_adjunto)
    descripcion = models.CharField("Descripción", max_length=255, blank=True)
    subido_en = models.DateTimeField("Subido el", auto_now_add=True)

    class Meta:
        verbose_name = "Adjunto"
        verbose_name_plural = "Adjuntos"
        ordering = ["-subido_en"]

    def __str__(self):
        return self.descripcion or self.archivo.name.rsplit("/", 1)[-1]
