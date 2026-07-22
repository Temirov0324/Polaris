from django.http import HttpResponse
from django.views.decorators.http import require_GET

# Deliberately a pure network passthrough — no caching. This project has
# already dealt with painful stale-static-asset bugs during dev; a caching
# service worker would reintroduce that class of bug for every user, not
# just during development. The only reason this exists is that Chrome's
# "Add to Home Screen" installability check requires a registered fetch
# handler alongside the manifest.
SERVICE_WORKER_JS = """
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));
self.addEventListener("fetch", (event) => {
  event.respondWith(fetch(event.request));
});
""".strip()


@require_GET
def service_worker(request):
    return HttpResponse(SERVICE_WORKER_JS, content_type="application/javascript")
