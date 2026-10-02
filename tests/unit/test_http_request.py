"""HTTP evidence tests use MockTransport exclusively, without internet I/O."""

import asyncio
import importlib
import json

import httpx
import pytest

from secureprobe.models import AssessmentRequest, AssessmentScope, AssessmentType, ExecutionStatus

tool = importlib.import_module("secureprobe.web.tools.http_request")


class Chunks(httpx.AsyncByteStream):
    def __init__(self, chunks):
        self.chunks = chunks
        self.read_count = 0
        self.closed = False

    async def __aiter__(self):
        for chunk in self.chunks:
            self.read_count += 1
            yield chunk

    async def aclose(self):
        self.closed = True


def response(status=200, body=b"<html>hello</html>", headers=None, stream=None):
    return httpx.Response(
        status, headers={"Content-Type": "text/html", **(headers or {})},
        stream=stream or Chunks([body]),
    )


@pytest.fixture
def mock_client(monkeypatch):
    real_client = httpx.AsyncClient
    calls = []
    settings = []

    def install(handler):
        def tracked(request):
            calls.append(request)
            return handler(request)

        def factory(**kwargs):
            settings.append(kwargs.copy())
            return real_client(transport=httpx.MockTransport(tracked), **kwargs)

        monkeypatch.setattr(tool.httpx, "AsyncClient", factory)
        return calls, settings

    return install


def execute(*, target="http://localhost", url="http://localhost", scope=None, **kwargs):
    request = AssessmentRequest(
        assessment_type=AssessmentType.WEB, target_url=target,
        scope=scope or AssessmentScope(), authorization_confirmed=False,
    )
    original = request.model_dump()
    result = asyncio.run(tool.http_request(
        assessment_request=request, url=url, test_id="TEST-HTTP-001", **kwargs,
    ))
    assert request.model_dump() == original
    assert result.tool_name == "http_request"
    assert result.test_id == "TEST-HTTP-001"
    assert result.execution_id.startswith("EXEC-")
    assert result.started_at <= result.finished_at
    assert result.duration_ms >= 0
    return result


def test_get_success_and_client_policy(mock_client):
    calls, settings = mock_client(lambda request: response())
    result = execute(url="http://localhost/search?q=test#admin", headers={"Accept": "text/html"})
    assert result.status == ExecutionStatus.SUCCESS
    assert result.error is None
    assert result.output["status_code"] == 200
    assert result.output["body_excerpt"] == "<html>hello</html>"
    assert result.output["elapsed_ms"] >= 0
    assert result.output["body_truncated"] is False
    assert calls[0].method == "GET"
    assert calls[0].url.raw_path == b"/search?q=test"
    assert calls[0].headers["user-agent"] == "SecureProbeAI/0.1"
    assert calls[0].headers["accept-encoding"] == "identity"
    assert settings == [{"timeout": 5.0, "follow_redirects": False, "verify": True, "trust_env": False}]


def test_head_does_not_read_body(mock_client):
    stream = Chunks([b"ignored"])
    calls, _ = mock_client(lambda request: response(stream=stream))
    result = execute(method="HEAD")
    assert result.status == ExecutionStatus.SUCCESS
    assert result.output["body_excerpt"] is None
    assert calls[0].method == "HEAD"
    assert stream.read_count == 0
    assert stream.closed


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT", "get"])
def test_unsupported_method_never_sends(mock_client, method):
    calls, settings = mock_client(lambda request: response())
    result = execute(method=method)
    assert result.status == ExecutionStatus.BLOCKED
    assert result.error.code == "METHOD_NOT_ALLOWED"
    assert not calls and not settings


@pytest.mark.parametrize("url", [
    "http:///admin", "file:///etc/passwd", "http://user:secret@localhost",
    "http://[::1", "http://local\nhost", "http://localhost:bad",
])
def test_safety_block_never_sends_or_records_credentials(mock_client, url):
    calls, _ = mock_client(lambda request: response())
    result = execute(url=url)
    assert result.status == ExecutionStatus.BLOCKED
    assert result.error.code == "SAFETY_BLOCKED"
    assert not calls
    assert "secret" not in result.model_dump_json()


def test_original_assessment_safety_checked(mock_client):
    calls, _ = mock_client(lambda request: response())
    assert execute(target="ftp://localhost").error.code == "SAFETY_BLOCKED"
    assert not calls


@pytest.mark.parametrize("scope,allowlist,allowed", [
    ([], set(), False), (["secureboard.local"], set(), False),
    ([], {"secureboard.local"}, False),
    (["SECUREBOARD.LOCAL."], {"SECUREBOARD.LOCAL."}, True),
])
def test_additional_host_needs_scope_and_allowlist(mock_client, scope, allowlist, allowed):
    calls, _ = mock_client(lambda request: response())
    result = execute(
        url="https://secureboard.local", scope=AssessmentScope(allowed_hosts=scope),
        allowlist=allowlist,
    )
    assert (result.status == ExecutionStatus.SUCCESS) is allowed
    assert len(calls) == int(allowed)
    if not allowed:
        assert result.error.code == "OUT_OF_SCOPE"


def test_external_passive_assessment_same_host_allowed(mock_client):
    calls, _ = mock_client(lambda request: response())
    assert execute(target="https://example.com", url="https://example.com/a").status == ExecutionStatus.SUCCESS
    assert len(calls) == 1


def test_out_of_scope_host(mock_client):
    calls, _ = mock_client(lambda request: response())
    result = execute(url="https://example.com")
    assert result.status == ExecutionStatus.BLOCKED
    assert result.error.code == "OUT_OF_SCOPE"
    assert not calls


@pytest.mark.parametrize("error,status,code", [
    (httpx.ReadTimeout, ExecutionStatus.TIMEOUT, "HTTP_TIMEOUT"),
    (httpx.ConnectError, ExecutionStatus.FAILED, "NETWORK_ERROR"),
])
def test_network_errors_structured_without_retry(mock_client, error, status, code):
    def handler(request):
        raise error("super-secret", request=request)
    calls, _ = mock_client(handler)
    result = execute()
    assert result.status == status
    assert result.error.code == code
    assert result.error.retryable is True
    assert "super-secret" not in result.model_dump_json()
    assert len(calls) == 1


@pytest.mark.parametrize("body,limit,truncated", [(b"abcdef", 3, True), (b"abc", 3, False), (b"ab", 3, False)])
def test_body_truncation(mock_client, body, limit, truncated):
    mock_client(lambda request: response(body=body, headers={"Content-Length": str(len(body))}))
    output = execute(max_body_bytes=limit).output
    assert output["body_excerpt"] == body[:limit].decode()
    assert output["body_truncated"] is truncated
    assert output["content_length"] == len(body)


def test_large_stream_stops_and_closes(mock_client):
    stream = Chunks([b"a" * 32768, b"b" * 32768, b"c", b"never read"])
    mock_client(lambda request: response(stream=stream))
    output = execute().output
    assert len(output["body_excerpt"]) == 65536
    assert output["body_truncated"] is True
    assert stream.read_count == 3
    assert stream.closed


@pytest.mark.parametrize("content_type,encoding", [
    ("application/octet-stream", "identity"), ("image/png", "identity"),
    ("application/pdf", "identity"), ("text/html", "gzip"),
])
def test_binary_and_compressed_content_metadata_only(mock_client, content_type, encoding):
    stream = Chunks([b"\xff\x00"])
    mock_client(lambda request: response(stream=stream, headers={"Content-Type": content_type, "Content-Encoding": encoding}))
    result = execute()
    assert result.status == ExecutionStatus.SUCCESS
    assert result.output["body_excerpt"] is None
    assert stream.read_count == 0
    assert stream.closed


@pytest.mark.parametrize("content_type", ["text/plain; charset=unknown-encoding", "application/json"])
def test_decode_errors_do_not_crash(mock_client, content_type):
    mock_client(lambda request: response(body=b"hello\xff", headers={"Content-Type": content_type}))
    assert execute().output["body_excerpt"].startswith("hello")


def test_response_headers_masked(mock_client):
    sensitive = {name: "super-secret" for name in tool._SENSITIVE_HEADERS}
    mock_client(lambda request: response(headers={**sensitive, "X-Test": "visible"}))
    output = execute().output
    assert "super-secret" not in json.dumps(output)
    assert output["headers"]["x-test"] == "visible"
    assert all(output["headers"][name] == "***MASKED***" for name in sensitive)


@pytest.mark.parametrize("name", ["Authorization", "pRoXy-AuThOrIzAtIoN", "Cookie", "Set-Cookie", "X-Api-Key", "API-Key", "Host"])
def test_sensitive_or_unapproved_request_headers_blocked(mock_client, name):
    calls, _ = mock_client(lambda request: response())
    result = execute(headers={name: "super-secret"})
    assert result.error.code == "HEADER_NOT_ALLOWED"
    assert "super-secret" not in result.model_dump_json()
    assert not calls


def test_header_injection_blocked(mock_client):
    calls, _ = mock_client(lambda request: response())
    assert execute(headers={"Accept": "text/html\r\nCookie: secret"}).error.code == "INVALID_HEADER"
    assert not calls


def test_redirect_disabled_by_default(mock_client):
    calls, _ = mock_client(lambda request: response(302, headers={"Location": "/b"}))
    result = execute()
    assert result.status == ExecutionStatus.SUCCESS
    assert result.output["status_code"] == 302
    assert len(calls) == 1


def test_redirect_in_scope_no_cookie_replay(mock_client):
    def handler(request):
        if request.url.path == "/a":
            return response(302, headers={"Location": "/b", "Set-Cookie": "session=super-secret; Path=/"})
        assert "cookie" not in request.headers
        return response()
    calls, _ = mock_client(handler)
    result = execute(url="http://localhost/a", follow_redirects=True)
    assert result.status == ExecutionStatus.SUCCESS
    assert result.output["final_url"] == "http://localhost/b"
    assert result.output["redirect_chain"] == ["http://localhost/a"]
    assert len(calls) == 2


@pytest.mark.parametrize("location,code", [
    ("https://example.com", "REDIRECT_OUT_OF_SCOPE"),
    ("http://user:secret@localhost/b", "SAFETY_BLOCKED"),
    ("ftp://localhost", "SAFETY_BLOCKED"),
    ("http://localhost\\evil", "INVALID_URL"),
])
def test_redirect_revalidated_before_send(mock_client, location, code):
    calls, _ = mock_client(lambda request: response(302, headers={"Location": location}))
    result = execute(follow_redirects=True)
    assert result.status == ExecutionStatus.BLOCKED
    assert result.error.code == code
    assert len(calls) == 1
    assert "secret" not in result.model_dump_json()


def test_redirect_limit(mock_client):
    calls, _ = mock_client(lambda request: response(302, headers={"Location": "/b" if request.url.path == "/a" else "/a"}))
    result = execute(url="http://localhost/a", follow_redirects=True)
    assert result.status == ExecutionStatus.FAILED
    assert result.error.code == "TOO_MANY_REDIRECTS"
    assert len(calls) == 4


def test_invalid_server_redirect_header_is_structured(mock_client):
    # HTTPX rejects control characters while constructing response.next_request,
    # before the tool receives the response. No second request may be sent.
    calls, _ = mock_client(lambda request: response(302, headers={"Location": "http://local\nhost/b"}))
    result = execute(follow_redirects=True)
    assert result.status == ExecutionStatus.FAILED
    assert result.error.code == "NETWORK_ERROR"
    assert len(calls) == 1


@pytest.mark.parametrize("kwargs", [
    {"timeout_seconds": 0}, {"timeout_seconds": 31}, {"timeout_seconds": float("nan")},
    {"timeout_seconds": float("inf")}, {"max_body_bytes": 0},
    {"max_body_bytes": 1048577}, {"max_body_bytes": True},
])
def test_invalid_limits_fail_before_network(mock_client, kwargs):
    calls, settings = mock_client(lambda request: response())
    result = execute(**kwargs)
    assert result.status == ExecutionStatus.FAILED
    assert result.error.code == "INVALID_INPUT"
    assert not calls and not settings


def test_whole_operation_timeout_closes_stream(mock_client):
    class WaitingStream(Chunks):
        async def __aiter__(self):
            await asyncio.Event().wait()
            yield b"never reached"

    stream = WaitingStream([])
    calls, _ = mock_client(lambda request: response(stream=stream))
    result = execute(timeout_seconds=0.1)
    assert result.status == ExecutionStatus.TIMEOUT
    assert result.error.code == "HTTP_TIMEOUT"
    assert result.error.retryable is True
    assert len(calls) == 1
    assert stream.closed


def test_source_assessment_cannot_send(mock_client):
    calls, _ = mock_client(lambda request: response())
    result = asyncio.run(tool.http_request(
        assessment_request=AssessmentRequest(
            assessment_type=AssessmentType.SOURCE, source_directory="secureboard",
        ), url="http://localhost", test_id="TEST-SOURCE",
    ))
    assert result.status == ExecutionStatus.BLOCKED
    assert result.error.code == "SAFETY_BLOCKED"
    assert not calls


def test_three_redirects_can_complete(mock_client):
    def handler(request):
        hop = int(request.url.path.strip("/") or "0")
        return response(302, headers={"Location": f"/{hop + 1}"}) if hop < 3 else response()
    calls, _ = mock_client(handler)
    result = execute(follow_redirects=True)
    assert result.status == ExecutionStatus.SUCCESS
    assert len(result.output["redirect_chain"]) == 3
    assert len(calls) == 4


@pytest.mark.parametrize("allowlist,allowed", [(set(), False), ({"secureboard.local"}, True)])
def test_redirect_additional_host_requires_both_permissions(mock_client, allowlist, allowed):
    def handler(request):
        return response(302, headers={"Location": "https://secureboard.local/b"}) if request.url.host == "localhost" else response()
    calls, _ = mock_client(handler)
    result = execute(
        follow_redirects=True, allowlist=allowlist,
        scope=AssessmentScope(allowed_hosts=["secureboard.local"]),
    )
    assert (result.status == ExecutionStatus.SUCCESS) is allowed
    assert len(calls) == 1 + int(allowed)


def test_allowed_headers_preserved_without_mutation(mock_client):
    supplied = {"User-Agent": "SecureProbeTest/0.1", "Accept-Language": "ko", "If-None-Match": '"etag"'}
    original = supplied.copy()
    calls, _ = mock_client(lambda request: response())
    assert execute(headers=supplied).status == ExecutionStatus.SUCCESS
    assert supplied == original
    assert calls[0].headers.get_list("user-agent") == ["SecureProbeTest/0.1"]
    assert calls[0].headers["if-none-match"] == '"etag"'


def test_redirect_userinfo_header_not_retained(mock_client):
    mock_client(lambda request: response(302, headers={"Location": "http://user:super-secret@localhost"}))
    result = execute()
    assert result.output["headers"]["location"] == "***MASKED***"
    assert "super-secret" not in result.model_dump_json()


@pytest.mark.parametrize("length", ["bad", "-1", "9" * 100])
def test_invalid_content_length_is_metadata_null(mock_client, length):
    mock_client(lambda request: response(headers={"Content-Length": length}))
    assert execute().output["content_length"] is None
