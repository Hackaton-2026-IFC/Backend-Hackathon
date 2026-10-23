from django.contrib.auth import get_user_model
from django.http import Http404
from django.db import transaction
from django.db.models import Exists, OuterRef
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Projeto, ProjetoMembro, ProjetoFixado, Tarefa
from core.serializers import ProjetoMembroSerializer, ProjetoSerializer, TarefaSerializer

User = get_user_model()


class ProjetoViewSet(ModelViewSet):
    serializer_class = ProjetoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _get_membro(self, projeto, usuario):
        return projeto.membros.filter(usuario=usuario).first()

    def _pode_editar_projeto(self, projeto, usuario):
        membro = self._get_membro(projeto, usuario)
        if membro is None:
            return False
        return membro.cargo in {ProjetoMembro.CARGO_OWNER, ProjetoMembro.CARGO_ADMIN}

    def get_queryset(self):
        fixados = ProjetoFixado.objects.filter(projeto_id=OuterRef('pk'), usuario=self.request.user)
        return (Projeto.objects.filter(membros__usuario=self.request.user)
                .annotate(fixado_usuario=Exists(fixados))
                .distinct().order_by('-fixado_usuario', '-data_criacao', '-id'))

    def get_object(self):
        try:
            obj = Projeto.objects.get(pk=self.kwargs['pk'])
        except Projeto.DoesNotExist as exc:
            raise Http404 from exc
        if not obj.membros.filter(usuario=self.request.user).exists():
            raise PermissionDenied('Você não faz parte desta equipe.')
        return obj

    def perform_create(self, serializer):
        serializer.save(criador=self.request.user)

    def update(self, request, *args, **kwargs):
        projeto = self.get_object()
        if not self._pode_editar_projeto(projeto, request.user):
            raise PermissionDenied('Apenas o owner ou admin podem alterar o projeto.')
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        projeto = self.get_object()
        if not self._pode_editar_projeto(projeto, request.user):
            raise PermissionDenied('Apenas o owner ou admin podem alterar o projeto.')
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        projeto = self.get_object()
        membro = self._get_membro(projeto, request.user)
        if membro is None or membro.cargo != ProjetoMembro.CARGO_OWNER:
            raise PermissionDenied('Apenas o owner pode excluir o projeto.')
        return super().destroy(request, *args, **kwargs)


    @action(detail=True, methods=['get'], url_path='kanban')
    def kanban(self, request, pk=None):
        """Kanban e progresso das tarefas de um projeto acessível ao usuário."""
        projeto = self.get_object()
        tarefas = list(
            Tarefa.objects.filter(projeto=projeto)
            .prefetch_related('dependencias', 'microtarefas')
            .order_by('-data_criacao', '-id')
        )
        colunas = {status: [] for status, _ in Tarefa.STATUS_CHOICES}
        for tarefa in tarefas:
            colunas[tarefa.status].append(
                TarefaSerializer(tarefa, context={'request': request}).data
            )

        total = len(tarefas)
        concluidas = len(colunas[Tarefa.STATUS_CONCLUIDO])
        return Response({
            'projeto': projeto.pk,
            'progresso': round(concluidas * 100 / total, 2) if total else 0,
            'total_tarefas': total,
            'tarefas_concluidas': concluidas,
            'kanban': colunas,
        })

    @action(detail=True, methods=['post', 'delete'], url_path='fixar')
    def fixar(self, request, pk=None):
        projeto = self.get_object()
        if request.method == 'POST':
            ProjetoFixado.objects.get_or_create(usuario=request.user, projeto=projeto)
            return Response({'fixado': True})
        ProjetoFixado.objects.filter(usuario=request.user, projeto=projeto).delete()
        return Response({'fixado': False})

    @action(detail=False, methods=['get'], url_path='meus-projetos')
    def meus_projetos(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='membros')
    def listar_membros(self, request, pk=None):
        projeto = self.get_object()
        membros = projeto.membros.select_related('usuario').order_by('id')
        return Response(ProjetoMembroSerializer(membros, many=True).data)

    @action(detail=True, methods=['post'], url_path='adicionar-membro')
    def adicionar_membro(self, request, pk=None):
        # Rota de compatibilidade com o frontend atual.
        # Somente o proprietário pode incluir administradores diretamente.
        projeto = self.get_object()
        ator = self._get_membro(projeto, request.user)
        if not ator or ator.cargo != ProjetoMembro.CARGO_OWNER:
            raise PermissionDenied('Somente o proprietário pode adicionar administradores diretamente.')

        usuario = User.objects.filter(pk=request.data.get('usuario')).first()
        if usuario is None:
            raise ValidationError({'usuario': 'Usuário não encontrado.'})
        cargo = request.data.get('cargo', ProjetoMembro.CARGO_ADMIN)
        if cargo not in {ProjetoMembro.CARGO_ADMIN, ProjetoMembro.CARGO_MEMBER}:
            raise ValidationError({'cargo': 'Cargo inválido.'})
        if projeto.membros.filter(usuario=usuario).exists():
            raise ValidationError({'usuario': 'Este usuário já participa do projeto.'})
        membro = ProjetoMembro.objects.create(projeto=projeto, usuario=usuario, cargo=cargo)
        return Response(ProjetoMembroSerializer(membro).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'membros/(?P<usuario_id>[^/.]+)')
    def remover_membro(self, request, pk=None, usuario_id=None):
        projeto = self.get_object()
        ator = self._get_membro(projeto, request.user)
        membro = projeto.membros.filter(usuario_id=usuario_id).first()
        if membro is None:
            raise Http404
        if membro.cargo == ProjetoMembro.CARGO_OWNER:
            raise PermissionDenied('O proprietário não pode ser removido; transfira a propriedade primeiro.')
        if membro.usuario_id != request.user.id:
            if ator.cargo == ProjetoMembro.CARGO_MEMBER:
                raise PermissionDenied('Membros não podem remover outros participantes.')
            if ator.cargo == ProjetoMembro.CARGO_ADMIN and membro.cargo != ProjetoMembro.CARGO_MEMBER:
                raise PermissionDenied('Administradores só podem remover membros comuns.')
        membro.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'], url_path=r'membros/(?P<usuario_id>[^/.]+)/cargo')
    def alterar_cargo(self, request, pk=None, usuario_id=None):
        projeto = self.get_object()
        ator = self._get_membro(projeto, request.user)
        if ator.cargo != ProjetoMembro.CARGO_OWNER:
            raise PermissionDenied('Somente o proprietário pode mudar cargos.')
        membro = projeto.membros.filter(usuario_id=usuario_id).first()
        if membro is None:
            raise Http404
        if membro.cargo == ProjetoMembro.CARGO_OWNER:
            raise PermissionDenied('Use a transferência de propriedade para alterar o proprietário.')
        cargo = request.data.get('cargo')
        if cargo not in {ProjetoMembro.CARGO_ADMIN, ProjetoMembro.CARGO_MEMBER}:
            raise ValidationError({'cargo': 'Cargo deve ser admin ou member.'})
        membro.cargo = cargo
        membro.save(update_fields=['cargo'])
        return Response(ProjetoMembroSerializer(membro).data)

    @transaction.atomic
    @action(detail=True, methods=['post'], url_path='transferir-propriedade')
    def transferir_propriedade(self, request, pk=None):
        projeto = self.get_object()
        membros = projeto.membros.select_for_update()
        atual = membros.filter(usuario=request.user, cargo=ProjetoMembro.CARGO_OWNER).first()
        if atual is None:
            raise PermissionDenied('Somente o proprietário pode transferir a propriedade.')
        novo = membros.filter(usuario_id=request.data.get('usuario')).first()
        if novo is None:
            raise ValidationError({'usuario': 'O novo proprietário deve participar do projeto.'})
        if novo.pk == atual.pk:
            raise ValidationError({'usuario': 'Este usuário já é o proprietário.'})
        novo.cargo = ProjetoMembro.CARGO_OWNER
        novo.save(update_fields=['cargo'])
        atual.cargo = ProjetoMembro.CARGO_ADMIN
        atual.save(update_fields=['cargo'])
        projeto.criador = novo.usuario
        projeto.save(update_fields=['criador'])
        return Response({'proprietario': novo.usuario_id})
