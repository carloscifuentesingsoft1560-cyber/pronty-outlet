from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone

from accounts.services import process_wholesale_benefit

from .models import Order, OrderItem
from .reservation_services import (
    cancel_unpaid_order,
    finalize_inventory_reservation,
    process_full_return,
)


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
        'inventory_reservation_status',
        'return_status',
        'total',
        'free_shipping',
        'wholesale_activation_qualified',
        'created_at',
    )

    list_filter = (
        'status',
        'inventory_reservation_status',
        'return_status',
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
        'reservation_expires_at',
        'inventory_reservation_status',
        'reservation_finalized_at',
        'reservation_released_at',
        'return_status',
        'returned_at',
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
            'Reserva de inventario',
            {
                'fields': (
                    'inventory_reservation_status',
                    'reservation_expires_at',
                    'reservation_finalized_at',
                    'reservation_released_at',
                )
            }
        ),

        (
            'Devoluciones',
            {
                'fields': (
                    'return_status',
                    'returned_at',
                    'return_reason',
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
        'cancel_unpaid_orders',
        'process_full_returns',
        'mark_as_preparing',
        'mark_as_shipped',
        'mark_as_delivered',
    )


    # ========================================================
    # CONFIRMAR PAGO
    # ========================================================

    @admin.action(
        description='Confirmar pago de pedidos seleccionados'
    )
    def confirm_payment(
        self,
        request,
        queryset
    ):

        confirmed = 0
        skipped_status = 0
        skipped_reservation = 0

        reservation_errors = []

        for selected_order in queryset:

            benefit_order = None

            with transaction.atomic():

                order = (
                    Order.objects
                    .select_for_update()
                    .get(
                        pk=selected_order.pk
                    )
                )

                if (
                    order.status
                    != Order.Status.PROOF_RECEIVED
                ):

                    skipped_status += 1
                    continue

                (
                    reservation_ok,
                    reservation_message
                ) = finalize_inventory_reservation(
                    order
                )

                if not reservation_ok:

                    skipped_reservation += 1

                    reservation_errors.append(
                        (
                            f'{order.order_number}: '
                            f'{reservation_message}'
                        )
                    )

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

                benefit_order = order

            if benefit_order is not None:

                process_wholesale_benefit(
                    benefit_order
                )

                confirmed += 1

        if confirmed:

            self.message_user(
                request,
                (
                    f'{confirmed} pedido(s) '
                    f'confirmado(s) correctamente. '
                    f'Las reservas fueron convertidas '
                    f'en ventas sin descontar nuevamente '
                    f'el inventario.'
                ),
                level=messages.SUCCESS
            )

        if skipped_status:

            self.message_user(
                request,
                (
                    f'{skipped_status} pedido(s) '
                    f'no estaban en estado '
                    f'"Comprobante recibido".'
                ),
                level=messages.WARNING
            )

        if skipped_reservation:

            self.message_user(
                request,
                (
                    f'{skipped_reservation} pedido(s) '
                    f'no pudieron confirmarse por problemas '
                    f'con la reserva de inventario.'
                ),
                level=messages.ERROR
            )

        for error in reservation_errors:

            self.message_user(
                request,
                error,
                level=messages.ERROR
            )


    # ========================================================
    # RECHAZAR PAGO
    # ========================================================

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
                    f'marcado(s) como pago rechazado. '
                    f'La reserva de inventario se mantiene.'
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


    # ========================================================
    # CANCELAR PEDIDOS SIN PAGO
    # ========================================================

    @admin.action(
        description=(
            'Cancelar pedidos sin pago y liberar reserva'
        )
    )
    def cancel_unpaid_orders(
        self,
        request,
        queryset
    ):

        canceled = 0
        skipped = 0
        errors = []

        for selected_order in queryset:

            with transaction.atomic():

                order = (
                    Order.objects
                    .select_for_update()
                    .get(
                        pk=selected_order.pk
                    )
                )

                (
                    canceled_ok,
                    cancellation_message
                ) = cancel_unpaid_order(
                    order,
                    reason=(
                        f'Cancelación administrativa '
                        f'del pedido '
                        f'{order.order_number}'
                    )
                )

                if not canceled_ok:

                    skipped += 1

                    errors.append(
                        (
                            f'{order.order_number}: '
                            f'{cancellation_message}'
                        )
                    )

                    continue

                canceled += 1

        if canceled:

            self.message_user(
                request,
                (
                    f'{canceled} pedido(s) '
                    f'cancelado(s) correctamente. '
                    f'Las reservas fueron liberadas '
                    f'y las unidades regresaron '
                    f'al inventario.'
                ),
                level=messages.SUCCESS
            )

        if skipped:

            self.message_user(
                request,
                (
                    f'{skipped} pedido(s) '
                    f'no pudieron cancelarse.'
                ),
                level=messages.WARNING
            )

        for error in errors:

            self.message_user(
                request,
                error,
                level=messages.ERROR
            )


    # ========================================================
    # DEVOLUCIÓN TOTAL
    # ========================================================

    @admin.action(
        description=(
            'Procesar devolución total de pedidos seleccionados'
        )
    )
    def process_full_returns(
        self,
        request,
        queryset
    ):

        returned = 0
        already_returned = 0
        skipped = 0
        errors = []

        for selected_order in queryset:

            was_already_returned = (
                selected_order.return_status
                == Order.ReturnStatus.FULL
            )

            (
                return_ok,
                return_message
            ) = process_full_return(
                selected_order,
                reason=(
                    f'Devolución total administrativa '
                    f'del pedido '
                    f'{selected_order.order_number}'
                ),
                created_by=request.user,
            )

            if not return_ok:

                skipped += 1

                errors.append(
                    (
                        f'{selected_order.order_number}: '
                        f'{return_message}'
                    )
                )

                continue

            if was_already_returned:

                already_returned += 1

            else:

                returned += 1

        if returned:

            self.message_user(
                request,
                (
                    f'{returned} pedido(s) '
                    f'procesado(s) como devolución total. '
                    f'Las unidades regresaron '
                    f'al inventario.'
                ),
                level=messages.SUCCESS
            )

        if already_returned:

            self.message_user(
                request,
                (
                    f'{already_returned} pedido(s) '
                    f'ya tenían devolución total. '
                    f'No se modificó nuevamente '
                    f'el inventario.'
                ),
                level=messages.INFO
            )

        if skipped:

            self.message_user(
                request,
                (
                    f'{skipped} pedido(s) '
                    f'no pudieron procesarse '
                    f'como devolución total.'
                ),
                level=messages.WARNING
            )

        for error in errors:

            self.message_user(
                request,
                error,
                level=messages.ERROR
            )


    # ========================================================
    # PREPARANDO
    # ========================================================

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


    # ========================================================
    # ENVIADO
    # ========================================================

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


    # ========================================================
    # ENTREGADO
    # ========================================================

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


    # ========================================================
    # GUARDADO MANUAL DESDE EL ADMIN
    # ========================================================

    def save_model(
        self,
        request,
        obj,
        form,
        change
    ):

        previous_status = None
        previous_order = None

        if change and obj.pk:

            previous_order = (
                Order.objects
                .filter(
                    pk=obj.pk
                )
                .first()
            )

            if previous_order:

                previous_status = (
                    previous_order.status
                )

        # =====================================================
        # PROTEGER PEDIDOS YA DEVUELTOS
        # =====================================================

        if (
            previous_order
            and previous_order.return_status
            == Order.ReturnStatus.FULL
            and obj.status
            != Order.Status.RETURNED
        ):

            obj.status = (
                Order.Status.RETURNED
            )

            obj.return_status = (
                previous_order.return_status
            )

            obj.returned_at = (
                previous_order.returned_at
            )

            obj.return_reason = (
                previous_order.return_reason
            )

            self.message_user(
                request,
                (
                    'Este pedido ya tiene una devolución '
                    'total procesada. Su estado no puede '
                    'cambiarse desde el formulario.'
                ),
                level=messages.ERROR
            )

        # =====================================================
        # CONFIRMACIÓN MANUAL DE PAGO
        # =====================================================

        if (
            previous_order
            and obj.status
            == Order.Status.PAYMENT_CONFIRMED
            and previous_status
            != Order.Status.PAYMENT_CONFIRMED
            and previous_order.return_status
            != Order.ReturnStatus.FULL
        ):

            (
                reservation_ok,
                reservation_message
            ) = finalize_inventory_reservation(
                previous_order
            )

            if not reservation_ok:

                obj.status = previous_status

                self.message_user(
                    request,
                    (
                        'El pago no pudo confirmarse. '
                        f'{reservation_message}'
                    ),
                    level=messages.ERROR
                )

            else:

                obj.payment_confirmed_at = (
                    timezone.now()
                )

                obj.inventory_reservation_status = (
                    previous_order
                    .inventory_reservation_status
                )

                obj.reservation_finalized_at = (
                    previous_order
                    .reservation_finalized_at
                )

                obj.reservation_released_at = (
                    previous_order
                    .reservation_released_at
                )

        # =====================================================
        # EVITAR CANCELACIÓN MANUAL INSEGURA
        # =====================================================

        if (
            previous_order
            and obj.status
            == Order.Status.CANCELED
            and previous_status
            != Order.Status.CANCELED
            and previous_order.return_status
            != Order.ReturnStatus.FULL
        ):

            (
                cancellation_ok,
                cancellation_message
            ) = cancel_unpaid_order(
                previous_order,
                reason=(
                    f'Cancelación administrativa '
                    f'del pedido '
                    f'{previous_order.order_number}'
                )
            )

            if not cancellation_ok:

                obj.status = previous_status

                self.message_user(
                    request,
                    (
                        'El pedido no pudo cancelarse. '
                        f'{cancellation_message}'
                    ),
                    level=messages.ERROR
                )

            else:

                obj.status = (
                    Order.Status.CANCELED
                )

                obj.payment_confirmed_at = None

                obj.inventory_reservation_status = (
                    previous_order
                    .inventory_reservation_status
                )

                obj.reservation_finalized_at = (
                    previous_order
                    .reservation_finalized_at
                )

                obj.reservation_released_at = (
                    previous_order
                    .reservation_released_at
                )

        # =====================================================
        # EVITAR DEVOLUCIÓN MANUAL INSEGURA
        # =====================================================

        if (
            previous_order
            and obj.status
            == Order.Status.RETURNED
            and previous_status
            != Order.Status.RETURNED
            and previous_order.return_status
            != Order.ReturnStatus.FULL
        ):

            return_reason = (
                obj.return_reason.strip()
                if obj.return_reason
                else (
                    f'Devolución total administrativa '
                    f'del pedido '
                    f'{previous_order.order_number}'
                )
            )

            (
                return_ok,
                return_message
            ) = process_full_return(
                previous_order,
                reason=return_reason,
                created_by=request.user,
            )

            if not return_ok:

                obj.status = previous_status

                obj.return_status = (
                    previous_order.return_status
                )

                obj.returned_at = (
                    previous_order.returned_at
                )

                obj.return_reason = (
                    previous_order.return_reason
                )

                self.message_user(
                    request,
                    (
                        'La devolución total no pudo '
                        'procesarse. '
                        f'{return_message}'
                    ),
                    level=messages.ERROR
                )

            else:

                obj.status = (
                    previous_order.status
                )

                obj.return_status = (
                    previous_order.return_status
                )

                obj.returned_at = (
                    previous_order.returned_at
                )

                obj.return_reason = (
                    previous_order.return_reason
                )

                self.message_user(
                    request,
                    (
                        'Devolución total procesada '
                        'correctamente. Las unidades '
                        'regresaron al inventario.'
                    ),
                    level=messages.SUCCESS
                )

        # =====================================================
        # ESTADOS SIN PAGO CONFIRMADO
        # =====================================================

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

        # =====================================================
        # FECHA DE ENVÍO
        # =====================================================

        if (
            obj.status
            == Order.Status.SHIPPED
            and not obj.shipped_at
        ):

            obj.shipped_at = (
                timezone.now()
            )

        # =====================================================
        # FECHA DE ENTREGA
        # =====================================================

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

        # =====================================================
        # BENEFICIO MAYORISTA
        # =====================================================

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