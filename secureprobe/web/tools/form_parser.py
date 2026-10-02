"""Parse form structure only; never submit forms or retain field values."""

from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from secureprobe.core.safety import validate_web_target
from secureprobe.models import AssessmentRequest, AssessmentScope, AssessmentType, Form, FormField


def _normalized_url(url: str) -> str | None:
    request = AssessmentRequest.model_construct(
        assessment_type=AssessmentType.WEB, target_url=url,
    )
    if not validate_web_target(request, active=False).allowed:
        return None
    parts = urlsplit(url)
    host = parts.hostname.lower().removesuffix(".")
    authority = f"[{host}]" if ":" in host else host
    if parts.port is not None:
        authority += f":{parts.port}"
    return urlunsplit((parts.scheme.lower(), authority, parts.path or "/", parts.query, ""))


def _action_url(base_url: str, action: str) -> str | None:
    action = action.strip()
    # Reject ambiguous references before urljoin can discard controls or repair
    # a malformed absolute URL. The public Safety Gate validates each result.
    if "\\" in action or any(
        char.isspace() or ord(char) < 32 or ord(char) == 127 for char in action
    ):
        return None
    try:
        parts = urlsplit(action)
        if parts.scheme:
            return _normalized_url(action)
        if action.startswith("//"):
            return _normalized_url(urlsplit(base_url).scheme + ":" + action)
        if ":" in action.split("/", 1)[0]:
            return None
        return _normalized_url(urljoin(base_url, action))
    except ValueError:
        return None


def parse_forms(
    *,
    base_url: str,
    html: str,
    scope: AssessmentScope | None = None,
    max_forms: int = 50,
    max_fields_per_form: int = 100,
) -> list[Form]:
    """Return forms and fields in DOM order, retaining only name/type metadata.

    Additional scoped hosts are candidates, not authorization. Actual request
    permission belongs to Safety Gate/http_request. POST is never executed.
    """
    for value, upper, name in (
        (max_forms, 200, "max_forms"),
        (max_fields_per_form, 500, "max_fields_per_form"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= upper:
            raise ValueError(f"{name} must be an integer between 1 and {upper}")
    if not isinstance(base_url, str) or not isinstance(html, str):
        raise ValueError("base_url and html must be strings")
    base = _normalized_url(base_url)
    if base is None:
        raise ValueError("base_url must be a valid HTTP(S) URL without userinfo")
    hosts = {urlsplit(base).hostname}
    if scope is not None:
        hosts.update(host.lower().removesuffix(".") for host in scope.allowed_hosts)

    forms = []
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("form"):
        raw_method = tag.get("method", "GET")
        if not isinstance(raw_method, str):
            continue
        method = raw_method.strip().upper()
        if method not in {"GET", "POST"}:
            continue
        raw_action = tag.get("action", "")
        if not isinstance(raw_action, str):
            continue
        action = _action_url(base, raw_action)
        if action is None or urlsplit(action).hostname not in hosts:
            continue

        fields = []
        seen = set()
        for field in tag.find_all(["input", "textarea", "select"]):
            if field.find_parent("form") is not tag:
                continue
            raw_name = field.get("name", "")
            if not isinstance(raw_name, str) or not raw_name.strip():
                continue
            name = raw_name.strip()
            if field.name == "input":
                raw_type = field.get("type", "text")
                field_type = raw_type.strip().lower() if isinstance(raw_type, str) else "text"
                field_type = field_type or "text"
            else:
                field_type = field.name
            key = (name, field_type)
            if key in seen:
                continue
            seen.add(key)
            fields.append(FormField(name=name, type=field_type))
            if len(fields) == max_fields_per_form:
                break
        forms.append(Form(action=action, method=method, fields=fields))
        if len(forms) == max_forms:
            break
    return forms
