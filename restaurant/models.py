from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models

from .validators import validate_menu_image


def category_image_path(category, filename):
    return f"menu/categories/{uuid4().hex}{Path(filename).suffix.lower()}"


def item_image_path(item, filename):
    return f"menu/items/{uuid4().hex}{Path(filename).suffix.lower()}"


class MenuCategory(models.Model):
    name = models.CharField("Category name", max_length=120)
    slug = models.SlugField(max_length=140, unique=True, help_text="Unique category identifier; suggested from the name.")
    layout = models.CharField(max_length=10, choices=[("cards", "Cards"), ("compact", "Compact rows")], default="cards", help_text="Use compact rows for sides, drinks or other small products.")
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to=category_image_path, blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_menu_image],
        help_text="Optional category photo. JPEG, PNG or WebP, up to 5 MB and 20 megapixels.",
    )
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first on the menu.")
    is_active = models.BooleanField("Show category on menu", default=True, help_text="Hide this category and all its dishes by clearing this box.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name", "pk"]
        verbose_name = "Menu category"
        verbose_name_plural = "Menu categories"
        indexes = [models.Index(fields=["is_active", "display_order"], name="menu_category_public_idx")]

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(MenuCategory, on_delete=models.PROTECT, related_name="items", help_text="Move or remove dishes before deleting their category.")
    name = models.CharField("Dish name", max_length=160)
    slug = models.SlugField(max_length=180, unique=True, help_text="Unique dish identifier; suggested from the name.")
    image = models.ImageField(
        upload_to=item_image_path,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_menu_image],
        help_text="Dish photo. JPEG, PNG or WebP, up to 5 MB and 20 megapixels.",
    )
    description = models.TextField(help_text="Ingredients and flavours shown on the menu.")
    badge_label = models.CharField(max_length=40, blank=True, help_text="Optional dish label, such as Most loved.")
    mrp_price = models.DecimalField("MRP", max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))], help_text="Regular price in CAD; must be greater than zero.")
    discount_price = models.DecimalField("Discount price", max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal("0.01"))], help_text="Optional sale price, greater than zero and lower than MRP.")
    is_available = models.BooleanField("Available to order", default=True, help_text="Unavailable dishes remain visible without an order link.")
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first within the category.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name", "pk"]
        verbose_name = "Menu item"
        verbose_name_plural = "Menu items"
        indexes = [models.Index(fields=["category", "display_order"], name="menu_item_category_order_idx")]
        constraints = [
            models.CheckConstraint(condition=models.Q(mrp_price__gt=0), name="menu_item_positive_mrp"),
            models.CheckConstraint(
                condition=models.Q(discount_price__isnull=True) | (models.Q(discount_price__gt=0) & models.Q(discount_price__lt=models.F("mrp_price"))),
                name="menu_item_valid_discount",
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if isinstance(self.discount_price, Decimal) and self.discount_price.is_finite() and isinstance(self.mrp_price, Decimal) and self.mrp_price.is_finite():
            if self.discount_price <= 0 or self.discount_price >= self.mrp_price:
                raise ValidationError({"discount_price": "Discount price must be greater than zero and lower than MRP."})


class MenuItemVariant(models.Model):
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="variants")
    label = models.CharField(max_length=40, help_text="Size or option, for example S, M or L.")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal("0.01"))])
    display_order = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["item", "label"], name="menu_variant_unique_label"),
            models.CheckConstraint(condition=models.Q(price__gt=0), name="menu_variant_positive_price"),
            models.CheckConstraint(condition=models.Q(discount_price__isnull=True) | (models.Q(discount_price__gt=0) & models.Q(discount_price__lt=models.F("price"))), name="menu_variant_valid_discount"),
        ]

    def __str__(self):
        return self.label

    def clean(self):
        super().clean()
        self.label = self.label.strip() if isinstance(self.label, str) else self.label
        if not self.label:
            raise ValidationError({"label": "Enter a size or option label."})
        if isinstance(self.price, Decimal) and self.price.is_finite() and isinstance(self.discount_price, Decimal) and self.discount_price.is_finite():
            if self.discount_price <= 0 or self.discount_price >= self.price:
                raise ValidationError({"discount_price": "Discount price must be greater than zero and lower than the variant price."})
