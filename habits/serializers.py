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


class HabitLogCreateSerializer(serializers.ModelSerializer):
    """Používá se jen pro create – přidává business validace."""

    class Meta:
        model = HabitLog
        fields = ["id", "habit", "date", "value", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_value(self, value):
        if value < 1:
            raise serializers.ValidationError("value musí být >= 1.")
        return value

    def validate(self, attrs):
        """
        - habit musí patřit přihlášenému userovi
        - unique (habit, date) – aby nedošlo ke zdvojení logu
        """
        request = self.context.get("request")
        habit = attrs.get("habit")
        log_date = attrs.get("date")

        if request is None or request.user.is_anonymous:
            raise serializers.ValidationError("Nepřihlášený uživatel.")

        if habit is None:
            raise serializers.ValidationError({"habit": "Povinné pole."})

        # habit patří uživateli?
        if habit.user_id != request.user.id:
            raise serializers.ValidationError({"habit": "Tento zvyk ti nepatří."})

        # duplicita
        if log_date is not None and HabitLog.objects.filter(habit=habit, date=log_date).exists():
            raise serializers.ValidationError(
                {"date": "Pro tento den už záznam existuje."}
            )

        return attrs