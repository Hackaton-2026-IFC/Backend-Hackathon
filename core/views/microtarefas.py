from django.http import Http404
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet

from core.models import MicroTarefa
from core.serializers import MicroTarefaSerializer


class MicroTarefaViewSet(ModelViewSet):
    serializer_class = MicroTarefaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MicroTarefa.objects.filter(tarefa__projeto__membros__usuario=self.request.user).distinct()

    def get_object(self):
        try:
            obj = MicroTarefa.objects.get(pk=self.kwargs['pk'])
        except MicroTarefa.DoesNotExist as exc:
            raise Http404 from exc
        if not obj.tarefa.projeto.membros.filter(usuario=self.request.user).exists():
            raise PermissionDenied('Você não faz parte do projeto desta microtarefa.')
        return obj

    def perform_create(self, serializer):
        tarefa = serializer.validated_data['tarefa']
        if not tarefa.projeto.membros.filter(usuario=self.request.user).exists():
            raise PermissionDenied('Você precisa fazer parte do projeto para criar microtarefas.')
        serializer.save()

    def update(self, request, *args, **kwargs):
        self.get_object()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self.get_object()
        return super().partial_update(request, *args, **kwargs)
