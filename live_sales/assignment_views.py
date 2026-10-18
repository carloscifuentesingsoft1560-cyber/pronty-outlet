from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from .models import LiveAssignment
from .services import release_live_assignment


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
# LISTADO DE ASIGNACIONES
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def live_assignments(request):

    search = (
        request.GET
        .get(
            'q',
            ''
        )
        .strip()
    )


    status_filter = (
        request.GET
        .get(
            'status',
            ''
        )
        .strip()
        .upper()
    )


    assignments = (
        LiveAssignment.objects
        .select_related(
            'live_session',
            'customer',
            'customer__user',
            'product',
            'order',
            'created_by',
        )
        .all()
    )


    # ========================================================
    # BÚSQUEDA
    # ========================================================

    if search:

        assignments = (
            assignments
            .filter(
                Q(
                    customer__customer_code__icontains=search
                )
                |
                Q(
                    customer__user__first_name__icontains=search
                )
                |
                Q(
                    customer__user__last_name__icontains=search
                )
                |
                Q(
                    customer__user__email__icontains=search
                )
                |
                Q(
                    product__name__icontains=search
                )
                |
                Q(
                    product__sku__icontains=search
                )
                |
                Q(
                    live_session__name__icontains=search
                )
                |
                Q(
                    order__order_number__icontains=search
                )
            )
        )


    # ========================================================
    # FILTRO POR ESTADO
    # ========================================================

    valid_statuses = {
        LiveAssignment.Status.ASSIGNED,
        LiveAssignment.Status.ORDERED,
        LiveAssignment.Status.RELEASED,
    }


    if status_filter in valid_statuses:

        assignments = (
            assignments
            .filter(
                status=status_filter
            )
        )

    else:

        status_filter = ''


    assignments = (
        assignments
        .order_by(
            '-assigned_at',
            '-pk',
        )
    )


    # ========================================================
    # MÉTRICAS
    # ========================================================

    assigned_count = (
        LiveAssignment.objects
        .filter(
            status=LiveAssignment.Status.ASSIGNED
        )
        .count()
    )


    ordered_count = (
        LiveAssignment.objects
        .filter(
            status=LiveAssignment.Status.ORDERED
        )
        .count()
    )


    released_count = (
        LiveAssignment.objects
        .filter(
            status=LiveAssignment.Status.RELEASED
        )
        .count()
    )


    total_count = (
        LiveAssignment.objects
        .count()
    )


    context = {
        'assignments': assignments,
        'search': search,
        'status_filter': status_filter,
        'assigned_count': assigned_count,
        'ordered_count': ordered_count,
        'released_count': released_count,
        'total_count': total_count,
    }


    return render(
        request,
        'live_sales/assignments.html',
        context
    )


# ============================================================
# LIBERAR ASIGNACIÓN
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
@require_POST
def live_assignment_release(
    request,
    assignment_id
):

    assignment = get_object_or_404(
        LiveAssignment.objects.select_related(
            'customer',
            'customer__user',
            'product',
            'live_session',
            'order',
        ),
        pk=assignment_id,
    )


    if (
        assignment.status
        != LiveAssignment.Status.ASSIGNED
    ):

        messages.warning(
            request,
            (
                'Solo se pueden liberar asignaciones '
                'que todavía estén en estado Asignado.'
            )
        )


        return redirect(
            'live_sales:assignments'
        )


    success, message = (
        release_live_assignment(
            assignment,
            released_by=request.user,
        )
    )


    if success:

        messages.success(
            request,
            (
                f'Asignación #{assignment.pk} '
                f'liberada correctamente. '
                f'{message}'
            )
        )

    else:

        messages.error(
            request,
            message
        )


    return redirect(
        'live_sales:assignments'
    )