from django.urls import path

from . import views


app_name = 'content'


urlpatterns = [

    path(
        'como-comprar/',
        views.how_to_buy,
        name='how_to_buy'
    ),

    path(
        'contacto/',
        views.contact,
        name='contact'
    ),

    path(
        'envios/',
        views.shipping,
        name='shipping'
    ),

    path(
        'cambios-y-devoluciones/',
        views.returns,
        name='returns'
    ),

    path(
        'preguntas-frecuentes/',
        views.faq,
        name='faq'
    ),

    path(
        'terminos-y-condiciones/',
        views.terms,
        name='terms'
    ),

    path(
        'politica-de-privacidad/',
        views.privacy,
        name='privacy'
    ),

    path(
        'tratamiento-de-datos/',
        views.data_processing,
        name='data_processing'
    ),

    path(
        'politica-de-cookies/',
        views.cookies_policy,
        name='cookies'
    ),

]