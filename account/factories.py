import itertools
import uuid

from django.contrib.auth import get_user_model

from .models import Address

_user_counter = itertools.count()


def _next_suffix():
    return next(_user_counter)


def UserFactory(**kwargs):
    user_model = get_user_model()
    idx = _next_suffix()
    defaults = {
        "phone_number": f"+100000000{idx:03d}",
        "email": f"user{idx}@example.com",
        "username": f"user_{idx}",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
    }
    password = kwargs.pop("password", "defaultpassword")
    defaults.update(kwargs)

    user = user_model.objects.create(**defaults)
    user.set_password(password)
    user.save()
    return user


def AdminUserFactory(**kwargs):
    return UserFactory(is_staff=True, is_superuser=True, **kwargs)


def AddressFactory(**kwargs):
    defaults = {
        "user": kwargs.get("user") or UserFactory(),
        "province": "Test Province",
        "city": "Test City",
        "postal_code": f"{uuid.uuid4().int % 100000:05d}",
        "address_detail": "123 Test Street",
        "receiver_name": "Test Receiver",
        "receiver_phone_number": f"+1999999{_next_suffix():05d}",
    }
    defaults.update(kwargs)
    return Address.objects.create(**defaults)
