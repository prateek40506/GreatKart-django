from django.shortcuts import render, redirect
from store.models import Product, Variation
from carts.models import Cart, CartItem
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist


# Create your views here.

# by adding an '_' in the front, a function becomes private


def _cart_id(request):
    cart_id = request.session.session_key
    if not cart_id:
        cart_id = request.session.create()
    return cart_id


def cart(request, cart_items=None):
    total = 0
    quantity = 0
    tax = 0
    grand_total = 0
    try:
        products_cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.all().filter(cart=products_cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.quantity * cart_item.product.price)
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass
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
    product = Product.objects.get(id=product_id)
    # to store all variations of the given product
    product_variation = []
    if request.method == "POST":
        for item in request.POST:
            key = item
            value = request.POST[key]
            print(key, value)
            try:
                variation = Variation.objects.get(product=product, variation_category=key, variation_value=value)
                product_variation.append(variation)
                print(variation.product)
            except Variation.DoesNotExist:
                print("variation object not found")
    try:
        products_cart = Cart.objects.get(
            cart_id=_cart_id(request))  # get the cart using the cart_id present in the session
    except Cart.DoesNotExist:
        products_cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )
        products_cart.save()
    # cart has been created if it didn't exist
    is_cart_item_exists = CartItem.objects.filter(product=product, cart=products_cart).exists()
    if is_cart_item_exists:
        # product exists in cart
        product_cart_items = CartItem.objects.filter(product=product, cart=products_cart)
        ex_var_list = []
        cart_sno = []
        for i in product_cart_items:
            existing_variation = i.variations.all()
            ex_var_list.append(list(existing_variation))
            cart_sno.append(i.id)
        if product_variation in ex_var_list:
            index = ex_var_list.index(product_variation)
            # print(index)
            # print(cart_sno[index])
            cart_item_object = CartItem.objects.get(product=product, id=cart_sno[index])
            cart_item_object.quantity += 1
            cart_item_object.save()
            # increase the cart item quantity
        else:
            item = CartItem.objects.create(
                product=product,
                cart=products_cart,
                quantity=1
            )
            item.variations.add(*product_variation)
            item.save()
    else:
        item = CartItem.objects.create(
            product=product,
            cart=products_cart,
            quantity=1
            )
        item.variations.add(*product_variation)
        item.save()
    return redirect('cart')


def increment_qty(request, item_id):
    cart_item = CartItem.objects.get(id=item_id)
    cart_item.quantity += 1
    cart_item.save()
    return redirect('cart')


def decrement_qty(request, item_id):
    cart_item = CartItem.objects.get(id=item_id)
    cart_item.quantity -= 1
    cart_item.save()
    return redirect('cart')


def delete_cart(request, item_id):
    cart_item = CartItem.objects.get(id=item_id)
    cart_item.delete()
    return redirect('cart')
