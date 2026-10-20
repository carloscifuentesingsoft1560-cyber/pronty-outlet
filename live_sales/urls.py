from django.urls import path

from . import assignment_views
from . import customer_views
from . import session_product_views
from . import views


app_name = 'live_sales'


urlpatterns = [

    # ========================================================
    # DASHBOARD
    # ========================================================

    path(
        '',
        views.live_dashboard,
        name='dashboard'
    ),

    # ========================================================
    # LIVES
    # ========================================================

    path(
        'lives/',
        views.live_sessions,
        name='sessions'
    ),

    path(
        'lives/nuevo/',
        views.live_session_create,
        name='session_create'
    ),

    path(
        'lives/<int:session_id>/editar/',
        views.live_session_edit,
        name='session_edit'
    ),

    path(
        'lives/<int:session_id>/iniciar/',
        views.live_session_start,
        name='session_start'
    ),

    path(
        'lives/<int:session_id>/finalizar/',
        views.live_session_close,
        name='session_close'
    ),

    path(
        'lives/<int:session_id>/cancelar/',
        views.live_session_cancel,
        name='session_cancel'
    ),

    # ========================================================
    # PRODUCTOS DE CADA LIVE
    # ========================================================

    path(
        'lives/<int:session_id>/productos/',
        session_product_views.live_session_products,
        name='session_products'
    ),

    path(
        'lives/<int:session_id>/productos/agregar/',
        session_product_views.live_session_product_add,
        name='session_product_add'
    ),

    path(
        'lives/productos/<int:session_product_id>/actualizar/',
        session_product_views.live_session_product_update,
        name='session_product_update'
    ),

    path(
        'lives/productos/<int:session_product_id>/quitar/',
        session_product_views.live_session_product_remove,
        name='session_product_remove'
    ),

    # ========================================================
    # CLIENTES LIVE
    # ========================================================

    path(
        'clientes/',
        customer_views.live_customers,
        name='customers'
    ),

    path(
        'clientes/codigos/buscar/',
        customer_views.live_customer_code_search,
        name='customer_code_search'
    ),

    path(
        'clientes/<int:user_id>/crear-acceso/',
        customer_views.live_customer_create_access,
        name='customer_create_access'
    ),

    path(
        'clientes/acceso/<int:access_id>/activar/',
        customer_views.live_customer_activate,
        name='customer_activate'
    ),

    path(
        'clientes/acceso/<int:access_id>/desactivar/',
        customer_views.live_customer_deactivate,
        name='customer_deactivate'
    ),

    # ========================================================
    # ASIGNACIONES
    # ========================================================

    path(
        'asignaciones/',
        assignment_views.live_assignments,
        name='assignments'
    ),

    path(
        'asignaciones/<int:assignment_id>/liberar/',
        assignment_views.live_assignment_release,
        name='assignment_release'
    ),

    # ========================================================
    # PRODUCTOS Y QR
    # ========================================================

    path(
        'productos/',
        views.live_products,
        name='products'
    ),

    # ========================================================
    # QR
    # ========================================================

    path(
        'qr/<uuid:code>/imagen/',
        views.product_qr_image,
        name='product_qr_image'
    ),

    path(
        'qr/<uuid:code>/etiqueta/',
        views.product_qr_label,
        name='product_qr_label'
    ),

    path(
        'qr/<uuid:code>/',
        views.scan_product_qr,
        name='scan_product'
    ),

]