from __future__ import annotations

import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from habits.models import Habit, HabitLog

daily_names = [
    "Čtení",
    "Meditace",
    "Pitný režim",
    "Protažení",
    "Vitamíny",
    "Psaní deníku",
]
weekly_names = [
    "Běh",
    "Cvičení",
    "Zavolat rodičům",
    "Hloubkový úklid",
    "Příprava jídel",
    "Turistika",
]


class Command(BaseCommand):
    help = (
        "Vytvoří demo uživatele, návyky a logy.\n"
        "Příklad: manage.py fill_demo_data --user demo --habits 6 --days 60 --seed 42 --reset\n"
        "Pozn.: pokud uživatel neexistuje, nastaví mu heslo 'demo12345'."
    )

    def add_arguments(self, parser):
        parser.add_argument("--user", default="demo", help="Uživatelské jméno, které se naplní daty")
        parser.add_argument("--habits", type=int, default=6, help="Počet návyků celkem")
        parser.add_argument("--days", type=int, default=60, help="Kolik dní zpětně vygenerovat logy")
        parser.add_argument("--seed", type=int, default=42, help="Seed pro náhodný generátor (deterministické)")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Před naplněním smaže existující návyky/logy daného uživatele",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        username: str = opts["user"]
        num_habits: int = max(1, int(opts["habits"]))
        num_days: int = max(1, int(opts["days"]))
        seed: int = int(opts["seed"])
        reset: bool = bool(opts["reset"])

        rng = random.Random(seed)
        today = date.today()
        start_date = today - timedelta(days=num_days - 1)

        # -- uživatel --
        UserModel = get_user_model()
        user, created = UserModel.objects.get_or_create(username=username)
        if created:
            user.set_password("demo12345")
            user.email = f"{username}@example.com"
            user.save()

        # -- reset starých dat (CASCADE smaže i HabitLog) --
        if reset:
            Habit.objects.filter(user=user).delete()

        # -- rozdělení: cca půlka denní, půlka týdenní --
        daily_count = num_habits // 2
        weekly_count = num_habits - daily_count

        habits: list[Habit] = []

        # denní návyky (cíl 1/den)
        for i in range(daily_count):
            base = daily_names[i % len(daily_names)]
            suffix = f" #{i+1}" if daily_count > 1 else ""
            name = f"{base}{suffix}"
            habits.append(
                Habit(
                    user=user,
                    name=name,
                    periodicity=Habit.Periodicity.DAILY,
                    target_per_period=1,
                )
            )

        # týdenní návyky (cíl 2–4 týdně)
        for i in range(weekly_count):
            base = weekly_names[i % len(weekly_names)]
            suffix = f" #{i+1}" if weekly_count > 1 else ""
            name = f"{base}{suffix}"
            target = rng.randint(2, 4)
            habits.append(
                Habit(
                    user=user,
                    name=name,
                    periodicity=Habit.Periodicity.WEEKLY,
                    target_per_period=target,
                )
            )

        Habit.objects.bulk_create(habits)
        habits = list(Habit.objects.filter(user=user).order_by("id"))

        # -- generování logů --
        to_create: list[HabitLog] = []
        for h in habits:
            if h.periodicity == Habit.Periodicity.DAILY:
                # denní: vyšší šance v posledních 10 dnech (hezčí streak)
                created_any = False
                for d in (start_date + timedelta(i) for i in range(num_days)):
                    p = 0.5
                    if (today - d).days <= 10:
                        p = 0.8
                    if rng.random() < p:
                        to_create.append(HabitLog(habit=h, date=d, value=1))
                        created_any = True
                # jistota alespoň jednoho záznamu
                if not created_any:
                    to_create.append(HabitLog(habit=h, date=today, value=1))
            else:
                # týdenní: menší šance, ale v posledních 10 dnech častěji
                for d in (start_date + timedelta(i) for i in range(num_days)):
                    p = 0.35
                    if (today - d).days <= 10:
                        p = 0.55
                    if rng.random() < p:
                        to_create.append(HabitLog(habit=h, date=d, value=1))

        # -- pojistka unikátnosti (habit, date) v bufferu --
        seen: set[tuple[int, date]] = set()
        unique_logs: list[HabitLog] = []
        for log in to_create:
            key = (log.habit_id, log.date)
            if key not in seen:
                seen.add(key)
                unique_logs.append(log)

        HabitLog.objects.bulk_create(unique_logs, batch_size=1000)

        # -- shrnutí pro konzoli --
        total_logs = HabitLog.objects.filter(habit__user=user).count()
        weekly_list = [h for h in habits if h.periodicity == Habit.Periodicity.WEEKLY]
        daily_list = [h for h in habits if h.periodicity == Habit.Periodicity.DAILY]
        self.stdout.write(
            self.style.SUCCESS(
                f"Hotovo: uživatel '{username}': {len(daily_list)} denních, {len(weekly_list)} týdenních, {total_logs} záznamů za {num_days} dní."
            )
        )
