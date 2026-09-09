from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config.views import custom_404


handler404 = 'config.views.custom_404'


urlpatterns = [
    path(
        'admin/',
        admin.site.urls
    ),

    path(
        'cuenta/',
        include('accounts.urls')
    ),

    path(
        'carrito/',
        include('cart.urls')
    ),

    path(
        '',
        include('catalog.urls')
    ),
]


if settings.DEBUG:

    urlpatterns += [
        path(
            '__prueba-404__/',
            custom_404,
            name='preview_404'
        ),
    ]

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )