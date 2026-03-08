from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from ..models import Category

User = get_user_model()

def create_user(username="testuser", password="testpass123"):
    return User.objects.create(username=username, password=password)

class CategoryTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user("User1", "User1pass23")
        self.client.force_authenticate(user=self.user)

    def test_category_creates_successfully(self):
