"""Strict CSV/photo-number matching; no image extraction to temp disk."""
import csv
import io
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 20 * 1024 * 1024
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}


def normalized(value):
    return re.sub(r'[^a-z0-9]', '', str(value or '').casefold())


ALIASES = {
    'serial': ('image number', 'image no', 'image id', 'photo number', 'photo no',
               'photo id', 'serial', 'serial no', 's no', 'sl no', 'sno',
               'number', 'product no', 'product number'),
    'image_file': ('image filename', 'image file', 'photo file', 'photo filename',
                   'product image', 'image path', 'photo path', 'image', 'photo', 'filename'),
    'sku': ('sku', 'product sku'),
    'name': ('product name', 'item name', 'product title', 'proposed product title',
             'title', 'name', 'product'),
    'brand': ('brand', 'brand name', 'manufacturer'),
    'category': ('category', 'suggested category', 'product category', 'main category'),
    'subcategory': ('subcategory', 'sub category', 'sub-category'),
    'description': ('description', 'product description', 'item description', 'details'),
    'pack': ('pack quantity', 'pack size', 'pack details', 'pack', 'quantity per pack',
             'units per pack', 'pack configuration', 'qty per pack',
             'variant', 'variant unverified', 'pack configuration unverified',
             'saleable variant', 'pack type', 'pack / variant to find'),
    'pack_verified': ('packaging quantity verified', 'pack quantity verified'),
    'mrp': ('mrp', 'mrp inr', 'mrp rs', 'list price', 'original price',
            'provisional price reference', 'price reference', 'manufacturer mrp'),
    'selling': ('selling price', 'selling price inr', 'sale price', 'offer price',
                'provisional offer', 'discount price'),
}


def _header_map(headers):
    lookup = {normalized(h): h for h in headers if h}
    result = {}
    for field, aliases in ALIASES.items():
        result[field] = next((lookup[normalized(k)] for k in aliases if normalized(k) in lookup), None)
    return result


def serial_number(value):
    text = str(value or '').strip()
    m = re.fullmatch(r'0*(\d{1,4})(?:\.0+)?', text)
    if not m:
        m = re.fullmatch(r'(?i:OJAS-B02-)0*(\d{1,4})', text)
    if not m:
        raise ValueError('Photo/serial number must be an integer from 1 to 2000')
    n = int(m.group(1))
    if not 1 <= n <= 2000:
        raise ValueError('Image number is outside batch-02 range 1..2000')
    return n


def filename_number(name):
    """Do not guess from arbitrary digits embedded in product names."""
    stem = Path(name).stem.strip()
    patterns = (
        r'0*(\d{1,4})',
        r'(?i:(?:img|image|photo|product|ojas[-_]?b02)[-_ ]*)0*(\d{1,4})',
        r'0*(\d{1,4})(?:[-_ ].+)',
    )
    for pat in patterns:
        m = re.fullmatch(pat, stem)
        if m:
            n = int(m.group(1))
            return n if 1 <= n <= 2000 else None
    return None


def read_rows(path):
    path = Path(path)
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        headers = reader.fieldnames or []
        mapped = _header_map(headers)
        if not mapped['name'] or not mapped['category']:
            raise ValueError('CSV must have product name and category columns; headers: ' + ', '.join(headers))
        if not (mapped['serial'] or mapped['image_file'] or mapped['sku']):
            raise ValueError('CSV needs a photo number, serial, image filename or batch SKU column; row order is never used as mapping')
        rows = []
        for line, row in enumerate(reader, 2):
            if not any(str(v or '').strip() for v in row.values()):
                continue
            extracted = {k: str(row.get(header) or '').strip() if header else '' for k, header in mapped.items()}
            extracted['line'] = line
            # 'Pack / Variant To Find' is a research target, not a confirmed manufacturer pack.
            # Never silently treat it as verified even if it looks like 'Pack of 5'.
            pack_header = normalized(mapped['pack']) if mapped['pack'] else ''
            pack_confirmation = extracted.get('pack_verified', '').strip().casefold()
            extracted['pack_unverified_source'] = bool(
                'unverified' in pack_header or 'tofind' in pack_header
                or (mapped['pack_verified'] and pack_confirmation not in
                    {'yes', 'y', 'true', '1', 'verified'}))
            extracted['raw'] = {str(k): str(v or '') for k, v in row.items() if k is not None}
            rows.append(extracted)
        return rows


class ImageSource:
    """Read numbered photos from a directory tree or ZIP; ambiguous numbers fail closed."""
    def __init__(self, path):
        self.path = Path(path)
        self.zip_file = None
        self.by_number = defaultdict(list)
        self.by_basename = defaultdict(list)
        if self.path.is_file() and zipfile.is_zipfile(self.path):
            self.zip_file = zipfile.ZipFile(self.path)
            names = [i.filename for i in self.zip_file.infolist()
                     if not i.is_dir() and i.file_size <= MAX_IMAGE_BYTES]
        elif self.path.is_dir():
            names = [str(p.relative_to(self.path)).replace('\\', '/')
                     for p in self.path.rglob('*') if p.is_file()]
        else:
            raise ValueError(f'Image source must be an existing folder or ZIP: {self.path}')
        for name in names:
            if Path(name).suffix.lower() not in EXTENSIONS:
                continue
            n = filename_number(Path(name).name)
            if n is not None:
                self.by_number[n].append(name)
            self.by_basename[Path(name).name.casefold()].append(name)

    def match(self, number, filename=''):
        # Explicit CSV filename disambiguates multiple photos, but must match serial.
        if filename:
            basename = Path(filename.replace('\\', '/')).name.casefold()
            candidates = self.by_basename.get(basename, [])
            if len(candidates) != 1:
                raise ValueError(f'CSV image filename {filename!r} matched {len(candidates)} photographs')
            actual_n = filename_number(Path(candidates[0]).name)
            if actual_n != number:
                raise ValueError(f'CSV image filename {filename!r} does not match photo number {number}')
            return candidates[0]
        candidates = self.by_number.get(number, [])
        if len(candidates) != 1:
            raise ValueError(f'Image {number:04d} matched {len(candidates)} photographs (missing or ambiguous)')
        return candidates[0]

    def read(self, name):
        if self.zip_file:
            item = self.zip_file.getinfo(name)
            if item.file_size > MAX_IMAGE_BYTES:
                raise ValueError('Photo exceeds 20 MB')
            data = self.zip_file.read(name)
        else:
            p = self.path / name
            if p.stat().st_size > MAX_IMAGE_BYTES:
                raise ValueError('Photo exceeds 20 MB')
            data = p.read_bytes()
        if len(data) > MAX_IMAGE_BYTES:
            raise ValueError('Photo exceeds 20 MB')
        try:
            with Image.open(io.BytesIO(data)) as im:
                fmt = im.format
                im.verify()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise ValueError('Invalid or corrupted image') from exc
        if fmt not in {'JPEG', 'PNG', 'WEBP'}:
            raise ValueError(f'Unsupported image encoding {fmt}')
        return data

    def close(self):
        if self.zip_file:
            self.zip_file.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
