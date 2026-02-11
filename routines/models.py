import calendar
from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Routine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="routines")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} (by {self.user.username})"


class Task(models.Model):
    RECURRENCE_TYPES = [
        ("daily", "Daily"),
        ("workdays", "Workdays (Mon-Fri)"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    # Recurrence fields
    recurrence_type = models.CharField(max_length=10, choices=RECURRENCE_TYPES)
    recurrence_metadata = models.JSONField(default=dict)

    # Alarm fields
    due_time = models.TimeField(null=True, blank=True, help_text="Time of day when task is due")
    alarm_enabled = models.BooleanField(default=False, help_text="Whether to send alarm reminders")
    alarm_minutes_before = models.PositiveIntegerField(default=15, help_text="Minutes before due time to send alarm")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_recurrence_type_display()})"

    def is_due_today(self, target_date: date = None) -> bool:
        """Check if this task is due on the given date (defaults to today)."""
        if target_date is None:
            target_date = date.today()

        weekday = target_date.weekday()  # Monday is 0, Sunday is 6

        if self.recurrence_type == "daily":
            return True
        elif self.recurrence_type == "workdays":
            return weekday <= 4  # Monday (0) to Friday (4)
        elif self.recurrence_type == "weekly":
            weekdays = self.recurrence_metadata.get("weekdays", [])
            return weekday in weekdays
        elif self.recurrence_type == "monthly":
            day_of_month = self.recurrence_metadata.get("day_of_month")
            if day_of_month is None:
                return False
            last_day_of_month = calendar.monthrange(
                target_date.year, target_date.month
            )[1]
            # If requested day exists in this month, check exact match
            if day_of_month <= last_day_of_month:
                return target_date.day == day_of_month
            # If requested day doesn't exist (e.g., 31st in February), task is due on last day
            return target_date.day == last_day_of_month
        elif self.recurrence_type == "yearly":
            month = self.recurrence_metadata.get("month")
            day = self.recurrence_metadata.get("day")
            if month is None or day is None:
                return False
            # Handle February 29th for non-leap years
            if month == 2 and day == 29 and not calendar.isleap(target_date.year):
                return False
            return target_date.month == month and target_date.day == day

        return False

    def is_completed_today(self, user: User, target_date: date = None) -> bool:
        """Check if this task has been completed by the user on the given date."""
        if target_date is None:
            target_date = date.today()

        # Convert date to datetime range for checking using timezone-aware datetimes
        from django.utils import timezone

        start_of_day = timezone.make_aware(
            datetime.combine(target_date, datetime.min.time())
        )
        end_of_day = timezone.make_aware(
            datetime.combine(target_date, datetime.max.time())
        )

        return self.completions.filter(
            user=user, completed_at__gte=start_of_day, completed_at__lte=end_of_day
        ).exists()

    @classmethod
    def get_due_today_for_user(cls, user: User):
        """Get all tasks due today for a specific user, ordered by task order."""
        return (
            cls.objects.filter(routine__user=user)
            .select_related("routine")
            .order_by("order", "created_at")
        )


class TaskCompletion(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="task_completions"
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="completions")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]
        indexes = [
            models.Index(fields=["user", "task"]),
            models.Index(fields=["user", "completed_at"]),
            models.Index(fields=["task", "completed_at"]),
        ]

    def __str__(self):
        return f"{self.task.title} completed by {self.user.username} at {self.completed_at}"
