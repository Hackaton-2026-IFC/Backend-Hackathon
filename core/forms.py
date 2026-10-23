"""Formulários do painel administrativo para o modelo de usuário customizado."""

from django import forms
from django.contrib.auth.forms import UserChangeForm

from core.models import User


class CustomUserChangeForm(UserChangeForm):
    # O UsernameField do UserChangeForm padrão chama len(value) antes de
    # tratar None. Nosso User.username aceita NULL, então usamos CharField.
    username = forms.CharField(max_length=30, required=False)

    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'
