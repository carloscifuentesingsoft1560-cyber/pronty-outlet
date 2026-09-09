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

from .models import CustomerProfile


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


@login_required(login_url='accounts:login')
def account_dashboard(request):

    # Un administrador no debe utilizar Mi cuenta
    # como si fuera un cliente.
    if request.user.is_staff or request.user.is_superuser:

        return redirect(
            '/admin/'
        )

    link_guest_orders_to_user(
        request.user
    )

    customer_profile = get_customer_profile(
        request.user
    )

    orders = (
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

    return render(
        request,
        'accounts/dashboard.html',
        {
            'orders': orders,
            'customer_profile': customer_profile,
        }
    )


@login_required(login_url='accounts:login')
def order_detail(request, order_number):

    if request.user.is_staff or request.user.is_superuser:

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

    return render(
        request,
        'accounts/order_detail.html',
        {
            'order': order
        }
    )


def account_login(request):

    if request.user.is_authenticated:

        if request.user.is_staff or request.user.is_superuser:

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
                'Ingresa tu correo electrónico y contraseña.'
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
                'El correo o la contraseña no son correctos.'
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
                    'Esta cuenta corresponde a la administración '
                    'de Pronty. Ingresa desde el panel administrativo.'
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
                'El correo o la contraseña no son correctos.'
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
            'Has iniciado sesión correctamente.'
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


def account_register(request):

    if request.user.is_authenticated:

        if request.user.is_staff or request.user.is_superuser:

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
                'Completa todos los campos obligatorios.'
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
                'Ingresa un correo electrónico válido.'
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
                'Las contraseñas no coinciden.'
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
                'Ya existe una cuenta registrada con este correo.'
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

                # Seguridad explícita:
                # un cliente nunca debe tener permisos administrativos.

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
                'Ya existe una cuenta registrada con este correo.'
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
            'Tu cuenta fue creada correctamente.'
        )

        return redirect(
            'accounts:dashboard'
        )

    return render(
        request,
        'accounts/register.html'
    )


@require_POST
def account_logout(request):

    logout(
        request
    )

    messages.success(
        request,
        'Has cerrado sesión correctamente.'
    )

    return redirect(
        'home'
    )