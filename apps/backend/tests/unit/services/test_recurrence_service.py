"""
Unit tests for RecurrenceService
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock

import pytest
from sqlalchemy.orm import Session

from app.db.models import RecurrencePattern, Task, TaskStatus
from app.models.task import RecurrenceConfig
from app.services.recurrence_service import RecurrenceService


class TestCalculateNextOccurrence:
    """Test calculate_next_occurrence method"""

    def test_daily_recurrence(self):
        """Test daily recurrence pattern"""
        base_date = datetime(2025, 1, 1, 10, 0, 0)
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date, pattern=RecurrencePattern.DAILY, interval=1
        )
        assert next_date == datetime(2025, 1, 2, 10, 0, 0)

        # Test with interval
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date, pattern=RecurrencePattern.DAILY, interval=3
        )
        assert next_date == datetime(2025, 1, 4, 10, 0, 0)

    def test_weekly_recurrence(self):
        """Test weekly recurrence pattern"""
        # Monday, January 1, 2025
        base_date = datetime(2025, 1, 6, 10, 0, 0)  # Monday

        # Next Wednesday and Friday
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date,
            pattern=RecurrencePattern.WEEKLY,
            interval=1,
            days_of_week=[2, 4],  # Wednesday and Friday
        )
        assert next_date == datetime(2025, 1, 8, 10, 0, 0)  # Wednesday

        # From Wednesday, next should be Friday
        base_date = datetime(2025, 1, 8, 10, 0, 0)  # Wednesday
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date,
            pattern=RecurrencePattern.WEEKLY,
            interval=1,
            days_of_week=[2, 4],  # Wednesday and Friday
        )
        assert next_date == datetime(2025, 1, 10, 10, 0, 0)  # Friday

        # From Friday, next should be Wednesday of next week
        base_date = datetime(2025, 1, 10, 10, 0, 0)  # Friday
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date,
            pattern=RecurrencePattern.WEEKLY,
            interval=1,
            days_of_week=[2, 4],  # Wednesday and Friday
        )
        assert next_date == datetime(2025, 1, 15, 10, 0, 0)  # Next Wednesday

    def test_weekdays_recurrence(self):
        """Test weekdays recurrence pattern"""
        # Friday
        base_date = datetime(2025, 1, 10, 10, 0, 0)  # Friday
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date, pattern=RecurrencePattern.WEEKDAYS
        )
        assert next_date == datetime(2025, 1, 13, 10, 0, 0)  # Monday

        # Monday
        base_date = datetime(2025, 1, 13, 10, 0, 0)  # Monday
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date, pattern=RecurrencePattern.WEEKDAYS
        )
        assert next_date == datetime(2025, 1, 14, 10, 0, 0)  # Tuesday

    def test_monthly_recurrence(self):
        """Test monthly recurrence pattern"""
        base_date = datetime(2025, 1, 15, 10, 0, 0)
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date,
            pattern=RecurrencePattern.MONTHLY,
            interval=1,
            day_of_month=15,
        )
        assert next_date == datetime(2025, 2, 15, 10, 0, 0)

        # Test with interval
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date,
            pattern=RecurrencePattern.MONTHLY,
            interval=2,
            day_of_month=15,
        )
        assert next_date == datetime(2025, 3, 15, 10, 0, 0)

        # Test month boundary (31st in February)
        base_date = datetime(2025, 1, 31, 10, 0, 0)
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date,
            pattern=RecurrencePattern.MONTHLY,
            interval=1,
            day_of_month=31,
        )
        assert next_date == datetime(2025, 2, 28, 10, 0, 0)  # Feb only has 28 days

    def test_yearly_recurrence(self):
        """Test yearly recurrence pattern"""
        base_date = datetime(2025, 3, 15, 10, 0, 0)
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date,
            pattern=RecurrencePattern.YEARLY,
            interval=1,
            day_of_month=15,
            month_of_year=3,
        )
        assert next_date == datetime(2026, 3, 15, 10, 0, 0)

        # Test leap year edge case
        base_date = datetime(2024, 2, 29, 10, 0, 0)
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date,
            pattern=RecurrencePattern.YEARLY,
            interval=1,
            day_of_month=29,
            month_of_year=2,
        )
        assert next_date == datetime(2025, 2, 28, 10, 0, 0)  # 2025 is not a leap year

    def test_invalid_parameters(self):
        """Test with invalid parameters"""
        base_date = datetime(2025, 1, 1, 10, 0, 0)

        # Weekly without days_of_week
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date, pattern=RecurrencePattern.WEEKLY, interval=1
        )
        assert next_date is None

        # Monthly without day_of_month
        next_date = RecurrenceService.calculate_next_occurrence(
            base_date=base_date, pattern=RecurrencePattern.MONTHLY, interval=1
        )
        assert next_date is None


class TestShouldCreateNextOccurrence:
    """Test should_create_next_occurrence method"""

    def test_non_recurring_task(self):
        """Test with non-recurring task"""
        task = Mock(is_recurring=False)
        result = RecurrenceService.should_create_next_occurrence(
            task, datetime.now(timezone.utc)
        )
        assert result is False

    def test_recurrence_ended_by_date(self):
        """Test when recurrence has ended by date"""
        task = Mock(
            is_recurring=True,
            recurrence_end_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            recurrence_count=None,
        )
        current_date = datetime(2025, 1, 2, tzinfo=timezone.utc)
        result = RecurrenceService.should_create_next_occurrence(task, current_date)
        assert result is False

    def test_recurrence_ended_by_count(self):
        """Test when recurrence has ended by count"""
        task = Mock(
            is_recurring=True,
            recurrence_end_date=None,
            recurrence_count=3,
            id="parent-id",
            recurrence_instances=[
                Mock(id="instance-1"),
                Mock(id="instance-2"),
                Mock(id="instance-3"),
            ],
        )
        current_date = datetime.now(timezone.utc)
        result = RecurrenceService.should_create_next_occurrence(task, current_date)
        assert result is False

    def test_should_create_occurrence(self):
        """Test when occurrence should be created"""
        task = Mock(
            is_recurring=True,
            recurrence_end_date=datetime(2025, 12, 31, tzinfo=timezone.utc),
            recurrence_count=None,
        )
        current_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        result = RecurrenceService.should_create_next_occurrence(task, current_date)
        assert result is True


class TestCreateRecurringInstance:
    """Test create_recurring_instance method"""

    def test_create_instance_basic(self):
        """Test creating a basic recurring instance"""
        db = Mock(spec=Session)
        parent_task = Mock(
            id="parent-id",
            title="Test Task",
            description="Test Description",
            priority="medium",
            user_id="user-1",
            project_id="project-1",
            assigned_to_id="user-2",
            estimated_hours=2.0,
            position=0,
            start_date=datetime(2025, 1, 1, 10, 0, 0),
            due_date=datetime(2025, 1, 1, 18, 0, 0),
            categories=[],
            tags=[],
        )

        occurrence_date = datetime(2025, 1, 8, 10, 0, 0)
        new_task = RecurrenceService.create_recurring_instance(
            db, parent_task, occurrence_date
        )

        assert new_task.title == parent_task.title
        assert new_task.description == parent_task.description
        assert new_task.status == TaskStatus.TODO
        assert new_task.recurrence_parent_id == parent_task.id
        assert new_task.is_recurring is False
        assert new_task.start_date == occurrence_date
        assert new_task.due_date == datetime(2025, 1, 8, 18, 0, 0)  # Same duration

        db.add.assert_called_once_with(new_task)


class TestCreateTaskWithRecurrence:
    """Test create_task_with_recurrence method"""

    def test_create_daily_recurring_task(self):
        """Test creating a daily recurring task"""
        db = Mock(spec=Session)
        db.add = Mock()
        db.flush = Mock()

        task_data = {
            "title": "Daily Task",
            "description": "Daily recurring task",
            "status": TaskStatus.TODO,
            "priority": "medium",
        }

        recurrence_config = RecurrenceConfig(
            pattern=RecurrencePattern.DAILY, interval=1
        )

        task = RecurrenceService.create_task_with_recurrence(
            db, task_data, recurrence_config, "user-1"
        )

        assert task.is_recurring is True
        assert task.recurrence_pattern == RecurrencePattern.DAILY
        assert task.recurrence_interval == 1
        assert task.title == "Daily Task"

        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_create_weekly_recurring_task(self):
        """Test creating a weekly recurring task"""
        db = Mock(spec=Session)
        db.add = Mock()
        db.flush = Mock()

        task_data = {"title": "Weekly Task", "description": "Weekly recurring task"}

        recurrence_config = RecurrenceConfig(
            pattern=RecurrencePattern.WEEKLY,
            interval=1,
            days_of_week=[1, 3, 5],  # Mon, Wed, Fri
        )

        task = RecurrenceService.create_task_with_recurrence(
            db, task_data, recurrence_config, "user-1"
        )

        assert task.is_recurring is True
        assert task.recurrence_pattern == RecurrencePattern.WEEKLY
        assert task.recurrence_days_of_week == "1,3,5"


class TestUpdateRecurrence:
    """Test update_recurrence method"""

    def test_update_non_recurring_to_recurring(self):
        """Test converting non-recurring task to recurring"""
        db = Mock(spec=Session)
        task = Mock(
            is_recurring=False,
            recurrence_pattern=None,
            recurrence_interval=None,
            recurrence_days_of_week=None,
            recurrence_day_of_month=None,
            recurrence_month_of_year=None,
            recurrence_end_date=None,
            recurrence_count=None,
        )

        recurrence_config = RecurrenceConfig(
            pattern=RecurrencePattern.DAILY, interval=2
        )

        updated_task = RecurrenceService.update_recurrence(db, task, recurrence_config)

        assert updated_task.is_recurring is True
        assert updated_task.recurrence_pattern == RecurrencePattern.DAILY
        assert updated_task.recurrence_interval == 2

    def test_update_recurrence_pattern(self):
        """Test updating recurrence pattern"""
        db = Mock(spec=Session)
        task = Mock(
            is_recurring=True,
            recurrence_pattern=RecurrencePattern.DAILY,
            recurrence_interval=1,
            recurrence_days_of_week=None,
            recurrence_day_of_month=None,
            recurrence_month_of_year=None,
            recurrence_end_date=None,
            recurrence_count=None,
        )

        recurrence_config = RecurrenceConfig(
            pattern=RecurrencePattern.WEEKLY, interval=1, days_of_week=[1, 3]
        )

        updated_task = RecurrenceService.update_recurrence(db, task, recurrence_config)

        assert updated_task.recurrence_pattern == RecurrencePattern.WEEKLY
        assert updated_task.recurrence_days_of_week == "1,3"


class TestDeleteRecurrence:
    """Test delete_recurrence method"""

    def test_delete_recurrence_keep_instances(self):
        """Test deleting recurrence but keeping instances"""
        db = Mock(spec=Session)
        task = Mock(
            is_recurring=True,
            recurrence_pattern=RecurrencePattern.DAILY,
            recurrence_interval=1,
            recurrence_days_of_week=None,
            recurrence_day_of_month=None,
            recurrence_month_of_year=None,
            recurrence_end_date=None,
            recurrence_count=None,
            recurrence_instances=[],
        )

        RecurrenceService.delete_recurrence(db, task, delete_instances=False)

        assert task.is_recurring is False
        assert task.recurrence_pattern is None
        assert task.recurrence_interval is None

    def test_delete_recurrence_with_instances(self):
        """Test deleting recurrence and instances"""
        db = Mock(spec=Session)
        db.delete = Mock()

        instance1 = Mock(status=TaskStatus.TODO)
        instance2 = Mock(status=TaskStatus.DONE)
        instance3 = Mock(status=TaskStatus.TODO)

        task = Mock(
            is_recurring=True,
            recurrence_pattern=RecurrencePattern.DAILY,
            recurrence_interval=1,
            recurrence_days_of_week=None,
            recurrence_day_of_month=None,
            recurrence_month_of_year=None,
            recurrence_end_date=None,
            recurrence_count=None,
            recurrence_instances=[instance1, instance2, instance3],
        )

        RecurrenceService.delete_recurrence(db, task, delete_instances=True)

        assert task.is_recurring is False
        # Should delete uncompleted instances
        assert db.delete.call_count == 2
        db.delete.assert_any_call(instance1)
        db.delete.assert_any_call(instance3)
        # Should not delete completed instance
        assert instance2 not in [call[0][0] for call in db.delete.call_args_list]
