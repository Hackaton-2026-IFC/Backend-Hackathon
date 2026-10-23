from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import ConviteProjeto, Projeto, ProjetoMembro
from core.serializers import ConviteProjetoSerializer, RespostaConviteSerializer


class ConviteProjetoViewSet(ModelViewSet):
    serializer_class = ConviteProjetoSerializer
    permission_classes = [permissions.IsAuthenticated]
    # Respostas são feitas pela action; PUT/PATCH/DELETE não devem alterar convites.
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        queryset = ConviteProjeto.objects.filter(
            Q(usuario=self.request.user) | Q(projeto__membros__usuario=self.request.user)
        ).distinct().order_by('-criado_em')
        if self.action == 'responder':
            # PostgreSQL proíbe SELECT ... FOR UPDATE combinado com DISTINCT.
            # Mantemos a verificação de visibilidade numa subquery e bloqueamos
            # somente a tabela de convites, sem JOIN/DISTINCT no SELECT externo.
            return ConviteProjeto.objects.filter(
                pk__in=queryset.values('pk')
            ).select_for_update().order_by('-criado_em')
        return queryset

    def get_object(self):
        obj = super().get_object()
        if obj.usuario == self.request.user:
            return obj
        if not obj.projeto.membros.filter(usuario=self.request.user).exists():
            raise PermissionDenied('Você não faz parte do projeto.')
        return obj

    def perform_create(self, serializer):
        projeto = serializer.validated_data['projeto']
        usuario = serializer.validated_data['usuario']

        if not projeto.membros.filter(
            usuario=self.request.user, cargo__in=[ProjetoMembro.CARGO_OWNER, ProjetoMembro.CARGO_ADMIN]
        ).exists():
            raise PermissionDenied('Apenas proprietário e administradores podem enviar convites.')

        ator = projeto.membros.get(usuario=self.request.user)
        cargo = serializer.validated_data.get('cargo', ProjetoMembro.CARGO_ADMIN)
        if ator.cargo == ProjetoMembro.CARGO_ADMIN and cargo != ProjetoMembro.CARGO_MEMBER:
            raise PermissionDenied('Administradores só podem convidar membros comuns.')

        if projeto.membros.filter(usuario=usuario).exists():
            raise ValidationError({'usuario': 'Este usuário já faz parte do projeto.'})

        serializer.save(enviado_por=self.request.user)

    @transaction.atomic
    @action(detail=True, methods=['post'], url_path='responder')
    def responder(self, request, pk=None):
        convite = self.get_object()
        serializer = RespostaConviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        acao = serializer.validated_data['acao']
        if convite.status != ConviteProjeto.STATUS_PENDENTE:
            raise ValidationError({'convite': 'Este convite já foi respondido.'})
        if convite.usuario != request.user:
            raise PermissionDenied('Você só pode responder ao seu próprio convite.')

        if acao == 'aceitar':
            convite.status = ConviteProjeto.STATUS_ACEITO
            convite.respondido_em = timezone.now()
            convite.save()

            ProjetoMembro.objects.get_or_create(
                projeto=convite.projeto,
                usuario=convite.usuario,
                defaults={'cargo': convite.cargo},
            )

            return Response(ConviteProjetoSerializer(convite).data, status=status.HTTP_200_OK)

        convite.status = ConviteProjeto.STATUS_RECUSADO
        convite.respondido_em = timezone.now()
        convite.save()
        return Response(ConviteProjetoSerializer(convite).data, status=status.HTTP_200_OK)
