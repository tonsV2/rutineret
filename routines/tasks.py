import calendar
from datetime import date, datetime, timedelta, time
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from celery import shared_task
from .models import Task, TaskCompletion
from users.models import User, UserProfile

import pytz


@shared_task
def check_pending_alarms():
    """
    Check for tasks that have alarms due in the next minute.
    This task runs every minute via Celery Beat.
    """
    try:
        # Get current time in UTC
        now_utc = timezone.now()

        # Get all users with alarm-enabled tasks
        users_with_alarms = User.objects.filter(
            routines__tasks__alarm_enabled=True, routines__tasks__due_time__isnull=False
        ).distinct()

        for user in users_with_alarms:
            # Get user's timezone preference
            try:
                user_profile = user.profile
                user_tz = pytz.timezone(user_profile.timezone)
            except:
                user_tz = pytz.UTC

            # Convert current time to user's timezone
            now_user_tz = now_utc.astimezone(user_tz)
            current_time = now_user_tz.time()
            current_date = now_user_tz.date()

            # Get all alarm-enabled tasks for this user
            tasks_with_alarms = Task.objects.filter(
                routine__user=user, alarm_enabled=True, due_time__isnull=False
            ).select_related("routine")

            for task in tasks_with_alarms:
                # Check if task is due today
                if task.is_due_today(current_date):
                    # Calculate alarm time
                    alarm_time = (
                        datetime.combine(current_date, task.due_time)
                        - timedelta(minutes=task.alarm_minutes_before)
                    ).time()

                    # Check if current time matches alarm time (within 1 minute)
                    time_diff = abs(
                        (
                            datetime.combine(current_date, current_time)
                            - datetime.combine(current_date, alarm_time)
                        ).total_seconds()
                        / 60
                    )

                    if time_diff <= 1.0:  # Within 1 minute
                        # Check if task is not already completed today
                        if not task.is_completed_today(user, current_date):
                            # Send alarm email
                            send_task_reminder_email.delay(task.id, user.id)
                            print(
                                f"Alarm sent for task '{task.title}' to user {user.email}"
                            )

    except Exception as e:
        print(f"Error in check_pending_alarms: {str(e)}")


@shared_task
def send_task_reminder_email(task_id, user_id):
    """
    Send email reminder for a specific task.
    """
    try:
        task = Task.objects.get(id=task_id)
        user = User.objects.get(id=user_id)

        # Get user's timezone
        try:
            user_profile = user.profile
            user_tz = pytz.timezone(user_profile.timezone)
        except:
            user_tz = pytz.UTC

        # Calculate due time in user's timezone
        now_user_tz = timezone.now().astimezone(user_tz)
        due_datetime = datetime.combine(now_user_tz.date(), task.due_time)
        due_datetime = user_tz.localize(due_datetime)

        # Render email template
        subject = f"Task Reminder: {task.title}"

        context = {
            "user": user,
            "task": task,
            "routine_name": task.routine.name,
            "due_time": due_datetime.strftime("%I:%M %p"),
            "alarm_minutes_before": task.alarm_minutes_before,
            "recurrence_type": task.get_recurrence_type_display(),
        }

        html_message = render_to_string("emails/task_reminder.html", context)
        text_message = render_to_string("emails/task_reminder.txt", context)

        # Send email
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        print(f"Reminder email sent for task '{task.title}' to {user.email}")

    except Task.DoesNotExist:
        print(f"Task with id {task_id} not found")
    except User.DoesNotExist:
        print(f"User with id {user_id} not found")
    except Exception as e:
        print(f"Error sending reminder email: {str(e)}")


@shared_task
def cleanup_old_reminders():
    """
    Clean up old task completions and other maintenance tasks.
    Runs every hour.
    """
    try:
        # Delete task completions older than 1 year
        one_year_ago = timezone.now() - timedelta(days=365)
        old_completions = TaskCompletion.objects.filter(completed_at__lt=one_year_ago)
        count = old_completions.count()
        old_completions.delete()

        if count > 0:
            print(f"Cleaned up {count} old task completions")

    except Exception as e:
        print(f"Error in cleanup_old_reminders: {str(e)}")


@shared_task
def test_alarm_system():
    """
    Test task to verify Celery is working.
    """
    print("Celery alarm system is working!")
    return "Alarm system test completed"
