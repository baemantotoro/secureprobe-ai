"""Pure HTML parser tests: no network transport or browser fixtures."""

import json

import pytest
from pydantic import ValidationError

from secureprobe.models import AssessmentScope, Endpoint, EndpointParameter
from secureprobe.web.tools.endpoint_collector import collect_endpoints


def collect(html="", **kwargs):
    return collect_endpoints(base_url=kwargs.pop("base_url", "http://localhost/index"), html=html, **kwargs)


def urls(endpoints):
    return [endpoint.url for endpoint in endpoints]


@pytest.mark.parametrize("html", ["", "plain text", "<p>hello</p>"])
def test_current_endpoint(html):
    result = collect(html)
    assert [endpoint.model_dump() for endpoint in result] == [{
        "url": "http://localhost/index", "method": "GET", "source": "current", "parameters": [],
    }]


@pytest.mark.parametrize("reference,expected", [
    ("/login", "http://localhost:5000/login"),
    ("../admin", "http://localhost:5000/admin"),
    ("login", "http://localhost:5000/app/login"),
    ("http://LOCALHOST.:5000/admin", "http://localhost:5000/admin"),
    ("//localhost:5000/path", "http://localhost:5000/path"),
    ("https://localhost/admin", "https://localhost/admin"),
])
def test_url_normalization(reference, expected):
    result = collect(f'<a href="{reference}">link</a>', base_url="http://localhost:5000/app/page")
    assert result[1].url == expected
    assert result[1].method == "GET"
    assert result[1].source == "link"


def test_query_preserved_names_deduplicated():
    result = collect('<a href="/search?q=test&amp;page=1&amp;q=other&amp;empty=&amp;encoded%20name=x">')
    assert result[1].url == "http://localhost/search?q=test&page=1&q=other&empty=&encoded%20name=x"
    assert [parameter.model_dump() for parameter in result[1].parameters] == [
        {"name": name, "location": "query"} for name in ["q", "page", "empty", "encoded name"]
    ]


def test_fragment_removal_and_empty_links():
    result = collect('<a href="/page#one"><a href="/page#two"><a href=""><a href="#"><a href="#section"><a>')
    assert urls(result) == ["http://localhost/index", "http://localhost/page"]
    assert collect(base_url="http://localhost/index?q=1#top")[0].url == "http://localhost/index?q=1"


@pytest.mark.parametrize("method,expected", [("get", "GET"), ("post", "POST"), (" PoSt ", "POST")])
def test_form_method_metadata(method, expected):
    result = collect(f'<form action="/search" method="{method}"><input name="q"></form>')
    assert result[1].method == expected
    assert result[1].source == "form"
    assert result[1].parameters == [EndpointParameter(name="q", location="form")]


def test_form_default_method_and_missing_action():
    result = collect('<form action="/search"></form><form method="post"></form>')
    assert [(endpoint.method, endpoint.url) for endpoint in result] == [
        ("GET", "http://localhost/index"), ("GET", "http://localhost/search"),
        ("POST", "http://localhost/index"),
    ]


@pytest.mark.parametrize("method", ["put", "delete", "HEAD", "dialog", ""])
def test_unsupported_form_method_ignored(method):
    assert len(collect(f'<form action="/skip" method="{method}"></form>')) == 1


def test_form_fields_merge_without_storing_values():
    result = collect('''<form action="/login?next=home" method="post">
        <input name="username" value="alice-secret">
        <input name="password" type="password" value="password-secret">
        <input name="csrf" type="hidden" value="token-secret">
        <textarea name="message">textarea-secret</textarea>
        <select name="choice"><option value="option-secret">secret</option></select>
        <input name="username"><input name=""><input><button name="ignored">
    </form>''')
    endpoint = result[1]
    assert [(parameter.name, parameter.location) for parameter in endpoint.parameters] == [
        ("next", "query"), ("username", "form"), ("password", "form"),
        ("csrf", "form"), ("message", "form"), ("choice", "form"),
    ]
    serialized = endpoint.model_dump_json()
    for secret in ["alice-secret", "password-secret", "token-secret", "textarea-secret", "option-secret"]:
        assert secret not in serialized


@pytest.mark.parametrize("reference", [
    "javascript:alert(1)", "mailto:test@example.com", "tel:01012345678",
    "data:text/plain,test", "ftp://localhost/file", "file:///etc/passwd",
    "gopher://localhost", "ws://localhost", "wss://localhost",
    "http://user:pass@localhost/", "http://localhost@evil.com/",
    "http://localhost.evil.com/admin", "http://evil-localhost.com",
    "https://example.com", "http://[::1", "http://local host",
    "http:///admin", "http://localhost:bad", "http://localhost:65536",
    "http://local\nhost", "http://localhost\\evil", "://localhost",
])
def test_rejected_candidates_do_not_prevent_valid_collection(reference):
    result = collect(f'<a href="{reference}">bad</a><form action="{reference}" method="post"></form><a href="/good">good</a>')
    assert urls(result) == ["http://localhost/index", "http://localhost/good"]


def test_additional_scope_hosts_are_candidates_only():
    scope = AssessmentScope(allowed_hosts=["SECUREBOARD.LOCAL."], allowed_paths=["/app"], deny_paths=["/logout"])
    original = scope.model_dump()
    result = collect('''<a href="https://secureboard.local/path">
        <a href="https://secureboard.local.evil.com/">
        <a href="https://evilsecureboard.local/">
        <a href="https://other.example/">''', scope=scope)
    assert urls(result) == ["http://localhost/index", "https://secureboard.local/path"]
    assert scope.model_dump() == original


def test_deduplication_first_source_and_parameter_merge():
    result = collect('''<a href="/login?q=1"><a href="/login?q=1#top">
        <form action="/login?q=1"><input name="q"><input name="username"></form>
        <form action="/login?q=1"><input name="username"><input name="csrf"></form>
        <form action="/login?q=1" method="post"><input name="password"></form>''')
    assert len(result) == 3
    assert result[1].source == "link"
    assert result[1].method == "GET"
    assert [(parameter.name, parameter.location) for parameter in result[1].parameters] == [
        ("q", "query"), ("q", "form"), ("username", "form"), ("csrf", "form"),
    ]
    assert result[2].method == "POST"


def test_deterministic_dom_order_and_limit():
    html = '<form action="/first" method="post"></form>' + ''.join(f'<a href="/item/{i}">' for i in range(120))
    first = collect(html, max_endpoints=10)
    assert len(first) == 10
    assert urls(first)[:3] == ["http://localhost/index", "http://localhost/first", "http://localhost/item/0"]
    assert first == collect(html, max_endpoints=10)
    assert len(collect(html, max_endpoints=1)) == 1
    assert len(collect(html)) == 100


def test_retained_endpoint_parameters_merge_after_cap_reached():
    result = collect('<a href="/extra"><form><input name="retained"></form>', max_endpoints=1)
    assert len(result) == 1
    assert result[0].source == "current"
    assert result[0].parameters == [EndpointParameter(name="retained", location="form")]


@pytest.mark.parametrize("limit", [0, -1, 501, True, False, 1.5, "10", None])
def test_invalid_limits(limit):
    with pytest.raises(ValueError):
        collect(max_endpoints=limit)


@pytest.mark.parametrize("base", ["", "/path", "ftp://localhost", "http://user:secret@localhost", "http://[::1", None])
def test_invalid_base_has_clear_error(base):
    with pytest.raises(ValueError):
        collect(base_url=base)


def test_ignored_elements_and_html_base_cannot_change_scope():
    result = collect('''<base href="https://evil.example/">
        <script src="/script.js">fetch('/fake')</script><img src="/image">
        <iframe src="/frame"></iframe><link href="/style"><meta http-equiv="refresh" content="0;url=/meta">
        <a onclick="fetch('/onclick')">no href</a><a href="/real">''')
    assert urls(result) == ["http://localhost/index", "http://localhost/real"]


def test_malformed_html_does_not_crash():
    result = collect('<form method action="/bad"><input name></form><a href="/good"><form action="/good"><input name>')
    assert "http://localhost/good" in urls(result)


def test_ipv6_normalization():
    result = collect('<a href="//[::1]:8080/next#top">', base_url="http://[::1]:8080/")
    assert urls(result) == ["http://[::1]:8080/", "http://[::1]:8080/next"]


@pytest.mark.parametrize("update", [
    {"url": " "}, {"method": "DELETE"}, {"source": "script"},
    {"parameters": "bad"}, {"ground_truth_id": "GT-1"},
    {"parameters": [{"name": "password", "location": "form", "value": "secret"}]},
])
def test_endpoint_model_invalid_payload_rejected(update):
    with pytest.raises(ValidationError):
        Endpoint.model_validate({"url": "http://localhost/", "method": "GET", "source": "link", **update})


def test_model_serialization_and_mutable_default_isolation():
    first = Endpoint(url="http://localhost/", method="GET", source="current")
    second = Endpoint(url="http://localhost/", method="GET", source="current")
    first.parameters.append(EndpointParameter(name="q", location="query"))
    assert second.parameters == []
    assert Endpoint.model_validate(json.loads(first.model_dump_json())) == first
