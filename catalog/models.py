from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction


class Category(models.Model):
    name = models.CharField(
        max_length=120,
        unique=True,
        verbose_name='Nombre'
    )

    slug = models.SlugField(
        max_length=140,
        unique=True
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(
        max_length=120,
        unique=True,
        verbose_name='Nombre'
    )

    slug = models.SlugField(
        max_length=140,
        unique=True
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        max_length=180,
        verbose_name='Nombre'
    )

    slug = models.SlugField(
        max_length=200,
        unique=True
    )

    sku = models.CharField(
        max_length=60,
        unique=True,
        verbose_name='Código / SKU'
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='Categoría'
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='Marca',
        null=True,
        blank=True
    )

    short_description = models.CharField(
        max_length=280,
        blank=True,
        verbose_name='Descripción corta'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )

    retail_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Precio detal'
    )

    wholesale_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Precio mayorista'
    )

    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Costo interno'
    )

    stock = models.PositiveIntegerField(
        default=0,
        verbose_name='Existencias'
    )

    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name='Imagen principal'
    )

    is_new = models.BooleanField(
        default=False,
        verbose_name='Nuevo'
    )

    is_on_sale = models.BooleanField(
        default=False,
        verbose_name='En promoción'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return 0 < self.stock <= 5

    @property
    def is_out_of_stock(self):
        return self.stock == 0


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Producto'
    )

    image = models.ImageField(
        upload_to='products/gallery/',
        verbose_name='Imagen'
    )

    alt_text = models.CharField(
        max_length=180,
        blank=True,
        verbose_name='Texto alternativo'
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Imagen de producto'
        verbose_name_plural = 'Imágenes de producto'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.product.name} - imagen {self.pk}'


class InventoryMovement(models.Model):

    class MovementType(models.TextChoices):
        ENTRY = 'ENTRY', 'Entrada de inventario'
        SALE = 'SALE', 'Venta'
        RETURN = 'RETURN', 'Devolución'
        ADJUSTMENT_IN = 'ADJUSTMENT_IN', 'Ajuste positivo'
        ADJUSTMENT_OUT = 'ADJUSTMENT_OUT', 'Ajuste negativo'

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='inventory_movements',
        verbose_name='Producto'
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
        verbose_name='Tipo de movimiento'
    )

    quantity = models.PositiveIntegerField(
        verbose_name='Cantidad'
    )

    previous_stock = models.PositiveIntegerField(
        default=0,
        editable=False,
        verbose_name='Existencias anteriores'
    )

    new_stock = models.PositiveIntegerField(
        default=0,
        editable=False,
        verbose_name='Existencias nuevas'
    )

    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Motivo / observación'
    )

    reference = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Referencia'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_movements',
        verbose_name='Registrado por'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha'
    )

    class Meta:
        verbose_name = 'Movimiento de inventario'
        verbose_name_plural = 'Movimientos de inventario'
        ordering = ['-created_at', '-id']

    def __str__(self):

        if self.movement_type == self.MovementType.ENTRY:
            movement_label = 'Entrada de inventario'

        elif self.movement_type == self.MovementType.SALE:
            movement_label = 'Venta'

        elif self.movement_type == self.MovementType.RETURN:
            movement_label = 'Devolución'

        elif self.movement_type == self.MovementType.ADJUSTMENT_IN:
            movement_label = 'Ajuste positivo'

        elif self.movement_type == self.MovementType.ADJUSTMENT_OUT:
            movement_label = 'Ajuste negativo'

        else:
            movement_label = self.movement_type

        return (
            f'{self.product.name} - '
            f'{movement_label} - '
            f'{self.quantity}'
        )

    @property
    def is_incoming(self):
        return self.movement_type in {
            self.MovementType.ENTRY,
            self.MovementType.RETURN,
            self.MovementType.ADJUSTMENT_IN,
        }

    @property
    def is_outgoing(self):
        return self.movement_type in {
            self.MovementType.SALE,
            self.MovementType.ADJUSTMENT_OUT,
        }

    def clean(self):
        super().clean()

        if self.quantity <= 0:
            raise ValidationError({
                'quantity': 'La cantidad debe ser mayor que cero.'
            })

    def save(self, *args, **kwargs):

        # Si el movimiento ya existe, no volver a modificar inventario.
        if self.pk:
            return super().save(*args, **kwargs)

        self.full_clean()

        with transaction.atomic():

            product = Product.objects.select_for_update().get(
                pk=self.product.pk
            )

            self.previous_stock = product.stock

            if self.is_incoming:

                resulting_stock = (
                    product.stock + self.quantity
                )

            elif self.is_outgoing:

                if self.quantity > product.stock:
                    raise ValidationError(
                        'No hay existencias suficientes para '
                        'registrar esta salida.'
                    )

                resulting_stock = (
                    product.stock - self.quantity
                )

            else:
                raise ValidationError(
                    'Tipo de movimiento de inventario inválido.'
                )

            self.new_stock = resulting_stock

            product.stock = resulting_stock

            product.save(
                update_fields=[
                    'stock',
                    'updated_at',
                ]
            )

            super().save(*args, **kwargs)