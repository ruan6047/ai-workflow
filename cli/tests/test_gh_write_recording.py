"""真實 gh API 錄放；core/verbs.md §2；只允許 #295 body／留言副作用。"""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
from types import SimpleNamespace

import pytest

from wf.gh.client import GhClient
from wf.gh.writes import card_span, read_card
from wf.verbs._write import reject
from .test_gh_recording import REPO, shape

FIXTURES = Path(__file__).parent / 'fixtures' / 's05'
SECRET = re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|(?:Authorization\s*:\s*(?:Bearer|token)\s+)\S+', re.I)
READ_CASES = ('issues', 'pulls_for_branch', 'comment_urls')


def ensure_clean(value):
    serialized = json.dumps(value, ensure_ascii=False)
    if SECRET.search(serialized):
        raise ValueError('fixture 含憑證，拒絕錄製')
    for key in ('GH_TOKEN', 'GITHUB_TOKEN', 'GH_ENTERPRISE_TOKEN', 'GITHUB_ENTERPRISE_TOKEN'):
        secret = os.environ.get(key)
        if secret and secret in serialized:
            raise ValueError('fixture 含環境憑證，拒絕錄製')


class Recorder:
    def __init__(self):
        self.exchanges = []

    def __call__(self, argv, **kwargs):
        assert argv[:2] == ['gh', 'api']
        method = argv[argv.index('--method') + 1]
        endpoint = argv[2]
        if method != 'GET':
            assert (method, endpoint) in (
                ('PATCH', f'repos/{REPO}/issues/295'),
                ('POST', f'repos/{REPO}/issues/295/comments'))
            payload = json.loads(kwargs['input'])
            assert set(payload) == {'body'}
        result = subprocess.run(argv, **kwargs)
        exchange = {'request': argv, 'kwargs': kwargs, 'source_command': shlex.join(argv),
                    'recorded_at': datetime.now(timezone.utc).isoformat(),
                    'response': {k: getattr(result, k) for k in ('returncode', 'stdout', 'stderr')}}
        ensure_clean(exchange)
        self.exchanges.append(exchange)
        return result


class WriteReplay:
    def __init__(self, fixture):
        self.exchanges = fixture['exchanges']
        self.index = 0

    def __call__(self, argv, **kwargs):
        exchange = self.exchanges[self.index]
        assert argv == exchange['request']
        assert kwargs == exchange['kwargs']
        self.index += 1
        return SimpleNamespace(**exchange['response'])

    def assert_consumed(self):
        assert self.index == len(self.exchanges)


def hash_body(body):
    return sha256(body.encode('utf-8')).hexdigest()


def same_prose(before, after):
    a, b = card_span(before)
    c, d = card_span(after)
    assert before[:a].encode() == after[:c].encode()
    assert before[b:].encode() == after[d:].encode()


def exercise(client, case, args):
    if case == 'write_restore':
        before = client.issue(295)['body']
        try:
            original = read_card(before)
            updated = original | {'note': 'S05 真實錄放：僅替換此區塊'}
            client.update_card_body(295, updated)
            after = client.issue(295)['body']
            same_prose(before, after)
            assert read_card(after) == updated
            comment = client.post_comment(295, 'wf:edit', 'S05 錄放測試：只換 wf-card 區塊；原 body 將恢復。')
            rejection = reject(client, 295, 'D3', 'S05 錄放測試：回讀不等').rejection
        finally:
            # 恢復原 body 字面；不透過重新序列化 JSON，以免格式改變。
            client._request(f'repos/{REPO}/issues/295', method='PATCH', payload={'body': before})
            restored = client.issue(295)['body']
            assert restored.encode() == before.encode()
        return {'before_hash': hash_body(before), 'after_hash': hash_body(restored),
                'changed_body': after, 'original_body': before, 'restored_body': restored,
                'comment_urls': [comment['html_url'], rejection['html_url']]}
    if case == 'comment_urls':
        result = []
        for url in args:
            by_url = client.comment_from_url(url)
            by_id = client.comment(int(url.rsplit('-', 1)[1]))
            assert by_url == by_id
            result.append(by_url)
        return result
    return getattr(client, case)(*args)


def load_case(case):
    return json.loads((FIXTURES / (case + '.json')).read_text())


def record():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    # 唯讀取得本 repo 已存在的留言；不額外貼湊數留言。
    existing = GhClient(REPO)._rest('issues/comments?per_page=3')
    urls = [row['html_url'] for row in existing]
    assert len(urls) == 3
    for case, args in [('write_restore', []), ('issues', []),
                       ('pulls_for_branch', ['claude/wf-step6-cli']), ('comment_urls', urls)]:
        recorder = Recorder()
        observed = exercise(GhClient(REPO, runner=recorder), case, args)
        fixture = {'provenance': '真實 API 回應', 'method': case, 'args': args,
                   'exchanges': recorder.exchanges, 'observed': observed, 'observed_shape': shape(observed)}
        ensure_clean(fixture)
        replay = WriteReplay(fixture)
        assert exercise(GhClient(REPO, runner=replay), case, args) == observed
        replay.assert_consumed()
        (FIXTURES / (case + '.json')).write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'case': case, 'requests': len(recorder.exchanges), 'live_equals_replay': True,
                          **({k: observed[k] for k in ('before_hash', 'after_hash', 'comment_urls')}
                             if case == 'write_restore' else {})}, ensure_ascii=False))


@pytest.mark.parametrize('case', ['write_restore', *READ_CASES])
def test_s05_real_recording_replay(case):
    fixture = load_case(case)
    replay = WriteReplay(fixture)
    actual = exercise(GhClient(REPO, runner=replay), case, fixture['args'])
    assert actual == fixture['observed']
    assert shape(actual) == fixture['observed_shape']
    assert fixture['provenance'] == '真實 API 回應'
    replay.assert_consumed()


def test_recorded_prose_and_restore_hash():
    data = load_case('write_restore')['observed']
    same_prose(data['original_body'], data['changed_body'])
    assert data['before_hash'] == data['after_hash'] == hash_body(data['restored_body'])
    assert len(data['comment_urls']) == 2
    print(json.dumps({k: data[k] for k in ('before_hash', 'after_hash', 'comment_urls')}))


def test_recorded_read_inventories():
    fixture = load_case('issues')
    raw = [row for exchange in fixture['exchanges'] for row in json.loads(exchange['response']['stdout'])]
    assert any('pull_request' in row for row in raw)
    assert fixture['observed'] == [row for row in raw if 'pull_request' not in row]
    assert any(row['number'] == 293 for row in load_case('pulls_for_branch')['observed'])
    urls = load_case('comment_urls')
    assert len(urls['args']) == len(urls['observed']) == 3
    print('RECORDED_ISSUES', len(raw), 'ISSUES', len(fixture['observed']))
    print('COMMENT_URLS', urls['args'])


def test_recordings_secret_negative_control():
    with pytest.raises(ValueError, match='憑證'):
        ensure_clean({'body': 'ghp_' + 'X' * 36})
    with pytest.raises(ValueError, match='憑證'):
        ensure_clean({'header': 'Authorization: Bearer sentinel'})
    paths = sorted(FIXTURES.glob('*.json'))
    assert paths
    for path in paths:
        ensure_clean(json.loads(path.read_text()))
    print('SECRET_NEGATIVE_CONTROL rejected; FILES', len(paths))


@pytest.mark.skipif(os.environ.get('WF_LIVE') != '1', reason='需明確啟用線上唯讀驗證')
def test_live_readonly_and_existing_s02_suite():
    from .test_gh_recording import verify_live
    verify_live()
    for case in READ_CASES:
        fixture = load_case(case)
        recorder = Recorder()
        actual = exercise(GhClient(REPO, runner=recorder), case, fixture['args'])
        replay = WriteReplay({'exchanges': recorder.exchanges})
        assert exercise(GhClient(REPO, runner=replay), case, fixture['args']) == actual
        replay.assert_consumed()
    expected = load_case('write_restore')['observed']['before_hash']
    assert hash_body(GhClient(REPO).issue(295)['body']) == expected
    print('LIVE_RESTORED_BODY_HASH', expected)


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['--record']:
        record()
