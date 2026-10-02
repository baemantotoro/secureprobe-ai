"""Deterministic safety policy tests without network fixtures."""

import pytest
from pydantic import ValidationError

from secureprobe.core.safety import validate_web_target
from secureprobe.models import AssessmentRequest, AssessmentScope, AssessmentType, Credentials


def web_request(target, *, authorized=True, **kwargs):
    return AssessmentRequest(
        assessment_type=AssessmentType.WEB,
        target_url=target,
        authorization_confirmed=authorized,
        **kwargs,
    )


def assert_denied(result):
    assert result.allowed is False
    assert result.active_assessment_allowed is False
    assert result.validated_scope is None
    assert result.reason


@pytest.mark.parametrize("target", [
    "http://localhost", "http://localhost:8080", "https://LOCALHOST",
    "http://localhost.", "http://127.0.0.1", "http://127.0.0.1:5000",
    "http://[::1]", "http://[::1]:8080",
    "http://localhost/search?q=example.com#admin",
])
def test_local_active_allowed(target):
    result = validate_web_target(web_request(target), active=True)
    assert result.allowed is True
    assert result.active_assessment_allowed is True


@pytest.mark.parametrize("target", [
    "https://example.com", "https://www.google.com",
    "http://localhost.evil.com", "http://evil-localhost.com",
    "http://localhost-example.com", "http://127.0.0.1.evil.com",
    "http://127.0.0.2", "http://127.1", "http://2130706433",
    "http://[0:0:0:0:0:0:0:1]", "http://[::ffff:127.0.0.1]",
    "https://example.com/?host=localhost#127.0.0.1",
])
def test_external_active_denied(target):
    result = validate_web_target(web_request(target), active=True)
    assert_denied(result)
    assert result.reason == "external target not in allowlist"


@pytest.mark.parametrize("target,allowlist", [
    ("https://secureboard.local", {"secureboard.local"}),
    ("https://secureboard.local:8443", {"SECUREBOARD.LOCAL."}),
    ("https://SECUREBOARD.LOCAL.", {"secureboard.local"}),
    ("http://192.0.2.10", {"192.0.2.10"}),
    ("http://[2001:db8::1]", {"2001:db8::1"}),
])
def test_explicit_allowlist_allowed(target, allowlist):
    original = allowlist.copy()
    result = validate_web_target(web_request(target), active=True, allowlist=allowlist)
    assert result.allowed is True
    assert result.active_assessment_allowed is True
    assert result.reason == "explicit allowlist target"
    assert allowlist == original


@pytest.mark.parametrize("host", ["secureboard.local.evil.com", "evilsecureboard.local"])
def test_allowlist_requires_exact_match(host):
    assert_denied(validate_web_target(
        web_request(f"https://{host}"), active=True, allowlist={"secureboard.local"},
    ))


@pytest.mark.parametrize("entry", [
    "https://secureboard.local", "secureboard.local:443", "*.local",
    "192.0.2.0/24", "secureboard.local/path", "secureboard.*",
    " secureboard.local", "secureboard.local..", "[2001:db8::1]",
])
def test_unsupported_allowlist_entries_do_not_authorize(entry):
    assert_denied(validate_web_target(
        web_request("https://secureboard.local"), active=True, allowlist={entry},
    ))


@pytest.mark.parametrize("host,allowlist", [
    ("localhost", None), ("127.0.0.1", set()), ("[::1]", None),
    ("secureboard.local", {"secureboard.local"}),
])
def test_authorization_required_for_active(host, allowlist):
    result = validate_web_target(
        web_request(f"http://{host}", authorized=False), active=True, allowlist=allowlist,
    )
    assert_denied(result)
    assert result.reason == "authorization not confirmed"


@pytest.mark.parametrize("target,authorized", [
    ("https://example.com", True), ("http://localhost", False),
])
def test_credentials_do_not_grant_authorization(target, authorized):
    request = web_request(
        target, authorized=authorized,
        credentials=Credentials(username="tester", password_ref="runtime-secret:tester"),
    )
    assert_denied(validate_web_target(request, active=True))


@pytest.mark.parametrize("host,authorized,allowlist,active_allowed", [
    ("example.com", False, None, False),
    ("example.com", True, None, False),
    ("localhost", False, None, False),
    ("localhost", True, None, True),
    ("secureboard.local", False, {"secureboard.local"}, False),
    ("secureboard.local", True, {"secureboard.local"}, True),
])
def test_passive_validation_separates_active_permission(host, authorized, allowlist, active_allowed):
    result = validate_web_target(
        web_request(f"https://{host}", authorized=authorized), active=False, allowlist=allowlist,
    )
    assert result.allowed is True
    assert result.active_assessment_allowed is active_allowed


@pytest.mark.parametrize("target", [
    "ftp://localhost", "file:///etc/passwd", "gopher://localhost",
    "ws://localhost", "wss://localhost", "data:text/plain,test",
    "javascript:alert(1)",
    "http://user:pass@localhost", "http://localhost@evil.com", "http://@localhost",
    "/admin", "localhost:8080", "http:///admin", "://localhost",
    "http://[::1", "http://localhost:bad", "http://localhost:65536",
    "http://localhost:-1", "http://localhost:", "http://local\nhost",
    "http://localhost\\@evil.com", "http://local host", "http://%6cocalhost",
    "http://localhost..", "http://[::1%25eth0]", "http://localhost\x00",
    "http://[::1]evil.com:80", "http://[::1].evil.com:80", "http://localhost:0",
])
@pytest.mark.parametrize("active", [False, True])
def test_invalid_urls_denied_in_both_modes(target, active):
    assert_denied(validate_web_target(web_request(target), active=active))


@pytest.mark.parametrize("target", [None, "", "   "])
def test_missing_url_rejected_by_model_and_gate(target):
    with pytest.raises(ValidationError):
        web_request(target)
    # Exercise defensive handling for callers bypassing Pydantic validation.
    request = AssessmentRequest.model_construct(
        assessment_type=AssessmentType.WEB, target_url=target,
    )
    assert_denied(validate_web_target(request, active=True))


@pytest.mark.parametrize("active", [False, True])
def test_source_request_is_unsupported(active):
    request = AssessmentRequest(assessment_type=AssessmentType.SOURCE, source_directory="secureboard")
    result = validate_web_target(request, active=active)
    assert_denied(result)
    assert result.reason == "unsupported assessment type"


def test_scope_preserved_without_granting_host_authorization():
    scope = AssessmentScope(
        allowed_hosts=["example.com"], allowed_paths=["/app"], deny_paths=["/logout"],
        include_paths=["src"], exclude_paths=["vendor"],
    )
    request = web_request("https://example.com/app", scope=scope)
    original = request.model_dump()
    passive = validate_web_target(request, active=False)
    assert passive.validated_scope.model_dump() == scope.model_dump()
    assert passive.active_assessment_allowed is False
    assert_denied(validate_web_target(request, active=True))
    allowed = validate_web_target(request, active=True, allowlist={"example.com"})
    assert allowed.validated_scope.model_dump() == scope.model_dump()
    assert request.model_dump() == original
