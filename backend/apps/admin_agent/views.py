import json

from django.contrib import admin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .services.agent import handle_message

HISTORY_SESSION_KEY = "admin_agent_history"


def _is_superuser(user):
    return user.is_active and user.is_superuser


@login_required(login_url="/admin/login/")
@user_passes_test(_is_superuser, login_url="/admin/login/")
def console(request):
    # This is a plain Django view, not a ModelAdmin one, so it never goes
    # through AdminSite.each_context() on its own — without it, Jazzmin's
    # base template has no `available_apps` and renders an empty sidebar.
    context = admin.site.each_context(request)
    context["history"] = request.session.get(HISTORY_SESSION_KEY, [])
    return render(request, "admin_agent/console.html", context)


@login_required(login_url="/admin/login/")
@user_passes_test(_is_superuser, login_url="/admin/login/")
@require_POST
def send_message(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Noto'g'ri so'rov"}, status=400)

    if payload.get("reset"):
        request.session[HISTORY_SESSION_KEY] = []
        return JsonResponse({"history": []})

    message = (payload.get("message") or "").strip()
    if not message:
        return JsonResponse({"error": "Xabar bo'sh bo'lishi mumkin emas"}, status=400)

    history = request.session.get(HISTORY_SESSION_KEY, [])
    result = handle_message(request.user, message, history)
    request.session[HISTORY_SESSION_KEY] = result["history"]
    return JsonResponse(result)
