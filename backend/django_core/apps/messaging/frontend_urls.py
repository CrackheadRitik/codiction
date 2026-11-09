from django.urls import path
from apps.messaging.views import MessagingPageView

app_name = "messaging_frontend"

urlpatterns = [
    path("messages/", MessagingPageView.as_view(), name="list"),
]