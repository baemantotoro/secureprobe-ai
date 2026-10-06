"""Observe Set-Cookie attributes without retaining values or replaying cookies."""

import re
import unicodedata

from secureprobe.models import CookieInfo


_COOKIE_NAME = re.compile(r"[!#$%&'*+.^_`|~0-9a-zA-Z-]+", re.ASCII)
_SAME_SITE = {"strict": "Strict", "lax": "Lax", "none": "None"}
_MAX_HEADER_CHARS = 8192
_MAX_ATTRIBUTE_CHARS = 2048


def _segments(header: str) -> list[str] | None:
    """Split on semicolons outside quotes; commas in Expires remain intact.

    A small scanner avoids SimpleCookie treating unknown name=value attributes
    as additional cookies or dropping the whole header for unknown flags.
    """
    segments = []
    start = 0
    quoted = False
    escaped = False
    for index, char in enumerate(header):
        if escaped:
            escaped = False
        elif char == "\\" and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif char == ";" and not quoted:
            segments.append(header[start:index].strip())
            start = index + 1
    if quoted or escaped:
        return None
    segments.append(header[start:].strip())
    return segments


def _metadata(value: str) -> str | None:
    value = value.strip()
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return value[:_MAX_ATTRIBUTE_CHARS] or None


def inspect_cookies(*, set_cookie_headers: str | list[str], max_cookies: int = 50) -> list[CookieInfo]:
    """Return independent cookie metadata in header order; never store values.

    Each string represents one Set-Cookie header. No comma splitting, cookie
    jar, session classification, or vulnerability judgment is performed.
    Duplicate attribute keys use the last occurrence; flag presence is boolean.
    """
    if isinstance(max_cookies, bool) or not isinstance(max_cookies, int) or not 1 <= max_cookies <= 200:
        raise ValueError("max_cookies must be an integer between 1 and 200")
    if isinstance(set_cookie_headers, str):
        headers = [set_cookie_headers]
    elif isinstance(set_cookie_headers, list) and all(isinstance(item, str) for item in set_cookie_headers):
        headers = set_cookie_headers
    else:
        raise ValueError("set_cookie_headers must be a string or list of strings")

    cookies = []
    for header in headers:
        if len(header) > _MAX_HEADER_CHARS or any(
            unicodedata.category(char).startswith("C") for char in header
        ):
            continue
        segments = _segments(header)
        if not segments:
            continue
        first = segments.pop(0)
        name, separator, _ = first.partition("=")
        name = name.strip()
        # Discard the cookie pair immediately; only the name reaches metadata.
        del first, _
        if not separator or not _COOKIE_NAME.fullmatch(name):
            continue
        secure = False
        http_only = False
        attributes = {}
        for segment in segments:
            key, separator, value = segment.partition("=")
            key = key.strip().lower()
            if key == "secure":
                secure = True
            elif key == "httponly":
                http_only = True
            elif separator and key in {"samesite", "domain", "path", "max-age", "expires"}:
                attributes[key] = None if key == "max-age" and len(value.strip()) > _MAX_ATTRIBUTE_CHARS else _metadata(value)
        max_age = None
        if attributes.get("max-age") is not None:
            try:
                max_age = int(attributes["max-age"])
            except ValueError:
                pass
        cookies.append(CookieInfo(
            name=name, secure=secure, http_only=http_only,
            same_site=_SAME_SITE.get((attributes.get("samesite") or "").lower()),
            domain=attributes.get("domain"), path=attributes.get("path"),
            max_age=max_age, expires=attributes.get("expires"),
        ))
        if len(cookies) == max_cookies:
            break
    return cookies
