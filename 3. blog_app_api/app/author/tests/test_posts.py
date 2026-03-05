from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import BlogPostModel, AuthorModel

from rest_framework.test import APIClient
from rest_framework import status

BLOG_LIST_LINK = reverse("blogpostmodel-list")
User = get_user_model()

def create_user(usernane, password):
    return User.objects.create(username=usernane, password=password)

def create_author(user, name="Example", email="email@example.com"):
    return AuthorModel.objects.create(user=user, name=name, email=email)


class test_post_create(TestCase):
    # check if user assigning automatically from token
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(usernane="My user", password="123example")
        self.client.force_authenticate(user=self.user)
        self.author = create_author(self.user, "Author1", "myauthor@example.com")
        self.post_link = reverse("blogpostmodel-list")

    def test_create_post_properly(self):
        payload = {
            "title": "from Author 1",
            "content": "hello",
            "author": self.author.id,
        }
        res = self.client.post(BLOG_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
