from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from tinyforum.models import Thread, Post


class BaseForm(forms.Form):
    required_css_class = 'required'
    error_css_class = 'error'

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)


class CreateThreadForm(BaseForm, forms.ModelForm):
    class Meta:
        model = Thread
        fields = ('title',)


class UpdateThreadForm(BaseForm, forms.ModelForm):
    close_thread = forms.BooleanField(
        label=_('Close thread'),
        required=False,
    )

    class Meta:
        model = Thread
        fields = ('title',)

    def save(self):
        instance = super().save(commit=False)
        if self.cleaned_data.get('close_thread'):
            instance.closed_at = timezone.now()
        instance.save()
        return instance


class ModerateThreadForm(BaseForm, forms.ModelForm):
    class Meta:
        model = Thread
        fields = ('title', 'is_pinned', 'moderation_status')


def form_for_thread(request, instance, moderation=False):
    kw = {
        'data': request.POST if request.method == 'POST' else None,
        'request': request,
        'instance': instance,
    }
    if moderation:
        return ModerateThreadForm(**kw)
    elif instance and request.user == instance.authored_by:
        return UpdateThreadForm(**kw)
    elif instance is None:
        return CreateThreadForm(**kw)
    return None


class CreatePostForm(BaseForm, forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text',)


class UpdatePostForm(BaseForm, forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text',)


class ModeratePostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'moderation_status')


def form_for_post(request, instance, moderation=False):
    kw = {
        'data': request.POST if request.method == 'POST' else None,
        'request': request,
        'instance': instance,
    }
    if moderation:
        return ModeratePostForm(**kw)
    elif instance and request.user == instance.authored_by:
        return UpdatePostForm(**kw)
    elif instance is None:
        return CreatePostForm(**kw)
    return None
