from pathlib import Path
from secrets import token_hex

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from shawarma_street.database import database_config


class DatabaseConfigurationTests(SimpleTestCase):
    def test_local_default_and_existing_override(self):
        root = Path("project")
        self.assertEqual(database_config(root, {}), {
            "ENGINE": "django.db.backends.sqlite3", "NAME": str(root / "db.sqlite3"),
        })
        self.assertEqual(database_config(root, {"RESTAURANT_DATABASE_PATH": "custom.sqlite3"})["NAME"], "custom.sqlite3")

    def test_vercel_requires_a_hosted_database(self):
        with self.assertRaisesRegex(ImproperlyConfigured, "DATABASE_URL is required on Vercel"):
            database_config(Path("unused"), {"VERCEL": "1"})

    def test_postgres_uses_supplied_credentials_and_options(self):
        password = token_hex(16)
        config = database_config(Path("unused"), {
            "DATABASE_URL": f"postgresql://test_user:{password}@db.example:5433/menu?sslmode=require",
            "RESTAURANT_DATABASE_PATH": "ignored.sqlite3",
        })
        self.assertEqual(config["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(config["USER"], "test_user")
        self.assertEqual(config["PASSWORD"], password)
        self.assertEqual(config["NAME"], "menu")
        self.assertEqual(config["HOST"], "db.example")
        self.assertEqual(config["PORT"], 5433)
        self.assertEqual(config["OPTIONS"]["sslmode"], "require")
        self.assertEqual(config["CONN_MAX_AGE"], 0)
        self.assertTrue(config["DISABLE_SERVER_SIDE_CURSORS"])

    def test_invalid_explicit_urls_never_fall_back_or_expose_credentials(self):
        for url in ("", " ", "invalid", "sqlite:///db.sqlite3", "mysql://u:secret@host/db", "postgresql://u:secret@host:bad/db", "postgresql:///", "postgresql://u:secret@host"):
            with self.subTest(url=url), self.assertRaises(ImproperlyConfigured) as error:
                database_config(Path("unused"), {"DATABASE_URL": url})
            self.assertNotIn("secret", str(error.exception))
