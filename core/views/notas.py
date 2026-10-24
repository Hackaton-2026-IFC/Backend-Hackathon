from django.db import transaction
from django.db.models import BooleanField, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Nota, NotaPreferencia, Projeto
from core.serializers import NotaSerializer


class NotaViewSet(ModelViewSet):
    """Ideias do projeto são compartilhadas; preferências de exibição são pessoais."""

    serializer_class = NotaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['projeto', 'arquivada']
    search_fields = ['titulo', 'conteudo', 'link']
    ordering_fields = ['titulo', 'criada_em', 'atualizada_em', 'lembrete_em']
    ordering = ['-fixada_usuario', 'ordem_usuario', '-atualizada_em', '-id']

    def get_queryset(self):
        user = self.request.user
        preferences = NotaPreferencia.objects.filter(nota_id=OuterRef('pk'), usuario=user)
        visible = Nota.objects.filter(
            Q(usuario=user, projeto__isnull=True)
            | Q(projeto__membros__usuario=user)
        )
        if self.action == 'list' and 'projeto' not in self.request.query_params:
            visible = visible.filter(usuario=user)

        qs = visible.annotate(
            fixada_usuario=Coalesce(
                Subquery(preferences.values('fixada')[:1]),
                Value(False),
                output_field=BooleanField(),
            ),
            ordem_usuario=Coalesce(
                Subquery(preferences.values('ordem')[:1]),
                Value(2147483647),
                output_field=IntegerField(),
            ),
        ).select_related('projeto', 'usuario').distinct()

        if self.action == 'list':
            # "fixada" no filtro pertence exclusivamente ao usuário logado.
            pin = self.request.query_params.get('fixada')
            if pin in ('true', 'false'):
                qs = qs.filter(fixada_usuario=(pin == 'true'))

        return qs.order_by('-fixada_usuario', 'ordem_usuario', '-atualizada_em', '-id')

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def _exigir_autoria(self, nota):
        if nota.usuario_id != self.request.user.pk:
            raise PermissionDenied('Somente o autor pode alterar ou excluir esta ideia.')

    def perform_update(self, serializer):
        self._exigir_autoria(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._exigir_autoria(instance)
        instance.delete()

    @action(detail=True, methods=['patch'], url_path='preferencia')
    def preferencia(self, request, pk=None):
        note = self.get_object()
        pin = serializers.BooleanField().run_validation(request.data.get('fixada'))
        pref, _ = NotaPreferencia.objects.update_or_create(
            nota=note,
            usuario=request.user,
            defaults={'fixada': pin},
        )
        note.fixada_usuario = pref.fixada
        note.ordem_usuario = pref.ordem if pref.ordem is not None else 2147483647
        return Response(self.get_serializer(note).data)

    @action(detail=False, methods=['post'], url_path='ordenar')
    @transaction.atomic
    def ordenar(self, request):
        projeto = serializers.IntegerField(min_value=1).run_validation(request.data.get('projeto'))
        ids = serializers.ListField(
            child=serializers.IntegerField(min_value=1),
            allow_empty=True,
            max_length=2000,
        ).run_validation(request.data.get('ids'))
        if not Projeto.objects.filter(pk=projeto, membros__usuario=request.user).exists():
            raise NotFound('Projeto não encontrado.')
        existentes = set(Nota.objects.filter(
            projeto_id=projeto, arquivada=False,
        ).values_list('id', flat=True))
        if len(ids) != len(set(ids)) or set(ids) != existentes:
            raise ValidationError({
                'ids': 'Envie uma vez cada ideia não arquivada deste projeto, sem IDs de outros projetos.'
            })

        for ordem, nota_id in enumerate(ids):
            NotaPreferencia.objects.update_or_create(
                nota_id=nota_id,
                usuario=request.user,
                defaults={'ordem': ordem},
            )
        return Response({'projeto': projeto, 'ids': ids}, status=status.HTTP_200_OK)
