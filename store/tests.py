from django.test import TestCase


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
