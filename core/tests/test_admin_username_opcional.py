from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.forms import CustomUserChangeForm

User = get_user_model()


class AdminUsernameOpcionalTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email='admin-f41@example.com', password='SenhaForte123'
        )
        self.usuario = User.objects.create_user(
            email='pessoa-f41@example.com',
            password='SenhaForte123', name='Nome Antigo', username=None,
        )
        self.client.force_login(self.superuser)
        self.url = reverse('admin:core_user_change', args=[self.usuario.pk])

    def test_admin_usa_formulario_compativel_com_username_nulo(self):
        model_admin = admin.site._registry[User]
        self.assertIs(model_admin.form, CustomUserChangeForm)
        form = model_admin.form(instance=self.usuario)
        self.assertFalse(form.fields['username'].required)
        self.assertEqual(form.fields['username'].clean(None), '')
        self.assertEqual(form.fields['username'].clean(''), '')

    def test_post_admin_salva_usuario_com_username_em_branco(self):
        resposta = self.client.post(
            self.url, {
                'email': self.usuario.email,
                'name': 'Nome Novo',
                'username': '',
                'profile_image': '',
                'is_active': 'on',
                '_save': 'Salvar',
            },
        )
        self.assertEqual(resposta.status_code, 302, resposta.content[:1500])
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.name, 'Nome Novo')
        self.assertIn(self.usuario.username, ('', None))

    def test_post_admin_salva_username_preenchido(self):
        resposta = self.client.post(self.url, {
            'email': self.usuario.email,
            'name': self.usuario.name,
            'username': 'nome_valido',
            'profile_image': '',
            'is_active': 'on',
            '_save': 'Salvar',
        })
        self.assertEqual(resposta.status_code, 302, resposta.content[:1500])
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.username, 'nome_valido')
