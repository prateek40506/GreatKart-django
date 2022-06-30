from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart, name='cart'),
    path('add-cart/<int:product_id>/', views.add_cart, name='add_cart'),
    path('decrement_qty/<int:item_id>/', views.decrement_qty, name='decrement_qty'),
    path('increment-qty/<int:item_id>/', views.increment_qty, name='increment_qty'),
    path('delete-cart/<int:item_id>/', views.delete_cart, name='delete_cart')
]
