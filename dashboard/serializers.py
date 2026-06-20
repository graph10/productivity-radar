from rest_framework import serializers
from .models import Habit, Entry


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = ["id", "name", "color", "created_at"]


class EntrySerializer(serializers.ModelSerializer):
    habit_name = serializers.CharField(source="habit.name", read_only=True)
    habit_color = serializers.CharField(source="habit.color", read_only=True)

    class Meta:
        model = Entry
        fields = ["id", "habit", "habit_name", "habit_color", "date", "completed", "energy"]
