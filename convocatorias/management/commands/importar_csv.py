"""
Importa convocatorias desde un archivo CSV — esta es la vía "automática"
(por script o cron), en contraste con el botón "Importar CSV" del admin.

Uso:
    python manage.py importar_csv ruta/al/archivo.csv

Ver convocatorias/importers.py para el formato esperado del CSV, o
plantilla_convocatorias.csv en la raíz del proyecto para un ejemplo listo
para llenar.
"""
from django.core.management.base import BaseCommand, CommandError

from convocatorias.importers import importar_convocatorias_csv


class Command(BaseCommand):
    help = "Importa (o actualiza) convocatorias desde un archivo CSV."

    def add_arguments(self, parser):
        parser.add_argument("archivo", type=str, help="Ruta al archivo .csv")

    def handle(self, *args, **options):
        ruta = options["archivo"]
        try:
            resultado = importar_convocatorias_csv(ruta)
        except FileNotFoundError:
            raise CommandError(f"No se encontró el archivo: {ruta}")

        for nombre in resultado["creadas"]:
            self.stdout.write(f"  + {nombre}")
        for nombre in resultado["actualizadas"]:
            self.stdout.write(f"  = {nombre} (actualizada)")
        for error in resultado["errores"]:
            self.stderr.write(self.style.WARNING(error))

        self.stdout.write(self.style.SUCCESS(
            f"\nListo: {len(resultado['creadas'])} creadas, "
            f"{len(resultado['actualizadas'])} actualizadas, "
            f"{len(resultado['errores'])} filas con error."
        ))
