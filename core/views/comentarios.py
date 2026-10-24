from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from core.models import Tarefa
from core.models.comentario_tarefa import ComentarioTarefa
from core.models.atividade import Atividade
from core.services.notificacoes import notificar_membros_projeto

class ComentarioSerializer(serializers.ModelSerializer):
    autor_nome = serializers.CharField(source='autor.name', read_only=True, allow_null=True)
    class Meta:
        model = ComentarioTarefa
        fields = ('id', 'tarefa', 'autor', 'autor_nome', 'conteudo', 'criado_em', 'atualizado_em')
        read_only_fields = ('id', 'tarefa', 'autor', 'autor_nome', 'criado_em', 'atualizado_em')

    def validate_conteudo(self, value):
        if not value.strip():
            raise serializers.ValidationError('O comentário não pode ficar vazio.')
        return value.strip()

def task_for_member(request, pk):
    task = Tarefa.objects.select_related('projeto').filter(pk=pk).first()
    if task is None:
        raise NotFound('Tarefa não encontrada.')
    if not task.projeto.membros.filter(usuario=request.user).exists():
        raise PermissionDenied('Você não participa do projeto.')
    return task

def activity(task, user, action, comment):
    Atividade.objects.create(projeto=task.projeto, tarefa=task, tarefa_id_original=task.pk,
        tarefa_titulo=task.titulo, autor=user, acao=action,
        alteracoes={'comentario_id': comment.pk})

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def comentarios(request, pk):
    task = task_for_member(request, pk)
    if request.method == 'GET':
        queryset = ComentarioTarefa.objects.filter(tarefa=task).select_related('autor')
        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginator.page_size_query_param = 'page_size'
        paginator.max_page_size = 100
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(ComentarioSerializer(page, many=True).data)
    serializer = ComentarioSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        comment = serializer.save(tarefa=task, autor=request.user)
        activity(task, request.user, 'comentario_criado', comment)
        notificar_membros_projeto(
            projeto=task.projeto,
            ator=request.user,
            tarefa=task,
            tipo='comentario_criado',
            titulo='Novo comentário',
            mensagem=f'{request.user.name or request.user.email} comentou na tarefa "{task.titulo}".',
            link=f'/projects/{task.projeto_id}/tasks',
        )
    return Response(ComentarioSerializer(comment).data, status=status.HTTP_201_CREATED)

@api_view(['PATCH','DELETE'])
@permission_classes([IsAuthenticated])
def comentario_detalhe(request, pk, comentario_id):
    task = task_for_member(request, pk)
    comment = ComentarioTarefa.objects.filter(pk=comentario_id, tarefa=task).first()
    if comment is None:
        raise NotFound('Comentário não encontrado.')
    if comment.autor_id != request.user.pk:
        raise PermissionDenied('Somente o autor pode editar ou excluir o comentário.')
    if request.method == 'DELETE':
        with transaction.atomic():
            activity(task, request.user, 'comentario_excluido', comment)
            comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = ComentarioSerializer(comment, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    if serializer.validated_data.get('conteudo') == comment.conteudo:
        return Response(ComentarioSerializer(comment).data)
    with transaction.atomic():
        serializer.save()
        activity(task, request.user, 'comentario_editado', comment)
    return Response(ComentarioSerializer(comment).data)
