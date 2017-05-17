from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _

from ckeditor.fields import RichTextField
from html_sanitizer.django import get_sanitizer


class BaseQuerySet(models.QuerySet):
    def visible(self):
        return self.exclude(moderation_status=self.model.HIDDEN)


class BaseModel(models.Model):
    GOOD = 'good'
    FLAGGED = 'flagged'
    COLLAPSED = 'collapsed'
    HIDDEN = 'hidden'

    MODERATION_STATUS_CHOICES = (
        (GOOD, _('good')),
        (FLAGGED, _('flagged')),
        (COLLAPSED, _('collapsed')),
        (HIDDEN, _('hidden')),
    )

    created_at = models.DateTimeField(
        _('created at'),
        default=timezone.now,
    )
    authored_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('authored by'),
    )
    moderation_status = models.CharField(
        _('moderation status'),
        max_length=10,
        choices=MODERATION_STATUS_CHOICES,
        default=GOOD,
    )

    objects = BaseQuerySet.as_manager()

    class Meta:
        abstract = True


class ThreadQuerySet(BaseQuerySet):
    def active(self):
        return self.visible().filter(closed_at__isnull=True)


class Thread(BaseModel):
    title = models.CharField(
        _('title'),
        max_length=200,
    )
    is_pinned = models.BooleanField(
        _('is pinned'),
        default=False,
    )
    closed_at = models.DateTimeField(
        _('closed at'),
        blank=True,
        null=True,
    )

    latest_post = models.OneToOneField(
        'Post',
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True,
        verbose_name=_('latest post'),
    )
    post_count = models.IntegerField(
        _('post count'),
        default=0,
    )

    objects = ThreadQuerySet.as_manager()

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = _('thread')
        verbose_name_plural = _('threads')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('tinyforum:thread-detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if self.pk:
            self.post_count = self.posts.visible().count()
            self.latest_post = self.posts.visible().last()
        super().save(*args, **kwargs)
    save.alters_data = True


class Post(BaseModel):
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        verbose_name=_('thread'),
        related_name='posts',
    )
    text = RichTextField(
        _('text'),
        config_name='tinyforum-post',
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = _('post')
        verbose_name_plural = _('post')

    def __str__(self):
        return Truncator(strip_tags(self.text)).words(20, truncate='...')

    def clean(self):
        super().clean()
        self.text = get_sanitizer('tinyforum-post').sanitize(self.text)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.thread.save()
    save.alters_data = True
