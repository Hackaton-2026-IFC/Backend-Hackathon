from django.utils import timezone
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

    def get_queryset(self):
        queryset = ConviteProjeto.objects.all()
        if self.action == 'responder':
            return queryset
        return queryset.filter(projeto__membros__usuario=self.request.user).distinct().order_by('-criado_em')

    def get_object(self):
        obj = super().get_object()
        if self.action == 'responder':
            if obj.usuario == self.request.user:
                return obj
            raise PermissionDenied('Você só pode responder ao seu próprio convite.')
        if not obj.projeto.membros.filter(usuario=self.request.user).exists():
            raise PermissionDenied('Você não faz parte do projeto.')
        return obj

    def perform_create(self, serializer):
        projeto = serializer.validated_data['projeto']
        usuario = serializer.validated_data['usuario']

        if not projeto.membros.filter(usuario=self.request.user).exists():
            raise PermissionDenied('Apenas membros do projeto podem convidar pessoas.')

        if projeto.membros.filter(usuario=usuario).exists():
            raise ValidationError({'usuario': 'Este usuário já faz parte do projeto.'})

        serializer.save(enviado_por=self.request.user)

    @action(detail=True, methods=['post'], url_path='responder')
    def responder(self, request, pk=None):
        convite = self.get_object()
        serializer = RespostaConviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        acao = serializer.validated_data['acao']
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
