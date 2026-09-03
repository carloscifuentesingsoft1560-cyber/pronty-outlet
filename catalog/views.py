from decimal import Decimal, InvalidOperation

from django.shortcuts import get_object_or_404, render

from .models import Brand, Category, Product, ProductImage


def home(request):
    return render(
        request,
        'home.html'
    )


def product_list(request):

    products = Product.objects.filter(
        is_active=True
    ).select_related(
        'category',
        'brand'
    ).prefetch_related(
        'images'
    )

    categories = Category.objects.filter(
        is_active=True
    ).order_by(
        'name'
    )

    brands = Brand.objects.filter(
        is_active=True
    ).order_by(
        'name'
    )

    # =========================
    # FILTROS
    # =========================

    selected_categories = request.GET.getlist(
        'category'
    )

    selected_brand = request.GET.get(
        'brand',
        ''
    ).strip()

    price_min_raw = request.GET.get(
        'price_min',
        ''
    ).strip()

    price_max_raw = request.GET.get(
        'price_max',
        ''
    ).strip()

    on_sale = request.GET.get(
        'on_sale',
        ''
    )

    ordering = request.GET.get(
        'ordering',
        'recent'
    )


    # =========================
    # CATEGORÍA
    # =========================

    if selected_categories:

        products = products.filter(
            category__slug__in=selected_categories
        )


    # =========================
    # MARCA
    # =========================

    if selected_brand:

        products = products.filter(
            brand__slug=selected_brand
        )


    # =========================
    # PRECIO MÍNIMO
    # =========================

    if price_min_raw:

        try:

            price_min = Decimal(
                price_min_raw
            )

            if price_min >= 0:

                products = products.filter(
                    retail_price__gte=price_min
                )

        except InvalidOperation:
            pass


    # =========================
    # PRECIO MÁXIMO
    # =========================

    if price_max_raw:

        try:

            price_max = Decimal(
                price_max_raw
            )

            if price_max >= 0:

                products = products.filter(
                    retail_price__lte=price_max
                )

        except InvalidOperation:
            pass


    # =========================
    # PROMOCIONES
    # =========================

    if on_sale:

        products = products.filter(
            is_on_sale=True
        )


    # =========================
    # ORDEN
    # =========================

    if ordering == 'price_asc':

        products = products.order_by(
            'retail_price',
            'name'
        )

    elif ordering == 'price_desc':

        products = products.order_by(
            '-retail_price',
            'name'
        )

    else:

        ordering = 'recent'

        products = products.order_by(
            '-created_at'
        )


    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'selected_categories': selected_categories,
        'selected_brand': selected_brand,
        'price_min': price_min_raw,
        'price_max': price_max_raw,
        'on_sale': on_sale,
        'ordering': ordering,
    }

    return render(
        request,
        'catalog/product_list.html',
        context
    )


def product_detail(request, slug):

    product = get_object_or_404(
        Product.objects.select_related(
            'category',
            'brand'
        ),
        slug=slug,
        is_active=True
    )

    gallery_images = list(
        ProductImage.objects.filter(
            product=product,
            is_active=True
        ).order_by(
            'order',
            'id'
        )
    )

    main_image = None

    if product.image:

        main_image = product.image

    elif gallery_images:

        main_image = gallery_images[0].image


    context = {
        'product': product,
        'gallery_images': gallery_images,
        'main_image': main_image,
    }

    return render(
        request,
        'catalog/product_detail.html',
        context
    )