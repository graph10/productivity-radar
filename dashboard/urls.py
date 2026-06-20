from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/habits/", views.habits_list, name="habits-list"),
    path("api/habits/create/", views.habits_create, name="habits-create"),
    path("api/stats/", views.stats, name="stats"),
    path("api/check/", views.check_habit, name="check-habit"),
    path("api/entries/", views.entries_list, name="entries-list"),
]
