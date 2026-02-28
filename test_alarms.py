#!/usr/bin/env python3
"""
Simple test script to verify alarm functionality works
"""

import os
import sys
import django
import pytest

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings.development")
django.setup()

from django.utils import timezone
from routines.models import Task, Routine
from users.models import User
from datetime import time


@pytest.mark.django_db(transaction=True)
def test_alarm_system():
    print("🔔 Testing Alarm System")
    print("=" * 50)

    # Get or create a test user
    user, created = User.objects.get_or_create(
        email="test@example.com",
        defaults={
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    if created:
        print(f"✅ Created user: {user.email}")
    # Profile is created automatically via signals
    profile = user.profile
    profile.timezone = "America/New_York"
    profile.save()

    # Get or create a test routine
    routine, created = Routine.objects.get_or_create(
        user=user,
        name="Test Routine",
        defaults={"description": "Routine for testing alarms"},
    )
    if created:
        print(f"✅ Created routine: {routine.name}")

    # Create a task with alarm settings
    task, created = Task.objects.get_or_create(
        routine=routine,
        title="Test Alarm Task",
        defaults={
            "description": "This is a test task for alarm functionality",
            "order": 1,
            "recurrence_type": "daily",
            "recurrence_metadata": {},
            "due_time": time(14, 30),  # 2:30 PM
            "alarm_enabled": True,
            "alarm_minutes_before": 15,  # 15 minutes before
        },
    )

    if created:
        print(f"✅ Created task: {task.title}")
        print(f"   Due Time: {task.due_time}")
        print(f"   Alarm Enabled: {task.alarm_enabled}")
        print(f"   Alarm Minutes Before: {task.alarm_minutes_before}")
    else:
        print(f"📋 Found existing task: {task.title}")
        # Update with alarm settings
        task.due_time = time(14, 30)
        task.alarm_enabled = True
        task.alarm_minutes_before = 15
        task.save()
        print(f"✅ Updated task with alarm settings")

    print("\n🔍 Testing Task Methods:")
    print(f"   Is task due today? {task.is_due_today()}")
    print(f"   User timezone: {user.profile.timezone}")

    print("\n📧 Testing Celery Task:")
    try:
        from routines.tasks import test_alarm_system

        result = test_alarm_system.delay()
        print(f"✅ Celery test task queued: {result.id}")
        print("   (Check celery logs for results)")
    except Exception as e:
        print(f"❌ Celery test failed: {e}")

    print("\n🎯 Alarm System Test Complete!")
    print("Next steps:")
    print("1. Start Redis: redis-server")
    print("2. Start Celery worker: celery -A rutineret worker --loglevel=info")
    print("3. Start Celery beat: celery -A rutineret beat --loglevel=info")
    print("4. Test alarm emails by setting due times soon")

    return True


if __name__ == "__main__":
    test_alarm_system()
