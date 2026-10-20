from pathlib import Path
from uuid import uuid4

from django.contrib import admin, messages
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import (
    HttpResponse,
    HttpResponseNotAllowed,
)
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path

from .image_import import (
    ProductImageImportError,
    ProductImageZipForm,
    import_validated_product_images,
    validate_product_images_zip,
)

from .models import (
    Brand,
    Category,
    InventoryMovement,
    Product,
    ProductImage,
)

from .product_import import (
    ProductImportError,
    ProductImportUploadForm,
    build_product_import_template,
    import_validated_products,
    validate_product_file,
)


# ============================================================
# INLINE: IMÁGENES
# ============================================================

class ProductImageInline(admin.TabularInline):

    model = ProductImage
    extra = 1

    fields = (
        'image',
        'alt_text',
        'order',
        'is_active',
    )


# ============================================================
# INLINE: INVENTARIO
# ============================================================

class InventoryMovementInline(admin.TabularInline):

    model = InventoryMovement
    extra = 0

    fields = (
        'movement_type',
        'quantity',
        'previous_stock',
        'new_stock',
        'reason',
        'reference',
        'created_by',
        'created_at',
    )

    readonly_fields = (
        'movement_type',
        'quantity',
        'previous_stock',
        'new_stock',
        'reason',
        'reference',
        'created_by',
        'created_at',
    )

    can_delete = False
    show_change_link = True


    def has_add_permission(
        self,
        request,
        obj=None,
    ):

        return False


# ============================================================
# CATEGORÍAS
# ============================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'slug',
        'is_active',
        'show_in_menu',
        'menu_order',
        'icon_name',
        'highlight_in_menu',
        'created_at',
    )

    list_editable = (
        'is_active',
        'show_in_menu',
        'menu_order',
        'highlight_in_menu',
    )

    list_filter = (
        'is_active',
        'show_in_menu',
        'highlight_in_menu',
    )

    search_fields = (
        'name',
        'slug',
    )

    prepopulated_fields = {
        'slug': (
            'name',
        )
    }

    fieldsets = (
        (
            'Categoría',
            {
                'fields': (
                    'name',
                    'slug',
                )
            }
        ),
        (
            'Visualización en la tienda',
            {
                'fields': (
                    'is_active',
                    'show_in_menu',
                    'menu_order',
                    'icon',
                    'highlight_in_menu',
                ),
                'description': (
                    'Configura cómo aparece esta categoría '
                    'en el menú principal de Pronty Outlet.'
                ),
            }
        ),
    )

    ordering = (
        'menu_order',
        'name',
    )


    @admin.display(
        description='Icono'
    )
    def icon_name(
        self,
        obj,
    ):

        icon_labels = {
            Category.Icon.SPARKLES: (
                '✨ Brillos / maquillaje'
            ),
            Category.Icon.HEART: (
                '❤️ Corazón'
            ),
            Category.Icon.DROPLETS: (
                '💧 Gotas / cuidado personal'
            ),
            Category.Icon.SHIRT: (
                '👕 Ropa / moda'
            ),
            Category.Icon.BADGE_PERCENT: (
                '🏷️ Promoción / descuento'
            ),
            Category.Icon.GEM: (
                '💎 Accesorios / joyería'
            ),
            Category.Icon.TAG: (
                '🔖 Etiqueta'
            ),
            Category.Icon.SHOPPING_BAG: (
                '🛍️ Bolsa de compras'
            ),
            Category.Icon.GIFT: (
                '🎁 Regalo'
            ),
            Category.Icon.STAR: (
                '⭐ Estrella'
            ),
            Category.Icon.PALETTE: (
                '🎨 Belleza / colores'
            ),
            Category.Icon.CROWN: (
                '👑 Premium'
            ),
            Category.Icon.BABY: (
                '👶 Infantil / bebé'
            ),
            Category.Icon.WATCH: (
                '⌚ Relojes'
            ),
            Category.Icon.GLASSES: (
                '👓 Gafas'
            ),
            Category.Icon.FOOTPRINTS: (
                '👣 Calzado'
            ),
            Category.Icon.FLOWER: (
                '🌸 Floral / femenino'
            ),
            Category.Icon.SMILE: (
                '😊 Kawaii / divertido'
            ),
            Category.Icon.PACKAGE: (
                '📦 Otros productos'
            ),
        }

        return icon_labels.get(
            obj.icon,
            obj.icon,
        )


# ============================================================
# MARCAS
# ============================================================

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
        'slug': (
            'name',
        )
    }


# ============================================================
# PRODUCTOS
# ============================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    change_list_template = (
        'admin/catalog/product/change_list.html'
    )

    list_display = (
        'name',
        'sku',
        'category',
        'brand',
        'retail_price',
        'wholesale_price',
        'stock',
        'is_new',
        'is_on_sale',
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
        'slug': (
            'name',
        )
    }

    readonly_fields = (
        'stock',
        'created_at',
        'updated_at',
    )

    inlines = [
        ProductImageInline,
        InventoryMovementInline,
    ]


    # ========================================================
    # URLS PERSONALIZADAS
    # ========================================================

    def get_urls(
        self
    ):

        default_urls = (
            super().get_urls()
        )


        custom_urls = [

            # =================================================
            # PRODUCTOS
            # =================================================

            path(
                'importar/',
                self.admin_site.admin_view(
                    self.import_products_view
                ),
                name=(
                    'catalog_product_import'
                ),
            ),

            path(
                'importar/confirmar/',
                self.admin_site.admin_view(
                    self.confirm_import_view
                ),
                name=(
                    'catalog_product_import_confirm'
                ),
            ),

            path(
                'importar/plantilla.xlsx',
                self.admin_site.admin_view(
                    self.download_template_view
                ),
                name=(
                    'catalog_product_import_template'
                ),
            ),

            # =================================================
            # IMÁGENES
            # =================================================

            path(
                'importar-imagenes/',
                self.admin_site.admin_view(
                    self.import_product_images_view
                ),
                name=(
                    'catalog_product_image_import'
                ),
            ),

            path(
                'importar-imagenes/confirmar/',
                self.admin_site.admin_view(
                    self.confirm_product_images_view
                ),
                name=(
                    'catalog_product_image_import_confirm'
                ),
            ),

        ]


        return (
            custom_urls
            + default_urls
        )


    # ========================================================
    # PRODUCTOS:
    # LIMPIAR ARCHIVO TEMPORAL
    # ========================================================

    def _clear_previous_temp_file(
        self,
        request,
    ):

        previous_path = (
            request.session.pop(
                'product_import_temp_path',
                None,
            )
        )


        request.session.pop(
            'product_import_original_name',
            None,
        )


        if (
            previous_path
            and default_storage.exists(
                previous_path
            )
        ):

            default_storage.delete(
                previous_path
            )


    # ========================================================
    # PRODUCTOS:
    # GUARDAR ARCHIVO TEMPORAL
    # ========================================================

    def _save_temp_file(
        self,
        request,
        uploaded_file,
    ):

        self._clear_previous_temp_file(
            request
        )


        extension = (
            Path(
                uploaded_file.name
            )
            .suffix
            .lower()
        )


        temp_name = (
            'imports/tmp/'
            f'{uuid4().hex}'
            f'{extension}'
        )


        uploaded_file.seek(
            0
        )


        content = ContentFile(
            uploaded_file.read()
        )


        saved_path = (
            default_storage.save(
                temp_name,
                content,
            )
        )


        request.session[
            'product_import_temp_path'
        ] = saved_path


        request.session[
            'product_import_original_name'
        ] = uploaded_file.name


        request.session.modified = True


        return saved_path


    # ========================================================
    # PRODUCTOS:
    # VALIDAR
    # ========================================================

    def import_products_view(
        self,
        request,
    ):

        result = None


        if request.method == 'POST':

            form = (
                ProductImportUploadForm(
                    request.POST,
                    request.FILES,
                )
            )


            if form.is_valid():

                uploaded_file = (
                    form.cleaned_data[
                        'file'
                    ]
                )


                try:

                    result = (
                        validate_product_file(
                            uploaded_file
                        )
                    )


                    if (
                        not result[
                            'file_errors'
                        ]
                        and result[
                            'valid_count'
                        ] > 0
                    ):

                        self._save_temp_file(
                            request,
                            uploaded_file,
                        )


                    else:

                        self._clear_previous_temp_file(
                            request
                        )


                except ProductImportError as exc:

                    self._clear_previous_temp_file(
                        request
                    )


                    form.add_error(
                        'file',
                        str(
                            exc
                        ),
                    )


        else:

            form = (
                ProductImportUploadForm()
            )


        context = {
            **self.admin_site.each_context(
                request
            ),
            'opts': (
                self.model._meta
            ),
            'title': (
                'Importar productos'
            ),
            'form': form,
            'result': result,
            'has_view_permission': True,
        }


        return TemplateResponse(
            request,
            (
                'admin/catalog/product/'
                'import_products.html'
            ),
            context,
        )


    # ========================================================
    # PRODUCTOS:
    # CONFIRMAR
    # ========================================================

    def confirm_import_view(
        self,
        request,
    ):

        if request.method != 'POST':

            return HttpResponseNotAllowed(
                [
                    'POST',
                ]
            )


        temp_path = (
            request.session.get(
                'product_import_temp_path'
            )
        )


        original_name = (
            request.session.get(
                'product_import_original_name',
                'archivo',
            )
        )


        if not temp_path:

            messages.error(
                request,
                (
                    'No hay una importación '
                    'validada pendiente.'
                )
            )


            return redirect(
                'admin:catalog_product_import'
            )


        if not default_storage.exists(
            temp_path
        ):

            self._clear_previous_temp_file(
                request
            )


            messages.error(
                request,
                (
                    'El archivo temporal ya no '
                    'está disponible. '
                    'Vuelve a validarlo.'
                )
            )


            return redirect(
                'admin:catalog_product_import'
            )


        try:

            with default_storage.open(
                temp_path,
                'rb',
            ) as stored_file:

                stored_file.name = (
                    original_name
                )


                result = (
                    import_validated_products(
                        stored_file,
                        request.user,
                    )
                )


        except Exception as exc:

            messages.error(
                request,
                (
                    'No fue posible completar '
                    'la importación. '
                    'No se guardaron cambios. '
                    f'Detalle: {exc}'
                )
            )


            return redirect(
                'admin:catalog_product_import'
            )


        self._clear_previous_temp_file(
            request
        )


        messages.success(
            request,
            (
                'Importación completada. '
                f'Productos creados: '
                f'{result["created_count"]}. '
                f'Productos actualizados: '
                f'{result["updated_count"]}. '
                f'Movimientos de inventario: '
                f'{result["movement_count"]}. '
                f'Filas omitidas por errores: '
                f'{result["skipped_error_count"]}. '
                f'Referencia: '
                f'{result["reference"]}.'
            )
        )


        return redirect(
            'admin:catalog_product_changelist'
        )


    # ========================================================
    # IMÁGENES:
    # LIMPIAR ZIP TEMPORAL
    # ========================================================

    def _clear_image_import_temp_file(
        self,
        request,
    ):

        previous_path = (
            request.session.pop(
                'product_image_import_temp_path',
                None,
            )
        )


        request.session.pop(
            'product_image_import_original_name',
            None,
        )


        if (
            previous_path
            and default_storage.exists(
                previous_path
            )
        ):

            default_storage.delete(
                previous_path
            )


    # ========================================================
    # IMÁGENES:
    # GUARDAR ZIP TEMPORAL
    # ========================================================

    def _save_image_import_temp_file(
        self,
        request,
        uploaded_file,
    ):

        self._clear_image_import_temp_file(
            request
        )


        temp_name = (
            'imports/images/tmp/'
            f'{uuid4().hex}.zip'
        )


        uploaded_file.seek(
            0
        )


        content = ContentFile(
            uploaded_file.read()
        )


        saved_path = (
            default_storage.save(
                temp_name,
                content,
            )
        )


        request.session[
            'product_image_import_temp_path'
        ] = saved_path


        request.session[
            'product_image_import_original_name'
        ] = uploaded_file.name


        request.session.modified = True


        return saved_path


    # ========================================================
    # IMÁGENES:
    # VALIDAR
    # ========================================================

    def import_product_images_view(
        self,
        request,
    ):

        result = None


        if request.method == 'POST':

            form = (
                ProductImageZipForm(
                    request.POST,
                    request.FILES,
                )
            )


            if form.is_valid():

                uploaded_zip = (
                    form.cleaned_data[
                        'images_zip'
                    ]
                )


                try:

                    result = (
                        validate_product_images_zip(
                            uploaded_zip
                        )
                    )


                    if (
                        result[
                            'valid_image_count'
                        ] > 0
                    ):

                        self._save_image_import_temp_file(
                            request,
                            uploaded_zip,
                        )


                    else:

                        self._clear_image_import_temp_file(
                            request
                        )


                except ProductImageImportError as exc:

                    self._clear_image_import_temp_file(
                        request
                    )


                    form.add_error(
                        'images_zip',
                        str(
                            exc
                        ),
                    )


        else:

            form = (
                ProductImageZipForm()
            )


        context = {
            **self.admin_site.each_context(
                request
            ),
            'opts': (
                self.model._meta
            ),
            'title': (
                'Importar imágenes de productos'
            ),
            'form': form,
            'result': result,
            'has_view_permission': True,
        }


        return TemplateResponse(
            request,
            (
                'admin/catalog/product/'
                'import_images.html'
            ),
            context,
        )


    # ========================================================
    # IMÁGENES:
    # CONFIRMAR IMPORTACIÓN
    # ========================================================

    def confirm_product_images_view(
        self,
        request,
    ):

        if request.method != 'POST':

            return HttpResponseNotAllowed(
                [
                    'POST',
                ]
            )


        temp_path = (
            request.session.get(
                'product_image_import_temp_path'
            )
        )


        original_name = (
            request.session.get(
                'product_image_import_original_name',
                'imagenes.zip',
            )
        )


        if not temp_path:

            messages.error(
                request,
                (
                    'No hay una importación '
                    'de imágenes validada pendiente.'
                )
            )


            return redirect(
                'admin:catalog_product_image_import'
            )


        if not default_storage.exists(
            temp_path
        ):

            self._clear_image_import_temp_file(
                request
            )


            messages.error(
                request,
                (
                    'El ZIP temporal ya no está '
                    'disponible. '
                    'Vuelve a validarlo.'
                )
            )


            return redirect(
                'admin:catalog_product_image_import'
            )


        try:

            with default_storage.open(
                temp_path,
                'rb',
            ) as stored_file:

                stored_file.name = (
                    original_name
                )


                result = (
                    import_validated_product_images(
                        stored_file
                    )
                )


        except Exception as exc:

            messages.error(
                request,
                (
                    'No fue posible completar '
                    'la importación de imágenes. '
                    f'Detalle: {exc}'
                )
            )


            return redirect(
                'admin:catalog_product_image_import'
            )


        self._clear_image_import_temp_file(
            request
        )


        messages.success(
            request,
            (
                'Importación de imágenes completada. '
                f'Imágenes principales actualizadas: '
                f'{result["principal_replaced_count"]}. '
                f'Imágenes agregadas a galería: '
                f'{result["gallery_created_count"]}. '
                f'Total guardadas: '
                f'{result["total_saved_count"]}. '
                f'Archivos omitidos: '
                f'{result["skipped_count"]}.'
            )
        )


        return redirect(
            'admin:catalog_product_changelist'
        )


    # ========================================================
    # DESCARGAR PLANTILLA DE PRODUCTOS
    # ========================================================

    def download_template_view(
        self,
        request,
    ):

        workbook = (
            build_product_import_template()
        )


        response = HttpResponse(
            content_type=(
                'application/vnd.'
                'openxmlformats-officedocument.'
                'spreadsheetml.sheet'
            )
        )


        response[
            'Content-Disposition'
        ] = (
            'attachment; '
            'filename="'
            'plantilla_importacion_'
            'productos_pronty.xlsx"'
        )


        workbook.save(
            response
        )


        return response


# ============================================================
# IMÁGENES DE PRODUCTO
# ============================================================

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):

    list_display = (
        'product',
        'order',
        'is_active',
        'created_at',
    )

    list_filter = (
        'is_active',
        'product',
    )

    search_fields = (
        'product__name',
        'alt_text',
    )

    ordering = (
        'product',
        'order',
    )


# ============================================================
# MOVIMIENTOS DE INVENTARIO
# ============================================================

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):

    list_display = (
        'product',
        'movement_type',
        'quantity',
        'previous_stock',
        'new_stock',
        'created_by',
        'created_at',
    )

    list_filter = (
        'movement_type',
        'created_at',
        'product',
    )

    search_fields = (
        'product__name',
        'product__sku',
        'reason',
        'reference',
    )

    readonly_fields = (
        'previous_stock',
        'new_stock',
        'created_by',
        'created_at',
    )

    ordering = (
        '-created_at',
    )

    fieldsets = (
        (
            'Movimiento',
            {
                'fields': (
                    'product',
                    'movement_type',
                    'quantity',
                )
            }
        ),
        (
            'Información adicional',
            {
                'fields': (
                    'reason',
                    'reference',
                )
            }
        ),
        (
            'Auditoría',
            {
                'fields': (
                    'previous_stock',
                    'new_stock',
                    'created_by',
                    'created_at',
                )
            }
        ),
    )


    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):

        if not change:

            obj.created_by = (
                request.user
            )


        super().save_model(
            request,
            obj,
            form,
            change,
        )


    def has_delete_permission(
        self,
        request,
        obj=None,
    ):

        return False