from django.conf import settings
import logging

from django.core.mail import send_mail
from django.db import transaction

from core.models import Notificacao

logger = logging.getLogger(__name__)


def _frontend_link(path):
    urls = getattr(settings, 'FRONTEND_URLS', [])
    if not path:
        return ''
    if urls:
        return f"{urls[0].rstrip('/')}/{path.lstrip('/')}"
    return path


def _enviar_email(notification_id):
    if not getattr(settings, 'NOTIFICATION_EMAIL_ENABLED', False):
        return
    notification = (
        Notificacao.objects.select_related('destinatario')
        .filter(pk=notification_id)
        .first()
    )
    if notification is None or not notification.destinatario.email:
        return

    body = notification.mensagem
    url = _frontend_link(notification.link)
    if url:
        body = f'{body}\n\nAbrir: {url}'

    try:
        sent = send_mail(
        subject=f'[Hackathon] {notification.titulo}',
        message=body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        recipient_list=[notification.destinatario.email],
        fail_silently=False,
        )
    except (OSError, ConnectionError, TimeoutError) as exc:
        logger.warning('Falha no envio de notificação por e-mail (id=%s): %s', notification_id, type(exc).__name__)
        return
    if sent:
        Notificacao.objects.filter(pk=notification.pk).update(email_enviado=True)


def criar_notificacao(*, destinatario, ator, projeto, tarefa=None, tipo, titulo, mensagem, link=''):
    if ator is not None and destinatario.pk == ator.pk:
        return None

    notification = Notificacao.objects.create(
        destinatario=destinatario,
        ator=ator,
        projeto=projeto,
        tarefa=tarefa,
        tipo=tipo,
        titulo=titulo[:180],
        mensagem=mensagem,
        link=link[:300],
    )
    if getattr(settings, 'NOTIFICATION_EMAIL_ENABLED', False):
        transaction.on_commit(lambda notification_id=notification.pk: _enviar_email(notification_id))
    return notification


def notificar_membros_projeto(*, projeto, ator, tarefa=None, tipo, titulo, mensagem, link=''):
    notifications = []
    membros = (
        projeto.membros.select_related('usuario')
        .exclude(usuario=ator)
        .order_by('id')
    )
    for membro in membros:
        notification = criar_notificacao(
            destinatario=membro.usuario,
            ator=ator,
            projeto=projeto,
            tarefa=tarefa,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            link=link,
        )
        if notification is not None:
            notifications.append(notification)
    return notifications
