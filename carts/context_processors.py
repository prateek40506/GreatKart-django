from .models import CartItem
from .views import _cart_id


def counter(request):
    total_items = 0
    cart_items = CartItem.objects.all().filter(cart__cart_id=_cart_id(request))
    if cart_items is not None:
        for cart_item in cart_items:
            total_items += cart_item.quantity
    return dict(counter=total_items)
