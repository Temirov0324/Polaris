from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("messages/", views.ChatMessageListView.as_view(), name="chat-messages"),
    path("send/", views.ChatSendView.as_view(), name="chat-send"),
]
