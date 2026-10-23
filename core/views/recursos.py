from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet

from core.models import Recurso, ProjetoMembro
from core.serializers.recursos import RecursoSerializer


class RecursoViewSet(ModelViewSet):
    """Consulta e manutenção de recursos; criação ocorre nas rotas de projeto/tarefa."""
    serializer_class = RecursoSerializer
    permission_classes = [permissions.IsAuthenticated]
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
