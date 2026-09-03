from django.urls import path

from . import views


urlpatterns = [
    path(
        '',
        views.home,
        name='home'
    ),

    path(
        'productos/',
        views.product_list,
        name='product_list'
    ),

    path(
        'productos/<slug:slug>/',
        views.product_detail,
        name='product_detail'
    ),
]