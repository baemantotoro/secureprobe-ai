"""Collect endpoint candidates from one HTML document without network I/O."""

from urllib.parse import parse_qsl, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from secureprobe.core.safety import validate_web_target
from secureprobe.models import AssessmentRequest, AssessmentScope, AssessmentType, Endpoint, EndpointParameter


def _normalize_url(url: str) -> str | None:
    # Reuse the public passive URL policy, without importing private helpers.
    request = AssessmentRequest.model_construct(
        assessment_type=AssessmentType.WEB, target_url=url,
    )
    if not validate_web_target(request, active=False).allowed:
        return None
    parsed = urlsplit(url)
    host = parsed.hostname.lower().removesuffix(".")
    authority = f"[{host}]" if ":" in host else host
    if parsed.port is not None:
        authority += f":{parsed.port}"
    return urlunsplit((parsed.scheme.lower(), authority, parsed.path or "/", parsed.query, ""))


def _resolve(base_url: str, reference: str) -> str | None:
    reference = reference.strip()
    # urljoin may discard controls before the Safety Gate sees them.
    if "\\" in reference or any(
        char.isspace() or ord(char) < 32 or ord(char) == 127 for char in reference
    ):
        return None
    try:
        reference_parts = urlsplit(reference)
        if reference_parts.scheme:
            return _normalize_url(reference)
        if reference.startswith("//"):
            return _normalize_url(urlsplit(base_url).scheme + ":" + reference)
        if ":" in reference.split("/", 1)[0]:
            return None
        return _normalize_url(urljoin(base_url, reference))
    except ValueError:
        return None


def _host(url: str) -> str:
    return urlsplit(url).hostname


def _query_parameters(url: str) -> list[EndpointParameter]:
    names = dict.fromkeys(name.strip() for name, _ in parse_qsl(urlsplit(url).query, keep_blank_values=True))
    return [EndpointParameter(name=name, location="query") for name in names if name]


def collect_endpoints(
    *,
    base_url: str,
    html: str,
    scope: AssessmentScope | None = None,
    max_endpoints: int = 100,
) -> list[Endpoint]:
    """Return current URL then DOM order, keeping the first source on duplicates.

    Scope membership creates a candidate, not permission to make a request.
    http_request must independently enforce Safety Gate and caller Allowlist.
    POST forms are metadata only. Field values are never retained.
    """
    if isinstance(max_endpoints, bool) or not isinstance(max_endpoints, int) or not 1 <= max_endpoints <= 500:
        raise ValueError("max_endpoints must be an integer between 1 and 500")
    if not isinstance(base_url, str) or not isinstance(html, str):
        raise ValueError("base_url and html must be strings")
    current = _normalize_url(base_url)
    if current is None:
        raise ValueError("base_url must be a valid HTTP(S) URL without userinfo")

    hosts = {_host(current)}
    if scope is not None:
        # Scope entries are host names/IP literals, not URLs, ports or patterns.
        hosts.update(value.lower().removesuffix(".") for value in scope.allowed_hosts)
    endpoints: dict[tuple[str, str], Endpoint] = {}
    parameter_keys: dict[tuple[str, str], set[tuple[str, str]]] = {}

    def add(url: str, method: str, source: str, field_names=()):
        if _host(url) not in hosts:
            return
        key = (method, url)
        if key not in endpoints:
            if len(endpoints) >= max_endpoints:
                return
            endpoints[key] = Endpoint(url=url, method=method, source=source)
            parameter_keys[key] = set()
        params = _query_parameters(url)
        params.extend(EndpointParameter(name=name, location="form") for name in field_names)
        for parameter in params:
            parameter_key = (parameter.name, parameter.location)
            if parameter_key not in parameter_keys[key]:
                endpoints[key].parameters.append(parameter)
                parameter_keys[key].add(parameter_key)

    add(current, "GET", "current")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["a", "form"]):
        if tag.name == "a":
            reference = tag.get("href")
            if not isinstance(reference, str) or not reference.strip() or reference.strip().startswith("#"):
                continue
            resolved = _resolve(current, reference)
            if resolved is not None:
                add(resolved, "GET", "link")
        else:
            raw_method = tag.get("method", "GET")
            if not isinstance(raw_method, str):
                continue
            method = raw_method.strip().upper()
            if method not in {"GET", "POST"}:
                continue
            reference = tag.get("action", "")
            if not isinstance(reference, str):
                continue
            resolved = _resolve(current, reference)
            if resolved is None:
                continue
            names = []
            for field in tag.find_all(["input", "textarea", "select"]):
                raw_name = field.get("name", "")
                if not isinstance(raw_name, str):
                    continue
                name = raw_name.strip()
                if name and field.find_parent("form") is tag:
                    names.append(name)
            add(resolved, method, "form", names)
    return list(endpoints.values())
