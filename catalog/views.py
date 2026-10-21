from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from live_sales.models import LiveSession

from .models import (
    Brand,
    Category,
    Product,
    ProductImage,
)


# ============================================================
# PLATAFORMAS DE LIVE
# ============================================================

def get_live_platform_label(
    platform: str
) -> str:

    if (
        platform
        == LiveSession.Platform.TIKTOK
    ):

        return 'TikTok'


    if (
        platform
        == LiveSession.Platform.INSTAGRAM
    ):

        return 'Instagram'


    if (
        platform
        == LiveSession.Platform.FACEBOOK
    ):

        return 'Facebook'


    if (
        platform
        == LiveSession.Platform.MIXED
    ):

        return 'Multiplataforma'


    return 'Live'


# ============================================================
# INICIO
# ============================================================

def home(request):

    # =========================================================
    # LIVE ACTUAL
    # =========================================================

    current_live = (
        LiveSession.objects
        .filter(
            status=LiveSession.Status.LIVE
        )
        .order_by(
            '-started_at',
            '-scheduled_at',
            '-created_at',
        )
        .first()
    )


    # =========================================================
    # PRÓXIMO LIVE PROGRAMADO
    # =========================================================

    upcoming_live = None


    if current_live is None:

        upcoming_live = (
            LiveSession.objects
            .filter(
                status=(
                    LiveSession
                    .Status
                    .SCHEDULED
                ),
                scheduled_at__isnull=False,
                scheduled_at__gte=timezone.now(),
            )
            .order_by(
                'scheduled_at',
                'created_at',
            )
            .first()
        )


    # =========================================================
    # LIVE QUE MOSTRARÁ EL HOME
    # =========================================================

    home_live = (
        current_live
        or upcoming_live
    )


    home_live_platform_label = None


    if home_live:

        home_live_platform_label = (
            get_live_platform_label(
                home_live.platform
            )
        )


    # =========================================================
    # CONTEXTO
    # =========================================================

    context = {
        'home_live': (
            home_live
        ),

        'home_live_is_active': (
            current_live is not None
        ),

        'home_live_platform_label': (
            home_live_platform_label
        ),
    }


    return render(
        request,
        'home.html',
        context
    )


# ============================================================
# LISTADO DE PRODUCTOS
# ============================================================

def product_list(request):

    # =========================================================
    # PRODUCTOS DISPONIBLES EN EL CATÁLOGO PÚBLICO
    # =========================================================

    products = (
        Product.objects
        .filter(
            is_active=True,
            category__is_active=True,
        )
        .select_related(
            'category',
            'brand'
        )
        .prefetch_related(
            'images'
        )
    )


    # =========================================================
    # CATEGORÍAS ACTIVAS
    # =========================================================

    categories = (
        Category.objects
        .filter(
            is_active=True
        )
        .order_by(
            'menu_order',
            'name',
        )
    )


    # =========================================================
    # MARCAS ACTIVAS
    # =========================================================

    brands = (
        Brand.objects
        .filter(
            is_active=True
        )
        .order_by(
            'name'
        )
    )


    # =========================================================
    # BÚSQUEDA
    # =========================================================

    search_query = (
        request.GET
        .get(
            'q',
            ''
        )
        .strip()
    )


    if search_query:

        products = products.filter(
            Q(
                name__icontains=search_query
            )
            |
            Q(
                sku__icontains=search_query
            )
            |
            Q(
                short_description__icontains=(
                    search_query
                )
            )
            |
            Q(
                description__icontains=(
                    search_query
                )
            )
            |
            Q(
                category__name__icontains=(
                    search_query
                )
            )
            |
            Q(
                brand__name__icontains=(
                    search_query
                )
            )
        )


    # =========================================================
    # FILTROS
    # =========================================================

    selected_categories = (
        request.GET
        .getlist(
            'category'
        )
    )


    selected_brand = (
        request.GET
        .get(
            'brand',
            ''
        )
        .strip()
    )


    price_min_raw = (
        request.GET
        .get(
            'price_min',
            ''
        )
        .strip()
    )


    price_max_raw = (
        request.GET
        .get(
            'price_max',
            ''
        )
        .strip()
    )


    on_sale = (
        request.GET
        .get(
            'on_sale',
            ''
        )
    )


    ordering = (
        request.GET
        .get(
            'ordering',
            'recent'
        )
    )


    # =========================================================
    # CATEGORÍA
    # =========================================================

    if selected_categories:

        products = (
            products.filter(
                category__slug__in=(
                    selected_categories
                ),
                category__is_active=True,
            )
        )


    # =========================================================
    # MARCA
    # =========================================================

    if selected_brand:

        products = (
            products.filter(
                brand__slug=(
                    selected_brand
                ),
                brand__is_active=True,
            )
        )


    # =========================================================
    # PRECIO MÍNIMO
    # =========================================================

    if price_min_raw:

        try:

            price_min = Decimal(
                price_min_raw
            )


            if price_min >= 0:

                products = (
                    products.filter(
                        retail_price__gte=(
                            price_min
                        )
                    )
                )

        except InvalidOperation:

            pass


    # =========================================================
    # PRECIO MÁXIMO
    # =========================================================

    if price_max_raw:

        try:

            price_max = Decimal(
                price_max_raw
            )


            if price_max >= 0:

                products = (
                    products.filter(
                        retail_price__lte=(
                            price_max
                        )
                    )
                )

        except InvalidOperation:

            pass


    # =========================================================
    # PROMOCIONES
    # =========================================================

    if on_sale:

        products = (
            products.filter(
                is_on_sale=True
            )
        )


    # =========================================================
    # ORDEN
    # =========================================================

    if ordering == 'price_asc':

        products = (
            products.order_by(
                'retail_price',
                'name'
            )
        )

    elif ordering == 'price_desc':

        products = (
            products.order_by(
                '-retail_price',
                'name'
            )
        )

    elif ordering == 'name_asc':

        products = (
            products.order_by(
                'name'
            )
        )

    elif ordering == 'name_desc':

        products = (
            products.order_by(
                '-name'
            )
        )

    else:

        ordering = 'recent'

        products = (
            products.order_by(
                '-created_at'
            )
        )


    # =========================================================
    # CONTEXTO
    # =========================================================

    context = {
        'products': (
            products
        ),

        'categories': (
            categories
        ),

        'brands': (
            brands
        ),

        'search_query': (
            search_query
        ),

        'selected_categories': (
            selected_categories
        ),

        'selected_brand': (
            selected_brand
        ),

        'price_min': (
            price_min_raw
        ),

        'price_max': (
            price_max_raw
        ),

        'on_sale': (
            on_sale
        ),

        'ordering': (
            ordering
        ),
    }


    return render(
        request,
        'catalog/product_list.html',
        context
    )


# ============================================================
# DETALLE DE PRODUCTO
# ============================================================

def product_detail(
    request,
    slug
):

    product = get_object_or_404(
        (
            Product.objects
            .select_related(
                'category',
                'brand'
            )
        ),
        slug=slug,
        is_active=True,
        category__is_active=True,
    )


    gallery_images = list(
        (
            ProductImage.objects
            .filter(
                product=product,
                is_active=True
            )
            .order_by(
                'order',
                'id'
            )
        )
    )


    main_image = None


    if product.image:

        main_image = (
            product.image
        )

    elif gallery_images:

        main_image = (
            gallery_images[
                0
            ].image
        )


    context = {
        'product': (
            product
        ),

        'gallery_images': (
            gallery_images
        ),

        'main_image': (
            main_image
        ),
    }


    return render(
        request,
        'catalog/product_detail.html',
        context
    )