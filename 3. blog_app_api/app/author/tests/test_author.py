from django.test import TestCase
from models import AuthorModel
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient
User = get_user_model()



def create_user(username, password):
    # for creating reusable user
    return User.objects.create(username=username, password=password)

class test_author_create(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user
        self.client.force_authenticate(user=self.user)

    