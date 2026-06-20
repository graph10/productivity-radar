from django.contrib import admin
from .models import Habit, Entry


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ["name", "color", "created_at"]
    search_fields = ["name"]


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ["habit", "date", "completed", "energy"]
    list_filter = ["completed", "date", "habit"]
    search_fields = ["habit__name"]
    date_hierarchy = "date"
