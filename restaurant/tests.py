from html.parser import HTMLParser
from pathlib import Path
import re

from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings
from django.urls import reverse


class RestaurantMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = []
        self.identifiers = []
        self.assets = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if 'id' in attributes:
            self.identifiers.append(attributes['id'])
        if tag == 'a':
            self.anchors.append(attributes.get('href', ''))
        for attribute in ('href', 'src'):
            if attributes.get(attribute, '').startswith('/static/'):
                self.assets.append(attributes[attribute].removeprefix('/static/'))


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class RestaurantPageTests(TestCase):
    def test_restaurant_page_and_internal_links(self):
        response = self.client.get(reverse('restaurant:restaurant_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Shawarma Street')
        self.assertContains(response, 'Chicken Shawarma')
        markup = RestaurantMarkup()
        markup.feed(response.content.decode())
        self.assertEqual(len(markup.identifiers), len(set(markup.identifiers)))
        for anchor in markup.anchors:
            if anchor.startswith('#') and anchor != '#':
                self.assertIn(anchor[1:], markup.identifiers)
        self.assertEqual(markup.anchors.count('#'), 3)
        for asset in markup.assets:
            self.assertIsNotNone(finders.find(asset), asset)

    def test_stylesheet_images_exist(self):
        stylesheet = Path(finders.find('restaurant/css/restaurant.css'))
        for image in re.findall(r"url\(['\"]?([^)'\"]+)", stylesheet.read_text()):
            self.assertTrue((stylesheet.parent / image).resolve().is_file(), image)

    def test_page_http_methods(self):
        self.assertEqual(self.client.head('/').status_code, 200)
        self.assertEqual(self.client.post('/').status_code, 405)

    def test_staff_login_branding(self):
        response = self.client.get(reverse('admin:login'))
        self.assertContains(response, 'Shawarma Street Administration')
