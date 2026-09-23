from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from catalog.models import InventoryMovement

from .models import (
    Order,
    OrderItem,
    ReturnRecord,
    ReturnRecordItem,
)


# ============================================================
# ESTADOS QUE PUEDEN VENCER AUTOMÁTICAMENTE
# ============================================================

EXPIRABLE_ORDER_STATUSES = {
    Order.Status.PENDING_PAYMENT,
    Order.Status.PAYMENT_DECLINED,
}


# ============================================================
# ESTADOS PROTEGIDOS MIENTRAS PRONTY REVISA EL PAGO
# ============================================================

PAYMENT_REVIEW_STATUSES = {
    Order.Status.PROOF_RECEIVED,
    Order.Status.PAYMENT_PROCESSING,
}


# ============================================================
# ESTADOS QUE PUEDEN CANCELARSE SIN PAGO CONFIRMADO
# ============================================================

CANCELLABLE_UNPAID_STATUSES = {
    Order.Status.PENDING_PAYMENT,
    Order.Status.PAYMENT_DECLINED,
}


# ============================================================
# ESTADOS DESDE LOS QUE PUEDE PROCESARSE UNA DEVOLUCIÓN
# ============================================================

RETURNABLE_ORDER_STATUSES = {
    Order.Status.PAYMENT_CONFIRMED,
    Order.Status.PREPARING,
    Order.Status.SHIPPED,
    Order.Status.DELIVERED,
    Order.Status.CHANGE_REQUESTED,
}


# ============================================================
# FINALIZAR RESERVA
# ============================================================

def finalize_inventory_reservation(order):
    """
    Convierte una reserva activa en venta definitiva.

    IMPORTANTE:
    No crea un nuevo movimiento SALE.

    El movimiento RESERVATION existente se transforma
    en SALE para evitar descontar el stock dos veces.

    Retorna:
        (True, mensaje)
        (False, mensaje)
    """

    with transaction.atomic():

        locked_order = (
            Order.objects
            .select_for_update()
            .get(
                pk=order.pk
            )
        )

        if (
            locked_order.inventory_reservation_status
            == Order.ReservationStatus.NOT_APPLICABLE
        ):

            return (
                True,
                'Pedido anterior al sistema de reservas.'
            )

        if (
            locked_order.inventory_reservation_status
            == Order.ReservationStatus.FINALIZED
        ):

            return (
                True,
                'La reserva ya estaba convertida en venta.'
            )

        if (
            locked_order.inventory_reservation_status
            == Order.ReservationStatus.RELEASED
        ):

            return (
                False,
                (
                    'La reserva ya fue liberada '
                    'y las unidades regresaron al inventario.'
                )
            )

        if (
            locked_order.inventory_reservation_status
            != Order.ReservationStatus.ACTIVE
        ):

            return (
                False,
                (
                    'El estado de la reserva '
                    'no permite finalizarla.'
                )
            )

        reservation_movements = list(
            InventoryMovement.objects
            .select_for_update()
            .filter(
                reference=locked_order.order_number,
                movement_type=(
                    InventoryMovement
                    .MovementType
                    .RESERVATION
                )
            )
        )

        if not reservation_movements:

            return (
                False,
                (
                    'El pedido figura con reserva activa, '
                    'pero no tiene movimientos de reserva.'
                )
            )

        InventoryMovement.objects.filter(
            pk__in=[
                movement.pk
                for movement in reservation_movements
            ]
        ).update(
            movement_type=(
                InventoryMovement
                .MovementType
                .SALE
            ),
            reason=(
                f'Reserva convertida en venta '
                f'por pago confirmado del pedido '
                f'{locked_order.order_number}'
            )
        )

        now = timezone.now()

        locked_order.inventory_reservation_status = (
            Order.ReservationStatus.FINALIZED
        )

        locked_order.reservation_finalized_at = now
        locked_order.reservation_released_at = None

        locked_order.save(
            update_fields=[
                'inventory_reservation_status',
                'reservation_finalized_at',
                'reservation_released_at',
                'updated_at',
            ]
        )

        order.inventory_reservation_status = (
            locked_order.inventory_reservation_status
        )

        order.reservation_finalized_at = (
            locked_order.reservation_finalized_at
        )

        order.reservation_released_at = (
            locked_order.reservation_released_at
        )

        return (
            True,
            'Reserva convertida en venta correctamente.'
        )


# ============================================================
# LIBERAR RESERVA
# ============================================================

def release_inventory_reservation(
    order,
    *,
    mark_as_expired=False,
    reason=None
):
    """
    Devuelve al inventario las unidades de una reserva activa.

    La operación es idempotente:
    solamente una reserva ACTIVE puede liberarse.
    """

    with transaction.atomic():

        locked_order = (
            Order.objects
            .select_for_update()
            .get(
                pk=order.pk
            )
        )

        if (
            locked_order.inventory_reservation_status
            == Order.ReservationStatus.NOT_APPLICABLE
        ):

            return (
                False,
                (
                    'Este pedido es anterior al sistema '
                    'de reservas de inventario.'
                )
            )

        if (
            locked_order.inventory_reservation_status
            == Order.ReservationStatus.RELEASED
        ):

            return (
                True,
                'La reserva ya estaba liberada.'
            )

        if (
            locked_order.inventory_reservation_status
            == Order.ReservationStatus.FINALIZED
        ):

            return (
                False,
                (
                    'La reserva ya fue convertida en venta '
                    'y no puede liberarse.'
                )
            )

        if (
            locked_order.inventory_reservation_status
            != Order.ReservationStatus.ACTIVE
        ):

            return (
                False,
                (
                    'El estado de la reserva '
                    'no permite liberarla.'
                )
            )

        reservation_movements = list(
            InventoryMovement.objects
            .select_for_update()
            .filter(
                reference=locked_order.order_number,
                movement_type=(
                    InventoryMovement
                    .MovementType
                    .RESERVATION
                )
            )
        )

        if not reservation_movements:

            return (
                False,
                (
                    'El pedido figura con reserva activa, '
                    'pero no tiene movimientos de reserva.'
                )
            )

        release_reason = (
            reason
            or (
                f'Liberación de reserva correspondiente '
                f'al pedido {locked_order.order_number}'
            )
        )

        for reservation in reservation_movements:

            InventoryMovement.objects.create(
                product=reservation.product,
                movement_type=(
                    InventoryMovement
                    .MovementType
                    .RESERVATION_RELEASE
                ),
                quantity=reservation.quantity,
                reason=release_reason,
                reference=locked_order.order_number,
                created_by=None,
            )

        now = timezone.now()

        locked_order.inventory_reservation_status = (
            Order.ReservationStatus.RELEASED
        )

        locked_order.reservation_released_at = now
        locked_order.reservation_finalized_at = None

        update_fields = [
            'inventory_reservation_status',
            'reservation_released_at',
            'reservation_finalized_at',
            'updated_at',
        ]

        if mark_as_expired:

            locked_order.status = (
                Order.Status.RESERVATION_EXPIRED
            )

            locked_order.payment_confirmed_at = None

            update_fields.extend([
                'status',
                'payment_confirmed_at',
            ])

        locked_order.save(
            update_fields=update_fields
        )

        order.inventory_reservation_status = (
            locked_order.inventory_reservation_status
        )

        order.reservation_released_at = (
            locked_order.reservation_released_at
        )

        order.reservation_finalized_at = (
            locked_order.reservation_finalized_at
        )

        order.status = (
            locked_order.status
        )

        return (
            True,
            'Reserva liberada correctamente.'
        )


# ============================================================
# CANCELAR PEDIDO SIN PAGO CONFIRMADO
# ============================================================

def cancel_unpaid_order(
    order,
    *,
    reason=None
):
    """
    Cancela un pedido que todavía NO tiene pago confirmado.

    ACTIVE
    -> libera inventario
    -> RELEASED
    -> CANCELED
    """

    with transaction.atomic():

        locked_order = (
            Order.objects
            .select_for_update()
            .get(
                pk=order.pk
            )
        )

        if (
            locked_order.status
            == Order.Status.CANCELED
        ):

            if (
                locked_order.inventory_reservation_status
                == Order.ReservationStatus.RELEASED
            ):

                return (
                    True,
                    'El pedido ya estaba cancelado.'
                )

            return (
                False,
                (
                    'El pedido figura como cancelado, '
                    'pero su reserva no está liberada.'
                )
            )

        if (
            locked_order.inventory_reservation_status
            == Order.ReservationStatus.NOT_APPLICABLE
        ):

            return (
                False,
                (
                    'Este pedido es anterior al sistema '
                    'de reservas y no puede cancelarse '
                    'mediante este proceso automático.'
                )
            )

        if (
            locked_order.inventory_reservation_status
            == Order.ReservationStatus.FINALIZED
        ):

            return (
                False,
                (
                    'El pago de este pedido ya fue confirmado. '
                    'Debe procesarse como devolución, '
                    'no como cancelación de reserva.'
                )
            )

        if (
            locked_order.inventory_reservation_status
            == Order.ReservationStatus.RELEASED
        ):

            return (
                False,
                (
                    'La reserva ya fue liberada '
                    'y el pedido no puede cancelarse '
                    'nuevamente.'
                )
            )

        if (
            locked_order.status
            in PAYMENT_REVIEW_STATUSES
        ):

            return (
                False,
                (
                    'El pedido tiene un comprobante de pago '
                    'pendiente de revisión. Revisa o rechaza '
                    'el comprobante antes de cancelar.'
                )
            )

        if (
            locked_order.status
            not in CANCELLABLE_UNPAID_STATUSES
        ):

            return (
                False,
                (
                    'El estado actual del pedido '
                    'no permite cancelarlo como '
                    'pedido sin pago.'
                )
            )

        cancellation_reason = (
            reason
            or (
                f'Cancelación del pedido '
                f'{locked_order.order_number} '
                f'antes de confirmar el pago'
            )
        )

        (
            released,
            release_message
        ) = release_inventory_reservation(
            locked_order,
            mark_as_expired=False,
            reason=cancellation_reason
        )

        if not released:

            return (
                False,
                release_message
            )

        locked_order.status = (
            Order.Status.CANCELED
        )

        locked_order.payment_confirmed_at = None

        locked_order.save(
            update_fields=[
                'status',
                'payment_confirmed_at',
                'updated_at',
            ]
        )

        order.status = (
            locked_order.status
        )

        order.inventory_reservation_status = (
            locked_order.inventory_reservation_status
        )

        order.reservation_released_at = (
            locked_order.reservation_released_at
        )

        order.reservation_finalized_at = (
            locked_order.reservation_finalized_at
        )

        order.payment_confirmed_at = None

        return (
            True,
            'Pedido cancelado y reserva liberada correctamente.'
        )


# ============================================================
# VALIDAR QUE EL PEDIDO TENGA UNA VENTA REAL
# ============================================================

def _validate_returnable_order(
    locked_order
):
    """
    Validaciones comunes para devoluciones.
    """

    if (
        locked_order.inventory_reservation_status
        != Order.ReservationStatus.FINALIZED
    ):

        return (
            False,
            (
                'El pedido no tiene una venta de inventario '
                'finalizada y no puede devolverse.'
            )
        )

    if not locked_order.payment_confirmed_at:

        return (
            False,
            (
                'El pedido no tiene fecha de '
                'confirmación de pago.'
            )
        )

    if (
        locked_order.return_status
        != Order.ReturnStatus.FULL
        and locked_order.status
        not in RETURNABLE_ORDER_STATUSES
    ):

        return (
            False,
            (
                'El estado actual del pedido '
                'no permite procesar una devolución.'
            )
        )

    return (
        True,
        'Pedido válido para devolución.'
    )


# ============================================================
# CANTIDAD VENDIDA DE UN PRODUCTO
# ============================================================

def _get_sold_quantity(
    order,
    product
):
    """
    Obtiene la cantidad realmente registrada como SALE
    para un producto dentro del pedido.
    """

    result = (
        InventoryMovement.objects
        .filter(
            reference=order.order_number,
            product=product,
            movement_type=(
                InventoryMovement
                .MovementType
                .SALE
            )
        )
        .aggregate(
            total=Sum('quantity')
        )
    )

    return (
        result['total']
        or 0
    )


# ============================================================
# CANTIDAD YA DEVUELTA EN INVENTARIO
# ============================================================

def _get_inventory_returned_quantity(
    order,
    product
):
    """
    Obtiene cuántas unidades RETURN ya existen
    para ese producto y pedido.
    """

    result = (
        InventoryMovement.objects
        .filter(
            reference=order.order_number,
            product=product,
            movement_type=(
                InventoryMovement
                .MovementType
                .RETURN
            )
        )
        .aggregate(
            total=Sum('quantity')
        )
    )

    return (
        result['total']
        or 0
    )


# ============================================================
# CREAR REGISTRO HISTÓRICO DE DEVOLUCIÓN
# ============================================================

def _create_return_record(
    *,
    order,
    return_type,
    reason,
    created_by,
    returned_items
):
    """
    Crea el historial de una operación de devolución.

    returned_items debe contener diccionarios con:
        order_item
        quantity

    El registro se crea dentro de la misma transacción
    de inventario que llamó esta función.
    """

    return_record = ReturnRecord.objects.create(
        order=order,
        return_type=return_type,
        reason=reason or '',
        created_by=created_by,
    )

    record_items = []

    for data in returned_items:

        item = data['order_item']
        quantity = data['quantity']

        record_items.append(
            ReturnRecordItem(
                return_record=return_record,
                order_item=item,
                product=item.product,
                product_name=item.product_name,
                sku=item.sku,
                quantity=quantity,
                unit_price=item.unit_price,
            )
        )

    ReturnRecordItem.objects.bulk_create(
        record_items
    )

    return return_record


# ============================================================
# DEVOLUCIÓN PARCIAL
# ============================================================

def process_partial_return(
    order_item,
    quantity,
    *,
    reason=None,
    created_by=None
):
    """
    Devuelve una cantidad específica de un producto.

    Nunca permite devolver más unidades de las compradas.

    Si después de esta operación todos los productos
    del pedido quedaron completamente devueltos,
    el pedido pasa automáticamente a devolución TOTAL.

    Cada operación genera además un registro independiente
    en el historial de devoluciones.

    Retorna:
        (True, mensaje)
        (False, mensaje)
    """

    try:

        quantity = int(
            quantity
        )

    except (
        TypeError,
        ValueError
    ):

        return (
            False,
            'La cantidad a devolver no es válida.'
        )

    if quantity <= 0:

        return (
            False,
            (
                'La cantidad a devolver '
                'debe ser mayor que cero.'
            )
        )

    with transaction.atomic():

        initial_item = (
            OrderItem.objects
            .get(
                pk=order_item.pk
            )
        )

        locked_order = (
            Order.objects
            .select_for_update()
            .get(
                pk=initial_item.order.pk
            )
        )

        locked_items = list(
            OrderItem.objects
            .select_for_update()
            .select_related(
                'product'
            )
            .filter(
                order=locked_order
            )
            .order_by(
                'id'
            )
        )

        locked_item = None

        for item in locked_items:

            if (
                item.pk
                == order_item.pk
            ):

                locked_item = item
                break

        if locked_item is None:

            return (
                False,
                (
                    'El producto no pertenece '
                    'al pedido indicado.'
                )
            )

        if (
            locked_order.return_status
            == Order.ReturnStatus.FULL
        ):

            return (
                False,
                (
                    'Este pedido ya tiene '
                    'devolución total.'
                )
            )

        (
            valid_order,
            validation_message
        ) = _validate_returnable_order(
            locked_order
        )

        if not valid_order:

            return (
                False,
                validation_message
            )

        available_to_return = max(
            locked_item.quantity
            - locked_item.returned_quantity,
            0
        )

        if available_to_return <= 0:

            return (
                False,
                (
                    'Este producto ya fue '
                    'devuelto completamente.'
                )
            )

        if (
            quantity
            > available_to_return
        ):

            return (
                False,
                (
                    f'Solo quedan '
                    f'{available_to_return} unidad(es) '
                    f'disponibles para devolución.'
                )
            )

        sold_quantity = (
            _get_sold_quantity(
                locked_order,
                locked_item.product
            )
        )

        if sold_quantity <= 0:

            return (
                False,
                (
                    'No existe un movimiento de venta '
                    'para este producto en el pedido.'
                )
            )

        inventory_returned = (
            _get_inventory_returned_quantity(
                locked_order,
                locked_item.product
            )
        )

        if (
            inventory_returned
            + quantity
            > sold_quantity
        ):

            return (
                False,
                (
                    'La devolución excedería la cantidad '
                    'registrada como vendida. '
                    'La operación fue bloqueada.'
                )
            )

        return_reason = (
            reason
            or (
                f'Devolución parcial del producto '
                f'{locked_item.product_name} '
                f'del pedido '
                f'{locked_order.order_number}'
            )
        )

        # ----------------------------------------------------
        # DEVOLVER INVENTARIO
        # ----------------------------------------------------

        InventoryMovement.objects.create(
            product=locked_item.product,
            movement_type=(
                InventoryMovement
                .MovementType
                .RETURN
            ),
            quantity=quantity,
            reason=return_reason,
            reference=locked_order.order_number,
            created_by=created_by,
        )

        # ----------------------------------------------------
        # ACTUALIZAR CANTIDAD DEVUELTA DEL PRODUCTO
        # ----------------------------------------------------

        locked_item.returned_quantity = (
            locked_item.returned_quantity
            + quantity
        )

        locked_item.save(
            update_fields=[
                'returned_quantity',
            ]
        )

        now = timezone.now()

        # ----------------------------------------------------
        # COMPROBAR SI TODO EL PEDIDO QUEDÓ DEVUELTO
        # ----------------------------------------------------

        all_fully_returned = True

        for item in locked_items:

            current_returned_quantity = (
                locked_item.returned_quantity
                if item.pk == locked_item.pk
                else item.returned_quantity
            )

            if (
                current_returned_quantity
                < item.quantity
            ):

                all_fully_returned = False
                break

        if all_fully_returned:

            locked_order.return_status = (
                Order.ReturnStatus.FULL
            )

            locked_order.status = (
                Order.Status.RETURNED
            )

            history_return_type = (
                ReturnRecord.ReturnType.FULL
            )

        else:

            locked_order.return_status = (
                Order.ReturnStatus.PARTIAL
            )

            history_return_type = (
                ReturnRecord.ReturnType.PARTIAL
            )

        locked_order.returned_at = now

        locked_order.return_reason = (
            return_reason
        )

        order_update_fields = [
            'return_status',
            'returned_at',
            'return_reason',
            'updated_at',
        ]

        if all_fully_returned:

            order_update_fields.append(
                'status'
            )

        locked_order.save(
            update_fields=order_update_fields
        )

        # ----------------------------------------------------
        # CREAR HISTORIAL DE ESTA DEVOLUCIÓN
        # ----------------------------------------------------

        _create_return_record(
            order=locked_order,
            return_type=history_return_type,
            reason=return_reason,
            created_by=created_by,
            returned_items=[
                {
                    'order_item': locked_item,
                    'quantity': quantity,
                }
            ],
        )

        # ----------------------------------------------------
        # SINCRONIZAR OBJETO RECIBIDO
        # ----------------------------------------------------

        order_item.returned_quantity = (
            locked_item.returned_quantity
        )

        if hasattr(
            order_item,
            'order'
        ):

            order_item.order.return_status = (
                locked_order.return_status
            )

            order_item.order.returned_at = (
                locked_order.returned_at
            )

            order_item.order.return_reason = (
                locked_order.return_reason
            )

            order_item.order.status = (
                locked_order.status
            )

        if all_fully_returned:

            return (
                True,
                (
                    'Devolución procesada correctamente. '
                    'Todos los productos del pedido '
                    'quedaron devueltos y el pedido '
                    'pasó a devolución total.'
                )
            )

        remaining = (
            locked_item.quantity
            - locked_item.returned_quantity
        )

        return (
            True,
            (
                f'Devolución parcial procesada correctamente. '
                f'Quedan {remaining} unidad(es) '
                f'de este producto disponibles '
                f'para devolución.'
            )
        )


# ============================================================
# DEVOLUCIÓN TOTAL
# ============================================================

def process_full_return(
    order,
    *,
    reason=None,
    created_by=None
):
    """
    Procesa la devolución total de una venta.

    Si ya existían devoluciones parciales, devuelve
    solamente las unidades restantes.

    Si el pedido ya estaba marcado FULL antes de existir
    returned_quantity, sincroniza los OrderItem sin volver
    a crear movimientos RETURN.

    Cada devolución nueva genera además un registro
    en el historial.

    La operación es idempotente.
    """

    with transaction.atomic():

        locked_order = (
            Order.objects
            .select_for_update()
            .get(
                pk=order.pk
            )
        )

        locked_items = list(
            OrderItem.objects
            .select_for_update()
            .select_related(
                'product'
            )
            .filter(
                order=locked_order
            )
            .order_by(
                'id'
            )
        )

        if not locked_items:

            return (
                False,
                (
                    'El pedido no contiene '
                    'productos para devolver.'
                )
            )

        # ----------------------------------------------------
        # PEDIDO YA DEVUELTO TOTALMENTE
        # ----------------------------------------------------
        #
        # Sincroniza pedidos antiguos sin returned_quantity.
        # No crea RETURN ni historial nuevo.
        # ----------------------------------------------------

        if (
            locked_order.return_status
            == Order.ReturnStatus.FULL
        ):

            items_to_sync = []

            for item in locked_items:

                if (
                    item.returned_quantity
                    != item.quantity
                ):

                    item.returned_quantity = (
                        item.quantity
                    )

                    items_to_sync.append(
                        item
                    )

            if items_to_sync:

                OrderItem.objects.bulk_update(
                    items_to_sync,
                    [
                        'returned_quantity'
                    ]
                )

            if (
                locked_order.status
                != Order.Status.RETURNED
            ):

                return (
                    False,
                    (
                        'El pedido figura con devolución total, '
                        'pero su estado general no es Devuelto.'
                    )
                )

            return (
                True,
                (
                    'El pedido ya tenía devolución total. '
                    'No se modificó nuevamente el inventario '
                    'ni se creó un historial duplicado.'
                )
            )

        (
            valid_order,
            validation_message
        ) = _validate_returnable_order(
            locked_order
        )

        if not valid_order:

            return (
                False,
                validation_message
            )

        return_reason = (
            reason
            or (
                f'Devolución total del pedido '
                f'{locked_order.order_number}'
            )
        )

        # ----------------------------------------------------
        # CALCULAR LO QUE FALTA POR DEVOLVER
        # ----------------------------------------------------

        remaining_by_product = {}
        returned_items_for_history = []

        for item in locked_items:

            remaining = max(
                item.quantity
                - item.returned_quantity,
                0
            )

            if remaining <= 0:

                continue

            returned_items_for_history.append(
                {
                    'order_item': item,
                    'quantity': remaining,
                }
            )

            product_id = (
                item.product.pk
            )

            if (
                product_id
                not in remaining_by_product
            ):

                remaining_by_product[
                    product_id
                ] = {
                    'product': item.product,
                    'quantity': 0,
                }

            remaining_by_product[
                product_id
            ]['quantity'] += (
                remaining
            )

        # ----------------------------------------------------
        # SI LOS ITEMS YA ESTABAN COMPLETAMENTE DEVUELTOS
        # ----------------------------------------------------
        #
        # Aquí no hubo unidades nuevas que regresaran
        # al inventario, así que tampoco creamos un
        # ReturnRecord vacío.
        # ----------------------------------------------------

        if not remaining_by_product:

            locked_order.return_status = (
                Order.ReturnStatus.FULL
            )

            locked_order.status = (
                Order.Status.RETURNED
            )

            locked_order.returned_at = (
                timezone.now()
            )

            locked_order.return_reason = (
                return_reason
            )

            locked_order.save(
                update_fields=[
                    'return_status',
                    'status',
                    'returned_at',
                    'return_reason',
                    'updated_at',
                ]
            )

            order.return_status = (
                locked_order.return_status
            )

            order.status = (
                locked_order.status
            )

            order.returned_at = (
                locked_order.returned_at
            )

            order.return_reason = (
                locked_order.return_reason
            )

            return (
                True,
                (
                    'Todos los productos ya estaban '
                    'devueltos. El pedido quedó marcado '
                    'como devolución total.'
                )
            )

        # ----------------------------------------------------
        # VALIDAR MOVIMIENTOS SALE Y RETURN
        # ----------------------------------------------------

        for data in remaining_by_product.values():

            product = (
                data['product']
            )

            remaining_quantity = (
                data['quantity']
            )

            sold_quantity = (
                _get_sold_quantity(
                    locked_order,
                    product
                )
            )

            if sold_quantity <= 0:

                return (
                    False,
                    (
                        f'No existe movimiento de venta '
                        f'para {product.name}.'
                    )
                )

            already_returned_inventory = (
                _get_inventory_returned_quantity(
                    locked_order,
                    product
                )
            )

            if (
                already_returned_inventory
                + remaining_quantity
                > sold_quantity
            ):

                return (
                    False,
                    (
                        f'La devolución de {product.name} '
                        f'excedería la cantidad vendida. '
                        f'La operación fue bloqueada.'
                    )
                )

        # ----------------------------------------------------
        # CREAR RETURN SOLO POR LO QUE FALTA
        # ----------------------------------------------------

        for data in remaining_by_product.values():

            InventoryMovement.objects.create(
                product=data['product'],
                movement_type=(
                    InventoryMovement
                    .MovementType
                    .RETURN
                ),
                quantity=data['quantity'],
                reason=return_reason,
                reference=locked_order.order_number,
                created_by=created_by,
            )

        # ----------------------------------------------------
        # MARCAR TODOS LOS ITEMS COMO DEVUELTOS
        # ----------------------------------------------------

        for item in locked_items:

            item.returned_quantity = (
                item.quantity
            )

        OrderItem.objects.bulk_update(
            locked_items,
            [
                'returned_quantity'
            ]
        )

        now = timezone.now()

        locked_order.return_status = (
            Order.ReturnStatus.FULL
        )

        locked_order.returned_at = now

        locked_order.return_reason = (
            return_reason
        )

        locked_order.status = (
            Order.Status.RETURNED
        )

        locked_order.save(
            update_fields=[
                'return_status',
                'returned_at',
                'return_reason',
                'status',
                'updated_at',
            ]
        )

        # ----------------------------------------------------
        # CREAR HISTORIAL DE LA DEVOLUCIÓN TOTAL
        # ----------------------------------------------------

        _create_return_record(
            order=locked_order,
            return_type=ReturnRecord.ReturnType.FULL,
            reason=return_reason,
            created_by=created_by,
            returned_items=returned_items_for_history,
        )

        # ----------------------------------------------------
        # SINCRONIZAR OBJETO RECIBIDO
        # ----------------------------------------------------

        order.return_status = (
            locked_order.return_status
        )

        order.returned_at = (
            locked_order.returned_at
        )

        order.return_reason = (
            locked_order.return_reason
        )

        order.status = (
            locked_order.status
        )

        return (
            True,
            (
                'Devolución total procesada correctamente. '
                'Las unidades pendientes regresaron '
                'al inventario.'
            )
        )


# ============================================================
# COMPROBAR SI UN PEDIDO YA VENCIÓ
# ============================================================

def expire_order_if_due(order):
    """
    Comprueba si una reserva debe vencer.
    """

    if (
        order.inventory_reservation_status
        != Order.ReservationStatus.ACTIVE
    ):

        return False

    if not order.reservation_expires_at:

        return False

    if (
        order.status
        in PAYMENT_REVIEW_STATUSES
    ):

        return False

    if (
        order.status
        not in EXPIRABLE_ORDER_STATUSES
    ):

        return False

    if (
        timezone.now()
        < order.reservation_expires_at
    ):

        return False

    released, _ = (
        release_inventory_reservation(
            order,
            mark_as_expired=True,
            reason=(
                f'Reserva vencida del pedido '
                f'{order.order_number}'
            )
        )
    )

    return released


# ============================================================
# PROCESAR TODAS LAS RESERVAS VENCIDAS
# ============================================================

def expire_due_reservations():
    """
    Busca pedidos cuya reserva ya venció
    y libera su inventario.
    """

    now = timezone.now()

    orders = (
        Order.objects
        .filter(
            inventory_reservation_status=(
                Order.ReservationStatus.ACTIVE
            ),
            status__in=EXPIRABLE_ORDER_STATUSES,
            reservation_expires_at__isnull=False,
            reservation_expires_at__lte=now,
        )
        .order_by(
            'id'
        )
    )

    expired_count = 0

    for order in orders.iterator():

        if expire_order_if_due(
            order
        ):

            expired_count += 1

    return expired_count