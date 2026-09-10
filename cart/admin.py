from django.contrib import admin, messages
from django.utils import timezone

from accounts.services import process_wholesale_benefit

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem

    extra = 0

    can_delete = False

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
        'city',
        'payment_method',
        'status',
        'total',
        'free_shipping',
        'wholesale_activation_qualified',
        'created_at',
    )

    list_filter = (
        'status',
        'payment_method',
        'free_shipping',
        'wholesale_activation_qualified',
        'created_at',
    )

    search_fields = (
        'order_number',
        'customer_name',
        'email',
        'whatsapp',
        'tracking_number',
    )

    readonly_fields = (
        'order_number',
        'customer',
        'total',
        'retail_reference_total',
        'wholesale_activation_qualified',
        'free_shipping',
        'commercial_benefit_processed_at',
        'commercial_benefit_result',
        'payment_proof_uploaded_at',
        'payment_confirmed_at',
        'shipped_at',
        'delivered_at',
        'created_at',
        'updated_at',
    )

    fieldsets = (

        (
            'Pedido',
            {
                'fields': (
                    'order_number',
                    'customer',
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
            'Activación mayorista',
            {
                'fields': (
                    'retail_reference_total',
                    'wholesale_activation_qualified',
                )
            }
        ),

        (
            'Beneficio de envío',
            {
                'fields': (
                    'free_shipping',
                    'shipping_cost',
                )
            }
        ),

        (
            'Beneficio comercial',
            {
                'fields': (
                    'commercial_benefit_processed_at',
                    'commercial_benefit_result',
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

    inlines = (
        OrderItemInline,
    )

    actions = (
        'confirm_payment',
        'reject_payment',
        'mark_as_preparing',
        'mark_as_shipped',
        'mark_as_delivered',
    )


    @admin.action(
        description='Confirmar pago de pedidos seleccionados'
    )
    def confirm_payment(
        self,
        request,
        queryset
    ):

        confirmed = 0
        skipped = 0

        for order in queryset:

            if (
                order.status
                != Order.Status.PROOF_RECEIVED
            ):

                skipped += 1
                continue

            order.status = (
                Order.Status.PAYMENT_CONFIRMED
            )

            order.payment_confirmed_at = (
                timezone.now()
            )

            order.save(
                update_fields=[
                    'status',
                    'payment_confirmed_at',
                    'updated_at',
                ]
            )

            process_wholesale_benefit(
                order
            )

            confirmed += 1

        if confirmed:

            self.message_user(
                request,
                (
                    f'{confirmed} pedido(s) '
                    f'confirmado(s) correctamente.'
                ),
                level=messages.SUCCESS
            )

        if skipped:

            self.message_user(
                request,
                (
                    f'{skipped} pedido(s) '
                    f'no estaban en estado '
                    f'"Comprobante recibido".'
                ),
                level=messages.WARNING
            )


    @admin.action(
        description='Rechazar pago de pedidos seleccionados'
    )
    def reject_payment(
        self,
        request,
        queryset
    ):

        updated = 0
        skipped = 0

        for order in queryset:

            if (
                order.status
                != Order.Status.PROOF_RECEIVED
            ):

                skipped += 1
                continue

            order.status = (
                Order.Status.PAYMENT_DECLINED
            )

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
                (
                    f'{updated} pedido(s) '
                    f'marcado(s) como pago rechazado.'
                ),
                level=messages.SUCCESS
            )

        if skipped:

            self.message_user(
                request,
                (
                    f'{skipped} pedido(s) '
                    f'no estaban en estado '
                    f'"Comprobante recibido".'
                ),
                level=messages.WARNING
            )


    @admin.action(
        description='Marcar pedidos seleccionados como preparando'
    )
    def mark_as_preparing(
        self,
        request,
        queryset
    ):

        updated = queryset.filter(
            status=Order.Status.PAYMENT_CONFIRMED
        ).update(
            status=Order.Status.PREPARING,
            updated_at=timezone.now()
        )

        self.message_user(
            request,
            (
                f'{updated} pedido(s) '
                f'marcado(s) como preparando.'
            ),
            level=messages.SUCCESS
        )


    @admin.action(
        description='Marcar pedidos seleccionados como enviados'
    )
    def mark_as_shipped(
        self,
        request,
        queryset
    ):

        updated = 0
        skipped = 0

        for order in queryset:

            if (
                order.status
                != Order.Status.PREPARING
            ):

                skipped += 1
                continue

            if (
                not order.shipping_carrier
                or not order.tracking_number
            ):

                skipped += 1
                continue

            order.status = (
                Order.Status.SHIPPED
            )

            order.shipped_at = (
                timezone.now()
            )

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
                (
                    f'{updated} pedido(s) '
                    f'marcado(s) como enviado(s).'
                ),
                level=messages.SUCCESS
            )

        if skipped:

            self.message_user(
                request,
                (
                    f'{skipped} pedido(s) '
                    f'no pudieron marcarse como enviados. '
                    f'Deben estar en "Preparando pedido" '
                    f'y tener transportadora y guía.'
                ),
                level=messages.WARNING
            )


    @admin.action(
        description='Marcar pedidos seleccionados como entregados'
    )
    def mark_as_delivered(
        self,
        request,
        queryset
    ):

        updated = 0
        skipped = 0

        for order in queryset:

            if (
                order.status
                != Order.Status.SHIPPED
            ):

                skipped += 1
                continue

            order.status = (
                Order.Status.DELIVERED
            )

            order.delivered_at = (
                timezone.now()
            )

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
                (
                    f'{updated} pedido(s) '
                    f'marcado(s) como entregado(s).'
                ),
                level=messages.SUCCESS
            )

        if skipped:

            self.message_user(
                request,
                (
                    f'{skipped} pedido(s) '
                    f'no estaban en estado "Enviado".'
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

            previous_status = (
                Order.objects
                .filter(
                    pk=obj.pk
                )
                .values_list(
                    'status',
                    flat=True
                )
                .first()
            )

        if (
            obj.status
            == Order.Status.PAYMENT_CONFIRMED
            and previous_status
            != Order.Status.PAYMENT_CONFIRMED
        ):

            if not obj.payment_confirmed_at:

                obj.payment_confirmed_at = (
                    timezone.now()
                )

        statuses_without_confirmed_payment = {
            Order.Status.PENDING_PAYMENT,
            Order.Status.PROOF_RECEIVED,
            Order.Status.PAYMENT_PROCESSING,
            Order.Status.PAYMENT_DECLINED,
            Order.Status.CANCELED,
            Order.Status.RESERVATION_EXPIRED,
        }

        if (
            obj.status
            in statuses_without_confirmed_payment
        ):

            obj.payment_confirmed_at = None

        if (
            obj.status
            == Order.Status.SHIPPED
            and not obj.shipped_at
        ):

            obj.shipped_at = (
                timezone.now()
            )

        if (
            obj.status
            == Order.Status.DELIVERED
            and not obj.delivered_at
        ):

            obj.delivered_at = (
                timezone.now()
            )

        super().save_model(
            request,
            obj,
            form,
            change
        )

        if (
            obj.status
            == Order.Status.PAYMENT_CONFIRMED
            and previous_status
            != Order.Status.PAYMENT_CONFIRMED
        ):

            process_wholesale_benefit(
                obj
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