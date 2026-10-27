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
router.register(r'dengue', views.PacienteDengueViewSet, basename='dengue')
router.register(r'tuberculose', views.PacienteTuberculoseViewSet, basename='tuberculose')
router.register(r'sifilis', views.PacienteSifilisViewSet, basename='sifilis')
router.register(r'chagas', views.PacienteChagasViewSet, basename='chagas')
router.register(r'violenciadomestica', views.PacienteViolenciaDomesticaViewSet, basename='violenciadomestica')
router.register(r'hans', views.PacientesHansViewSet, basename='hans')
router.register(r'hepatite', views.PacientesHepatiteViewSet, basename='hepatite')
router.register(r'animaispec', views.PacienteAnimaisPecViewSet, basename='animaispec')
router.register(r'intoxicacao', views.PacienteIntoxicacaoViewSet, basename='intoxicacao')
router.register(r'leish', views.PacienteLeishViewSet, basename='leish')
router.register(r'aidsadulta', views.PacienteAidsAdultoViewSet, basename='aidsadulta')
router.register(r'coberturavacinal', views.CoberturaVacinalViewSet, basename='coberturavacinal')
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/casos_por_bairro/', views.casos_por_bairro, name='casos_por_bairro'),
    path('api/chat/', views.chat_suporte, name='chat_suporte'),
    path('api/upload/', views.upload_arquivo, name='upload_arquivo'),
    path('api/sincronizar-governo/', views.sincronizar_api_governo, name='sincronizar_api_governo'),
    path('api/exportar/<str:doenca>/', views.exportar_dados, name='exportar_dados'),

    # Rotas do Token
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Rotas do Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Rota da Interface Gráfica do Swagger UI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]