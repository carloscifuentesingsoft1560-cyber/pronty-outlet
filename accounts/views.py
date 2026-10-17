from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import override
from django.views.decorators.http import require_POST

from cart.models import Order
from cart.reservation_services import expire_order_if_due

from live_sales.models import (
    LiveAssignment,
    LiveCustomerAccess,
)
from live_sales.services import (
    convert_live_assignments_to_order,
)

from .models import CustomerProfile


# ============================================================
# USUARIO CLIENTE
# ============================================================

def is_customer_user(user):
    """
    Retorna True solamente para usuarios que pertenecen
    al frontend de clientes de Pronty.
    """

    return (
        user.is_authenticated
        and not user.is_staff
        and not user.is_superuser
    )


# ============================================================
# VINCULAR PEDIDOS DE INVITADO
# ============================================================

def link_guest_orders_to_user(user):
    """
    Vincula pedidos anteriores realizados como invitado
    con la cuenta de un cliente Pronty.

    Los administradores nunca reciben pedidos comerciales.
    """

    if not is_customer_user(user):
        return 0

    if not user.email:
        return 0

    email = user.email.strip().lower()

    updated_orders = (
        Order.objects
        .filter(
            customer__isnull=True,
            email__iexact=email
        )
        .update(
            customer=user
        )
    )

    return updated_orders


# ============================================================
# PERFIL COMERCIAL
# ============================================================

def get_customer_profile(user):
    """
    Obtiene o crea el perfil comercial exclusivamente
    para clientes de Pronty.
    """

    if not is_customer_user(user):
        return None

    profile, _ = (
        CustomerProfile.objects
        .get_or_create(
            user=user
        )
    )

    profile.refresh_commercial_status()

    return profile


# ============================================================
# MI CUENTA
# ============================================================

@login_required(
    login_url='accounts:login'
)
def account_dashboard(request):

    # ========================================================
    # ADMINISTRADORES NO USAN MI CUENTA
    # ========================================================

    if (
        request.user.is_staff
        or request.user.is_superuser
    ):

        return redirect(
            '/admin/'
        )

    # ========================================================
    # PEDIDOS PREVIOS
    # ========================================================

    link_guest_orders_to_user(
        request.user
    )

    customer_profile = get_customer_profile(
        request.user
    )

    orders = list(
        Order.objects
        .filter(
            customer=request.user
        )
        .prefetch_related(
            'items'
        )
        .order_by(
            '-created_at'
        )
    )

    # ========================================================
    # COMPROBAR RESERVAS VENCIDAS
    # ========================================================

    for order in orders:

        expired = expire_order_if_due(
            order
        )

        if expired:

            order.refresh_from_db()

    # ========================================================
    # PRONTY LIVE DEL CLIENTE
    # ========================================================

    live_access = (
        LiveCustomerAccess.objects
        .filter(
            user=request.user,
            is_activated=True,
        )
        .first()
    )

    live_assignments = []

    if live_access:

        live_assignments = list(
            LiveAssignment.objects
            .select_related(
                'product',
                'live_session',
                'order',
            )
            .filter(
                customer=live_access,
                status=(
                    LiveAssignment
                    .Status
                    .ASSIGNED
                ),
            )
            .order_by(
                '-assigned_at'
            )
        )

    # ========================================================
    # RENDER
    # ========================================================

    return render(
        request,
        'accounts/dashboard.html',
        {
            'orders': orders,
            'customer_profile': customer_profile,
            'live_access': live_access,
            'live_assignments': live_assignments,
        }
    )


# ============================================================
# GENERAR PEDIDO DESDE PRONTY LIVE
# ============================================================

@login_required(
    login_url='accounts:login'
)
@require_POST
def generate_live_order(request):
    """
    Permite al cliente convertir sus asignaciones activas
    de Pronty Live en un pedido real.

    Seguridad:
    - solamente asignaciones del usuario autenticado;
    - solamente ASSIGNED;
    - el servicio vuelve a validar todo dentro de transacción;
    - no se vuelve a descontar inventario.
    """

    # ========================================================
    # ADMINISTRADORES NO GENERAN PEDIDOS COMO CLIENTES
    # ========================================================

    if (
        request.user.is_staff
        or request.user.is_superuser
    ):

        return redirect(
            '/admin/'
        )

    # ========================================================
    # ACCESO LIVE
    # ========================================================

    live_access = (
        LiveCustomerAccess.objects
        .filter(
            user=request.user,
            is_activated=True,
        )
        .first()
    )

    if not live_access:

        messages.error(
            request,
            (
                'Tu cuenta no tiene activado '
                'Pronty Live.'
            )
        )

        return redirect(
            'accounts:dashboard'
        )

    # ========================================================
    # IDS SELECCIONADOS
    # ========================================================

    raw_assignment_ids = (
        request.POST.getlist(
            'assignment_ids'
        )
    )

    if not raw_assignment_ids:

        messages.warning(
            request,
            (
                'Selecciona al menos un producto '
                'de Pronty Live.'
            )
        )

        return redirect(
            'accounts:dashboard'
        )

    try:

        assignment_ids = sorted({
            int(assignment_id)
            for assignment_id
            in raw_assignment_ids
        })

    except (
        TypeError,
        ValueError,
    ):

        messages.error(
            request,
            (
                'La selección de productos '
                'no es válida.'
            )
        )

        return redirect(
            'accounts:dashboard'
        )

    if not assignment_ids:

        messages.warning(
            request,
            (
                'Selecciona al menos un producto '
                'de Pronty Live.'
            )
        )

        return redirect(
            'accounts:dashboard'
        )

    # ========================================================
    # VALIDAR PROPIEDAD DE LAS ASIGNACIONES
    # ========================================================

    valid_assignment_ids = list(
        LiveAssignment.objects
        .filter(
            pk__in=assignment_ids,
            customer=live_access,
            status=(
                LiveAssignment
                .Status
                .ASSIGNED
            ),
        )
        .values_list(
            'pk',
            flat=True
        )
    )

    if (
        len(valid_assignment_ids)
        != len(assignment_ids)
    ):

        messages.error(
            request,
            (
                'Uno o más productos seleccionados '
                'ya no están disponibles para '
                'generar el pedido. '
                'Actualiza la página e inténtalo nuevamente.'
            )
        )

        return redirect(
            'accounts:dashboard'
        )

    # ========================================================
    # CONVERTIR A PEDIDO
    # ========================================================

    try:

        order = (
            convert_live_assignments_to_order(
                valid_assignment_ids,
                created_by=request.user,
            )
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

        return redirect(
            'accounts:dashboard'
        )

    except Exception as error:

        messages.error(
            request,
            (
                'No fue posible generar el pedido '
                'de Pronty Live. '
                f'Detalle: {error}'
            )
        )

        return redirect(
            'accounts:dashboard'
        )

    # ========================================================
    # ÉXITO
    # ========================================================

    messages.success(
        request,
        (
            'Tu pedido de Pronty Live fue creado '
            f'correctamente: {order.order_number}. '
            'Ahora puedes continuar con el pago.'
        )
    )

    return redirect(
        'accounts:order_detail',
        order_number=order.order_number
    )


# ============================================================
# DETALLE DE PEDIDO
# ============================================================

@login_required(
    login_url='accounts:login'
)
def order_detail(
    request,
    order_number
):

    if (
        request.user.is_staff
        or request.user.is_superuser
    ):

        return redirect(
            '/admin/'
        )

    link_guest_orders_to_user(
        request.user
    )

    get_customer_profile(
        request.user
    )

    order = get_object_or_404(
        Order.objects.prefetch_related(
            'items'
        ),
        order_number=order_number,
        customer=request.user
    )

    # ========================================================
    # COMPROBAR VENCIMIENTO
    # ========================================================

    expired = expire_order_if_due(
        order
    )

    if expired:

        order.refresh_from_db()

        messages.warning(
            request,
            (
                'La reserva de este pedido venció. '
                'Los productos fueron liberados '
                'y regresaron al inventario.'
            )
        )

    return render(
        request,
        'accounts/order_detail.html',
        {
            'order': order
        }
    )


# ============================================================
# LOGIN
# ============================================================

def account_login(request):

    if request.user.is_authenticated:

        if (
            request.user.is_staff
            or request.user.is_superuser
        ):

            return redirect(
                '/admin/'
            )

        return redirect(
            'accounts:dashboard'
        )

    if request.method == 'POST':

        email = (
            request.POST
            .get(
                'email',
                ''
            )
            .strip()
            .lower()
        )

        password = request.POST.get(
            'password',
            ''
        )

        if not email or not password:

            messages.error(
                request,
                (
                    'Ingresa tu correo electrónico '
                    'y contraseña.'
                )
            )

            return render(
                request,
                'accounts/login.html',
                {
                    'email': email
                }
            )

        user_record = (
            User.objects
            .filter(
                email__iexact=email
            )
            .first()
        )

        if not user_record:

            messages.error(
                request,
                (
                    'El correo o la contraseña '
                    'no son correctos.'
                )
            )

            return render(
                request,
                'accounts/login.html',
                {
                    'email': email
                }
            )

        # =====================================================
        # ADMINISTRADORES NO ENTRAN POR LOGIN DE CLIENTES
        # =====================================================

        if (
            user_record.is_staff
            or user_record.is_superuser
        ):

            messages.error(
                request,
                (
                    'Esta cuenta corresponde a la '
                    'administración de Pronty. '
                    'Ingresa desde el panel administrativo.'
                )
            )

            return render(
                request,
                'accounts/login.html',
                {
                    'email': email
                }
            )

        user = authenticate(
            request,
            username=user_record.username,
            password=password
        )

        if user is None:

            messages.error(
                request,
                (
                    'El correo o la contraseña '
                    'no son correctos.'
                )
            )

            return render(
                request,
                'accounts/login.html',
                {
                    'email': email
                }
            )

        login(
            request,
            user
        )

        link_guest_orders_to_user(
            user
        )

        get_customer_profile(
            user
        )

        messages.success(
            request,
            (
                'Has iniciado sesión '
                'correctamente.'
            )
        )

        next_url = request.GET.get(
            'next',
            ''
        )

        if (
            next_url
            and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={
                    request.get_host()
                },
                require_https=request.is_secure()
            )
        ):

            return redirect(
                next_url
            )

        return redirect(
            'accounts:dashboard'
        )

    return render(
        request,
        'accounts/login.html'
    )


# ============================================================
# REGISTRO
# ============================================================

def account_register(request):

    if request.user.is_authenticated:

        if (
            request.user.is_staff
            or request.user.is_superuser
        ):

            return redirect(
                '/admin/'
            )

        return redirect(
            'accounts:dashboard'
        )

    if request.method == 'POST':

        first_name = (
            request.POST
            .get(
                'first_name',
                ''
            )
            .strip()
        )

        last_name = (
            request.POST
            .get(
                'last_name',
                ''
            )
            .strip()
        )

        email = (
            request.POST
            .get(
                'email',
                ''
            )
            .strip()
            .lower()
        )

        password = request.POST.get(
            'password',
            ''
        )

        password_confirm = request.POST.get(
            'password_confirm',
            ''
        )

        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
        }

        # =====================================================
        # CAMPOS OBLIGATORIOS
        # =====================================================

        if (
            not first_name
            or not email
            or not password
            or not password_confirm
        ):

            messages.error(
                request,
                (
                    'Completa todos los '
                    'campos obligatorios.'
                )
            )

            return render(
                request,
                'accounts/register.html',
                {
                    'form_data': form_data
                }
            )

        # =====================================================
        # CORREO VÁLIDO
        # =====================================================

        try:

            validate_email(
                email
            )

        except ValidationError:

            messages.error(
                request,
                (
                    'Ingresa un correo '
                    'electrónico válido.'
                )
            )

            return render(
                request,
                'accounts/register.html',
                {
                    'form_data': form_data
                }
            )

        # =====================================================
        # CONTRASEÑAS COINCIDEN
        # =====================================================

        if password != password_confirm:

            messages.error(
                request,
                (
                    'Las contraseñas '
                    'no coinciden.'
                )
            )

            return render(
                request,
                'accounts/register.html',
                {
                    'form_data': form_data
                }
            )

        # =====================================================
        # CORREO YA REGISTRADO
        # =====================================================

        if User.objects.filter(
            email__iexact=email
        ).exists():

            messages.error(
                request,
                (
                    'Ya existe una cuenta '
                    'registrada con este correo.'
                )
            )

            return render(
                request,
                'accounts/register.html',
                {
                    'form_data': form_data
                }
            )

        # =====================================================
        # VALIDACIÓN DE CONTRASEÑA
        # =====================================================

        temporary_user = User(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name
        )

        try:

            with override('es'):

                validate_password(
                    password,
                    user=temporary_user
                )

        except ValidationError as error:

            password_errors = ' '.join(
                error.messages
            )

            messages.error(
                request,
                password_errors
            )

            return render(
                request,
                'accounts/register.html',
                {
                    'form_data': form_data
                }
            )

        # =====================================================
        # CREACIÓN DEL CLIENTE
        # =====================================================

        try:

            with transaction.atomic():

                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )

                user.is_staff = False
                user.is_superuser = False

                user.save(
                    update_fields=[
                        'is_staff',
                        'is_superuser',
                    ]
                )

                CustomerProfile.objects.get_or_create(
                    user=user
                )

                link_guest_orders_to_user(
                    user
                )

        except IntegrityError:

            messages.error(
                request,
                (
                    'Ya existe una cuenta '
                    'registrada con este correo.'
                )
            )

            return render(
                request,
                'accounts/register.html',
                {
                    'form_data': form_data
                }
            )

        login(
            request,
            user
        )

        messages.success(
            request,
            (
                'Tu cuenta fue creada '
                'correctamente.'
            )
        )

        return redirect(
            'accounts:dashboard'
        )

    return render(
        request,
        'accounts/register.html'
    )


# ============================================================
# CERRAR SESIÓN
# ============================================================

@require_POST
def account_logout(request):

    logout(
        request
    )

    messages.success(
        request,
        (
            'Has cerrado sesión '
            'correctamente.'
        )
    )

    return redirect(
        'home'
    )