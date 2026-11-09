from django.urls import path
from apps.problems.views import ProblemListPageView

app_name = "problems_frontend"

urlpatterns = [
    path("problems/", ProblemListPageView.as_view(), name="list"),
]