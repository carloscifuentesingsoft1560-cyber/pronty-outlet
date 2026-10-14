from django.db import transaction
from django.utils import timezone

from .models import Order


# ============================================================
# TRANSICIONES DE ESTADO PERMITIDAS DESDE EL ADMIN
# ============================================================

ALLOWED_ADMIN_TRANSITIONS = {

    Order.Status.PENDING_PAYMENT: {
        Order.Status.CANCELED,
    },

    Order.Status.PROOF_RECEIVED: {
        Order.Status.PAYMENT_CONFIRMED,
        Order.Status.PAYMENT_DECLINED,
    },

    Order.Status.PAYMENT_PROCESSING: {
        Order.Status.PAYMENT_CONFIRMED,
        Order.Status.PAYMENT_DECLINED,
    },

    Order.Status.PAYMENT_DECLINED: {
        Order.Status.CANCELED,
    },

    Order.Status.PAYMENT_CONFIRMED: {
        Order.Status.PREPARING,
        Order.Status.RETURNED,
    },

    Order.Status.PREPARING: {
        Order.Status.SHIPPED,
        Order.Status.RETURNED,
    },

    Order.Status.SHIPPED: {
        Order.Status.DELIVERED,
        Order.Status.RETURNED,
    },

    Order.Status.DELIVERED: {
        Order.Status.CHANGE_REQUESTED,
        Order.Status.RETURNED,
    },

    Order.Status.CHANGE_REQUESTED: {
        Order.Status.RETURNED,
    },

    Order.Status.RETURNED: set(),

    Order.Status.CANCELED: set(),

    Order.Status.RESERVATION_EXPIRED: set(),
}


# ============================================================
# NOMBRES AMIGABLES DE LOS ESTADOS
# ============================================================

def _status_label(status):

    labels = dict(
        Order.Status.choices
    )

    return labels.get(
        status,
        status
    )


# ============================================================
# VALIDAR TRANSICIÓN DE ESTADO
# ============================================================

def validate_admin_status_transition(
    current_status,
    new_status
):

    if current_status == new_status:

        return (
            True,
            'El estado no cambió.'
        )

    allowed_statuses = (
        ALLOWED_ADMIN_TRANSITIONS.get(
            current_status,
            set()
        )
    )

    if new_status not in allowed_statuses:

        return (
            False,
            (
                'No se permite cambiar el pedido '
                f'directamente de '
                f'"{_status_label(current_status)}" '
                f'a '
                f'"{_status_label(new_status)}".'
            )
        )

    return (
        True,
        'Transición de estado permitida.'
    )


# ============================================================
# VALIDAR VENTA CONFIRMADA
# ============================================================

def _validate_finalized_sale(
    order
):

    if (
        order.return_status
        == Order.ReturnStatus.FULL
    ):

        return (
            False,
            (
                'El pedido ya tiene una devolución '
                'total procesada.'
            )
        )

    if (
        order.inventory_reservation_status
        != Order.ReservationStatus.FINALIZED
    ):

        return (
            False,
            (
                'La reserva de inventario '
                'no está convertida en venta.'
            )
        )

    if not order.payment_confirmed_at:

        return (
            False,
            (
                'El pedido no tiene una fecha '
                'de confirmación de pago.'
            )
        )

    return (
        True,
        'Venta confirmada correctamente.'
    )


# ============================================================
# MARCAR PEDIDO COMO PREPARANDO
# ============================================================

def mark_order_as_preparing(
    order
):

    with transaction.atomic():

        locked_order = (
            Order.objects
            .select_for_update()
            .get(
                pk=order.pk
            )
        )

        (
            transition_ok,
            transition_message
        ) = validate_admin_status_transition(
            locked_order.status,
            Order.Status.PREPARING
        )

        if not transition_ok:

            return (
                False,
                transition_message
            )

        (
            sale_ok,
            sale_message
        ) = _validate_finalized_sale(
            locked_order
        )

        if not sale_ok:

            return (
                False,
                sale_message
            )

        locked_order.status = (
            Order.Status.PREPARING
        )

        locked_order.save(
            update_fields=[
                'status',
                'updated_at',
            ]
        )

        order.status = (
            locked_order.status
        )

        return (
            True,
            (
                'Pedido marcado como '
                '"Preparando pedido".'
            )
        )


# ============================================================
# MARCAR PEDIDO COMO ENVIADO
# ============================================================

def mark_order_as_shipped(
    order,
    *,
    shipping_carrier=None,
    tracking_number=None,
    shipping_notes=None
):

    with transaction.atomic():

        locked_order = (
            Order.objects
            .select_for_update()
            .get(
                pk=order.pk
            )
        )

        (
            transition_ok,
            transition_message
        ) = validate_admin_status_transition(
            locked_order.status,
            Order.Status.SHIPPED
        )

        if not transition_ok:

            return (
                False,
                transition_message
            )

        (
            sale_ok,
            sale_message
        ) = _validate_finalized_sale(
            locked_order
        )

        if not sale_ok:

            return (
                False,
                sale_message
            )


        # =====================================================
        # DATOS DE DESPACHO
        # =====================================================

        if shipping_carrier is not None:

            locked_order.shipping_carrier = (
                shipping_carrier.strip()
            )

        if tracking_number is not None:

            locked_order.tracking_number = (
                tracking_number.strip()
            )

        if shipping_notes is not None:

            locked_order.shipping_notes = (
                shipping_notes.strip()
            )


        if not locked_order.shipping_carrier:

            return (
                False,
                (
                    'Debes registrar la transportadora '
                    'antes de marcar el pedido '
                    'como enviado.'
                )
            )

        if not locked_order.tracking_number:

            return (
                False,
                (
                    'Debes registrar el número de guía '
                    'antes de marcar el pedido '
                    'como enviado.'
                )
            )


        # =====================================================
        # CAMBIAR ESTADO
        # =====================================================

        locked_order.status = (
            Order.Status.SHIPPED
        )

        locked_order.shipped_at = (
            timezone.now()
        )

        locked_order.save(
            update_fields=[
                'status',
                'shipping_carrier',
                'tracking_number',
                'shipping_notes',
                'shipped_at',
                'updated_at',
            ]
        )


        order.status = (
            locked_order.status
        )

        order.shipping_carrier = (
            locked_order.shipping_carrier
        )

        order.tracking_number = (
            locked_order.tracking_number
        )

        order.shipping_notes = (
            locked_order.shipping_notes
        )

        order.shipped_at = (
            locked_order.shipped_at
        )


        return (
            True,
            'Pedido marcado como enviado.'
        )


# ============================================================
# MARCAR PEDIDO COMO ENTREGADO
# ============================================================

def mark_order_as_delivered(
    order
):

    with transaction.atomic():

        locked_order = (
            Order.objects
            .select_for_update()
            .get(
                pk=order.pk
            )
        )

        (
            transition_ok,
            transition_message
        ) = validate_admin_status_transition(
            locked_order.status,
            Order.Status.DELIVERED
        )

        if not transition_ok:

            return (
                False,
                transition_message
            )

        (
            sale_ok,
            sale_message
        ) = _validate_finalized_sale(
            locked_order
        )

        if not sale_ok:

            return (
                False,
                sale_message
            )

        if not locked_order.shipped_at:

            return (
                False,
                (
                    'El pedido no tiene una fecha '
                    'de envío registrada.'
                )
            )

        if not locked_order.shipping_carrier:

            return (
                False,
                (
                    'El pedido no tiene '
                    'transportadora registrada.'
                )
            )

        if not locked_order.tracking_number:

            return (
                False,
                (
                    'El pedido no tiene '
                    'número de guía registrado.'
                )
            )


        locked_order.status = (
            Order.Status.DELIVERED
        )

        locked_order.delivered_at = (
            timezone.now()
        )

        locked_order.save(
            update_fields=[
                'status',
                'delivered_at',
                'updated_at',
            ]
        )


        order.status = (
            locked_order.status
        )

        order.delivered_at = (
            locked_order.delivered_at
        )


        return (
            True,
            'Pedido marcado como entregado.'
        )


# ============================================================
# MARCAR SOLICITUD DE CAMBIO
# ============================================================

def mark_order_change_requested(
    order
):

    with transaction.atomic():

        locked_order = (
            Order.objects
            .select_for_update()
            .get(
                pk=order.pk
            )
        )

        (
            transition_ok,
            transition_message
        ) = validate_admin_status_transition(
            locked_order.status,
            Order.Status.CHANGE_REQUESTED
        )

        if not transition_ok:

            return (
                False,
                transition_message
            )

        (
            sale_ok,
            sale_message
        ) = _validate_finalized_sale(
            locked_order
        )

        if not sale_ok:

            return (
                False,
                sale_message
            )

        if not locked_order.delivered_at:

            return (
                False,
                (
                    'Solo puede registrarse un cambio '
                    'después de que el pedido '
                    'haya sido entregado.'
                )
            )


        locked_order.status = (
            Order.Status.CHANGE_REQUESTED
        )

        locked_order.save(
            update_fields=[
                'status',
                'updated_at',
            ]
        )


        order.status = (
            locked_order.status
        )


        return (
            True,
            'Solicitud de cambio registrada.'
        )
    