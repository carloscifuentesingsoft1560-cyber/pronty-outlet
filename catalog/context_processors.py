from .models import Category


def navigation_categories(request):
    """
    Hace disponibles en todas las plantillas
    las categorías activas que deben aparecer
    en el menú principal.
    """

    categories = (
        Category.objects
        .filter(
            is_active=True,
            show_in_menu=True,
        )
        .order_by(
            'menu_order',
            'name',
        )
    )

    return {
        'navigation_categories': categories,
    }