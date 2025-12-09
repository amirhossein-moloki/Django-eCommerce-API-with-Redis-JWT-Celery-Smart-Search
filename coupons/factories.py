import itertools
from datetime import timedelta

from django.utils import timezone

from .models import Coupon

_coupon_counter = itertools.count()


def CouponFactory(**kwargs):
    idx = next(_coupon_counter)
    defaults = {
        "code": f"COUPON{idx}",
        "valid_from": timezone.now(),
        "valid_to": timezone.now() + timedelta(days=7),
        "discount_percent": 10,
        "max_usage_count": 10,
        "is_active": True,
    }
    defaults.update(kwargs)
    return Coupon.objects.create(**defaults)
