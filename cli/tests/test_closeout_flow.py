"""消費 core/ruling.md 表、core/dispatch.md closeout、core/handoff.md、
core/verbs.md §1 brief／§2、core/platform.md P5、core/return.md；S12 驗收。
"""
import importlib.util
import json
from pathlib import Path
import re
import socket

import pytest

from wf.verbs import closeout
from wf.verbs.brief import brief, run
from .test_brief_sections import (RULES, SOURCE, TODAY, WRITES, block, card, make_client,
                                  make_root)

FIXTURE = Path(__file__).parent / 'fixtures/closeout/returns.json'


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('CLOSEOUT_NETWORK_DENIED')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(closeout, 'merge_tree', lambda *args, **kwargs: 0)
    with pytest.raises(AssertionError, match='CLOSEOUT_NETWORK_DENIED'):
        socket.socket().connect(('example.invalid', 443))


def comments():
    return json.loads(FIXTURE.read_text())


def client_for(current=None, **responses):
    return make_client(current or card(branch='topic', source_sha='c' * 40), **{
        'comments': comments(), 'pulls_for_branch': [{'number': 11}],
        'pull_request': {'merge_commit_sha': 'd' * 40, 'head': {'sha': 'c' * 40}},
        'is_ancestor': True,
        'ci_checks': {'check_runs': [{'name': 'unit', 'conclusion': 'success'}], 'statuses': []},
        **responses})


def render(tmp_path, client=None, *, listed=(), **flags):
    client = client or client_for()
    root = make_root(tmp_path, listed=listed)
    result = brief(10, target='closeout', client=client, root=root, today=TODAY,
                   emit=lambda line: None, **flags)
    assert result.rc == 0
    assert not any(name in WRITES for name, _ in client.calls), client.calls
    return list(result.printed), client, root


def message(lines):
    return lines[lines.index('```text') + 1]


def checker():
    spec = importlib.util.spec_from_file_location('trailer_check', RULES / '.github/scripts/trailer_check.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('listed', [(), ('escalation',), ('identity',), ('escalation', 'identity')])
def test_ruling_table_and_enabled_titles(tmp_path, listed):
    lines, _, root = render(tmp_path, listed=listed)
    table = [line.strip('|').split('|') for line in (root / 'core/ruling.md').read_text().splitlines()
             if line.startswith('| ')][1:]
    declared = json.loads(re.search(r'```json wf-module-sections\n(.*?)\n```',
                                    (root / 'core/dispatch.md').read_text(), re.S)[1])['closeout']
    expected = []
    for name, who, note in table:
        expected += ([title for module, titles in declared.items() if module in listed for title in titles]
                     if 'wf-module-sections.closeout' in note else [name.strip()])
    actual = [line[3:] for line in lines if line.startswith('## ')]
    assert actual == expected
    for index, line in enumerate(lines):
        if line.startswith('## '):
            assert SOURCE.fullmatch(lines[index + 1])
            if line[3:] not in expected[:2]:
                assert lines[index + 2] == '（人填）'
                assert lines[index + 3].startswith('## ') or lines[index + 3].startswith('缺 ')
    assert '交回單 JSON 樣板' not in lines
    print('RULING_HEADINGS', json.dumps(actual, ensure_ascii=False))


def test_timeline_and_latest_finding(tmp_path):
    lines, _, _ = render(tmp_path)
    timeline = '\n'.join(lines[:lines.index('## 現況')])
    assert timeline.index('exec-a') < timeline.index('review-a') < timeline.index('review-b')
    assert timeline.count('iteration：2') == 3
    assert 'role：executor' in timeline and timeline.count('role：reviewer') == 2
    assert 'review_result：REQUEST_CHANGES' in timeline and 'review_result：APPROVE' in timeline
    assert '請補驗；逐字理由' in timeline
    for data in comments():
        parsed = json.loads(data['body'].split('```json wf-return\n')[1].split('\n```')[0])
        for finding in parsed['findings']:
            assert json.dumps(finding, ensure_ascii=False) in timeline
    assert '首行不應讀取' not in '\n'.join(lines) and '散文不應讀取' not in '\n'.join(lines)
    assert any(line.startswith('open 且 blocking：不成立') for line in lines)


def test_squash_current_verdicts_and_literals(tmp_path):
    old = dict(comments()[0], author='previous-review', created_at='2026-08-01T00:00:00Z',
               body=block('wf-return', {'role': 'reviewer', 'iteration': 1, 'review_result': 'REQUEST_CHANGES'}))
    lines, _, _ = render(tmp_path, client_for(comments=[old, *comments()]),
                          requested_by='  A @session  ', planned_by='B', implemented_by='C',
                          reviewed_by=['D', 'E'])
    msg = message(lines)
    assert msg.splitlines()[0] == 'WF-001 功能'
    assert msg.split('\n\n')[1] == '被審 SHA：' + 'c' * 40 + '\nreview-a：REQUEST_CHANGES\nreview-b：APPROVE'
    assert 'previous-review' not in msg
    assert msg.split('\n\n')[-1] == ('Requested-by:   A @session  \nPlanned-by: B\nImplemented-by: C\n'
                                       'Reviewed-by: D\nReviewed-by: E')
    check = checker()
    bad = msg.replace('\nPlanned-by:', '\n\nPlanned-by:')
    errors = check.check('negative', bad)
    assert errors
    print('TRAILER_NEGATIVE rc=1', errors)
    errors = check.check('generated', msg)
    assert not errors
    assert {line.split(':', 1)[0].lower() for line in msg.split('\n\n')[-1].splitlines()} <= check.ALLOWED
    print('TRAILER_GENERATED rc=0', errors)


def test_missing_trailers_and_author_fallback(tmp_path):
    lines, _, _ = render(tmp_path, requested_by='A', implemented_by='C')
    assert '缺 Planned-by' in lines
    msg = message(lines)
    assert 'Planned-by:' not in msg
    assert msg.endswith('Reviewed-by: review-a\nReviewed-by: review-b')
    assert not checker().check('generated', msg)


def test_argparse_forwards_repeated_reviewers(tmp_path, capsys):
    root, client = make_root(tmp_path), client_for()
    assert run(['10', '--for', 'closeout', '--requested-by', 'A', '--planned-by', 'B',
                '--implemented-by', 'C', '--reviewed-by', 'D', '--reviewed-by', 'E'],
               client=client, root=root) == 0
    text = capsys.readouterr().out
    assert 'Requested-by: A\nPlanned-by: B\nImplemented-by: C\nReviewed-by: D\nReviewed-by: E\n```' in text
    assert not any(name in WRITES for name, _ in client.calls)


@pytest.mark.parametrize('target', ['executor', 'reviewer'])
def test_trailer_flags_do_not_change_dispatch(tmp_path, target, capsys, monkeypatch):
    monkeypatch.setattr('wf.verbs.brief.merge_tree', lambda *args, **kwargs: 0)
    root = make_root(tmp_path)
    for extra in ([], ['--requested-by', 'A', '--reviewed-by', 'B']):
        assert run(['10', '--for', target, *extra], client=client_for(), root=root) == 0
        output = capsys.readouterr().out
        if not extra:
            original = output
        else:
            assert output == original


def test_branch_conflict_uses_the_main_head_and_the_source_sha(tmp_path, monkeypatch):
    """S11b：分支衝突取源＝遠端 main 頭 vs 卡面 source_sha，與 brief 的 reviewer 段同一組。
    負控：分支頭另給第三個值，舊取源（main 頭 vs 分支頭）會讓下面的等式 FAIL。"""
    seen = []
    monkeypatch.setattr(closeout, 'merge_tree',
                        lambda base, head, **kwargs: seen.append((base, head)) or 1)
    heads = {'main': 'a' * 40, 'topic': 'b' * 40}
    client = client_for(branch_head=lambda branch: heads[branch])
    lines, _, _ = render(tmp_path, client)
    assert seen == [('a' * 40, 'c' * 40)]
    assert f"分支衝突：成立；證據：merge-tree {'a' * 40} {'c' * 40} rc=1" in lines
    assert ('branch_head', {'branch': 'topic'}) not in client.calls
    print('負控：舊取源會是', ('a' * 40, heads['topic']), '≠ 實際', seen[0])


def test_branch_conflict_without_a_source_sha_is_not_a_verdict(tmp_path, monkeypatch):
    """S11b：source_sha 未填 ⇒ 印未能取得，⛔ 不當成不成立、⛔ 不呼叫 merge-tree。"""
    seen = []
    monkeypatch.setattr(closeout, 'merge_tree', lambda *args, **kwargs: seen.append(args) or 0)
    lines, _, _ = render(tmp_path, client_for(card(branch='topic', source_sha=None)))
    assert seen == []
    assert '分支衝突：未能取得 merge-tree：來源 SHA 未填' in lines
    assert not any(line.startswith('分支衝突：不成立') for line in lines)
