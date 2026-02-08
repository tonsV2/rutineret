from django.utils import timezone
from django.db import models
from rest_framework import serializers
from datetime import date
from .models import Routine, Task, TaskCompletion


class TaskCompletionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    task_title = serializers.CharField(source="task.title", read_only=True)

    class Meta:
        model = TaskCompletion
        fields = ["id", "user", "task", "task_title", "completed_at"]
        read_only_fields = ["id", "user", "completed_at"]


class TaskSerializer(serializers.ModelSerializer):
    routine_name = serializers.CharField(source="routine.name", read_only=True)
    is_due_today = serializers.BooleanField(read_only=True)
    is_completed_today = serializers.BooleanField(read_only=True)
    completions_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "routine",
            "routine_name",
            "title",
            "description",
            "order",
            "recurrence_type",
            "recurrence_metadata",
            "is_due_today",
            "is_completed_today",
            "completions_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_completions_count(self, obj):
        """Get total number of completions for this task."""
        return obj.completions.count()

    def validate_recurrence_metadata(self, value):
        """Validate recurrence metadata based on recurrence type."""
        recurrence_type = self.initial_data.get("recurrence_type")

        if recurrence_type == "weekly":
            weekdays = value.get("weekdays", [])
            if not weekdays:
                raise serializers.ValidationError(
                    "Weekly tasks must have at least one weekday specified"
                )
            if not all(isinstance(day, int) and 0 <= day <= 6 for day in weekdays):
                raise serializers.ValidationError(
                    "Weekdays must be integers between 0 (Monday) and 6 (Sunday)"
                )
            if len(set(weekdays)) != len(weekdays):
                raise serializers.ValidationError("Weekdays must be unique")

        elif recurrence_type == "monthly":
            day_of_month = value.get("day_of_month")
            if not day_of_month:
                raise serializers.ValidationError(
                    "Monthly tasks must specify day_of_month"
                )
            if not isinstance(day_of_month, int) or not (1 <= day_of_month <= 31):
                raise serializers.ValidationError(
                    "day_of_month must be an integer between 1 and 31"
                )

        elif recurrence_type == "yearly":
            month = value.get("month")
            day = value.get("day")
            if not month or not day:
                raise serializers.ValidationError(
                    "Yearly tasks must specify both month and day"
                )
            if not isinstance(month, int) or not (1 <= month <= 12):
                raise serializers.ValidationError(
                    "Month must be an integer between 1 and 12"
                )
            if not isinstance(day, int) or not (1 <= day <= 31):
                raise serializers.ValidationError(
                    "Day must be an integer between 1 and 31"
                )
            # Validate day/month combinations (e.g., February 30th)
            if month == 2 and day > 29:
                raise serializers.ValidationError(
                    "February cannot have more than 29 days"
                )
            elif month in [4, 6, 9, 11] and day > 30:
                raise serializers.ValidationError(
                    f"Month {month} cannot have more than 30 days"
                )

        return value

    def create(self, validated_data):
        """Set order automatically if not provided."""
        if "order" not in validated_data or validated_data["order"] == 0:
            # Get the highest order for this routine and increment
            max_order = (
                Task.objects.filter(routine=validated_data["routine"]).aggregate(
                    models.Max("order")
                )["order__max"]
                or 0
            )
            validated_data["order"] = max_order + 1

        return super().create(validated_data)


class RoutineSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)
    tasks_count = serializers.SerializerMethodField()
    due_today_count = serializers.SerializerMethodField()

    class Meta:
        model = Routine
        fields = [
            "id",
            "user",
            "name",
            "description",
            "tasks",
            "tasks_count",
            "due_today_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def get_tasks_count(self, obj):
        """Get total number of tasks in this routine."""
        return obj.tasks.count()

    def get_due_today_count(self, obj):
        """Get number of tasks due today for this routine."""
        today = date.today()
        due_count = 0
        for task in obj.tasks.all():
            if task.is_due_today(today):
                due_count += 1
        return due_count


class TaskReorderSerializer(serializers.Serializer):
    """Serializer for reordering tasks within a routine."""

    task_ids = serializers.ListField(
        child=serializers.IntegerField(), help_text="Ordered list of task IDs"
    )

    def validate_task_ids(self, value):
        """Validate that all task IDs belong to the same routine."""
        if not value:
            raise serializers.ValidationError("Task IDs list cannot be empty")

        # Check if all tasks exist and belong to the same routine
        tasks = Task.objects.filter(id__in=value)
        if tasks.count() != len(value):
            raise serializers.ValidationError("One or more task IDs are invalid")

        # Check if all tasks belong to the same routine
        routines = tasks.values_list("routine_id", flat=True).distinct()
        if len(set(routines)) > 1:
            raise serializers.ValidationError(
                "All tasks must belong to the same routine"
            )

        return value


class TaskCompleteSerializer(serializers.Serializer):
    """Serializer for marking a task as complete."""

    completion_time = serializers.DateTimeField(
        required=False, help_text="Optional custom completion time (defaults to now)"
    )

    def validate_completion_time(self, value):
        """Validate completion time is not in the future."""
        if value and value > timezone.now():
            raise serializers.ValidationError("Completion time cannot be in the future")
        return value


class TodayRoutineSerializer(serializers.Serializer):
    """Serializer for today's routine response."""

    date = serializers.DateField(read_only=True)
    routine = RoutineSerializer(read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)


class TaskCompletionListSerializer(serializers.ModelSerializer):
    """Detailed serializer for completion lists with pagination."""

    task_title = serializers.CharField(source="task.title", read_only=True)
    routine_name = serializers.CharField(source="task.routine.name", read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = TaskCompletion
        fields = ["id", "user", "task", "task_title", "routine_name", "completed_at"]
        read_only_fields = ["id", "user", "completed_at"]
