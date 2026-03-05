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

