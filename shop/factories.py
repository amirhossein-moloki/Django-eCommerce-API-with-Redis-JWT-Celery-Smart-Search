import itertools
from decimal import Decimal

from account.factories import UserFactory
from .models import Category, Product, Review

_category_counter = itertools.count()
_product_counter = itertools.count()


def CategoryFactory(**kwargs):
    idx = next(_category_counter)
    defaults = {"name": f"Category {idx}", "slug": f"category-{idx}"}
    defaults.update(kwargs)
    return Category.objects.create(**defaults)


def ProductFactory(**kwargs):
    idx = next(_product_counter)
    defaults = {
        "user": kwargs.get("user") or UserFactory(),
        "category": kwargs.get("category") or CategoryFactory(),
        "name": kwargs.get("name") or f"Product {idx}",
        "slug": kwargs.get("slug") or f"product-{idx}",
        "description": kwargs.get("description") or "Sample product description",
        "price": kwargs.get("price") or Decimal("100.00"),
        "stock": kwargs.get("stock") or 10,
        "weight": kwargs.get("weight") or Decimal("1.00"),
        "length": kwargs.get("length") or Decimal("1.00"),
        "width": kwargs.get("width") or Decimal("1.00"),
        "height": kwargs.get("height") or Decimal("1.00"),
    }
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


def ReviewFactory(**kwargs):
    defaults = {
        "product": kwargs.get("product") or ProductFactory(),
        "user": kwargs.get("user") or UserFactory(),
        "rating": kwargs.get("rating") or 3,
        "comment": kwargs.get("comment") or "Test review comment",
    }
    defaults.update(kwargs)
    return Review.objects.create(**defaults)
