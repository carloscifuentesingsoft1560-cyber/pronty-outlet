from .cart import Cart


def cart(request):
    return {
        'cart_global': Cart(request)
    }
