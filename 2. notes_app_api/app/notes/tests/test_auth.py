from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category_endpoint = reverse("category-list")
        self.note_endpoint = reverse("note-list")
        self.tag_enpoint = reverse("tag-list")

    def test_category_requires_login(self):
        res = self.client.get(self.category_endpoint)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)