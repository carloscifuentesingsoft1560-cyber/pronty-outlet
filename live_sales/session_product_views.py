from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from catalog.models import Product

from .models import (
    LiveSession,
    LiveSessionProduct,
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
# PRODUCTOS DE UN LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def live_session_products(
    request,
    session_id
):

    session = get_object_or_404(
        LiveSession,
        pk=session_id,
    )


    search = (
        request.GET
        .get(
            'q',
            ''
        )
        .strip()
    )


    # ========================================================
    # PRODUCTOS YA HABILITADOS
    # ========================================================

    session_products = (
        LiveSessionProduct.objects
        .select_related(
            'product'
        )
        .filter(
            live_session=session
        )
        .order_by(
            'product__name'
        )
    )


    # ========================================================
    # CATÁLOGO DISPONIBLE PARA AGREGAR
    # ========================================================

    existing_product_ids = (
        LiveSessionProduct.objects
        .filter(
            live_session=session
        )
        .values_list(
            'product__pk',
            flat=True,
        )
    )


    available_products = (
        Product.objects
        .exclude(
            pk__in=existing_product_ids
        )
        .order_by(
            'name'
        )
    )


    if search:

        available_products = (
            available_products
            .filter(
                Q(
                    name__icontains=search
                )
                |
                Q(
                    sku__icontains=search
                )
            )
        )


    available_products = (
        available_products[:100]
    )


    context = {
        'session': session,
        'session_products': session_products,
        'available_products': available_products,
        'search': search,
        'can_edit': (
            session.status
            in {
                LiveSession.Status.SCHEDULED,
                LiveSession.Status.LIVE,
            }
        ),
    }


    return render(
        request,
        'live_sales/session_products.html',
        context
    )


# ============================================================
# AGREGAR PRODUCTO AL LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
@require_POST
def live_session_product_add(
    request,
    session_id
):

    session = get_object_or_404(
        LiveSession,
        pk=session_id,
    )


    if (
        session.status
        not in {
            LiveSession.Status.SCHEDULED,
            LiveSession.Status.LIVE,
        }
    ):

        messages.error(
            request,
            (
                'No se pueden agregar productos '
                'a un Live finalizado o cancelado.'
            )
        )

        return redirect(
            'live_sales:session_products',
            session_id=session.pk,
        )


    product_id = (
        request.POST
        .get(
            'product_id'
        )
    )


    live_price_raw = (
        request.POST
        .get(
            'live_price',
            ''
        )
        .strip()
    )


    product = get_object_or_404(
        Product,
        pk=product_id,
    )


    live_price = None


    if live_price_raw:

        try:

            live_price = Decimal(
                live_price_raw
            )

        except InvalidOperation:

            messages.error(
                request,
                (
                    'El precio especial del Live '
                    'no tiene un formato válido.'
                )
            )

            return redirect(
                'live_sales:session_products',
                session_id=session.pk,
            )


        if live_price <= 0:

            messages.error(
                request,
                (
                    'El precio especial del Live '
                    'debe ser mayor que cero.'
                )
            )

            return redirect(
                'live_sales:session_products',
                session_id=session.pk,
            )


    try:

        with transaction.atomic():

            LiveSessionProduct.objects.create(
                live_session=session,
                product=product,
                is_active=True,
                live_price=live_price,
            )


    except IntegrityError:

        messages.warning(
            request,
            (
                f'{product.name} ya pertenece '
                f'a este Live.'
            )
        )


    else:

        messages.success(
            request,
            (
                f'{product.name} fue agregado '
                f'a {session.name}.'
            )
        )


    return redirect(
        'live_sales:session_products',
        session_id=session.pk,
    )


# ============================================================
# ACTUALIZAR PRODUCTO DEL LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
@require_POST
def live_session_product_update(
    request,
    session_product_id
):

    session_product = get_object_or_404(
        LiveSessionProduct.objects.select_related(
            'live_session',
            'product',
        ),
        pk=session_product_id,
    )


    session = (
        session_product.live_session
    )


    if (
        session.status
        not in {
            LiveSession.Status.SCHEDULED,
            LiveSession.Status.LIVE,
        }
    ):

        messages.error(
            request,
            (
                'No se pueden modificar productos '
                'de un Live finalizado o cancelado.'
            )
        )

        return redirect(
            'live_sales:session_products',
            session_id=session.pk,
        )


    live_price_raw = (
        request.POST
        .get(
            'live_price',
            ''
        )
        .strip()
    )


    is_active = (
        request.POST
        .get(
            'is_active'
        )
        == 'on'
    )


    live_price = None


    if live_price_raw:

        try:

            live_price = Decimal(
                live_price_raw
            )

        except InvalidOperation:

            messages.error(
                request,
                (
                    'El precio especial del Live '
                    'no tiene un formato válido.'
                )
            )

            return redirect(
                'live_sales:session_products',
                session_id=session.pk,
            )


        if live_price <= 0:

            messages.error(
                request,
                (
                    'El precio especial del Live '
                    'debe ser mayor que cero.'
                )
            )

            return redirect(
                'live_sales:session_products',
                session_id=session.pk,
            )


    session_product.live_price = (
        live_price
    )

    session_product.is_active = (
        is_active
    )


    session_product.save(
        update_fields=[
            'live_price',
            'is_active',
            'updated_at',
        ]
    )


    messages.success(
        request,
        (
            f'{session_product.product.name} '
            f'fue actualizado.'
        )
    )


    return redirect(
        'live_sales:session_products',
        session_id=session.pk,
    )


# ============================================================
# QUITAR PRODUCTO DEL LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
@require_POST
def live_session_product_remove(
    request,
    session_product_id
):

    session_product = get_object_or_404(
        LiveSessionProduct.objects.select_related(
            'live_session',
            'product',
        ),
        pk=session_product_id,
    )


    session = (
        session_product.live_session
    )


    product_name = (
        session_product.product.name
    )


    if (
        session.status
        not in {
            LiveSession.Status.SCHEDULED,
            LiveSession.Status.LIVE,
        }
    ):

        messages.error(
            request,
            (
                'No se pueden quitar productos '
                'de un Live finalizado o cancelado.'
            )
        )

        return redirect(
            'live_sales:session_products',
            session_id=session.pk,
        )


    session_product.delete()


    messages.success(
        request,
        (
            f'{product_name} fue retirado '
            f'de {session.name}.'
        )
    )


    return redirect(
        'live_sales:session_products',
        session_id=session.pk,
    )