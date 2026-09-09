from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomerProfile


User = get_user_model()


@receiver(post_save, sender=User)
def ensure_customer_profile(sender, instance, created, **kwargs):
    """
    Crea un perfil comercial solamente para clientes reales.

    Los administradores y superusuarios de Django
    no forman parte del sistema comercial de Pronty.
    """

    if instance.is_staff or instance.is_superuser:

        CustomerProfile.objects.filter(
            user=instance
        ).delete()

        return

    CustomerProfile.objects.get_or_create(
        user=instance
    )