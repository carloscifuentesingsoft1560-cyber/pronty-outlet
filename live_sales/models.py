import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# ============================================================
# ACCESO DEL CLIENTE A PRONTY LIVE
# ============================================================

class LiveCustomerAccess(models.Model):

    ACTIVATION_AMOUNT = Decimal('20000.00')


    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='live_access',
        verbose_name='Cliente'
    )

    customer_code = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        verbose_name='Código permanente del cliente'
    )

    is_activated = models.BooleanField(
        default=False,
        verbose_name='Live activado'
    )

    activation_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=ACTIVATION_AMOUNT,
        verbose_name='Valor de activación'
    )

    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de activación'
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

        verbose_name = 'Acceso a Pronty Live'
        verbose_name_plural = 'Accesos a Pronty Live'

        ordering = [
            'customer_code'
        ]


    def __str__(self):

        try:
            user = self.user

        except Exception:
            user = None


        if not user:

            return (
                self.customer_code
                or 'Acceso Pronty Live'
            )


        customer_name = (
            user.get_full_name().strip()
            or user.username
        )


        return (
            f'{self.customer_code} - '
            f'{customer_name}'
        )


    def save(
        self,
        *args,
        **kwargs
    ):

        try:
            user = self.user

        except Exception:
            user = None


        # ====================================================
        # GENERAR CÓDIGO PERMANENTE
        # ====================================================

        if (
            not self.customer_code
            and user
            and user.pk
        ):

            self.customer_code = (
                f'PRY-C{user.pk:06d}'
            )


        # ====================================================
        # FECHA DE ACTIVACIÓN
        # ====================================================

        if (
            self.is_activated
            and not self.activated_at
        ):

            self.activated_at = (
                timezone.now()
            )


        super().save(
            *args,
            **kwargs
        )


    @property
    def can_participate_in_live(self):

        return self.is_activated


# ============================================================
# SESIÓN DE LIVE
# ============================================================

class LiveSession(models.Model):

    class Platform(models.TextChoices):

        TIKTOK = (
            'TIKTOK',
            'TikTok'
        )

        INSTAGRAM = (
            'INSTAGRAM',
            'Instagram'
        )

        FACEBOOK = (
            'FACEBOOK',
            'Facebook'
        )

        MIXED = (
            'MIXED',
            'Multiplataforma'
        )


    class Status(models.TextChoices):

        SCHEDULED = (
            'SCHEDULED',
            'Programado'
        )

        LIVE = (
            'LIVE',
            'En vivo'
        )

        CLOSED = (
            'CLOSED',
            'Finalizado'
        )

        CANCELED = (
            'CANCELED',
            'Cancelado'
        )


    name = models.CharField(
        max_length=180,
        verbose_name='Nombre del live'
    )

    platform = models.CharField(
        max_length=20,
        choices=Platform.choices,
        default=Platform.TIKTOK,
        verbose_name='Plataforma'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        verbose_name='Estado'
    )

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha programada'
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Inicio real'
    )

    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fin real'
    )

    notes = models.TextField(
        blank=True,
        verbose_name='Observaciones'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_live_sessions',
        verbose_name='Creado por'
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

        verbose_name = 'Live'
        verbose_name_plural = 'Lives'

        ordering = [
            '-scheduled_at',
            '-created_at',
        ]


    def __str__(self):

        return self.name


# ============================================================
# QR PERMANENTE DEL PRODUCTO
# ============================================================

class LiveProductQR(models.Model):

    product = models.OneToOneField(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='live_qr',
        verbose_name='Producto'
    )

    code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Código QR'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='QR activo'
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

        verbose_name = 'QR de producto para Live'
        verbose_name_plural = 'QR de productos para Live'

        ordering = [
            'product__name'
        ]


    def __str__(self):

        return (
            f'{self.product.sku} - '
            f'{self.product.name}'
        )


# ============================================================
# PRODUCTO HABILITADO DENTRO DE UN LIVE
# ============================================================

class LiveSessionProduct(models.Model):

    live_session = models.ForeignKey(
        LiveSession,
        on_delete=models.CASCADE,
        related_name='session_products',
        verbose_name='Live'
    )

    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.PROTECT,
        related_name='live_session_products',
        verbose_name='Producto'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Disponible en este live'
    )

    live_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Precio especial del live'
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

        verbose_name = 'Producto del Live'
        verbose_name_plural = 'Productos del Live'

        ordering = [
            'product__name'
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'live_session',
                    'product',
                ],
                name=(
                    'unique_product_per_live_session'
                )
            )
        ]


    def __str__(self):

        return (
            f'{self.live_session.name} - '
            f'{self.product.name}'
        )


    @property
    def effective_price(self):

        if self.live_price is not None:

            return self.live_price

        return self.product.retail_price


# ============================================================
# ASIGNACIÓN DE PRODUCTO A CLIENTE DURANTE EL LIVE
# ============================================================

class LiveAssignment(models.Model):

    class Status(models.TextChoices):

        ASSIGNED = (
            'ASSIGNED',
            'Asignado'
        )

        ORDERED = (
            'ORDERED',
            'Convertido en pedido'
        )

        RELEASED = (
            'RELEASED',
            'Liberado'
        )


    live_session = models.ForeignKey(
        LiveSession,
        on_delete=models.PROTECT,
        related_name='assignments',
        verbose_name='Live'
    )

    customer = models.ForeignKey(
        LiveCustomerAccess,
        on_delete=models.PROTECT,
        related_name='assignments',
        verbose_name='Cliente'
    )

    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.PROTECT,
        related_name='live_assignments',
        verbose_name='Producto'
    )

    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Cantidad'
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Precio unitario asignado'
    )

    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Costo unitario registrado'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ASSIGNED,
        verbose_name='Estado'
    )

    order = models.ForeignKey(
        'cart.Order',
        on_delete=models.PROTECT,
        related_name='live_assignments',
        null=True,
        blank=True,
        verbose_name='Pedido generado'
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de asignación'
    )

    released_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de liberación'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='live_assignments_created',
        verbose_name='Asignado por'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )


    class Meta:

        verbose_name = 'Asignación de Live'
        verbose_name_plural = 'Asignaciones de Live'

        ordering = [
            '-assigned_at',
            '-id',
        ]


    def __str__(self):

        try:
            live_name = (
                self.live_session.name
            )

        except Exception:
            live_name = 'Live'


        try:
            customer_code = (
                self.customer.customer_code
            )

        except Exception:
            customer_code = 'Cliente'


        try:
            product_name = (
                self.product.name
            )

        except Exception:
            product_name = 'Producto'


        return (
            f'{live_name} - '
            f'{customer_code} - '
            f'{product_name}'
        )


    # ========================================================
    # VALIDACIONES
    # ========================================================

    def clean(self):

        super().clean()


        # ====================================================
        # CANTIDAD
        # ====================================================

        if (
            self.quantity is None
            or self.quantity <= 0
        ):

            raise ValidationError({
                'quantity': (
                    'La cantidad debe ser mayor que cero.'
                )
            })


        # ====================================================
        # CLIENTE
        # ====================================================

        try:
            customer = self.customer

        except Exception:
            customer = None


        if (
            customer
            and not customer.is_activated
        ):

            raise ValidationError({
                'customer': (
                    'El cliente no tiene activado '
                    'Pronty Live.'
                )
            })


        # ====================================================
        # LIVE
        # ====================================================

        try:
            live_session = (
                self.live_session
            )

        except Exception:
            live_session = None


        if (
            live_session
            and live_session.status
            == LiveSession.Status.CANCELED
        ):

            raise ValidationError({
                'live_session': (
                    'No se pueden realizar asignaciones '
                    'en un Live cancelado.'
                )
            })


        # ====================================================
        # PEDIDO
        # ====================================================

        try:
            order = self.order

        except Exception:
            order = None


        if (
            self.status
            == self.Status.ORDERED
            and not order
        ):

            raise ValidationError({
                'order': (
                    'Una asignación convertida en pedido '
                    'debe estar vinculada a un pedido.'
                )
            })


        if (
            self.status
            != self.Status.ORDERED
            and order
        ):

            raise ValidationError({
                'order': (
                    'Solo una asignación convertida '
                    'en pedido puede tener un pedido asociado.'
                )
            })


    # ========================================================
    # VALORES CALCULADOS
    # ========================================================

    @property
    def subtotal(self):

        if (
            self.unit_price is None
            or self.quantity is None
        ):

            return Decimal('0.00')


        return (
            self.unit_price
            * self.quantity
        )


    @property
    def total_cost(self):

        if (
            self.unit_cost is None
            or self.quantity is None
        ):

            return Decimal('0.00')


        return (
            self.unit_cost
            * self.quantity
        )


    @property
    def gross_profit(self):

        return (
            self.subtotal
            - self.total_cost
        )


    @property
    def gross_margin_percentage(self):

        subtotal = self.subtotal


        if subtotal <= 0:

            return Decimal('0.00')


        return (
            (
                self.gross_profit
                / subtotal
            )
            * Decimal('100.00')
        )