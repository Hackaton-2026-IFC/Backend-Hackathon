from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Projeto, ProjetoMembro
from core.serializers import ProjetoMembroSerializer, ProjetoSerializer

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
        return Projeto.objects.filter(membros__usuario=self.request.user).distinct().order_by('-data_criacao')

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

    @action(detail=False, methods=['get'], url_path='meus-projetos')
    def meus_projetos(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='adicionar-membro')
    def adicionar_membro(self, request, pk=None):
        projeto = self.get_object()
        if not self._pode_editar_projeto(projeto, request.user):
            raise PermissionDenied('Apenas o owner ou admin podem gerenciar membros.')

        usuario_id = request.data.get('usuario')
        cargo = request.data.get('cargo', ProjetoMembro.CARGO_ADMIN)

        if not usuario_id:
            raise ValidationError({'usuario': 'Informe o usuário.'})

        usuario = User.objects.filter(pk=usuario_id).first()
        if usuario is None:
            raise ValidationError({'usuario': 'Usuário não encontrado.'})

        if cargo not in dict(ProjetoMembro.CARGO_CHOICES):
            raise ValidationError({'cargo': 'Cargo inválido.'})

        if usuario == request.user and cargo == ProjetoMembro.CARGO_ADMIN:
            pass

        membro, created = ProjetoMembro.objects.get_or_create(
            projeto=projeto,
            usuario=usuario,
            defaults={'cargo': cargo},
        )
        if not created:
            membro.cargo = cargo
            membro.save()

        return Response(
            ProjetoMembroSerializer(membro).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
