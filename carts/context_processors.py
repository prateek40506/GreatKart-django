from .models import CartItem
from .views import _cart_id


def counter(request):
    total_items = 0
    # condition for a logged-in user
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
    else:
        cart_items = CartItem.objects.filter(cart__cart_id=_cart_id(request))
    if cart_items is not None:
        for cart_item in cart_items:
            total_items += cart_item.quantity
    return dict(counter=total_items)
