from rest_framework import viewsets, permissions
from .models import CanalComunicacao
from .serializers import CanalComunicacaoSerializer

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

class CanalComunicacaoViewSet(viewsets.ModelViewSet):
    queryset = CanalComunicacao.objects.all().order_by('-date', '-time')
    serializer_class = CanalComunicacaoSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user
        nome_autor = user.get_full_name().strip() or user.username
        serializer.save(author=nome_autor)