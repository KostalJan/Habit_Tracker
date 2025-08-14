from django.http import HttpResponse
from django.urls import path


def home(_request):
    return HttpResponse("Habit Tracker běží")


urlpatterns = [path("", home, name="home")]
