from decimal import Decimal

from django.contrib.auth.decorators import user_passes_test
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    Sum,
)
from django.shortcuts import (
    get_object_or_404,
    render,
)

from .models import (
    LiveAssignment,
    LiveSession,
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
# ETIQUETAS DE CHOICES
# ============================================================

PLATFORM_LABELS = dict(
    LiveSession.Platform.choices
)

STATUS_LABELS = dict(
    LiveSession.Status.choices
)


def _platform_label(session):

    return PLATFORM_LABELS.get(
        session.platform,
        session.platform,
    )


def _status_label(session):

    return STATUS_LABELS.get(
        session.status,
        session.status,
    )


# ============================================================
# EXPRESIONES FINANCIERAS
# ============================================================

MONEY_FIELD = DecimalField(
    max_digits=18,
    decimal_places=2,
)


SALE_EXPRESSION = ExpressionWrapper(
    F('unit_price') * F('quantity'),
    output_field=MONEY_FIELD,
)


COST_EXPRESSION = ExpressionWrapper(
    F('unit_cost') * F('quantity'),
    output_field=MONEY_FIELD,
)


# ============================================================
# UTILIDADES
# ============================================================

def _decimal_value(value):

    if value is None:

        return Decimal('0.00')


    return Decimal(value)


def _money(value):

    value = _decimal_value(
        value
    )


    formatted = (
        f'{value:,.0f}'
        .replace(
            ',',
            '.'
        )
    )


    return (
        f'${formatted}'
    )


def _percentage(value):

    value = _decimal_value(
        value
    )


    formatted = (
        f'{value:.2f}'
        .replace(
            '.',
            ','
        )
    )


    return (
        f'{formatted} %'
    )


# ============================================================
# ÍNDICE DE REPORTES
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def live_reports(request):

    sessions = list(
        LiveSession.objects
        .all()
        .order_by(
            '-scheduled_at',
            '-created_at',
        )
    )


    rows = []


    for session in sessions:

        assignments = (
            LiveAssignment.objects
            .filter(
                live_session=session
            )
        )


        ordered_assignments = (
            assignments
            .filter(
                status=(
                    LiveAssignment.Status.ORDERED
                )
            )
        )


        totals = (
            ordered_assignments
            .aggregate(
                sales=Sum(
                    SALE_EXPRESSION
                ),

                units=Sum(
                    'quantity'
                ),
            )
        )


        rows.append({
            'session': session,

            'platform': (
                _platform_label(
                    session
                )
            ),

            'status': (
                _status_label(
                    session
                )
            ),

            'sales': (
                _money(
                    totals.get(
                        'sales'
                    )
                )
            ),

            'units': (
                totals.get(
                    'units'
                )
                or 0
            ),

            'assignments': (
                assignments.count()
            ),

            'orders': (
                ordered_assignments
                .exclude(
                    order__isnull=True
                )
                .values(
                    'order_id'
                )
                .distinct()
                .count()
            ),
        })


    context = {
        'rows': rows,
        'sessions': sessions,
    }


    return render(
        request,
        'live_sales/reports.html',
        context
    )


# ============================================================
# REPORTE DE UN LIVE
# ============================================================

@user_passes_test(
    _staff_required,
    login_url='/admin/login/'
)
def live_report_detail(
    request,
    session_id
):

    session = get_object_or_404(
        LiveSession,
        pk=session_id,
    )


    sessions = (
        LiveSession.objects
        .all()
        .order_by(
            '-scheduled_at',
            '-created_at',
        )
    )


    all_assignments = (
        LiveAssignment.objects
        .filter(
            live_session=session
        )
    )


    # ========================================================
    # VENTAS REALES
    # ========================================================

    ordered_assignments = (
        all_assignments
        .filter(
            status=(
                LiveAssignment.Status.ORDERED
            )
        )
    )


    financial_totals = (
        ordered_assignments
        .aggregate(
            sales=Sum(
                SALE_EXPRESSION
            ),

            cost=Sum(
                COST_EXPRESSION
            ),

            units=Sum(
                'quantity'
            ),
        )
    )


    total_sales = (
        _decimal_value(
            financial_totals.get(
                'sales'
            )
        )
    )


    total_cost = (
        _decimal_value(
            financial_totals.get(
                'cost'
            )
        )
    )


    total_units = (
        financial_totals.get(
            'units'
        )
        or 0
    )


    gross_profit = (
        total_sales
        - total_cost
    )


    if total_sales > 0:

        gross_margin = (
            gross_profit
            / total_sales
            * Decimal('100.00')
        )

    else:

        gross_margin = (
            Decimal('0.00')
        )


    # ========================================================
    # MÉTRICAS COMERCIALES
    # ========================================================

    ordered_assignment_count = (
        ordered_assignments
        .count()
    )


    order_count = (
        ordered_assignments
        .exclude(
            order__isnull=True
        )
        .values(
            'order_id'
        )
        .distinct()
        .count()
    )


    customer_count = (
        ordered_assignments
        .values(
            'customer_id'
        )
        .distinct()
        .count()
    )


    product_count = (
        ordered_assignments
        .values(
            'product_id'
        )
        .distinct()
        .count()
    )


    # ========================================================
    # MÉTRICAS OPERATIVAS
    # ========================================================

    pending_assignments = (
        all_assignments
        .filter(
            status=(
                LiveAssignment.Status.ASSIGNED
            )
        )
    )


    released_assignments = (
        all_assignments
        .filter(
            status=(
                LiveAssignment.Status.RELEASED
            )
        )
    )


    pending_count = (
        pending_assignments
        .count()
    )


    released_count = (
        released_assignments
        .count()
    )


    pending_units = (
        pending_assignments
        .aggregate(
            total=Sum(
                'quantity'
            )
        )
        .get(
            'total'
        )
        or 0
    )


    released_units = (
        released_assignments
        .aggregate(
            total=Sum(
                'quantity'
            )
        )
        .get(
            'total'
        )
        or 0
    )


    total_assignment_count = (
        all_assignments
        .count()
    )


    # ========================================================
    # PRODUCTOS
    # ========================================================

    product_rows = (
        ordered_assignments
        .values(
            'product_id',
            'product__sku',
            'product__name',
        )
        .annotate(
            units=Sum(
                'quantity'
            ),

            sales=Sum(
                SALE_EXPRESSION
            ),

            cost=Sum(
                COST_EXPRESSION
            ),
        )
        .order_by(
            '-sales',
            'product__name',
        )
    )


    products = []


    for row in product_rows:

        sales = (
            _decimal_value(
                row.get(
                    'sales'
                )
            )
        )


        cost = (
            _decimal_value(
                row.get(
                    'cost'
                )
            )
        )


        profit = (
            sales
            - cost
        )


        if sales > 0:

            margin = (
                profit
                / sales
                * Decimal('100.00')
            )

        else:

            margin = (
                Decimal('0.00')
            )


        products.append({
            'product_id': (
                row[
                    'product_id'
                ]
            ),

            'sku': (
                row[
                    'product__sku'
                ]
            ),

            'name': (
                row[
                    'product__name'
                ]
            ),

            'units': (
                row[
                    'units'
                ]
                or 0
            ),

            'sales': (
                _money(
                    sales
                )
            ),

            'cost': (
                _money(
                    cost
                )
            ),

            'profit': (
                _money(
                    profit
                )
            ),

            'margin': (
                _percentage(
                    margin
                )
            ),
        })


    # ========================================================
    # CLIENTES
    # ========================================================

    customer_rows = (
        ordered_assignments
        .values(
            'customer_id',

            'customer__customer_code',

            'customer__user__first_name',

            'customer__user__last_name',

            'customer__user__username',
        )
        .annotate(
            units=Sum(
                'quantity'
            ),

            sales=Sum(
                SALE_EXPRESSION
            ),
        )
        .order_by(
            '-sales',
            'customer__customer_code',
        )
    )


    customers = []


    for row in customer_rows:

        first_name = (
            row[
                'customer__user__first_name'
            ]
            or ''
        )


        last_name = (
            row[
                'customer__user__last_name'
            ]
            or ''
        )


        full_name = (
            f'{first_name} {last_name}'
            .strip()
        )


        if not full_name:

            full_name = (
                row[
                    'customer__user__username'
                ]
            )


        customers.append({
            'customer_id': (
                row[
                    'customer_id'
                ]
            ),

            'customer_code': (
                row[
                    'customer__customer_code'
                ]
            ),

            'name': (
                full_name
            ),

            'units': (
                row[
                    'units'
                ]
                or 0
            ),

            'sales': (
                _money(
                    row.get(
                        'sales'
                    )
                )
            ),
        })


    # ========================================================
    # CONTEXTO
    # ========================================================

    context = {
        'session': session,

        'sessions': sessions,

        'platform': (
            _platform_label(
                session
            )
        ),

        'status': (
            _status_label(
                session
            )
        ),

        'financial': {
            'sales': (
                _money(
                    total_sales
                )
            ),

            'cost': (
                _money(
                    total_cost
                )
            ),

            'profit': (
                _money(
                    gross_profit
                )
            ),

            'margin': (
                _percentage(
                    gross_margin
                )
            ),
        },

        'commercial': {
            'units_sold': (
                total_units
            ),

            'assignments_converted': (
                ordered_assignment_count
            ),

            'orders': (
                order_count
            ),

            'customers': (
                customer_count
            ),

            'products': (
                product_count
            ),
        },

        'operations': {
            'total_assignments': (
                total_assignment_count
            ),

            'pending_assignments': (
                pending_count
            ),

            'pending_units': (
                pending_units
            ),

            'released_assignments': (
                released_count
            ),

            'released_units': (
                released_units
            ),
        },

        'products': products,

        'customers': customers,
    }


    return render(
        request,
        'live_sales/report_detail.html',
        context
    )