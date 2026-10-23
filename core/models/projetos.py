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

    nome = models.CharField(max_length=100)
    data_criacao = models.DateField(auto_now_add=True)
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

    CARGO_CHOICES = (
        (CARGO_OWNER, 'Owner'),
        (CARGO_ADMIN, 'Admin'),
    )

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='membros')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='membros_projeto')
    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES, default=CARGO_ADMIN)

    class Meta:
        unique_together = ('projeto', 'usuario')

    def __str__(self):
        return f'{self.usuario} ({self.cargo})'
