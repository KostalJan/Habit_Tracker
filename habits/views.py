from datetime import date

from django.http import HttpResponse
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

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
    return HttpResponse("HabitTracker Mini – běží.")


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

