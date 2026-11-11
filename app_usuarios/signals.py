from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver

from .models import PerfilCliente


@receiver(post_save, sender=get_user_model())
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        PerfilCliente.objects.get_or_create(usuario=instance)


@receiver(social_account_added)
def pop_user_google_avatar(request, sociallogin, **kwargs):
    user = sociallogin.user
    perfil, _ = PerfilCliente.objects.get_or_create(usuario=user)

    if sociallogin.account.provider == 'google':
        picture_url = sociallogin.account.extra_data.get('picture')
        if picture_url and not perfil.avatar:
            perfil.avatar_url = picture_url
            perfil.save()