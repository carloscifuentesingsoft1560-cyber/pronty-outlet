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
            .get(pk=order.pk)
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
                'El estado de la reserva no permite finalizarla.'
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

        # Mantener sincronizado el objeto recibido.
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

    La operación es idempotente a nivel del estado del pedido:
    solo una reserva ACTIVE puede liberarse.

    Retorna:
        (True, mensaje)
        (False, mensaje)
    """

    with transaction.atomic():

        locked_order = (
            Order.objects
            .select_for_update()
            .get(pk=order.pk)
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
                'El estado de la reserva no permite liberarla.'
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

        # Mantener sincronizado el objeto recibido.
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

    Esta función servirá posteriormente para:
        - comando de administración;
        - tarea programada en producción.

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
        .order_by('id')
    )

    expired_count = 0

    for order in orders.iterator():

        if expire_order_if_due(order):
            expired_count += 1

    return expired_count