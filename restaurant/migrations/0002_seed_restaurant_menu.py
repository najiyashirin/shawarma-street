"""Preserve the launch menu and copy its photograph into media storage."""
from decimal import Decimal
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import migrations


def seed_restaurant_menu(apps, schema_editor):
    MenuCategory = apps.get_model("restaurant", "MenuCategory")
    MenuItem = apps.get_model("restaurant", "MenuItem")
    database = schema_editor.connection.alias
    category, _ = MenuCategory.objects.using(database).get_or_create(
        slug="shawarmas", defaults={"name": "Shawarmas", "display_order": 0},
    )
    photo = Path(__file__).resolve().parents[1] / "static/restaurant/images/shawarma-grill.png"
    storage = MenuItem._meta.get_field("image").storage
    photo_name = "menu/items/shawarma-grill.png"
    if not storage.exists(photo_name):
        photo_name = storage.save(photo_name, ContentFile(photo.read_bytes()))
    dishes = (
        ("chicken-shawarma", "Chicken Shawarma", "Chargrilled chicken, pickles, garlic sauce.", "8.99", "Most loved"),
        ("beef-shawarma", "Beef Shawarma", "Slow-roasted beef, sumac onions, tahini.", "9.99", ""),
        ("mixed-shawarma", "Mixed Shawarma", "The best of both, with house-made sauce.", "10.99", ""),
    )
    for display_order, (slug, name, description, price, badge_label) in enumerate(dishes):
        MenuItem.objects.using(database).get_or_create(slug=slug, defaults={
            "category": category, "name": name, "description": description,
            "mrp_price": Decimal(price), "badge_label": badge_label,
            "image": photo_name, "display_order": display_order,
        })


class Migration(migrations.Migration):
    dependencies = [("restaurant", "0001_initial")]
    # Reversing this seed must not delete dishes subsequently edited by staff.
    operations = [migrations.RunPython(seed_restaurant_menu, migrations.RunPython.noop)]
