"""
Lógica compartida para importar convocatorias desde un archivo CSV.

Se usa desde dos lugares:
  1. El comando de gestión `importar_csv` (uso automático / por script).
  2. La vista de carga dentro del admin (uso desde la interfaz gráfica).

Formato esperado del CSV (encabezados, en cualquier orden; solo
"institucion" es obligatoria):

    institucion,link,fecha_limite,area,monto,estado,viabilidad,notas,etiquetas,proyectos

- fecha_limite en formato AAAA-MM-DD (déjala vacía si no hay fecha exacta).
- estado: por_evaluar, pendiente, en_preparacion, aplicada, adjudicada,
  en_espera, no_aplica (si se deja vacío, usa "por_evaluar").
- viabilidad: por_evaluar, baja, media, alta (si se deja vacío, usa
  "por_evaluar").
- etiquetas / proyectos: nombres separados por coma (ej. "Innovación,Medio
  ambiente"). Si no existen todavía, se crean automáticamente.

El "institucion" se usa como identificador: si ya existe una convocatoria
con ese nombre, se actualiza con los datos nuevos en vez de duplicarla.
"""
import csv
import io

from .models import Convocatoria, Etiqueta, Proyecto

CAMPOS_SIMPLES = {"link", "fecha_limite", "area", "monto", "estado", "viabilidad", "notas"}
CAMPOS_M2M = {"etiquetas", "proyectos"}
ESTADOS_VALIDOS = {c[0] for c in Convocatoria.ESTADO_CHOICES}
VIABILIDADES_VALIDAS = {c[0] for c in Convocatoria.VIABILIDAD_CHOICES}


class FilaInvalida(Exception):
    pass


def _limpiar_fila(fila: dict, numero: int) -> dict:
    institucion = (fila.get("institucion") or "").strip()
    if not institucion:
        raise FilaInvalida(f"Fila {numero}: falta 'institucion'.")

    datos = {"institucion": institucion}
    for campo in CAMPOS_SIMPLES:
        valor = (fila.get(campo) or "").strip()
        if campo == "fecha_limite":
            datos[campo] = valor or None
        elif campo == "estado":
            datos[campo] = valor if valor in ESTADOS_VALIDOS else "por_evaluar"
        elif campo == "viabilidad":
            datos[campo] = valor if valor in VIABILIDADES_VALIDAS else "por_evaluar"
        else:
            datos[campo] = valor

    for campo in CAMPOS_M2M:
        crudo = (fila.get(campo) or "").strip()
        datos[campo] = [n.strip() for n in crudo.split(",") if n.strip()] if crudo else []

    return datos


def importar_convocatorias_csv(archivo):
    """
    `archivo` puede ser una ruta (str) o un objeto tipo archivo (ej. el que
    entrega un <input type="file"> en Django). Devuelve un dict con el
    resumen del resultado.
    """
    if isinstance(archivo, str):
        f = open(archivo, newline="", encoding="utf-8-sig")
        cerrar_al_final = True
    else:
        contenido = archivo.read()
        if isinstance(contenido, bytes):
            contenido = contenido.decode("utf-8-sig")
        f = io.StringIO(contenido)
        cerrar_al_final = False

    creadas, actualizadas, errores = [], [], []
    try:
        lector = csv.DictReader(f)
        for i, fila in enumerate(lector, start=2):  # fila 1 = encabezados
            try:
                datos = _limpiar_fila(fila, i)
            except FilaInvalida as e:
                errores.append(str(e))
                continue

            institucion = datos.pop("institucion")
            nombres_etiquetas = datos.pop("etiquetas")
            nombres_proyectos = datos.pop("proyectos")

            obj, creada = Convocatoria.objects.update_or_create(
                institucion=institucion, defaults=datos
            )

            if nombres_etiquetas:
                etiquetas = [Etiqueta.objects.get_or_create(nombre=n)[0] for n in nombres_etiquetas]
                obj.etiquetas.set(etiquetas)
            if nombres_proyectos:
                proyectos = [Proyecto.objects.get_or_create(nombre=n)[0] for n in nombres_proyectos]
                obj.proyectos.set(proyectos)

            (creadas if creada else actualizadas).append(institucion)
    finally:
        if cerrar_al_final:
            f.close()

    return {"creadas": creadas, "actualizadas": actualizadas, "errores": errores}
