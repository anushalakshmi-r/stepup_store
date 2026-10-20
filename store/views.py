
from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        # You can handle form saving here later
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')
    return render(request, 'contact.html')

from django.shortcuts import render

def login_register_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'login':
            email = request.POST.get('email')
            password = request.POST.get('password')
            # Ikkada login authentication logic rayavachu
        elif action == 'register':
            email = request.POST.get('email')
            password = request.POST.get('password')
            terms = request.POST.get('terms')
            # Ikkada new user registration logic rayavachu
            
    return render(request, 'login.html')   


def womens_view(request):
    return render(request, 'womens.html')     

def mens_view(request):
    return render(request, 'mens.html')

def kids_view(request):
    return render(request, 'kids.html')

def cart_view(request):
    return render(request, 'cart.html')

def checkout_view(request):
    return render(request, 'checkout.html')

def order_success_view(request):
    return render(request, 'order_success.html')

def track_order_view(request):
    return render(request, 'track_order.html')

from django.shortcuts import render, redirect
from django.contrib import messages


def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            
            messages.success(request, f"Thank you for subscribing with {email}! Check your inbox for exclusive offers.")
        else:
            messages.error(request, "Please enter a valid email address.")
    

    return redirect(request.META.get('HTTP_REFERER', 'home'))