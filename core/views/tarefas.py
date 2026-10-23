from django.http import Http404
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Tarefa
from core.serializers import TarefaSerializer


class TarefaViewSet(ModelViewSet):
    serializer_class = TarefaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Tarefa.objects.filter(projeto__membros__usuario=self.request.user).distinct().order_by('-data_criacao')

    def get_object(self):
        try:
            obj = Tarefa.objects.get(pk=self.kwargs['pk'])
        except Tarefa.DoesNotExist as exc:
            raise Http404 from exc
        if not obj.projeto.membros.filter(usuario=self.request.user).exists():
            raise PermissionDenied('Você não faz parte do projeto desta tarefa.')
        return obj

    def perform_create(self, serializer):
        projeto = serializer.validated_data.get('projeto')
        if projeto is None or not projeto.membros.filter(usuario=self.request.user).exists():
            raise PermissionDenied('Você precisa fazer parte do projeto para criar tarefas.')
        serializer.save(criado_por=self.request.user)

    def update(self, request, *args, **kwargs):
        self.get_object()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self.get_object()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self.get_object()
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='kanban')
    def kanban(self, request):
        projeto_id = request.query_params.get('projeto')
        queryset = self.get_queryset()
        if projeto_id:
            queryset = queryset.filter(projeto_id=projeto_id)

        agrupado = {
            'planejado': [],
            'em_andamento': [],
            'concluido': [],
        }

        for tarefa in queryset:
            agrupado.setdefault(tarefa.status, []).append(self.get_serializer(tarefa).data)

        return Response(agrupado)
