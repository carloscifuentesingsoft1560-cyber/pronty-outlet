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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
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
        'slug': ('name',)
    }


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
        'slug': ('name',)
    }


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
        'slug': ('name',)
    }

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    inlines = [
        ProductImageInline,
    ]


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
            obj.created_by = request.user

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