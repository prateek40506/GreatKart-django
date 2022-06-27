from django.shortcuts import render, get_object_or_404, HttpResponse
from store.models import Product
from category.models import Category


# Create your views here.


def store(request, category_slug=None):
    if category_slug is not None:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.all().filter(category=category, is_available=True)
    else:
        products = Product.objects.all().filter(is_available=True)
    product_count = len(products)
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'products': products,
        'product_count': product_count
    }
    return render(request, 'store/store.html', context)


def product_details(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
    except Exception as e:
        raise e
    context = {
        'product_details': single_product
    }
    return render(request, 'store/product-detail.html', context)
