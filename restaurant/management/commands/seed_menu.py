"""Repeatable development menu data; never replace unrelated data by default."""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from restaurant.models import MenuCategory, MenuItem, MenuItemVariant


# Prices are strings until converted to Decimal, never binary floats.
# A tuple of prices represents S/M/L (or S/M); its first price is the base fallback.
MENU = (
    ("Sandwiches", "cards", (
        ("Chicken Shawarma", "Marinated chicken, garlic sauce, pickles and fresh vegetables in warm pita.", "9.49"),
        ("Beef Shawarma", "Slow-roasted beef, sumac onions, tomatoes and tahini in warm pita.", "9.99"),
        ("Shish Tawook", "Grilled marinated chicken, garlic sauce, pickles and fresh vegetables.", "9.99"),
        ("Falafel", "Crispy falafel, tahini, pickles and fresh vegetables in warm pita.", "8.49"),
    )),
    ("Platters", "cards", (
        ("Chicken Shawarma", "Sliced chicken shawarma with seasoned rice, salad and garlic sauce.", "17.99"),
        ("Beef Shawarma", "Sliced beef shawarma with seasoned rice, salad and tahini sauce.", "18.99"),
        ("Shish Tawook", "Grilled chicken skewers served with rice, salad and garlic sauce.", "18.99"),
        ("Mix Grill", "Chicken, beef kabab and shawarma with rice, salad and house sauces.", "24.99"),
    )),
    ("Sides", "compact", (
        ("Fries", "Crispy golden fries, lightly salted and served hot.", ("5.99", "7.99", "9.99")),
        ("Poutine", "Golden fries topped with cheese curds and rich gravy.", ("6.99", "8.99", "11.99")),
        ("Fattoush Salad", "Fresh mixed vegetables, crispy pita and tangy sumac dressing.", ("6.99", "8.99", "10.99")),
        ("Hummus", "Smooth chickpea dip with tahini, lemon and olive oil.", ("5.99", "9.99")),
    )),
    ("Drinks", "compact", (
        ("Pop", "A refreshing selection of canned soft drinks.", "1.37"),
        ("Juice", "Assorted bottled fruit juices, served chilled.", "2.99"),
        ("Water", "Chilled bottled water.", "1.37"),
    )),
    ("Salads", "cards", (
        ("Fattoush Salad", "Crisp lettuce, tomatoes, cucumber and toasted pita with sumac dressing.", "10.99"),
        ("Greek Salad", "Tomatoes, cucumber, peppers, olives and feta with herb dressing.", "11.99"),
        ("Chicken Salad", "Grilled chicken over fresh greens, tomatoes and cucumber with house dressing.", "14.99"),
    )),
)


class Command(BaseCommand):
    help = "Add/update the development menu, preserving unrelated menu records and uploaded images."

    def add_arguments(self, parser):
        parser.add_argument("--reset-menu", action="store_true", help="Delete ALL menu categories, items and variants before seeding; requires confirmation.")
        parser.add_argument("--noinput", action="store_true", help="Skip confirmation when used with --reset-menu.")

    def handle(self, *args, **options):
        if options["reset_menu"] and not options["noinput"]:
            self.stdout.write(self.style.WARNING(
                "This deletes ALL MenuItemVariant, MenuItem and MenuCategory records. "
                "Users, auth records, sessions and uploaded files will not be deleted."
            ))
            try:
                confirmed = input('Type "yes" to reset the menu: ').strip().lower() == "yes"
            except (EOFError, KeyboardInterrupt):
                confirmed = False
            if not confirmed:
                self.stdout.write("Cancelled. No data changed.")
                return

        with transaction.atomic():
            if options["reset_menu"]:
                MenuItemVariant.objects.all().delete()
                MenuItem.objects.all().delete()
                MenuCategory.objects.all().delete()

            for category_order, (name, layout, dishes) in enumerate(MENU):
                category_slug = slugify(name)
                category, _ = MenuCategory.objects.update_or_create(
                    slug=category_slug,
                    defaults={"name": name, "layout": layout, "display_order": category_order, "is_active": True},
                )
                category.full_clean()
                for item_order, (item_name, description, prices) in enumerate(dishes):
                    variant_prices = prices if isinstance(prices, tuple) else ()
                    item, _ = MenuItem.objects.update_or_create(
                        slug=f"{category_slug}-{slugify(item_name)}",
                        defaults={
                            "category": category, "name": item_name, "description": description,
                            "mrp_price": Decimal(variant_prices[0] if variant_prices else prices),
                            "discount_price": None, "display_order": item_order, "is_available": True,
                        },
                    )
                    # Empty seed photos are intentional. Keep the admin's required-image
                    # validation unchanged and validate every other field/constraint.
                    item.full_clean(exclude=["image"] if not item.image else None)
                    for variant_order, (label, price) in enumerate(zip(("S", "M", "L"), variant_prices)):
                        variant, _ = MenuItemVariant.objects.update_or_create(
                            item=item, label=label,
                            defaults={"price": Decimal(price), "discount_price": None,
                                      "display_order": variant_order, "is_available": True},
                        )
                        variant.full_clean()

        self.stdout.write(self.style.SUCCESS(
            "Seeded 5 categories, 18 items and 11 variants. "
            + ("Previous menu records were reset." if options["reset_menu"] else "Unrelated records and existing images were preserved.")
        ))
