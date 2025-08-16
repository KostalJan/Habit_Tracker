from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    HabitLogViewSet,
    HabitViewSet,
    StatisticsView, 
    home,
    stats_page,      
    today_view,   
    toggle_today ,
    export_logs_csv  
)

router = SimpleRouter()
router.register("api/habits", HabitViewSet, basename="habits")
router.register("api/logs", HabitLogViewSet, basename="logs")

urlpatterns = [
    path("", home, name="home"),
    path("today/", today_view, name="today"),
    path("today/toggle/<int:habit_id>/", toggle_today, name="toggle_today"),
    path("stats/", stats_page, name="stats_page"),
    path("api/stats/", StatisticsView.as_view(), name="stats"),
    path("export/logs.csv", export_logs_csv, name="export_logs"),
    path("", include(router.urls)),
]
