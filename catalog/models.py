from django.db import models


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
        verbose_name='Stock'
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