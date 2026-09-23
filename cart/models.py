from decimal import Decimal

from django.conf import settings
from django.db import models

from catalog.models import Product


class Order(models.Model):

    class Status(models.TextChoices):

        PENDING_PAYMENT = (
            'PENDING_PAYMENT',
            'Pendiente de pago'
        )

        PROOF_RECEIVED = (
            'PROOF_RECEIVED',
            'Comprobante recibido'
        )

        PAYMENT_PROCESSING = (
            'PAYMENT_PROCESSING',
            'Pago en proceso'
        )

        PAYMENT_CONFIRMED = (
            'PAYMENT_CONFIRMED',
            'Pago confirmado'
        )

        PAYMENT_DECLINED = (
            'PAYMENT_DECLINED',
            'Pago rechazado'
        )

        PREPARING = (
            'PREPARING',
            'Preparando pedido'
        )

        SHIPPED = (
            'SHIPPED',
            'Enviado'
        )

        DELIVERED = (
            'DELIVERED',
            'Entregado'
        )

        CHANGE_REQUESTED = (
            'CHANGE_REQUESTED',
            'Cambio solicitado'
        )

        RETURNED = (
            'RETURNED',
            'Devuelto'
        )

        CANCELED = (
            'CANCELED',
            'Cancelado'
        )

        RESERVATION_EXPIRED = (
            'RESERVATION_EXPIRED',
            'Reserva vencida'
        )


    class PaymentMethod(models.TextChoices):

        NEQUI = (
            'NEQUI',
            'Nequi'
        )

        BRE_B = (
            'BRE_B',
            'Llave Bre-B'
        )

        BANCOLOMBIA = (
            'BANCOLOMBIA',
            'Bancolombia'
        )


    class PaymentGateway(models.TextChoices):

        WOMPI = (
            'WOMPI',
            'Wompi'
        )


    class ReservationStatus(models.TextChoices):

        NOT_APPLICABLE = (
            'NOT_APPLICABLE',
            'No aplica'
        )

        ACTIVE = (
            'ACTIVE',
            'Reserva activa'
        )

        FINALIZED = (
            'FINALIZED',
            'Reserva convertida en venta'
        )

        RELEASED = (
            'RELEASED',
            'Reserva liberada'
        )


    class ReturnStatus(models.TextChoices):

        NOT_RETURNED = (
            'NOT_RETURNED',
            'Sin devolución'
        )

        PARTIAL = (
            'PARTIAL',
            'Devolución parcial'
        )

        FULL = (
            'FULL',
            'Devolución total'
        )


    # =========================================================
    # CUENTA DEL CLIENTE
    # =========================================================

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='orders',
        blank=True,
        null=True,
        verbose_name='Cuenta del cliente'
    )


    # =========================================================
    # PEDIDO
    # =========================================================

    order_number = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        verbose_name='Número de pedido'
    )

    customer_name = models.CharField(
        max_length=180,
        verbose_name='Nombre del cliente'
    )

    email = models.EmailField(
        verbose_name='Correo electrónico'
    )

    whatsapp = models.CharField(
        max_length=30,
        verbose_name='WhatsApp'
    )


    # =========================================================
    # ENTREGA
    # =========================================================

    department = models.CharField(
        max_length=120,
        verbose_name='Departamento'
    )

    city = models.CharField(
        max_length=120,
        verbose_name='Ciudad / municipio'
    )

    address = models.CharField(
        max_length=255,
        verbose_name='Dirección de entrega'
    )

    delivery_notes = models.TextField(
        blank=True,
        verbose_name='Indicaciones de entrega'
    )

    carrier = models.CharField(
        max_length=60,
        verbose_name='Transportadora solicitada'
    )


    # =========================================================
    # PAGO MANUAL
    # =========================================================

    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        blank=True,
        verbose_name='Método de pago'
    )

    payment_proof = models.ImageField(
        upload_to='payment_proofs/',
        blank=True,
        null=True,
        verbose_name='Comprobante de pago'
    )

    payment_proof_uploaded_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de carga del comprobante'
    )


    # =========================================================
    # PASARELA FUTURA
    # =========================================================

    payment_gateway = models.CharField(
        max_length=30,
        choices=PaymentGateway.choices,
        blank=True,
        default='',
        verbose_name='Pasarela de pago'
    )

    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Referencia de pago'
    )

    payment_transaction_id = models.CharField(
        max_length=150,
        blank=True,
        default='',
        verbose_name='ID de transacción'
    )

    payment_status = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='Estado en la pasarela'
    )

    payment_confirmed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de confirmación del pago'
    )


    # =========================================================
    # ACTIVACIÓN MAYORISTA
    # =========================================================

    retail_reference_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total de referencia a precio detal'
    )

    wholesale_activation_qualified = models.BooleanField(
        default=False,
        verbose_name='Calificó para activación mayorista'
    )


    # =========================================================
    # BENEFICIO COMERCIAL
    # =========================================================

    commercial_benefit_processed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de procesamiento comercial'
    )

    commercial_benefit_result = models.CharField(
        max_length=120,
        blank=True,
        default='',
        verbose_name='Resultado comercial'
    )


    # =========================================================
    # BENEFICIO DE ENVÍO
    # =========================================================

    free_shipping = models.BooleanField(
        default=False,
        verbose_name='Envío gratis'
    )

    shipping_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Costo de envío'
    )


    # =========================================================
    # RESERVA DEL PEDIDO
    # =========================================================

    reservation_expires_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha límite de reserva'
    )

    inventory_reservation_status = models.CharField(
        max_length=30,
        choices=ReservationStatus.choices,
        default=ReservationStatus.NOT_APPLICABLE,
        verbose_name='Estado de la reserva de inventario'
    )

    reservation_finalized_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de conversión a venta'
    )

    reservation_released_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de liberación de reserva'
    )


    # =========================================================
    # DEVOLUCIONES
    # =========================================================

    return_status = models.CharField(
        max_length=30,
        choices=ReturnStatus.choices,
        default=ReturnStatus.NOT_RETURNED,
        verbose_name='Estado de devolución'
    )

    returned_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de devolución'
    )

    return_reason = models.TextField(
        blank=True,
        default='',
        verbose_name='Motivo de devolución'
    )


    # =========================================================
    # DESPACHO
    # =========================================================

    shipping_carrier = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Transportadora de despacho'
    )

    tracking_number = models.CharField(
        max_length=120,
        blank=True,
        default='',
        verbose_name='Número de guía'
    )

    shipping_notes = models.TextField(
        blank=True,
        verbose_name='Observaciones de despacho'
    )

    shipped_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de envío'
    )

    delivered_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de entrega'
    )


    # =========================================================
    # ESTADO Y TOTAL
    # =========================================================

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        verbose_name='Estado'
    )

    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total de productos'
    )


    # =========================================================
    # FECHAS
    # =========================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )


    class Meta:

        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

        ordering = [
            '-created_at'
        ]


    def __str__(self):

        return (
            self.order_number
            or f'Pedido {self.pk}'
        )


    def save(
        self,
        *args,
        **kwargs
    ):

        is_new = (
            self.pk is None
        )

        super().save(
            *args,
            **kwargs
        )

        if (
            is_new
            and not self.order_number
        ):

            self.order_number = (
                f'PRY-'
                f'{self.created_at.year}-'
                f'{self.pk:06d}'
            )

            super().save(
                update_fields=[
                    'order_number'
                ]
            )


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Pedido'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='Producto'
    )

    product_name = models.CharField(
        max_length=180,
        verbose_name='Nombre del producto'
    )

    sku = models.CharField(
        max_length=60,
        verbose_name='SKU'
    )

    quantity = models.PositiveIntegerField(
        verbose_name='Cantidad'
    )

    returned_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name='Cantidad devuelta'
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Precio unitario'
    )

    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='Subtotal'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        verbose_name = 'Producto del pedido'
        verbose_name_plural = 'Productos del pedido'

        ordering = [
            'id'
        ]


    @property
    def returnable_quantity(self):

        return max(
            self.quantity
            - self.returned_quantity,
            0
        )


    @property
    def is_fully_returned(self):

        return (
            self.returned_quantity
            >= self.quantity
        )


    def __str__(self):

        return (
            f'{self.product_name} '
            f'x {self.quantity}'
        )


# ============================================================
# HISTORIAL DE DEVOLUCIONES
# ============================================================

class ReturnRecord(models.Model):

    class ReturnType(models.TextChoices):

        PARTIAL = (
            'PARTIAL',
            'Devolución parcial'
        )

        FULL = (
            'FULL',
            'Devolución total'
        )


    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='return_records',
        verbose_name='Pedido'
    )

    return_type = models.CharField(
        max_length=20,
        choices=ReturnType.choices,
        verbose_name='Tipo de devolución'
    )

    reason = models.TextField(
        blank=True,
        default='',
        verbose_name='Motivo de devolución'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='processed_return_records',
        blank=True,
        null=True,
        verbose_name='Procesado por'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de devolución'
    )


    class Meta:

        verbose_name = 'Registro de devolución'
        verbose_name_plural = 'Registros de devoluciones'

        ordering = [
            '-created_at',
            '-id',
        ]


    @property
    def total_units(self):

        return sum(
            item.quantity
            for item in ReturnRecordItem.objects.filter(
                return_record=self
            )
        )


    def __str__(self):

        if self.return_type == self.ReturnType.FULL:
            return_type_display = 'Devolución total'
        else:
            return_type_display = 'Devolución parcial'

        return (
        f'{return_type_display} - '
        f'{self.order.order_number}'
        )


class ReturnRecordItem(models.Model):

    return_record = models.ForeignKey(
        ReturnRecord,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Devolución'
    )

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.SET_NULL,
        related_name='return_record_items',
        blank=True,
        null=True,
        verbose_name='Producto original del pedido'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        related_name='return_record_items',
        blank=True,
        null=True,
        verbose_name='Producto'
    )

    product_name = models.CharField(
        max_length=180,
        verbose_name='Nombre del producto'
    )

    sku = models.CharField(
        max_length=60,
        verbose_name='SKU'
    )

    quantity = models.PositiveIntegerField(
        verbose_name='Cantidad devuelta'
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Precio unitario'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de registro'
    )


    class Meta:

        verbose_name = 'Producto de devolución'
        verbose_name_plural = 'Productos de devolución'

        ordering = [
            'id'
        ]


    @property
    def subtotal(self):

        return (
            self.unit_price
            * self.quantity
        )


    def __str__(self):

        return (
            f'{self.product_name} '
            f'x {self.quantity}'
        )