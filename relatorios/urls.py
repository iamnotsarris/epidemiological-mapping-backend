from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from api import views
from api.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

router = routers.DefaultRouter()
urlpatterns = [
    # Rota do Relatório
    path('api/relatorios/mensal/', views.download_relatorio_mensal, name='download_relatorio_mensal'),
]