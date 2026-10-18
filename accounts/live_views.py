from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from live_sales.models import (
    LiveAssignment,
    LiveCustomerAccess,
)


# ============================================================
# PRONTY LIVE DEL CLIENTE
# ============================================================

@login_required(
    login_url='accounts:login'
)
def customer_live_dashboard(request):

    # ========================================================
    # ADMINISTRADORES NO USAN EL PORTAL DE CLIENTE
    # ========================================================

    if (
        request.user.is_staff
        or request.user.is_superuser
    ):

        return redirect(
            'live_sales:dashboard'
        )


    # ========================================================
    # ACCESO PERMANENTE A PRONTY LIVE
    # ========================================================

    live_access = (
        LiveCustomerAccess.objects
        .filter(
            user=request.user
        )
        .first()
    )


    # ========================================================
    # ASIGNACIONES ACTIVAS
    # ========================================================

    live_assignments = []


    if (
        live_access
        and live_access.is_activated
    ):

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
    # TOTALES
    # ========================================================

    total_assigned = sum(
        assignment.subtotal
        for assignment in live_assignments
    )


    # ========================================================
    # RENDER
    # ========================================================

    context = {
        'live_access': live_access,
        'live_assignments': live_assignments,
        'total_assigned': total_assigned,
    }


    return render(
        request,
        'accounts/live.html',
        context
    )