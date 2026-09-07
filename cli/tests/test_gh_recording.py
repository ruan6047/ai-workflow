"""錄放工具；消費 docs/research/2026-09-07-step6-spec.md 第 6 步、core/card-schema.md §5。"""
import json
from pathlib import Path
import re
import shlex
import subprocess
from datetime import datetime, timezone
from types import SimpleNamespace

FIXTURES = Path(__file__).parent / 'fixtures' / 'gh'
REPO = 'ruan6047/ai-workflow'
SHA = 'f52df839b43e637cd6c399e4834bea76da4af029'
MERGE = '4bec8934646c51e6db05af782e28b85115a1e2ad'
HEAD = '05daecce60f04cb615a5bb55ee575184260df93f'


def projection_names():
    text = (Path(__file__).parents[2] / 'core/card-schema.md').read_text()
    section = text.split('## 5 · 投影欄')[1].split('## 6')[0]
    return re.findall(r'([^\s、：]+)←`[^`]+`', section)


def scenarios():
    return {
        'issue': ('issue', [228]),
        'issue_exists': ('issue_exists', [228]),
        'issue_open': ('issue_is_open', [228]),
        'comments': ('comments', [228]),
        'comment': ('comment', [None]),  # 由已錄製留言 id 取代。
        'commit': ('commit', [SHA]),
        'commit_exists': ('commit_exists', [SHA]),
        'branch': ('branch_head', ['main']),
        'pr': ('pull_request', [292]),
        'ci': ('ci_checks', [HEAD]),
        'ancestor': ('is_ancestor', [MERGE, 'main']),
        'merge_base': ('merge_base', [SHA, MERGE]),
        'project': ('project', ['ruan6047', 4, projection_names()]),
    }


def shape(value):
    if isinstance(value, dict):
        return {k: shape(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        variants = {json.dumps(shape(v), sort_keys=True) for v in value}
        return {'list': [json.loads(v) for v in sorted(variants)]}
    return type(value).__name__


class Replay:
    def __init__(self, fixture):
        self.fixture = fixture
        self.calls = []

    def __call__(self, args, **kwargs):
        entry = self.fixture['exchanges'][len(self.calls)]
        assert args == entry['request']
        assert kwargs == dict(capture_output=True, text=True, check=False, timeout=60)
        self.calls.append(args)
        return SimpleNamespace(**entry['response'])

    def assert_consumed(self):
        assert len(self.calls) == len(self.fixture['exchanges'])


def load(name):
    return json.loads((FIXTURES / f'{name}.json').read_text())


def record():
    from wf.gh.client import GhClient
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name, (method, args) in scenarios().items():
        if name == 'comment':
            args = [load('comments')['observed'][0]['id']]
        exchanges = []

        def recording_runner(argv, **kwargs):
            response = subprocess.run(argv, **kwargs)
            exchange = {
                'request': argv,
                'source_command': shlex.join(argv),
                'recorded_at': datetime.now(timezone.utc).isoformat(),
                'response': {k: getattr(response, k) for k in ('returncode', 'stdout', 'stderr')},
            }
            # 寫檔前檢查；拒絕整筆，不修改真實 API 回應。
            assert not re.search(r'token|authorization|gh[pousr]_[A-Za-z0-9]+|github_pat_', json.dumps(exchange), re.I), name
            exchanges.append(exchange)
            return response

        client = GhClient(REPO, runner=recording_runner, page_size=1 if name == 'comments' else 100)
        result = getattr(client, method)(*args)
        fixture = dict(provenance='真實 API 回應', method=method, args=args,
                       page_size=client.page_size, exchanges=exchanges,
                       observed=result, observed_shape=shape(result))
        replay = Replay(fixture)
        replay_result = getattr(GhClient(REPO, runner=replay, page_size=client.page_size), method)(*args)
        assert replay_result == result and shape(replay_result) == shape(result)
        replay.assert_consumed()
        serialized = json.dumps(fixture, ensure_ascii=False, indent=2) + '\n'
        assert not re.search('token|authorization', serialized, re.I), name
        (FIXTURES / f'{name}.json').write_text(serialized)
        print(json.dumps(dict(fixture=name, requests=len(exchanges), output_type=type(result).__name__,
                              live_equals_replay=True), ensure_ascii=False))


def verify_live():
    """正式預設 runner 實跑後，將同次回應交 fake 比對；不覆寫 fixture。"""
    from unittest.mock import patch
    from wf.gh.client import GhClient

    real_run = subprocess.run
    for name in scenarios():
        fixture = load(name)
        exchanges = []

        def live_runner(argv, **kwargs):
            response = real_run(argv, **kwargs)
            exchanges.append({'request': argv, 'response': {
                k: getattr(response, k) for k in ('returncode', 'stdout', 'stderr')
            }})
            return response

        with patch('wf.gh.client.subprocess.run', live_runner):
            client = GhClient(REPO, page_size=fixture['page_size'])
            assert client.runner is live_runner
            result = getattr(client, fixture['method'])(*fixture['args'])
        replay = Replay({'exchanges': exchanges})
        replay_result = getattr(GhClient(REPO, runner=replay, page_size=fixture['page_size']),
                                fixture['method'])(*fixture['args'])
        assert replay_result == result
        assert shape(replay_result) == shape(result)
        replay.assert_consumed()
        print(json.dumps(dict(operation=name, requests=len(exchanges), output_type=type(result).__name__,
                              default_runner=True, live_equals_replay=True, shape_equal=True)))


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['--record']:
        record()
    elif sys.argv[1:] == ['--verify-live']:
        verify_live()
    else:
        for path in sorted(FIXTURES.glob('*.json')):
            fixture = json.loads(path.read_text())
            print(path.name, fixture['method'])
            for exchange in fixture['exchanges']:
                print(exchange['recorded_at'], exchange['source_command'])
