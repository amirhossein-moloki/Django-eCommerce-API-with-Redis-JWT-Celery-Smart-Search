from decimal import Decimal

from account.factories import AddressFactory, UserFactory
from coupons.factories import CouponFactory
from shop.factories import ProductFactory
from .models import Order, OrderItem


def OrderFactory(**kwargs):
    defaults = {
        "user": kwargs.get("user") or UserFactory(),
        "address": kwargs.get("address") or AddressFactory(),
        "status": kwargs.get("status") or Order.Status.PENDING,
        "coupon": kwargs.get("coupon") or CouponFactory(),
    }
    defaults.setdefault(
        "discount_amount", getattr(defaults["coupon"], "discount_percent", 0)
    )
    defaults.update(kwargs)
    return Order.objects.create(**defaults)


def OrderItemFactory(**kwargs):
    order = kwargs.get("order") or OrderFactory()
    product = kwargs.get("product") or ProductFactory()
    defaults = {
        "order": order,
        "product": product,
        "quantity": kwargs.get("quantity") or 1,
        "price": kwargs.get("price") or Decimal(product.price),
    }
    defaults.update(kwargs)
    return OrderItem.objects.create(**defaults)
