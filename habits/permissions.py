from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Habit, HabitLog


class IsOwner(BasePermission):
    """
    Umožní jen vlastníkovi čtení a zápis objektu.
    Souběžně filtruje querysety podle přihlášeného uživatele.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Habit):
            return obj.user_id == request.user.id
        if isinstance(obj, HabitLog):
            return obj.habit.user_id == request.user.id
        return False
