"""
Task factory for generating test data.
"""

import uuid

import factory
from factory.fuzzy import FuzzyChoice
from faker import Faker

from app.db.models import Task, TaskStatus

fake = Faker()


class TaskFactory(factory.Factory):
    """
    Factory for creating Task instances for testing.
    """

    class Meta:
        model = Task

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    title = factory.LazyFunction(lambda: fake.catch_phrase())
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    status = FuzzyChoice([status.value for status in TaskStatus])
    user_id = None  # Must be provided when creating

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to handle SQLAlchemy models."""
        if "user_id" not in kwargs or kwargs["user_id"] is None:
            raise ValueError("user_id must be provided when creating a Task")
        return model_class(**kwargs)


class TaskCreateFactory(factory.Factory):
    """
    Factory for creating TaskCreate schema instances (for API requests).
    """

    class Meta:
        model = dict

    title = factory.LazyFunction(lambda: fake.catch_phrase())
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    status = FuzzyChoice(["todo", "in_progress", "done"])

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Return a dictionary for API requests."""
        return kwargs


class TaskUpdateFactory(factory.Factory):
    """
    Factory for creating TaskUpdate schema instances (for API requests).
    """

    class Meta:
        model = dict

    title = factory.LazyFunction(lambda: fake.catch_phrase())
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    status = FuzzyChoice(["todo", "in_progress", "done"])

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Return a dictionary for API requests."""
        # Remove None values for partial updates
        return {k: v for k, v in kwargs.items() if v is not None}
