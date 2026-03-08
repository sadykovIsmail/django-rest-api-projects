from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from ..models import Tag
User = get_user_model()

def create_user(username, password):
    return User.objects.create(username=username, password=password)

def create_tag(name="example", user="example user"):
    return Tag.objects.create(name=name, user=user)

class test_tags(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user("My user", "password123d")
        self.client.force_authenticate(user=self.user)
        self.tags_endnpoint = reverse("tag-list")

    def test_tag_creation(self):
        payload = {"name": "example"}
        res = self.client.post(self.tags_endnpoint, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_tag_user_sees_own(self):
        other_user = create_user("OtherUser", "password123")
        create_tag(name="Other-User", user=other_user)
        create_tag(name="MyUser", user=self.user)
        res = self.client.get(self.tags_endnpoint)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], "MyUser")

