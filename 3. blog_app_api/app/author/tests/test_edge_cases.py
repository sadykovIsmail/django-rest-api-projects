from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from ..models import AuthorModel, BlogPostModel

User = get_user_model()
AUTHOR_LIST_LINK = reverse("authormodel-list")
BLOG_LIST_LINK = reverse("blogpostmodel-list")


def create_user(username, password):
    return User.objects.create(username=username, password=password)

def create_author(user, name="Example", email="email@example.com"):
    return AuthorModel.objects.create(user=user, name=name, email=email)

def create_post(user, author, title="Default Title", content="Default content"):
    return BlogPostModel.objects.create(user=user, author=author, title=title, content=content)


class TestAuthorEdgeCases(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user("edgeuser", "pass123edge")
        self.client.force_authenticate(user=self.user)

    def test_create_author_with_invalid_email_fails(self):
        payload = {"name": "Bad Email Author", "email": "not-an-email"}
        res = self.client.post(AUTHOR_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_author_with_empty_name_fails(self):
        payload = {"name": "", "email": "valid@example.com"}
        res = self.client.post(AUTHOR_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_author_missing_email_fails(self):
        payload = {"name": "No Email"}
        res = self.client.post(AUTHOR_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_author_missing_name_fails(self):
        payload = {"email": "noname@example.com"}
        res = self.client.post(AUTHOR_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_author_name(self):
        author = create_author(self.user, "Old Name", "old@example.com")
        url = reverse("authormodel-detail", args=[author.id])
        res = self.client.patch(url, {"name": "New Name"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        author.refresh_from_db()
        self.assertEqual(author.name, "New Name")

    def test_partial_update_author_email(self):
        author = create_author(self.user, "AuthorName", "old@example.com")
        url = reverse("authormodel-detail", args=[author.id])
        res = self.client.patch(url, {"email": "new@example.com"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        author.refresh_from_db()
        self.assertEqual(author.email, "new@example.com")

    def test_delete_author_removes_it(self):
        author = create_author(self.user, "ToDelete", "delete@example.com")
        url = reverse("authormodel-detail", args=[author.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AuthorModel.objects.filter(id=author.id).exists())

    def test_retrieve_author_returns_correct_data(self):
        author = create_author(self.user, "Specific Author", "specific@example.com")
        url = reverse("authormodel-detail", args=[author.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "Specific Author")
        self.assertEqual(res.data["email"], "specific@example.com")


class TestPostEdgeCases(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user("postedgeuser", "pass123edge")
        self.client.force_authenticate(user=self.user)
        self.author = create_author(self.user, "Edge Author", "edge@example.com")

    def test_create_post_with_empty_title_fails(self):
        payload = {"title": "", "content": "Some content", "author": self.author.id}
        res = self.client.post(BLOG_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_post_with_max_length_title_succeeds(self):
        payload = {"title": "a" * 255, "content": "hello", "author": self.author.id}
        res = self.client.post(BLOG_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_post_title_exceeds_max_length_fails(self):
        payload = {"title": "a" * 256, "content": "hello", "author": self.author.id}
        res = self.client.post(BLOG_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_post_content_exceeds_max_length_fails(self):
        payload = {"title": "Valid Title", "content": "x" * 256, "author": self.author.id}
        res = self.client.post(BLOG_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_post_missing_content_fails(self):
        payload = {"title": "No Content", "author": self.author.id}
        res = self.client.post(BLOG_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_post_title(self):
        post = create_post(self.user, self.author, "Original Title")
        url = reverse("blogpostmodel-detail", args=[post.id])
        res = self.client.patch(url, {"title": "Updated Title"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, "Updated Title")

    def test_full_update_post(self):
        post = create_post(self.user, self.author, "Original Title", "Original content")
        url = reverse("blogpostmodel-detail", args=[post.id])
        payload = {"title": "New Title", "content": "New content", "author": self.author.id}
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, "New Title")
        self.assertEqual(post.content, "New content")

    def test_delete_own_post_succeeds(self):
        post = create_post(self.user, self.author, "To Delete")
        url = reverse("blogpostmodel-detail", args=[post.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(BlogPostModel.objects.filter(id=post.id).exists())

    def test_retrieve_post_returns_correct_data(self):
        post = create_post(self.user, self.author, "My Specific Post", "Specific content")
        url = reverse("blogpostmodel-detail", args=[post.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], "My Specific Post")
        self.assertEqual(res.data["content"], "Specific content")

    def test_deleted_post_no_longer_retrievable(self):
        post = create_post(self.user, self.author, "Gone Post")
        url = reverse("blogpostmodel-detail", args=[post.id])
        self.client.delete(url)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
