from django.conf import settings
from django.db import models


class Habit(models.Model):
    class Periodicity(models.TextChoices):
        DAILY = "daily", "Denně"
        WEEKLY = "weekly", "Týdně"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="habits"
    )
    name = models.CharField(max_length=100)
    periodicity = models.CharField(
        max_length=10, choices=Periodicity.choices, default=Periodicity.DAILY
    )
    target_per_period = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} ({self.get_periodicity_display()})"


class HabitLog(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name="logs")
    date = models.DateField(db_index=True)
    value = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        constraints = [
            # omezení na max 1 log za den
            models.UniqueConstraint(fields=["habit", "date"], name="unique_log_per_day")
        ]

    def __str__(self):
        return f"{self.habit.name} @ {self.date} (+{self.value})"
