"""Bounded passive HTTP evidence collection with explicit redirect checks."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import math
from time import perf_counter
from urllib.parse import urljoin, urlsplit
from uuid import uuid4

import httpx

from secureprobe.core.safety import _canonical_host, validate_web_target
from secureprobe.models import AssessmentRequest, ExecutionStatus, ToolError, ToolExecution
from .cookie_inspector import inspect_cookies


_REQUEST_HEADERS = frozenset({
    "accept", "accept-language", "user-agent", "referer",
    "if-none-match", "if-modified-since",
})
_SENSITIVE_HEADERS = frozenset({
    "authorization", "proxy-authorization", "cookie", "set-cookie",
    "www-authenticate", "x-api-key", "api-key",
})
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


def _cookie_metadata(response: httpx.Response) -> list[dict]:
    try:
        # Raw headers are transient parser input only, never output/log/error.
        return [cookie.model_dump(mode="json") for cookie in inspect_cookies(
            set_cookie_headers=response.headers.get_list("set-cookie"),
        )]
    except Exception:
        # Ancillary parser failures must not expose raw headers or fail HTTP.
        return []


def _host(url: str) -> str:
    # Only called after the existing Safety Gate has validated the URL.
    return _canonical_host(urlsplit(url).hostname)


def _scope_allows(request: AssessmentRequest, url: str, allowlist: set[str]) -> bool:
    host = _host(url)
    if host == _host(request.target_url):
        return True
    scope_hosts = {_canonical_host(value) for value in request.scope.allowed_hosts}
    authorized_hosts = {_canonical_host(value) for value in allowlist}
    return host in scope_hosts and host in authorized_hosts


def _response_headers(response: httpx.Response) -> dict[str, str]:
    result = {}
    for name, value in response.headers.items():
        if name.lower() in _SENSITIVE_HEADERS:
            value = "***MASKED***"
        elif name.lower() == "location":
            # Do not retain credentials from an untrusted redirect URL.
            try:
                if urlsplit(value).username is not None:
                    value = "***MASKED***"
            except ValueError:
                value = "***INVALID_URL***"
        result[name] = value
    return result


async def _body_excerpt(response: httpx.Response, method: str, limit: int):
    content_type = response.headers.get("content-type", "").split(";", 1)[0].lower().strip()
    is_text = (
        content_type.startswith("text/")
        or content_type in {"application/json", "application/xml", "application/javascript"}
        or content_type.endswith(("+json", "+xml"))
    )
    # Request identity encoding and never decompress untrusted compressed data
    # into potentially unbounded memory. Binary/encoded responses keep metadata.
    encoding = response.headers.get("content-encoding", "identity").lower().strip()
    if method == "HEAD" or not is_text or encoding != "identity":
        return None, False
    body = bytearray()
    truncated = False
    async for chunk in response.aiter_raw():
        remaining = limit - len(body)
        body.extend(chunk[:remaining])
        if len(chunk) > remaining:
            truncated = True
            break
    try:
        excerpt = body.decode(response.encoding or "utf-8", errors="replace")
    except LookupError:
        excerpt = body.decode("utf-8", errors="replace")
    return excerpt, truncated


async def http_request(
    *,
    assessment_request: AssessmentRequest,
    url: str,
    test_id: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    follow_redirects: bool = False,
    timeout_seconds: float = 5.0,
    max_body_bytes: int = 65536,
    allowlist: set[str] | None = None,
) -> ToolExecution:
    """Collect one response, or at most four requests including redirects.

    Additional hosts require BOTH scope.allowed_hosts and caller allowlist.
    No retries, authentication sessions, or vulnerability judgments are made.
    Timeout bounds the whole operation as well as individual HTTP operations.
    """
    if not isinstance(test_id, str) or not test_id.strip():
        raise ValueError("test_id must be a nonempty string")
    started_at = datetime.now(timezone.utc)
    started = perf_counter()
    execution_id = f"EXEC-{uuid4().hex}"
    tool_input = {"method": method}

    def finish(status, *, output=None, code=None, message=None, retryable=False):
        return ToolExecution(
            execution_id=execution_id, test_id=test_id, tool_name="http_request",
            input=tool_input, status=status, started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            duration_ms=max(0, int((perf_counter() - started) * 1000)),
            output=output if output is not None else {"cookies": []},
            error=ToolError(code=code, message=message, retryable=retryable) if code else None,
        )

    if method not in {"GET", "HEAD"}:
        return finish(ExecutionStatus.BLOCKED, code="METHOD_NOT_ALLOWED", message="Only GET and HEAD are allowed")
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(timeout_seconds)
        or not 0.1 <= timeout_seconds <= 30
        or isinstance(max_body_bytes, bool)
        or not isinstance(max_body_bytes, int)
        or not 1 <= max_body_bytes <= 1048576
    ):
        return finish(ExecutionStatus.FAILED, code="INVALID_INPUT", message="Invalid timeout or body limit")

    request_headers = {"User-Agent": "SecureProbeAI/0.1", "Accept-Encoding": "identity"}
    for name, value in (headers or {}).items():
        if name.lower() not in _REQUEST_HEADERS:
            return finish(ExecutionStatus.BLOCKED, code="HEADER_NOT_ALLOWED", message="Request header is not allowed")
        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            return finish(ExecutionStatus.BLOCKED, code="INVALID_HEADER", message="Invalid request header value")
        request_headers[name.lower()] = value
    # Avoid two differently cased User-Agent keys when overridden by a caller.
    request_headers = {name.lower(): value for name, value in request_headers.items()}
    try:
        httpx.Headers(request_headers)
    except UnicodeEncodeError:
        return finish(ExecutionStatus.BLOCKED, code="INVALID_HEADER", message="Invalid request header encoding")

    allowlist = set(allowlist or ())
    base_gate = validate_web_target(assessment_request, active=False, allowlist=allowlist)
    if not base_gate.allowed:
        return finish(ExecutionStatus.BLOCKED, code="SAFETY_BLOCKED", message=base_gate.reason)

    def check_target(target, *, redirect=False):
        gate = validate_web_target(
            assessment_request.model_copy(update={"target_url": target}),
            active=False, allowlist=allowlist,
        )
        if not gate.allowed:
            return finish(ExecutionStatus.BLOCKED, code="SAFETY_BLOCKED", message=gate.reason)
        if not _scope_allows(assessment_request, target, allowlist):
            return finish(
                ExecutionStatus.BLOCKED,
                code="REDIRECT_OUT_OF_SCOPE" if redirect else "OUT_OF_SCOPE",
                message="Target host is outside the assessment scope",
            )
        return None

    blocked = check_target(url)
    if blocked is not None:
        return blocked
    tool_input.update(url=url, headers=request_headers.copy(), follow_redirects=follow_redirects,
                      timeout_seconds=timeout_seconds, max_body_bytes=max_body_bytes)
    current_url = url
    redirect_chain = []
    try:
        async with asyncio.timeout(timeout_seconds):
            async with httpx.AsyncClient(
                timeout=timeout_seconds, follow_redirects=False, verify=True, trust_env=False,
            ) as client:
                for hop in range(4):
                    # Never replay a server-issued cookie on a redirect.
                    client.cookies.clear()
                    async with client.stream(method, current_url, headers=request_headers) as response:
                        if follow_redirects and response.status_code in _REDIRECT_STATUSES and "location" in response.headers:
                            if hop == 3:
                                return finish(ExecutionStatus.FAILED, code="TOO_MANY_REDIRECTS", message="Redirect limit exceeded")
                            location = response.headers["location"]
                            if "\\" in location or any(
                                char.isspace() or ord(char) < 32 or ord(char) == 127
                                for char in location
                            ):
                                return finish(ExecutionStatus.BLOCKED, code="INVALID_URL", message="Invalid redirect URL")
                            try:
                                next_url = urljoin(str(response.url), location)
                            except ValueError:
                                return finish(ExecutionStatus.BLOCKED, code="INVALID_URL", message="Invalid redirect URL")
                            blocked = check_target(next_url, redirect=True)
                            if blocked is not None:
                                return blocked
                            redirect_chain.append(str(response.url))
                            current_url = next_url
                            continue

                        excerpt, truncated = await _body_excerpt(response, method, max_body_bytes)
                        length = response.headers.get("content-length", "")
                        content_length = int(length) if length.isascii() and length.isdecimal() and len(length) <= 20 else None
                        return finish(ExecutionStatus.SUCCESS, output={
                            "status_code": response.status_code,
                            "headers": _response_headers(response),
                            "cookies": _cookie_metadata(response),
                            "content_type": response.headers.get("content-type"),
                            "body_excerpt": excerpt, "body_truncated": truncated,
                            "content_length": content_length,
                            "elapsed_ms": max(0, int((perf_counter() - started) * 1000)),
                            "final_url": str(response.url), "redirect_chain": redirect_chain,
                        })
    except (httpx.TimeoutException, TimeoutError):
        return finish(ExecutionStatus.TIMEOUT, code="HTTP_TIMEOUT", message="HTTP request timed out", retryable=True)
    except httpx.InvalidURL:
        return finish(ExecutionStatus.BLOCKED, code="INVALID_URL", message="Invalid HTTP URL")
    except httpx.RequestError:
        # Exception text can contain URLs or sensitive server data.
        return finish(ExecutionStatus.FAILED, code="NETWORK_ERROR", message="HTTP network request failed", retryable=True)
