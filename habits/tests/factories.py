import factory
from django.contrib.auth import get_user_model

from habits.models import Habit, HabitLog

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.sequence(lambda n: f"user{n}")


class HabitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Habit

    user = factory.SubFactory(UserFactory)
    name = factory.Faker("word")
    periodicity = Habit.Periodicity.DAILY
    target_per_period = 1


class HabitLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HabitLog

    habit = factory.SubFactory(HabitFactory)
    date = factory.Faker("date_this_year")
    value = 1
