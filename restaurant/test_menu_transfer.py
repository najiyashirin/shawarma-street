import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command, CommandError
from django.db import IntegrityError
from django.test import TestCase

from .models import MenuCategory, MenuItem


class MenuTransferTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.fixture = Path(self.directory.name) / "menu.json"
        call_command("dumpdata", "restaurant.MenuCategory", "restaurant.MenuItem", output=str(self.fixture), verbosity=0)
        self.original = json.loads(self.fixture.read_text())

    def import_menu(self, **options):
        call_command("import_menu", str(self.fixture), stdout=StringIO(), stderr=StringIO(), **options)

    def test_existing_menu_requires_explicit_consent(self):
        with self.assertRaisesMessage(CommandError, "Menu already exists"):
            self.import_menu()
        self.assertEqual(MenuItem.objects.count(), 3)

    def test_round_trip_repeat_and_sequence(self):
        for _ in range(2):
            self.import_menu(replace_menu=True)
            output = StringIO()
            call_command("dumpdata", "restaurant.MenuCategory", "restaurant.MenuItem", stdout=output)
            self.assertEqual(json.loads(output.getvalue()), self.original)
        category = MenuCategory.objects.create(name="New", slug="new")
        self.assertGreater(category.pk, max(row["pk"] for row in self.original if row["model"] == "restaurant.menucategory"))

    def test_empty_target_import(self):
        MenuItem.objects.all().delete()
        MenuCategory.objects.all().delete()
        self.import_menu()
        self.assertEqual(MenuItem.objects.count(), 3)

    def test_nonmenu_and_missing_relationship_rejected(self):
        for payload in ([{"model": "auth.user", "pk": 1, "fields": {}}], [row for row in self.original if row["model"] == "restaurant.menuitem"]):
            self.fixture.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(CommandError):
                self.import_menu(replace_menu=True)
            self.assertEqual(MenuItem.objects.count(), 3)

    def test_constraint_failure_rolls_back_replacement(self):
        for row in self.original:
            if row["model"] == "restaurant.menuitem":
                row["fields"]["mrp_price"] = "-1.00"
        self.fixture.write_text(json.dumps(self.original), encoding="utf-8")
        with self.assertRaises(IntegrityError):
            self.import_menu(replace_menu=True)
        self.assertTrue(all(item.mrp_price > 0 for item in MenuItem.objects.all()))
