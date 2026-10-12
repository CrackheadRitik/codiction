"""
Codiction — User Manager

Custom manager for the User model.
Provides create_user() and create_superuser() methods.
"""

from typing import Optional

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom manager for the User model.

    Uses email as the unique identifier instead of username.
    """

    use_in_migrations = True

    def _create_user(
        self,
        email: str,
        password: Optional[str] = None,
        **extra_fields,
    ):
        """Internal method to create and save a user."""
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self,
        email: str,
        password: Optional[str] = None,
        **extra_fields,
    ):
        """Create a regular user."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self,
        email: str,
        password: Optional[str] = None,
        **extra_fields,
    ):
        """Create a superuser (for admin panel)."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)
