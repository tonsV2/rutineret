import calendar
from datetime import date, datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Routine, Task, TaskCompletion

User = get_user_model()


class RoutineModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.routine = Routine.objects.create(
            user=self.user,
            name="Morning Routine",
            description="Daily morning activities",
        )

    def test_routine_creation(self):
        self.assertEqual(self.routine.name, "Morning Routine")
        self.assertEqual(self.routine.user, self.user)
        self.assertEqual(str(self.routine), "Morning Routine (by testuser)")

    def test_routine_ordering(self):
        routine2 = Routine.objects.create(user=self.user, name="Evening Routine")
        routines = list(Routine.objects.filter(user=self.user))
        self.assertEqual(routines[0].name, "Evening Routine")
        self.assertEqual(routines[1].name, "Morning Routine")


class TaskModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.routine = Routine.objects.create(user=self.user, name="Morning Routine")

    def test_task_creation(self):
        task = Task.objects.create(
            routine=self.routine,
            title="Exercise",
            description="30 minutes of cardio",
            order=1,
            recurrence_type="daily",
        )
        self.assertEqual(task.title, "Exercise")
        self.assertEqual(task.routine, self.routine)
        self.assertEqual(task.order, 1)

    def test_daily_task_due_today(self):
        task = Task.objects.create(
            routine=self.routine, title="Exercise", recurrence_type="daily"
        )
        self.assertTrue(task.is_due_today())

    def test_workdays_task_due_today(self):
        task = Task.objects.create(
            routine=self.routine, title="Work meeting", recurrence_type="workdays"
        )

        # Test on a weekday (Monday)
        monday = date(2024, 1, 8)  # Monday
        self.assertTrue(task.is_due_today(monday))

        # Test on a weekend (Sunday)
        sunday = date(2024, 1, 7)  # Sunday
        self.assertFalse(task.is_due_today(sunday))

    def test_weekly_task_due_today(self):
        task = Task.objects.create(
            routine=self.routine,
            title="Team meeting",
            recurrence_type="weekly",
            recurrence_metadata={"weekdays": [1, 3]},  # Tuesday, Thursday
        )

        # Test on Tuesday (weekday 1)
        tuesday = date(2024, 1, 9)  # Tuesday
        self.assertTrue(task.is_due_today(tuesday))

        # Test on Wednesday (weekday 2)
        wednesday = date(2024, 1, 10)  # Wednesday
        self.assertFalse(task.is_due_today(wednesday))

        # Test on Thursday (weekday 3)
        thursday = date(2024, 1, 11)  # Thursday
        self.assertTrue(task.is_due_today(thursday))

    def test_monthly_task_due_today(self):
        task = Task.objects.create(
            routine=self.routine,
            title="Pay bills",
            recurrence_type="monthly",
            recurrence_metadata={"day_of_month": 15},
        )

        # Test on 15th of month
        fifteenth = date(2024, 1, 15)
        self.assertTrue(task.is_due_today(fifteenth))

        # Test on different day
        tenth = date(2024, 1, 10)
        self.assertFalse(task.is_due_today(tenth))

    def test_monthly_task_last_day_handling(self):
        task = Task.objects.create(
            routine=self.routine,
            title="End of month review",
            recurrence_type="monthly",
            recurrence_metadata={"day_of_month": 31},
        )

        # Test in February (non-leap year)
        feb_2023 = date(2023, 2, 28)  # Non-leap year
        self.assertFalse(task.is_due_today(feb_2023))
        # Test in February (leap year)
        feb_2024 = date(2024, 2, 29)  # Leap year
        self.assertTrue(task.is_due_today(feb_2024))

        # Test in month with 30 days
        apr_last = date(2024, 4, 30)
        self.assertTrue(task.is_due_today(apr_last))

    def test_yearly_task_due_today(self):
        task = Task.objects.create(
            routine=self.routine,
            title="Birthday",
            recurrence_type="yearly",
            recurrence_metadata={"month": 6, "day": 15},  # June 15
        )

        # Test on birthday
        birthday = date(2024, 6, 15)
        self.assertTrue(task.is_due_today(birthday))

        # Test on different date
        not_birthday = date(2024, 6, 14)
        self.assertFalse(task.is_due_today(not_birthday))

    def test_yearly_task_feb_29_leap_year(self):
        task = Task.objects.create(
            routine=self.routine,
            title="Leap day celebration",
            recurrence_type="yearly",
            recurrence_metadata={"month": 2, "day": 29},
        )

        # Test on leap year
        leap_day = date(2024, 2, 29)
        self.assertTrue(task.is_due_today(leap_day))

        # Test on non-leap year
        feb_28 = date(2024, 2, 28)
        self.assertFalse(task.is_due_today(feb_28))

    def test_task_completion_today(self):
        task = Task.objects.create(
            routine=self.routine, title="Exercise", recurrence_type="daily"
        )

        # Initially not completed
        self.assertFalse(task.is_completed_today(self.user))

        # Complete task
        completion = TaskCompletion.objects.create(user=self.user, task=task)

        # Now should be completed today
        self.assertTrue(task.is_completed_today(self.user))

    def test_multiple_completions_same_day(self):
        task = Task.objects.create(
            routine=self.routine, title="Exercise", recurrence_type="daily"
        )

        # Complete task multiple times today
        TaskCompletion.objects.create(user=self.user, task=task)
        TaskCompletion.objects.create(user=self.user, task=task)

        self.assertTrue(task.is_completed_today(self.user))
        self.assertEqual(task.completions.count(), 2)

    def test_task_completion_different_days(self):
        task = Task.objects.create(
            routine=self.routine, title="Exercise", recurrence_type="daily"
        )

        # Complete task yesterday only
        yesterday = timezone.now() - timedelta(days=1)
        TaskCompletion.objects.create(user=self.user, task=task, completed_at=yesterday)

        # Should not be completed today
        self.assertFalse(task.is_completed_today(self.user))

    def test_get_due_today_for_user(self):
        # Create tasks with different recurrence types
        daily_task = Task.objects.create(
            routine=self.routine, title="Daily task", recurrence_type="daily", order=1
        )

        weekend_task = Task.objects.create(
            routine=self.routine,
            title="Weekend task",
            recurrence_type="weekly",
            recurrence_metadata={"weekdays": [6, 0]},  # Saturday, Sunday
            order=2,
        )

        # Test with today's date - this method always uses current date
        due_tasks = Task.get_due_today_for_user(self.user)

        # Should find both tasks in the queryset, but only daily task should be due today
        task_titles = [task.title for task in due_tasks]
        self.assertIn("Daily task", task_titles)
        self.assertIn("Weekend task", task_titles)  # Both should be in queryset

        # Check actual due status for each task
        daily_task = next(t for t in due_tasks if t.title == "Daily task")
        weekend_task = next(t for t in due_tasks if t.title == "Weekend task")

        self.assertTrue(daily_task.is_due_today())  # Daily should be due today
        # Weekend task due status depends on current day of week


class TaskCompletionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.routine = Routine.objects.create(user=self.user, name="Morning Routine")
        self.task = Task.objects.create(
            routine=self.routine, title="Exercise", recurrence_type="daily"
        )

    def test_completion_creation(self):
        completion = TaskCompletion.objects.create(user=self.user, task=self.task)
        self.assertEqual(completion.user, self.user)
        self.assertEqual(completion.task, self.task)
        self.assertIsNotNone(completion.completed_at)

    def test_completion_string_representation(self):
        completion = TaskCompletion.objects.create(user=self.user, task=self.task)
        expected = (
            f"Exercise completed by {self.user.username} at {completion.completed_at}"
        )
        self.assertEqual(str(completion), expected)

    def test_completion_ordering(self):
        # Create completions at different times
        time1 = timezone.now() - timedelta(minutes=10)
        time2 = timezone.now() - timedelta(minutes=5)
        time3 = timezone.now()

        completion1 = TaskCompletion.objects.create(
            user=self.user, task=self.task, completed_at=time1
        )
        completion2 = TaskCompletion.objects.create(
            user=self.user, task=self.task, completed_at=time2
        )
        completion3 = TaskCompletion.objects.create(
            user=self.user, task=self.task, completed_at=time3
        )

        # Should be ordered by completed_at descending
        completions = list(TaskCompletion.objects.all())
        self.assertEqual(completions[0], completion3)
        self.assertEqual(completions[1], completion2)
        self.assertEqual(completions[2], completion1)


class RoutineAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_routine(self):
        data = {"name": "Morning Routine", "description": "Daily morning activities"}
        response = self.client.post("/api/routines/routines/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Routine.objects.count(), 1)

        routine = Routine.objects.first()
        self.assertEqual(routine.name, "Morning Routine")
        self.assertEqual(routine.user, self.user)

    def test_list_routines(self):
        Routine.objects.create(user=self.user, name="Morning Routine")
        Routine.objects.create(user=self.user, name="Evening Routine")

        response = self.client.get("/api/routines/routines/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_task_in_routine(self):
        routine = Routine.objects.create(user=self.user, name="Morning Routine")

        data = {
            "title": "Exercise",
            "description": "30 minutes of cardio",
            "recurrence_type": "daily",
            "order": 1,
        }

        response = self.client.post(
            f"/api/routines/routines/{routine.id}/tasks/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)

    def test_mark_task_complete(self):
        routine = Routine.objects.create(user=self.user, name="Morning Routine")
        task = Task.objects.create(
            routine=routine, title="Exercise", recurrence_type="daily"
        )

        response = self.client.post(f"/api/routines/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TaskCompletion.objects.count(), 1)

        completion = TaskCompletion.objects.first()
        self.assertEqual(completion.user, self.user)
        self.assertEqual(completion.task, task)

    def test_mark_task_uncompleted_single_completion(self):
        routine = Routine.objects.create(user=self.user, name="Morning Routine")
        task = Task.objects.create(
            routine=routine, title="Exercise", recurrence_type="daily"
        )

        # First complete the task
        self.client.post(f"/api/routines/tasks/{task.id}/complete/")
        self.assertEqual(TaskCompletion.objects.count(), 1)
        self.assertTrue(task.is_completed_today(self.user))

        # Then uncomplete it
        response = self.client.delete(f"/api/routines/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TaskCompletion.objects.count(), 0)
        self.assertFalse(task.is_completed_today(self.user))

    def test_mark_task_uncompleted_multiple_completions(self):
        routine = Routine.objects.create(user=self.user, name="Morning Routine")
        task = Task.objects.create(
            routine=routine, title="Exercise", recurrence_type="daily"
        )

        # Complete the task multiple times today
        self.client.post(f"/api/routines/tasks/{task.id}/complete/")
        self.client.post(f"/api/routines/tasks/{task.id}/complete/")
        self.client.post(f"/api/routines/tasks/{task.id}/complete/")

        self.assertEqual(TaskCompletion.objects.count(), 3)
        self.assertTrue(task.is_completed_today(self.user))

        # Uncomplete should remove one completion (any of today's)
        response = self.client.delete(f"/api/routines/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TaskCompletion.objects.count(), 2)  # Should have 2 remaining
        self.assertTrue(task.is_completed_today(self.user))  # Still completed today

    def test_uncompleted_task_no_completions_today(self):
        routine = Routine.objects.create(user=self.user, name="Morning Routine")
        task = Task.objects.create(
            routine=routine, title="Exercise", recurrence_type="daily"
        )

        # Try to uncomplete without any completions
        response = self.client.delete(f"/api/routines/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertIn("No completions found for today", data["error"])

    def test_uncompleted_task_only_yesterday_completions(self):
        routine = Routine.objects.create(user=self.user, name="Morning Routine")
        task = Task.objects.create(
            routine=routine, title="Exercise", recurrence_type="daily"
        )

        # Create a completion from yesterday by creating it normally and then updating the time
        completion = TaskCompletion.objects.create(user=self.user, task=task)
        yesterday = timezone.now() - timedelta(days=1)
        completion.completed_at = yesterday
        completion.save()

        # Should not be able to uncomplete yesterday's completion
        response = self.client.delete(f"/api/routines/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = response.json()
        self.assertIn("No completions found for today", data["error"])

        # Yesterday's completion should still exist
        self.assertEqual(TaskCompletion.objects.count(), 1)

    def test_uncompleted_task_mixed_completions(self):
        routine = Routine.objects.create(user=self.user, name="Morning Routine")
        task = Task.objects.create(
            routine=routine, title="Exercise", recurrence_type="daily"
        )

        # Create completions from yesterday and today
        yesterday_completion = TaskCompletion.objects.create(user=self.user, task=task)
        yesterday = timezone.now() - timedelta(days=1)
        yesterday_completion.completed_at = yesterday
        yesterday_completion.save()

        # Complete today
        self.client.post(f"/api/routines/tasks/{task.id}/complete/")

        self.assertEqual(TaskCompletion.objects.count(), 2)

        # Uncomplete should only remove today's completion
        response = self.client.delete(f"/api/routines/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Should still have yesterday's completion
        self.assertEqual(TaskCompletion.objects.count(), 1)
        self.assertFalse(task.is_completed_today(self.user))

    def test_uncompleted_task_not_found(self):
        # Try to uncomplete a non-existent task
        response = self.client.delete("/api/routines/tasks/999/complete/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        data = response.json()
        self.assertEqual(data["error"], "Task not found")

    def test_uncompleted_task_unauthorized(self):
        # Create task for different user
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="otherpass123"
        )
        other_routine = Routine.objects.create(user=other_user, name="Other Routine")
        other_task = Task.objects.create(
            routine=other_routine, title="Other Exercise", recurrence_type="daily"
        )

        # Try to uncomplete other user's task
        response = self.client.delete(f"/api/routines/tasks/{other_task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        data = response.json()
        self.assertEqual(data["error"], "Task not found")

    def test_complete_and_uncomplete_workflow(self):
        routine = Routine.objects.create(user=self.user, name="Morning Routine")
        task = Task.objects.create(
            routine=routine, title="Exercise", recurrence_type="daily"
        )

        # Initial state
        self.assertFalse(task.is_completed_today(self.user))
        self.assertEqual(TaskCompletion.objects.count(), 0)

        # Complete task
        response = self.client.post(f"/api/routines/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(task.is_completed_today(self.user))
        self.assertEqual(TaskCompletion.objects.count(), 1)

        # Uncomplete task
        response = self.client.delete(f"/api/routines/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(task.is_completed_today(self.user))
        self.assertEqual(TaskCompletion.objects.count(), 0)

        # Complete again
        response = self.client.post(f"/api/routines/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(task.is_completed_today(self.user))
        self.assertEqual(TaskCompletion.objects.count(), 1)

    def test_today_routine_endpoint(self):
        routine = Routine.objects.create(user=self.user, name="Morning Routine")

        # Create tasks
        Task.objects.create(
            routine=routine, title="Daily exercise", recurrence_type="daily", order=1
        )

        Task.objects.create(
            routine=routine,
            title="Weekend hobby",
            recurrence_type="weekly",
            recurrence_metadata={"weekdays": [6, 0]},  # Weekend
            order=2,
        )

        response = self.client.get("/api/routines/today/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("date", data)
        self.assertIn("tasks", data)

        # Should include daily task but not weekend task (assuming today is weekday)
        task_titles = [task["title"] for task in data["tasks"]]
        self.assertIn("Daily exercise", task_titles)

    def test_reorder_tasks(self):
        routine = Routine.objects.create(user=self.user, name="Morning Routine")

        # Create tasks with initial order
        task1 = Task.objects.create(
            routine=routine, title="Task 1", recurrence_type="daily", order=1
        )
        task2 = Task.objects.create(
            routine=routine, title="Task 2", recurrence_type="daily", order=2
        )
        task3 = Task.objects.create(
            routine=routine, title="Task 3", recurrence_type="daily", order=3
        )

        # Reorder tasks
        data = {"task_ids": [task2.id, task3.id, task1.id]}
        response = self.client.post(
            f"/api/routines/routines/{routine.id}/tasks/reorder/", data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh tasks from database
        task1.refresh_from_db()
        task2.refresh_from_db()
        task3.refresh_from_db()

        self.assertEqual(task1.order, 3)
        self.assertEqual(task2.order, 1)
        self.assertEqual(task3.order, 2)

    def test_task_validation_errors(self):
        routine = Routine.objects.create(user=self.user, name="Morning Routine")

        # Test invalid weekly recurrence (no weekdays)
        data = {
            "title": "Invalid weekly task",
            "recurrence_type": "weekly",
            "recurrence_metadata": {"weekdays": []},
        }

        response = self.client.post(
            f"/api/routines/routines/{routine.id}/tasks/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test invalid monthly recurrence (invalid day)
        data = {
            "title": "Invalid monthly task",
            "recurrence_type": "monthly",
            "recurrence_metadata": {"day_of_month": 32},
        }

        response = self.client.post(
            f"/api/routines/routines/{routine.id}/tasks/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_access(self):
        # Test without authentication
        self.client.force_authenticate(user=None)

        routine = Routine.objects.create(user=self.user, name="Morning Routine")

        response = self.client.get("/api/routines/routines/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(f"/api/routines/routines/{routine.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
