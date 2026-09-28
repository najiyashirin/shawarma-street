from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import MenuCategory, MenuItem, MenuItemVariant
from .test_menu import menu_photo


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class SeedMenuTests(TestCase):
    def seed(self, *args):
        output = StringIO()
        call_command("seed_menu", *args, stdout=output)
        return output.getvalue()

    def snapshot(self):
        return [list(model.objects.order_by("pk").values()) for model in (MenuCategory, MenuItem, MenuItemVariant)]

    def test_categories_items_prices_images_and_ordering(self):
        self.seed("--reset-menu", "--noinput")
        self.assertEqual(list(MenuCategory.objects.values_list("name", "layout", "display_order")), [
            ("Sandwiches", "cards", 0), ("Platters", "cards", 1), ("Sides", "compact", 2),
            ("Drinks", "compact", 3), ("Salads", "cards", 4),
        ])
        expected = {
            "sandwiches": [("Chicken Shawarma", "9.49"), ("Beef Shawarma", "9.99"), ("Shish Tawook", "9.99"), ("Falafel", "8.49")],
            "platters": [("Chicken Shawarma", "17.99"), ("Beef Shawarma", "18.99"), ("Shish Tawook", "18.99"), ("Mix Grill", "24.99")],
            "sides": [("Fries", "5.99"), ("Poutine", "6.99"), ("Fattoush Salad", "6.99"), ("Hummus", "5.99")],
            "drinks": [("Pop", "1.37"), ("Juice", "2.99"), ("Water", "1.37")],
            "salads": [("Fattoush Salad", "10.99"), ("Greek Salad", "11.99"), ("Chicken Salad", "14.99")],
        }
        self.assertEqual(MenuItem.objects.count(), 18)
        self.assertEqual(MenuItem.objects.values("slug").distinct().count(), 18)
        for category in MenuCategory.objects.all():
            self.assertTrue(category.is_active)
            self.assertFalse(category.image)
            self.assertEqual(list(category.items.values_list("name", "mrp_price")), [
                (name, Decimal(price)) for name, price in expected[category.slug]
            ])
            for index, item in enumerate(category.items.all()):
                self.assertEqual(item.display_order, index)
                self.assertTrue(item.is_available)
                self.assertTrue(item.description)
                self.assertFalse(item.image)
                self.assertIsNone(item.discount_price)
                self.assertIsInstance(item.mrp_price, Decimal)
                self.assertTrue(item.slug.startswith(category.slug + "-"))
                item.full_clean(exclude=["image"])

    def test_side_variants_and_decimal_prices(self):
        self.seed()
        expected = {
            "sides-fries": ["5.99", "7.99", "9.99"],
            "sides-poutine": ["6.99", "8.99", "11.99"],
            "sides-fattoush-salad": ["6.99", "8.99", "10.99"],
            "sides-hummus": ["5.99", "9.99"],
        }
        self.assertEqual(MenuItemVariant.objects.count(), 11)
        for slug, prices in expected.items():
            item = MenuItem.objects.get(slug=slug)
            self.assertEqual(list(item.variants.values_list("label", "price", "display_order")), [
                (label, Decimal(price), index) for index, (label, price) in enumerate(zip(("S", "M", "L"), prices))
            ])
            for variant in item.variants.all():
                self.assertTrue(variant.is_available)
                self.assertIsNone(variant.discount_price)
                self.assertIsInstance(variant.price, Decimal)
                variant.full_clean()

    def test_reruns_preserve_ids_unrelated_records_and_uploaded_images(self):
        original_category = MenuCategory.objects.get(slug="shawarmas")
        original_items = list(original_category.items.values())
        self.seed()
        original_ids = [list(model.objects.values_list("pk", flat=True)) for model in (MenuCategory, MenuItem, MenuItemVariant)]
        item = MenuItem.objects.get(slug="sides-fries")
        item.image = menu_photo()
        item.mrp_price = Decimal("19.99")
        item.discount_price = Decimal("15.99")
        item.is_available = False
        item.display_order = 99
        item.save()
        photo_name = item.image.name
        category = item.category
        category.image = menu_photo("category.png")
        category.is_active = False
        category.layout = "cards"
        category.display_order = 99
        category.save()
        category_photo_name = category.image.name
        item.variants.update(price=Decimal("20.00"), discount_price=Decimal("10.00"), is_available=False, display_order=99)
        # An extra staff-created variant must survive a normal seed run.
        extra = MenuItemVariant.objects.create(item=item, label="XL", price="14.99", display_order=4)
        self.seed()
        self.assertEqual(MenuCategory.objects.count(), 6)
        self.assertEqual(MenuItem.objects.count(), 21)
        self.assertEqual(MenuItemVariant.objects.count(), 12)
        for model, ids in zip((MenuCategory, MenuItem, MenuItemVariant), original_ids):
            self.assertEqual(set(model.objects.filter(pk__in=ids).values_list("pk", flat=True)), set(ids))
        self.assertEqual(list(original_category.items.values()), original_items)
        item.refresh_from_db()
        category.refresh_from_db()
        self.assertEqual(item.image.name, photo_name)
        self.assertEqual(category.image.name, category_photo_name)
        self.assertEqual(item.mrp_price, Decimal("5.99"))
        self.assertIsNone(item.discount_price)
        self.assertTrue(item.is_available)
        self.assertEqual(item.display_order, 0)
        self.assertTrue(category.is_active)
        self.assertEqual(category.layout, "compact")
        self.assertEqual(category.display_order, 2)
        variant = item.variants.get(label="S")
        self.assertEqual(variant.price, Decimal("5.99"))
        self.assertIsNone(variant.discount_price)
        self.assertTrue(variant.is_available)
        self.assertEqual(variant.display_order, 0)
        self.assertTrue(MenuItemVariant.objects.filter(pk=extra.pk).exists())

    def test_running_twice_has_no_duplicates(self):
        self.seed()
        before = [list(model.objects.values_list("pk", flat=True)) for model in (MenuCategory, MenuItem, MenuItemVariant)]
        self.seed()
        after = [list(model.objects.values_list("pk", flat=True)) for model in (MenuCategory, MenuItem, MenuItemVariant)]
        self.assertEqual(before, after)

    def test_reset_only_deletes_menu_records(self):
        user = get_user_model().objects.create_user(username="menu-staff", password="test-password", is_staff=True)
        group = Group.objects.create(name="Restaurant staff")
        permission = Permission.objects.get(codename="change_menuitem")
        group.permissions.add(permission)
        user.groups.add(group)
        user.user_permissions.add(permission)
        session = Session.objects.create(session_key="seed-test-session", session_data="preserve-me", expire_date=timezone.now())
        permissions_before = list(Permission.objects.values())
        user_before = get_user_model().objects.values().get(pk=user.pk)
        original_item = MenuItem.objects.get(slug="chicken-shawarma")
        MenuItemVariant.objects.create(item=original_item, label="Old size", price="8.00")
        with patch("builtins.input", return_value="yes") as confirmation:
            self.seed("--reset-menu")
        confirmation.assert_called_once()
        self.assertEqual(MenuCategory.objects.count(), 5)
        self.assertEqual(MenuItem.objects.count(), 18)
        self.assertEqual(MenuItemVariant.objects.count(), 11)
        self.assertFalse(MenuCategory.objects.filter(slug="shawarmas").exists())
        self.assertFalse(MenuItemVariant.objects.filter(label="Old size").exists())
        self.assertEqual(get_user_model().objects.values().get(pk=user.pk), user_before)
        self.assertEqual(list(Permission.objects.values()), permissions_before)
        self.assertTrue(user.groups.filter(pk=group.pk).exists())
        self.assertTrue(user.user_permissions.filter(pk=permission.pk).exists())
        self.assertTrue(group.permissions.filter(pk=permission.pk).exists())
        session.refresh_from_db()
        self.assertEqual(session.session_data, "preserve-me")
        with patch("builtins.input") as confirmation:
            self.seed("--reset-menu", "--noinput")
        confirmation.assert_not_called()
        self.assertEqual(MenuItem.objects.count(), 18)

    def test_reset_cancellation_changes_nothing(self):
        before = self.snapshot()
        for answer in ("no", "", "y"):
            with self.subTest(answer=answer), patch("builtins.input", return_value=answer):
                self.assertIn("Cancelled", self.seed("--reset-menu"))
            self.assertEqual(self.snapshot(), before)
        with patch("builtins.input", side_effect=EOFError):
            self.assertIn("Cancelled", self.seed("--reset-menu"))
        self.assertEqual(self.snapshot(), before)

    def test_validation_failure_rolls_back_even_reset(self):
        before = self.snapshot()
        with patch.object(MenuItemVariant, "full_clean", side_effect=ValidationError("Invalid price")):
            with self.assertRaises(ValidationError):
                self.seed("--reset-menu", "--noinput")
        self.assertEqual(self.snapshot(), before)
