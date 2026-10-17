from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import (
    LiveAssignment,
    LiveCustomerAccess,
    LiveProductQR,
    LiveSession,
    LiveSessionProduct,
)

from .services import (
    reserve_new_live_assignment,
)


# ============================================================
# SEGURIDAD
# ============================================================

def _staff_required(user):

    return (
        user.is_authenticated
        and (
            user.is_staff
            or user.is_superuser
        )
    )


# ============================================================
# DASHBOARD DE PRONTY LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def live_dashboard(request):

    sessions = (
        LiveSession.objects
        .all()
        .order_by(
            '-scheduled_at',
            '-created_at',
        )[:10]
    )

    active_sessions = (
        LiveSession.objects
        .filter(
            status__in=[
                LiveSession.Status.SCHEDULED,
                LiveSession.Status.LIVE,
            ]
        )
        .count()
    )

    active_customers = (
        LiveCustomerAccess.objects
        .filter(
            is_activated=True
        )
        .count()
    )

    pending_assignments = (
        LiveAssignment.objects
        .filter(
            status=(
                LiveAssignment.Status.ASSIGNED
            )
        )
        .count()
    )

    context = {
        'sessions': sessions,
        'active_sessions': active_sessions,
        'active_customers': active_customers,
        'pending_assignments': pending_assignments,
    }

    return render(
        request,
        'live_sales/dashboard.html',
        context
    )


# ============================================================
# ESCANEO DE QR DE PRODUCTO
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def scan_product_qr(
    request,
    code
):

    # ========================================================
    # IDENTIFICAR QR Y PRODUCTO
    # ========================================================

    qr = get_object_or_404(
        LiveProductQR.objects.select_related(
            'product'
        ),
        code=code,
        is_active=True,
    )

    product = qr.product


    # ========================================================
    # LIVES DONDE EL PRODUCTO ESTÁ HABILITADO
    # ========================================================

    session_products = list(
        LiveSessionProduct.objects
        .select_related(
            'live_session',
            'product',
        )
        .filter(
            product=product,
            is_active=True,
            live_session__status__in=[
                LiveSession.Status.SCHEDULED,
                LiveSession.Status.LIVE,
            ]
        )
        .order_by(
            '-live_session__started_at',
            '-live_session__scheduled_at',
            '-live_session__created_at',
        )
    )


    # ========================================================
    # SESIÓN SELECCIONADA
    # ========================================================

    selected_session_product = None

    requested_live_id = (
        request.GET.get('live')
        or request.POST.get('live_session')
    )


    if requested_live_id:

        for session_product in session_products:

            if (
                str(
                    session_product.live_session.pk
                )
                == str(requested_live_id)
            ):

                selected_session_product = (
                    session_product
                )

                break


    # Si solamente hay un Live posible,
    # lo seleccionamos automáticamente.

    if (
        selected_session_product is None
        and len(session_products) == 1
    ):

        selected_session_product = (
            session_products[0]
        )


    # ========================================================
    # CREAR ASIGNACIÓN
    # ========================================================

    if request.method == 'POST':

        if not selected_session_product:

            messages.error(
                request,
                (
                    'Selecciona el Live en el que '
                    'se está realizando la venta.'
                )
            )

        else:

            customer_code = (
                request.POST
                .get(
                    'customer_code',
                    ''
                )
                .strip()
                .upper()
            )

            quantity_raw = (
                request.POST
                .get(
                    'quantity',
                    '1'
                )
                .strip()
            )


            # =================================================
            # CLIENTE
            # =================================================

            customer = (
                LiveCustomerAccess.objects
                .select_related(
                    'user'
                )
                .filter(
                    customer_code__iexact=(
                        customer_code
                    )
                )
                .first()
            )


            if not customer:

                messages.error(
                    request,
                    (
                        'No existe un cliente Live '
                        f'con el código {customer_code}.'
                    )
                )

            elif not customer.is_activated:

                messages.error(
                    request,
                    (
                        'El cliente existe, pero '
                        'Pronty Live no está activado '
                        'para su cuenta.'
                    )
                )

            else:

                # =============================================
                # CANTIDAD
                # =============================================

                try:

                    quantity = int(
                        quantity_raw
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    quantity = 0


                if quantity <= 0:

                    messages.error(
                        request,
                        (
                            'La cantidad debe ser '
                            'mayor que cero.'
                        )
                    )

                else:

                    # =========================================
                    # CREAR ASIGNACIÓN
                    # =========================================

                    assignment = (
                        LiveAssignment(
                            live_session=(
                                selected_session_product
                                .live_session
                            ),

                            customer=customer,

                            product=product,

                            quantity=quantity,
                        )
                    )


                    try:

                        reserve_new_live_assignment(
                            assignment,
                            created_by=request.user,
                        )


                    except ValidationError as error:

                        if getattr(
                            error,
                            'messages',
                            None
                        ):

                            error_message = ' '.join(
                                error.messages
                            )

                        else:

                            error_message = str(
                                error
                            )


                        messages.error(
                            request,
                            error_message
                        )


                    except Exception as error:

                        messages.error(
                            request,
                            (
                                'No fue posible realizar '
                                'la asignación. '
                                f'Detalle: {error}'
                            )
                        )


                    else:

                        customer_name = (
                            customer.user
                            .get_full_name()
                            .strip()
                            or customer.user.username
                        )


                        messages.success(
                            request,
                            (
                                f'{quantity} unidad(es) de '
                                f'{product.name} asignadas a '
                                f'{customer.customer_code} - '
                                f'{customer_name}.'
                            )
                        )


                        scan_url = reverse(
                            'live_sales:scan_product',
                            kwargs={
                                'code': qr.code
                            }
                        )


                        return redirect(
                            (
                                f'{scan_url}'
                                f'?live='
                                f'{selected_session_product.live_session.pk}'
                            )
                        )


    # ========================================================
    # ASIGNACIONES RECIENTES
    # ========================================================

    recent_assignments = (
        LiveAssignment.objects
        .select_related(
            'customer',
            'customer__user',
            'product',
            'live_session',
            'order',
        )
        .filter(
            product=product
        )
    )


    if selected_session_product:

        recent_assignments = (
            recent_assignments
            .filter(
                live_session=(
                    selected_session_product
                    .live_session
                )
            )
        )


    recent_assignments = (
        recent_assignments
        .order_by(
            '-assigned_at'
        )[:10]
    )


    # ========================================================
    # CONTEXTO
    # ========================================================

    context = {
        'qr': qr,
        'product': product,
        'session_products': session_products,
        'selected_session_product': (
            selected_session_product
        ),
        'recent_assignments': (
            recent_assignments
        ),
    }


    return render(
        request,
        'live_sales/scan_product.html',
        context
    )