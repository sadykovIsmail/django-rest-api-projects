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


class TestNoteEdgeCases(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user("noteedgeuser", "pass123edge")
        self.client.force_authenticate(user=self.user)
        self.category = create_category(self.user, "Edge Category")
        self.tag = create_tag(self.user, "Edge Tag")

    def test_create_note_with_empty_title_fails(self):
        payload = {"title": "", "content": "Some content", "category": self.category.id}
        res = self.client.post(NOTE_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_note_missing_title_fails(self):
        payload = {"content": "No title here", "category": self.category.id}
        res = self.client.post(NOTE_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_note_with_max_length_title_succeeds(self):
        payload = {"title": "a" * 255, "content": "hello", "category": self.category.id}
        res = self.client.post(NOTE_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_note_title_exceeds_max_length_fails(self):
        payload = {"title": "a" * 256, "content": "hello", "category": self.category.id}
        res = self.client.post(NOTE_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_note_missing_category_fails(self):
        payload = {"title": "No Category", "content": "Some content"}
        res = self.client.post(NOTE_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_note_with_blank_content_succeeds(self):
        # content has blank=True so empty string is valid
        payload = {"title": "No Content Note", "content": "", "category": self.category.id}
        res = self.client.post(NOTE_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_note_with_tag_succeeds(self):
        payload = {
            "title": "Tagged Note",
            "content": "hello",
            "category": self.category.id,
            "tags": [self.tag.id],
        }
        res = self.client.post(NOTE_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_user_assigned_from_token_not_payload(self):
        payload = {"title": "Token Test", "content": "hello", "category": self.category.id}
        res = self.client.post(NOTE_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        note = Note.objects.get(id=res.data["id"])
        self.assertEqual(note.user, self.user)

    def test_partial_update_note_title(self):
        note = create_note(self.user, self.category, "Original Title")
        url = reverse("note-detail", args=[note.id])
        res = self.client.patch(url, {"title": "Updated Title"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        note.refresh_from_db()
        self.assertEqual(note.title, "Updated Title")

    def test_partial_update_note_content(self):
        note = create_note(self.user, self.category, "Some Note", "Old content")
        url = reverse("note-detail", args=[note.id])
        res = self.client.patch(url, {"content": "New content"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        note.refresh_from_db()
        self.assertEqual(note.content, "New content")

    def test_full_update_note(self):
        note = create_note(self.user, self.category, "Original Title", "Original content")
        url = reverse("note-detail", args=[note.id])
        payload = {"title": "New Title", "content": "New content", "category": self.category.id}
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        note.refresh_from_db()
        self.assertEqual(note.title, "New Title")
        self.assertEqual(note.content, "New content")

    def test_delete_own_note_succeeds(self):
        note = create_note(self.user, self.category, "To Delete")
        url = reverse("note-detail", args=[note.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Note.objects.filter(id=note.id).exists())

    def test_retrieve_note_returns_correct_data(self):
        note = create_note(self.user, self.category, "Specific Note", "Specific content")
        url = reverse("note-detail", args=[note.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], "Specific Note")
        self.assertEqual(res.data["content"], "Specific content")

    def test_deleted_note_no_longer_retrievable(self):
        note = create_note(self.user, self.category, "Gone Note")
        url = reverse("note-detail", args=[note.id])
        self.client.delete(url)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_returns_only_own_notes(self):
        other_user = create_user("othernote", "pass456")
        other_cat = create_category(other_user, "Other Cat")
        create_note(other_user, other_cat, "Other Note")
        create_note(self.user, self.category, "My Note")
        res = self.client.get(NOTE_LIST_LINK)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["title"], "My Note")


class TestCategoryEdgeCases(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user("catedgeuser", "pass123edge")
        self.client.force_authenticate(user=self.user)

    def test_create_category_with_empty_name_fails(self):
        payload = {"name": ""}
        res = self.client.post(CATEGORY_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_category_missing_name_fails(self):
        res = self.client.post(CATEGORY_LIST_LINK, {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_category_with_max_length_name_succeeds(self):
        payload = {"name": "c" * 255}
        res = self.client.post(CATEGORY_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_category_name_exceeds_max_length_fails(self):
        payload = {"name": "c" * 256}
        res = self.client.post(CATEGORY_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_category_name(self):
        cat = create_category(self.user, "Old Name")
        url = reverse("category-detail", args=[cat.id])
        res = self.client.patch(url, {"name": "New Name"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        cat.refresh_from_db()
        self.assertEqual(cat.name, "New Name")

    def test_delete_category_removes_it(self):
        cat = create_category(self.user, "To Delete")
        url = reverse("category-detail", args=[cat.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=cat.id).exists())

    def test_retrieve_category_returns_correct_data(self):
        cat = create_category(self.user, "Specific Category")
        url = reverse("category-detail", args=[cat.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "Specific Category")

    def test_user_assigned_from_token_not_payload(self):
        payload = {"name": "Token Category"}
        res = self.client.post(CATEGORY_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        cat = Category.objects.get(id=res.data["id"])
        self.assertEqual(cat.user, self.user)

    def test_list_returns_only_own_categories(self):
        other_user = create_user("othercat", "pass456")
        create_category(other_user, "Other Cat")
        create_category(self.user, "My Cat")
        res = self.client.get(CATEGORY_LIST_LINK)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], "My Cat")


class TestTagEdgeCases(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user("tagedgeuser", "pass123edge")
        self.client.force_authenticate(user=self.user)

    def test_create_tag_with_empty_name_fails(self):
        payload = {"name": ""}
        res = self.client.post(TAG_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_tag_missing_name_fails(self):
        res = self.client.post(TAG_LIST_LINK, {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_tag_with_max_length_name_succeeds(self):
        payload = {"name": "t" * 255}
        res = self.client.post(TAG_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_tag_name_exceeds_max_length_fails(self):
        payload = {"name": "t" * 256}
        res = self.client.post(TAG_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_tag_name(self):
        tag = create_tag(self.user, "Old Tag")
        url = reverse("tag-detail", args=[tag.id])
        res = self.client.patch(url, {"name": "New Tag"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, "New Tag")

    def test_delete_tag_removes_it(self):
        tag = create_tag(self.user, "To Delete Tag")
        url = reverse("tag-detail", args=[tag.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_retrieve_tag_returns_correct_data(self):
        tag = create_tag(self.user, "Specific Tag")
        url = reverse("tag-detail", args=[tag.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "Specific Tag")

    def test_user_assigned_from_token_not_payload(self):
        payload = {"name": "Token Tag"}
        res = self.client.post(TAG_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        tag = Tag.objects.get(id=res.data["id"])
        self.assertEqual(tag.user, self.user)

    def test_list_returns_only_own_tags(self):
        other_user = create_user("othertag", "pass456")
        create_tag(other_user, "Other Tag")
        create_tag(self.user, "My Tag")
        res = self.client.get(TAG_LIST_LINK)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], "My Tag")
