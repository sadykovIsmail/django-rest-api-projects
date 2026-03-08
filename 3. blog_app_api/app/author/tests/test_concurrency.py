import threading
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import connection

from ..models import AuthorModel, BlogPostModel

User = get_user_model()


def create_user(username, password):
    return User.objects.create(username=username, password=password)

def create_author(user, name="Example", email="email@example.com"):
    return AuthorModel.objects.create(user=user, name=name, email=email)


class TestConcurrentPostCreation(TransactionTestCase):
    """
    Simulate concurrent requests to verify no data loss or corruption
    when multiple posts are created simultaneously for the same user.

    Uses TransactionTestCase (instead of TestCase) so each thread can
    open its own database connection and see committed data.
    """

    def setUp(self):
        self.user = create_user("concuser", "pass123conc")
        self.author = create_author(self.user, "ConcAuthor", "conc@example.com")

    def test_concurrent_post_creation_no_data_loss(self):
        errors = []
        results = []
        lock = threading.Lock()

        def create():
            try:
                post = BlogPostModel.objects.create(
                    user=self.user,
                    author=self.author,
                    title=f"Post by {threading.current_thread().name}",
                    content="concurrent content",
                )
                with lock:
                    results.append(post.id)
            except Exception as e:
                with lock:
                    errors.append(str(e))
            finally:
                # Close the thread-local DB connection to avoid leaks
                connection.close()

        threads = [threading.Thread(target=create, name=f"Thread-{i}") for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Errors during concurrent creation: {errors}")
        self.assertEqual(len(results), 5, "Expected 5 posts to be created")
        self.assertEqual(
            BlogPostModel.objects.filter(user=self.user).count(), 5
        )

    def test_concurrent_author_creation_no_data_loss(self):
        errors = []
        results = []
        lock = threading.Lock()

        def create(index):
            try:
                author = AuthorModel.objects.create(
                    user=self.user,
                    name=f"Author {index}",
                    email=f"author{index}@example.com",
                )
                with lock:
                    results.append(author.id)
            except Exception as e:
                with lock:
                    errors.append(str(e))
            finally:
                connection.close()

        threads = [threading.Thread(target=create, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Errors: {errors}")
        # +1 because setUp already created one author
        self.assertEqual(AuthorModel.objects.filter(user=self.user).count(), 6)

    def test_concurrent_reads_return_consistent_data(self):
        """Multiple threads reading posts simultaneously should all see the same data."""
        for i in range(3):
            BlogPostModel.objects.create(
                user=self.user,
                author=self.author,
                title=f"Existing Post {i}",
                content="content",
            )

        counts = []
        errors = []
        lock = threading.Lock()

        def read():
            try:
                count = BlogPostModel.objects.filter(user=self.user).count()
                with lock:
                    counts.append(count)
            except Exception as e:
                with lock:
                    errors.append(str(e))
            finally:
                connection.close()

        threads = [threading.Thread(target=read) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        # All threads should see the same count
        self.assertTrue(all(c == 3 for c in counts), f"Inconsistent reads: {counts}")
