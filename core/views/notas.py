from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from core.models import Nota
from core.serializers import NotaSerializer


class NotaViewSet(ModelViewSet):
    serializer_class = NotaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['projeto', 'fixada', 'arquivada']
    search_fields = ['titulo', 'conteudo']
    ordering_fields = ['titulo', 'criada_em', 'atualizada_em', 'lembrete_em']
    ordering = ['-fixada', '-atualizada_em', '-id']

    def get_queryset(self):
        return (
            Nota.objects.filter(usuario=self.request.user)
            .select_related('projeto')
            .order_by('-fixada', '-atualizada_em', '-id')
        )

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
