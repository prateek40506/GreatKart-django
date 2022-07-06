from django.shortcuts import render, redirect, HttpResponse
from carts.models import CartItem
from .forms import Order, OrderForm
from .models import Order, Payment, OrderProduct
import datetime
import json
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage


# Create your views here.


def place_order(request):
    if request.method == 'POST':
        current_user = request.user
        # if the cart_count is less than or equal to 0, then redirect to the store pagedsdz
        cart_items = CartItem.objects.filter(user=current_user)
        if len(cart_items) <= 0:
            return redirect('store')
        else:
            form = OrderForm(request.POST)
            if form.is_valid():
                # Store all the willing information inside Order Table
                order = Order()
                order.user = current_user
                order.first_name = form.cleaned_data['first_name']
                order.last_name = form.cleaned_data['last_name']
                order.phone = form.cleaned_data['phone']
                order.email = form.cleaned_data['email']
                order.address_line_1 = form.cleaned_data['address_line_1']
                order.address_line_2 = form.cleaned_data['address_line_2']
                order.country = form.cleaned_data['country']
                order.state = form.cleaned_data['state']
                order.city = form.cleaned_data['city']
                order.order_note = form.cleaned_data['order_note']
                total = 0
                quantity = 0
                for cart_item in cart_items:
                    total += (cart_item.product.price * cart_item.quantity)
                    quantity += cart_item.quantity
                tax = (2 * total) / 100
                grand_total = total + tax
                order.order_total = grand_total
                order.tax = tax
                order.ip = request.META.get('REMOTE_ADDR')
                # after saving the data, the order object gets the id
                order.save()
                # generate order number
                yr = int(datetime.date.today().strftime('%Y'))
                dt = int(datetime.date.today().strftime('%d'))
                mt = int(datetime.date.today().strftime('%m'))
                d = datetime.date(yr, mt, dt)
                current_date = d.strftime('%Y%m%d')  # 20220704
                order_number = current_date + str(order.id)
                order.order_number = order_number
                order.save()
                context = {
                    'order': order,
                    'cart_items': cart_items,
                    'total': total,
                    'tax': tax,
                    'grand_total': grand_total
                }
                return render(request, 'orders/payments.html', context)
            else:
                return HttpResponse("hi")
    else:
        redirect('checkout')


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])
    payment = Payment.objects.create(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status']
    )
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()
    # Move the cart items to the Order Product table
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        # color = ""
        # size = ""
        # for variation in item.variations.all():
        #     if variation.variation_category == 'color':
        #         color = variation.variation_value
        #     else:
        #         size = variation.variation_value
        order_product = OrderProduct.objects.create(
            order=order,
            payment=payment,
            user=request.user,
            product=item.product,
            quantity=item.quantity,
            product_price=item.product.price,
            is_ordered=True,
        )
        order_product.save()
        # we need to save the object first in order to add the many to many fields variation
        order_product_variations = list(item.variations.all())
        order_product.variation.add(*order_product_variations)
        order_product.save()
        # Reduce the quantity of the sold products
        item.product.stock -= item.quantity
        item.product.save()
        # Clear the user cart
        item.delete()
        # Send order received email to costumer
    # mail_subject = 'Thank you for your order'
    # message = render_to_string('orders/order_received_email.html', {
    #     'user': request.user,
    #     'order': order
    # })
    # to_email = request.user.email
    # send_email = EmailMessage(mail_subject, message, to=[to_email])
    # send_email.send()
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id
    }
    # this data will go where it came from i.e the script portion for the payment gateway html page
    return JsonResponse(data)

    # Send order number and transaction id back to sendData method via json response


def order_complete(request):
    orderID = request.GET['order_number']
    transID = request.GET['payment_id']
    try:
        order = Order.objects.get(user=request.user, is_ordered=True, order_number=orderID)
        ordered_products = OrderProduct.objects.filter(order=order, is_ordered=True)
        sub_total = order.order_total - order.tax
        context = {
            'order': order,
            'orderID': orderID,
            'transID': transID,
            'ordered_products': ordered_products,
            'sub_total': sub_total
        }
        return render(request, 'orders/order_complete.html', context)
    except (Order.DoesNotExist, OrderProduct.DoesNotExist):
        return redirect('home')


