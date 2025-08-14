from datetime import date

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Habit, HabitLog
from .permissions import IsOwner
from .serializers import HabitLogSerializer, HabitSerializer


def home(_request):
    return HttpResponse("HabitTracker Mini – běží.")


class HabitViewSet(ReadOnlyModelViewSet):
    """
    /api/habits/ — list/retrieve jen vlastních návyků
    """
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user).order_by("id")


class HabitLogViewSet(ReadOnlyModelViewSet):
    """
    /api/logs/?habit_id=&date__gte=&date__lte=&ordering=-date
    Vrací pouze logy patřící přihlášenému uživateli.
    """
    serializer_class = HabitLogSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        qs = HabitLog.objects.select_related("habit").filter(
            habit__user=self.request.user
        )

        habit_id = self.request.query_params.get("habit_id")
        if habit_id:
            try:
                qs = qs.filter(habit_id=int(habit_id))
            except ValueError:
                pass  # ignorování nevalidního vstupu

        d_gte = self.request.query_params.get("date__gte")
        if d_gte:
            try:
                qs = qs.filter(date__gte=date.fromisoformat(d_gte))
            except ValueError:
                pass

        d_lte = self.request.query_params.get("date__lte")
        if d_lte:
            try:
                qs = qs.filter(date__lte=date.fromisoformat(d_lte))
            except ValueError:
                pass

        ordering = self.request.query_params.get("ordering", "-date")
        if ordering.lstrip("-") in {"date", "id"}:
            qs = qs.order_by(ordering)

        return qs
