from django.shortcuts import render, redirect, HttpResponse
from carts.models import CartItem
from .forms import Order, OrderForm
import datetime
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
                tax = (2 * total)/100
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
                current_date = d.strftime('%Y%m%d') # 20220704
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
    return render(request, 'orders/payments.html')




