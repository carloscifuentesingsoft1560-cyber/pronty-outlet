from django.urls import path

from accounts import views


app_name = 'accounts'


urlpatterns = [
    path(
        '',
        views.account_dashboard,
        name='dashboard'
    ),

    path(
        'pedido/<str:order_number>/',
        views.order_detail,
        name='order_detail'
    ),

    path(
        'ingresar/',
        views.account_login,
        name='login'
    ),

    path(
        'registro/',
        views.account_register,
        name='register'
    ),

    path(
        'salir/',
        views.account_logout,
        name='logout'
    ),
]