from django.contrib import admin
from django.utils.html import format_html

from .models import MenuCategory, MenuItem, MenuItemVariant

admin.site.site_header = "Shawarma Street Administration"
admin.site.site_title = "Shawarma Street"
admin.site.index_title = "Restaurant menu management"


class MenuImageAdmin(admin.ModelAdmin):
    readonly_fields = ("image_preview", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Current photo")
    def image_preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" alt="{}" width="160" height="110" style="object-fit:cover;border-radius:6px">', obj.image.url, obj.name)
        return "No photo uploaded."


@admin.register(MenuCategory)
class MenuCategoryAdmin(MenuImageAdmin):
    list_display = ("name", "display_order", "is_active", "updated_at")
    list_editable = ("display_order", "is_active")
    search_fields = ("name", "description")
    list_filter = ("is_active",)
    fields = ("name", "slug", "description", "layout", "image", "image_preview", "display_order", "is_active", "created_at", "updated_at")


class MenuItemVariantInline(admin.TabularInline):
    model = MenuItemVariant
    extra = 0
    fields = ("label", "price", "discount_price", "display_order", "is_available")
    ordering = ("display_order", "pk")
    verbose_name_plural = "Variants (CAD) ? replace base prices when present"


@admin.register(MenuItem)
class MenuItemAdmin(MenuImageAdmin):
    inlines = (MenuItemVariantInline,)
    list_display = ("name", "category", "mrp_price", "discount_price", "is_available", "display_order")
    list_editable = ("is_available", "display_order")
    list_filter = ("category", "is_available")
    search_fields = ("name", "description", "category__name")
    list_select_related = ("category",)
    fieldsets = (
        ("Dish details", {"fields": ("name", "slug", "category", "description", "badge_label")}),
        ("Menu photo", {"fields": ("image", "image_preview")}),
        ("Pricing and availability", {"description": "Base CAD prices apply only without variants. Each variant uses its own price and discount; discounts never stack. Item availability overrides all variants.", "fields": ("mrp_price", "discount_price", "is_available", "display_order")}),
        ("Record dates", {"fields": ("created_at", "updated_at")}),
    )
