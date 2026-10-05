"""Observe eight response headers without network I/O or finding judgments."""

from collections.abc import Mapping
import unicodedata
from urllib.parse import urlsplit

from secureprobe.core.safety import validate_web_target
from secureprobe.models import (
    AssessmentRequest,
    AssessmentType,
    HeaderInspectionResult,
    HeaderObservation,
)


_OBSERVED_HEADERS = (
    "Content-Security-Policy",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
    "Strict-Transport-Security",
    "Cache-Control",
    "Pragma",
)
_HEADER_KEYS = frozenset(name.lower() for name in _OBSERVED_HEADERS)
_MAX_VALUE_CHARS = 4096


def inspect_headers(*, url: str, headers: Mapping[str, str]) -> HeaderInspectionResult:
    """Return fixed-order metadata only; missing headers are not findings.

    Sensitive and unknown headers never enter the output. Cookie analysis
    belongs to cookie_inspector. Case variants use the first mapping entry.
    """
    if not isinstance(url, str):
        raise ValueError("url must be a valid HTTP(S) absolute URL")
    request = AssessmentRequest.model_construct(
        assessment_type=AssessmentType.WEB, target_url=url,
    )
    if not validate_web_target(request, active=False).allowed:
        raise ValueError("url must be a valid HTTP(S) absolute URL without userinfo")
    if not isinstance(headers, Mapping):
        raise ValueError("headers must be a string-to-string mapping")

    values = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise ValueError("header names and values must be strings")
        key = name.lower()
        if key in _HEADER_KEYS and key not in values:
            values[key] = value

    scheme = urlsplit(url).scheme
    observations = []
    for name in _OBSERVED_HEADERS:
        key = name.lower()
        present = key in values
        value = None
        notes = ["present" if present else "not present"]
        if present:
            raw_value = values[key]
            # Omit the whole value instead of reinterpreting an injected CR/LF
            # sequence. Also omit Unicode control/format/surrogate characters.
            if any(unicodedata.category(char).startswith("C") for char in raw_value):
                notes.append("value omitted: control characters")
            else:
                stripped = raw_value.strip()
                value = stripped[:_MAX_VALUE_CHARS]
                if len(stripped) > _MAX_VALUE_CHARS:
                    notes.append("value truncated")
        if key == "strict-transport-security" and scheme == "http":
            notes.append("HSTS is only effective over HTTPS")
        observations.append(HeaderObservation(
            name=name, present=present, value=value, note="; ".join(notes),
        ))
    return HeaderInspectionResult(url=url, scheme=scheme, observations=observations)
