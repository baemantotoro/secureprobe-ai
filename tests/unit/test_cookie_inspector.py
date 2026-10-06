"""Cookie metadata tests require no transport, session or credentials."""

import json

import pytest
from pydantic import ValidationError

from secureprobe.models import CookieInfo
from secureprobe.web.tools.cookie_inspector import inspect_cookies


def inspect(headers, **kwargs):
    return inspect_cookies(set_cookie_headers=headers, **kwargs)


def test_basic_cookie_value_not_stored():
    result = inspect("SESSION=abc123")
    assert result[0].model_dump() == {
        "name": "SESSION", "secure": False, "http_only": False,
        "same_site": None, "domain": None, "path": None, "max_age": None, "expires": None,
    }
    assert "abc123" not in result[0].model_dump_json()
    assert "value" not in CookieInfo.model_fields


@pytest.mark.parametrize("flags,secure,http_only", [
    ("Secure", True, False), ("HttpOnly", False, True),
    ("Secure; HttpOnly", True, True), ("secure; HTTPONLY", True, True),
    ("Secure=false; HttpOnly=false", True, True),
])
def test_flags_observed_by_presence(flags, secure, http_only):
    cookie = inspect(f"SESSION=secret; {flags}")[0]
    assert cookie.secure is secure
    assert cookie.http_only is http_only
    assert "secret" not in cookie.model_dump_json()


@pytest.mark.parametrize("value,expected", [
    ("Strict", "Strict"), ("strict", "Strict"), ("LAX", "Lax"),
    ("lAx", "Lax"), ("None", "None"), ("nOnE", "None"), ("Invalid", None), ("", None),
])
def test_same_site_canonical(value, expected):
    assert inspect(f"id=secret; sAmEsItE={value}")[0].same_site == expected


def test_domain_path_max_age_expires_and_case():
    cookie = inspect("id=secret; DOMAIN=LOCALHOST; PATH=/app; Max-Age=3600; Expires=Wed, 21 Oct 2026 07:28:00 GMT")[0]
    assert cookie.domain == "LOCALHOST"
    assert cookie.path == "/app"
    assert cookie.max_age == 3600
    assert cookie.expires == "Wed, 21 Oct 2026 07:28:00 GMT"


@pytest.mark.parametrize("value,expected", [("abc", None), ("1.5", None), ("", None), ("0", 0), ("-1", -1), ("+3600", 3600)])
def test_max_age_invalid_does_not_drop_cookie(value, expected):
    result = inspect(f"id=secret; Max-Age={value}; Secure")
    assert result[0].max_age == expected
    assert result[0].secure is True


def test_multiple_headers_duplicate_names_input_order():
    headers = ["id=first-secret; Path=/", "theme=second-secret; SameSite=Lax", "id=third-secret; Path=/admin"]
    original = headers.copy()
    result = inspect(headers)
    assert [cookie.name for cookie in result] == ["id", "theme", "id"]
    assert [cookie.path for cookie in result] == ["/", None, "/admin"]
    assert headers == original
    serialized = json.dumps([cookie.model_dump() for cookie in result])
    assert all(secret not in serialized for secret in ["first-secret", "second-secret", "third-secret"])
    assert result == inspect(headers)


@pytest.mark.parametrize("value", ['"abc;123"', '"abc; Secure; Domain=private-cookie-value"', '"abc\\\";123"'])
def test_quoted_value_does_not_become_attributes(value):
    cookie = inspect(f"session={value}; Secure; HttpOnly")[0]
    assert cookie.name == "session"
    assert cookie.secure and cookie.http_only
    assert cookie.domain is None
    assert "abc" not in cookie.model_dump_json()
    assert "private-cookie-value" not in cookie.model_dump_json()


def test_unknown_attributes_ignored_not_new_cookies():
    result = inspect("id=secret; Priority=High; Partitioned; Foo=unknown-secret; Secure; HttpOnly")
    assert len(result) == 1
    assert result[0].secure and result[0].http_only
    assert "unknown-secret" not in result[0].model_dump_json()


@pytest.mark.parametrize("bad", ["", "   ", "broken", "=bad", "bad name=value", 'id="unclosed', 'id="escaped\\'])
def test_malformed_cookie_individually_ignored(bad):
    assert [cookie.name for cookie in inspect([bad, "valid=secret; Secure"])] == ["valid"]


@pytest.mark.parametrize("control", ["\r", "\n", "\x00", "\t", "\x7f", "\x85", "\u200b"])
def test_control_headers_excluded(control):
    result = inspect([f"id=token-secret{control}; Secure", "good=private-cookie-value"])
    assert [cookie.name for cookie in result] == ["good"]
    assert "private-cookie-value" not in result[0].model_dump_json()


def test_header_size_boundary_and_oversized_header():
    exact = "id=" + "x" * (8192 - 3)
    assert len(inspect(exact)) == 1
    assert inspect(exact + "x") == []
    assert [cookie.name for cookie in inspect([exact + "x", "good=secret"])] == ["good"]


@pytest.mark.parametrize("attribute,field", [("Domain", "domain"), ("Path", "path"), ("Expires", "expires")])
def test_metadata_length_limited(attribute, field):
    cookie = inspect(f"id=secret; {attribute}=" + "x" * 3000)[0]
    assert len(getattr(cookie, field)) == 2048


def test_oversized_max_age_not_parsed_as_truncated_integer():
    assert inspect("id=secret; Max-Age=" + "1" * 3000)[0].max_age is None


def test_cookie_limit_counts_only_valid_cookies():
    headers = ["broken"] + [f"id{i}=secret" for i in range(100)]
    assert [cookie.name for cookie in inspect(headers, max_cookies=10)] == [f"id{i}" for i in range(10)]
    assert len(inspect(headers)) == 50
    assert len(inspect(headers, max_cookies=200)) == 100
    assert inspect([]) == []


@pytest.mark.parametrize("limit", [0, -1, 201, True, False, 1.5, "10", None])
def test_invalid_limit(limit):
    with pytest.raises(ValueError):
        inspect("id=secret", max_cookies=limit)


@pytest.mark.parametrize("headers", [None, {}, 123, ("id=secret",), ["id=secret", None]])
def test_invalid_input(headers):
    with pytest.raises(ValueError):
        inspect(headers)


def test_expires_comma_and_quoted_metadata():
    result = inspect('id=secret; Expires=Wed, 21 Oct 2026 07:28:00 GMT; Path="/app;section"')
    assert len(result) == 1
    assert result[0].expires == "Wed, 21 Oct 2026 07:28:00 GMT"
    assert result[0].path == "/app;section"


def test_duplicate_attribute_last_value():
    cookie = inspect("id=secret; Path=/first; Path=/last; SameSite=Strict; SameSite=Lax")[0]
    assert cookie.path == "/last"
    assert cookie.same_site == "Lax"


@pytest.mark.parametrize("update", [
    {"name": ""}, {"name": " "}, {"secure": "yes"}, {"http_only": 1},
    {"value": "secret"}, {"same_site": "Unknown"}, {"severity": "HIGH"},
    {"ground_truth_id": "GT-1"}, {"benchmark_result": {}},
])
def test_cookie_model_rejects_invalid_or_extra_fields(update):
    with pytest.raises(ValidationError):
        CookieInfo.model_validate({"name": "id", "secure": False, "http_only": False, **update})


def test_json_round_trip():
    cookie = inspect("id=secret; Secure; HttpOnly; SameSite=Lax; Path=/; Max-Age=3600")[0]
    assert CookieInfo.model_validate(cookie.model_dump(mode="json")) == cookie
