from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from .models import LiveCustomerAccess


User = get_user_model()


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
# LISTADO DE CLIENTES LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def live_customers(request):

    search = (
        request.GET
        .get(
            'q',
            ''
        )
        .strip()
    )


    users = (
        User.objects
        .filter(
            is_staff=False,
            is_superuser=False,
        )
        .order_by(
            'first_name',
            'last_name',
            'email',
            'username',
        )
    )


    if search:

        users = (
            users
            .filter(
                Q(
                    first_name__icontains=search
                )
                |
                Q(
                    last_name__icontains=search
                )
                |
                Q(
                    email__icontains=search
                )
                |
                Q(
                    username__icontains=search
                )
                |
                Q(
                    live_access__customer_code__icontains=search
                )
            )
            .distinct()
        )


    users = list(
        users[:150]
    )


    access_records = (
        LiveCustomerAccess.objects
        .filter(
            user__in=users
        )
        .select_related(
            'user'
        )
    )


    access_by_user = {
        access.user.pk: access
        for access in access_records
    }


    rows = []


    for user in users:

        access = (
            access_by_user.get(
                user.pk
            )
        )


        rows.append({
            'user': user,
            'access': access,
        })


    total_live_customers = (
        LiveCustomerAccess.objects
        .count()
    )


    active_live_customers = (
        LiveCustomerAccess.objects
        .filter(
            is_activated=True
        )
        .count()
    )


    inactive_live_customers = (
        LiveCustomerAccess.objects
        .filter(
            is_activated=False
        )
        .count()
    )


    context = {
        'rows': rows,
        'search': search,
        'total_live_customers': (
            total_live_customers
        ),
        'active_live_customers': (
            active_live_customers
        ),
        'inactive_live_customers': (
            inactive_live_customers
        ),
        'activation_amount': (
            LiveCustomerAccess.ACTIVATION_AMOUNT
        ),
    }


    return render(
        request,
        'live_sales/customers.html',
        context
    )


# ============================================================
# CREAR ACCESO PRONTY LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
@require_POST
def live_customer_create_access(
    request,
    user_id
):

    user = get_object_or_404(
        User,
        pk=user_id,
        is_staff=False,
        is_superuser=False,
    )


    with transaction.atomic():

        access, created = (
            LiveCustomerAccess.objects
            .get_or_create(
                user=user
            )
        )


    customer_name = (
        user.get_full_name().strip()
        or user.email
        or user.username
    )


    if created:

        messages.success(
            request,
            (
                f'Se creó el acceso de '
                f'Pronty Live para '
                f'{customer_name}. '
                f'Código permanente: '
                f'{access.customer_code}.'
            )
        )

    else:

        messages.info(
            request,
            (
                f'{customer_name} ya tiene '
                f'el código '
                f'{access.customer_code}.'
            )
        )


    return redirect(
        'live_sales:customers'
    )


# ============================================================
# ACTIVAR CLIENTE LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
@require_POST
def live_customer_activate(
    request,
    access_id
):

    with transaction.atomic():

        access = (
            LiveCustomerAccess.objects
            .select_for_update()
            .select_related(
                'user'
            )
            .get(
                pk=access_id
            )
        )


        if access.is_activated:

            messages.info(
                request,
                (
                    f'{access.customer_code} '
                    f'ya está activado.'
                )
            )


            return redirect(
                'live_sales:customers'
            )


        access.is_activated = True

        access.save()


    customer_name = (
        access.user
        .get_full_name()
        .strip()
        or access.user.email
        or access.user.username
    )


    messages.success(
        request,
        (
            f'Pronty Live activado para '
            f'{customer_name}. '
            f'Código: {access.customer_code}.'
        )
    )


    return redirect(
        'live_sales:customers'
    )


# ============================================================
# DESACTIVAR CLIENTE LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
@require_POST
def live_customer_deactivate(
    request,
    access_id
):

    with transaction.atomic():

        access = (
            LiveCustomerAccess.objects
            .select_for_update()
            .select_related(
                'user'
            )
            .get(
                pk=access_id
            )
        )


        if not access.is_activated:

            messages.info(
                request,
                (
                    f'{access.customer_code} '
                    f'ya está desactivado.'
                )
            )


            return redirect(
                'live_sales:customers'
            )


        access.is_activated = False

        access.save(
            update_fields=[
                'is_activated',
                'updated_at',
            ]
        )


    customer_name = (
        access.user
        .get_full_name()
        .strip()
        or access.user.email
        or access.user.username
    )


    messages.success(
        request,
        (
            f'Pronty Live fue desactivado '
            f'para {customer_name}.'
        )
    )


    return redirect(
        'live_sales:customers'
    )