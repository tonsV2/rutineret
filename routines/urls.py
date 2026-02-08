from django.urls import path
from . import views

app_name = "routines"

urlpatterns = [
    # Routine endpoints
    path(
        "routines/", views.RoutineListCreateView.as_view(), name="routine_list_create"
    ),
    path(
        "routines/<int:pk>/", views.RoutineDetailView.as_view(), name="routine_detail"
    ),
    # Task endpoints (nested under routines)
    path(
        "routines/<int:routine_id>/tasks/",
        views.TaskListCreateView.as_view(),
        name="task_list_create",
    ),
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task_detail"),
    # Task operations
    path(
        "tasks/<int:task_id>/complete/",
        views.TaskCompleteView.as_view(),
        name="task_complete",
    ),
    path(
        "routines/<int:routine_id>/tasks/reorder/",
        views.TaskReorderView.as_view(),
        name="task_reorder",
    ),
    # Today's routine and completions
    path("today/", views.today_routine, name="today_routine"),
    path(
        "completions/", views.TaskCompletionListView.as_view(), name="completion_list"
    ),
]
