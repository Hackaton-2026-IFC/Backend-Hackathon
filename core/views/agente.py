from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Projeto
from core.services.ai_agent import generate_project_analysis


class AgentRequestSerializer(serializers.Serializer):
    objetivo = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    ideias = serializers.ListField(
        child=serializers.CharField(max_length=500, trim_whitespace=True),
        required=False,
        allow_empty=True,
        max_length=20,
    )

    def validate_ideias(self, value):
        return [idea.strip() for idea in value if idea.strip()]


class ProjectAgentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        project = Projeto.objects.filter(pk=pk).first()
        if project is None:
            from django.http import Http404
            raise Http404
        if not project.membros.filter(usuario=request.user).exists():
            raise PermissionDenied('Você não faz parte deste projeto.')

        serializer = AgentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = generate_project_analysis(
            project,
            request.user,
            data.get('ideias', []),
            data.get('objetivo', '').strip(),
        )
        return Response({
            'projeto': project.id,
            'nome': project.nome,
            **result,
        })
