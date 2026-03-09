import threading
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import connection

from ..models import Note, Category, Tag

User = get_user_model()


def create_user(username, password):
    return User.objects.create(username=username, password=password)

def create_category(user, name="Default Category"):
    return Category.objects.create(user=user, name=name)

def create_tag(user, name="Default Tag"):
    return Tag.objects.create(user=user, name=name)


class TestConcurrentNoteCreation(TransactionTestCase):
    """
    Simulate concurrent requests to verify no data loss or corruption
    when multiple notes are created simultaneously for the same user.

    Uses TransactionTestCase (instead of TestCase) so each thread can
    open its own database connection and see committed data.
    """

    def setUp(self):
        self.user = create_user("concnoteuser", "pass123conc")
        self.category = create_category(self.user, "Conc Category")

    def test_concurrent_note_creation_no_data_loss(self):
        errors = []
        results = []
        lock = threading.Lock()

        def create():
            try:
                note = Note.objects.create(
                    user=self.user,
                    category=self.category,
                    title=f"Note by {threading.current_thread().name}",
                    content="concurrent content",
                )
                with lock:
                    results.append(note.id)
            except Exception as e:
                with lock:
                    errors.append(str(e))
            finally:
                connection.close()

        threads = [threading.Thread(target=create, name=f"Thread-{i}") for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Errors during concurrent creation: {errors}")
        self.assertEqual(len(results), 5, "Expected 5 notes to be created")
        self.assertEqual(Note.objects.filter(user=self.user).count(), 5)

    def test_concurrent_category_creation_no_data_loss(self):
        errors = []
        results = []
        lock = threading.Lock()

        def create(index):
            try:
                cat = Category.objects.create(
                    user=self.user,
                    name=f"Category {index}",
                )
                with lock:
                    results.append(cat.id)
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
        # +1 because setUp already created one category
        self.assertEqual(Category.objects.filter(user=self.user).count(), 6)

    def test_concurrent_tag_creation_no_data_loss(self):
        errors = []
        results = []
        lock = threading.Lock()

        def create(index):
            try:
                tag = Tag.objects.create(
                    user=self.user,
                    name=f"Tag {index}",
                )
                with lock:
                    results.append(tag.id)
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
        self.assertEqual(Tag.objects.filter(user=self.user).count(), 5)

    def test_concurrent_reads_return_consistent_data(self):
        """Multiple threads reading notes simultaneously should all see the same data."""
        for i in range(3):
            Note.objects.create(
                user=self.user,
                category=self.category,
                title=f"Existing Note {i}",
                content="content",
            )

        counts = []
        errors = []
        lock = threading.Lock()

        def read():
            try:
                count = Note.objects.filter(user=self.user).count()
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
        self.assertTrue(all(c == 3 for c in counts), f"Inconsistent reads: {counts}")
