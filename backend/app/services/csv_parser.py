"""CSV parsing and row validation. Pure standard library (no DB, no web framework)."""
from __future__ import annotations

import csv
import io
import re

FIELDS = ["company_name", "contact_name", "email", "job_title", "industry", "employee_count",
          "location", "website", "annual_revenue", "description", "notes"]
REQUIRED = "company_name"
MAX_LEN = {"company_name": 255, "contact_name": 255, "email": 255, "job_title": 255,
           "industry": 120, "location": 255, "website": 255, "description": 5000, "notes": 5000}

ALIASES = {
    "company_name": {"company_name", "company", "organization", "organisation", "account", "account_name", "business_name"},
    "contact_name": {"contact_name", "contact", "name", "full_name", "person"},
    "email": {"email", "email_address", "e_mail", "contact_email"},
    "job_title": {"job_title", "title", "position", "role"},
    "industry": {"industry", "sector", "vertical"},
    "employee_count": {"employee_count", "employees", "company_size", "headcount", "size", "number_of_employees"},
    "location": {"location", "city", "country", "region", "hq", "headquarters"},
    "website": {"website", "url", "web", "domain", "company_website"},
    "annual_revenue": {"annual_revenue", "revenue", "yearly_revenue", "arr"},
    "description": {"description", "about", "business_description", "summary"},
    "notes": {"notes", "note", "comments"},
}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class CsvFileError(ValueError):
    """The file as a whole cannot be processed."""


def normalize_header(h: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (h or "").strip().lower()).strip("_")


def detect_mapping(headers: list[str]) -> dict[str, str | None]:
    """csv header -> internal field (or None if unrecognised / duplicate)."""
    used: set[str] = set()
    out: dict[str, str | None] = {}
    for h in headers:
        n = normalize_header(h)
        field = next((f for f, names in ALIASES.items() if n in names), None)
        if field and field not in used:
            used.add(field)
            out[h] = field
        else:
            out[h] = None
    return out


def parse_csv(content: bytes, mapping: dict[str, str] | None = None, max_rows: int = 5000) -> dict:
    """Returns {headers, mapping, rows: [{"row_number": int, "raw": {field: str}}]}."""
    if not content or not content.strip():
        raise CsvFileError("The file is empty.")
    if b"\x00" in content:
        raise CsvFileError("The file does not look like a text CSV file.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise CsvFileError("The file must be UTF-8 encoded. Re-save it as 'CSV UTF-8'.")
    reader = csv.reader(io.StringIO(text))
    try:
        headers = next(reader)
    except StopIteration:
        raise CsvFileError("The file is empty.")
    except csv.Error as e:
        raise CsvFileError(f"Malformed CSV: {e}")
    headers = [h.strip() for h in headers]
    if not any(headers):
        raise CsvFileError("The first row must contain column names.")

    if mapping is None:
        mapping = detect_mapping(headers)
    else:
        bad = [f for f in mapping.values() if f and f not in FIELDS]
        if bad:
            raise CsvFileError(f"Unknown target field(s) in mapping: {', '.join(sorted(set(bad)))}")
        targets = [f for f in mapping.values() if f]
        if len(targets) != len(set(targets)):
            raise CsvFileError("Two CSV columns are mapped to the same field.")
        mapping = {h: mapping.get(h) or None for h in headers}
    if REQUIRED not in mapping.values():
        raise CsvFileError("Missing required column 'company_name' (accepted names include: company, "
                           f"organization, account). Columns found: {', '.join(h for h in headers if h)}")

    rows = []
    try:
        for cells in reader:
            if not any(c.strip() for c in cells):
                continue
            if len(rows) >= max_rows:
                raise CsvFileError(f"Too many rows. The limit is {max_rows} rows per import.")
            raw = {f: "" for f in FIELDS}
            extra = len(cells) > len(headers)
            for h, c in zip(headers, cells):
                f = mapping.get(h)
                if f:
                    raw[f] = c.strip()
            rows.append({"row_number": reader.line_num, "raw": raw, "extra_columns": extra})
    except csv.Error as e:
        raise CsvFileError(f"Malformed CSV near line {reader.line_num}: {e}")
    if not rows:
        raise CsvFileError("The file has a header row but no data rows.")
    return {"headers": headers, "mapping": mapping, "rows": rows}


def _parse_number(v: str, allow_float: bool = False):
    s = re.sub(r"[,\s$€£_]", "", v)
    if not re.fullmatch(r"\d+(\.\d+)?", s):
        raise ValueError
    f = float(s)
    return int(f)


def validate_row(raw: dict, extra_columns: bool = False) -> tuple[dict, list[str]]:
    errors: list[str] = []
    data: dict = {}
    for f in FIELDS:
        v = (raw.get(f) or "").strip()
        data[f] = v or None
    if extra_columns:
        errors.append("Row has more cells than the header row (possible unquoted comma).")
    if not data["company_name"]:
        errors.append("company_name is required.")
    for f, limit in MAX_LEN.items():
        if data[f] and len(data[f]) > limit:
            errors.append(f"{f} is longer than {limit} characters.")
    if data["email"]:
        data["email"] = data["email"].lower()
        if not EMAIL_RE.match(data["email"]):
            errors.append(f"email '{data['email']}' is not a valid email address.")
    if data["website"] and re.search(r"\s", data["website"]):
        errors.append("website must not contain spaces.")
    for f, cap in (("employee_count", 10_000_000), ("annual_revenue", 10**13)):
        if data[f] is not None:
            try:
                n = _parse_number(data[f])
                if n > cap:
                    raise ValueError
                data[f] = n
            except ValueError:
                errors.append(f"{f} '{raw.get(f)}' must be a non-negative number (digits only).")
                data[f] = None
    return data, errors


def dedupe_key(company_name: str | None, email: str | None) -> str:
    return f"{(company_name or '').strip().lower()}|{(email or '').strip().lower()}"


def apply_corrections(rows: list[dict], corrections: dict | None) -> None:
    """Mutates rows in place. corrections = {"<row_number>": {field: value}}; unknown fields ignored."""
    if not corrections:
        return
    for r in rows:
        fix = corrections.get(str(r["row_number"]))
        if isinstance(fix, dict):
            for k, v in fix.items():
                if k in FIELDS and isinstance(v, (str, int, float)):
                    r["raw"][k] = str(v).strip()
            r["extra_columns"] = False  # a manual correction resolves the structural warning


def classify(rows: list[dict], existing_keys: set[str]) -> list[dict]:
    """Adds status (valid|invalid|duplicate), errors, data, duplicate_of to each row."""
    seen: set[str] = set()
    out = []
    for r in rows:
        data, errors = validate_row(r["raw"], r.get("extra_columns", False))
        status, dup_of = "valid", None
        if errors:
            status = "invalid"
        else:
            key = dedupe_key(data["company_name"], data["email"])
            if key in existing_keys:
                status, dup_of = "duplicate", "database"
            elif key in seen:
                status, dup_of = "duplicate", "file"
            seen.add(key)
        out.append({"row_number": r["row_number"], "status": status, "errors": errors,
                    "data": data, "duplicate_of": dup_of})
    return out


# ---- CSV export safety -------------------------------------------------------
def csv_safe(value) -> str:
    """Neutralise spreadsheet formula injection when writing CSV."""
    if value is None:
        return ""
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s
