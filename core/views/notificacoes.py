from django.utils import timezone
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from core.models import Notificacao
from core.serializers import NotificacaoSerializer


class NotificacaoViewSet(ReadOnlyModelViewSet):
    serializer_class = NotificacaoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Notificacao.objects.filter(destinatario=self.request.user)
            .select_related('ator', 'projeto', 'tarefa')
            .order_by('-criada_em', '-id')
        )

    @action(detail=True, methods=['post'], url_path='ler')
    def ler(self, request, pk=None):
        notification = self.get_object()
        if notification.lida_em is None:
            notification.lida_em = timezone.now()
            notification.save(update_fields=['lida_em'])
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=['post'], url_path='ler-todas')
    def ler_todas(self, request):
        updated = self.get_queryset().filter(lida_em__isnull=True).update(lida_em=timezone.now())
        return Response({'atualizadas': updated})

    @action(detail=False, methods=['get'], url_path='nao-lidas')
    def nao_lidas(self, request):
        queryset = self.get_queryset().filter(lida_em__isnull=True)
        return Response({'quantidade': queryset.count()})
