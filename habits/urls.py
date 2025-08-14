from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import HabitLogViewSet, HabitViewSet, home

router = SimpleRouter()
router.register("api/habits", HabitViewSet, basename="habits")
router.register("api/logs", HabitLogViewSet, basename="logs")

urlpatterns = [
    path("", home, name="home"),
    path("", include(router.urls)),
]
