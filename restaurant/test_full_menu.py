from decimal import Decimal

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse

from .admin import MenuItemVariantInline
from .models import MenuCategory, MenuItem, MenuItemVariant
from .test_menu import menu_photo
from .tests import RestaurantMarkup


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class FullMenuTests(TestCase):
    def setUp(self):
        self.category = MenuCategory.objects.create(name="Test sides", slug="test-sides", layout="compact", display_order=8)
        self.item = MenuItem.objects.create(category=self.category, name="Test fries", slug="test-fries", description="Crispy golden fries.", mrp_price="15.00", discount_price="14.00")

    def variant(self, label="S", **kwargs):
        return MenuItemVariant.objects.create(item=self.item, label=label, price=Decimal("5.99"), **kwargs)

    def test_route_shared_navigation_and_home_preview(self):
        url = reverse("restaurant:restaurant_menu")
        self.assertEqual(url, "/menu/")
        for page in ["/", url]:
            response = self.client.get(page)
            self.assertEqual(response.status_code, 200)
            markup = RestaurantMarkup()
            markup.feed(response.content.decode())
            self.assertGreaterEqual(markup.anchors.count(url), 3)
            self.assertContains(response, 'id="restaurant-navigation"')
            self.assertContains(response, 'class="restaurant-footer-brand"')
        home = self.client.get("/")
        self.assertContains(home, 'id="restaurant-menu"')
        self.assertContains(home, 'href="/menu/">Explore Menu')
        self.assertEqual(self.client.head(url).status_code, 200)
        self.assertEqual(self.client.post(url).status_code, 405)

    def test_dynamic_categories_ordering_and_hidden_category(self):
        later = MenuCategory.objects.create(name="Desserts", slug="desserts", display_order=9)
        hidden = MenuCategory.objects.create(name="Secret menu", slug="secret", is_active=False)
        MenuItem.objects.create(category=hidden, name="Secret dish", slug="secret-dish", mrp_price=10)
        MenuItem.objects.create(category=self.category, name="First dish", slug="first-dish", mrp_price=10, display_order=0)
        self.item.display_order = 10
        self.item.save()
        response = self.client.get("/menu/")
        self.assertContains(response, 'href="#category-desserts"')
        self.assertContains(response, 'id="category-desserts"')
        self.assertContains(response, "New dishes are coming soon.")
        self.assertNotContains(response, "Secret menu")
        self.assertNotContains(response, "Secret dish")
        content = response.content.decode()
        self.assertLess(content.index('id="category-test-sides"'), content.index('id="category-desserts"'))
        self.assertLess(content.index('id="menu-item-first-dish"'), content.index('id="menu-item-test-fries"'))
        later.is_active = False
        later.save()
        self.assertNotContains(self.client.get("/menu/"), 'category-desserts')

    def test_single_discount_prices_and_missing_images(self):
        response = self.client.get("/menu/")
        self.assertContains(response, '<del aria-label="Original MRP">$15.00</del>', html=True)
        self.assertContains(response, '<strong aria-label="Discount price">$14.00</strong>', html=True)
        self.assertContains(response, "full-menu-no-image")
        self.assertNotContains(response, 'src=""')
        self.item.discount_price = None
        self.item.save()
        self.assertContains(self.client.get("/menu/"), '<strong aria-label="MRP">$15.00</strong>', html=True)

    def test_variants_replace_base_prices_on_both_pages_and_are_ordered(self):
        MenuItemVariant.objects.create(item=self.item, label="L", price="9.99", display_order=3)
        MenuItemVariant.objects.create(item=self.item, label="S", price="5.99", display_order=1)
        MenuItemVariant.objects.create(item=self.item, label="M", price="7.99", discount_price="6.99", display_order=2, is_available=False)
        for page in ["/", "/menu/"]:
            response = self.client.get(page)
            self.assertNotContains(response, "$15.00")
            self.assertNotContains(response, "$14.00")
            for price in ["5.99", "7.99", "6.99", "9.99"]:
                self.assertContains(response, "$" + price)
            content = response.content.decode().split('id="menu-item-test-fries"', 1)[1].split("</article>", 1)[0]
            self.assertLess(content.index("$5.99"), content.index("$7.99"))
            self.assertLess(content.index("$7.99"), content.index("$9.99"))
            self.assertContains(response, "menu-variant-unavailable")
        self.assertContains(self.client.get("/"), 'aria-label="Enquire about ordering Test fries"')

    def test_availability_item_overrides_variants_and_all_unavailable(self):
        variant = self.variant(is_available=False)
        for page in ["/", "/menu/"]:
            response = self.client.get(page)
            self.assertContains(response, "Unavailable")
            self.assertNotContains(response, 'aria-label="Enquire about ordering Test fries"')
        variant.is_available = True
        variant.save()
        self.item.is_available = False
        self.item.save()
        self.assertContains(self.client.get("/menu/"), "menu-variant-unavailable")
        self.assertNotContains(self.client.get("/"), 'aria-label="Enquire about ordering Test fries"')

    def test_constant_queries_with_many_categories_items_and_variants(self):
        for number in range(8):
            category = MenuCategory.objects.create(name=f"Category {number}", slug=f"category-{number}")
            for index in range(3):
                item = MenuItem.objects.create(category=category, name=f"Dish {number}-{index}", slug=f"dish-{number}-{index}", mrp_price=5)
                MenuItemVariant.objects.create(item=item, label="S", price=4)
        for page in ["/", "/menu/"]:
            with self.assertNumQueries(3):
                response = self.client.get(page)
                self.assertEqual(response.status_code, 200)

    def test_variant_validation_and_database_constraints(self):
        for price, discount in [("0", None), ("-1", None), ("5", "0"), ("5", "5"), ("5", "6"), ("5", "1.001")]:
            variant = MenuItemVariant(item=self.item, label="S", price=Decimal(price), discount_price=Decimal(discount) if discount else None)
            with self.subTest(price=price, discount=discount), self.assertRaises(ValidationError):
                variant.full_clean()
        for price, discount in [(0, None), (5, 0), (5, 5), (5, 6)]:
            with self.subTest(price=price, discount=discount), self.assertRaises(IntegrityError), transaction.atomic():
                MenuItemVariant.objects.create(item=self.item, label="S", price=price, discount_price=discount)
        self.variant()
        with self.assertRaises(ValidationError):
            MenuItemVariant(item=self.item, label="S", price=5).full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.variant()
        with self.assertRaises(ValidationError):
            MenuItemVariant(item=self.item, label=" ", price=5).full_clean()

    def test_admin_inline_and_staff_permission_boundaries(self):
        self.assertIn(MenuItemVariantInline, admin.site._registry[MenuItem].inlines)
        staff = get_user_model().objects.create_user(username="variant-editor", is_staff=True)
        staff.user_permissions.add(*Permission.objects.filter(content_type__app_label="restaurant", codename__in=[
            "view_menuitem", "change_menuitem", "view_menuitemvariant", "add_menuitemvariant", "change_menuitemvariant", "delete_menuitemvariant"
        ]))
        self.client.force_login(staff)
        url = reverse("admin:restaurant_menuitem_change", args=[self.item.pk])
        self.assertContains(self.client.get(url), 'name="variants-TOTAL_FORMS"')
        data = dict(name=self.item.name, slug=self.item.slug, category=self.category.pk, description=self.item.description,
                    mrp_price="15.00", discount_price="14.00", display_order=0, is_available="on", image=menu_photo(),
                    **{"variants-TOTAL_FORMS": "1", "variants-INITIAL_FORMS": "0", "variants-MIN_NUM_FORMS": "0", "variants-MAX_NUM_FORMS": "1000",
                       "variants-0-label": "S", "variants-0-price": "5.99", "variants-0-display_order": "2", "variants-0-is_available": "on"})
        self.assertEqual(self.client.post(url, data).status_code, 302)
        variant = self.item.variants.get()
        self.assertEqual(variant.price, Decimal("5.99"))
        data.pop("image")
        data.update({"variants-INITIAL_FORMS": "1", "variants-0-id": variant.pk, "variants-0-price": "7.99", "variants-0-display_order": "1"})
        data.pop("variants-0-is_available")
        self.assertEqual(self.client.post(url, data).status_code, 302)
        variant.refresh_from_db()
        self.assertFalse(variant.is_available)
        self.assertEqual(variant.display_order, 1)
        data["variants-0-discount_price"] = "8.00"
        self.assertEqual(self.client.post(url, data).status_code, 200)
        variant.refresh_from_db()
        self.assertIsNone(variant.discount_price)
        data["variants-0-discount_price"] = ""
        data["variants-0-DELETE"] = "on"
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertFalse(self.item.variants.exists())
        staff.user_permissions.remove(*Permission.objects.filter(content_type__model="menuitemvariant"))
        self.assertNotContains(self.client.get(url), 'name="variants-TOTAL_FORMS"')

    def test_category_photo_description_empty_menu_and_unavailable_single_item(self):
        self.category.image = menu_photo("category.png")
        self.category.description = "Choose a freshly made side."
        self.category.save()
        self.item.is_available = False
        self.item.save()
        response = self.client.get("/menu/")
        self.assertContains(response, self.category.image.url)
        self.assertContains(response, self.category.description)
        self.assertContains(response, "menu-layout-compact")
        self.assertContains(response, '<span class="menu-unavailable-label">Unavailable</span>', html=True)
        self.assertContains(response, "Crispy golden fries.")
        MenuCategory.objects.update(is_active=False)
        with self.assertNumQueries(1):
            response = self.client.get("/menu/")
        self.assertContains(response, "Our menu is being updated.")
        self.assertNotContains(response, 'class="menu-categories"')

    def test_variant_deletion_restores_base_price_and_item_delete_cascades(self):
        self.variant()
        self.assertNotContains(self.client.get("/menu/"), "$14.00")
        self.item.variants.all().delete()
        self.assertContains(self.client.get("/menu/"), "$14.00")
        self.variant()
        self.item.delete()
        self.assertFalse(MenuItemVariant.objects.exists())

    def test_home_preview_limits_categories_and_dishes_without_limiting_full_menu(self):
        MenuCategory.objects.update(is_active=False)
        expected = []
        for index in range(5):
            category = MenuCategory.objects.create(name=f"Preview {index}", slug=f"preview-{index}", display_order=index)
            MenuItem.objects.create(category=category, name="Later dish", slug=f"later-{index}", mrp_price=7, display_order=2)
            first = MenuItem.objects.create(category=category, name="First dish", slug=f"first-{index}", mrp_price=6, display_order=1)
            if index < 4:
                expected.append(first.pk)
        with self.assertNumQueries(3):
            response = self.client.get("/")
        categories = response.context["menu_categories"]
        self.assertEqual([item.pk for category in categories for item in category.preview_items], expected)
        markup = RestaurantMarkup()
        markup.feed(response.content.decode())
        self.assertEqual([value for value in markup.identifiers if value.startswith("menu-item-")],
                         [f"menu-item-first-{index}" for index in range(4)])
        self.assertNotContains(response, "Later dish")
        full = self.client.get("/menu/")
        for index in range(5):
            self.assertContains(full, f'id="menu-item-first-{index}"')
            self.assertContains(full, f'id="menu-item-later-{index}"')

    def test_shared_header_home_link_and_current_page(self):
        for path in ["/", "/menu/"]:
            response = self.client.get(path)
            nav = response.content.decode().split('<nav id="restaurant-navigation"', 1)[1].split("</nav>", 1)[0]
            self.assertIn('>Home</a>', nav)
            self.assertIn('href="/"', nav)
            if path == "/":
                self.assertIn('href="/" aria-current="page">Home</a>', nav)
            else:
                self.assertNotIn('href="/" aria-current="page">Home</a>', nav)
