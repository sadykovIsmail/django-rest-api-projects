from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from ..models import Note, Tag, Category

User = get_user_model()

def create_user(username, password):
    return User.objects.create(username=username, password=password)

def create_category(user, name):
    return Category.objects.create(user=user, name=name)

def create_tag(user, name):
    return Tag.objects.create(user=user, name=name)

def create_note(title, content, user, tags, category):
    return Note.objects.create(title=title, content=content, user=user, tags=tags, category=category)
