from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from store.models import Product, Variation
from carts.models import Cart, CartItem


# Create your views here.

# by adding an '_' in the front, a function becomes private


def _cart_id(request):
    cart_id = request.session.session_key
    if not cart_id:
        cart_id = request.session.create()
    return cart_id


def cart(request):
    total = 0
    quantity = 0
    tax = 0
    grand_total = 0
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)
    else:
        cart_items = CartItem.objects.filter(cart__cart_id=_cart_id(request), is_active=True)
    if cart_items is not None:
        for cart_item in cart_items:
            total += (cart_item.quantity * cart_item.product.price)
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total += total + tax
    context = {
        'cart_items': cart_items,
        'quantity': quantity,
        'total': total,
        'tax': tax,
        'grand_total': grand_total
    }
    return render(request, 'store/cart.html', context)


# the session id is the cart id


def add_cart(request, product_id):
    if request.method == 'POST':
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id=_cart_id(request)
            )
            cart.save()
        product = Product.objects.get(id=product_id)
        product_variations = []
        #  key is the variation category
        for key in request.POST:
            value = request.POST[key]
            try:
                product_variation = Variation.objects.get(product=product, variation_category=key, variation_value=value)
                product_variations.append(product_variation)
            except Variation.DoesNotExist:
                pass
        # print(product_variations)
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, product=product)
            if cart_items is not None:
                ex_var_list = []
                cart_sno = []
                for cart_item in cart_items:
                    existing_variations = cart_item.variations.all()
                    ex_var_list.append(list(existing_variations))
                    cart_sno.append(cart_item.id)
                if product_variations in ex_var_list:
                    cart_item_id = cart_sno[ex_var_list.index(product_variations)]
                    item = CartItem.objects.get(id=cart_item_id)
                    item.quantity += 1
                    item.save()
                else:
                    cart_item = CartItem.objects.create(
                        user=request.user,
                        product=product,
                        cart=cart,
                        quantity=1
                    )
                    cart_item.variations.add(*product_variations)
                    cart_item.save()
            else:
                cart_item = CartItem.objects.create(
                    user=request.user,
                    product=product,
                    cart=cart,
                    quantity=1
                )
                cart_item.variations.add(*product_variations)
                cart_item.save()
        else:
            cart_items = CartItem.objects.filter(cart=cart, product=product)
            if cart_items is not None:
                ex_var_list = []
                cart_sno = []
                for cart_item in cart_items:
                    existing_variations = cart_item.variations.all()
                    ex_var_list.append(list(existing_variations))
                    cart_sno.append(cart_item.id)
                if product_variations in ex_var_list:
                    cart_item_id = cart_sno[ex_var_list.index(product_variations)]
                    item = CartItem.objects.get(id=cart_item_id)
                    item.quantity += 1
                    item.save()
                else:
                    cart_item = CartItem.objects.create(
                        product=product,
                        cart=cart,
                        quantity=1
                    )
                    cart_item.variations.add(*product_variations)
                    cart_item.save()
            else:
                cart_item = CartItem.objects.create(
                    user=request.user,
                    product=product,
                    cart=cart,
                    quantity=1
                )
                cart_item.variations.add(*product_variations)
                cart_item.save()
    return redirect('cart')


def increment_qty(request, item_id):
    cart_item = CartItem.objects.get(id=item_id)
    cart_item.quantity += 1
    cart_item.save()
    return redirect('cart')


def decrement_qty(request, item_id):
    cart_item = CartItem.objects.get(id=item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')


def delete_cart(request, item_id):
    cart_item = CartItem.objects.get(id=item_id)
    cart_item.delete()
    return redirect('cart')


@login_required(login_url='login')
def checkout(request):
    total = 0
    quantity = 0
    tax = 0
    grand_total = 0
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
    else:
        cart_items = CartItem.objects.filter(cart__cart_id=_cart_id(request))
    if cart_items is not None:
        for cart_item in cart_items:
            total += (cart_item.quantity * cart_item.product.price)
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    context = {
        'cart_items': cart_items,
        'quantity': quantity,
        'total': total,
        'tax': tax,
        'grand_total': grand_total
    }
    return render(request, 'store/checkout.html', context)
