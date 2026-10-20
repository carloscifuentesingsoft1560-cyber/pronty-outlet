import io
import zipfile

from pathlib import Path

from django import forms
from django.core.files.base import ContentFile
from django.db import transaction

from PIL import Image, UnidentifiedImageError

from .models import (
    Product,
    ProductImage,
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

MAX_ZIP_SIZE = (
    250 * 1024 * 1024
)

MAX_IMAGE_SIZE = (
    15 * 1024 * 1024
)

MAX_IMAGES = 10000

MAX_TOTAL_UNCOMPRESSED_SIZE = (
    500 * 1024 * 1024
)


ALLOWED_IMAGE_EXTENSIONS = {
    '.jpg',
    '.jpeg',
    '.png',
    '.webp',
}


# ============================================================
# EXCEPCIÓN
# ============================================================

class ProductImageImportError(
    Exception
):
    pass


# ============================================================
# FORMULARIO
# ============================================================

class ProductImageZipForm(
    forms.Form
):

    images_zip = forms.FileField(
        label='Archivo ZIP de imágenes',
        help_text=(
            'Carga un archivo .zip '
            'con las fotografías de productos.'
        ),
        widget=forms.ClearableFileInput(
            attrs={
                'accept': '.zip',
            }
        ),
    )


    def clean_images_zip(
        self
    ):

        uploaded_file = (
            self.cleaned_data[
                'images_zip'
            ]
        )


        extension = (
            Path(
                uploaded_file.name
            )
            .suffix
            .lower()
        )


        if extension != '.zip':

            raise forms.ValidationError(
                (
                    'El archivo de imágenes '
                    'debe ser un ZIP.'
                )
            )


        if (
            uploaded_file.size
            > MAX_ZIP_SIZE
        ):

            raise forms.ValidationError(
                (
                    'El archivo ZIP supera '
                    'el máximo permitido '
                    'de 250 MB.'
                )
            )


        return uploaded_file


# ============================================================
# NOMBRE SEGURO
# ============================================================

def _safe_basename(
    filename
):

    normalized = (
        filename
        .replace(
            '\\',
            '/'
        )
    )


    return (
        Path(
            normalized
        ).name
    )


# ============================================================
# VERIFICAR CONTENIDO REAL DE IMAGEN
# ============================================================

def _verify_image_bytes(
    image_bytes,
):

    try:

        image_buffer = io.BytesIO(
            image_bytes
        )


        with Image.open(
            image_buffer
        ) as image:

            image.verify()


        return True


    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ):

        return False


# ============================================================
# INTERPRETAR NOMBRE DE IMAGEN
# ============================================================

def _parse_image_filename(
    filename,
    products_by_sku,
):

    basename = (
        _safe_basename(
            filename
        )
    )


    path = Path(
        basename
    )


    extension = (
        path.suffix
        .lower()
    )


    if (
        extension
        not in ALLOWED_IMAGE_EXTENSIONS
    ):

        return None


    stem = (
        path.stem
        .strip()
    )


    if not stem:

        return None


    # ========================================================
    # REGLA 1:
    # EL NOMBRE COMPLETO PUEDE SER UN SKU REAL
    #
    # TEST-001.jpg
    # → SKU TEST-001
    # ========================================================

    exact_product = (
        products_by_sku.get(
            stem.casefold()
        )
    )


    if exact_product is not None:

        return {
            'sku': (
                exact_product.sku
            ),
            'order': 1,
            'is_numbered': False,
            'filename': basename,
            'extension': extension,
            'product': (
                exact_product
            ),
        }


    # ========================================================
    # REGLA 2:
    # SKU-NÚMERO
    #
    # SHEIN-BLU-001-2.jpg
    # → SKU SHEIN-BLU-001
    # → orden 2
    # ========================================================

    if '-' in stem:

        possible_sku, possible_order = (
            stem.rsplit(
                '-',
                1,
            )
        )


        possible_sku = (
            possible_sku
            .strip()
        )


        possible_order = (
            possible_order
            .strip()
        )


        if (
            possible_sku
            and possible_order.isdigit()
        ):

            order = int(
                possible_order
            )


            if order > 0:

                product = (
                    products_by_sku.get(
                        possible_sku.casefold()
                    )
                )


                if product is not None:

                    return {
                        'sku': (
                            product.sku
                        ),
                        'order': order,
                        'is_numbered': True,
                        'filename': basename,
                        'extension': extension,
                        'product': (
                            product
                        ),
                    }


    # ========================================================
    # NO SE ENCONTRÓ PRODUCTO
    # ========================================================

    return {
        'sku': stem,
        'order': 1,
        'is_numbered': False,
        'filename': basename,
        'extension': extension,
        'product': None,
    }


# ============================================================
# ABRIR ZIP
# ============================================================

def _open_zip(
    uploaded_file,
):

    uploaded_file.seek(
        0
    )


    try:

        raw_bytes = (
            uploaded_file.read()
        )


        zip_buffer = (
            io.BytesIO(
                raw_bytes
            )
        )


        archive = zipfile.ZipFile(
            zip_buffer,
            'r',
        )


        return archive


    except (
        zipfile.BadZipFile,
        OSError,
    ) as exc:

        raise ProductImageImportError(
            (
                'No fue posible abrir '
                'el archivo ZIP.'
            )
        ) from exc


# ============================================================
# VALIDAR ZIP
# ============================================================

def validate_product_images_zip(
    uploaded_file,
):

    archive = (
        _open_zip(
            uploaded_file
        )
    )


    products_by_sku = {
        product.sku.casefold(): product
        for product
        in Product.objects.all()
    }


    valid_images = []

    invalid_files = []

    missing_products = []

    oversized_images = []


    seen_names = set()


    image_count = 0

    total_uncompressed_size = 0


    try:

        for zip_info in archive.infolist():


            if zip_info.is_dir():

                continue


            basename = (
                _safe_basename(
                    zip_info.filename
                )
            )


            # =================================================
            # IGNORAR ARCHIVOS DE SISTEMA
            # =================================================

            if (
                basename.startswith(
                    '.'
                )
                or basename.lower()
                in {
                    'thumbs.db',
                    'desktop.ini',
                }
            ):

                continue


            parsed = (
                _parse_image_filename(
                    basename,
                    products_by_sku,
                )
            )


            if parsed is None:

                invalid_files.append({
                    'filename': (
                        basename
                    ),
                    'reason': (
                        'Formato o extensión '
                        'no permitida.'
                    ),
                })

                continue


            image_count += 1


            if image_count > MAX_IMAGES:

                raise ProductImageImportError(
                    (
                        'El ZIP supera el máximo '
                        f'de {MAX_IMAGES} imágenes.'
                    )
                )


            total_uncompressed_size += (
                zip_info.file_size
            )


            if (
                total_uncompressed_size
                > MAX_TOTAL_UNCOMPRESSED_SIZE
            ):

                raise ProductImageImportError(
                    (
                        'El contenido descomprimido '
                        'del ZIP supera el máximo '
                        'permitido de 500 MB.'
                    )
                )


            # =================================================
            # TAMAÑO INDIVIDUAL
            # =================================================

            if (
                zip_info.file_size
                > MAX_IMAGE_SIZE
            ):

                oversized_images.append({
                    'filename': (
                        basename
                    ),
                    'size': (
                        zip_info.file_size
                    ),
                })

                continue


            # =================================================
            # DUPLICADO DE NOMBRE
            # =================================================

            normalized_name = (
                basename.casefold()
            )


            if (
                normalized_name
                in seen_names
            ):

                invalid_files.append({
                    'filename': (
                        basename
                    ),
                    'reason': (
                        'Nombre de imagen '
                        'duplicado dentro del ZIP.'
                    ),
                })

                continue


            seen_names.add(
                normalized_name
            )


            # =================================================
            # VERIFICAR QUE SEA IMAGEN REAL
            # =================================================

            try:

                image_bytes = (
                    archive.read(
                        zip_info
                    )
                )


            except (
                KeyError,
                RuntimeError,
                OSError,
            ):

                invalid_files.append({
                    'filename': (
                        basename
                    ),
                    'reason': (
                        'No fue posible leer '
                        'el archivo.'
                    ),
                })

                continue


            if not _verify_image_bytes(
                image_bytes
            ):

                invalid_files.append({
                    'filename': (
                        basename
                    ),
                    'reason': (
                        'El archivo no contiene '
                        'una imagen válida.'
                    ),
                })

                continue


            # =================================================
            # PRODUCTO
            # =================================================

            product = (
                parsed[
                    'product'
                ]
            )


            if product is None:

                missing_products.append({
                    'filename': (
                        basename
                    ),
                    'sku': (
                        parsed[
                            'sku'
                        ]
                    ),
                })

                continue


            valid_images.append({
                'filename': (
                    basename
                ),
                'zip_path': (
                    zip_info.filename
                ),
                'sku': (
                    product.sku
                ),
                'product_id': (
                    product.pk
                ),
                'product_name': (
                    product.name
                ),
                'order': (
                    parsed[
                        'order'
                    ]
                ),
                'is_numbered': (
                    parsed[
                        'is_numbered'
                    ]
                ),
                'size': (
                    zip_info.file_size
                ),
                'extension': (
                    parsed[
                        'extension'
                    ]
                ),
            })


    finally:

        archive.close()


    # ========================================================
    # AGRUPAR POR PRODUCTO
    # ========================================================

    grouped = {}


    for image in valid_images:

        sku_key = (
            image[
                'sku'
            ].casefold()
        )


        if sku_key not in grouped:

            grouped[
                sku_key
            ] = {
                'sku': (
                    image[
                        'sku'
                    ]
                ),
                'product_id': (
                    image[
                        'product_id'
                    ]
                ),
                'product_name': (
                    image[
                        'product_name'
                    ]
                ),
                'images': [],
            }


        grouped[
            sku_key
        ][
            'images'
        ].append(
            image
        )


    product_groups = []


    for group in grouped.values():

        group[
            'images'
        ].sort(
            key=lambda item: (
                item[
                    'order'
                ],
                item[
                    'filename'
                ].casefold(),
            )
        )


        has_plain = any(
            not image[
                'is_numbered'
            ]
            for image
            in group[
                'images'
            ]
        )


        has_numbered = any(
            image[
                'is_numbered'
            ]
            for image
            in group[
                'images'
            ]
        )


        warnings = []


        # ====================================================
        # IMAGEN SIMPLE + NUMERADAS
        # ====================================================

        if (
            has_plain
            and has_numbered
        ):

            warnings.append(
                (
                    'El SKU tiene una imagen '
                    'simple y también imágenes '
                    'numeradas. Si existe una '
                    'imagen -1, esa tendrá '
                    'prioridad como principal.'
                )
            )


        # ====================================================
        # ÓRDENES NUMERADOS DUPLICADOS
        # ====================================================

        numbered_orders = [
            image[
                'order'
            ]
            for image
            in group[
                'images'
            ]
            if image[
                'is_numbered'
            ]
        ]


        duplicate_orders = {
            order
            for order
            in numbered_orders
            if (
                numbered_orders.count(
                    order
                )
                > 1
            )
        }


        if duplicate_orders:

            warnings.append(
                (
                    'Hay números de imagen '
                    'repetidos: '
                    + ', '.join(
                        str(
                            value
                        )
                        for value
                        in sorted(
                            duplicate_orders
                        )
                    )
                    + '.'
                )
            )


        # ====================================================
        # NUMERADAS SIN -1
        # ====================================================

        if (
            has_numbered
            and numbered_orders
            and 1 not in numbered_orders
        ):

            warnings.append(
                (
                    'Las imágenes numeradas '
                    'no incluyen una imagen -1. '
                    'No se reemplazará la imagen '
                    'principal con este grupo.'
                )
            )


        group[
            'warnings'
        ] = warnings


        group[
            'image_count'
        ] = len(
            group[
                'images'
            ]
        )


        product_groups.append(
            group
        )


    product_groups.sort(
        key=lambda item: (
            item[
                'sku'
            ].casefold()
        )
    )


    warning_count = sum(
        1
        for group
        in product_groups
        if group[
            'warnings'
        ]
    )


    return {
        'filename': (
            uploaded_file.name
        ),
        'total_files': (
            image_count
        ),
        'valid_image_count': (
            len(
                valid_images
            )
        ),
        'product_count': (
            len(
                product_groups
            )
        ),
        'missing_product_count': (
            len(
                missing_products
            )
        ),
        'invalid_file_count': (
            len(
                invalid_files
            )
        ),
        'oversized_count': (
            len(
                oversized_images
            )
        ),
        'warning_count': (
            warning_count
        ),
        'product_groups': (
            product_groups
        ),
        'missing_products': (
            missing_products
        ),
        'invalid_files': (
            invalid_files
        ),
        'oversized_images': (
            oversized_images
        ),
        'valid_images': (
            valid_images
        ),
    }


# ============================================================
# ELEGIR IMAGEN PRINCIPAL
# ============================================================

def _get_main_image(
    images,
):

    # ========================================================
    # PRIORIDAD 1:
    # SKU-1.jpg
    # ========================================================

    numbered_main = next(
        (
            image
            for image
            in images
            if (
                image[
                    'is_numbered'
                ]
                and image[
                    'order'
                ] == 1
            )
        ),
        None,
    )


    if numbered_main is not None:

        return numbered_main


    # ========================================================
    # PRIORIDAD 2:
    # SKU.jpg
    # ========================================================

    plain_main = next(
        (
            image
            for image
            in images
            if not image[
                'is_numbered'
            ]
        ),
        None,
    )


    return plain_main


# ============================================================
# IMPORTAR IMÁGENES VALIDADAS
# ============================================================

def import_validated_product_images(
    uploaded_file,
):

    # ========================================================
    # VOLVER A VALIDAR ANTES DE GUARDAR
    # ========================================================

    validation = (
        validate_product_images_zip(
            uploaded_file
        )
    )


    valid_images = (
        validation[
            'valid_images'
        ]
    )


    if not valid_images:

        raise ProductImageImportError(
            (
                'El ZIP no contiene '
                'imágenes válidas para importar.'
            )
        )


    # ========================================================
    # REABRIR ZIP
    # ========================================================

    archive = (
        _open_zip(
            uploaded_file
        )
    )


    principal_replaced_count = 0

    gallery_created_count = 0

    skipped_count = (
        validation[
            'missing_product_count'
        ]
        + validation[
            'invalid_file_count'
        ]
        + validation[
            'oversized_count'
        ]
    )


    try:

        with transaction.atomic():

            for group in validation[
                'product_groups'
            ]:

                product = (
                    Product.objects
                    .select_for_update()
                    .get(
                        pk=(
                            group[
                                'product_id'
                            ]
                        )
                    )
                )


                images = (
                    group[
                        'images'
                    ]
                )


                main_image = (
                    _get_main_image(
                        images
                    )
                )


                # =================================================
                # IMAGEN PRINCIPAL
                # =================================================

                if main_image is not None:

                    main_bytes = (
                        archive.read(
                            main_image[
                                'zip_path'
                            ]
                        )
                    )


                    main_file = ContentFile(
                        main_bytes
                    )


                    product.image.save(
                        main_image[
                            'filename'
                        ],
                        main_file,
                        save=False,
                    )


                    product.save(
                        update_fields=[
                            'image',
                            'updated_at',
                        ]
                    )


                    principal_replaced_count += 1


                # =================================================
                # GALERÍA
                # =================================================

                for image in images:


                    if (
                        main_image is not None
                        and image[
                            'zip_path'
                        ]
                        == main_image[
                            'zip_path'
                        ]
                    ):

                        continue


                    # ---------------------------------------------
                    # UNA IMAGEN SIMPLE NO SE DUPLICA EN GALERÍA
                    # ---------------------------------------------

                    if not image[
                        'is_numbered'
                    ]:

                        continue


                    # ---------------------------------------------
                    # -1 ES PRINCIPAL
                    # ---------------------------------------------

                    if image[
                        'order'
                    ] == 1:

                        continue


                    gallery_bytes = (
                        archive.read(
                            image[
                                'zip_path'
                            ]
                        )
                    )


                    gallery_file = ContentFile(
                        gallery_bytes
                    )


                    product_image = (
                        ProductImage(
                            product=product,
                            alt_text=(
                                product.name
                            ),
                            order=(
                                image[
                                    'order'
                                ]
                            ),
                            is_active=True,
                        )
                    )


                    product_image.image.save(
                        image[
                            'filename'
                        ],
                        gallery_file,
                        save=False,
                    )


                    product_image.save()


                    gallery_created_count += 1


    except (
        KeyError,
        RuntimeError,
        OSError,
    ) as exc:

        raise ProductImageImportError(
            (
                'No fue posible leer una '
                'de las imágenes del ZIP.'
            )
        ) from exc


    finally:

        archive.close()


    return {
        'principal_replaced_count': (
            principal_replaced_count
        ),
        'gallery_created_count': (
            gallery_created_count
        ),
        'total_saved_count': (
            principal_replaced_count
            + gallery_created_count
        ),
        'skipped_count': (
            skipped_count
        ),
        'product_count': (
            validation[
                'product_count'
            ]
        ),
    }