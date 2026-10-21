from django.shortcuts import render


# ============================================================
# AYUDA
# ============================================================

def how_to_buy(request):

    context = {
        'page_title': 'Cómo comprar',
        'page_eyebrow': 'Ayuda',
        'page_icon': 'shopping-cart',
    }

    return render(
        request,
        'content/how_to_buy.html',
        context
    )


def contact(request):

    context = {
        'page_title': 'Contáctanos',
        'page_eyebrow': 'Ayuda',
        'page_icon': 'messages-square',
    }

    return render(
        request,
        'content/contact.html',
        context
    )


def shipping(request):

    context = {
        'page_title': 'Envíos',
        'page_eyebrow': 'Ayuda',
        'page_icon': 'truck',
    }

    return render(
        request,
        'content/shipping.html',
        context
    )


def returns(request):

    context = {
        'page_title': 'Cambios y devoluciones',
        'page_eyebrow': 'Ayuda',
        'page_icon': 'refresh-cw',
    }

    return render(
        request,
        'content/returns.html',
        context
    )


def faq(request):

    context = {
        'page_title': 'Preguntas frecuentes',
        'page_eyebrow': 'Ayuda',
        'page_icon': 'circle-help',
    }

    return render(
        request,
        'content/faq.html',
        context
    )


# ============================================================
# INFORMACIÓN LEGAL
# ============================================================

def terms(request):

    context = {
        'page_title': 'Términos y condiciones',
        'page_eyebrow': 'Información legal',
        'page_icon': 'file-text',
    }

    return render(
        request,
        'content/terms.html',
        context
    )


def privacy(request):

    context = {
        'page_title': 'Política de privacidad',
        'page_eyebrow': 'Información legal',
        'page_icon': 'shield-check',
    }

    return render(
        request,
        'content/privacy.html',
        context
    )


def data_processing(request):

    context = {
        'page_title': 'Tratamiento de datos',
        'page_eyebrow': 'Información legal',
        'page_icon': 'database',
    }

    return render(
        request,
        'content/data_processing.html',
        context
    )


def cookies_policy(request):

    context = {
        'page_title': 'Política de cookies',
        'page_eyebrow': 'Información legal',
        'page_icon': 'cookie',
    }

    return render(
        request,
        'content/cookies.html',
        context
    )