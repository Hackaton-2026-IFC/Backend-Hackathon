from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from core.models.atividade import Atividade
from core.models import Projeto, Tarefa
from core.serializers.atividade import AtividadeSerializer

class ActivityPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProjectActivityView(ListAPIView):
    serializer_class = AtividadeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ActivityPagination
    def get_queryset(self):
        project = Projeto.objects.filter(pk=self.kwargs['pk']).first()
        if not project or not project.membros.filter(usuario=self.request.user).exists():
            raise PermissionDenied('Você não participa deste projeto.')
        qs = Atividade.objects.filter(projeto=project).select_related('autor', 'tarefa')
        if self.request.query_params.get('tarefa'):
            qs = qs.filter(tarefa_id_original=self.request.query_params['tarefa'])
        return qs

class TaskActivityView(ListAPIView):
    serializer_class = AtividadeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ActivityPagination
    def get_queryset(self):
        task = Tarefa.objects.filter(pk=self.kwargs['pk']).select_related('projeto').first()
        if not task or not task.projeto.membros.filter(usuario=self.request.user).exists():
            raise PermissionDenied('Você não participa deste projeto.')
        return Atividade.objects.filter(projeto=task.projeto, tarefa_id_original=task.pk).select_related('autor', 'tarefa')
