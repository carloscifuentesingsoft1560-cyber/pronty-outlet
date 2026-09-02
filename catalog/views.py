from django.shortcuts import render, get_object_or_404
from .models import Product, Category, Brand


def home(request):
    return render(request, 'home.html')


def product_list(request):

    products = Product.objects.filter(
        is_active=True
    ).select_related(
        'category',
        'brand'
    )

    categories = Category.objects.filter(
        is_active=True
    )

    brands = Brand.objects.filter(
        is_active=True
    )

    selected_categories = request.GET.getlist('category')
    selected_brand = request.GET.get('brand')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    on_sale = request.GET.get('on_sale')
    ordering = request.GET.get('ordering')


    if selected_categories:
        products = products.filter(
            category__slug__in=selected_categories
        )


    if selected_brand:
        products = products.filter(
            brand__slug=selected_brand
        )


    if price_min:
        products = products.filter(
            retail_price__gte=price_min
        )


    if price_max:
        products = products.filter(
            retail_price__lte=price_max
        )


    if on_sale:
        products = products.filter(
            is_on_sale=True
        )


    if ordering == 'price_asc':

        products = products.order_by(
            'retail_price'
        )

    elif ordering == 'price_desc':

        products = products.order_by(
            '-retail_price'
        )

    else:

        products = products.order_by(
            '-created_at'
        )


    context = {
        'products': products,
        'categories': categories,
        'brands': brands,

        'selected_categories': selected_categories,
        'selected_brand': selected_brand,
        'price_min': price_min,
        'price_max': price_max,
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

    return render(
        request,
        'catalog/product_detail.html',
        {
            'product': product
        }
    )