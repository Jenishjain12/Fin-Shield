from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

PHONE_RE = re.compile(
    r"(?:(?:\+|00)\d{1,3}[\s-]?)?(?:\(?\d{2,5}\)?[\s-]?)?\d{3,5}[\s-]?\d{3,5}(?:[\s-]?\d{2,4})?"
)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.IGNORECASE)
DOMAIN_RE = re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|net|org|in|io|co|info|biz)\b", re.IGNORECASE)
UPI_RE = re.compile(r"\b[a-zA-Z0-9._-]{2,256}@[a-zA-Z]{2,64}\b")
ACCOUNT_RE = re.compile(r"\b(?:a/?c|account(?:\s*(?:no|number|#))?|iban)[:\s#-]*([A-Z0-9]{8,34})\b", re.IGNORECASE)

BTC_RE = re.compile(r"\b(?:bc1[a-zA-HJ-NP-Z0-9]{25,62}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b")
ETH_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
TRON_RE = re.compile(r"\bT[A-Za-z1-9]{33}\b")

RETURN_RATE_RE = re.compile(
    r"(?P<rate>\d+(?:\.\d+)?)\s*%\s*(?P<period>daily|per\s+day|every\s+day|a\s+day|weekly|per\s+week|every\s+week|a\s+week|monthly|per\s+month|every\s+month|a\s+month|annually|per\s+annum|every\s+year|a\s+year|annual(?:ly)?|p\.?a\.?|p\.?m\.?|apy|apr)?",
    re.IGNORECASE,
)
GENERIC_RETURN_RE = re.compile(
    r"(?:returns?|profit|income|yield|roi|gains?)\s+(?:of\s+)?(?:up\s+to\s+)?(?P<rate>\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)

PHRASE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "guaranteed_return",
        re.compile(
            r"guaranteed\s+(?:returns?|profit|income|gains?|yield|growth|payouts?)"
            r"|guaranteed\s+(?:\w+\s+){1,3}(?:returns?|profit|income|gains?|yield|growth|payouts?)"
            r"|assured\s+(?:returns?|profit|income|gains?|yield)"
            r"|100%\s+(?:returns?|profit|income)"
            r"|risk[- ]?free\s+(?:returns?|profit|income|investment)"
            r"|\b(?:zero[- ]risk|100%\s+safe|capital[- ]protected|no[- ]risk)\s+(?:returns?|profit|income|gains?|yield|growth|payouts?)\b"
            r"|\b(?:returns?|profit|income|payouts?)\s+(?:are\s+)?(?:guaranteed|assured|100%\s+guaranteed)\b"
            r"|\b(?:100%|risk[- ]?free)\s+(?:profit|returns?|guarantee)\b"
            r"|\b(?:never\s+lose|zero\s+loss(?:es)?|cannot\s+lose)\b",
            re.I,
        ),
    ),
    (
        "urgency",
        re.compile(
            r"\b(?:act\s+now|limited\s+time(?:frame)?|today\s+only|hurry(?:\s+up)?|last\s+chance|expires?\s+(?:today|tonight|soon)|immediate(?:ly)?\s+(?:join|apply|action)|offer\s+ends\s+soon|only\s+\d+\s*(?:spots?|seats?|slots?)\s+left|limited\s+(?:seats?|slots?|spots?)|don['’]t\s+miss\s+out|closing\s+(?:today|tonight|soon)|window\s+closing)\b",
            re.I,
        ),
    ),
    (
        "advance_payment",
        re.compile(
            r"\b(?:advance(?:\s+payment|\s+fee)?|processing\s+fee|registration\s+fee|pay\s+first|deposit\s+now|upfront\s+fee|upfront\s+deposit|release\s+fee|activation\s+fee|clearance\s+(?:fee|charge)|pay\s+(?:a\s+)?(?:small\s+)?fee\s+to\s+claim)\b",
            re.I,
        ),
    ),
    (
        "credential_request",
        re.compile(
            r"\b(?:otp|cvv|pin|internet\s+banking|netbanking\s+password|debit\s+card\s+(?:details|number)|share\s+(?:your\s+)?(?:otp|pin|password))\b",
            re.I,
        ),
    ),
    (
        "financial_solicitation",
        re.compile(
            r"\b(?:double\s+your\s+money|secret\s+(?:scheme|tip)|insider\s+(?:tip|deal)|quick\s+riches|get\s+rich|multiply\s+your\s+(?:money|investment))\b",
            re.I,
        ),
    ),
    (
        "deposit_incentive",
        re.compile(
            r"\b(?:(?:deposit|welcome|signup|sign-up|trading|account)\s+bonus(?:es)?|bonus\s+on\s+(?:your\s+)?(?:first\s+)?deposit|\d+%\s+(?:deposit\s+)?bonus|claim\s+(?:your\s+)?(?:\$\d+|\d+\s*(?:usd|inr|eur|gbp))?\s*bonus|free\s+(?:trading\s+credit|cash\s+bonus|deposit\s+match)|deposit\s+match(?:ing)?)\b",
            re.I,
        ),
    ),
    (
        "regulatory_claim",
        re.compile(
            r"\b(?:(?:sebi|fca|sec|finra|rbi|cftc|asic|cysec|mas|fsra|bafin)\s+(?:registered|regulated|licensed|approved|authorized|compliant)|(?:registered|regulated|licensed|approved|authorized)\s+(?:by|with)\s+(?:sebi|fca|sec|finra|rbi|cftc|asic|cysec|mas|fsra|bafin)|government\s+(?:approved|registered|licensed)|officially\s+(?:registered|regulated|licensed)|licensed\s+(?:broker|dealer|platform|firm))\b",
            re.I,
        ),
    ),
    (
        "unverified_testimonials",
        re.compile(
            r"\b(?:\d+[\d,]*\+?\s*(?:satisfied|happy|active)?\s*(?:clients|investors|users|traders|members|reviews)|(?:rated|rating)\s+5\s*(?:stars?|\/5)|(?:9[0-9]|100)%\s*(?:win\s+rate|success\s+rate|satisfaction\s+rate)|proven\s+track\s+record|client\s+testimonials?|customer\s+reviews?)\b",
            re.I,
        ),
    ),
    (
        "suspicious_payment",
        re.compile(
            r"\b(?:send\s+(?:crypto|bitcoin|btc|usdt|eth)|pay\s+via\s+(?:crypto|usdt|bitcoin|gift\s*card|western\s+union)|personal\s+(?:bank\s+)?account|deposit\s+via\s+usdt)\b",
            re.I,
        ),
    ),
]


@dataclass
class ExtractedItem:
    entity_type: str
    raw_value: str
    normalized_value: str
    source_text: str
    extraction_method: str = "regex"
    confidence: float = 1.0


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def normalize_phone(value: str) -> str | None:
    digits = _digits(value)
    if len(digits) < 10 or len(digits) > 15:
        return None
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) == 10:
        return f"+91{digits}"
    return f"+{digits}"


def normalize_url(value: str) -> str | None:
    candidate = value.strip().rstrip(").,;")
    if candidate.lower().startswith("www."):
        candidate = "http://" + candidate
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    host = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{host}{path}"


def normalize_domain(value: str) -> str:
    return value.lower().strip().lstrip("www.")


def normalize_upi(value: str) -> str | None:
    if EMAIL_RE.fullmatch(value):
        return None
    handle, _, psp = value.partition("@")
    if not handle or not psp:
        return None
    if "." in psp:
        return None
    return f"{handle.lower()}@{psp.lower()}"


def _context(text: str, start: int, end: int, window: int = 40) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    return text[left:right].strip()


def extract_entities(text: str) -> list[ExtractedItem]:
    if not text:
        return []
    found: dict[tuple[str, str], ExtractedItem] = {}

    def add(item: ExtractedItem) -> None:
        key = (item.entity_type, item.normalized_value)
        if key not in found:
            found[key] = item

    for match in PHONE_RE.finditer(text):
        raw = match.group(0).strip()
        normalized = normalize_phone(raw)
        if not normalized:
            continue
        add(ExtractedItem("phone", raw, normalized, _context(text, match.start(), match.end()), "regex"))

    for match in EMAIL_RE.finditer(text):
        raw = match.group(0)
        add(ExtractedItem("email", raw, raw.lower(), _context(text, match.start(), match.end()), "regex"))

    for match in URL_RE.finditer(text):
        raw = match.group(0)
        normalized = normalize_url(raw)
        if not normalized:
            continue
        add(ExtractedItem("url", raw, normalized, _context(text, match.start(), match.end()), "regex"))
        parsed = urlparse(normalized)
        add(ExtractedItem("domain", parsed.netloc, normalize_domain(parsed.netloc), parsed.netloc, "derived"))

    for match in DOMAIN_RE.finditer(text):
        raw = match.group(0)
        if "@" in (text[max(0, match.start() - 1) : match.start()]):
            continue
        add(ExtractedItem("domain", raw, normalize_domain(raw), _context(text, match.start(), match.end()), "regex"))

    for match in UPI_RE.finditer(text):
        raw = match.group(0)
        normalized = normalize_upi(raw)
        if not normalized:
            continue
        add(ExtractedItem("upi", raw, normalized, _context(text, match.start(), match.end()), "regex"))

    for match in ACCOUNT_RE.finditer(text):
        raw = match.group(1)
        add(
            ExtractedItem(
                "account_like",
                raw,
                re.sub(r"\s+", "", raw).upper(),
                _context(text, match.start(), match.end()),
                "regex",
                0.6,
            )
        )

    for match in BTC_RE.finditer(text):
        raw = match.group(0)
        add(ExtractedItem("crypto_wallet", raw, f"btc:{raw}", _context(text, match.start(), match.end()), "regex", 0.95))

    for match in ETH_RE.finditer(text):
        raw = match.group(0)
        add(ExtractedItem("crypto_wallet", raw, f"eth:{raw.lower()}", _context(text, match.start(), match.end()), "regex", 0.95))

    for match in TRON_RE.finditer(text):
        raw = match.group(0)
        add(ExtractedItem("crypto_wallet", raw, f"tron:{raw}", _context(text, match.start(), match.end()), "regex", 0.95))

    for match in RETURN_RATE_RE.finditer(text):
        rate_str = match.group("rate")
        period = (match.group("period") or "").lower().strip()
        try:
            rate = float(rate_str)
        except ValueError:
            continue
        is_unusually_high = False
        if any(term in period for term in ("day", "daily")):
            is_unusually_high = rate >= 0.5
        elif any(term in period for term in ("week", "weekly")):
            is_unusually_high = rate >= 2.0
        elif any(term in period for term in ("month", "monthly", "p.m")):
            is_unusually_high = rate >= 8.0
        elif any(term in period for term in ("year", "annual", "p.a", "apy", "apr")):
            is_unusually_high = rate >= 30.0
        elif rate >= 20.0:
            is_unusually_high = True

        if is_unusually_high:
            raw = match.group(0)
            norm_period = period or "unspecified"
            add(
                ExtractedItem(
                    "phrase",
                    raw,
                    f"high_return_claim:{rate}% {norm_period}:{raw.lower()}",
                    _context(text, match.start(), match.end()),
                    "rule",
                    0.95,
                )
            )

    for match in GENERIC_RETURN_RE.finditer(text):
        rate_str = match.group("rate")
        try:
            rate = float(rate_str)
        except ValueError:
            continue
        if rate >= 15.0:
            raw = match.group(0)
            add(
                ExtractedItem(
                    "phrase",
                    raw,
                    f"high_return_claim:{rate}% generic:{raw.lower()}",
                    _context(text, match.start(), match.end()),
                    "rule",
                    0.95,
                )
            )

    for phrase_type, pattern in PHRASE_PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group(0)
            add(
                ExtractedItem(
                    "phrase",
                    raw,
                    f"{phrase_type}:{raw.lower()}",
                    _context(text, match.start(), match.end()),
                    "rule",
                    0.9,
                )
            )

    return list(found.values())
