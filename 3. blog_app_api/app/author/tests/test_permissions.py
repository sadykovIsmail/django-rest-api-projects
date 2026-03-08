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


class TestPostPermissions(TestCase):
    """User1 should not be able to read, modify, or delete user2's posts."""

    def setUp(self):
        self.user1 = create_user("permuser1", "pass123")
        self.user2 = create_user("permuser2", "pass456")

        self.author1 = create_author(self.user1, "Author One", "one@example.com")
        self.author2 = create_author(self.user2, "Author Two", "two@example.com")

        self.post1 = create_post(self.user1, self.author1, "User1 Post")
        self.post2 = create_post(self.user2, self.author2, "User2 Post")

        self.client1 = APIClient()
        self.client2 = APIClient()
        self.client1.force_authenticate(user=self.user1)
        self.client2.force_authenticate(user=self.user2)

    def test_user1_cannot_retrieve_user2_post(self):
        url = reverse("blogpostmodel-detail", args=[self.post2.id])
        res = self.client1.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_user1_cannot_patch_user2_post(self):
        url = reverse("blogpostmodel-detail", args=[self.post2.id])
        res = self.client1.patch(url, {"title": "Hacked Title"})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.post2.refresh_from_db()
        self.assertEqual(self.post2.title, "User2 Post")

    def test_user1_cannot_put_user2_post(self):
        url = reverse("blogpostmodel-detail", args=[self.post2.id])
        payload = {"title": "Hacked", "content": "Hacked", "author": self.author2.id}
        res = self.client1.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.post2.refresh_from_db()
        self.assertEqual(self.post2.title, "User2 Post")

    def test_user1_cannot_delete_user2_post(self):
        url = reverse("blogpostmodel-detail", args=[self.post2.id])
        res = self.client1.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(BlogPostModel.objects.filter(id=self.post2.id).exists())

    def test_user1_cannot_upload_image_to_user2_post(self):
        url = reverse("blogpostmodel-upload-image", args=[self.post2.id])
        res = self.client1.post(url, {}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_user_cannot_delete_post(self):
        unauthenticated = APIClient()
        url = reverse("blogpostmodel-detail", args=[self.post1.id])
        res = unauthenticated.delete(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(BlogPostModel.objects.filter(id=self.post1.id).exists())

    def test_unauthenticated_user_cannot_patch_post(self):
        unauthenticated = APIClient()
        url = reverse("blogpostmodel-detail", args=[self.post1.id])
        res = unauthenticated.patch(url, {"title": "Sneaky"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAuthorPermissions(TestCase):
    """User1 should not be able to modify or delete user2's authors."""

    def setUp(self):
        self.user1 = create_user("authperm1", "pass123")
        self.user2 = create_user("authperm2", "pass456")

        self.author1 = create_author(self.user1, "Author One", "one@perm.com")
        self.author2 = create_author(self.user2, "Author Two", "two@perm.com")

        self.client1 = APIClient()
        self.client2 = APIClient()
        self.client1.force_authenticate(user=self.user1)
        self.client2.force_authenticate(user=self.user2)

    def test_user1_cannot_retrieve_user2_author(self):
        url = reverse("authormodel-detail", args=[self.author2.id])
        res = self.client1.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_user1_cannot_patch_user2_author(self):
        url = reverse("authormodel-detail", args=[self.author2.id])
        res = self.client1.patch(url, {"name": "Hacked"})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.author2.refresh_from_db()
        self.assertEqual(self.author2.name, "Author Two")

    def test_user1_cannot_delete_user2_author(self):
        url = reverse("authormodel-detail", args=[self.author2.id])
        res = self.client1.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(AuthorModel.objects.filter(id=self.author2.id).exists())

    def test_unauthenticated_user_cannot_create_author(self):
        unauthenticated = APIClient()
        payload = {"name": "Anon", "email": "anon@example.com"}
        res = unauthenticated.post(AUTHOR_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
