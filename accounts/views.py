from django.shortcuts import render, HttpResponse, redirect
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from carts.models import Cart, CartItem
from orders.models import Order, OrderProduct
from carts.views import _cart_id
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
# Create your views here.
# verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
import requests


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            username = email.split('@')[0]
            password = form.cleaned_data['password']
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email,
                                               username=username, password=password)
            user.phone_number = phone_number
            user.save()
            # create user profile
            user_profile = UserProfile()
            user_profile.user = user
            user_profile.profile_picture = 'default/default_profile.png'
            user_profile.save()

            # USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            # messages.success(request, 'Thank you for registering with us. We have sent you a verification email to your registered email address. Please verify it.')
            return redirect('/accounts/login/?command=verification&email=' + email)
    else:
        form = RegistrationForm()
    context = {
        'form': form
    }
    return render(request, 'accounts/register.html', context)


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(email=email, password=password)
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)
                    cart_item_variations = []
                    cart_item_id = []
                    for item in cart_item:
                        existing_variations = list(item.variations.all())
                        cart_item_id.append(item.id)
                        cart_item_variations.append(existing_variations)
                    is_user_item_exists = CartItem.objects.filter(user=user).exists()
                    if is_user_item_exists:
                        user_item = CartItem.objects.filter(user=user)
                    else:
                        cart_item = CartItem.objects.filter(cart=cart)
                        for item in cart_item:
                            item.user = user
                            item.save()
                    user_item_variations = []
                    user_item_id = []
                    for item in user_item:
                        existing_variations = list(item.variations.all())
                        user_item_id.append(item.id)
                        user_item_variations.append(existing_variations)
                    for variation in cart_item_variations:
                        if variation in user_item_variations:
                            cart_index = cart_item_variations.index(variation)
                            cart_id = cart_item_id[cart_index]
                            user_cart_index = user_item_variations.index(variation)
                            user_cart_id = user_item_id[user_cart_index]
                            user_cart_object = CartItem.objects.get(id=user_cart_id)
                            cart_object = CartItem.objects.get(id=cart_id)
                            user_cart_object.quantity = user_cart_object.quantity + cart_object.quantity
                            user_cart_object.save()
                            cart_object.delete()
                        else:
                            cart_index = cart_item_variations.index(variation)
                            cart_id = cart_item_id[cart_index]
                            cart_object = CartItem.objects.get(id=cart_id)
                            cart_object.user = user
                            cart_object.save()
            except:
                pass
            auth.login(request, user)
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                print('query -->', query)
                # next=/cart/checkout
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    next_page = params['next']
                    return redirect(next_page)
                return redirect(query.split('=')[1])
            except:
                messages.success(request, 'You are now logged in.')
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')
    else:
        return render(request, 'accounts/login.html')


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out.')
    return redirect('login')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations, Your account is activated.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid Activation Link')
        return redirect('register')


@login_required(login_url='login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user=request.user, is_ordered=True)
    orders_count = orders.count()
    user_profile = UserProfile.objects.get(user=request.user)
    context = {
        'orders_count': orders_count,
        'user_profile': user_profile
    }
    return render(request, 'accounts/dashboard.html', context)


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        is_user_registered = Account.objects.filter(email=email).exists()
        if is_user_registered:
            # return redirect('/accounts/updatePassword/'+email)
            user = Account.objects.get(email__exact=email)
            # RESET PASSWORD EMAIL
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
                'email': email
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['createPassword']
        confirm_password = request.POST['confirmPassword']
        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successfully.')
            return redirect('login')
        else:
            messages.error(request, 'Passwords do not match')
            return redirect('resetPassword')
    return render(request, 'accounts/resetPassword.html')


def reset_password_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        return render(request, 'accounts/resetPassword.html')
    else:
        messages.error(request, 'Password recovery email has expired.')
        return redirect('forgotPassword')


@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.order_by('-created_at').filter(user=request.user, is_ordered=True)
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/my_orders.html', context)


@login_required(login_url='login')
def edit_profile(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if user_form.is_valid() and profile_form.is_valid():
            # print(profile_form.cleaned_data['profile_picture'].url)
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'user_profile': user_profile
        }
        return render(request, 'accounts/edit_profile.html', context)


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        user = Account.objects.get(username__exact=request.user.username)
        if new_password == confirm_password:
            # as passwords are hashed
            # check_password and set_password are built in django functions
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password updated successfully')
                return redirect('change_password')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('change_password')
        else:
            messages.error(request, 'password does not match')
            return redirect('change_password')
    return render(request, 'accounts/change_password.html')


@login_required(login_url='login')
def order_detail(request, order_id):
    order_details = OrderProduct.objects.filter(order__order_number=order_id, user=request.user)
    order = Order.objects.get(order_number=order_id)
    sub_total = 0
    for order_product in order_details:
        sub_total += (order_product.product_price * order_product.quantity)
    context = {
        'order_details': order_details,
        'order': order,
        'sub_total': sub_total
    }
    return render(request, 'accounts/order_detail.html', context)
