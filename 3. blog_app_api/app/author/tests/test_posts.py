from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import BlogPostModel

from rest_framework.test import APIClient
from rest_framework import status