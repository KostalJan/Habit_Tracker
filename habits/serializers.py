from rest_framework import serializers
from .models import Habit, HabitLog


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = ["id", "name", "periodicity", "target_per_period", "created_at"]
        read_only_fields = ["id", "created_at"]


class HabitLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitLog
        fields = ["id", "habit", "date", "value", "created_at"]
        read_only_fields = ["id", "created_at"]
