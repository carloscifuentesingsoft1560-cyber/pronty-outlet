from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class CustomerProfile(models.Model):

    class CommercialStatus(models.TextChoices):
        RETAIL = (
            'RETAIL',
            'Cliente detal'
        )

        WHOLESALE_MAINTENANCE = (
            'WHOLESALE_MAINTENANCE',
            'Mayorista - mantenimiento'
        )

        WHOLESALE_ACTIVE = (
            'WHOLESALE_ACTIVE',
            'Mayorista activo'
        )

        WHOLESALE_GRACE = (
            'WHOLESALE_GRACE',
            'Mayorista - período de gracia'
        )

        WHOLESALE_EXPIRED = (
            'WHOLESALE_EXPIRED',
            'Mayorista vencido'
        )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        verbose_name='Usuario'
    )

    commercial_status = models.CharField(
        max_length=40,
        choices=CommercialStatus.choices,
        default=CommercialStatus.RETAIL,
        verbose_name='Estado comercial'
    )

    wholesale_activated_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de activación mayorista'
    )

    maintenance_deadline = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha límite de mantenimiento'
    )

    grace_started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Inicio del período de gracia'
    )

    grace_deadline = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha límite del período de gracia'
    )

    last_wholesale_purchase_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Última compra mayorista válida'
    )

    last_wholesale_purchase_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Valor de la última compra mayorista válida'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        verbose_name = 'Perfil comercial'
        verbose_name_plural = 'Perfiles comerciales'
        ordering = [
            'user__first_name',
            'user__last_name',
            'user__email'
        ]

    def __str__(self):

        full_name = self.user.get_full_name().strip()

        if full_name:
            return full_name

        return self.user.email or self.user.username

    # =========================================================
    # PROPIEDADES COMERCIALES
    # =========================================================

    @property
    def has_wholesale_prices(self):
        """
        Indica si el cliente puede utilizar precios mayoristas.

        Durante mantenimiento y gracia conserva el beneficio.
        """

        return self.commercial_status in {
            self.CommercialStatus.WHOLESALE_MAINTENANCE,
            self.CommercialStatus.WHOLESALE_ACTIVE,
            self.CommercialStatus.WHOLESALE_GRACE,
        }

    @property
    def is_retail(self):
        return not self.has_wholesale_prices

    @property
    def days_until_maintenance_deadline(self):

        if not self.maintenance_deadline:
            return None

        remaining = (
            self.maintenance_deadline
            - timezone.now()
        )

        return max(
            remaining.days,
            0
        )

    @property
    def days_until_grace_deadline(self):

        if not self.grace_deadline:
            return None

        remaining = (
            self.grace_deadline
            - timezone.now()
        )

        return max(
            remaining.days,
            0
        )

    # =========================================================
    # ACTIVACIÓN MAYORISTA
    # =========================================================

    def activate_wholesale(self, purchase_total=None, purchase_date=None):
        """
        Activa por primera vez al cliente como mayorista.

        Después de la activación comienza un período de
        mantenimiento de 30 días.
        """

        purchase_date = (
            purchase_date
            or timezone.now()
        )

        self.commercial_status = (
            self.CommercialStatus.WHOLESALE_MAINTENANCE
        )

        self.wholesale_activated_at = (
            purchase_date
        )

        self.maintenance_deadline = (
            purchase_date
            + timedelta(days=30)
        )

        self.grace_started_at = None
        self.grace_deadline = None

        self.last_wholesale_purchase_at = (
            purchase_date
        )

        if purchase_total is not None:
            self.last_wholesale_purchase_total = (
                purchase_total
            )

        self.save()

    # =========================================================
    # MANTENIMIENTO
    # =========================================================

    def confirm_maintenance(self, purchase_total=None, purchase_date=None):
        """
        El cliente realizó la compra mínima requerida
        para mantener su condición mayorista.

        Reinicia un nuevo período de 30 días.
        """

        purchase_date = (
            purchase_date
            or timezone.now()
        )

        self.commercial_status = (
            self.CommercialStatus.WHOLESALE_ACTIVE
        )

        self.maintenance_deadline = (
            purchase_date
            + timedelta(days=30)
        )

        self.grace_started_at = None
        self.grace_deadline = None

        self.last_wholesale_purchase_at = (
            purchase_date
        )

        if purchase_total is not None:
            self.last_wholesale_purchase_total = (
                purchase_total
            )

        self.save()

    # =========================================================
    # PERÍODO DE GRACIA
    # =========================================================

    def start_grace_period(self):
        """
        Inicia el período adicional de gracia de 30 días.
        """

        now = timezone.now()

        self.commercial_status = (
            self.CommercialStatus.WHOLESALE_GRACE
        )

        self.grace_started_at = now

        self.grace_deadline = (
            now
            + timedelta(days=30)
        )

        self.save(
            update_fields=[
                'commercial_status',
                'grace_started_at',
                'grace_deadline',
                'updated_at',
            ]
        )

    def reactivate_from_grace(
        self,
        purchase_total=None,
        purchase_date=None
    ):
        """
        Reactiva al cliente después de cumplir
        la compra requerida durante el período de gracia.
        """

        purchase_date = (
            purchase_date
            or timezone.now()
        )

        self.commercial_status = (
            self.CommercialStatus.WHOLESALE_ACTIVE
        )

        self.maintenance_deadline = (
            purchase_date
            + timedelta(days=30)
        )

        self.grace_started_at = None
        self.grace_deadline = None

        self.last_wholesale_purchase_at = (
            purchase_date
        )

        if purchase_total is not None:
            self.last_wholesale_purchase_total = (
                purchase_total
            )

        self.save()

    # =========================================================
    # VENCIMIENTO
    # =========================================================

    def expire_wholesale(self):
        """
        Finaliza el beneficio mayorista.

        El historial de activación se conserva para efectos
        administrativos, pero el cliente vuelve a comprar
        con precios detal.
        """

        self.commercial_status = (
            self.CommercialStatus.WHOLESALE_EXPIRED
        )

        self.maintenance_deadline = None
        self.grace_started_at = None
        self.grace_deadline = None

        self.save(
            update_fields=[
                'commercial_status',
                'maintenance_deadline',
                'grace_started_at',
                'grace_deadline',
                'updated_at',
            ]
        )

    # =========================================================
    # ACTUALIZACIÓN TEMPORAL
    # =========================================================

    def refresh_commercial_status(self):
        """
        Revisa si los plazos comerciales ya vencieron.

        La evaluación real de compras se conectará después
        con los pedidos cuyo pago esté confirmado.
        """

        now = timezone.now()

        if (
            self.commercial_status
            in {
                self.CommercialStatus.WHOLESALE_MAINTENANCE,
                self.CommercialStatus.WHOLESALE_ACTIVE,
            }
            and self.maintenance_deadline
            and now > self.maintenance_deadline
        ):

            self.start_grace_period()

            return self.commercial_status

        if (
            self.commercial_status
            == self.CommercialStatus.WHOLESALE_GRACE
            and self.grace_deadline
            and now > self.grace_deadline
        ):

            self.expire_wholesale()

            return self.commercial_status

        return self.commercial_status