"""Transparent provisional retail planning estimates, never manufacturer-verified."""
import hashlib
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def number(raw):
    raw = re.sub(r'(?i)(inr|rs\.?|₹|,|\s)', '', str(raw or ''))
    if not raw:
        return None
    try:
        value = Decimal(raw)
        return value if value.is_finite() and value > 0 else None
    except InvalidOperation:
        return None


def pack_details(raw, title):
    """Returns raw customer label, multiplier for packs of units, review-needed flag."""
    text = str(raw or '').strip()
    source = text or title
    match = re.search(r'(?i)(?:pack\s*of|set\s*of|box\s*of)\s*(\d{1,3})\b', source)
    if match:
        n = int(match.group(1))
        return (text or f'Pack of {n}', n, n <= 0)
    match = re.search(r'(?i)\b(\d{1,3})\s*(?:pieces?|pcs?|units?)\b', source)
    if match:
        n = int(match.group(1))
        return (text or f'{n} Pieces', n, n <= 0)
    match = re.search(r'(?i)\b(\d{1,3})\s*(?:colou?rs?|shades?)\b', source)
    if match:
        # Colours is a set specification, NOT a multiplier of individually sold sets.
        return (text or f'{match.group(1)} Colours', 1, False)
    if re.search(r'(?i)\b(single|one piece|1 piece|1 pc|1 unit|each|per piece)\b', source):
        return (text or 'Single Piece', 1, False)
    if re.search(r'(?i)\b(1 set|one set|geometry box|1 box)\b', source):
        return (text or '1 Set', 1, False)
    if text:
        return (text, 1, True)  # Preserve exact CSV wording for human review.
    return ('', 1, True)  # Never invent manufacturer pack quantities.


RULES = [
    ('geometry box', 160), ('compass', 95), ('calculator', 260),
    ('colour pencil', 120), ('color pencil', 120), ('sketch pen', 95),
    ('water colour', 110), ('watercolor', 110), ('paint', 85),
    ('highlighter', 45), ('marker', 45), ('gel pen', 20), ('ball pen', 15),
    ('pen', 20), ('sharpener', 12), ('eraser', 12), ('pencil', 12),
    ('notebook', 65), ('register', 85), ('drawing book', 70),
    ('diary', 115), ('file folder', 35), ('folder', 35), ('file', 35),
    ('stapler', 85), ('glue', 40), ('adhesive', 40), ('tape', 35),
    ('scale', 25), ('ruler', 25), ('crayon', 80), ('brush', 45),
    ('scissor', 90), ('paper', 60), ('chart', 20), ('bag', 420),
]


def estimate_prices(row, multiplier):
    """Use valid CSV price references if present; otherwise deterministic type estimate."""
    mrp = number(row.get('mrp'))
    selling = number(row.get('selling'))
    if mrp and selling and selling > mrp:
        raise ValueError('CSV selling price exceeds CSV MRP')
    if not mrp and selling:
        mrp = (selling / Decimal('0.88')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    if not mrp:
        name = (row.get('name', '') + ' ' + row.get('category', '')).casefold()
        base = next((v for token, v in RULES if token in name), 79)
        brand = row.get('brand', '').casefold()
        # Common premium brand price bands are heuristics, never advertised as verified MSRP.
        factor = Decimal('1.15') if any(k in brand for k in
            ('faber', 'camlin', 'classmate', 'pilot', 'staedtler', 'maped', 'parker')) else Decimal('1')
        estimate = Decimal(base) * factor * Decimal(multiplier)
        mrp = (estimate / Decimal('5')).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * Decimal('5')
        mrp = max(Decimal('10'), mrp)
    if not selling:
        selling = (mrp * Decimal('0.90')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    if selling >= mrp:
        selling = None  # Django admin requires discount_price strictly below MRP.
    if mrp > Decimal('99999999.99') or (selling and selling > Decimal('99999999.99')):
        raise ValueError('Price exceeds database field range')
    return mrp.quantize(Decimal('.01')), selling.quantize(Decimal('.01')) if selling else None


def estimated_stock(sku):
    """Reproducible 12..40 units; does NOT represent physical inventory."""
    return 12 + int.from_bytes(hashlib.sha256(sku.encode('ascii')).digest()[:4], 'big') % 29


def sale_name(title, pack):
    title = str(title or '').strip()
    if pack and pack.casefold() not in title.casefold():
        # Avoid doubles like "Pencil 12 Colours — 12 Colours".
        if not re.search(r'(?i)(?:pack\s*of|\d+\s*(?:pcs?|pieces?|colou?rs?|shades?)|single piece|1 set)\b', title):
            title = f'{title} — {pack}'
    if len(title) > 255:
        raise ValueError('Product name exceeds 255 characters')
    return title
