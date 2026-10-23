from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet

from core.models import Recurso, ProjetoMembro
from core.serializers.recursos import RecursoSerializer


class RecursoViewSet(ModelViewSet):
    """Consulta e manutenção de recursos; criação ocorre nas rotas de projeto/tarefa."""
    serializer_class = RecursoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['projeto', 'tarefa', 'tipo', 'adicionado_por']
    search_fields = ['titulo', 'descricao', 'url', 'projeto__nome', 'tarefa__titulo']
    ordering_fields = ['titulo', 'criado_em', 'tipo']
    ordering = ['-criado_em', '-id']
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Recurso.objects.filter(
            projeto__membros__usuario=self.request.user
        ).distinct().select_related('projeto', 'tarefa', 'adicionado_por')

    def _exigir_permissao_edicao(self, recurso):
        usuario = self.request.user
        membro = recurso.projeto.membros.filter(usuario=usuario).first()
        if usuario.id == recurso.adicionado_por_id:
            return
        if membro and membro.cargo in (ProjetoMembro.CARGO_OWNER, ProjetoMembro.CARGO_ADMIN):
            return
        raise PermissionDenied('Somente o autor ou administradores podem alterar este recurso.')

    def perform_update(self, serializer):
        self._exigir_permissao_edicao(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._exigir_permissao_edicao(instance)
        instance.delete()
