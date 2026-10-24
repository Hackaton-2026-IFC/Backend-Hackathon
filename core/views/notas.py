from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from core.models import Nota
from core.serializers import NotaSerializer


class NotaViewSet(ModelViewSet):
    """Notas pessoais são privadas; notas de projeto pertencem ao mural da equipe."""

    serializer_class = NotaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['projeto', 'fixada', 'arquivada']
    search_fields = ['titulo', 'conteudo', 'link']
    ordering_fields = ['titulo', 'criada_em', 'atualizada_em', 'lembrete_em']
    ordering = ['-fixada', '-atualizada_em', '-id']

    def get_queryset(self):
        user = self.request.user
        # Uma nota sem projeto só pode ser vista por seu autor. Notas
        # associadas a projeto são visíveis a todos os membros atuais.
        visible = Nota.objects.filter(
            Q(usuario=user, projeto__isnull=True)
            | Q(projeto__membros__usuario=user)
        )
        if self.action == 'list' and 'projeto' not in self.request.query_params:
            # Preserva a listagem histórica de notas do próprio usuário,
            # sem misturar notas publicadas pelos demais participantes.
            visible = visible.filter(usuario=user)
        return (
            visible.select_related('projeto', 'usuario')
            .distinct()
            .order_by('-fixada', '-atualizada_em', '-id')
        )

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def _exigir_autoria(self, nota):
        # Os participantes podem ler e adicionar ideias; edição/remoção
        # de ideias alheias permanece bloqueada, inclusive para admins.
        if nota.usuario_id != self.request.user.pk:
            raise PermissionDenied('Somente o autor pode alterar ou excluir esta ideia.')

    def perform_update(self, serializer):
        self._exigir_autoria(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._exigir_autoria(instance)
        instance.delete()
