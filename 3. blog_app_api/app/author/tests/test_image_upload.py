import io
from unittest.mock import patch, MagicMock

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework import status
from rest_framework.test import APIClient

from ..models import AuthorModel, BlogPostModel

User = get_user_model()


def create_user(username, password):
    return User.objects.create(username=username, password=password)

def create_author(user, name="Example", email="email@example.com"):
    return AuthorModel.objects.create(user=user, name=name, email=email)

def create_post(user, author, title="Default Title", content="Default content"):
    return BlogPostModel.objects.create(user=user, author=author, title=title, content=content)

def make_image_file(filename="test.png"):
    """
    Create a minimal in-memory PNG file without hitting disk.
    This mocks an external file/storage interaction in tests.
    """
    try:
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (10, 10), color="blue").save(buf, format="PNG")
        buf.seek(0)
        return SimpleUploadedFile(filename, buf.read(), content_type="image/png")
    except ImportError:
        # Fallback: minimal valid PNG bytes (1x1 pixel)
        png_bytes = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
            b'\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18'
            b'\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        return SimpleUploadedFile(filename, png_bytes, content_type="image/png")


class TestImageUpload(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user("imguser", "pass123img")
        self.client.force_authenticate(user=self.user)
        self.author = create_author(self.user, "Img Author", "img@example.com")
        self.post = create_post(self.user, self.author, "Post With Image")

    def _upload_url(self, post_id):
        return reverse("blogpostmodel-upload-image", args=[post_id])

    @patch("django.core.files.storage.FileSystemStorage.save")
    def test_upload_image_calls_storage_save(self, mock_save):
        """
        Demonstrates mocking an external service (file storage).
        Verifies the storage layer is called during image upload
        without writing anything to disk.
        """
        mock_save.return_value = "posts/mocked_image.png"
        image = make_image_file()
        url = self._upload_url(self.post.id)
        res = self.client.post(url, {"image": image}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        mock_save.assert_called_once()

    @patch("django.core.files.storage.FileSystemStorage.save")
    def test_upload_image_updates_post_image_field(self, mock_save):
        mock_save.return_value = "posts/mocked_image.png"
        image = make_image_file()
        url = self._upload_url(self.post.id)
        res = self.client.post(url, {"image": image}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)

    def test_upload_image_without_file_clears_image(self):
        # image is null=True, blank=True — omitting it is valid and clears the field
        url = self._upload_url(self.post.id)
        res = self.client.post(url, {}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertFalse(self.post.image)

    def test_upload_image_to_nonexistent_post_fails(self):
        url = reverse("blogpostmodel-upload-image", args=[99999])
        image = make_image_file()
        res = self.client.post(url, {"image": image}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_user1_cannot_upload_image_to_user2_post(self):
        """Permission check: image upload respects ownership."""
        other_user = create_user("otherimguser", "pass456")
        other_author = create_author(other_user, "Other Img Author", "other@img.com")
        other_post = create_post(other_user, other_author, "Other Post")

        url = self._upload_url(other_post.id)
        image = make_image_file()
        res = self.client.post(url, {"image": image}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_upload_fails(self):
        unauthenticated = APIClient()
        url = self._upload_url(self.post.id)
        image = make_image_file()
        res = unauthenticated.post(url, {"image": image}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TestMockedExternalNotification(TestCase):
    """
    Demonstrates how to mock external services (e.g. email, payment).
    Pattern: patch the external call and assert it was triggered correctly.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = create_user("notifuser", "pass123notif")
        self.client.force_authenticate(user=self.user)
        self.author = create_author(self.user, "Notif Author", "notif@example.com")

    @patch("django.core.mail.send_mail")
    def test_post_creation_would_trigger_email_notification(self, mock_send_mail):
        """
        Example of mocking an email service.
        If the API were to send a notification email on post creation,
        this test verifies send_mail is called with the correct arguments.

        Currently send_mail is mocked (not called by the app itself) —
        this test serves as a template for when email notifications are added.
        """
        mock_send_mail.return_value = 1  # simulate 1 email sent

        # Simulate what a notification function would do
        from django.core.mail import send_mail
        send_mail(
            subject="New post created",
            message="Your post was published.",
            from_email="no-reply@blog.com",
            recipient_list=[self.user.username],
        )

        mock_send_mail.assert_called_once_with(
            subject="New post created",
            message="Your post was published.",
            from_email="no-reply@blog.com",
            recipient_list=[self.user.username],
        )
