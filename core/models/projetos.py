from django.conf import settings
from django.db import models


class Projeto(models.Model):
    ICON_CHOICES = (
        ('', 'Sem ícone'),
        ('school', 'School'),
        ('book-open-page-variant', 'Book Open'),
        ('briefcase', 'Briefcase'),
        ('laptop', 'Laptop'),
        ('dumbbell', 'Dumbbell'),
        ('heart-pulse', 'Heart Pulse'),
        ('target', 'Target'),
        ('rocket-launch', 'Rocket Launch'),
        ('folder', 'Folder'),
        ('home', 'Home'),
        ('airplane', 'Airplane'),
        ('car', 'Car'),
        ('camera', 'Camera'),
        ('music', 'Music'),
        ('gamepad-variant', 'Gamepad'),
    )

    STATUS_PLANEJADO = 'planejado'
    STATUS_EM_ANDAMENTO = 'em_andamento'
    STATUS_CONCLUIDO = 'concluido'
    STATUS_CHOICES = (
        (STATUS_PLANEJADO, 'Planejado'),
        (STATUS_EM_ANDAMENTO, 'Em andamento'),
        (STATUS_CONCLUIDO, 'Concluído'),
    )

    nome = models.CharField(max_length=100)
    data_criacao = models.DateField(auto_now_add=True)
    data_limite = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANEJADO)
    descricao = models.TextField(blank=True, null=True)
    cor = models.CharField(max_length=7, default='#FFFFFF')
    icone = models.CharField(max_length=50, choices=ICON_CHOICES, default='folder', blank=True)
    criador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projetos_criados')
    participantes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ProjetoMembro',
        related_name='projetos_participando',
    )

    def __str__(self):
        return self.nome


class ProjetoMembro(models.Model):
    CARGO_OWNER = 'owner'
    CARGO_ADMIN = 'admin'
    CARGO_MEMBER = 'member'

    CARGO_CHOICES = (
        (CARGO_OWNER, 'Owner'),
        (CARGO_ADMIN, 'Admin'),
        (CARGO_MEMBER, 'Membro'),
    )

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='membros')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='membros_projeto')
    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES, default=CARGO_ADMIN)

    class Meta:
        unique_together = ('projeto', 'usuario')

    def __str__(self):
        return f'{self.usuario} ({self.cargo})'

class ProjetoFixado(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projetos_fixados')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='fixacoes')
    fixado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'projeto'], name='projeto_fixado_por_usuario_unico')
        ]
