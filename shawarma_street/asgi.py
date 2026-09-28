"""ASGI entry point for Shawarma Street."""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shawarma_street.settings")
application = get_asgi_application()
