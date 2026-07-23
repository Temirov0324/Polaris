from django.urls import path

from . import views

app_name = "admin_agent"

urlpatterns = [
    path("", views.console, name="console"),
    path("message/", views.send_message, name="message"),
]
