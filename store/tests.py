import json
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from razorpay.errors import SignatureVerificationError


class HomePageTests(TestCase):
    def test_homepage_renders_all_hero_slides(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        for image in ("redheel.jpg", "blueheel.jpg", "kid1.jpg", "menc.jpg"):
            self.assertContains(response, f"images/{image}")
        self.assertContains(response, 'class="hero-slide active"', count=1)
        self.assertContains(response, 'class="hero-slide"', count=3)

    def test_category_navigation_includes_mega_menus(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        for category, url in (
            ("Womens", "/womens/"),
            ("Mens", "/mens/"),
            ("Kids", "/kids/"),
        ):
            with self.subTest(category=category):
                self.assertContains(response, f'href="{url}"')
        self.assertContains(response, "Girls Sandals")
        self.assertContains(response, "Strap Sandals")
        self.assertContains(response, "Strappy")

    def test_home_cart_and_hero_links_open_their_destinations(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/cart/" class="cart-link"')
        for category in ("womens", "kids", "mens"):
            with self.subTest(category=category):
                self.assertContains(
                    response,
                    f'href="/{category}/#products-grid" class="shop-now-btn"',
                )
        self.assertContains(response, 'href="#categories-preview" class="view-all-btn"')

    def test_about_cart_link_opens_cart_page(self):
        response = self.client.get("/about/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/cart/" class="cart-link"')

    def test_shared_navigation_has_working_links_and_one_hidden_offers_menu(self):
        for path in ("/cart/", "/login/", "/checkout/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'href="/cart/" class="cart-link"')
                self.assertContains(response, 'href="/login/"')
                self.assertEqual(response.content.count(b'class="offers-menu-box"'), 1)
                self.assertEqual(response.content.count(b'id="offers-menu"'), 1)

    def test_category_view_all_links_target_product_grids(self):
        for category in ("mens", "womens", "kids"):
            with self.subTest(category=category):
                response = self.client.get(f"/{category}/")

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'id="products-grid"')
                self.assertContains(response, 'href="#products-grid" class="view-all-pill-btn"')

    def test_dynamic_footer_is_shared_across_pages(self):
        for path in ("/", "/about/", "/womens/", "/mens/", "/kids/"):
            with self.subTest(path=path):
                response = self.client.get(path)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'id="footer-section"', count=1)
                self.assertContains(response, 'id="policy-modal"', count=1)
                self.assertContains(response, 'action="/subscribe/"')
                self.assertContains(response, "04633-222333")

    def test_newsletter_submission_shows_success_message(self):
        response = self.client.post(
            "/subscribe/",
            {"email": "shopper@example.com"},
            HTTP_REFERER="/about/",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thank you for subscribing with shopper@example.com")


class CartPageTests(TestCase):
    def test_cart_page_renders_successfully(self):
        response = self.client.get("/cart/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'const defaultProductImage = "/static/images/mens/prod1.png";')


class CheckoutPageTests(TestCase):
    def test_checkout_page_renders_payment_scripts_and_options(self):
        response = self.client.get("/checkout/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<script src="https://checkout.razorpay.com/v1/checkout.js"></script>')
        self.assertContains(response, 'id="razorpay-radio"')
        self.assertEqual(response.content.count(b"function handleOrderSubmission(event)"), 1)
        self.assertContains(response, '"method": "card"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    @override_settings(RAZORPAY_KEY_ID=None, RAZORPAY_KEY_SECRET=None)
    def test_checkout_disables_card_payment_when_gateway_is_not_configured(self):
        response = self.client.get("/checkout/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Card payments are not configured")
        self.assertContains(response, 'id="razorpay-radio"')
        self.assertContains(response, 'value="RAZORPAY"')
        self.assertContains(response, "disabled")


class PaymentFlowTests(TestCase):
    order_data = {
        "amount": 2799,
        "customer": {
            "name": "Shopper Example",
            "email": "shopper@example.com",
            "phone": "9876543210",
            "address": "1 Main Street",
            "city": "Tenkasi",
        },
        "items": [{
            "brand": "Comfy Steps",
            "title": "Harlan Mens Tan Boat Shoe",
            "price": 2799,
            "quantity": 1,
            "image": "/static/images/mens/prod1.png",
        }],
    }

    def test_cod_order_persists_order_number_and_tracking_details(self):
        response = self.client.post(
            "/complete-cod-order/",
            data=json.dumps(self.order_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redirect_url"], "/order-success/")
        order = self.client.session["last_order"]
        self.assertRegex(order["orderNo"], r"^BH[0-9A-F]{8}$")
        self.assertEqual(order["paymentMode"], "Cash on Delivery")
        self.assertEqual(order["amount"], 2799)

        success_response = self.client.get("/order-success/")
        tracking_response = self.client.get("/track-order/")
        self.assertContains(success_response, order["orderNo"])
        self.assertContains(success_response, order["paymentMode"])
        self.assertContains(tracking_response, order["orderNo"])
        self.assertContains(tracking_response, "Preparing your order")
        self.assertContains(tracking_response, "Shipment tracking will be available after dispatch.")
        self.assertNotContains(tracking_response, "May 21,2025")

    @override_settings(RAZORPAY_KEY_ID="rzp_test_example", RAZORPAY_KEY_SECRET="test_secret")
    @patch("store.views.razorpay.Client")
    def test_card_payment_is_verified_and_saved_to_session(self, client_factory):
        gateway = Mock()
        gateway.order.create.return_value = {"id": "order_test_123"}
        client_factory.return_value = gateway

        create_response = self.client.post(
            "/create-razorpay-order/",
            data=json.dumps(self.order_data),
            content_type="application/json",
        )

        self.assertEqual(create_response.status_code, 200)
        gateway.order.create.assert_called_once_with(
            data={
                "amount": 279900,
                "currency": "INR",
                "receipt": gateway.order.create.call_args.kwargs["data"]["receipt"],
            }
        )
        self.assertNotIn("payment_capture", gateway.order.create.call_args.kwargs["data"])

        payment_data = {
            "razorpay_order_id": "order_test_123",
            "razorpay_payment_id": "pay_test_456",
            "razorpay_signature": "valid-signature",
        }
        verify_response = self.client.post(
            "/verify-payment/",
            data=json.dumps(payment_data),
            content_type="application/json",
        )

        self.assertEqual(verify_response.status_code, 200)
        self.assertEqual(verify_response.json()["redirect_url"], "/order-success/")
        gateway.utility.verify_payment_signature.assert_called_once_with(payment_data)
        order = self.client.session["last_order"]
        self.assertEqual(order["paymentMode"], "Card payment (Razorpay)")
        self.assertEqual(order["transactionId"], "pay_test_456")
        self.assertContains(self.client.get("/order-success/"), "pay_test_456")
        self.assertContains(self.client.get("/track-order/"), "pay_test_456")

    @override_settings(RAZORPAY_KEY_ID=None, RAZORPAY_KEY_SECRET=None)
    def test_card_order_returns_actionable_error_when_keys_are_missing(self):
        response = self.client.post(
            "/create-razorpay-order/",
            data=json.dumps(self.order_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn("not configured", response.json()["message"])

    def test_payment_verification_rejects_mismatched_order(self):
        session = self.client.session
        session["pending_payment"] = {"order_id": "order_expected"}
        session.save()

        response = self.client.post(
            "/verify-payment/",
            data=json.dumps({
                "razorpay_order_id": "order_other",
                "razorpay_payment_id": "pay_test",
                "razorpay_signature": "signature",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("does not match", response.json()["message"])

    @override_settings(RAZORPAY_KEY_ID="rzp_test_example", RAZORPAY_KEY_SECRET="test_secret")
    @patch("store.views.razorpay.Client")
    def test_invalid_signature_does_not_confirm_order(self, client_factory):
        gateway = Mock()
        gateway.utility.verify_payment_signature.side_effect = SignatureVerificationError()
        client_factory.return_value = gateway
        session = self.client.session
        session["pending_payment"] = {
            "order_id": "order_test_123",
            "amount": 2799,
            "customer": self.order_data["customer"],
            "items": self.order_data["items"],
        }
        session.save()

        response = self.client.post(
            "/verify-payment/",
            data=json.dumps({
                "razorpay_order_id": "order_test_123",
                "razorpay_payment_id": "pay_invalid",
                "razorpay_signature": "invalid-signature",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("last_order", self.client.session)


class OrderPageTests(TestCase):
    def test_order_pages_show_checkout_prompt_without_confirmed_order(self):
        success_response = self.client.get("/order-success/")
        tracking_response = self.client.get("/track-order/")

        self.assertEqual(success_response.status_code, 200)
        self.assertContains(success_response, "No confirmed order found")

        self.assertEqual(tracking_response.status_code, 200)
        self.assertContains(tracking_response, "No order to track yet")
