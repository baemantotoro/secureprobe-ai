"""Assemble one passive HTTP observation using the existing public tools."""

from uuid import uuid4

from secureprobe.models import (
    AssessmentRequest, AssessmentType, CookieInfo, ExecutionStatus, WebTargetContext,
)
from secureprobe.web.tools.endpoint_collector import collect_endpoints
from secureprobe.web.tools.form_parser import parse_forms
from secureprobe.web.tools.header_inspector import inspect_headers
from secureprobe.web.tools.http_request import http_request


_SESSION_NAMES = frozenset({"session", "sessionid", "jsessionid", "phpsessid", "connect.sid"})
_REQUIRED_OUTPUT = ("final_url", "headers", "cookies", "content_type", "body_excerpt")


async def observe_web_target(
    *,
    assessment_request: AssessmentRequest,
    test_id: str = "OBSERVE-WEB-001",
    allowlist: set[str] | None = None,
) -> WebTargetContext:
    """Observe the landing response; never crawl or submit credentials.

    Network safety and redirect scope remain the HTTP tool's responsibility.
    A null HTML excerpt is treated as empty HTML, including its current endpoint.
    Truncated excerpts are parsed best-effort without retaining the body.
    """
    if assessment_request.assessment_type != AssessmentType.WEB:
        raise ValueError("web observation requires a WEB assessment")

    execution = await http_request(
        assessment_request=assessment_request,
        url=assessment_request.target_url,
        test_id=test_id,
        method="GET",
        follow_redirects=True,
        allowlist=allowlist,
    )
    if execution.status != ExecutionStatus.SUCCESS:
        # Even tool error codes/messages may contain untrusted response data.
        raise RuntimeError("web observation failed: HTTP tool did not succeed")

    output = execution.output
    for key in _REQUIRED_OUTPUT:
        if key not in output:
            raise ValueError(f"invalid HTTP output: missing {key}")
    final_url = output["final_url"]
    headers = output["headers"]
    cookie_items = output["cookies"]
    content_type = output["content_type"]
    body = output["body_excerpt"]
    if not isinstance(final_url, str) or not final_url.strip():
        raise ValueError("invalid HTTP output: final_url")
    if not isinstance(headers, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in headers.items()
    ):
        raise ValueError("invalid HTTP output: headers")
    if not isinstance(cookie_items, list) or any(not isinstance(item, dict) for item in cookie_items):
        raise ValueError("invalid HTTP output: cookies")
    if content_type is not None and not isinstance(content_type, str):
        raise ValueError("invalid HTTP output: content_type")
    if body is not None and not isinstance(body, str):
        raise ValueError("invalid HTTP output: body_excerpt")

    try:
        cookies = [CookieInfo.model_validate(item) for item in cookie_items]
    except ValueError:
        raise ValueError("invalid HTTP output: cookie metadata") from None

    mime = content_type.split(";", 1)[0].strip().lower() if content_type is not None else ""
    try:
        header_result = inspect_headers(url=final_url, headers=headers)
        endpoints = []
        forms = []
        if mime == "text/html":
            endpoints = collect_endpoints(base_url=final_url, html=body or "", scope=assessment_request.scope)
            forms = parse_forms(base_url=final_url, html=body or "", scope=assessment_request.scope)
        return WebTargetContext(
            context_id=f"CTX-WEB-{uuid4().hex}",
            base_url=final_url,
            endpoints=endpoints,
            forms=forms,
            headers={item.name: item.value if item.present else None for item in header_result.observations},
            cookies=cookies,
            authentication_detected=any(field.type == "password" for form in forms for field in form.fields),
            session_detected=any(cookie.name.lower() in _SESSION_NAMES for cookie in cookies),
            content_types=[mime] if mime else [],
        )
    except ValueError:
        raise ValueError("invalid HTTP output: passive context assembly failed") from None
