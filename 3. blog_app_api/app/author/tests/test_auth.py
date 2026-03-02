from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author_list_url = reverse("authormodel-list")
        self.post_list_url = reverse("blogpostmodel-list")

    def test_endpoint_author_requires_login(self):
        res = self.client.get(self.author_list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_endpoint_post_requires_login(self):
        res = self.client.get(self.post_list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
