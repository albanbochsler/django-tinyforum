from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import Client, TestCase

from tinyforum.models import Thread


def messages(response):
    return [m.message for m in get_messages(response.wsgi_request)]


class ForumTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = User.objects.create_superuser(
            "admin", "admin@example.com", "password"
        )
        cls.user1 = User.objects.create_user("user1", "user1@example.com", "password")
        cls.user2 = User.objects.create_user("user2", "user2@example.com", "password")

    def test_posting_a_bit(self):
        c = Client()
        c.force_login(self.user1)
        response = c.get("/")
        # print(response.content.decode("utf-8"))

        response = c.post(
            "/create/", {"title": "Thread title", "text": "<p>Frsit psot.</p>"}
        )
        thread = Thread.objects.get()
        self.assertRedirects(response, thread.get_absolute_url())
        self.assertEqual(thread.authored_by, self.user1)

        response = c.get(thread.get_absolute_url())
        self.assertContains(response, "Frsit psot.")

        response = c.get(thread.get_absolute_url() + "update/")
        self.assertEqual(response.status_code, 200)

        c = Client()
        c.force_login(self.user2)
        response = c.post(thread.get_absolute_url(), {"text": "<p>Second!</p>"})
        self.assertRedirects(response, "%s?page=last" % thread.get_absolute_url())

        response = c.get(thread.get_absolute_url() + "update/")
        self.assertRedirects(response, thread.get_absolute_url())
        self.assertEqual(messages(response), ["Sorry, you do not have permissions."])

        c = Client()
        c.force_login(self.user1)
        response = c.get(thread.get_absolute_url() + "update/")
        self.assertContains(response, 'for="id_close_thread"')

        response = c.post(
            thread.get_absolute_url() + "update/",
            {"title": thread.title, "close_thread": True},
        )
        self.assertRedirects(response, thread.get_absolute_url())

        thread.refresh_from_db()
        self.assertFalse(thread.closed_at is None)

        response = c.get(thread.get_absolute_url() + "update/")
        self.assertNotContains(response, 'for="id_close_thread"')

        response = c.get("/?status=closed")
        self.assertContains(response, '<a href="/%s/?page=last">' % thread.pk)

    def test_thread_list(self):
        Thread.objects.create(title="One", authored_by=self.user1)
        Thread.objects.create(title="Two", authored_by=self.user1)

        c = Client()
        response = c.get("/")
        self.assertContains(response, "data-set-status", 0)

        c.force_login(self.user2)
        response = c.get("/")
        self.assertContains(response, "data-set-status", 2)
        # print(response.content.decode("utf-8"))

    def test_thread_update(self):
        t = Thread.objects.create(title="One", authored_by=self.user1)

        c = Client()
        c.force_login(self.user1)
        response = c.post(t.get_absolute_url() + "update/", {"title": "Two"})
        self.assertRedirects(response, t.get_absolute_url())
        self.assertEqual(messages(response), [])

        t.refresh_from_db()
        self.assertEqual(t.title, "Two")

        c.force_login(self.user2)
        response = c.post(t.get_absolute_url() + "update/", {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(messages(response), ["Sorry, you do not have permissions."])

    def test_anonymous(self):
        c = Client()
        self.assertEqual(c.get("/").status_code, 200)
        self.assertRedirects(c.get("/create/"), "/accounts/login/?next=/create/")

        t = Thread.objects.create(title="Test", authored_by=self.user1)
        self.assertEqual(c.get(t.get_absolute_url()).status_code, 200)
        self.assertEqual(c.get(t.get_absolute_url() + "update/").status_code, 302)
        self.assertEqual(c.get(t.get_absolute_url() + "star/").status_code, 302)

    def test_user(self):
        c = Client()
        c.force_login(self.user1)
        response = c.get("/moderation/")
        self.assertRedirects(response, "/")
        self.assertEqual(messages(response), ["You do not have moderation powers."])

    def test_moderator(self):
        c = Client()
        c.force_login(self.admin)
        self.assertEqual(c.get("/moderation/").status_code, 200)
