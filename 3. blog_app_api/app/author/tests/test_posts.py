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

def create_post(user, author, title="Default Title", content="Default content"):
    return BlogPostModel.objects.create(user=user, author=author, title=title, content=content)


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

    def test_create_post_without_author_fails(self):
        # author is required — sending without it should return 400
        payload = {
            "title": "No Author Post",
            "content": "hello",
        }
        res = self.client.post(BLOG_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_assigned_from_token_not_payload(self):
        # user should come from the token, not from whatever the client sends
        payload = {
            "title": "Token Test",
            "content": "hello",
            "author": self.author.id,
        }
        res = self.client.post(BLOG_LIST_LINK, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        post = BlogPostModel.objects.get(id=res.data["id"])
        self.assertEqual(post.user, self.user)

    def test_get_posts_returns_only_own(self):
        # GET /api/posts/ should return only the logged-in user's posts
        other_user = create_user(usernane="other", password="other123")
        other_author = create_author(other_user, "Other Author", "other@example.com")

        create_post(user=self.user, author=self.author, title="My Post")
        create_post(user=other_user, author=other_author, title="Other Post")

        res = self.client.get(BLOG_LIST_LINK)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["title"], "My Post")


class test_post_isolation(TestCase):
    # two users — neither should be able to touch the other's posts
    def setUp(self):
        self.user1 = create_user(usernane="user1", password="user1pass")
        self.user2 = create_user(usernane="user2", password="user2pass")

        self.author1 = create_author(self.user1, "Author One", "one@example.com")
        self.author2 = create_author(self.user2, "Author Two", "two@example.com")

        self.post1 = create_post(user=self.user1, author=self.author1, title="User1 Post")
        self.post2 = create_post(user=self.user2, author=self.author2, title="User2 Post")

        self.client1 = APIClient()
        self.client2 = APIClient()
        self.client1.force_authenticate(user=self.user1)
        self.client2.force_authenticate(user=self.user2)

    def test_user1_sees_only_own_posts(self):
        res = self.client1.get(BLOG_LIST_LINK)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["title"], "User1 Post")

    def test_user2_sees_only_own_posts(self):
        res = self.client2.get(BLOG_LIST_LINK)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["title"], "User2 Post")

    def test_user1_cannot_delete_user2_post(self):
        # post2 belongs to user2 — user1 should get 404 (invisible, not just forbidden)
        url = reverse("blogpostmodel-detail", args=[self.post2.id])
        res = self.client1.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        # confirm post2 still exists
        self.assertTrue(BlogPostModel.objects.filter(id=self.post2.id).exists())
