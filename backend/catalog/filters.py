from decimal import Decimal, InvalidOperation
from django.db.models import Q
from rest_framework.exceptions import ValidationError


def filter_products(queryset, params):
    """Public catalog filters; study levels never restrict purchasing."""
    search = params.get("search", "").strip()
    if search:
        queryset = smart_product_search(queryset, search)

    # Comma-separated category slugs are used by home shortcuts that span
    # multiple catalogue categories (e.g. Pens and Pencils).
    category_slugs = params.get("category_slugs", "")
    if category_slugs:
        slugs = [slug.strip() for slug in category_slugs.split(",") if slug.strip()]
        if not slugs or len(slugs) > 30:
            raise ValidationError({"category_slugs": "Provide 1 to 30 category slugs."})
        queryset = queryset.filter(category__slug__in=slugs)

    for key, field in (("category", "category__slug"), ("brand", "brand__slug"),
                       ("study_level", "study_levels__slug"), ("product_type", "product_type")):
        value = params.get(key)
        if value:
            queryset = queryset.filter(**{field: value})

    # Optional pack/subcategory filtering uses existing JSON metadata; no schema migration.
    for key, field in (("pack_quantity", "specifications__pack_quantity__iexact"),
                       ("subcategory", "specifications__subcategory__iexact")):
        value = params.get(key)
        if value:
            value = value.strip()
            if len(value) > 120:
                raise ValidationError({key: "Maximum 120 characters."})
            queryset = queryset.filter(**{field: value})

    department = params.get("department")
    if department:
        queryset = queryset.filter(category__parent__slug=department.strip())

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


# Shared search for web and mobile: brand/product names, spaces and common typos.
# Exact results take priority; fuzzy matching runs only if exact search finds nothing.
def smart_product_search(queryset, search):
    import re
    import unicodedata
    from difflib import SequenceMatcher
    from django.db.models import Case, IntegerField, When

    def normalize(text):
        text = unicodedata.normalize('NFKC', str(text or '')).casefold()
        return re.sub(r'[^a-z0-9]+', '', text)

    raw = str(search or '').strip()[:100]
    if not raw:
        return queryset
    words = re.findall(r'[a-z0-9]+', raw.casefold())
    exact = (Q(name__icontains=raw) | Q(description__icontains=raw)
             | Q(sku__icontains=raw) | Q(brand__name__icontains=raw))
    # A query like "class mate notebook" should also find "Classmate Notebook".
    if len(words) > 1:
        all_words = Q()
        for word in words:
            all_words &= (Q(name__icontains=word) | Q(brand__name__icontains=word)
                          | Q(category__name__icontains=word))
        exact |= all_words
    result = queryset.filter(exact)
    if result.exists():
        return result

    needle = normalize(raw)
    if len(needle) < 3:
        return queryset.none()
    # Limit candidates to prevent unbounded fuzzy searches as catalog grows.
    candidates = list(queryset.select_related('brand', 'category').only(
        'id', 'name', 'sku', 'brand__name', 'category__name')[:2500])
    ranked = []
    for product in candidates:
        brand = product.brand.name if product.brand_id else ''
        fields = [product.name, brand, product.sku, product.category.name,
                  f'{brand} {product.name}']
        scores = []
        for field in fields:
            cleaned = normalize(field)
            if not cleaned: continue
            score = SequenceMatcher(None, needle, cleaned).ratio()
            if needle in cleaned or cleaned in needle: score = max(score, 0.84)
            for token in re.findall(r'[a-z0-9]+', str(field).casefold()):
                if len(token) >= 3:
                    score = max(score, SequenceMatcher(None, needle, token).ratio())
            scores.append(score)
        score = max(scores, default=0)
        if score >= (0.66 if len(needle) <= 5 else 0.61):
            ranked.append((score, product.pk))
    ranked.sort(reverse=True)
    ids = [pk for _, pk in ranked[:80]]
    if not ids: return queryset.none()
    # Preserve relevance order, including when the view applies default ordering.
    return queryset.filter(pk__in=ids)
