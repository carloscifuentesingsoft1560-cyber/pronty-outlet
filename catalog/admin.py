from django.contrib import admin

from .models import (
    Brand,
    Category,
    InventoryMovement,
    Product,
    ProductImage,
)


class ProductImageInline(admin.TabularInline):

    model = ProductImage
    extra = 1

    fields = (
        'image',
        'alt_text',
        'order',
        'is_active',
    )


class InventoryMovementInline(admin.TabularInline):

    model = InventoryMovement
    extra = 0

    fields = (
        'movement_type',
        'quantity',
        'previous_stock',
        'new_stock',
        'reason',
        'reference',
        'created_by',
        'created_at',
    )

    readonly_fields = (
        'movement_type',
        'quantity',
        'previous_stock',
        'new_stock',
        'reason',
        'reference',
        'created_by',
        'created_at',
    )

    can_delete = False

    show_change_link = True


    def has_add_permission(
        self,
        request,
        obj=None
    ):

        return False


# ============================================================
# CATEGORÍAS
# ============================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'slug',
        'is_active',
        'show_in_menu',
        'menu_order',
        'icon_name',
        'highlight_in_menu',
        'created_at',
    )

    list_editable = (
        'is_active',
        'show_in_menu',
        'menu_order',
        'highlight_in_menu',
    )

    list_filter = (
        'is_active',
        'show_in_menu',
        'highlight_in_menu',
    )

    search_fields = (
        'name',
        'slug',
    )

    prepopulated_fields = {
        'slug': (
            'name',
        )
    }

    fieldsets = (
        (
            'Categoría',
            {
                'fields': (
                    'name',
                    'slug',
                )
            }
        ),
        (
            'Visualización en la tienda',
            {
                'fields': (
                    'is_active',
                    'show_in_menu',
                    'menu_order',
                    'icon',
                    'highlight_in_menu',
                ),
                'description': (
                    'Configura cómo aparece esta categoría '
                    'en el menú principal de Pronty Outlet.'
                ),
            }
        ),
    )

    ordering = (
        'menu_order',
        'name',
    )


    @admin.display(
        description='Icono'
    )
    def icon_name(
        self,
        obj
    ):

        icon_labels = {
            Category.Icon.SPARKLES: (
                '✨ Brillos / maquillaje'
            ),
            Category.Icon.HEART: (
                '❤️ Corazón'
            ),
            Category.Icon.DROPLETS: (
                '💧 Gotas / cuidado personal'
            ),
            Category.Icon.SHIRT: (
                '👕 Ropa / moda'
            ),
            Category.Icon.BADGE_PERCENT: (
                '🏷️ Promoción / descuento'
            ),
            Category.Icon.GEM: (
                '💎 Accesorios / joyería'
            ),
            Category.Icon.TAG: (
                '🔖 Etiqueta'
            ),
            Category.Icon.SHOPPING_BAG: (
                '🛍️ Bolsa de compras'
            ),
            Category.Icon.GIFT: (
                '🎁 Regalo'
            ),
            Category.Icon.STAR: (
                '⭐ Estrella'
            ),
            Category.Icon.PALETTE: (
                '🎨 Belleza / colores'
            ),
            Category.Icon.CROWN: (
                '👑 Premium'
            ),
            Category.Icon.BABY: (
                '👶 Infantil / bebé'
            ),
            Category.Icon.WATCH: (
                '⌚ Relojes'
            ),
            Category.Icon.GLASSES: (
                '👓 Gafas'
            ),
            Category.Icon.FOOTPRINTS: (
                '👣 Calzado'
            ),
            Category.Icon.FLOWER: (
                '🌸 Floral / femenino'
            ),
            Category.Icon.SMILE: (
                '😊 Kawaii / divertido'
            ),
            Category.Icon.PACKAGE: (
                '📦 Otros productos'
            ),
        }

        return icon_labels.get(
            obj.icon,
            obj.icon
        )


# ============================================================
# MARCAS
# ============================================================

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'slug',
        'is_active',
        'created_at',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'name',
        'slug',
    )

    prepopulated_fields = {
        'slug': (
            'name',
        )
    }


# ============================================================
# PRODUCTOS
# ============================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'sku',
        'category',
        'brand',
        'retail_price',
        'wholesale_price',
        'stock',
        'is_new',
        'is_on_sale',
        'is_active',
    )

    list_filter = (
        'category',
        'brand',
        'is_new',
        'is_on_sale',
        'is_active',
    )

    search_fields = (
        'name',
        'sku',
        'category__name',
        'brand__name',
    )

    prepopulated_fields = {
        'slug': (
            'name',
        )
    }

    readonly_fields = (
        'stock',
        'created_at',
        'updated_at',
    )

    inlines = [
        ProductImageInline,
        InventoryMovementInline,
    ]


# ============================================================
# IMÁGENES DE PRODUCTO
# ============================================================

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):

    list_display = (
        'product',
        'order',
        'is_active',
        'created_at',
    )

    list_filter = (
        'is_active',
        'product',
    )

    search_fields = (
        'product__name',
        'alt_text',
    )

    ordering = (
        'product',
        'order',
    )


# ============================================================
# MOVIMIENTOS DE INVENTARIO
# ============================================================

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):

    list_display = (
        'product',
        'movement_type',
        'quantity',
        'previous_stock',
        'new_stock',
        'created_by',
        'created_at',
    )

    list_filter = (
        'movement_type',
        'created_at',
        'product',
    )

    search_fields = (
        'product__name',
        'product__sku',
        'reason',
        'reference',
    )

    readonly_fields = (
        'previous_stock',
        'new_stock',
        'created_by',
        'created_at',
    )

    ordering = (
        '-created_at',
    )

    fieldsets = (
        (
            'Movimiento',
            {
                'fields': (
                    'product',
                    'movement_type',
                    'quantity',
                )
            }
        ),
        (
            'Información adicional',
            {
                'fields': (
                    'reason',
                    'reference',
                )
            }
        ),
        (
            'Auditoría',
            {
                'fields': (
                    'previous_stock',
                    'new_stock',
                    'created_by',
                    'created_at',
                )
            }
        ),
    )


    def save_model(
        self,
        request,
        obj,
        form,
        change
    ):

        if not change:

            obj.created_by = (
                request.user
            )

        super().save_model(
            request,
            obj,
            form,
            change
        )


    def has_delete_permission(
        self,
        request,
        obj=None
    ):

        return False