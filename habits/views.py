import csv
import io

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
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

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
    

def _build_today_context(user):
    today = date.today()
    monday = today - dt.timedelta(days=today.weekday())

    habits = Habit.objects.filter(user=user).order_by("id")
    logs_today = {
        x["habit_id"]
        for x in HabitLog.objects.filter(habit__user=user, date=today).values("habit_id")
    }
    logs_this_week = defaultdict(int)
    for d, hid, val in HabitLog.objects.filter(
        habit__user=user, date__gte=monday, date__lte=today
    ).values_list("date", "habit_id", "value"):
        logs_this_week[hid] += int(val)

    daily, weekly = [], []
    for h in habits:
        if h.periodicity == Habit.Periodicity.DAILY:
            daily.append({"habit": h, "checked": h.id in logs_today})
        else:
            weekly.append({"habit": h, "count": logs_this_week.get(h.id, 0)})
    return {"today": today, "daily": daily, "weekly": weekly}


@login_required
def today_view(request):
    ctx = _build_today_context(request.user)
    # HTMX požadavek? vrať jen partial
    if request.headers.get("HX-Request") == "true":
        return render(request, "habits/_today_list.html", ctx)
    return render(request, "habits/today.html", ctx)


@login_required
def stats_page(request):
    data = compute_user_stats(request.user)
    return render(request, "habits/stats.html", {"stats": data})


@login_required
@require_POST
def toggle_today(request, habit_id: int):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    today = dt.date.today()

    # toggle dnešního logu
    existing = HabitLog.objects.filter(habit=habit, date=today).first()
    if existing:
        existing.delete()
    else:
        HabitLog.objects.create(habit=habit, date=today, value=1)

    ctx = _build_today_context(request.user)
    return render(request, "habits/_today_list.html", ctx)


@login_required
def export_logs_csv(request):
    """
    Stáhne CSV s logy přihlášeného uživatele.
    Filtry: ?habit_id=&date__gte=&date__lte=&ordering=(date|-date|id|-id)
    """
    qs = HabitLog.objects.select_related("habit").filter(habit__user=request.user)

    habit_id = request.GET.get("habit_id")
    if habit_id:
        try:
            qs = qs.filter(habit_id=int(habit_id))
        except ValueError:
            pass

    d_gte = request.GET.get("date__gte")
    if d_gte:
        try:
            qs = qs.filter(date__gte=date.fromisoformat(d_gte))
        except ValueError:
            pass

    d_lte = request.GET.get("date__lte")
    if d_lte:
        try:
            qs = qs.filter(date__lte=date.fromisoformat(d_lte))
        except ValueError:
            pass

    ordering = request.GET.get("ordering", "date")
    if ordering.lstrip("-") in {"date", "id"}:
        qs = qs.order_by(ordering)

    # CSV do paměti
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["habit_id", "habit_name", "date", "value"])
    for log in qs:
        writer.writerow([log.habit_id, log.habit.name, log.date.isoformat(), int(log.value)])

    content = buf.getvalue()

    # Odpověď s UTF-8 BOM (pro Excel)
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="logs.csv"'
    resp.write("\ufeff")  # BOM
    resp.write(content)
    return resp
