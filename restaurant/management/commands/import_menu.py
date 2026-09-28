"""Import only a complete Django JSON menu fixture, with explicit replacement consent."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core import serializers
from django.core.management import BaseCommand, CommandError, call_command
from django.db import transaction

from restaurant.models import MenuCategory, MenuItem


class Command(BaseCommand):
    help = "Import menu-only JSON. Refuses existing menu data unless --replace-menu is supplied."

    def add_arguments(self, parser):
        parser.add_argument("fixture", type=Path)
        parser.add_argument("--replace-menu", action="store_true", help="WARNING: delete the entire existing menu, including seed data, before importing.")

    def handle(self, *args, **options):
        try:
            payload = json.loads(options["fixture"].read_text(encoding="utf-8"))
            if not isinstance(payload, list) or not payload:
                raise ValueError("Expected a nonempty menu fixture.")
            allowed = {"restaurant.menucategory", "restaurant.menuitem"}
            if any(row.get("model") not in allowed for row in payload):
                raise ValueError("Only MenuCategory and MenuItem records are allowed.")
            keys = [(row["model"], row["pk"]) for row in payload]
            if any(not isinstance(pk, int) or pk <= 0 for _, pk in keys) or len(set(keys)) != len(keys):
                raise ValueError("Each menu record must have a unique positive integer primary key.")
            categories = {pk for model, pk in keys if model == "restaurant.menucategory"}
            if any(row["fields"]["category"] not in categories for row in payload if row["model"] == "restaurant.menuitem"):
                raise ValueError("Every item must reference a category in this fixture.")
            # Parse all fields before any deletion. loaddata checks DB constraints and resets sequences.
            data = json.dumps(payload)
            list(serializers.deserialize("json", data))
        except (OSError, ValueError, KeyError, TypeError, AttributeError, serializers.base.DeserializationError) as exc:
            raise CommandError("Invalid menu fixture; nothing imported.") from exc

        with transaction.atomic():
            if MenuCategory.objects.exists() or MenuItem.objects.exists():
                if not options["replace_menu"]:
                    raise CommandError("Menu already exists (including migration seed data). Back it up, then use --replace-menu only if replacing ALL menu data is intended.")
                self.stderr.write("WARNING: replacing all existing menu categories and items.")
                MenuItem.objects.all().delete()
                MenuCategory.objects.all().delete()
            # Read the validated in-memory content, avoiding file changes between validation and import.
            with TemporaryDirectory() as directory:
                fixture = Path(directory) / "menu.json"
                fixture.write_text(data, encoding="utf-8")
                call_command("loaddata", str(fixture), stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS("Menu imported. Users and other application data were not imported."))
