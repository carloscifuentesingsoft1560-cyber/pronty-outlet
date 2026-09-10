from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from catalog.models import InventoryMovement, Product

from .cart import Cart
from .models import Order, OrderItem


FREE_SHIPPING_MINIMUM = Decimal('1000000.00')


def get_order_for_payment(request, order_number):

    if request.user.is_authenticated:

        return get_object_or_404(
            Order,
            order_number=order_number,
            customer=request.user
        )

    order = get_object_or_404(
        Order,
        order_number=order_number,
        customer__isnull=True
    )

    session_order_id = request.session.get(
        'last_order_id'
    )

    if session_order_id != order.pk:

        raise Http404(
            'Pedido no encontrado.'
        )

    return order


def cart_detail(request):

    cart = Cart(request)

    return render(
        request,
        'cart/cart_detail.html',
        {
            'cart': cart
        }
    )


def checkout(request):

    cart = Cart(request)

    if len(cart) == 0:

        return redirect(
            'cart:cart_detail'
        )

    checkout_data = {
        'name': '',
        'email': '',
        'whatsapp': '',
        'department': '',
        'city': '',
        'address': '',
        'delivery_notes': '',
        'carrier': '',
    }

    if request.user.is_authenticated:

        checkout_data['name'] = (
            request.user.get_full_name()
            or request.user.username
        )

        checkout_data['email'] = (
            request.user.email
            or ''
        )

    if request.method == 'POST':

        checkout_data = {
            'name': request.POST.get(
                'name',
                ''
            ).strip(),

            'email': request.POST.get(
                'email',
                ''
            ).strip(),

            'whatsapp': request.POST.get(
                'whatsapp',
                ''
            ).strip(),

            'department': request.POST.get(
                'department',
                ''
            ).strip(),

            'city': request.POST.get(
                'city',
                ''
            ).strip(),

            'address': request.POST.get(
                'address',
                ''
            ).strip(),

            'delivery_notes': request.POST.get(
                'delivery_notes',
                ''
            ).strip(),

            'carrier': request.POST.get(
                'carrier',
                ''
            ).strip(),
        }

        required_fields = [
            'name',
            'email',
            'whatsapp',
            'department',
            'city',
            'address',
            'carrier',
        ]

        missing_fields = [
            field
            for field in required_fields
            if not checkout_data[field]
        ]

        if missing_fields:

            messages.error(
                request,
                'Completa todos los campos obligatorios.'
            )

            return render(
                request,
                'cart/checkout.html',
                {
                    'cart': cart,
                    'checkout_data': checkout_data,
                }
            )

        try:

            validate_email(
                checkout_data['email']
            )

        except ValidationError:

            messages.error(
                request,
                'Ingresa un correo electrónico válido.'
            )

            return render(
                request,
                'cart/checkout.html',
                {
                    'cart': cart,
                    'checkout_data': checkout_data,
                }
            )

        # =====================================================
        # INFORMACIÓN COMERCIAL
        # =====================================================

        retail_reference_total = (
            cart.get_retail_reference_total()
        )

        wholesale_activation_qualified = (
            cart.qualifies_for_wholesale_activation()
        )

        final_order_total = (
            cart.get_total_price()
        )

        # =====================================================
        # ENVÍO GRATIS DESDE $1.000.000
        # =====================================================

        free_shipping = (
            final_order_total
            >= FREE_SHIPPING_MINIMUM
        )

        if free_shipping:
            shipping_cost = Decimal('0.00')
        else:
            shipping_cost = None

        try:

            with transaction.atomic():

                cart_items = list(cart)

                if not cart_items:

                    messages.error(
                        request,
                        'Tu carrito está vacío.'
                    )

                    return redirect(
                        'cart:cart_detail'
                    )

                validated_items = []

                # =================================================
                # VALIDAR EXISTENCIAS
                # =================================================

                for item in cart_items:

                    product = (
                        Product.objects
                        .select_for_update()
                        .get(
                            pk=item['product'].pk,
                            is_active=True
                        )
                    )

                    quantity = item[
                        'quantity'
                    ]

                    if quantity > product.stock:

                        raise ValidationError(
                            (
                                f'No hay suficientes unidades de '
                                f'"{product.name}". '
                                f'Disponibles: {product.stock}.'
                            )
                        )

                    validated_items.append(
                        {
                            'product': product,
                            'quantity': quantity,
                            'unit_price': item['price'],
                            'subtotal': item['total_price'],
                        }
                    )

                # =================================================
                # CLIENTE
                # =================================================

                customer = None

                if (
                    request.user.is_authenticated
                    and not request.user.is_staff
                    and not request.user.is_superuser
                ):

                    customer = request.user

                # =================================================
                # CREAR PEDIDO
                # =================================================

                order = Order.objects.create(
                    customer=customer,

                    customer_name=checkout_data[
                        'name'
                    ],

                    email=checkout_data[
                        'email'
                    ],

                    whatsapp=checkout_data[
                        'whatsapp'
                    ],

                    department=checkout_data[
                        'department'
                    ],

                    city=checkout_data[
                        'city'
                    ],

                    address=checkout_data[
                        'address'
                    ],

                    delivery_notes=checkout_data[
                        'delivery_notes'
                    ],

                    carrier=checkout_data[
                        'carrier'
                    ],

                    retail_reference_total=(
                        retail_reference_total
                    ),

                    wholesale_activation_qualified=(
                        wholesale_activation_qualified
                    ),

                    free_shipping=(
                        free_shipping
                    ),

                    shipping_cost=(
                        shipping_cost
                    ),

                    total=(
                        final_order_total
                    ),
                )

                # =================================================
                # RESERVA EXACTA DE 3 DÍAS
                # =================================================

                order.reservation_expires_at = (
                    order.created_at
                    + timedelta(days=3)
                )

                order.save(
                    update_fields=[
                        'reservation_expires_at',
                        'updated_at',
                    ]
                )

                # =================================================
                # PRODUCTOS + RESERVA DE INVENTARIO
                # =================================================

                for item in validated_items:

                    product = item[
                        'product'
                    ]

                    quantity = item[
                        'quantity'
                    ]

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        sku=product.sku,
                        quantity=quantity,
                        unit_price=item[
                            'unit_price'
                        ],
                        subtotal=item[
                            'subtotal'
                        ],
                    )

                    # =============================================
                    # IMPORTANTE:
                    # YA NO ES UNA VENTA.
                    # ES UNA RESERVA TEMPORAL.
                    # =============================================

                    InventoryMovement.objects.create(
                        product=product,

                        movement_type=(
                            InventoryMovement
                            .MovementType
                            .RESERVATION
                        ),

                        quantity=quantity,

                        reason=(
                            f'Reserva temporal correspondiente '
                            f'al pedido {order.order_number}'
                        ),

                        reference=(
                            order.order_number
                        ),

                        created_by=(
                            request.user
                            if (
                                request.user.is_authenticated
                                and not request.user.is_staff
                                and not request.user.is_superuser
                            )
                            else None
                        ),
                    )

        except Product.DoesNotExist:

            messages.error(
                request,
                'Uno de los productos del carrito '
                'ya no está disponible.'
            )

            return render(
                request,
                'cart/checkout.html',
                {
                    'cart': cart,
                    'checkout_data': checkout_data,
                }
            )

        except ValidationError as error:

            if hasattr(
                error,
                'messages'
            ):

                error_message = ' '.join(
                    error.messages
                )

            else:

                error_message = str(
                    error
                )

            messages.error(
                request,
                error_message
            )

            return render(
                request,
                'cart/checkout.html',
                {
                    'cart': cart,
                    'checkout_data': checkout_data,
                }
            )

        request.session[
            'last_order_id'
        ] = order.pk

        cart.clear()

        return redirect(
            'cart:order_confirmation'
        )

    return render(
        request,
        'cart/checkout.html',
        {
            'cart': cart,
            'checkout_data': checkout_data,
        }
    )


def order_confirmation(request):

    order_id = request.session.get(
        'last_order_id'
    )

    if not order_id:

        return redirect(
            'home'
        )

    if request.user.is_authenticated:

        if (
            request.user.is_staff
            or request.user.is_superuser
        ):

            raise Http404(
                'Pedido no encontrado.'
            )

        order = get_object_or_404(
            Order.objects.prefetch_related(
                'items'
            ),
            pk=order_id,
            customer=request.user
        )

    else:

        order = get_object_or_404(
            Order.objects.prefetch_related(
                'items'
            ),
            pk=order_id,
            customer__isnull=True
        )

    return render(
        request,
        'cart/order_confirmation.html',
        {
            'order': order
        }
    )


def order_payment(request, order_number):

    order = get_order_for_payment(
        request,
        order_number
    )

    allowed_statuses = [
        Order.Status.PENDING_PAYMENT,
        Order.Status.PROOF_RECEIVED,
        Order.Status.PAYMENT_DECLINED,
    ]

    if order.status not in allowed_statuses:

        request.session[
            'last_order_id'
        ] = order.pk

        return redirect(
            'cart:order_confirmation'
        )

    if request.method == 'POST':

        payment_method = request.POST.get(
            'payment_method',
            ''
        ).strip()

        payment_proof = request.FILES.get(
            'payment_proof'
        )

        valid_methods = [
            Order.PaymentMethod.NEQUI,
            Order.PaymentMethod.BRE_B,
            Order.PaymentMethod.BANCOLOMBIA,
        ]

        if payment_method not in valid_methods:

            messages.error(
                request,
                'Selecciona un método de pago válido.'
            )

            return render(
                request,
                'cart/order_payment.html',
                {
                    'order': order,
                    'selected_payment_method': payment_method,
                }
            )

        if not payment_proof:

            messages.error(
                request,
                'Debes adjuntar el comprobante de pago.'
            )

            return render(
                request,
                'cart/order_payment.html',
                {
                    'order': order,
                    'selected_payment_method': payment_method,
                }
            )

        allowed_content_types = [
            'image/jpeg',
            'image/png',
            'image/webp',
        ]

        if (
            payment_proof.content_type
            not in allowed_content_types
        ):

            messages.error(
                request,
                'El comprobante debe ser una imagen '
                'JPG, PNG o WEBP.'
            )

            return render(
                request,
                'cart/order_payment.html',
                {
                    'order': order,
                    'selected_payment_method': payment_method,
                }
            )

        max_size = (
            5
            * 1024
            * 1024
        )

        if payment_proof.size > max_size:

            messages.error(
                request,
                'El comprobante no puede superar 5 MB.'
            )

            return render(
                request,
                'cart/order_payment.html',
                {
                    'order': order,
                    'selected_payment_method': payment_method,
                }
            )

        order.payment_method = (
            payment_method
        )

        order.payment_proof = (
            payment_proof
        )

        order.payment_proof_uploaded_at = (
            timezone.now()
        )

        order.status = (
            Order.Status.PROOF_RECEIVED
        )

        order.save(
            update_fields=[
                'payment_method',
                'payment_proof',
                'payment_proof_uploaded_at',
                'status',
                'updated_at',
            ]
        )

        request.session[
            'last_order_id'
        ] = order.pk

        messages.success(
            request,
            'Comprobante recibido correctamente. '
            'Nuestro equipo validará el pago.'
        )

        return redirect(
            'cart:order_confirmation'
        )

    return render(
        request,
        'cart/order_payment.html',
        {
            'order': order,
            'selected_payment_method': (
                order.payment_method
            ),
        }
    )


@require_POST
def cart_add(request, product_id):

    cart = Cart(request)

    product = get_object_or_404(
        Product,
        pk=product_id,
        is_active=True
    )

    try:

        quantity = int(
            request.POST.get(
                'quantity',
                1
            )
        )

    except (
        TypeError,
        ValueError
    ):

        quantity = 1

    if quantity < 1:
        quantity = 1

    if product.stock <= 0:

        return redirect(
            'product_detail',
            slug=product.slug
        )

    product_id_string = str(
        product.pk
    )

    current_quantity = (
        cart.cart
        .get(
            product_id_string,
            {}
        )
        .get(
            'quantity',
            0
        )
    )

    available_quantity = max(
        product.stock
        - current_quantity,
        0
    )

    quantity = min(
        quantity,
        available_quantity
    )

    if quantity > 0:

        cart.add(
            product=product,
            quantity=quantity
        )

    return redirect(
        'cart:cart_detail'
    )


@require_POST
def cart_update(request, product_id):

    cart = Cart(request)

    product = get_object_or_404(
        Product,
        pk=product_id,
        is_active=True
    )

    try:

        quantity = int(
            request.POST.get(
                'quantity',
                1
            )
        )

    except (
        TypeError,
        ValueError
    ):

        quantity = 1

    if quantity <= 0:

        cart.remove(
            product
        )

    else:

        quantity = min(
            quantity,
            product.stock
        )

        cart.add(
            product=product,
            quantity=quantity,
            override_quantity=True
        )

    return redirect(
        'cart:cart_detail'
    )


@require_POST
def cart_remove(request, product_id):

    cart = Cart(request)

    product = get_object_or_404(
        Product,
        pk=product_id
    )

    cart.remove(
        product
    )

    return redirect(
        'cart:cart_detail'
    )


@require_POST
def cart_clear(request):

    cart = Cart(request)

    cart.clear()

    return redirect(
        'cart:cart_detail'
    )