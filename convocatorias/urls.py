from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista_convocatorias, name="lista_convocatorias"),
    path("fuentes/", views.lista_fuentes, name="lista_fuentes"),
]
