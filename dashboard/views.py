import json
from datetime import date, timedelta
from collections import defaultdict
from django.shortcuts import render
from django.db.models import Avg
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Habit, Entry
from .serializers import HabitSerializer, EntrySerializer


def index(request):
    """Главная страница дашборда."""
    habits = Habit.objects.all()
    today = date.today()
    week_ago = today - timedelta(days=6)

    entries = Entry.objects.filter(date__gte=week_ago)
    entries_by_day: dict = defaultdict(list)
    for e in entries:
        entries_by_day[e.date.isoformat()].append(e)

    week_data = []
    for i in range(7):
        d = week_ago + timedelta(days=i)
        day_entries = entries_by_day.get(d.isoformat(), [])
        total = len(day_entries)
        done = sum(1 for e in day_entries if e.completed)
        week_data.append({
            "date": d.isoformat(),
            "label": d.strftime("%a"),
            "total": total,
            "done": done,
            "rate": round(done / total * 100, 1) if total else 0,
        })

    habits_data = HabitSerializer(habits, many=True).data
    context = {
        "habits": json.dumps(habits_data),
        "today": today.isoformat(),
        "week_data": week_data,
    }
    return render(request, "dashboard/index.html", context)


@api_view(["GET"])
def habits_list(request):
    """GET /api/habits/ — список всех привычек."""
    habits = Habit.objects.all()
    serializer = HabitSerializer(habits, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def habits_create(request):
    """POST /api/habits/ — создать привычку."""
    serializer = HabitSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def stats(request):
    """GET /api/stats/ — общая статистика."""
    today = date.today()
    week_ago = today - timedelta(days=6)
    month_ago = today - timedelta(days=29)

    all_entries = Entry.objects.all()
    total_entries = all_entries.count()
    completed_entries = all_entries.filter(completed=True).count()
    completion_rate = round(completed_entries / total_entries * 100, 1) if total_entries else 0

    avg_energy = all_entries.aggregate(avg=Avg("energy"))["avg"] or 0

    weekday_stats = defaultdict(lambda: {"total": 0, "done": 0, "energy_sum": 0, "energy_count": 0})
    for entry in all_entries:
        wd = entry.date.weekday()
        weekday_stats[wd]["total"] += 1
        if entry.completed:
            weekday_stats[wd]["done"] += 1
        weekday_stats[wd]["energy_sum"] += entry.energy
        weekday_stats[wd]["energy_count"] += 1

    best_day = None
    best_rate = -1
    for wd in range(7):
        s = weekday_stats[wd]
        rate = s["done"] / s["total"] if s["total"] else 0
        if rate > best_rate:
            best_rate = rate
            best_day = wd

    days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    best_day_name = days_ru[best_day] if best_day is not None else "—"

    week_entries = Entry.objects.filter(date__gte=week_ago).order_by("date")
    daily_stats: dict = defaultdict(lambda: {"done": 0, "total": 0, "energy": []})
    for e in week_entries:
        key = e.date.isoformat()
        daily_stats[key]["total"] += 1
        if e.completed:
            daily_stats[key]["done"] += 1
        daily_stats[key]["energy"].append(e.energy)

    activity_chart = []
    for i in range(7):
        d = week_ago + timedelta(days=i)
        key = d.isoformat()
        s = daily_stats.get(key, {"done": 0, "total": 0, "energy": []})
        activity_chart.append({
            "date": key,
            "label": d.strftime("%d.%m"),
            "rate": round(s["done"] / s["total"] * 100, 1) if s["total"] else 0,
            "energy": round(sum(s["energy"]) / len(s["energy"]), 1) if s["energy"] else 0,
        })

    habits_count = Habit.objects.count()
    month_entries = Entry.objects.filter(date__gte=month_ago, completed=True).count()

    return Response({
        "completion_rate": completion_rate,
        "best_day": best_day_name,
        "best_day_rate": round(best_rate * 100, 1) if best_day is not None else 0,
        "avg_energy": round(avg_energy, 1),
        "total_habits": habits_count,
        "total_entries": total_entries,
        "completed_entries": completed_entries,
        "month_completed": month_entries,
        "activity_chart": activity_chart,
        "weekday_breakdown": [
            {
                "day": days_ru[wd],
                "total": weekday_stats[wd]["total"],
                "done": weekday_stats[wd]["done"],
                "rate": round(weekday_stats[wd]["done"] / weekday_stats[wd]["total"] * 100, 1) if weekday_stats[wd]["total"] else 0,
                "avg_energy": round(weekday_stats[wd]["energy_sum"] / weekday_stats[wd]["energy_count"], 1) if weekday_stats[wd]["energy_count"] else 0,
            }
            for wd in range(7)
        ],
    })


@api_view(["POST"])
def check_habit(request):
    """POST /api/check/ — отметить привычку выполненной."""
    habit_id = request.data.get("habit_id")
    entry_date = request.data.get("date")
    completed = request.data.get("completed", True)
    energy = request.data.get("energy", 3)

    if not habit_id or not entry_date:
        return Response(
            {"error": "habit_id и date обязательны"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        habit = Habit.objects.get(pk=habit_id)
    except Habit.DoesNotExist:
        return Response(
            {"error": "Привычка не найдена"},
            status=status.HTTP_404_NOT_FOUND,
        )

    entry, _ = Entry.objects.update_or_create(
        habit=habit,
        date=entry_date,
        defaults={"completed": completed, "energy": energy},
    )

    serializer = EntrySerializer(entry)
    return Response(serializer.data)


@api_view(["GET"])
def entries_list(request):
    """GET /api/entries/ — записи за период."""
    habit_id = request.query_params.get("habit_id")
    from_date = request.query_params.get("from")
    to_date = request.query_params.get("to")

    queryset = Entry.objects.all()
    if habit_id:
        queryset = queryset.filter(habit_id=habit_id)
    if from_date:
        queryset = queryset.filter(date__gte=from_date)
    if to_date:
        queryset = queryset.filter(date__lte=to_date)

    serializer = EntrySerializer(queryset[:100], many=True)
    return Response(serializer.data)
