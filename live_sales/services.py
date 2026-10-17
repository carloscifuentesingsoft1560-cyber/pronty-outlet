import io
from datetime import timedelta
from decimal import Decimal

import qrcode

from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from qrcode.constants import ERROR_CORRECT_M

from accounts.models import CustomerProfile
from cart.models import Order, OrderItem
from catalog.models import InventoryMovement, Product

from .models import (
    LiveAssignment,
    LiveProductQR,
    LiveSession,
    LiveSessionProduct,
)


# ============================================================
# CONSTANTES
# ============================================================

FREE_SHIPPING_MINIMUM = Decimal(
    '1000000.00'
)

WHOLESALE_ACTIVATION_MINIMUM = Decimal(
    '300000.00'
)


# ============================================================
# REFERENCIA DE INVENTARIO PARA LIVE
# ============================================================

def get_live_assignment_reference(
    assignment
):

    if not assignment.pk:

        raise ValidationError(
            (
                'La asignación debe estar guardada '
                'antes de generar su referencia.'
            )
        )


    return (
        f'LIVE-ASG-{assignment.pk:06d}'
    )


# ============================================================
# CREAR ASIGNACIÓN + RESERVAR INVENTARIO
# ============================================================

def reserve_new_live_assignment(
    assignment,
    *,
    created_by=None
):

    if assignment.pk:

        raise ValidationError(
            (
                'Esta asignación ya existe y no puede '
                'reservarse nuevamente como nueva.'
            )
        )


    with transaction.atomic():

        # ====================================================
        # PRODUCTO
        # ====================================================

        try:
            selected_product = (
                assignment.product
            )

        except Exception:
            selected_product = None


        if not selected_product:

            raise ValidationError(
                'Debes seleccionar un producto.'
            )


        product = (
            Product.objects
            .select_for_update()
            .get(
                pk=selected_product.pk
            )
        )


        assignment.product = (
            product
        )


        # ====================================================
        # CLIENTE
        # ====================================================

        try:
            customer = (
                assignment.customer
            )

        except Exception:
            customer = None


        if not customer:

            raise ValidationError(
                'Debes seleccionar un cliente.'
            )


        if not customer.is_activated:

            raise ValidationError(
                (
                    'El cliente no tiene activado '
                    'Pronty Live.'
                )
            )


        # ====================================================
        # LIVE
        # ====================================================

        try:
            live_session = (
                assignment.live_session
            )

        except Exception:
            live_session = None


        if not live_session:

            raise ValidationError(
                'Debes seleccionar un Live.'
            )


        if (
            live_session.status
            == LiveSession.Status.CANCELED
        ):

            raise ValidationError(
                (
                    'No se pueden realizar asignaciones '
                    'en un Live cancelado.'
                )
            )


        # ====================================================
        # PRODUCTO HABILITADO EN EL LIVE
        # ====================================================

        live_product = (
            LiveSessionProduct.objects
            .select_for_update()
            .filter(
                live_session=live_session,
                product=product,
                is_active=True,
            )
            .first()
        )


        if not live_product:

            raise ValidationError(
                (
                    'Este producto no está habilitado '
                    'para el Live seleccionado.'
                )
            )


        # ====================================================
        # CANTIDAD
        # ====================================================

        if (
            assignment.quantity is None
            or assignment.quantity <= 0
        ):

            raise ValidationError(
                (
                    'La cantidad debe ser '
                    'mayor que cero.'
                )
            )


        # ====================================================
        # STOCK
        # ====================================================

        if (
            assignment.quantity
            > product.stock
        ):

            raise ValidationError(
                (
                    f'No hay existencias suficientes. '
                    f'Disponibles actualmente: '
                    f'{product.stock}.'
                )
            )


        # ====================================================
        # PRECIO Y COSTO
        # ====================================================

        assignment.unit_price = (
            live_product.effective_price
        )

        assignment.unit_cost = (
            product.cost
        )

        assignment.status = (
            LiveAssignment.Status.ASSIGNED
        )

        assignment.created_by = (
            created_by
        )


        # ====================================================
        # GUARDAR ASIGNACIÓN
        # ====================================================

        assignment.full_clean()

        assignment.save()


        # ====================================================
        # CREAR RESERVA REAL
        # ====================================================

        reference = (
            get_live_assignment_reference(
                assignment
            )
        )


        InventoryMovement.objects.create(
            product=product,

            movement_type=(
                InventoryMovement
                .MovementType
                .RESERVATION
            ),

            quantity=(
                assignment.quantity
            ),

            reason=(
                f'Reserva de Pronty Live para '
                f'{customer.customer_code} '
                f'en {live_session.name}'
            ),

            reference=reference,

            created_by=created_by,
        )


        return assignment


# ============================================================
# LIBERAR ASIGNACIÓN LIVE
# ============================================================

def release_live_assignment(
    assignment,
    *,
    released_by=None
):

    if not assignment.pk:

        return (
            False,
            'La asignación no está guardada.'
        )


    with transaction.atomic():

        locked_assignment = (
            LiveAssignment.objects
            .select_for_update()
            .select_related(
                'product',
                'customer',
                'live_session',
                'order',
            )
            .get(
                pk=assignment.pk
            )
        )


        # ====================================================
        # YA LIBERADA
        # ====================================================

        if (
            locked_assignment.status
            == LiveAssignment.Status.RELEASED
        ):

            return (
                True,
                'La asignación ya estaba liberada.'
            )


        # ====================================================
        # YA CONVERTIDA EN PEDIDO
        # ====================================================

        if (
            locked_assignment.status
            == LiveAssignment.Status.ORDERED
        ):

            return (
                False,
                (
                    'La asignación ya fue convertida '
                    'en pedido y no puede liberarse '
                    'por este proceso.'
                )
            )


        # ====================================================
        # REFERENCIA LIVE
        # ====================================================

        reference = (
            get_live_assignment_reference(
                locked_assignment
            )
        )


        # ====================================================
        # BUSCAR RESERVA
        # ====================================================

        reservation = (
            InventoryMovement.objects
            .select_for_update()
            .filter(
                reference=reference,

                movement_type=(
                    InventoryMovement
                    .MovementType
                    .RESERVATION
                ),
            )
            .first()
        )


        if not reservation:

            return (
                False,
                (
                    'La asignación no tiene un movimiento '
                    'de reserva de inventario asociado.'
                )
            )


        # ====================================================
        # EVITAR DOBLE LIBERACIÓN
        # ====================================================

        already_released = (
            InventoryMovement.objects
            .filter(
                reference=reference,

                movement_type=(
                    InventoryMovement
                    .MovementType
                    .RESERVATION_RELEASE
                ),
            )
            .exists()
        )


        if already_released:

            return (
                False,
                (
                    'El inventario de esta asignación '
                    'ya fue liberado anteriormente.'
                )
            )


        # ====================================================
        # DEVOLVER INVENTARIO
        # ====================================================

        InventoryMovement.objects.create(
            product=(
                locked_assignment.product
            ),

            movement_type=(
                InventoryMovement
                .MovementType
                .RESERVATION_RELEASE
            ),

            quantity=(
                locked_assignment.quantity
            ),

            reason=(
                f'Liberación de asignación '
                f'Pronty Live '
                f'{locked_assignment.pk}'
            ),

            reference=reference,

            created_by=released_by,
        )


        # ====================================================
        # ACTUALIZAR ESTADO
        # ====================================================

        now = timezone.now()


        (
            LiveAssignment.objects
            .filter(
                pk=locked_assignment.pk
            )
            .update(
                status=(
                    LiveAssignment
                    .Status
                    .RELEASED
                ),

                released_at=now,

                updated_at=now,
            )
        )


        assignment.status = (
            LiveAssignment.Status.RELEASED
        )

        assignment.released_at = (
            now
        )


        return (
            True,
            'Asignación liberada correctamente.'
        )


# ============================================================
# CONVERTIR ASIGNACIONES LIVE EN PEDIDO
# ============================================================

def convert_live_assignments_to_order(
    assignment_ids,
    *,
    created_by=None
):

    assignment_ids = list(
        dict.fromkeys(
            assignment_ids
        )
    )


    if not assignment_ids:

        raise ValidationError(
            'No se seleccionaron asignaciones.'
        )


    with transaction.atomic():

        # ====================================================
        # CARGAR Y BLOQUEAR ASIGNACIONES
        # ====================================================

        assignments = list(
            LiveAssignment.objects
            .select_for_update()
            .select_related(
                'customer',
                'customer__user',
                'product',
                'live_session',
                'order',
            )
            .filter(
                pk__in=assignment_ids
            )
            .order_by(
                'id'
            )
        )


        if (
            len(assignments)
            != len(assignment_ids)
        ):

            raise ValidationError(
                (
                    'Una o más asignaciones '
                    'no fueron encontradas.'
                )
            )


        # ====================================================
        # ESTADO DE LAS ASIGNACIONES
        # ====================================================

        for assignment in assignments:

            if (
                assignment.status
                != LiveAssignment.Status.ASSIGNED
            ):

                raise ValidationError(
                    (
                        f'La asignación '
                        f'#{assignment.pk} '
                        f'no está en estado ASIGNADO.'
                    )
                )


            try:
                existing_order = (
                    assignment.order
                )

            except Exception:
                existing_order = None


            if existing_order:

                raise ValidationError(
                    (
                        f'La asignación '
                        f'#{assignment.pk} '
                        f'ya está vinculada '
                        f'a un pedido.'
                    )
                )


        # ====================================================
        # TODAS DEL MISMO CLIENTE
        # ====================================================

        customer_ids = {
            assignment.customer.pk
            for assignment in assignments
        }


        if len(customer_ids) != 1:

            raise ValidationError(
                (
                    'Todas las asignaciones seleccionadas '
                    'deben pertenecer al mismo cliente.'
                )
            )


        customer_access = (
            assignments[0].customer
        )


        if not customer_access.is_activated:

            raise ValidationError(
                (
                    'El cliente no tiene activado '
                    'Pronty Live.'
                )
            )


        user = (
            customer_access.user
        )


        # ====================================================
        # PERFIL
        # ====================================================

        try:

            profile = (
                CustomerProfile.objects
                .select_for_update()
                .get(
                    user=user
                )
            )

        except CustomerProfile.DoesNotExist:

            raise ValidationError(
                (
                    'El cliente no tiene un perfil '
                    'comercial registrado.'
                )
            )


        # ====================================================
        # DATOS DEL CLIENTE
        # ====================================================

        customer_name = (
            user.get_full_name().strip()
            or user.username
        )


        email = (
            user.email.strip()
            if user.email
            else ''
        )


        required_values = {
            'nombre': customer_name,
            'correo': email,
            'WhatsApp': profile.whatsapp,
            'departamento': profile.department,
            'ciudad': profile.city,
            'dirección': profile.address,
            'transportadora': (
                profile.preferred_carrier
            ),
        }


        missing = [
            label
            for label, value
            in required_values.items()
            if not value
        ]


        if missing:

            raise ValidationError(
                (
                    'Faltan datos del cliente para '
                    'crear el pedido: '
                    + ', '.join(missing)
                    + '.'
                )
            )


        # ====================================================
        # VALIDAR RESERVAS LIVE
        # ====================================================

        reservation_movements = []


        for assignment in assignments:

            live_reference = (
                get_live_assignment_reference(
                    assignment
                )
            )


            movement = (
                InventoryMovement.objects
                .select_for_update()
                .filter(
                    reference=live_reference,

                    product=(
                        assignment.product
                    ),

                    movement_type=(
                        InventoryMovement
                        .MovementType
                        .RESERVATION
                    ),
                )
                .first()
            )


            if not movement:

                raise ValidationError(
                    (
                        f'La asignación '
                        f'#{assignment.pk} '
                        f'no tiene una reserva activa '
                        f'de inventario.'
                    )
                )


            released = (
                InventoryMovement.objects
                .filter(
                    reference=live_reference,

                    movement_type=(
                        InventoryMovement
                        .MovementType
                        .RESERVATION_RELEASE
                    ),
                )
                .exists()
            )


            if released:

                raise ValidationError(
                    (
                        f'La reserva de la asignación '
                        f'#{assignment.pk} '
                        f'ya fue liberada.'
                    )
                )


            if (
                movement.quantity
                != assignment.quantity
            ):

                raise ValidationError(
                    (
                        f'La cantidad reservada de '
                        f'la asignación '
                        f'#{assignment.pk} '
                        f'no coincide con la asignación.'
                    )
                )


            reservation_movements.append(
                movement
            )


        # ====================================================
        # TOTAL DEL PEDIDO
        # ====================================================

        total = sum(
            (
                assignment.unit_price
                * assignment.quantity
            )
            for assignment in assignments
        )


        # ====================================================
        # TOTAL REFERENCIA DETAL
        # ====================================================

        retail_reference_total = sum(
            (
                assignment.product.retail_price
                * assignment.quantity
            )
            for assignment in assignments
        )


        # ====================================================
        # ACTIVACIÓN MAYORISTA
        # ====================================================

        wholesale_activation_qualified = (
            retail_reference_total
            >= WHOLESALE_ACTIVATION_MINIMUM
        )


        # ====================================================
        # ENVÍO GRATIS
        # ====================================================

        free_shipping = (
            total
            >= FREE_SHIPPING_MINIMUM
        )


        if free_shipping:

            shipping_cost = (
                Decimal('0.00')
            )

        else:

            shipping_cost = None


        # ====================================================
        # CREAR PEDIDO
        # ====================================================

        order = Order.objects.create(
            customer=user,

            customer_name=customer_name,

            email=email,

            whatsapp=(
                profile.whatsapp
            ),

            department=(
                profile.department
            ),

            city=(
                profile.city
            ),

            address=(
                profile.address
            ),

            delivery_notes=(
                profile.delivery_notes
            ),

            carrier=(
                profile.preferred_carrier
            ),

            retail_reference_total=(
                retail_reference_total
            ),

            wholesale_activation_qualified=(
                wholesale_activation_qualified
            ),

            free_shipping=(
                free_shipping
            ),

            shipping_cost=(
                shipping_cost
            ),

            total=(
                total
            ),

            status=(
                Order.Status.PENDING_PAYMENT
            ),

            inventory_reservation_status=(
                Order
                .ReservationStatus
                .ACTIVE
            ),
        )


        # ====================================================
        # RESERVA DE 3 DÍAS
        # ====================================================

        order.reservation_expires_at = (
            order.created_at
            + timedelta(days=3)
        )


        order.save(
            update_fields=[
                'reservation_expires_at',
                'updated_at',
            ]
        )


        # ====================================================
        # ITEMS DEL PEDIDO
        # ====================================================

        for assignment in assignments:

            subtotal = (
                assignment.unit_price
                * assignment.quantity
            )


            OrderItem.objects.create(
                order=order,

                product=(
                    assignment.product
                ),

                product_name=(
                    assignment.product.name
                ),

                sku=(
                    assignment.product.sku
                ),

                quantity=(
                    assignment.quantity
                ),

                unit_price=(
                    assignment.unit_price
                ),

                subtotal=(
                    subtotal
                ),
            )


        # ====================================================
        # TRANSFERIR RESERVAS LIVE AL PEDIDO
        # ====================================================
        #
        # NO se descuenta stock nuevamente.
        #
        # Solo cambiamos la referencia:
        #
        # LIVE-ASG-000003
        #
        #        ↓
        #
        # PRY-2026-000034
        # ====================================================

        for movement in reservation_movements:

            movement.reference = (
                order.order_number
            )

            movement.reason = (
                f'Reserva de Pronty Live '
                f'transferida al pedido '
                f'{order.order_number}'
            )

            movement.save(
                update_fields=[
                    'reference',
                    'reason',
                ]
            )


        # ====================================================
        # MARCAR ASIGNACIONES COMO ORDERED
        # ====================================================

        now = timezone.now()


        assignment_pks = [
            assignment.pk
            for assignment in assignments
        ]


        (
            LiveAssignment.objects
            .filter(
                pk__in=assignment_pks
            )
            .update(
                status=(
                    LiveAssignment
                    .Status
                    .ORDERED
                ),

                order=order,

                released_at=None,

                updated_at=now,
            )
        )


        return order


# ============================================================
# QR PERMANENTE DE PRODUCTO
# ============================================================

def get_or_create_product_qr(
    product
):
    """
    Obtiene o crea el código QR permanente de un producto.

    Cada producto tiene un único LiveProductQR.
    El UUID permanece igual independientemente del Live.
    """

    qr_record, _ = (
        LiveProductQR.objects
        .get_or_create(
            product=product,
            defaults={
                'is_active': True,
            },
        )
    )

    return qr_record


# ============================================================
# URL ABSOLUTA DEL QR
# ============================================================

def build_product_qr_absolute_url(
    request,
    qr_record
):
    """
    Construye la URL absoluta que se guardará dentro
    del código QR.
    """

    relative_url = reverse(
        'live_sales:scan_product',
        kwargs={
            'code': qr_record.code,
        },
    )


    return request.build_absolute_uri(
        relative_url
    )


# ============================================================
# GENERAR IMAGEN PNG DEL QR
# ============================================================

def build_product_qr_image_bytes(
    request,
    qr_record
):
    """
    Genera el PNG del QR permanente en memoria.
    """

    qr_url = (
        build_product_qr_absolute_url(
            request,
            qr_record,
        )
    )


    qr_code = qrcode.QRCode(
        version=None,

        error_correction=(
            ERROR_CORRECT_M
        ),

        box_size=10,

        border=4,
    )


    qr_code.add_data(
        qr_url
    )

    qr_code.make(
        fit=True
    )


    image = qr_code.make_image(
        fill_color='black',
        back_color='white',
    )


    buffer = io.BytesIO()


    image.save(
        buffer,
        'PNG',
    )


    buffer.seek(0)


    return buffer.getvalue()


# ============================================================
# GENERAR QR DE UN PRODUCTO
# ============================================================

def generate_product_qr_png(
    request,
    product
):
    """
    Obtiene o crea el LiveProductQR permanente del producto
    y devuelve la imagen PNG correspondiente.
    """

    qr_record = (
        get_or_create_product_qr(
            product
        )
    )


    return (
        build_product_qr_image_bytes(
            request,
            qr_record,
        )
    )