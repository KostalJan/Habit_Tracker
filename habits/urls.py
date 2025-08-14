from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    HabitLogViewSet,
    HabitViewSet,
    StatisticsView,  # API /api/stats/
    home,
    stats_page,      # web stránka /stats/
    today_view,      # web stránka /today/
)

router = SimpleRouter()
router.register("api/habits", HabitViewSet, basename="habits")
router.register("api/logs", HabitLogViewSet, basename="logs")

urlpatterns = [
    path("", home, name="home"),
    path("today/", today_view, name="today"),
    path("stats/", stats_page, name="stats_page"),
    path("api/stats/", StatisticsView.as_view(), name="stats"),
    path("", include(router.urls)),
]
