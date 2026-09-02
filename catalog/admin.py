from django.contrib import admin
from .models import Category, Brand, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'is_active',
        'created_at',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'name',
        'slug',
    )

    prepopulated_fields = {
        'slug': ('name',)
    }


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'is_active',
        'created_at',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'name',
        'slug',
    )

    prepopulated_fields = {
        'slug': ('name',)
    }


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'sku',
        'category',
        'brand',
        'retail_price',
        'wholesale_price',
        'stock',
        'is_active',
    )

    list_filter = (
        'category',
        'brand',
        'is_new',
        'is_on_sale',
        'is_active',
    )

    search_fields = (
        'name',
        'sku',
        'category__name',
        'brand__name',
    )

    prepopulated_fields = {
        'slug': ('name',)
    }

    readonly_fields = (
        'created_at',
        'updated_at',
    )