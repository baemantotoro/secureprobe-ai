"""Pure form metadata tests; no network or credential fixtures."""

import pytest
from pydantic import ValidationError

from secureprobe.models import AssessmentScope, Form, FormField
from secureprobe.web.tools.form_parser import parse_forms


def parse(html="", **kwargs):
    return parse_forms(base_url=kwargs.pop("base_url", "http://localhost/app/page"), html=html, **kwargs)


def test_basic_form():
    result = parse('''<form action="/login" method="post">
        <input name="username" type="text"><input name="password" type="password">
    </form>''')
    assert [form.model_dump() for form in result] == [{
        "action": "http://localhost/login", "method": "POST", "fields": [
            {"name": "username", "type": "text"}, {"name": "password", "type": "password"},
        ],
    }]


@pytest.mark.parametrize("action,expected", [
    ("../login", "http://localhost/login"),
    ("/search?type=all", "http://localhost/search?type=all"),
    ("/login#form", "http://localhost/login"),
    ("//LOCALHOST.:8080/login", "http://localhost:8080/login"),
    ("https://LOCALHOST./login", "https://localhost/login"),
    ("", "http://localhost/app/page"),
    ("#form", "http://localhost/app/page"),
])
def test_action_normalization(action, expected):
    assert parse(f'<form action="{action}"></form>')[0].action == expected


def test_default_method_and_missing_action():
    result = parse('<form action="/search"></form><form method="POST"></form>', base_url="http://localhost/index?q=1#top")
    assert [(form.action, form.method) for form in result] == [
        ("http://localhost/search", "GET"), ("http://localhost/index?q=1", "POST"),
    ]


def test_field_types_and_dom_order():
    result = parse('''<form><textarea name="content"></textarea><select name="role"></select>
        <input name="username"><input type=" PASSWORD " name="password">
        <input type="hidden" name="csrf_token"><input type="" name="blank_type">
        <input type name="boolean_type"><button name="ignored">Send</button></form>''')
    assert [(field.name, field.type) for field in result[0].fields] == [
        ("content", "textarea"), ("role", "select"), ("username", "text"),
        ("password", "password"), ("csrf_token", "hidden"),
        ("blank_type", "text"), ("boolean_type", "text"),
    ]


def test_no_name_fields_excluded():
    result = parse('<form><input><input name=""><input name="   "><input name><textarea></textarea><select name=""></select></form>')
    assert result[0].fields == []


def test_sensitive_values_not_stored():
    result = parse('''<form>
        <input type="password" name="password" value="super-secret">
        <input type="hidden" name="csrf_token" value="token-secret">
        <textarea name="memo">secret-text</textarea>
        <select name="role"><option selected value="admin-secret">Admin</option></select>
    </form>''')
    serialized = result[0].model_dump_json()
    for secret in ["super-secret", "token-secret", "secret-text", "admin-secret"]:
        assert secret not in serialized
    assert [(field.name, field.type) for field in result[0].fields] == [
        ("password", "password"), ("csrf_token", "hidden"), ("memo", "textarea"), ("role", "select"),
    ]


def test_duplicate_fields_dedupe_by_name_and_type():
    result = parse('''<form><input name="q"><input name="q" type="TEXT">
        <input name="q" type="hidden"><textarea name="q"></textarea><input name="q"></form>''')
    assert [(field.name, field.type) for field in result[0].fields] == [
        ("q", "text"), ("q", "hidden"), ("q", "textarea"),
    ]


@pytest.mark.parametrize("method", ["delete", "PUT", "HEAD", "OPTIONS", "dialog", ""])
def test_unsupported_method_ignored(method):
    result = parse(f'<form method="{method}" action="/bad"></form><form action="/good"></form>')
    assert [form.action for form in result] == ["http://localhost/good"]


@pytest.mark.parametrize("action", [
    "javascript:alert(1)", "data:text/plain,test", "mailto:user@example.com", "tel:123",
    "ftp://localhost", "file:///etc/passwd", "gopher://localhost", "ws://localhost", "wss://localhost",
    "http://user:pass@localhost/login", "http://localhost@evil.com/login",
    "https://example.com/login", "http://localhost.evil.com/login", "http://evil-localhost.com/",
    "http://[::1", "http://local host", "http:///admin", "http://localhost:bad",
    "http://localhost:65536", "http://local\nhost", "http://localhost\\evil", "://localhost",
])
def test_invalid_or_out_of_scope_action_only_skips_its_form(action):
    result = parse(f'<form action="{action}"><input name="bad"></form><form action="/good"><input name="good"></form>')
    assert [form.action for form in result] == ["http://localhost/good"]


def test_scoped_host_candidate_does_not_mutate_scope():
    scope = AssessmentScope(allowed_hosts=["SECUREBOARD.LOCAL."], allowed_paths=["/app"], deny_paths=["/logout"])
    original = scope.model_dump()
    result = parse('''<form action="https://secureboard.local/login"></form>
        <form action="https://secureboard.local.evil.com/login"></form>''', scope=scope)
    assert len(result) == 1
    assert result[0].action == "https://secureboard.local/login"
    assert scope.model_dump() == original


@pytest.mark.parametrize("html", ["", "<p>No forms</p>", "plain text"])
def test_no_forms_returns_empty(html):
    assert parse(html) == []


def test_form_and_field_limits_after_filtering_and_deduplication():
    fields = '<input><input name="same"><input name="same">' + ''.join(f'<input name="field{i}">' for i in range(110))
    html = '<form method="delete"></form>' + ''.join(f'<form action="/form{i}">{fields}</form>' for i in range(60))
    result = parse(html, max_forms=2, max_fields_per_form=3)
    assert [form.action for form in result] == ["http://localhost/form0", "http://localhost/form1"]
    assert [field.name for field in result[0].fields] == ["same", "field0", "field1"]
    defaults = parse(html)
    assert len(defaults) == 50
    assert all(len(form.fields) == 100 for form in defaults)


@pytest.mark.parametrize("option,invalid", [
    ("max_forms", 0), ("max_forms", -1), ("max_forms", 201), ("max_forms", True),
    ("max_forms", 1.5), ("max_forms", "1"), ("max_forms", None),
    ("max_fields_per_form", 0), ("max_fields_per_form", -1), ("max_fields_per_form", 501),
    ("max_fields_per_form", False), ("max_fields_per_form", 2.0),
    ("max_fields_per_form", "2"), ("max_fields_per_form", None),
])
def test_invalid_limits(option, invalid):
    with pytest.raises(ValueError):
        parse(**{option: invalid})


@pytest.mark.parametrize("base", ["", "relative/path", "ftp://localhost", "http://user:secret@localhost", "http://[::1", None])
def test_invalid_base_has_clear_failure(base):
    with pytest.raises(ValueError):
        parse(base_url=base)


def test_deterministic_malformed_html():
    html = '<form action="/first"><input name="q"><textarea name="memo"></textarea></form><form action="/second"><input name="x">'
    result = parse(html)
    assert [form.action for form in result] == ["http://localhost/first", "http://localhost/second"]
    assert result == parse(html)


def test_nested_form_fields_not_assigned_to_parent():
    result = parse('<form action="/outer"><input name="outer"><form action="/inner"><input name="inner"></form></form>')
    assert [field.name for field in result[0].fields] == ["outer"]
    assert [field.name for field in result[1].fields] == ["inner"]


def test_ipv6_and_html_base_handling():
    result = parse('<base href="https://evil.example/"><form action="/login"></form>', base_url="http://[::1]:8080/")
    assert result[0].action == "http://[::1]:8080/login"


@pytest.mark.parametrize("payload", [
    {"name": "", "type": "text"}, {"name": "   ", "type": "text"},
    {"name": "q", "type": " "}, {"name": "q", "type": "text", "value": "secret"},
])
def test_form_field_model_invalid_payload(payload):
    with pytest.raises(ValidationError):
        FormField.model_validate(payload)


@pytest.mark.parametrize("update", [
    {"action": ""}, {"action": " "}, {"method": "DELETE"},
    {"fields": "bad"}, {"ground_truth_id": "GT-1"}, {"benchmark_result": {}},
])
def test_form_model_invalid_payload(update):
    with pytest.raises(ValidationError):
        Form.model_validate({"action": "http://localhost/login", "method": "POST", **update})


def test_model_normalization_round_trip_and_mutable_default():
    field = FormField(name=" q ", type=" TEXT ")
    assert field.name == "q"
    assert field.type == "text"
    first = Form(action="http://localhost/", method="GET")
    second = Form(action="http://localhost/", method="GET")
    first.fields.append(field)
    assert second.fields == []
    assert Form.model_validate(first.model_dump(mode="json")) == first
