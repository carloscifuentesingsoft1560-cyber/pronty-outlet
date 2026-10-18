from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from catalog.models import Product

from .forms import LiveSessionForm

from .models import (
    LiveAssignment,
    LiveCustomerAccess,
    LiveProductQR,
    LiveSession,
    LiveSessionProduct,
)

from .services import (
    build_product_qr_image_bytes,
    get_or_create_product_qr,
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


    qr_products = (
        LiveProductQR.objects
        .filter(
            is_active=True
        )
        .count()
    )


    context = {
        'sessions': sessions,
        'active_sessions': active_sessions,
        'active_customers': active_customers,
        'pending_assignments': pending_assignments,
        'qr_products': qr_products,
    }


    return render(
        request,
        'live_sales/dashboard.html',
        context
    )


# ============================================================
# LISTADO DE LIVES
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def live_sessions(request):

    search = (
        request.GET
        .get(
            'q',
            ''
        )
        .strip()
    )


    sessions = (
        LiveSession.objects
        .all()
    )


    if search:

        sessions = (
            sessions
            .filter(
                Q(
                    name__icontains=search
                )
                |
                Q(
                    notes__icontains=search
                )
            )
        )


    sessions = (
        sessions
        .order_by(
            '-scheduled_at',
            '-created_at',
        )
    )


    context = {
        'sessions': sessions,
        'search': search,
    }


    return render(
        request,
        'live_sales/sessions.html',
        context
    )


# ============================================================
# CREAR LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def live_session_create(request):

    if request.method == 'POST':

        form = LiveSessionForm(
            request.POST
        )


        if form.is_valid():

            session = form.save(
                commit=False
            )

            session.status = (
                LiveSession.Status.SCHEDULED
            )

            session.created_by = (
                request.user
            )

            session.save()


            messages.success(
                request,
                (
                    f'El Live "{session.name}" '
                    f'fue creado correctamente.'
                )
            )


            return redirect(
                'live_sales:sessions'
            )

    else:

        form = LiveSessionForm()


    context = {
        'form': form,
        'page_title': 'Crear Live',
        'submit_text': 'Crear Live',
        'session': None,
    }


    return render(
        request,
        'live_sales/session_form.html',
        context
    )


# ============================================================
# EDITAR LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def live_session_edit(
    request,
    session_id
):

    session = get_object_or_404(
        LiveSession,
        pk=session_id,
    )


    if request.method == 'POST':

        form = LiveSessionForm(
            request.POST,
            instance=session,
        )


        if form.is_valid():

            session = form.save()


            messages.success(
                request,
                (
                    f'El Live "{session.name}" '
                    f'fue actualizado.'
                )
            )


            return redirect(
                'live_sales:sessions'
            )

    else:

        form = LiveSessionForm(
            instance=session
        )


    context = {
        'form': form,
        'page_title': 'Editar Live',
        'submit_text': 'Guardar cambios',
        'session': session,
    }


    return render(
        request,
        'live_sales/session_form.html',
        context
    )


# ============================================================
# INICIAR LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
@require_POST
def live_session_start(
    request,
    session_id
):

    with transaction.atomic():

        session = (
            LiveSession.objects
            .select_for_update()
            .get(
                pk=session_id
            )
        )


        if (
            session.status
            == LiveSession.Status.LIVE
        ):

            messages.info(
                request,
                (
                    'Este Live ya está '
                    'en transmisión.'
                )
            )


            return redirect(
                'live_sales:sessions'
            )


        if (
            session.status
            in [
                LiveSession.Status.CLOSED,
                LiveSession.Status.CANCELED,
            ]
        ):

            messages.error(
                request,
                (
                    'Este Live ya fue cerrado '
                    'o cancelado y no puede iniciarse.'
                )
            )


            return redirect(
                'live_sales:sessions'
            )


        session.status = (
            LiveSession.Status.LIVE
        )

        session.started_at = (
            timezone.now()
        )

        session.ended_at = None


        session.save(
            update_fields=[
                'status',
                'started_at',
                'ended_at',
                'updated_at',
            ]
        )


    messages.success(
        request,
        (
            f'El Live "{session.name}" '
            f'ahora está EN VIVO.'
        )
    )


    return redirect(
        'live_sales:sessions'
    )


# ============================================================
# FINALIZAR LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
@require_POST
def live_session_close(
    request,
    session_id
):

    with transaction.atomic():

        session = (
            LiveSession.objects
            .select_for_update()
            .get(
                pk=session_id
            )
        )


        if (
            session.status
            == LiveSession.Status.CLOSED
        ):

            messages.info(
                request,
                'Este Live ya está finalizado.'
            )


            return redirect(
                'live_sales:sessions'
            )


        if (
            session.status
            != LiveSession.Status.LIVE
        ):

            messages.error(
                request,
                (
                    'Solo se puede finalizar '
                    'un Live que esté EN VIVO.'
                )
            )


            return redirect(
                'live_sales:sessions'
            )


        session.status = (
            LiveSession.Status.CLOSED
        )

        session.ended_at = (
            timezone.now()
        )


        session.save(
            update_fields=[
                'status',
                'ended_at',
                'updated_at',
            ]
        )


    messages.success(
        request,
        (
            f'El Live "{session.name}" '
            f'fue finalizado correctamente.'
        )
    )


    return redirect(
        'live_sales:sessions'
    )


# ============================================================
# CANCELAR LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
@require_POST
def live_session_cancel(
    request,
    session_id
):

    with transaction.atomic():

        session = (
            LiveSession.objects
            .select_for_update()
            .get(
                pk=session_id
            )
        )


        if (
            session.status
            == LiveSession.Status.CANCELED
        ):

            messages.info(
                request,
                'Este Live ya está cancelado.'
            )


            return redirect(
                'live_sales:sessions'
            )


        if (
            session.status
            == LiveSession.Status.LIVE
        ):

            messages.error(
                request,
                (
                    'Un Live que está EN VIVO '
                    'debe finalizarse, no cancelarse.'
                )
            )


            return redirect(
                'live_sales:sessions'
            )


        if (
            session.status
            == LiveSession.Status.CLOSED
        ):

            messages.error(
                request,
                (
                    'Un Live finalizado no puede '
                    'marcarse como cancelado.'
                )
            )


            return redirect(
                'live_sales:sessions'
            )


        session.status = (
            LiveSession.Status.CANCELED
        )


        session.save(
            update_fields=[
                'status',
                'updated_at',
            ]
        )


    messages.success(
        request,
        (
            f'El Live "{session.name}" '
            f'fue cancelado.'
        )
    )


    return redirect(
        'live_sales:sessions'
    )


# ============================================================
# PRODUCTOS Y CÓDIGOS QR
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def live_products(request):

    search = (
        request.GET
        .get(
            'q',
            ''
        )
        .strip()
    )


    if request.method == 'POST':

        product_pk = (
            request.POST
            .get(
                'product_id'
            )
        )


        product = get_object_or_404(
            Product,
            pk=product_pk,
        )


        qr_record = (
            get_or_create_product_qr(
                product
            )
        )


        messages.success(
            request,
            (
                f'El QR permanente de '
                f'{product.name} está listo.'
            )
        )


        return redirect(
            'live_sales:product_qr_label',
            code=qr_record.code,
        )


    products = (
        Product.objects
        .select_related(
            'category',
            'brand',
        )
        .all()
    )


    if search:

        products = (
            products
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


    products = list(
        products
        .order_by(
            'name'
        )[:100]
    )


    product_pks = [
        product.pk
        for product in products
    ]


    qr_records = (
        LiveProductQR.objects
        .filter(
            product__pk__in=product_pks
        )
        .select_related(
            'product'
        )
    )


    qr_by_product = {
        qr_record.product.pk: qr_record
        for qr_record in qr_records
    }


    rows = [
        {
            'product': product,
            'qr': (
                qr_by_product.get(
                    product.pk
                )
            ),
        }
        for product in products
    ]


    context = {
        'rows': rows,
        'search': search,
    }


    return render(
        request,
        'live_sales/products.html',
        context
    )


# ============================================================
# IMAGEN PNG DEL QR
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def product_qr_image(
    request,
    code
):

    qr_record = get_object_or_404(
        LiveProductQR.objects.select_related(
            'product'
        ),
        code=code,
        is_active=True,
    )


    image_bytes = (
        build_product_qr_image_bytes(
            request,
            qr_record,
        )
    )


    response = HttpResponse(
        image_bytes,
        content_type='image/png',
    )


    response[
        'Content-Disposition'
    ] = (
        f'inline; '
        f'filename="pronty-live-producto-'
        f'{qr_record.product.pk}.png"'
    )


    return response


# ============================================================
# ETIQUETA QR
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def product_qr_label(
    request,
    code
):

    qr_record = get_object_or_404(
        LiveProductQR.objects.select_related(
            'product'
        ),
        code=code,
        is_active=True,
    )


    product = qr_record.product


    context = {
        'qr': qr_record,
        'product': product,
    }


    return render(
        request,
        'live_sales/product_qr_label.html',
        context
    )


# ============================================================
# ESCANEO DE QR
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def scan_product_qr(
    request,
    code
):

    qr = get_object_or_404(
        LiveProductQR.objects.select_related(
            'product'
        ),
        code=code,
        is_active=True,
    )


    product = qr.product


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


    selected_session_product = None


    requested_live_pk = (
        request.GET.get('live')
        or request.POST.get('live_session')
    )


    if requested_live_pk:

        for session_product in session_products:

            if (
                str(
                    session_product.live_session.pk
                )
                == str(requested_live_pk)
            ):

                selected_session_product = (
                    session_product
                )

                break


    if (
        selected_session_product is None
        and len(session_products) == 1
    ):

        selected_session_product = (
            session_products[0]
        )


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