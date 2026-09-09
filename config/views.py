from django.shortcuts import render


def custom_404(request, exception=None):
    """
    Página 404 personalizada de Pronty Outlet.

    En producción Django utilizará esta vista cuando
    DEBUG=False y una URL no exista o un recurso
    protegido devuelva Http404.
    """

    return render(
        request,
        '404.html',
        status=404
    )