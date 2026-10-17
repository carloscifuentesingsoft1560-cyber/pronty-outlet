from django.urls import path

from . import views


app_name = 'live_sales'


urlpatterns = [

    path(
        '',
        views.live_dashboard,
        name='dashboard'
    ),

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