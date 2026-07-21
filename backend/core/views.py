from pathlib import Path

from django.conf import settings
from django.views.generic import TemplateView


def _static_version() -> str:
    """Latest mtime across the static tree, recomputed every request in
    DEBUG. Used to cache-bust asset URLs so a browser reload always picks
    up CSS/JS edits — no manual hard-refresh needed, even mid-SPA-session
    on the next full navigation."""
    static_dir = Path(settings.BASE_DIR) / "frontend" / "static"
    try:
        return str(int(max(p.stat().st_mtime for p in static_dir.rglob("*") if p.is_file())))
    except ValueError:
        return "0"


class FrontendAppView(TemplateView):
    """Serves the SPA-lite shell for every non-API route so the
    hash-router (frontend/static/js/router.js) can take over client-side."""

    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["static_version"] = _static_version() if settings.DEBUG else "1"
        return context
