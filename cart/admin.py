from django.contrib import admin, messages
from django.utils import timezone

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

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'order_number',
        'customer_name',
        'whatsapp',
        'city',
        'payment_method',
        'status',
        'tracking_number',
        'total',
        'created_at',
    )

    list_filter = (
        'status',
        'payment_method',
        'department',
        'carrier',
        'shipping_carrier',
        'created_at',
    )

    search_fields = (
        'order_number',
        'customer_name',
        'email',
        'whatsapp',
        'city',
        'address',
        'tracking_number',
        'shipping_carrier',
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
        'payment_proof_uploaded_at',
        'payment_confirmed_at',
        'shipped_at',
        'delivered_at',
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
            'Entrega solicitada',
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
            'Pago manual',
            {
                'fields': (
                    'payment_method',
                    'payment_proof',
                    'payment_proof_uploaded_at',
                    'payment_confirmed_at',
                )
            }
        ),
        (
            'Despacho',
            {
                'fields': (
                    'shipping_carrier',
                    'tracking_number',
                    'shipping_notes',
                    'shipped_at',
                    'delivered_at',
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

    actions = [
        'confirm_payment',
        'reject_payment',
        'mark_preparing',
        'mark_shipped',
        'mark_delivered',
    ]

    @admin.action(
        description='Confirmar pago de pedidos seleccionados'
    )
    def confirm_payment(self, request, queryset):

        updated = 0

        for order in queryset:

            if order.status != Order.Status.PROOF_RECEIVED:
                continue

            order.status = Order.Status.PAYMENT_CONFIRMED
            order.payment_confirmed_at = timezone.now()

            order.save(
                update_fields=[
                    'status',
                    'payment_confirmed_at',
                    'updated_at',
                ]
            )

            updated += 1

        if updated:
            self.message_user(
                request,
                f'{updated} pedido(s) marcado(s) como pago confirmado.',
                level=messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                (
                    'No se modificaron pedidos. '
                    'Solo se pueden confirmar pedidos con '
                    'estado "Comprobante recibido".'
                ),
                level=messages.WARNING
            )

    @admin.action(
        description='Rechazar pago de pedidos seleccionados'
    )
    def reject_payment(self, request, queryset):

        updated = 0

        for order in queryset:

            if order.status != Order.Status.PROOF_RECEIVED:
                continue

            order.status = Order.Status.PAYMENT_DECLINED
            order.payment_confirmed_at = None

            order.save(
                update_fields=[
                    'status',
                    'payment_confirmed_at',
                    'updated_at',
                ]
            )

            updated += 1

        if updated:
            self.message_user(
                request,
                f'{updated} pedido(s) marcado(s) como pago rechazado.',
                level=messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                (
                    'No se modificaron pedidos. '
                    'Solo se pueden rechazar pedidos con '
                    'estado "Comprobante recibido".'
                ),
                level=messages.WARNING
            )

    @admin.action(
        description='Marcar pedidos seleccionados como preparando'
    )
    def mark_preparing(self, request, queryset):

        updated = 0

        for order in queryset:

            if order.status != Order.Status.PAYMENT_CONFIRMED:
                continue

            order.status = Order.Status.PREPARING

            order.save(
                update_fields=[
                    'status',
                    'updated_at',
                ]
            )

            updated += 1

        if updated:
            self.message_user(
                request,
                f'{updated} pedido(s) marcado(s) como preparando.',
                level=messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                (
                    'No se modificaron pedidos. '
                    'Solo se pueden preparar pedidos con '
                    'estado "Pago confirmado".'
                ),
                level=messages.WARNING
            )

    @admin.action(
        description='Marcar pedidos seleccionados como enviados'
    )
    def mark_shipped(self, request, queryset):

        updated = 0
        missing_shipping_data = 0

        for order in queryset:

            if order.status != Order.Status.PREPARING:
                continue

            if not order.shipping_carrier or not order.tracking_number:
                missing_shipping_data += 1
                continue

            order.status = Order.Status.SHIPPED
            order.shipped_at = timezone.now()

            order.save(
                update_fields=[
                    'status',
                    'shipped_at',
                    'updated_at',
                ]
            )

            updated += 1

        if updated:
            self.message_user(
                request,
                f'{updated} pedido(s) marcado(s) como enviados.',
                level=messages.SUCCESS
            )

        if missing_shipping_data:
            self.message_user(
                request,
                (
                    f'{missing_shipping_data} pedido(s) no se enviaron '
                    'porque les falta transportadora de despacho '
                    'o número de guía.'
                ),
                level=messages.WARNING
            )

        if not updated and not missing_shipping_data:
            self.message_user(
                request,
                (
                    'No se modificaron pedidos. '
                    'Solo se pueden enviar pedidos con '
                    'estado "Preparando pedido".'
                ),
                level=messages.WARNING
            )

    @admin.action(
        description='Marcar pedidos seleccionados como entregados'
    )
    def mark_delivered(self, request, queryset):

        updated = 0

        for order in queryset:

            if order.status != Order.Status.SHIPPED:
                continue

            order.status = Order.Status.DELIVERED
            order.delivered_at = timezone.now()

            order.save(
                update_fields=[
                    'status',
                    'delivered_at',
                    'updated_at',
                ]
            )

            updated += 1

        if updated:
            self.message_user(
                request,
                f'{updated} pedido(s) marcado(s) como entregados.',
                level=messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                (
                    'No se modificaron pedidos. '
                    'Solo se pueden entregar pedidos con '
                    'estado "Enviado".'
                ),
                level=messages.WARNING
            )

    def save_model(
        self,
        request,
        obj,
        form,
        change
    ):

        previous_status = None

        if change and obj.pk:

            previous_order = Order.objects.filter(
                pk=obj.pk
            ).first()

            if previous_order:
                previous_status = previous_order.status

        if (
            obj.status == Order.Status.PAYMENT_CONFIRMED
            and previous_status != Order.Status.PAYMENT_CONFIRMED
        ):
            obj.payment_confirmed_at = timezone.now()

        if (
            obj.status != Order.Status.PAYMENT_CONFIRMED
            and previous_status == Order.Status.PAYMENT_CONFIRMED
        ):
            obj.payment_confirmed_at = None

        if (
            obj.status == Order.Status.SHIPPED
            and previous_status != Order.Status.SHIPPED
        ):
            obj.shipped_at = timezone.now()

        if (
            obj.status == Order.Status.DELIVERED
            and previous_status != Order.Status.DELIVERED
        ):
            obj.delivered_at = timezone.now()

        super().save_model(
            request,
            obj,
            form,
            change
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