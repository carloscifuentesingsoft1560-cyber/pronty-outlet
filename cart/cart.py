from decimal import Decimal

from accounts.models import CustomerProfile
from catalog.models import Product


WHOLESALE_ACTIVATION_MINIMUM = Decimal('300000.00')


class Cart:

    def __init__(self, request):

        self.request = request
        self.session = request.session

        cart = self.session.get('cart')

        if not cart:
            cart = self.session['cart'] = {}

        self.cart = cart
        self.customer_profile = None

        # =====================================================
        # PERFIL COMERCIAL
        # SOLO PARA CLIENTES REALES
        # =====================================================

        if (
            request.user.is_authenticated
            and not request.user.is_staff
            and not request.user.is_superuser
        ):

            self.customer_profile, _ = (
                CustomerProfile.objects
                .get_or_create(
                    user=request.user
                )
            )

            self.customer_profile.refresh_commercial_status()


    # =========================================================
    # PRODUCTOS DEL CARRITO
    # =========================================================

    def _get_products(self):

        product_ids = self.cart.keys()

        return (
            Product.objects
            .filter(
                pk__in=product_ids,
                is_active=True
            )
        )


    # =========================================================
    # TOTAL DE REFERENCIA DETAL
    # =========================================================

    def get_retail_reference_total(self):

        products = self._get_products()

        total = Decimal('0.00')

        for product in products:

            product_id = str(product.pk)

            cart_item = self.cart.get(
                product_id
            )

            if not cart_item:
                continue

            quantity = cart_item.get(
                'quantity',
                0
            )

            total += (
                Decimal(product.retail_price)
                * quantity
            )

        return total


    # =========================================================
    # CALIFICA PARA ACTIVACIÓN MAYORISTA
    # =========================================================

    def qualifies_for_wholesale_activation(self):

        if (
            not self.request.user.is_authenticated
            or self.request.user.is_staff
            or self.request.user.is_superuser
        ):
            return False

        if not self.customer_profile:
            return False

        if self.customer_profile.commercial_status not in {
            CustomerProfile.CommercialStatus.RETAIL,
            CustomerProfile.CommercialStatus.WHOLESALE_EXPIRED,
        }:
            return False

        return (
            self.get_retail_reference_total()
            >= WHOLESALE_ACTIVATION_MINIMUM
        )


    # =========================================================
    # ¿USA PRECIO MAYORISTA?
    # =========================================================

    def uses_wholesale_prices(self):

        if not self.customer_profile:
            return False

        if self.customer_profile.has_wholesale_prices:
            return True

        return self.qualifies_for_wholesale_activation()


    # =========================================================
    # PRECIO DEL PRODUCTO
    # =========================================================

    def get_product_price(
        self,
        product,
        use_wholesale=None
    ):

        if use_wholesale is None:
            use_wholesale = self.uses_wholesale_prices()

        if (
            use_wholesale
            and product.wholesale_price is not None
        ):
            return Decimal(
                product.wholesale_price
            )

        return Decimal(
            product.retail_price
        )


    # =========================================================
    # ACTUALIZAR PRECIOS
    # =========================================================

    def refresh_prices(self):

        use_wholesale = (
            self.uses_wholesale_prices()
        )

        changed = False

        for product in self._get_products():

            product_id = str(product.pk)

            if product_id not in self.cart:
                continue

            correct_price = (
                self.get_product_price(
                    product,
                    use_wholesale=use_wholesale
                )
            )

            stored_price = Decimal(
                self.cart[
                    product_id
                ].get(
                    'price',
                    '0'
                )
            )

            if stored_price != correct_price:

                self.cart[
                    product_id
                ][
                    'price'
                ] = str(
                    correct_price
                )

                changed = True

        if changed:
            self.save()


    # =========================================================
    # AGREGAR PRODUCTO
    # =========================================================

    def add(
        self,
        product,
        quantity=1,
        override_quantity=False
    ):

        product_id = str(product.pk)

        if product_id not in self.cart:

            self.cart[
                product_id
            ] = {
                'quantity': 0,
                'price': str(
                    product.retail_price
                ),
            }

        if override_quantity:

            self.cart[
                product_id
            ][
                'quantity'
            ] = quantity

        else:

            self.cart[
                product_id
            ][
                'quantity'
            ] += quantity

        self.refresh_prices()

        self.save()


    # =========================================================
    # GUARDAR SESIÓN
    # =========================================================

    def save(self):

        self.session.modified = True


    # =========================================================
    # ELIMINAR PRODUCTO
    # =========================================================

    def remove(
        self,
        product
    ):

        product_id = str(product.pk)

        if product_id in self.cart:

            del self.cart[
                product_id
            ]

            self.refresh_prices()

            self.save()


    # =========================================================
    # ITERAR CARRITO
    # =========================================================

    def __iter__(self):

        self.refresh_prices()

        products = self._get_products()

        cart = self.cart.copy()

        use_wholesale = (
            self.uses_wholesale_prices()
        )

        for product in products:

            product_id = str(product.pk)

            if product_id not in cart:
                continue

            cart[
                product_id
            ][
                'product'
            ] = product

        for item in cart.values():

            if 'product' not in item:
                continue

            item[
                'price'
            ] = Decimal(
                item['price']
            )

            item[
                'total_price'
            ] = (
                item['price']
                * item['quantity']
            )

            item[
                'is_wholesale_price'
            ] = use_wholesale

            yield item


    # =========================================================
    # CANTIDAD
    # =========================================================

    def __len__(self):

        return sum(
            item['quantity']
            for item
            in self.cart.values()
        )


    # =========================================================
    # TOTAL
    # =========================================================

    def get_total_price(self):

        return sum(
            (
                item['total_price']
                for item
                in self
            ),
            Decimal('0.00')
        )


    # =========================================================
    # FALTA PARA MAYORISTA
    # =========================================================

    def get_amount_to_wholesale_activation(self):

        retail_total = (
            self.get_retail_reference_total()
        )

        remaining = (
            WHOLESALE_ACTIVATION_MINIMUM
            - retail_total
        )

        return max(
            remaining,
            Decimal('0.00')
        )


    # =========================================================
    # VACIAR
    # =========================================================

    def clear(self):

        if 'cart' in self.session:

            del self.session['cart']

            self.save()