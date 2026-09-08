"""消費 core/ruling.md 表、core/dispatch.md closeout、core/handoff.md、
core/verbs.md §1 brief／§2、core/platform.md P5、core/return.md；S12 驗收。

S19 現況更新（取代 S12／S13 證據包裡已過期的兩句）：closeout 的分支衝突「成立」與
「merge-tree 工具失敗」不再只有臨時探針，已落在本檔（見下方五個異常情境）；
終態的「封存」依 core/glossary.md §「封存、撤銷、停止」＝關 issue（Project item 不移出、
不 isArchived），不是未實作的缺口——關 issue 的正例在 test_move_core.py 與 test_end_to_end.py。
"""
import importlib.util
import json
from pathlib import Path
import re
import socket

import pytest

from wf.gh.client import GhError
from wf.gh.localgit import LocalGitUnavailable
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


def render(tmp_path, client=None, *, listed=(), name='root', **flags):
    """`name` 讓同一個 tmp_path 能建第二份 root（正負控同題並列時用）。"""
    client = client or client_for()
    root = make_root(tmp_path, listed=listed, name=name)
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


# ── S19 射程 2：closeout 五種異常情境落成回歸案例（各案 rc=0、輸出逐字、零遠端寫入）──
# `render()` 已經替每一案斷言 rc=0 與 client.calls 不含任何寫入方法（WRITES）。

MERGE_TREE_UNKNOWN = '分支衝突：未能取得 merge-tree：'


def boom(exc):
    def raise_it(*args, **kwargs):
        raise exc
    return raise_it


def assert_merge_tree_unknown(lines, reason):
    """未知不冒充事實：只准印「未能取得」，⛔ 不准印成衝突成立或不成立。"""
    assert MERGE_TREE_UNKNOWN + reason in lines
    assert not [line for line in lines if line.startswith('分支衝突：成立')
                or line.startswith('分支衝突：不成立')], lines


def test_ci_not_green_is_stated_with_its_evidence(tmp_path):
    """異常一：CI 非綠。正控＝同一組替身只把 conclusion 換成 success ⇒ 不成立。"""
    red = client_for(ci_checks={'check_runs': [{'name': 'unit', 'conclusion': 'failure'}],
                                'statuses': [{'state': 'success'}]})
    lines, client, _ = render(tmp_path, red)
    assert f"PR #11 merge SHA：{'d' * 40}" in lines
    assert 'CI 非綠：成立；證據：上述 CI 狀態' in lines
    assert '"conclusion": "failure"' in '\n'.join(lines)
    assert ('ci_checks', {'sha': 'd' * 40}) in client.calls
    green, _, _ = render(tmp_path, client_for(), name='control')
    assert 'CI 非綠：不成立；證據：上述 CI 狀態' in green
    print('CI 非綠正負控：', [line for line in lines + green if line.startswith('CI 非綠')])


def test_branch_conflict_holds_when_merge_tree_returns_one(tmp_path, monkeypatch):
    """異常二：分支衝突成立（merge-tree rc=1）；正控＝rc=0 ⇒ 不成立。"""
    monkeypatch.setattr(closeout, 'merge_tree', lambda base, head, **kwargs: 1)
    lines, _, _ = render(tmp_path)
    assert f"分支衝突：成立；證據：merge-tree {'a' * 40} {'c' * 40} rc=1" in lines
    monkeypatch.setattr(closeout, 'merge_tree', lambda base, head, **kwargs: 0)
    clean, _, _ = render(tmp_path, name='control')
    assert f"分支衝突：不成立；證據：merge-tree {'a' * 40} {'c' * 40} rc=0" in clean


@pytest.mark.parametrize('source, exc, reason', [
    ('merge_tree', LocalGitUnavailable('GIT_TOOL_DOWN'), 'GIT_TOOL_DOWN'),
    ('branch_head', GhError('MAIN_HEAD_UNAVAILABLE'), 'MAIN_HEAD_UNAVAILABLE')])
def test_merge_tree_failure_prints_unknown_not_a_verdict(tmp_path, monkeypatch, source, exc, reason):
    """異常三：merge-tree 工具失敗／取不到 main 頭 ⇒ 印「未能取得」，⛔ 不印成衝突或無衝突。"""
    client = client_for()
    if source == 'merge_tree':
        monkeypatch.setattr(closeout, 'merge_tree', boom(exc))
    else:
        client.responses['branch_head'] = boom(exc)
    lines, _, _ = render(tmp_path, client)
    assert_merge_tree_unknown(lines, reason)
    print('工具失敗：', [line for line in lines if line.startswith('分支衝突')])


def test_open_blocking_finding_holds(tmp_path):
    """異常四：只有 status=open 且 blocking=true 的 finding ⇒ 成立並附該 finding 逐字。
    正控＝加回後續把它改 resolved 的裁定單 ⇒ 不成立（既有 fixture）。"""
    only_open = [row for row in comments() if row['author'] != 'review-b']
    lines, _, _ = render(tmp_path, client_for(comments=only_open))
    assert 'open 且 blocking：成立；證據：依留言時間序取各 finding_id 最後狀態' in lines
    assert any('F-reviewer-01' in line and '"status": "open"' in line for line in lines)
    resolved, _, _ = render(tmp_path, name='control')
    assert 'open 且 blocking：不成立；證據：依留言時間序取各 finding_id 最後狀態' in resolved
    print('open+blocking 正負控：', [line for line in lines + resolved
                                    if line.startswith('open 且 blocking')])


def test_no_pull_request_skips_merge_sha_ancestor_and_ci(tmp_path):
    """異常五：無 PR ⇒ 三行逐字、⛔ 不呼叫 pull_request／ci_checks、⛔ 不印 CI 不成立。"""
    lines, client, _ = render(tmp_path, client_for(pulls_for_branch=[]))
    assert ['無 PR', '未能取得 merge SHA；main 祖先與 CI 略過',
            'CI 非綠：未能取得 CI（無 PR）'] == [line for line in lines if line.startswith(
                ('無 PR', '未能取得 merge SHA', 'CI 非綠'))]
    assert [name for name, _ in client.calls if name in ('pull_request', 'ci_checks')] == []
    assert ('pulls_for_branch', {'branch': 'topic'}) in client.calls


def sloppy_current():
    """驗收 6 的負控素材：在**記憶體**裡把 closeout 的「未知不冒充事實」那段改成印
    「不成立」（＝無衝突），⛔ 不動 cli/src 任何一行；回傳改過的 _current 與其命名空間。"""
    source = (RULES / 'cli/src/wf/verbs/closeout.py').read_text(encoding='utf-8')
    needle = "        lines.append(f'分支衝突：未能取得 merge-tree：{exc}')"
    assert needle in source, '負控錨點消失：closeout.py 的未知分支已改寫，負控要重寫'
    namespace = {'__name__': 'closeout_sloppy'}
    exec(compile(source.replace(needle, "        lines.append('分支衝突：不成立；證據：無衝突')"),
                 'closeout_sloppy', 'exec'), namespace)
    return namespace


def test_negative_control_unknown_merge_tree_pretending_no_conflict(tmp_path, monkeypatch):
    """驗收 6 的負控：把未知那段改成印「無衝突」⇒ 上面的工具失敗案必 FAIL。"""
    namespace = sloppy_current()
    namespace['merge_tree'] = boom(LocalGitUnavailable('GIT_TOOL_DOWN'))
    monkeypatch.setattr(closeout, 'merge_tree', boom(LocalGitUnavailable('GIT_TOOL_DOWN')))
    monkeypatch.setattr(closeout, '_current', namespace['_current'])
    lines, _, _ = render(tmp_path)
    with pytest.raises(AssertionError):
        assert_merge_tree_unknown(lines, 'GIT_TOOL_DOWN')
    assert '分支衝突：不成立；證據：無衝突' in lines
    assert not any(line.startswith(MERGE_TREE_UNKNOWN) for line in lines)
    print('負控：未知改印無衝突 ⇒', [line for line in lines if line.startswith('分支衝突')])
