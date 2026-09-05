from django.urls import path

from . import views


app_name = 'cart'


urlpatterns = [
    path(
        '',
        views.cart_detail,
        name='cart_detail'
    ),

    path(
        'checkout/',
        views.checkout,
        name='checkout'
    ),

    path(
        'pedido-confirmado/',
        views.order_confirmation,
        name='order_confirmation'
    ),

    path(
        'pedido/<str:order_number>/pago/',
        views.order_payment,
        name='order_payment'
    ),

    path(
        'agregar/<int:product_id>/',
        views.cart_add,
        name='cart_add'
    ),

    path(
        'actualizar/<int:product_id>/',
        views.cart_update,
        name='cart_update'
    ),

    path(
        'eliminar/<int:product_id>/',
        views.cart_remove,
        name='cart_remove'
    ),

    path(
        'vaciar/',
        views.cart_clear,
        name='cart_clear'
    ),
]