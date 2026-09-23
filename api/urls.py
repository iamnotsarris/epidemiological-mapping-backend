from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from api import views
from api.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = routers.DefaultRouter()
router.register(r'dengue', views.PacienteDengueViewSet)
router.register(r'tuberculose', views.PacienteTuberculoseViewSet)
router.register(r'sifilis', views.PacienteSifilisViewSet)
router.register(r'chagas', views.PacienteChagasViewSet)
router.register(r'violenciadomestica', views.PacienteViolenciaDomesticaViewSet)
router.register(r'hans', views.PacientesHansViewSet)
router.register(r'hepatite', views.PacientesHepatiteViewSet)
router.register(r'animaispec', views.PacienteAnimaisPecViewSet)
router.register(r'intoxicacao', views.PacienteIntoxicacaoViewSet)
router.register(r'leish', views.PacienteLeishViewSet)
router.register(r'aidsadulta', views.PacienteAidsAdultoViewSet)
router.register(r'coberturavacinal', views.CoberturaVacinalViewSet)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/casos_por_bairro/', views.casos_por_bairro, name='casos_por_bairro'),
    path('api/chat/', views.chat_suporte, name='chat_suporte'),

    # Rotas do Token
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]