
import json
import logging
from uuid import uuid4

import razorpay
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone


logger = logging.getLogger(__name__)


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

def order_success_view(request):
    return render(
        request,
        'order_success.html',
        {'order': request.session.get('last_order')},
    )


def track_order_view(request):
    return render(
        request,
        'track_order.html',
        {'order': request.session.get('last_order')},
    )


def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            
            messages.success(request, f"Thank you for subscribing with {email}! Check your inbox for exclusive offers.")
        else:
            messages.error(request, "Please enter a valid email address.")
    

    return redirect(request.META.get('HTTP_REFERER', 'home'))



def checkout_view(request):
    key_id = settings.RAZORPAY_KEY_ID
    razorpay_enabled = bool(key_id and settings.RAZORPAY_KEY_SECRET)
    context = {
        'razorpay_key_id': key_id,
        'razorpay_enabled': razorpay_enabled,
        'razorpay_test_mode': bool(key_id and key_id.startswith('rzp_test_')),
    }
    return render(request, 'checkout.html', context)


def _read_json_body(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _valid_amount(amount):
    return isinstance(amount, int) and not isinstance(amount, bool) and amount > 0


def _customer_and_items(data):
    customer = data.get('customer')
    items = data.get('items')
    if not isinstance(customer, dict) or not isinstance(items, list) or not items:
        return None
    return customer, items


def _new_order(amount, customer, items, payment_mode, transaction_id):
    primary_item = items[0] if isinstance(items[0], dict) else {}
    now = timezone.localtime()
    return {
        'orderNo': f'BH{uuid4().hex[:8].upper()}',
        'amount': amount,
        'item': primary_item,
        'items': items,
        'customerName': str(customer.get('name', '')),
        'city': str(customer.get('city', '')),
        'address': str(customer.get('address', '')),
        'paymentMode': payment_mode,
        'transactionId': transaction_id,
        'status': 'Order placed',
        'orderedAt': now.strftime('%B %d, %Y at %I:%M %p'),
    }


def _payment_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return None
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def complete_cod_order(request):
    if request.method != 'POST':
        return JsonResponse(
            {'status': 'error', 'message': 'Invalid request method.'},
            status=405,
        )

    data = _read_json_body(request)
    if data is None or not _valid_amount(data.get('amount')):
        return JsonResponse(
            {'status': 'error', 'message': 'The order amount is invalid.'},
            status=400,
        )
    customer_and_items = _customer_and_items(data)
    if customer_and_items is None:
        return JsonResponse(
            {'status': 'error', 'message': 'The order details are missing.'},
            status=400,
        )

    customer, items = customer_and_items
    request.session['last_order'] = _new_order(
        data['amount'],
        customer,
        items,
        'Cash on Delivery',
        f'COD-{uuid4().hex[:12].upper()}',
    )
    request.session.pop('pending_payment', None)
    return JsonResponse(
        {'status': 'success', 'redirect_url': reverse('order_success')}
    )


def create_razorpay_order(request):
    if request.method != 'POST':
        return JsonResponse(
            {'status': 'error', 'message': 'Invalid request method.'},
            status=405,
        )

    data = _read_json_body(request)
    if data is None or not _valid_amount(data.get('amount')):
        return JsonResponse(
            {'status': 'error', 'message': 'The order amount is invalid.'},
            status=400,
        )
    customer_and_items = _customer_and_items(data)
    if customer_and_items is None:
        return JsonResponse(
            {'status': 'error', 'message': 'The order details are missing.'},
            status=400,
        )

    client = _payment_client()
    if client is None:
        return JsonResponse(
            {
                'status': 'error',
                'message': 'Card payments are not configured. Please choose Cash on Delivery.',
            },
            status=503,
        )

    amount_in_paise = data['amount'] * 100
    try:
        order = client.order.create(
            data={
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': f'stepup-{uuid4().hex[:24]}',
            }
        )
    except (
        razorpay.errors.BadRequestError,
        razorpay.errors.GatewayError,
        razorpay.errors.ServerError,
    ):
        logger.exception('Razorpay order creation failed')
        return JsonResponse(
            {
                'status': 'error',
                'message': 'Razorpay could not start the card payment. Please retry or choose Cash on Delivery.',
            },
            status=502,
        )

    customer, items = customer_and_items
    request.session['pending_payment'] = {
        'order_id': order['id'],
        'amount': data['amount'],
        'customer': customer,
        'items': items,
    }
    return JsonResponse(
        {
            'status': 'success',
            'order_id': order['id'],
            'amount': amount_in_paise,
        }
    )


def verify_payment(request):
    if request.method != 'POST':
        return JsonResponse(
            {'status': 'error', 'message': 'Invalid request method.'},
            status=405,
        )

    data = _read_json_body(request)
    required_fields = (
        'razorpay_order_id',
        'razorpay_payment_id',
        'razorpay_signature',
    )
    if data is None or any(not data.get(field) for field in required_fields):
        return JsonResponse(
            {'status': 'error', 'message': 'The payment details are incomplete.'},
            status=400,
        )

    pending_payment = request.session.get('pending_payment')
    if not pending_payment or data['razorpay_order_id'] != pending_payment['order_id']:
        return JsonResponse(
            {'status': 'error', 'message': 'This payment does not match the current order.'},
            status=400,
        )

    client = _payment_client()
    if client is None:
        return JsonResponse(
            {'status': 'error', 'message': 'Card payments are not configured.'},
            status=503,
        )

    try:
        client.utility.verify_payment_signature(
            {
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature'],
            }
        )
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse(
            {'status': 'error', 'message': 'Payment verification failed. Contact support before retrying.'},
            status=400,
        )
    except (
        razorpay.errors.BadRequestError,
        razorpay.errors.GatewayError,
        razorpay.errors.ServerError,
    ):
        logger.exception('Razorpay payment verification failed')
        return JsonResponse(
            {'status': 'error', 'message': 'Payment verification is temporarily unavailable. Please contact support.'},
            status=502,
        )

    request.session['last_order'] = _new_order(
        pending_payment['amount'],
        pending_payment['customer'],
        pending_payment['items'],
        'Card payment (Razorpay)',
        data['razorpay_payment_id'],
    )
    request.session.pop('pending_payment', None)
    return JsonResponse(
        {'status': 'success', 'redirect_url': reverse('order_success')}
    )