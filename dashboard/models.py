from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Habit(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    color = models.CharField(max_length=7, default="#3B82F6", verbose_name="Цвет")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class Entry(models.Model):
    habit = models.ForeignKey(
        Habit, on_delete=models.CASCADE, related_name="entries", verbose_name="Привычка"
    )
    date = models.DateField(verbose_name="Дата")
    completed = models.BooleanField(default=False, verbose_name="Выполнено")
    energy = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Энергия",
    )

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        unique_together = ["habit", "date"]
        ordering = ["-date"]

    def __str__(self) -> str:
        status = "✓" if self.completed else "○"
        return f"{status} {self.habit.name} — {self.date}"
