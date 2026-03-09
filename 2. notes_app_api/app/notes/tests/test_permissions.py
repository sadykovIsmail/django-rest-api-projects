from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from ..models import Note, Category, Tag

User = get_user_model()

NOTE_LIST_LINK = reverse("note-list")
CATEGORY_LIST_LINK = reverse("category-list")
TAG_LIST_LINK = reverse("tag-list")


def create_user(username, password):
    return User.objects.create(username=username, password=password)

def create_category(user, name="Default Category"):
    return Category.objects.create(user=user, name=name)

def create_tag(user, name="Default Tag"):
    return Tag.objects.create(user=user, name=name)

def create_note(user, category, title="Default Title", content="Default content"):
    return Note.objects.create(user=user, category=category, title=title, content=content)


class TestNotePermissions(TestCase):
    """User1 should not be able to read, modify, or delete user2's notes."""

    def setUp(self):
        self.user1 = create_user("noteperm1", "pass123")
        self.user2 = create_user("noteperm2", "pass456")

        self.cat1 = create_category(self.user1, "Cat One")
        self.cat2 = create_category(self.user2, "Cat Two")

        self.note1 = create_note(self.user1, self.cat1, "User1 Note")
        self.note2 = create_note(self.user2, self.cat2, "User2 Note")

        self.client1 = APIClient()
        self.client2 = APIClient()
        self.client1.force_authenticate(user=self.user1)
        self.client2.force_authenticate(user=self.user2)

    def test_user1_cannot_retrieve_user2_note(self):
        url = reverse("note-detail", args=[self.note2.id])
        res = self.client1.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_user1_cannot_patch_user2_note(self):
        url = reverse("note-detail", args=[self.note2.id])
        res = self.client1.patch(url, {"title": "Hacked Title"})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.note2.refresh_from_db()
        self.assertEqual(self.note2.title, "User2 Note")

    def test_user1_cannot_put_user2_note(self):
        url = reverse("note-detail", args=[self.note2.id])
        payload = {"title": "Hacked", "content": "Hacked", "category": self.cat2.id}
        res = self.client1.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.note2.refresh_from_db()
        self.assertEqual(self.note2.title, "User2 Note")

    def test_user1_cannot_delete_user2_note(self):
        url = reverse("note-detail", args=[self.note2.id])
        res = self.client1.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Note.objects.filter(id=self.note2.id).exists())

    def test_user1_cannot_upload_image_to_user2_note(self):
        url = reverse("note-image-upload", args=[self.note2.id])
        res = self.client1.post(url, {}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_user_cannot_delete_note(self):
        unauthenticated = APIClient()
        url = reverse("note-detail", args=[self.note1.id])
        res = unauthenticated.delete(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Note.objects.filter(id=self.note1.id).exists())

    def test_unauthenticated_user_cannot_patch_note(self):
        unauthenticated = APIClient()
        url = reverse("note-detail", args=[self.note1.id])
        res = unauthenticated.patch(url, {"title": "Sneaky"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TestCategoryPermissions(TestCase):
    """User1 should not be able to modify or delete user2's categories."""

    def setUp(self):
        self.user1 = create_user("catperm1", "pass123")
        self.user2 = create_user("catperm2", "pass456")

        self.cat1 = create_category(self.user1, "Cat One")
        self.cat2 = create_category(self.user2, "Cat Two")

        self.client1 = APIClient()
        self.client2 = APIClient()
        self.client1.force_authenticate(user=self.user1)
        self.client2.force_authenticate(user=self.user2)

    def test_user1_cannot_retrieve_user2_category(self):
        url = reverse("category-detail", args=[self.cat2.id])
        res = self.client1.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_user1_cannot_patch_user2_category(self):
        url = reverse("category-detail", args=[self.cat2.id])
        res = self.client1.patch(url, {"name": "Hacked"})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.cat2.refresh_from_db()
        self.assertEqual(self.cat2.name, "Cat Two")

    def test_user1_cannot_delete_user2_category(self):
        url = reverse("category-detail", args=[self.cat2.id])
        res = self.client1.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Category.objects.filter(id=self.cat2.id).exists())

    def test_unauthenticated_user_cannot_create_category(self):
        unauthenticated = APIClient()
        payload = {"name": "Anon Category"}
        res = unauthenticated.post(CATEGORY_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TestTagPermissions(TestCase):
    """User1 should not be able to modify or delete user2's tags."""

    def setUp(self):
        self.user1 = create_user("tagperm1", "pass123")
        self.user2 = create_user("tagperm2", "pass456")

        self.tag1 = create_tag(self.user1, "Tag One")
        self.tag2 = create_tag(self.user2, "Tag Two")

        self.client1 = APIClient()
        self.client2 = APIClient()
        self.client1.force_authenticate(user=self.user1)
        self.client2.force_authenticate(user=self.user2)

    def test_user1_cannot_retrieve_user2_tag(self):
        url = reverse("tag-detail", args=[self.tag2.id])
        res = self.client1.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_user1_cannot_patch_user2_tag(self):
        url = reverse("tag-detail", args=[self.tag2.id])
        res = self.client1.patch(url, {"name": "Hacked"})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.tag2.refresh_from_db()
        self.assertEqual(self.tag2.name, "Tag Two")

    def test_user1_cannot_delete_user2_tag(self):
        url = reverse("tag-detail", args=[self.tag2.id])
        res = self.client1.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Tag.objects.filter(id=self.tag2.id).exists())

    def test_unauthenticated_user_cannot_create_tag(self):
        unauthenticated = APIClient()
        payload = {"name": "Anon Tag"}
        res = unauthenticated.post(TAG_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
