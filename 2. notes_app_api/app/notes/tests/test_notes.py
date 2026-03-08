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
    note = Note.objects.create(title=title, content=content, user=user, category=category)
    note.tags.set([tags])
    return note


class test_note(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user("My User", "passwords123")
        self.client.force_authenticate(user=self.user)
        self.tag_endpoint_link = reverse("tag-list")
        self.category_endpoint_link = reverse("category-list")
        self.note_endpoint_link = reverse("note-list")
        self.tag = create_tag(self.user, "example")
        self.category = create_category(self.user, "example_category")


    def test_notes_create_success(self):
        payload = {
            "title": "first note",
            "content": "hello",
            "tags": self.tag.id,
            "category": self.category.id,
        }
        res = self.client.post(self.note_endpoint_link, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_notes_sees_own_notes(self):
        other_user = create_user("OtherUser", "pass134d")
        other_tag = create_tag(other_user, "other_user_tag")
        other_category = create_category(other_user, "other_user_category")

        create_note("Other_user_note", "hello", other_user, other_tag, other_category)
        create_note("MyUser_note", "hello", self.user, self.tag, self.category)
        res = self.client.get(self.note_endpoint_link)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["title"], "MyUser_note")