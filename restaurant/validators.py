"""Validation shared by restaurant image uploads."""
import warnings

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


def validate_menu_image(image):
    """Accept bounded, decoded raster images rather than trusting extensions."""
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("Menu images must be 5 MB or smaller.")
    try:
        image.open("rb")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            photo = Image.open(image)
            if photo.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValidationError("Upload a JPEG, PNG or WebP image.")
            if photo.width * photo.height > 20_000_000:
                raise ValidationError("Menu images must not exceed 20 megapixels.")
            photo.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise ValidationError("Upload a valid JPEG, PNG or WebP image.") from error
    finally:
        image.seek(0)
