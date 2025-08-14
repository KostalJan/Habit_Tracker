from datetime import date
import datetime as dt
from collections import defaultdict

from django.http import HttpResponse
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Habit, HabitLog
from .stats import compute_user_stats


class StatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = compute_user_stats(request.user)
        return Response({"habits": data})


from .models import Habit, HabitLog
from .permissions import IsOwner
from .serializers import (
    HabitLogCreateSerializer,
    HabitLogSerializer,
    HabitSerializer,
)


def home(_request):
    return HttpResponse("HabitTracker běží.")


class HabitViewSet(viewsets.ModelViewSet):
    """
    /api/habits/ — full CRUD nad vlastními návyky
    """
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user).order_by("id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HabitLogViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    /api/logs/ — list/retrieve/create/delete jen pro logy přihlášeného uživatele.
    Filtrování: habit_id, date__gte, date__lte, ordering (date/id).
    """
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
                pass

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

    def get_serializer_class(self):
        return HabitLogCreateSerializer if self.action == "create" else HabitLogSerializer

    http_method_names = ["get", "post", "delete", "head", "options"]
    

@login_required
def today_view(request):
    user = request.user
    today = dt.date.today()
    monday = today - dt.timedelta(days=today.weekday())

    habits = Habit.objects.filter(user=user).order_by("id")
    logs_today = {
        x["habit_id"]
        for x in HabitLog.objects.filter(habit__user=user, date=today).values("habit_id")
    }
    logs_this_week = defaultdict(int)
    for d, hid, val in HabitLog.objects.filter(habit__user=user, date__gte=monday, date__lte=today).values_list(
        "date", "habit_id", "value"
    ):
        logs_this_week[hid] += int(val)

    daily = []
    weekly = []
    for h in habits:
        if h.periodicity == Habit.Periodicity.DAILY:
            daily.append({"habit": h, "checked": h.id in logs_today})
        else:
            weekly.append({"habit": h, "count": logs_this_week.get(h.id, 0)})

    context = {"today": today, "daily": daily, "weekly": weekly}
    return render(request, "habits/today.html", context)


@login_required
def stats_page(request):
    data = compute_user_stats(request.user)
    return render(request, "habits/stats.html", {"stats": data})

