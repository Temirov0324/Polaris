from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.serviceworker import service_worker
from core.views import FrontendAppView

admin.site.site_header = "PolarisAI boshqaruv paneli"
admin.site.site_title = "PolarisAI Admin"
admin.site.index_title = "Boshqaruv"

api_v1_patterns = [
    path("auth/", include("apps.users.urls")),
    path("destinations/", include("apps.destinations.urls")),
    path("", include("apps.trips.urls")),
    path("", include("apps.savings.urls")),
    path("chat/", include("apps.chat.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Served from the root path (not /static/) so its default scope covers
    # the whole origin -- a service worker under /static/ would only be
    # allowed to control /static/* without extra response headers.
    path("sw.js", service_worker, name="service-worker"),
    # Everything else is handled client-side by the SPA-lite router.
    re_path(r"^(?!api/|admin/|static/).*$", FrontendAppView.as_view(), name="frontend"),
]
