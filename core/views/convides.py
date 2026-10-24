from django.utils import timezone
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
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
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['projeto', 'usuario', 'enviado_por', 'cargo', 'status']
    search_fields = ['projeto__nome', 'usuario__name', 'usuario__username']
    ordering_fields = ['criado_em', 'respondido_em', 'status']
    ordering = ['-criado_em', '-id']
    # Respostas são feitas pela action; PUT/PATCH/DELETE não devem alterar convites.
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        # Convites são privados: somente o usuário destinatário pode listá-los,
        # visualizá-los ou respondê-los. Filtrar pelo projeto não deve ampliar
        # essa visibilidade, mesmo quando o usuário é owner/admin.
        queryset = ConviteProjeto.objects.filter(
            usuario=self.request.user
        ).order_by('-criado_em', '-id')
        if self.action == 'responder':
            # Bloqueio na própria tabela, sem DISTINCT/JOIN, para evitar
            # duas respostas simultâneas ao mesmo convite.
            return queryset.select_for_update()
        return queryset

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
