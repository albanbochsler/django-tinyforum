from functools import wraps

from django.conf.urls import url
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from tinyforum import views


def moderator_required(fn):
    @login_required
    def view(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "You do not have moderation powers.")
            return redirect("tinyforum:thread-list")
        return fn(request, *args, **kwargs)

    return view


def moderation(fn):
    @wraps(fn)
    def dec(request, *args, **kwargs):
        # kwargs["moderation"] = request.user.profile.has_moderation_powers
        kwargs["moderation"] = request.user.is_staff
        return fn(request, *args, **kwargs)

    return dec


app_name = "tinyforum"
urlpatterns = [
    url(r"^$", views.thread_list, name="thread-list"),
    url(
        r"^create/$",
        login_required(moderation(views.thread_form)),
        name="thread-create",
    ),
    url(r"^(?P<pk>[0-9]+)/$", views.post_list, name="thread-detail"),
    url(
        r"^(?P<pk>[0-9]+)/update/$",
        login_required(moderation(views.thread_form)),
        name="thread-update",
    ),
    url(
        r"^(?P<pk>[0-9]+)/star/$", login_required(views.thread_star), name="thread-star"
    ),
    url(
        r"^post/(?P<pk>[0-9]+)/update/$",
        login_required(moderation(views.post_form)),
        name="post-update",
    ),
    url(
        r"^post/(?P<pk>[0-9]+)/report/$",
        login_required(views.post_report),
        name="post-report",
    ),
    url(r"^moderation/$", moderator_required(views.report_list), name="report-list"),
    url(
        r"^moderation/(?P<pk>[0-9]+)/$",
        moderator_required(views.report_handle),
        name="report-handle",
    ),
]