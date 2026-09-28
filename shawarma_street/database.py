"""Database selection shared by settings and configuration tests."""
import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured


def database_config(base_dir, environ=None):
    env = os.environ if environ is None else environ
    if "DATABASE_URL" not in env:
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": env.get("RESTAURANT_DATABASE_PATH", str(base_dir / "db.sqlite3")),
        }
    try:
        config = dj_database_url.parse(env["DATABASE_URL"], conn_max_age=0)
        if config.get("ENGINE") != "django.db.backends.postgresql" or not all(
            config.get(key) for key in ("NAME", "HOST", "USER")
        ):
            raise ValueError
    except (ValueError, TypeError, KeyError):
        # Parser errors may contain the supplied URL: never echo credentials.
        raise ImproperlyConfigured(
            "DATABASE_URL must be a valid PostgreSQL URL with host, user and database."
        ) from None
    # Compatible with transaction-pooling providers; no persistent Django connections.
    config["DISABLE_SERVER_SIDE_CURSORS"] = True
    return config
