"""Response metadata tests without HTTP clients or network fixtures."""

from types import MappingProxyType

import pytest
from pydantic import ValidationError

from secureprobe.models import HeaderInspectionResult, HeaderObservation
from secureprobe.web.tools.header_inspector import inspect_headers


NAMES = [
    "Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options",
    "Referrer-Policy", "Permissions-Policy", "Strict-Transport-Security", "Cache-Control", "Pragma",
]


def inspect(headers, url="https://localhost"):
    return inspect_headers(url=url, headers=headers)


def test_all_headers_present_in_fixed_order():
    headers = dict(reversed([(name, f" value-{i} ") for i, name in enumerate(NAMES)]))
    result = inspect(headers)
    assert [observation.name for observation in result.observations] == NAMES
    assert all(observation.present for observation in result.observations)
    assert [observation.value for observation in result.observations] == [f"value-{i}" for i in range(8)]
    assert result.scheme == "https"


def test_empty_headers():
    result = inspect({})
    assert len(result.observations) == 8
    assert all(not observation.present and observation.value is None for observation in result.observations)


@pytest.mark.parametrize("name", NAMES)
def test_case_insensitive_header_name(name):
    result = inspect({name.swapcase(): "observed"})
    present = [observation for observation in result.observations if observation.present]
    assert len(present) == 1
    assert present[0].name == name
    assert present[0].value == "observed"


@pytest.mark.parametrize("scheme", ["http", "https"])
@pytest.mark.parametrize("present", [False, True])
def test_hsts_scheme_context(scheme, present):
    headers = {"Strict-Transport-Security": "max-age=31536000"} if present else {}
    result = inspect(headers, url=f"{scheme}://localhost")
    observation = result.observations[5]
    assert observation.present is present
    assert ("HSTS is only effective over HTTPS" in observation.note) is (scheme == "http")
    assert "vulnerab" not in result.model_dump_json().lower()


@pytest.mark.parametrize("name", [
    "Authorization", "Proxy-Authorization", "Set-Cookie", "WWW-Authenticate", "X-Api-Key", "API-Key", "Cookie",
])
def test_sensitive_headers_excluded(name):
    result = inspect({name.swapcase(): "super-secret", "X-Frame-Options": "DENY"})
    serialized = result.model_dump_json()
    assert "super-secret" not in serialized
    assert name.lower() not in [observation.name.lower() for observation in result.observations]
    assert len(result.observations) == 8


def test_set_cookie_not_inspected():
    result = inspect({"Set-Cookie": "session=secret; Secure; HttpOnly; SameSite=Lax"})
    assert all(not observation.present for observation in result.observations)
    assert "secret" not in result.model_dump_json()
    assert set(result.model_dump()) == {"url", "scheme", "observations"}


def test_unknown_headers_ignored():
    result = inspect({name: "ignored" for name in ["Server", "Date", "Content-Length", "ETag", "X-Powered-By"]})
    assert all(not observation.present for observation in result.observations)
    assert "ignored" not in result.model_dump_json()


@pytest.mark.parametrize("length,truncated", [(4095, False), (4096, False), (4097, True), (10000, True)])
def test_value_length_limit(length, truncated):
    result = inspect({"Content-Security-Policy": "x" * length})
    observation = result.observations[0]
    assert len(observation.value) == min(length, 4096)
    assert ("value truncated" in observation.note) is truncated


@pytest.mark.parametrize("control", ["\r", "\n", "\x00", "\t", "\x7f", "\x85", "\u200b"])
def test_control_values_omitted_without_losing_presence(control):
    result = inspect({"Cache-Control": f"start{control}end"})
    observation = result.observations[6]
    assert observation.present is True
    assert observation.value is None
    assert "control characters" in observation.note


def test_present_but_empty_value():
    result = inspect({"Pragma": "   "})
    assert result.observations[7].present is True
    assert result.observations[7].value == ""


def test_mapping_input_preserved_and_result_deterministic():
    headers = {"x-frame-options": "SAMEORIGIN", "Cache-Control": "no-store"}
    original = headers.copy()
    result = inspect(MappingProxyType(headers))
    assert result == inspect(MappingProxyType(headers))
    assert headers == original
    assert [observation.name for observation in result.observations] == NAMES


def test_duplicate_case_variant_uses_first_mapping_entry():
    result = inspect({"x-frame-options": "DENY", "X-Frame-Options": "SAMEORIGIN"})
    assert result.observations[2].value == "DENY"


@pytest.mark.parametrize("url", [
    "ftp://localhost", "relative/path", "http://user:pass@localhost", "http://[::1",
    "http:///admin", "http://local host", "http://localhost:bad", "", None,
])
def test_invalid_url(url):
    with pytest.raises(ValueError):
        inspect({}, url=url)


@pytest.mark.parametrize("headers", [None, [], "headers", [("Pragma", "value")], {1: "value"}, {"Pragma": None}, {"Server": 123}])
def test_invalid_header_input(headers):
    with pytest.raises(ValueError):
        inspect(headers)


@pytest.mark.parametrize("update", [{"name": ""}, {"name": " "}, {"present": "yes"}, {"severity": "HIGH"}])
def test_observation_model_rejects_invalid_payload(update):
    with pytest.raises(ValidationError):
        HeaderObservation.model_validate({"name": "Pragma", "present": True, **update})


@pytest.mark.parametrize("update", [
    {"url": ""}, {"scheme": "ftp"}, {"observations": "bad"},
    {"ground_truth_id": "GT-1"}, {"benchmark_result": {}}, {"finding": {}},
])
def test_result_model_rejects_invalid_payload(update):
    with pytest.raises(ValidationError):
        HeaderInspectionResult.model_validate({"url": "https://localhost", "scheme": "https", **update})


def test_model_round_trip_and_mutable_default_isolation():
    first = HeaderInspectionResult(url="https://localhost", scheme="https")
    second = HeaderInspectionResult(url="https://localhost", scheme="https")
    first.observations.append(HeaderObservation(name="Pragma", present=False))
    assert second.observations == []
    result = inspect({"X-Frame-Options": "DENY"})
    assert HeaderInspectionResult.model_validate(result.model_dump(mode="json")) == result
