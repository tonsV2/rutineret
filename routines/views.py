from django.utils import timezone
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
    CreateAPIView,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Routine, Task, TaskCompletion
from .serializers import (
    RoutineSerializer,
    TaskSerializer,
    TaskCompletionSerializer,
    TaskReorderSerializer,
    TaskCompleteSerializer,
    TodayRoutineSerializer,
    TaskCompletionListSerializer,
)


class RoutineListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: RoutineSerializer(many=True)},
        summary="List User's Routines",
        description="Get all routines for the authenticated user",
    )
    def get(self, request):
        routines = Routine.objects.filter(user=request.user).prefetch_related("tasks")
        serializer = RoutineSerializer(routines, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=RoutineSerializer,
        responses={201: RoutineSerializer},
        summary="Create New Routine",
        description="Create a new routine for the authenticated user",
    )
    def post(self, request):
        serializer = RoutineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoutineDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = RoutineSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Routine.objects.filter(user=self.request.user).prefetch_related("tasks")

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class TaskListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: TaskSerializer(many=True)},
        summary="List Tasks in Routine",
        description="Get all tasks for a specific routine",
    )
    def get(self, request, routine_id):
        tasks = Task.objects.filter(routine_id=routine_id, routine__user=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=TaskSerializer,
        responses={201: TaskSerializer},
        summary="Create Task in Routine",
        description="Add a new task to a specific routine",
    )
    def post(self, request, routine_id):
        try:
            routine = Routine.objects.get(id=routine_id, user=request.user)
        except Routine.DoesNotExist:
            return Response(
                {"error": "Routine not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(routine=routine)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(routine__user=self.request.user)


class TaskCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=TaskCompleteSerializer,
        responses={201: TaskCompletionSerializer},
        summary="Mark Task as Complete",
        description="Mark a task as completed for the current date/time",
    )
    def post(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id, routine__user=request.user)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = TaskCompleteSerializer(data=request.data)
        if serializer.is_valid():
            completion_time = serializer.validated_data.get(
                "completion_time", timezone.now()
            )

            completion = TaskCompletion.objects.create(
                user=request.user, task=task, completed_at=completion_time
            )

            response_serializer = TaskCompletionSerializer(completion)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskReorderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=TaskReorderSerializer,
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}}
        },
        summary="Reorder Tasks",
        description="Reorder tasks within a routine",
    )
    def post(self, request, routine_id):
        try:
            routine = Routine.objects.get(id=routine_id, user=request.user)
        except Routine.DoesNotExist:
            return Response(
                {"error": "Routine not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = TaskReorderSerializer(data=request.data)
        if serializer.is_valid():
            task_ids = serializer.validated_data["task_ids"]

            # Verify all tasks belong to this routine
            tasks = Task.objects.filter(id__in=task_ids, routine=routine)
            if tasks.count() != len(task_ids):
                return Response(
                    {"error": "One or more tasks do not belong to this routine"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Update task orders in a transaction
            with transaction.atomic():
                for index, task_id in enumerate(task_ids):
                    Task.objects.filter(id=task_id).update(order=index + 1)

            return Response({"message": "Tasks reordered successfully"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="date",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description="Date to check for due tasks (YYYY-MM-DD format, defaults to today)",
        )
    ],
    responses={200: TaskSerializer(many=True)},
    summary="Get Today's Routine",
    description="Get all tasks due today for the authenticated user",
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def today_routine(request):
    from datetime import date, datetime

    # Get target date from query parameter or default to today
    date_param = request.query_params.get("date")
    if date_param:
        try:
            target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        target_date = date.today()

    # Get all user's tasks and filter due ones
    all_tasks = (
        Task.objects.filter(routine__user=request.user)
        .select_related("routine")
        .order_by("order", "created_at")
    )

    due_tasks = []
    for task in all_tasks:
        if task.is_due_today(target_date):
            task.is_due_today = True
            task.is_completed_today = task.is_completed_today(request.user, target_date)
            due_tasks.append(task)

    serializer = TaskSerializer(due_tasks, many=True)

    return Response(
        {
            "date": target_date.isoformat(),
            "tasks": serializer.data,
        }
    )


class TaskCompletionListView(ListAPIView):
    serializer_class = TaskCompletionListSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="task_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter by specific task ID",
            ),
            OpenApiParameter(
                name="routine_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter by specific routine ID",
            ),
        ],
        summary="List Task Completions",
        description="Get paginated list of task completions for the authenticated user",
    )
    def get_queryset(self):
        queryset = (
            TaskCompletion.objects.filter(user=self.request.user)
            .select_related("task", "task__routine")
            .order_by("-completed_at")
        )

        task_id = self.request.query_params.get("task_id")
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        routine_id = self.request.query_params.get("routine_id")
        if routine_id:
            queryset = queryset.filter(task__routine_id=routine_id)

        return queryset
