import openpyxl
from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from simple_history.admin import SimpleHistoryAdmin

from .importers import importar_convocatorias_csv
from .models import Adjunto, Convocatoria, Etiqueta, Fuente, Proyecto


@admin.register(Fuente)
class FuenteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "url")
    list_filter = ("tipo",)
    search_fields = ("nombre", "notas")


@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "descripcion")


class AdjuntoInline(admin.TabularInline):
    model = Adjunto
    extra = 1
    fields = ("archivo", "descripcion", "subido_en")
    readonly_fields = ("subido_en",)


@admin.register(Convocatoria)
class ConvocatoriaAdmin(SimpleHistoryAdmin):
    list_display = (
        "institucion", "fecha_limite", "dias_restantes_display",
        "area", "monto", "estado", "viabilidad", "etiquetas_display",
    )
    list_filter = ("estado", "viabilidad", "area", "etiquetas", "proyectos")
    search_fields = ("institucion", "area", "notas")
    date_hierarchy = "fecha_limite"
    autocomplete_fields = ["fuente"]
    filter_horizontal = ("etiquetas", "proyectos")
    inlines = [AdjuntoInline]
    actions = ["exportar_a_excel"]
    change_list_template = "admin/convocatorias/convocatoria_changelist.html"

    fieldsets = (
        (None, {
            "fields": ("institucion", "fuente", "area", "link")
        }),
        ("Plazos y financiamiento", {
            "fields": ("fecha_limite", "monto")
        }),
        ("Seguimiento", {
            "fields": ("estado", "viabilidad", "notas")
        }),
        ("Clasificación", {
            "fields": ("etiquetas", "proyectos")
        }),
    )

    @admin.display(description="Días restantes")
    def dias_restantes_display(self, obj):
        dias = obj.dias_restantes
        """
        Alertas
        
        """
        if dias is None:
            return "—"
        if dias < 0:
            return "Vencida"
        return f"{dias} d" + (" ⚠️" if obj.es_urgente else "")

    @admin.display(description="Etiquetas")
    def etiquetas_display(self, obj):
        return ", ".join(e.nombre for e in obj.etiquetas.all()) or "—"

    @admin.action(description="Exportar seleccionadas a Excel")
    def exportar_a_excel(self, request, queryset):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Convocatorias"
        headers = [
            "Institución", "Fecha límite", "Área", "Monto", "Estado",
            "Viabilidad", "Etiquetas", "Proyectos", "Link", "Notas",
        ]
        ws.append(headers)
        for c in queryset:
            ws.append([
                c.institucion,
                c.fecha_limite.strftime("%Y-%m-%d") if c.fecha_limite else "",
                c.area,
                c.monto,
                c.get_estado_display(),
                c.get_viabilidad_display(),
                ", ".join(e.nombre for e in c.etiquetas.all()),
                ", ".join(p.nombre for p in c.proyectos.all()),
                c.link,
                c.notas,
            ])
        for col in ws.columns:
            width = max(len(str(cell.value)) if cell.value else 0 for cell in col) + 2
            ws.column_dimensions[col[0].column_letter].width = min(width, 60)

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="convocatorias.xlsx"'
        wb.save(response)
        return response

    # ---- Importar CSV desde la interfaz gráfica del admin ----
    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path("importar-csv/", self.admin_site.admin_view(self.importar_csv_view), name="convocatorias_importar_csv"),
        ]
        return extra + urls

    def importar_csv_view(self, request):
        if request.method == "POST" and request.FILES.get("archivo_csv"):
            resultado = importar_convocatorias_csv(request.FILES["archivo_csv"])
            if resultado["creadas"]:
                messages.success(request, f"Creadas: {len(resultado['creadas'])} — {', '.join(resultado['creadas'])}")
            if resultado["actualizadas"]:
                messages.info(request, f"Actualizadas: {len(resultado['actualizadas'])} — {', '.join(resultado['actualizadas'])}")
            if resultado["errores"]:
                messages.error(request, f"Filas con error: {'; '.join(resultado['errores'])}")
            if not (resultado["creadas"] or resultado["actualizadas"] or resultado["errores"]):
                messages.warning(request, "El archivo no tenía filas para importar.")
            return redirect("..")
        return render(request, "admin/convocatorias/importar_csv.html", {
            "opts": self.model._meta,
            "title": "Importar convocatorias desde CSV",
        })


admin.site.site_header = "Registro de Convocatorias"
admin.site.site_title = "Convocatorias"
admin.site.index_title = "Panel de gestión"
