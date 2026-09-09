from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from cart.models import Order

from .models import CustomerProfile


WHOLESALE_ACTIVATION_MINIMUM = Decimal(
    '300000.00'
)

WHOLESALE_MAINTENANCE_MINIMUM = Decimal(
    '50000.00'
)

WHOLESALE_GRACE_MINIMUM = Decimal(
    '150000.00'
)


@transaction.atomic
def process_wholesale_benefit(order):
    """
    Procesa una compra con pago confirmado para determinar
    si activa, mantiene o reactiva la categoría mayorista.

    Cada pedido puede procesarse comercialmente una sola vez.
    """

    order = (
        Order.objects
        .select_for_update()
        .select_related(
            'customer'
        )
        .get(
            pk=order.pk
        )
    )

    # =========================================================
    # SOLO PEDIDOS CON PAGO CONFIRMADO
    # =========================================================

    if order.status != Order.Status.PAYMENT_CONFIRMED:
        return None

    # =========================================================
    # EVITAR DOBLE PROCESAMIENTO
    # =========================================================

    if order.commercial_benefit_processed_at:

        return (
            order.commercial_benefit_result
        )

    # =========================================================
    # PEDIDO SIN CUENTA
    # =========================================================

    if not order.customer:

        order.commercial_benefit_processed_at = (
            timezone.now()
        )

        order.commercial_benefit_result = (
            'Pedido sin cuenta: no aplica beneficio mayorista.'
        )

        order.save(
            update_fields=[
                'commercial_benefit_processed_at',
                'commercial_benefit_result',
                'updated_at',
            ]
        )

        return (
            order.commercial_benefit_result
        )

    # =========================================================
    # PERFIL COMERCIAL
    # =========================================================

    profile, _ = (
        CustomerProfile.objects
        .select_for_update()
        .get_or_create(
            user=order.customer
        )
    )

    profile.refresh_commercial_status()

    payment_date = (
        order.payment_confirmed_at
        or timezone.now()
    )

    result = (
        'Compra confirmada sin cambio de categoría.'
    )

    # =========================================================
    # CLIENTE DETAL O MAYORISTA VENCIDO
    # =========================================================

    if profile.commercial_status in {
        CustomerProfile.CommercialStatus.RETAIL,
        CustomerProfile.CommercialStatus.WHOLESALE_EXPIRED,
    }:

        activation_is_valid = (
            order.wholesale_activation_qualified
            and
            order.retail_reference_total
            >= WHOLESALE_ACTIVATION_MINIMUM
        )

        if activation_is_valid:

            profile.activate_wholesale(
                purchase_total=(
                    order.retail_reference_total
                ),
                purchase_date=payment_date
            )

            result = (
                'Mayorista activado por compra '
                'calificada desde $300.000 a precio detal.'
            )

        else:

            result = (
                'Compra confirmada sin requisito '
                'de activación mayorista.'
            )

    # =========================================================
    # MAYORISTA EN MANTENIMIENTO O ACTIVO
    # =========================================================

    elif profile.commercial_status in {
        CustomerProfile.CommercialStatus.WHOLESALE_MAINTENANCE,
        CustomerProfile.CommercialStatus.WHOLESALE_ACTIVE,
    }:

        if (
            order.total
            >= WHOLESALE_MAINTENANCE_MINIMUM
        ):

            profile.confirm_maintenance(
                purchase_total=order.total,
                purchase_date=payment_date
            )

            result = (
                'Categoría mayorista mantenida '
                'por compra confirmada desde $50.000.'
            )

        else:

            result = (
                'Compra confirmada inferior a $50.000. '
                'No reinicia el período de mantenimiento.'
            )

    # =========================================================
    # PERÍODO DE GRACIA
    # =========================================================

    elif (
        profile.commercial_status
        == CustomerProfile.CommercialStatus.WHOLESALE_GRACE
    ):

        if (
            order.total
            >= WHOLESALE_GRACE_MINIMUM
        ):

            profile.reactivate_from_grace(
                purchase_total=order.total,
                purchase_date=payment_date
            )

            result = (
                'Categoría mayorista reactivada '
                'durante el período de gracia '
                'por compra desde $150.000.'
            )

        else:

            result = (
                'Compra confirmada inferior a $150.000. '
                'El cliente continúa en período de gracia.'
            )

    # =========================================================
    # REGISTRAR PROCESAMIENTO
    # =========================================================

    order.commercial_benefit_processed_at = (
        timezone.now()
    )

    order.commercial_benefit_result = result

    order.save(
        update_fields=[
            'commercial_benefit_processed_at',
            'commercial_benefit_result',
            'updated_at',
        ]
    )

    return result