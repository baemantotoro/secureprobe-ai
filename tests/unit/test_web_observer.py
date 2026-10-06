"""Observer contracts with structured HTTP mocks and real passive parsers."""
import ast
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import pytest
from pydantic import ValidationError
from secureprobe.models import AssessmentRequest, CookieInfo, ExecutionStatus, ToolError, ToolExecution, WebTargetContext
from secureprobe.web import observer

@pytest.fixture
def request_model():
    return AssessmentRequest(assessment_type='WEB', target_url='http://localhost')

@pytest.fixture
def output():
    return {'status_code': 200, 'final_url': 'http://localhost/home', 'headers': {'x-content-type-options': 'nosniff', 'X-Frame-Options': 'DENY'}, 'cookies': [{'name': 'SESSION', 'secure': True, 'http_only': True, 'same_site': 'Lax'}], 'content_type': 'Text/HTML; Charset=UTF-8', 'body_excerpt': '<a href="/login">Login</a><form action="/login" method="post"><input name="username"><input name="password" type="password"></form>', 'body_truncated': False, 'redirect_chain': ['http://localhost/home']}

@pytest.fixture
def mock_http(monkeypatch, output):
    calls = []

    async def fake(**kwargs):
        calls.append(kwargs)
        return ToolExecution(execution_id='exec-mock', test_id=kwargs['test_id'], tool_name='http_request', status=ExecutionStatus.SUCCESS, started_at=datetime.now(timezone.utc), output=output)
    monkeypatch.setattr(observer, 'http_request', fake)
    return calls

def test_html_context_and_call_contract(request_model, output, mock_http):
    before = request_model.model_dump()
    allowed = {'localhost'}
    context = asyncio.run(observer.observe_web_target(assessment_request=request_model, test_id='custom', allowlist=allowed))
    assert context.base_url == output['final_url']
    assert context.content_types == ['text/html']
    assert [(e.method, e.url) for e in context.endpoints] == [('GET', 'http://localhost/home'), ('GET', 'http://localhost/login'), ('POST', 'http://localhost/login')]
    assert context.forms[0].action == 'http://localhost/login'
    assert context.authentication_detected is True
    assert context.session_detected is True
    assert isinstance(context.cookies[0], CookieInfo)
    assert context.headers['X-Content-Type-Options'] == 'nosniff'
    assert context.headers['X-Frame-Options'] == 'DENY'
    assert context.headers['Content-Security-Policy'] is None
    assert len(context.headers) == 8
    assert context.context_id.startswith('CTX-WEB-')
    assert WebTargetContext.model_validate_json(context.model_dump_json()) == context
    assert mock_http == [dict(assessment_request=request_model, url=request_model.target_url, test_id='custom', method='GET', follow_redirects=True, allowlist=allowed)]
    assert mock_http[0]['allowlist'] is allowed
    assert request_model.model_dump() == before

@pytest.mark.parametrize('mime,expected', [('application/json; charset=utf-8', 'application/json'), ('application/pdf', 'application/pdf'), ('image/png', 'image/png'), ('application/octet-stream', 'application/octet-stream'), ('text/plain', 'text/plain'), (None, None), (' ; charset=utf-8', None)])
def test_non_html_skips_parsers(request_model, output, mock_http, monkeypatch, mime, expected):
    output['content_type'] = mime
    output['body_excerpt'] = None

    def forbidden(**kwargs):
        pytest.fail('non-HTML must not invoke HTML parsers')
    monkeypatch.setattr(observer, 'collect_endpoints', forbidden)
    monkeypatch.setattr(observer, 'parse_forms', forbidden)
    context = asyncio.run(observer.observe_web_target(assessment_request=request_model))
    assert context.endpoints == context.forms == []
    assert context.content_types == ([expected] if expected else [])
    assert context.authentication_detected is False
    assert context.session_detected is True
    assert mock_http[0]['test_id'] == 'OBSERVE-WEB-001'

@pytest.mark.parametrize('body', ['', None])
def test_empty_html(request_model, output, mock_http, body):
    output['body_excerpt'] = body
    context = asyncio.run(observer.observe_web_target(assessment_request=request_model))
    assert len(context.endpoints) == 1
    assert context.endpoints[0].source == 'current'
    assert context.forms == []
    assert context.authentication_detected is False

def test_truncated_html(request_model, output, mock_http):
    output.update(body_truncated=True, body_excerpt='<form><input name="pw" type="password"><a href="/more">')
    context = asyncio.run(observer.observe_web_target(assessment_request=request_model))
    assert context.authentication_detected is True
    assert any((e.url == 'http://localhost/more' for e in context.endpoints))
    assert 'body_truncated' not in context.model_dump()

@pytest.mark.parametrize('name,expected', [('SESSION', True), ('sessionid', True), ('JSESSIONID', True), ('PHPSESSID', True), ('connect.sid', True), ('theme', False), ('language', False), ('analytics', False), ('session-extra', False), ('mysession', False)])
def test_exact_session_hint(request_model, output, mock_http, name, expected):
    output['cookies'][0]['name'] = name
    assert asyncio.run(observer.observe_web_target(assessment_request=request_model)).session_detected is expected

@pytest.mark.parametrize('html', ['<a href="/login">Login</a>', '<form action="/auth"><input name="password"></form>', ''])
def test_auth_requires_password_type(request_model, output, mock_http, html):
    output['body_excerpt'] = html
    output['final_url'] = 'http://localhost/signin'
    output['cookies'] = []
    context = asyncio.run(observer.observe_web_target(assessment_request=request_model))
    assert context.authentication_detected is False
    assert context.session_detected is False

def test_non_web_before_http(mock_http):
    request = AssessmentRequest(assessment_type='SOURCE', source_directory='src')
    with pytest.raises(ValueError, match='WEB assessment'):
        asyncio.run(observer.observe_web_target(assessment_request=request))
    assert mock_http == []

@pytest.mark.parametrize('status', [ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT, ExecutionStatus.BLOCKED, ExecutionStatus.UNSUPPORTED])
def test_failure_without_secret(request_model, monkeypatch, status):

    async def fake(**kwargs):
        return ToolExecution(execution_id='fail', test_id='test', tool_name='http_request', status=status, started_at=datetime.now(timezone.utc), output={}, error=ToolError(code='private-token', message='raw-password'))
    monkeypatch.setattr(observer, 'http_request', fake)
    with pytest.raises(RuntimeError, match='HTTP tool did not succeed') as exc:
        asyncio.run(observer.observe_web_target(assessment_request=request_model))
    assert 'private-token' not in str(exc.value)
    assert 'raw-password' not in str(exc.value)

@pytest.mark.parametrize('key', ['final_url', 'headers', 'cookies', 'content_type', 'body_excerpt'])
def test_missing_output(request_model, output, mock_http, key):
    del output[key]
    with pytest.raises(ValueError, match=f'missing {key}'):
        asyncio.run(observer.observe_web_target(assessment_request=request_model))

@pytest.mark.parametrize('key,value', [('final_url', None), ('final_url', ' '), ('final_url', 1), ('headers', None), ('headers', []), ('headers', {'name': None}), ('headers', {1: 'value'}), ('cookies', None), ('cookies', {}), ('cookies', ['raw-password']), ('content_type', 1), ('body_excerpt', b'raw-password')])
def test_wrong_output_type(request_model, output, mock_http, key, value):
    output[key] = value
    with pytest.raises(ValueError, match=f'invalid HTTP output: {key}') as exc:
        asyncio.run(observer.observe_web_target(assessment_request=request_model))
    assert 'raw-password' not in str(exc.value)

@pytest.mark.parametrize('item', [{'name': 'SESSION', 'secure': 'yes', 'http_only': True}, {'name': 'SESSION', 'secure': True}, {'name': 'SESSION', 'secure': True, 'http_only': True, 'value': 'super-secret-cookie'}, {'name': 'SESSION', 'secure': True, 'http_only': 1}])
def test_invalid_cookie_sanitized(request_model, output, mock_http, item):
    output['cookies'] = [item]
    with pytest.raises(ValueError, match='cookie metadata') as exc:
        asyncio.run(observer.observe_web_target(assessment_request=request_model))
    assert 'super-secret-cookie' not in str(exc.value)
    assert exc.value.__suppress_context__

def test_sensitive_data_not_retained(request_model, output, mock_http):
    output['headers'].update({'Authorization': 'private-token', 'Proxy-Authorization': 'private-token', 'X-Api-Key': 'private-token', 'Set-Cookie': '[MASKED]', 'Cookie': '[MASKED]'})
    output['body_excerpt'] += '<input name="pw" type="password" value="raw-password">super-secret-cookie'
    output['ground_truth_id'] = 'private-token'
    output['benchmark_result'] = 'private-token'
    serialized = asyncio.run(observer.observe_web_target(assessment_request=request_model)).model_dump_json()
    for secret in ('private-token', 'raw-password', 'super-secret-cookie', 'Set-Cookie', 'Authorization', 'body_excerpt', 'ground_truth', 'benchmark'):
        assert secret not in serialized

def test_invalid_final_url_sanitized(request_model, output, mock_http):
    output['final_url'] = 'http://user:raw-password@localhost'
    with pytest.raises(ValueError, match='passive context assembly failed') as exc:
        asyncio.run(observer.observe_web_target(assessment_request=request_model))
    assert 'raw-password' not in str(exc.value)

@pytest.mark.parametrize('field', ['ground_truth_id', 'known_vulnerability', 'expected_ground_truth', 'expected_finding', 'zap_result', 'semgrep_result', 'benchmark_result', 'benchmark_finding', 'body', 'raw_html'])
def test_context_rejects_extra_fields(field):
    with pytest.raises(ValidationError):
        WebTargetContext(context_id='ctx', base_url='http://localhost', **{field: 'injected'})

@pytest.mark.parametrize('field,value', [('context_id', ''), ('context_id', ' '), ('base_url', ''), ('base_url', ' '), ('authentication_detected', 1), ('authentication_detected', 'true'), ('session_detected', 0), ('session_detected', 'false')])
def test_context_validation(field, value):
    data = dict(context_id='ctx', base_url='http://localhost')
    data[field] = value
    with pytest.raises(ValidationError):
        WebTargetContext(**data)

def test_mutable_defaults_isolated():
    first = WebTargetContext(context_id='ctx1', base_url='http://localhost')
    second = WebTargetContext(context_id='ctx2', base_url='http://localhost')
    for name in ('endpoints', 'forms', 'headers', 'cookies', 'content_types'):
        assert getattr(first, name) is not getattr(second, name)
    first.headers['X-Frame-Options'] = 'DENY'
    first.content_types.append('text/html')
    assert second.headers == {}
    assert second.content_types == []

def test_no_direct_network_import():
    tree = ast.parse(Path(observer.__file__).read_text(encoding='utf-8'))
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend((alias.name.split('.')[0] for alias in node.names))
        elif isinstance(node, ast.ImportFrom):
            modules.append((node.module or '').split('.')[0])
    assert not {'httpx', 'requests', 'socket'}.intersection(modules)
