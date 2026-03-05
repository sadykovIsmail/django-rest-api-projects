from django.test import TestCase
from models import AuthorModel
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient
User = get_user_model()

AUTHOR_LIST_LINK = reverse("authormobile-list")


def create_user(username, password):
    # for creating reusable user
    return User.objects.create(username=username, password=password)

def create_author(user, name="Example", email="example@example.com"):
    # creatign author
    return AuthorModel.objects.create(user=user, name=name, email=email)

class test_author_create(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        self.author_list_link = reverse("authormodel-list")
    def test_author_login_returns_only_own(self):
        other_user = create_user("OtherUser", "Otheruser122")
        create_author(user=other_user, name="OtherUser")
        create_author(user=self.user, name="MyAuthor")
        res = self.client.get(AUTHOR_LIST_LINK)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], "MyAuthor")




