from django.contrib import admin

from .models import Habit, HabitLog


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "name",
        "periodicity",
        "target_per_period",
        "created_at",
    )
    list_filter = ("periodicity", "created_at")
    search_fields = ("name", "user__username")
    autocomplete_fields = ("user",)


@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ("id", "habit", "date", "value", "created_at")
    list_filter = ("date",)
    search_fields = ("habite__name", "habit__user__username")
    autocomplete_fields = ("habit",)
    date_hierarchy = "date"
