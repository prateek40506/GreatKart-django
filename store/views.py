from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating, ProductGallery
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import HttpResponse
from django.db.models.query_utils import Q
from .forms import ReviewForm
from django.contrib import messages
from .models import Variation
from orders.models import OrderProduct


# Create your views here.


def store(request, category_slug=None):
    products_display = []
    products_per_page = 1
    if request.method == 'POST':
        size = request.POST['size']
        min_price = int(request.POST['min_price'])
        max_price = int(request.POST['max_price'])
        variations = None
        if category_slug is not None:
            category = get_object_or_404(Category, slug=category_slug)
            products_exist = Variation.objects.filter(product__category=category, variation_category='size', variation_value=size).exists()
            if products_exist:
                variations = Variation.objects.filter(product__category=category, variation_category='size', variation_value=size)
        else:
            products_exist = Variation.objects.filter(variation_category='size', variation_value=size).exists()
            if products_exist:
                variations = Variation.objects.filter(variation_category='size', variation_value=size)
        if variations:
            for variation in variations:
                if min_price <= variation.product.price <= max_price:
                    products_display.append(variation.product)
    else:
        if category_slug is not None:
            category = get_object_or_404(Category, slug=category_slug)
            products_exist = Product.objects.filter(category=category).exists()
            if products_exist:
                products_display = Product.objects.filter(category=category)
        else:
            products_display = Product.objects.all().filter(is_available=True).order_by('id')
            products_per_page = 3
    categories = Category.objects.all()
    paginator = Paginator(products_display, products_per_page)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    context = {
        'categories': categories,
        'products': paged_products,
        'product_count': len(products_display),
        'category_slug': category_slug
    }
    return render(request, 'store/store.html', context)


def product_details(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e
    if request.user.is_authenticated:
        is_logged_in = True
        is_ordered_product = OrderProduct.objects.filter(user=request.user, product=single_product).exists()
    else:
        is_logged_in = False
        is_ordered_product = False
    is_product_reviews = ReviewRating.objects.filter(product=single_product)
    if is_product_reviews:
        product_reviews = ReviewRating.objects.filter(product=single_product, status=True)
    else:
        product_reviews = None
    product_gallery = ProductGallery.objects.filter(product=single_product)
    context = {
        'product_details': single_product,
        'in_cart': in_cart,
        'is_ordered_product': is_ordered_product,
        'is_logged_in': is_logged_in,
        'product_reviews': product_reviews,
        'product_gallery': product_gallery
    }
    return render(request, 'store/product-detail.html', context)


def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
    context = {
        'products': products,
        'product_count': product_count
    }
    return render(request, 'store/store.html', context)


def submit_review(request, product_id):
    # obtains the url of the previous page from where we came to this page
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user=request.user, product__id=product_id)
            # instance is simply checking for the past created reviews otherwise it will always create a new review, it should update the review incase the review is added by the same person for the same product
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                product = Product.objects.get(id=product_id)
                data = ReviewRating.objects.create(
                    user=request.user,
                    product=product,
                    subject=form.cleaned_data['subject'],
                    review=form.cleaned_data['review'],
                    rating=form.cleaned_data['rating'],
                    ip=request.META.get('REMOTE_ADDR'),
                )
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)
