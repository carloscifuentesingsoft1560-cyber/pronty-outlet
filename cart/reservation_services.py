from django.db import transaction
from django.utils import timezone

from catalog.models import InventoryMovement

from .models import Order


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

        # ----------------------------------------------------
        # PEDIDOS ANTERIORES AL SISTEMA DE RESERVAS
        # ----------------------------------------------------

        if (
            locked_order.inventory_reservation_status
            == Order.ReservationStatus.NOT_APPLICABLE
        ):

            return (
                True,
                'Pedido anterior al sistema de reservas.'
            )

        # ----------------------------------------------------
        # YA FINALIZADA
        # ----------------------------------------------------

        if (
            locked_order.inventory_reservation_status
            == Order.ReservationStatus.FINALIZED
        ):

            return (
                True,
                'La reserva ya estaba convertida en venta.'
            )

        # ----------------------------------------------------
        # YA LIBERADA
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # DEBE ESTAR ACTIVA
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # CONVERTIR RESERVA EN VENTA
        # ----------------------------------------------------
        #
        # QuerySet.update() NO ejecuta InventoryMovement.save().
        # Por tanto, el stock NO vuelve a disminuir.
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # SINCRONIZAR OBJETO RECIBIDO
        # ----------------------------------------------------

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

    Por cada movimiento RESERVATION crea un movimiento
    RESERVATION_RELEASE.

    El nuevo movimiento suma nuevamente las existencias.

    La operación es idempotente a nivel del pedido:
    únicamente una reserva ACTIVE puede liberarse.

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

        # ----------------------------------------------------
        # PEDIDO ANTIGUO
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # YA LIBERADA
        # ----------------------------------------------------

        if (
            locked_order.inventory_reservation_status
            == Order.ReservationStatus.RELEASED
        ):

            return (
                True,
                'La reserva ya estaba liberada.'
            )

        # ----------------------------------------------------
        # YA ES VENTA
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # DEBE ESTAR ACTIVA
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # DEVOLVER CADA UNIDAD AL INVENTARIO
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # SI FUE POR VENCIMIENTO
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # SINCRONIZAR OBJETO RECIBIDO
        # ----------------------------------------------------

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

    La cancelación:

        ACTIVE
        -> libera inventario
        -> RELEASED
        -> CANCELED

    No puede utilizarse para una venta ya finalizada.

    Tampoco cancela directamente pedidos con comprobante
    recibido o pago en revisión. En esos casos Pronty debe
    revisar primero el comprobante.

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

        # ----------------------------------------------------
        # YA CANCELADO
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # PEDIDOS ANTIGUOS
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # VENTA YA CONFIRMADA
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # RESERVA YA LIBERADA
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # COMPROBANTE EN REVISIÓN
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # ESTADO PERMITIDO PARA CANCELACIÓN
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # LIBERAR LA RESERVA
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # MARCAR PEDIDO COMO CANCELADO
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # SINCRONIZAR OBJETO RECIBIDO
        # ----------------------------------------------------

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
# PROCESAR DEVOLUCIÓN TOTAL
# ============================================================

def process_full_return(
    order,
    *,
    reason=None,
    created_by=None
):
    """
    Procesa la devolución total de una venta confirmada.

    Por cada producto del pedido crea un movimiento RETURN.

    El movimiento RETURN suma nuevamente las unidades
    al inventario disponible.

    La operación es idempotente:
    si el pedido ya tiene devolución total, no vuelve a
    crear movimientos ni a sumar inventario.

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

        # ----------------------------------------------------
        # YA DEVUELTO
        # ----------------------------------------------------

        if (
            locked_order.return_status
            == Order.ReturnStatus.FULL
        ):

            if (
                locked_order.status
                == Order.Status.RETURNED
            ):

                return (
                    True,
                    'El pedido ya tenía devolución total.'
                )

            return (
                False,
                (
                    'El pedido figura con devolución total, '
                    'pero su estado general no es Devuelto.'
                )
            )

        # ----------------------------------------------------
        # DEVOLUCIÓN PARCIAL EXISTENTE
        # ----------------------------------------------------

        if (
            locked_order.return_status
            == Order.ReturnStatus.PARTIAL
        ):

            return (
                False,
                (
                    'El pedido ya tiene una devolución parcial. '
                    'La devolución total deberá procesarse '
                    'desde el módulo de devoluciones parciales.'
                )
            )

        # ----------------------------------------------------
        # DEBE EXISTIR UNA VENTA REAL
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # ESTADO DEL PEDIDO
        # ----------------------------------------------------

        if (
            locked_order.status
            not in RETURNABLE_ORDER_STATUSES
        ):

            return (
                False,
                (
                    'El estado actual del pedido '
                    'no permite procesar una devolución.'
                )
            )

        # ----------------------------------------------------
        # DEBE EXISTIR PAGO CONFIRMADO
        # ----------------------------------------------------

        if not locked_order.payment_confirmed_at:

            return (
                False,
                (
                    'El pedido no tiene fecha de '
                    'confirmación de pago.'
                )
            )

        # ----------------------------------------------------
        # VERIFICAR QUE EXISTAN MOVIMIENTOS DE VENTA
        # ----------------------------------------------------

        sale_movements = list(
            InventoryMovement.objects
            .select_for_update()
            .filter(
                reference=locked_order.order_number,
                movement_type=(
                    InventoryMovement
                    .MovementType
                    .SALE
                )
            )
        )

        if not sale_movements:

            return (
                False,
                (
                    'No se encontraron movimientos de venta '
                    'para este pedido.'
                )
            )

        # ----------------------------------------------------
        # VERIFICAR QUE NO EXISTAN DEVOLUCIONES PREVIAS
        # ----------------------------------------------------

        existing_returns = (
            InventoryMovement.objects
            .filter(
                reference=locked_order.order_number,
                movement_type=(
                    InventoryMovement
                    .MovementType
                    .RETURN
                )
            )
            .exists()
        )

        if existing_returns:

            return (
                False,
                (
                    'Ya existen movimientos de devolución '
                    'para este pedido. Se bloqueó la operación '
                    'para evitar duplicar inventario.'
                )
            )

        return_reason = (
            reason
            or (
                f'Devolución total del pedido '
                f'{locked_order.order_number}'
            )
        )

        # ----------------------------------------------------
        # DEVOLVER AL INVENTARIO LAS UNIDADES VENDIDAS
        # ----------------------------------------------------
        #
        # Usamos los movimientos SALE y no solamente los
        # OrderItem para devolver exactamente las cantidades
        # que salieron del inventario.
        # ----------------------------------------------------

        for sale in sale_movements:

            InventoryMovement.objects.create(
                product=sale.product,

                movement_type=(
                    InventoryMovement
                    .MovementType
                    .RETURN
                ),

                quantity=sale.quantity,

                reason=return_reason,

                reference=locked_order.order_number,

                created_by=created_by,
            )

        now = timezone.now()

        # ----------------------------------------------------
        # MARCAR DEVOLUCIÓN TOTAL
        # ----------------------------------------------------

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
                'Las unidades regresaron al inventario.'
            )
        )


# ============================================================
# COMPROBAR SI UN PEDIDO YA VENCIÓ
# ============================================================

def expire_order_if_due(order):
    """
    Comprueba si una reserva debe vencer.

    Solo vence automáticamente cuando:
        - la reserva está ACTIVE;
        - existe reservation_expires_at;
        - ya pasó la fecha límite;
        - el pedido sigue esperando pago
          o tiene un comprobante rechazado.

    Si el comprobante ya fue recibido o está en revisión,
    la reserva se conserva mientras Pronty valida el pago.

    Retorna:
        True  -> la reserva fue vencida/liberada.
        False -> no debía vencerse.
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
    Busca pedidos cuya reserva ya venció y libera
    su inventario.

    Esta función puede utilizarse desde:
        - comando de administración;
        - tarea programada;
        - scheduler de producción.

    Retorna la cantidad de reservas liberadas.
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