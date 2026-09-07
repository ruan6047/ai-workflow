"""驗證 core/verbs.md §1–2、core/dispatch.md 基線、core/platform.md P1–P5 事實讀取。"""
import json
from types import SimpleNamespace

import pytest

from wf.gh.client import GhClient, GhError, NotFound, PermissionDenied, TransportError, NotLoggedIn
from .test_gh_recording import FIXTURES, REPO, Replay, load, shape, scenarios


@pytest.mark.parametrize('name', [
    'issue', 'issue_exists', 'issue_open', 'comments', 'comment', 'commit',
    'commit_exists', 'branch', 'pr', 'ci', 'ancestor', 'merge_base', 'project',
])
def test_real_recording_replays_same_output_and_types(name):
    fixture = load(name)
    runner = Replay(fixture)
    result = getattr(GhClient(REPO, runner=runner, page_size=fixture['page_size']), fixture['method'])(*fixture['args'])
    assert result == fixture['observed']
    assert shape(result) == fixture['observed_shape']
    assert fixture['provenance'] == '真實 API 回應'
    runner.assert_consumed()


def test_comments_pagination_complete_without_duplicates():
    fixture = load('comments')
    pages = [json.loads(e['response']['stdout']) for e in fixture['exchanges']]
    assert len([p for p in pages if p]) > 1
    expected = [c for page in pages for c in page]
    runner = Replay(fixture)
    actual = GhClient(REPO, runner=runner, page_size=fixture['page_size']).comments(228)
    assert len(actual) == len(expected) == len({c['id'] for c in actual})
    assert [c['body'] for c in actual] == [c['body'] for c in expected]
    assert all(set(c) == {'id', 'url', 'author', 'created_at', 'body'} for c in actual)
    runner.assert_consumed()


def test_project_pagination_and_raw_projection_values():
    fixture = load('project')
    pages = [json.loads(e['response']['stdout'])['data']['node']['items']['nodes']
             for e in fixture['exchanges'] if 'items(first:' in ' '.join(e['request'])]
    assert len(pages) > 1
    raw = [item for page in pages for item in page]
    runner = Replay(fixture)
    actual = GhClient(REPO, runner=runner, page_size=fixture['page_size']).project(*fixture['args'])
    assert len(actual['items']) == len(raw) == len({item['id'] for item in actual['items']})
    for item, source in zip(actual['items'], raw, strict=True):
        assert item['fieldValues'] == {name: source[f'f{i}'] for i, name in enumerate(fixture['args'][2])}
    assert any((item['content'] or {}).get('repository', {}).get('nameWithOwner') == REPO
               for item in actual['items'])
    runner.assert_consumed()


def test_fixture_inventory_covers_public_read_operations():
    expected = {name for name, value in vars(GhClient).items()
                if not name.startswith('_') and callable(value)}
    fixtures = [load(name) for name in scenarios()]
    assert {f['method'] for f in fixtures} == expected


def test_default_runner_and_injected_runner_use_identical_requests(monkeypatch):
    fixture = load('issue')
    default = Replay(fixture)
    monkeypatch.setattr('wf.gh.client.subprocess.run', default)
    client = GhClient(REPO)
    assert client.runner is default
    injected = Replay(fixture)
    assert client.issue(*fixture['args']) == GhClient(REPO, runner=injected).issue(*fixture['args'])
    assert default.calls == injected.calls
    default.assert_consumed()
    injected.assert_consumed()


@pytest.mark.parametrize(('rc', 'stdout', 'stderr', 'error'), [
    (1, '{"message":"Not Found"}', 'gh: Not Found (HTTP 404)', NotFound),
    (1, '', 'gh: Forbidden (HTTP 403)', PermissionDenied),
    (1, '', 'gh: Bad credentials (HTTP 401)', PermissionDenied),
    (1, '', 'gh: Too Many Requests (HTTP 429)', TransportError),
    (1, '', 'gh: Internal Server Error (HTTP 500)', TransportError),
    (1, '', 'dial tcp: network unreachable', TransportError),
    (1, '', 'gh: API rate limit exceeded (HTTP 403)', TransportError),
    (4, '', 'To get started with GitHub CLI, please run: gh auth login', NotLoggedIn),
    (0, '{"errors":[{"type":"FORBIDDEN","message":"denied"}]}', '', PermissionDenied),
    (0, '{"errors":[{"type":"NOT_FOUND","message":"missing"}]}', '', NotFound),
    (0, '{"errors":[{"type":"RATE_LIMITED","message":"limited"}]}', '', TransportError),
    (1, '', 'gh: Validation Failed (HTTP 422)', GhError),
])
def test_hand_constructed_errors_are_separate(rc, stdout, stderr, error):
    """手構錯誤回應，非真實錄製。"""
    runner = lambda *a, **kw: SimpleNamespace(returncode=rc, stdout=stdout, stderr=stderr)
    with pytest.raises(error) as caught:
        GhClient(REPO, runner=runner).issue(228)
    assert type(caught.value) is error


@pytest.mark.parametrize('method,args', [('issue_exists', [228]), ('commit_exists', ['abc'])])
@pytest.mark.parametrize('status', [401, 403, 429, 503])
def test_unfinished_never_becomes_absent(method, args, status):
    """手構：存在性查詢不能吞掉非 404。"""
    runner = lambda *a, **kw: SimpleNamespace(returncode=1, stdout='', stderr=f'gh: error (HTTP {status})')
    with pytest.raises((PermissionDenied, TransportError)):
        getattr(GhClient(REPO, runner=runner), method)(*args)


def test_fake_negative_control_rejects_wrong_request():
    fixture = load('issue')
    with pytest.raises(AssertionError):
        GhClient(REPO, runner=Replay(fixture)).issue(999)


def test_fixtures_have_no_sensitive_words():
    import re
    pattern = re.compile('token|authorization', re.I)
    assert pattern.search('Authorization: sentinel')
    assert pattern.search('token sentinel')
    paths = sorted(FIXTURES.glob('*.json'))
    assert paths
    for path in paths:
        assert not pattern.search(path.read_text()), path
