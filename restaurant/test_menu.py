from decimal import Decimal
from io import BytesIO

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import MenuCategory, MenuItem


def menu_photo(name="dish.png"):
    photo = BytesIO()
    Image.new("RGB", (16, 16), "red").save(photo, "PNG")
    return SimpleUploadedFile(name, photo.getvalue(), content_type="image/png")


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class MenuManagementTests(TestCase):
    def setUp(self):
        self.category = MenuCategory.objects.create(name="Sides", slug="sides", display_order=10)

    def new_dish(self, **changes):
        details = dict(category=self.category, name="Grilled side", slug="grilled-side", image=menu_photo(), description="Fresh from the grill.", mrp_price=Decimal("5.00"))
        details.update(changes)
        return MenuItem(**details)

    def test_category_and_dish_creation(self):
        self.category.full_clean()
        dish = self.new_dish(discount_price=Decimal("4.00"))
        dish.full_clean()
        dish.save()
        self.assertEqual(str(dish), "Grilled side")
        self.assertEqual(str(self.category), "Sides")
        self.assertEqual(self.category.items.get(), dish)
        self.assertTrue(dish.image.name.startswith("menu/items/"))
        self.assertIsNotNone(dish.created_at)
        self.assertIsNotNone(dish.updated_at)
        with self.assertRaises(ProtectedError):
            self.category.delete()

    def test_price_validation(self):
        for mrp, discount in [("0", None), ("-1", None), ("5", "0"), ("5", "-1"), ("5", "5"), ("5", "6"), ("5", "1.001")]:
            with self.subTest(mrp=mrp, discount=discount):
                dish = self.new_dish(mrp_price=Decimal(mrp), discount_price=Decimal(discount) if discount is not None else None)
                with self.assertRaises(ValidationError):
                    dish.full_clean()
        self.new_dish().full_clean()
        self.new_dish(discount_price=Decimal("0.01")).full_clean()

    def test_database_rejects_invalid_prices_without_form_validation(self):
        for mrp, discount in [(0, None), (5, 0), (5, 5), (5, 6)]:
            with self.subTest(mrp=mrp, discount=discount), self.assertRaises(IntegrityError), transaction.atomic():
                MenuItem.objects.create(category=self.category, name="Invalid", slug="invalid", image="menu/items/photo.png", mrp_price=mrp, discount_price=discount)

    def test_images_required_and_verified(self):
        for photo in [None, SimpleUploadedFile("fake.png", b"not an image"), menu_photo("dish.svg")]:
            with self.subTest(photo=photo), self.assertRaises(ValidationError):
                self.new_dish(image=photo).full_clean()
        oversized = SimpleUploadedFile("large.png", b"0" * (5 * 1024 * 1024 + 1))
        with self.assertRaises(ValidationError):
            self.new_dish(image=oversized).full_clean()

    def test_active_categories_ordered_without_extra_queries(self):
        dish = self.new_dish()
        dish.save()
        MenuCategory.objects.create(name="Starters", slug="starters", display_order=0)
        hidden = MenuCategory.objects.create(name="Hidden specials", slug="hidden-specials", is_active=False)
        self.new_dish(category=hidden, slug="secret", name="Secret dish").save()
        with self.assertNumQueries(3):
            response = self.client.get("/menu/")
        self.assertContains(response, "Grilled side")
        self.assertNotContains(response, "Hidden specials")
        self.assertNotContains(response, "Secret dish")
        self.assertLess(response.content.index(b'id="category-starters"'), response.content.index(b'id="category-sides"'))
        self.assertEqual(list(response.context["menu_categories"])[-1], self.category)

    def test_prices_availability_ordering_and_refresh(self):
        dish = self.new_dish(discount_price=Decimal("4.00"), display_order=2)
        dish.save()
        self.new_dish(slug="first-side", name="First side", display_order=1).save()
        response = self.client.get("/menu/")
        self.assertContains(response, '<del aria-label="Original MRP">$5.00</del>', html=True)
        self.assertContains(response, '<strong aria-label="Discount price">$4.00</strong>', html=True)
        self.assertNotContains(response, 'class="menu-unavailable-label"')
        self.assertLess(response.content.index(b'id="menu-item-first-side"'), response.content.index(b'id="menu-item-grilled-side"'))
        dish.is_available = False
        dish.name = "Updated side"
        dish.save()
        response = self.client.get("/menu/")
        self.assertContains(response, "Updated side")
        self.assertContains(response, 'class="menu-unavailable-label">Unavailable')
        self.assertNotContains(response, 'aria-label="Enquire about ordering Updated side"')

    def test_category_image_description_and_empty_states(self):
        self.category.image = menu_photo("category.png")
        self.category.description = "Fresh sides for every wrap."
        self.category.full_clean()
        self.category.save()
        response = self.client.get("/menu/")
        self.assertContains(response, self.category.image.url)
        self.assertContains(response, self.category.description)
        self.assertContains(response, "New dishes are coming soon.")
        MenuCategory.objects.update(is_active=False)
        self.assertContains(self.client.get("/menu/"), "Our menu is being updated.")

    def test_seeded_menu(self):
        seeded = MenuCategory.objects.get(slug="shawarmas")
        self.assertEqual(list(seeded.items.values_list("name", "mrp_price")), [
            ("Chicken Shawarma", Decimal("8.99")), ("Beef Shawarma", Decimal("9.99")), ("Mixed Shawarma", Decimal("10.99")),
        ])

    def test_staff_permissions_and_admin_upload(self):
        staff = get_user_model().objects.create_user(username="menu-staff", password="test-password", is_staff=True)
        dish_url = reverse("admin:restaurant_menuitem_changelist")
        add_url = reverse("admin:restaurant_menuitem_add")
        self.assertEqual(self.client.get(dish_url).status_code, 302)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(dish_url).status_code, 403)
        self.assertEqual(self.client.post(add_url, {}).status_code, 403)
        staff.user_permissions.add(*Permission.objects.filter(content_type__app_label="restaurant", codename__in=["view_menuitem", "add_menuitem", "change_menuitem", "view_menucategory"]))
        self.assertEqual(self.client.get(dish_url).status_code, 200)
        data = dict(name="Admin dish", slug="admin-dish", category=self.category.pk, image=menu_photo(), description="Created by staff", mrp_price="6.00", discount_price="4.00", is_available="on", display_order="3", _save="Save")
        self.assertEqual(self.client.post(add_url, data).status_code, 302)
        dish = MenuItem.objects.get(slug="admin-dish")
        self.assertContains(self.client.get("/menu/"), "Admin dish")
        self.assertContains(self.client.get("/menu/"), dish.image.url)
        self.assertEqual(self.client.get(reverse("admin:restaurant_menuitem_delete", args=[dish.pk])).status_code, 403)
        self.assertFalse(staff.is_superuser)
        data.pop("image")
        data.pop("is_available")
        data.update(name="Staff updated dish", discount_price="3.50")
        self.assertEqual(self.client.post(reverse("admin:restaurant_menuitem_change", args=[dish.pk]), data).status_code, 302)
        dish.refresh_from_db()
        self.assertFalse(dish.is_available)
        self.assertEqual(dish.discount_price, Decimal("3.50"))
        response = self.client.get("/menu/")
        self.assertContains(response, "Staff updated dish")
        self.assertNotContains(response, 'aria-label="Enquire about ordering Staff updated dish"')

    def test_category_staff_permissions_and_csrf(self):
        staff = get_user_model().objects.create_user(username="category-editor", is_staff=True)
        staff.user_permissions.add(*Permission.objects.filter(content_type__app_label="restaurant", codename__in=["view_menucategory", "add_menucategory", "change_menucategory"]))
        self.client.force_login(staff)
        data = dict(name="Drinks", slug="drinks", description="Cold drinks", layout="compact", display_order="5", is_active="on", image=menu_photo())
        self.assertEqual(self.client.post(reverse("admin:restaurant_menucategory_add"), data).status_code, 302)
        category = MenuCategory.objects.get(slug="drinks")
        self.assertContains(self.client.get("/menu/"), "Drinks")
        data.pop("image")
        data.pop("is_active")
        self.assertEqual(self.client.post(reverse("admin:restaurant_menucategory_change", args=[category.pk]), data).status_code, 302)
        self.assertNotContains(self.client.get("/menu/"), "Drinks")
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(staff)
        self.assertEqual(csrf_client.post(reverse("admin:restaurant_menucategory_add"), data).status_code, 403)

    def test_duplicate_slugs_and_negative_order_are_invalid(self):
        with self.assertRaises(ValidationError):
            MenuCategory(name="Another", slug="sides").full_clean()
        with self.assertRaises(ValidationError):
            self.new_dish(display_order=-1).full_clean()
        with self.assertRaises(ValidationError):
            self.new_dish(slug="chicken-shawarma").full_clean()

    def test_admin_rejects_invalid_price_and_image(self):
        staff = get_user_model().objects.create_user(username="menu-editor", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="add_menuitem"))
        self.client.force_login(staff)
        data = dict(name="Bad dish", slug="bad-dish", category=self.category.pk, description="Bad price", mrp_price="6.00", discount_price="7.00", display_order="0", image=menu_photo())
        response = self.client.post(reverse("admin:restaurant_menuitem_add"), data)
        self.assertContains(response, "Discount price must be greater than zero and lower than MRP.")
        self.assertFalse(MenuItem.objects.filter(slug="bad-dish").exists())
        data.update(discount_price="", image=SimpleUploadedFile("fake.png", b"invalid"))
        response = self.client.post(reverse("admin:restaurant_menuitem_add"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MenuItem.objects.filter(slug="bad-dish").exists())

    def test_admin_configuration(self):
        dish_admin = admin.site._registry[MenuItem]
        self.assertIn("is_available", dish_admin.list_editable)
        self.assertIn("display_order", dish_admin.list_editable)
        self.assertIn("category", dish_admin.list_filter)
        self.assertIn("image_preview", dish_admin.readonly_fields)
        self.assertEqual(dish_admin.list_select_related, ("category",))
