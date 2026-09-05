from decimal import Decimal

from catalog.models import Product


class Cart:
    def __init__(self, request):
        self.session = request.session

        cart = self.session.get('cart')

        if not cart:
            cart = self.session['cart'] = {}

        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.pk)

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.retail_price),
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.pk)

        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        product_ids = self.cart.keys()

        products = Product.objects.filter(
            pk__in=product_ids,
            is_active=True
        )

        cart = self.cart.copy()

        for product in products:
            cart[str(product.pk)]['product'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])

            item['total_price'] = (
                item['price'] * item['quantity']
            )

            yield item

    def __len__(self):
        return sum(
            item['quantity']
            for item in self.cart.values()
        )

    def get_total_price(self):
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def clear(self):
        if 'cart' in self.session:
            del self.session['cart']
            self.save()