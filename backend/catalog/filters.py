"""Product-only catalogue search and public filters.

Do not search long generic descriptions for short queries: a word such as
'pen' must not match pencil kits, paper or unrelated stationery merely because
an item description happens to mention a pen.  The API is shared by web and
Android, so relevance belongs here rather than in one frontend.
"""
import re
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

from django.db.models import Case, IntegerField, Q, Value, When
from rest_framework.exceptions import ValidationError


# Common spelling errors entered on mobile keyboards. Deliberately small and
# conservative: do not silently reinterpret an unrelated product category.
SPELLING = {
    "staler": "stapler", "stpler": "stapler", "staplar": "stapler",
    "stapller": "stapler", "pensil": "pencil", "pencel": "pencil",
    "ballpen": "pen", "notbook": "notebook", "noteook": "notebook",
}
SINGULAR = {"pens": "pen", "pencils": "pencil", "staplers": "stapler", "erasers": "eraser", "rulers": "ruler", "pins": "pin", "markers": "marker", "notebooks": "notebook", "folders": "folder"}
STOP_WORDS = {"and", "or", "the", "with", "for", "of", "a", "an", "to", "in", "by"}
# These terms represent product TYPES, not text anywhere in descriptions.
# Do not let fuzzy fallback broaden a specific type to something else.
STRICT_TYPES = {
    "pen", "pencil", "stapler", "staple", "pin", "paper", "notebook",
    "eraser", "ruler", "marker", "sharpener", "glue", "tape", "file",
    "folder", "bag", "calculator", "scissor", "brush", "paint",
}
PLURAL = {
    "pen": "pens?", "pencil": "pencils?", "stapler": "staplers?",
    "staple": "staples?", "pin": "pins?", "notebook": "notebooks?",
    "eraser": "erasers?", "ruler": "rulers?", "marker": "markers?",
    "sharpener": "sharpeners?", "file": "files?", "folder": "folders?",
    "bag": "bags?", "calculator": "calculators?", "brush": "brush(?:es)?",
    "scissor": "scissors?", "paint": "paints?", "tape": "tapes?",
}


def tokenize(raw):
    tokens = re.findall(r"[a-z0-9]+", str(raw or "").casefold()[:100])
    return [SINGULAR.get(SPELLING.get(token, token), SPELLING.get(token, token)) for token in tokens if token not in STOP_WORDS][:8]


def word_regex(token):
    # PostgreSQL and SQLite both support this portable regular expression.
    # It ensures "pen" != "pencil" != "open" != "Pentel".
    if token in PLURAL:
        body = PLURAL[token]
    elif token.endswith("s") and len(token) > 4 and not token.endswith("ss"):
        body = re.escape(token[:-1]) + "s?"
    else:
        body = re.escape(token) + ("s?" if len(token) > 3 and not token.endswith("s") else "")
    return r"(^|[^a-z0-9])(" + body + r")($|[^a-z0-9])"


def keyword_query(tokens, fields):
    query = Q()
    for token in tokens:
        alternatives = Q()
        pattern = word_regex(token)
        for field in fields:
            alternatives |= Q(**{f"{field}__iregex": pattern})
        query &= alternatives
    return query


def smart_product_search(queryset, search):
    raw = str(search or "").strip()[:100]
    tokens = tokenize(raw)
    if not tokens:
        return queryset.none() if raw else queryset

    # 1. Search only the *product title*, with real word boundaries, so a
    #    'pen' query never returns an unrelated product via its description.
    title_matches = queryset.filter(keyword_query(tokens, ("name",)))
    if title_matches.exists():
        # Relevance first for the default sort: title begins with the query,
        # followed by exact phrase matches, then other title-token matches.
        phrase = " ".join(tokens)
        return title_matches.annotate(search_rank=Case(
            When(name__istartswith=phrase, then=Value(0)),
            When(name__icontains=phrase, then=Value(1)),
            default=Value(2), output_field=IntegerField(),
        ))

    # 2. If there are no title matches, a user can explicitly search a brand
    #    (e.g. "Classmate") or an exact SKU without showing unrelated goods.
    brand_matches = queryset.filter(keyword_query(tokens, ("brand__name", "name")))
    if brand_matches.exists():
        return brand_matches.annotate(search_rank=Value(3, output_field=IntegerField()))
    if len(tokens) == 1 and len(tokens[0]) >= 4:
        sku_matches = queryset.filter(sku__iexact=raw)
        if sku_matches.exists():
            return sku_matches.annotate(search_rank=Value(3, output_field=IntegerField()))

    # 3. Only full, explicit category terms can expand a search to a whole
    #    category; NEVER match categories from a single generic word.
    if len(tokens) >= 2:
        exact_category = queryset.filter(keyword_query(tokens, ("category__name",)))
        if exact_category.exists():
            return exact_category.annotate(search_rank=Value(4, output_field=IntegerField()))

    # 4. Optional typo tolerance, limited to longer non-type words and title
    #    tokens. No broad description/category/substring search is performed.
    if len(tokens) != 1 or len(tokens[0]) <= 4 or tokens[0] in STRICT_TYPES:
        return queryset.none()
    needle = tokens[0]
    ids = []
    for pk, name in queryset.order_by("id").values_list("pk", "name")[:5000]:
        words = re.findall(r"[a-z0-9]+", (name or "").casefold())
        if any(SequenceMatcher(None, needle, word).ratio() >= 0.86 for word in words):
            ids.append(pk)
        if len(ids) >= 80:
            break
    return queryset.filter(pk__in=ids).annotate(search_rank=Value(5, output_field=IntegerField())) if ids else queryset.none()


def filter_products(queryset, params):
    """Public catalogue filters; study levels never restrict purchasing."""
    search = params.get("search", "").strip()
    if search:
        queryset = smart_product_search(queryset, search)

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

    # Preserve previously installed Batch-02 pack and department filters.
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
            from django.db.models.functions import Coalesce
            queryset = queryset.annotate(selling_price=Coalesce("discount_price", "price"))
            queryset = queryset.filter(**{f"selling_price__{lookup}": amount})

    if params.get("in_stock") in ("true", "1"):
        queryset = queryset.filter(stock__gt=0)
    elif params.get("in_stock") not in (None, "false", "0"):
        raise ValidationError({"in_stock": "Use true or false."})
    return queryset.distinct()
