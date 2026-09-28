from django.db.models import Prefetch
from django.shortcuts import render
from django.views.decorators.http import require_safe

from .models import MenuCategory, MenuItem, MenuItemVariant


def public_menu(*, preview=False):
    items = MenuItem.objects.prefetch_related(
        Prefetch("variants", queryset=MenuItemVariant.objects.all(), to_attr="menu_variants")
    )
    categories = MenuCategory.objects.filter(is_active=True)
    if preview:
        # Sliced prefetch limits each category to its first ordered dish in SQL.
        categories = categories[:4]
        items = items[:1]
    categories = list(categories.prefetch_related(Prefetch("items", queryset=items, to_attr="preview_items" if preview else None)))
    for category in categories:
        for item in (category.preview_items if preview else category.items.all()):
            item.can_order = item.is_available and (not item.menu_variants or any(v.is_available for v in item.menu_variants))
    return categories


@require_safe
def restaurant_home(request):
    return render(request, "restaurant/restaurant.html", {"menu_categories": public_menu(preview=True)})


@require_safe
def restaurant_menu(request):
    return render(request, "restaurant/full_menu.html", {"menu_categories": public_menu(), "is_full_menu": True})
