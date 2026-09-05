from decimal import Decimal

from django.db import models

from catalog.models import Product


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING_PAYMENT = 'PENDING_PAYMENT', 'Pendiente de pago'
        PROOF_RECEIVED = 'PROOF_RECEIVED', 'Comprobante recibido'
        PAYMENT_CONFIRMED = 'PAYMENT_CONFIRMED', 'Pago confirmado'
        PREPARING = 'PREPARING', 'Preparando pedido'
        SHIPPED = 'SHIPPED', 'Enviado'
        DELIVERED = 'DELIVERED', 'Entregado'
        CHANGE_REQUESTED = 'CHANGE_REQUESTED', 'Cambio solicitado'
        CANCELED = 'CANCELED', 'Cancelado'
        RESERVATION_EXPIRED = 'RESERVATION_EXPIRED', 'Reserva vencida'

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
        verbose_name='Transportadora'
    )

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
        verbose_name='Total'
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
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number or f'Pedido {self.pk}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new and not self.order_number:
            self.order_number = (
                f'PRY-{self.created_at.year}-{self.pk:06d}'
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
        ordering = ['id']

    def __str__(self):
        return (
            f'{self.product_name} '
            f'x {self.quantity}'
        )