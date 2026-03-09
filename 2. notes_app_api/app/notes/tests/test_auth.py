from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.note_list_url = reverse("note-list")
        self.category_list_url = reverse("category-list")
        self.tag_list_url = reverse("tag-list")

    def test_endpoint_notes_requires_login(self):
        res = self.client.get(self.note_list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_endpoint_categories_requires_login(self):
        res = self.client.get(self.category_list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_endpoint_tags_requires_login(self):
        res = self.client.get(self.tag_list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_note_requires_login(self):
        res = self.client.post(self.note_list_url, {"title": "test", "content": "x"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_category_requires_login(self):
        res = self.client.post(self.category_list_url, {"name": "test"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_tag_requires_login(self):
        res = self.client.post(self.tag_list_url, {"name": "test"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
