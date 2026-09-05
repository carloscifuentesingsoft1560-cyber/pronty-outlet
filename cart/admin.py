from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False

    fields = (
        'product',
        'product_name',
        'sku',
        'quantity',
        'unit_price',
        'subtotal',
    )

    readonly_fields = (
        'product',
        'product_name',
        'sku',
        'quantity',
        'unit_price',
        'subtotal',
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'order_number',
        'customer_name',
        'whatsapp',
        'city',
        'status',
        'total',
        'created_at',
    )

    list_filter = (
        'status',
        'department',
        'carrier',
        'created_at',
    )

    search_fields = (
        'order_number',
        'customer_name',
        'email',
        'whatsapp',
        'city',
        'address',
    )

    readonly_fields = (
        'order_number',
        'customer_name',
        'email',
        'whatsapp',
        'department',
        'city',
        'address',
        'delivery_notes',
        'carrier',
        'total',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (
            'Pedido',
            {
                'fields': (
                    'order_number',
                    'status',
                    'total',
                )
            }
        ),
        (
            'Cliente',
            {
                'fields': (
                    'customer_name',
                    'email',
                    'whatsapp',
                )
            }
        ),
        (
            'Entrega',
            {
                'fields': (
                    'department',
                    'city',
                    'address',
                    'delivery_notes',
                    'carrier',
                )
            }
        ),
        (
            'Fechas',
            {
                'fields': (
                    'created_at',
                    'updated_at',
                )
            }
        ),
    )

    inlines = [
        OrderItemInline,
    ]

    ordering = (
        '-created_at',
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        'order',
        'product_name',
        'sku',
        'quantity',
        'unit_price',
        'subtotal',
    )

    search_fields = (
        'order__order_number',
        'product_name',
        'sku',
    )

    readonly_fields = (
        'order',
        'product',
        'product_name',
        'sku',
        'quantity',
        'unit_price',
        'subtotal',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False