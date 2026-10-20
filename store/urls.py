
from django.urls import path  
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login_register_view, name='login'),
    path('womens/', views.womens_view, name='womens'),
    path('mens/', views.mens_view, name='mens'),     
    path('kids/', views.kids_view, name='kids'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('order-success/', views.order_success_view, name='order_success'),
    path('track-order/', views.track_order_view, name='track_order'),
    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
]
