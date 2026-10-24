from datetime import date, timedelta
from django.utils import timezone
import requests
from django.db.models import Q
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from core.models import Projeto, Tarefa
from core.models.calendar_event import CalendarEvent

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = ('id', 'projeto', 'titulo', 'descricao', 'data', 'hora_inicio', 'hora_fim', 'localizacao', 'criado_por')
        read_only_fields = ('id', 'projeto', 'criado_por')

    def validate(self, attrs):
        start = attrs.get('hora_inicio', getattr(self.instance, 'hora_inicio', None))
        end = attrs.get('hora_fim', getattr(self.instance, 'hora_fim', None))
        if bool(start) != bool(end):
            raise serializers.ValidationError({'hora_inicio': 'Informe início e fim, ou deixe ambos vazios para evento de dia inteiro.'})
        if start and end and end <= start:
            raise serializers.ValidationError({'hora_fim': 'Deve ocorrer após a hora de início.'})
        return attrs

def allowed_project(request, pk):
    try:
        project = Projeto.objects.get(pk=pk)
    except Projeto.DoesNotExist as exc:
        raise NotFound('Projeto não encontrado.') from exc
    if not project.membros.filter(usuario=request.user).exists():
        raise PermissionDenied('Você não participa deste projeto.')
    return project

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def calendario(request, pk):
    project = allowed_project(request, pk)
    if request.method == 'POST':
        serializer = EventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(projeto=project, criado_por=request.user)
        return Response(serializer.data, status=201)
    try:
        start = date.fromisoformat(request.query_params.get('inicio', '')) if request.query_params.get('inicio') else timezone.localdate()
        end = date.fromisoformat(request.query_params.get('fim', '')) if request.query_params.get('fim') else start + timedelta(days=30)
    except ValueError as exc:
        raise ValidationError({'data': 'Utilize YYYY-MM-DD.'}) from exc
    if end < start or (end - start).days > 366:
        raise ValidationError({'fim': 'Intervalo deve ter entre 0 e 366 dias.'})
    events = list(CalendarEvent.objects.filter(projeto=project, data__range=(start, end)).values(
        'id', 'titulo', 'descricao', 'data', 'hora_inicio', 'hora_fim', 'localizacao'))
    tasks = list(Tarefa.objects.filter(projeto=project).filter(
        Q(data_limite__range=(start,end)) | Q(prazo_antecipado__range=(start,end))
    ).values('id','titulo','status','data_limite','prazo_antecipado','clima_influencia','localizacao'))
    return Response({'projeto': project.pk, 'inicio': start, 'fim': end,
                     'eventos': events, 'tarefas': tasks})

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def calendario_evento(request, pk, event_id):
    project = allowed_project(request, pk)
    try:
        event = CalendarEvent.objects.get(pk=event_id, projeto=project)
    except CalendarEvent.DoesNotExist as exc:
        raise NotFound('Evento não encontrado.') from exc
    role = project.membros.get(usuario=request.user).cargo
    if event.criado_por_id != request.user.id and role not in ('owner', 'admin'):
        raise PermissionDenied('Apenas o autor ou um administrador pode alterar o evento.')
    if request.method == 'DELETE':
        event.delete()
        return Response(status=204)
    serializer = EventSerializer(event, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_google_agenda(request, pk):
    project = allowed_project(request, pk)
    # Obrigatório ter realizado login Google ou vínculo explícito anteriormente.
    if not hasattr(request.user, 'google_identity') or not request.auth or request.auth.get('auth_provider') != 'google':
        raise PermissionDenied('Para acessar Google Agenda, faça login com Google nesta sessão.')
    token = request.data.get('access_token')
    event_id = request.data.get('evento')
    if not isinstance(token, str) or not token or not event_id:
        raise ValidationError({'detail': 'Informe evento e access_token OAuth com escopo calendar.events.'})
    event = CalendarEvent.objects.filter(pk=event_id, projeto=project).first()
    if not event:
        raise NotFound('Evento não encontrado no projeto.')
    try:
        info_response = requests.get('https://www.googleapis.com/oauth2/v3/tokeninfo', params={'access_token': token}, timeout=6)
        info_response.raise_for_status()
        info = info_response.json()
        scopes = info.get('scope', '').split()
        if 'openid' not in scopes or 'https://www.googleapis.com/auth/calendar.events' not in scopes:
            raise PermissionDenied('Autorize os escopos openid e calendar.events para exportar.')
        # Usar userinfo com token delegado para garantir que pertence à conta vinculada.
        user_response = requests.get('https://openidconnect.googleapis.com/v1/userinfo', headers={'Authorization': 'Bearer ' + token}, timeout=6)
        user_response.raise_for_status()
        if user_response.json().get('sub') != request.user.google_identity.sub:
            raise PermissionDenied('Autorização Google pertence a outra conta.')
        if event.hora_inicio:
            from datetime import datetime, time
            from django.utils import timezone
            start = datetime.combine(event.data, event.hora_inicio)
            finish = datetime.combine(event.data, event.hora_fim or time(23, 59))
            if finish <= start:
                raise ValidationError({'hora_fim': 'Horário inválido.'})
            tz = timezone.get_current_timezone()
            start = timezone.make_aware(start, tz).isoformat()
            finish = timezone.make_aware(finish, tz).isoformat()
            payload = {'summary': event.titulo, 'description': event.descricao,
                       'start': {'dateTime': start}, 'end': {'dateTime': finish}}
        else:
            payload = {'summary': event.titulo, 'description': event.descricao,
                       'start': {'date': event.data.isoformat()},
                       'end': {'date': (event.data + timedelta(days=1)).isoformat()}}
        result = requests.post('https://www.googleapis.com/calendar/v3/calendars/primary/events',
                               json=payload, headers={'Authorization': 'Bearer ' + token}, timeout=8)
        if result.status_code not in (200, 201):
            return Response({'detail': 'Não foi possível exportar para o Google Agenda.'}, status=502)
        data = result.json()
        return Response({'id': data.get('id'), 'htmlLink': data.get('htmlLink')}, status=201)
    except requests.RequestException:
        return Response({'detail': 'Google Agenda indisponível. Tente novamente.'}, status=502)
