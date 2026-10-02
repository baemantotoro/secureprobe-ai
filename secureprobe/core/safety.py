"""Web target safety policy; performs no HTTP requests or DNS resolution."""

from __future__ import annotations

from ipaddress import IPv6Address
import re
from urllib.parse import urlsplit

from secureprobe.models import AssessmentRequest, AssessmentType, ValidationResult


_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_HOST_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", re.ASCII)


def _canonical_host(host: str) -> str | None:
    """Accept bare ASCII hostnames or IP literals, without URL syntax."""
    host = host.lower().removesuffix(".")
    if ":" in host:
        if "%" in host:  # Scoped IPv6 literals are outside this policy.
            return None
        try:
            IPv6Address(host)
        except ValueError:
            return None
        return host
    if len(host) > 253 or not all(_HOST_LABEL.fullmatch(label) for label in host.split(".")):
        return None
    return host


def _deny(reason: str) -> ValidationResult:
    return ValidationResult(
        allowed=False,
        reason=reason,
        active_assessment_allowed=False,
        validated_scope=None,
    )


def validate_web_target(
    request: AssessmentRequest,
    *,
    active: bool,
    allowlist: set[str] | None = None,
) -> ValidationResult:
    """Validate a WEB request using caller-supplied, exact host authorization.

    Passive requests still require a valid HTTP(S) URL. Active permission
    requires both host authorization and authorization_confirmed, even when
    validating a passive request. Credentials and scope.allowed_hosts do not
    grant authorization. Path scope enforcement belongs to the tool layer.
    Invalid allowlist entries are ignored; no wildcard or CIDR is supported.
    """
    if request.assessment_type != AssessmentType.WEB:
        return _deny("unsupported assessment type")

    target = request.target_url
    if not target:
        return _deny("target URL missing")
    # urlsplit can silently discard controls; reject ambiguous input first.
    if "\\" in target or any(
        char.isspace() or ord(char) < 32 or ord(char) == 127 for char in target
    ):
        return _deny("malformed target URL")
    try:
        parsed = urlsplit(target)
        if parsed.scheme not in {"http", "https"}:
            return _deny("unsupported URL scheme")
        if parsed.username is not None or parsed.password is not None:
            return _deny("URL userinfo is not allowed")
        if not parsed.hostname:
            return _deny("target URL missing hostname")
        # Accessing port also detects nonnumeric and out-of-range ports.
        port = parsed.port
        authority_host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
        if not re.fullmatch(re.escape(authority_host) + r"(?::[0-9]+)?", parsed.netloc.lower()):
            return _deny("malformed URL authority")
        if port == 0:
            return _deny("invalid URL port")
        host = _canonical_host(parsed.hostname)
    except ValueError:
        return _deny("malformed target URL")
    if host is None:
        return _deny("invalid target hostname")

    authorized_hosts = {
        canonical
        for entry in (allowlist or set())
        if (canonical := _canonical_host(entry)) is not None
    }
    host_allowed = host in _LOCAL_HOSTS or host in authorized_hosts
    active_allowed = host_allowed and request.authorization_confirmed
    if active and not request.authorization_confirmed:
        return _deny("authorization not confirmed")
    if active and not host_allowed:
        return _deny("external target not in allowlist")

    if host == "localhost":
        reason = "localhost target"
    elif host in _LOCAL_HOSTS:
        reason = "loopback target"
    elif host in authorized_hosts:
        reason = "explicit allowlist target"
    else:
        reason = "passive HTTP(S) target"
    return ValidationResult(
        allowed=True,
        reason=reason,
        active_assessment_allowed=active_allowed,
        validated_scope=request.scope,
    )
