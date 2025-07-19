"""
User factory for generating test data.
"""
import factory
from factory.fuzzy import FuzzyChoice
from faker import Faker
import uuid
from app.db.models import User
from app.core.middleware.jwt_auth_backend import get_password_hash

fake = Faker()


class UserFactory(factory.Factory):
    """
    Factory for creating User instances for testing.
    """
    class Meta:
        model = User
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    username = factory.LazyFunction(lambda: fake.user_name())
    email = factory.LazyFunction(lambda: fake.email())
    hashed_password = factory.LazyFunction(lambda: get_password_hash("testpass123"))
    is_active = True
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to handle SQLAlchemy models."""
        return model_class(**kwargs)
    
    @classmethod
    def create_batch(cls, size, **kwargs):
        """Create multiple users with unique usernames and emails."""
        users = []
        for i in range(size):
            user_kwargs = kwargs.copy()
            if 'username' not in user_kwargs:
                user_kwargs['username'] = f"user_{fake.user_name()}_{i}"
            if 'email' not in user_kwargs:
                user_kwargs['email'] = f"user_{i}_{fake.email()}"
            users.append(cls.create(**user_kwargs))
        return users


class UserCreateFactory(factory.Factory):
    """
    Factory for creating UserCreate schema instances (for API requests).
    """
    class Meta:
        model = dict
    
    username = factory.LazyFunction(lambda: fake.user_name())
    email = factory.LazyFunction(lambda: fake.email())
    password = "testpass123"
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Return a dictionary for API requests."""
        return kwargs