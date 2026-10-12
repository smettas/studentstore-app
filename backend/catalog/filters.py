from decimal import Decimal, InvalidOperation
from django.db.models import Q
from rest_framework.exceptions import ValidationError


def filter_products(queryset, params):
    """Public catalog filters; study levels never restrict purchasing."""
    search = params.get("search", "").strip()
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
            | Q(sku__icontains=search) | Q(brand__name__icontains=search)
        )

    for key, field in (("category", "category__slug"), ("brand", "brand__slug"),
                       ("study_level", "study_levels__slug"), ("product_type", "product_type")):
        value = params.get(key)
        if value:
            queryset = queryset.filter(**{field: value})

    for key, lookup in (("min_price", "gte"), ("max_price", "lte")):
        value = params.get(key)
        if value is not None:
            try:
                amount = Decimal(value)
                if not amount.is_finite() or amount < 0:
                    raise ValueError
            except (InvalidOperation, ValueError, TypeError):
                raise ValidationError({key: "Enter a valid non-negative price."})
            # Compare the actual selling price, not the original list price.
            from django.db.models import F
            from django.db.models.functions import Coalesce
            queryset = queryset.annotate(selling_price=Coalesce("discount_price", "price"))
            queryset = queryset.filter(**{f"selling_price__{lookup}": amount})

    if params.get("in_stock") in ("true", "1"):
        queryset = queryset.filter(stock__gt=0)
    elif params.get("in_stock") not in (None, "false", "0"):
        raise ValidationError({"in_stock": "Use true or false."})

    return queryset.distinct()
