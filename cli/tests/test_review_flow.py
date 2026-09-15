"""消費 core/verbs.md §1 review／§2／§3、core/return.md、core/naming.md §3／§4。
手構 fake 接住 GitHub；不錄真實 API、不改共用測試或唯讀介面。
"""
import json
from pathlib import Path
import re
import socket
import subprocess

import pytest

from wf.compose.blocks import load_blocks
from wf.compose.schema import compose_schema
from wf.gh.client import NotFound
from wf.gh.writes import read_block
from wf.verbs.notes import notes
from wf.verbs.review import NO_APPENDIX, NO_LOCAL_HEAD, review, run
from .test_brief_sections import (CANDIDATE, PERTURBATIONS, WRITES, assert_prose_goes_blind,
                                  block, card, formal_card, make_client, make_root,
                                  perturb)  # noqa: F401（perturb 是 fixture，靠名字注入）

ALLOWED_GIT = {'rev-parse', 'log', 'diff'}  # review 的本機唯讀取源；⛔ 不含任何寫入型子指令


def git_subcommand(argv):
    """`git [全域旗標…] <子指令>` 的子指令；`-C` 另吃一個值。不是 git ⇒ None。"""
    if not argv or Path(argv[0]).name != 'git':
        return None
    rest = list(argv[1:])
    while rest:
        token = rest.pop(0)
        if token == '-C' and rest:
            rest.pop(0)
        elif not token.startswith('-'):
            return token
    return None


def strict_offline(monkeypatch, token):
    """嚴格放行（需求方 2026-09-14 裁定）：只有本機 git 的 rev-parse／log／diff 可跑——
    `review` 的本機分支頭比對與 git 附錄走 gh/localrev.py 這三個唯讀子指令（CLI-001）。
    字串型 shell command、gh／curl／wget／ssh、其他 git 子指令與任何其他子程序一律擋；
    socket 連線一律擋（roles/conduct-common.md §1）。"""
    real = subprocess.run

    def denied(*args, **kwargs):
        raise AssertionError(token)

    def guarded(argv, *args, **kwargs):
        if isinstance(argv, (str, bytes)) or git_subcommand([str(item) for item in argv]) not in ALLOWED_GIT:
            denied()
        return real(argv, *args, **kwargs)

    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(subprocess, 'run', guarded)




@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    strict_offline(monkeypatch, 'REVIEW_NETWORK_DENIED')
    with pytest.raises(AssertionError, match='REVIEW_NETWORK_DENIED'):
        subprocess.run(['gh', 'api', 'negative-control'])
    with pytest.raises(AssertionError, match='REVIEW_NETWORK_DENIED'):
        subprocess.run('git rev-parse HEAD')          # 字串型 shell command
    with pytest.raises(AssertionError, match='REVIEW_NETWORK_DENIED'):
        subprocess.run(['git', 'push', 'origin'])     # 寫入型 git 子指令
    with pytest.raises(AssertionError, match='REVIEW_NETWORK_DENIED'):
        subprocess.run(['python', '-c', 'pass'])      # 其他子程序


def invoke(tmp_path, *, data=None, changes=None, role='executor', listed=(), comments=(),
           head='a' * 40, root=None, client=None):
    root = root or make_root(tmp_path, listed=listed, project=False)
    current = card(**({'branch': 'wf/WF-001', 'source_sha': 'b' * 40} | (changes or {})))
    client = client or make_client(current, comments=comments, branch_head=head)
    path = tmp_path / 'return.json'
    path.write_text(json.dumps({} if data is None else data, ensure_ascii=False), encoding='utf-8')
    lines = []
    result = review(10, file=path, role=role, client=client, root=root, emit=lines.append)
    assert result.printed == tuple(lines)
    writes = [(name, args) for name, args in client.calls if name in WRITES]
    assert [name for name, _ in writes] == ['post_comment'], writes
    posted = writes[0][1]
    return result, lines, posted, client


def promote(root, name):
    """把 tmp root 內某模組的 maturity 改成 ready。

    core/modules.md §3：module_return_sections 只由 capable 貢獻 ⇒ 要測段標籤與 marker 語意，
    被測模組必須是 ready。⛔ 不動 repo 內的規則，只改這份複本；非 ready 的零貢獻另有測試釘。
    """
    path = root / f'modules/{name}/module.md'
    text = path.read_text(encoding='utf-8')
    assert '"maturity": "ready"' not in text, name
    path.write_text(re.sub(r'"maturity": "[a-z]+"', '"maturity": "ready"', text, count=1),
                    encoding='utf-8')
    return root


def finding(**changes):
    return dict(finding_id='WF-001-R2.1-01', severity='major', blocking=True, status='open',
                finding_class='implementation', attribution='executor', root_cause_id='test',
                evidence='證據', disposition='補修') | changes


@pytest.mark.parametrize('data', [
    {'self_run': [{'command': 'pytest', 'rc': 0}]},
    {'self_run': '錯誤型別'},
    {'unknown': True},
])
def test_d3_schema_cases(tmp_path, data):
    result, _, posted, _ = invoke(tmp_path, data=data)
    assert result.rc != 0 and posted['first_line'] == 'wf:reject'
    assert posted['body'].startswith('拒收・D3・')
    print('D3_NEGATIVE_CONTROL', data, posted['body'])


@pytest.mark.parametrize('raw', ['{broken', 'null', '[]'])
def test_d3_invalid_json_or_top_level(tmp_path, raw):
    root = make_root(tmp_path, project=False)
    path = tmp_path / 'return.json'
    path.write_text(raw)
    client = make_client(card())
    result = review(10, file=path, role='executor', client=client, root=root, emit=lambda _: None)
    assert result.rc != 0
    writes = [(name, args) for name, args in client.calls if name in WRITES]
    assert len(writes) == 1 and writes[0][1]['first_line'] == 'wf:reject'


def missing_branch(branch):
    if branch == 'main':
        return 'c' * 40
    raise NotFound('遠端分支不存在')


@pytest.mark.parametrize('stage', ['執行', '審核', '部署', '維護', '結案', '規劃', '研究', '需求'])
@pytest.mark.parametrize('case', ['null', 'missing', 'malformed', 'zero'])
def test_d4_stage_and_main_fallback(tmp_path, stage, case):
    current = card(stage=stage, branch=None if case == 'null' else 'wf/WF-001')
    head = missing_branch if case == 'missing' else lambda branch: (
        'c' * 40 if branch == 'main' else 'short' if case == 'malformed' else '0' * 40)
    client = make_client(current, branch_head=head)
    result, _, posted, client = invoke(tmp_path, client=client)
    if stage in ('需求', '研究', '規劃'):
        assert result.rc == 0 and posted['first_line'] == 'wf:return'
        assert read_block(posted['body'], 'wf-return')['source_sha'] == 'c' * 40
        assert ('branch_head', {'branch': 'main'}) in client.calls
    else:
        assert result.rc != 0 and posted['body'].startswith('拒收・D4・')
        assert ('branch_head', {'branch': 'main'}) not in client.calls
    print('D4_PROBE', stage, case, 'rc', result.rc, posted['first_line'])


@pytest.mark.parametrize('role,expected', [('executor', 'a' * 40), ('reviewer', 'b' * 40)])
def test_sources_and_identity_are_overwritten(tmp_path, role, expected):
    data = {'card_id': 'fake', 'iteration': 'fake', 'role': 'fake', 'source_sha': 'fake'}
    result, lines, posted, client = invoke(tmp_path, data=data, role=role)
    assert result.rc == 0
    returned = read_block(posted['body'], 'wf-return')
    assert returned == dict(card_id='WF-001', iteration=2, role=role, source_sha=expected)
    assert posted['first_line'] == ('wf:return' if role == 'executor' else 'wf:verdict')
    if role == 'executor':  # tmp root 不是 git 工作樹＝本機狀態取不到（CLI-001 驗收 1(c)）
        assert NO_LOCAL_HEAD in lines
    else:  # reviewer 只讀遠端預設分支頭當 git 附錄的 base，⛔ 不讀卡面分支的遠端頭
        assert [args['branch'] for name, args in client.calls if name == 'branch_head'] == ['main']
    appendix = [line for line in lines if line.startswith(NO_APPENDIX)]
    assert len(appendix) == 1 and appendix[0].partition('：')[2].strip()
    assert posted['body'].count('```json wf-return\n') == 1
    assert posted['body'].endswith('\n```\n\n' + appendix[0] + '\n')


def test_reviewer_null_sha_is_d3(tmp_path):
    client = make_client(card(source_sha=None))
    result, _, posted, _ = invoke(tmp_path, role='reviewer', client=client)
    assert result.rc != 0 and posted['body'].startswith('拒收・D3・')


@pytest.mark.parametrize('tier', ['T0', 'T1', 'T2', 'T3', 'T4'])
@pytest.mark.parametrize('role', ['executor', 'reviewer'])
def test_missing_sections_follow_tier_and_role(tmp_path, tier, role):
    result, lines, _, _ = invoke(tmp_path, changes={'tier': tier}, role=role)
    expected = {'self_run', 'acceptance'}
    if tier in ('T2', 'T3', 'T4'):
        expected |= {'unverified', 'note_responses', 'out_of_scope'}
        expected |= {'mistakes'} if role == 'executor' else {'review_result', 'core_pain_resolved', 'findings'}
    assert result.rc == 0
    assert {line.removeprefix('缺段：') for line in lines if line.startswith('缺段：')} == expected


def test_enabled_module_schema_and_labels(tmp_path):
    root = promote(make_root(tmp_path, listed=['stat-redline'], project=False), 'stat-redline')
    schema = compose_schema(load_blocks(root), 'wf-return', ['stat-redline'])
    sections = schema['$defs']['module_return_sections']['stat-redline']
    changes = {'tier': 'T1', 'tier_basis': {'sensitive': ['statistics'], 'recoverable': 'reversible', 'blast': 'file'}}
    result, lines, _, _ = invoke(tmp_path, root=root, changes=changes)
    assert result.rc == 0
    for spec in sections.values():
        assert '缺段：' + spec['label'] in lines
    data = {'redlines': [], 'adversarial_tests': [{'angle': '甲', 'result': '不適用', 'text': ''}]}
    result, lines, _, _ = invoke(tmp_path, root=root, data=data, changes=changes)
    assert result.rc == 0 and 'adversarial_tests[0]：text 空' in lines
    result, _, posted, _ = invoke(tmp_path, root=root, data={'redlines': 4}, changes=changes)
    assert result.rc != 0 and posted['body'].startswith('拒收・D3・')


def test_module_fields_not_enabled_are_unknown(tmp_path):
    result, _, posted, _ = invoke(tmp_path, data={'redlines': []})
    assert result.rc != 0 and posted['body'].startswith('拒收・D3・')


def test_non_ready_module_contributes_no_return_sections(tmp_path):
    """core/modules.md §3：module_return_sections 是自動能力七項之一 ⇒ 非 ready 的模組即使
    enable_if 成立也零貢獻。負控＝同一張卡在 promote 後段標籤就出現（上面那條）。"""
    root = make_root(tmp_path, listed=['stat-redline'], project=False)
    changes = {'tier': 'T1', 'tier_basis': {'sensitive': ['statistics'], 'recoverable': 'reversible', 'blast': 'file'}}
    labels = [spec['label'] for spec in compose_schema(
        load_blocks(root), 'wf-return', ['stat-redline'])['$defs']['module_return_sections']['stat-redline'].values()]
    assert labels, '段標籤仍住 core/return.md，宣告未 ready ⛔ 不代表標籤消失'
    result, lines, _, _ = invoke(tmp_path, root=root, changes=changes)
    assert result.rc == 0
    assert not [line for line in lines if any(label in line for label in labels)], lines
    result, _, posted, _ = invoke(tmp_path, root=root, data={'redlines': []}, changes=changes)
    assert result.rc != 0 and posted['body'].startswith('拒收・D3・')  # 欄位仍是未知鍵
    print('NON_READY_NO_RETURN_SECTIONS stat-redline', labels)


def test_notes_uses_formal_list_and_excludes_candidates(tmp_path):
    root = make_root(tmp_path, project=False)
    current = card(branch='wf/WF-001', notes=[{'id': 'T-執行-01', 'text': '逐字', 'origin': 'url'}])
    comments = [{'url': 'candidate', 'body': block('wf-note',
                 {'text': '1. F-候選-01：假清單', 'origin': 'url'})}]
    formal = notes(10, client=make_client(current, comments=comments), root=root, emit=lambda _: None)
    ids = [line.split('. ', 1)[1].split('：', 1)[0] for line in formal.printed if line[:1].isdigit()]
    assert 'T-執行-01' in ids
    data = {'note_responses': [{'id': note, 'value': 'followed'} for note in ids if note != 'T-執行-01']}
    result, lines, _, _ = invoke(tmp_path, root=root, data=data,
                                client=make_client(current, comments=comments))
    assert result.rc == 0
    assert [line for line in lines if line.startswith('note_responses 未覆蓋：')] == [
        'note_responses 未覆蓋：T-執行-01']
    data['note_responses'].append({'id': 'T-執行-01', 'value': 'followed'})
    _, covered, _, _ = invoke(tmp_path, root=root, data=data, client=make_client(current, comments=comments))
    assert not [line for line in covered if line.startswith('note_responses 未覆蓋：')]
    print('NOTE_NEGATIVE_CONTROL missing T-執行-01; covered removes hint; candidate excluded')


@pytest.mark.parametrize('value', ['not_applicable', 'found', 'followed'])
@pytest.mark.parametrize('text', ['', '   ', '逐字證據'])
def test_empty_text_and_reason_are_only_printed(tmp_path, value, text):
    data = {'note_responses': [{'id': 'T-執行-01', 'value': value, 'text': text}],
            'unverified': [{'item': '量測', 'kind': 'cannot', 'reason': text}]}
    result, lines, posted, _ = invoke(tmp_path, data=data)
    assert result.rc == 0 and posted['first_line'] == 'wf:return'
    assert ('note_responses[0]：text 空' in lines) == (value != 'followed' and not text.strip())
    assert ('unverified[0].reason 空' in lines) == (not text.strip())


def test_existing_findings_collide_without_renumbering(tmp_path):
    old = finding()
    comments = [{'body': '代貼裁決\n' + block('wf-return', {'findings': [old]})},
                {'body': block('wf-ruling', {'findings': [finding(finding_id='other')]})}]
    data = {'findings': [old, finding(finding_id='other')], 'review_result': 'APPROVE'}
    result, lines, posted, _ = invoke(tmp_path, data=data, comments=comments, role='reviewer')
    assert result.rc == 0
    assert [line for line in lines if line.startswith('finding_id 撞號：')] == [
        'finding_id 撞號：' + old['finding_id']]
    assert read_block(posted['body'], 'wf-return')['findings'] == data['findings']
    comparison = next(line for line in lines if line.startswith('交回單欄位一致性'))
    assert json.loads(comparison.split('：', 1)[1]) == data


def test_once_returned_workflow_keeps_original_finding_id(tmp_path):
    root = make_root(tmp_path, project=False)
    first = {'findings': [finding()], 'review_result': 'REQUEST_CHANGES'}
    _, _, rejected, _ = invoke(tmp_path, root=root, data=first, role='reviewer')
    changes = {'findings': [finding(status='resolved')], 'review_result': 'APPROVE'}
    result, lines, accepted, _ = invoke(tmp_path, root=root, data=changes, role='reviewer',
                                       changes={'iteration': 3}, comments=[{'body': rejected['body']}])
    returned = read_block(accepted['body'], 'wf-return')
    assert result.rc == 0 and returned['iteration'] == 3
    assert returned['findings'][0] == changes['findings'][0]
    assert 'finding_id 撞號：' + finding()['finding_id'] in lines


def test_run_parses_card_file_role(tmp_path):
    root = make_root(tmp_path, project=False)
    path = tmp_path / 'return.json'
    path.write_text('{}')
    client = make_client(card(branch='wf/WF-001'))
    assert run(['WF-001', '--file', str(path), '--role', 'executor'], client=client, root=root) == 0
    with pytest.raises(SystemExit):
        run(['10', '--file', str(path), '--role', 'pm'], client=client, root=root)


def test_module_free_text_is_not_a_status(tmp_path):
    root = promote(make_root(tmp_path, project=False), 'stat-redline')
    changes = {'tier_basis': {'sensitive': ['statistics'], 'recoverable': 'reversible', 'blast': 'file'}}
    data = {'adversarial_tests': [{'angle': '發現', 'result': '支持', 'text': ''}]}
    result, lines, _, _ = invoke(tmp_path, root=root, changes=changes, data=data)
    assert result.rc == 0
    assert 'adversarial_tests[0]：text 空' not in lines
    print('MODULE_TEXT_NEGATIVE_CONTROL angle=發現 is prose; result=不適用 is checked elsewhere')


def test_missing_text_and_explicit_empty_sections(tmp_path):
    data = {'self_run': [], 'acceptance': [], 'mistakes': [], 'unverified': [],
            'out_of_scope': [], 'note_responses': [{'id': 'T-執行-01', 'value': 'found'}]}
    result, lines, _, _ = invoke(tmp_path, data=data)
    assert result.rc == 0 and 'note_responses[0]：text 空' in lines
    assert not [line for line in lines if line.startswith('缺段：')]


def test_return_schema_is_consumed_at_runtime(tmp_path):
    root = make_root(tmp_path, project=False)
    path = root / 'core/return.md'
    text = path.read_text(encoding='utf-8')
    original = '"self_run": {"type": "array"'
    assert original in text
    path.write_text(text.replace(original, '"self_run": {"type": "string"', 1), encoding='utf-8')
    result, _, posted, _ = invoke(tmp_path, root=root, data={'self_run': []})
    assert result.rc != 0 and posted['body'].startswith('拒收・D3・')
    result, _, _, _ = invoke(tmp_path, root=root, data={'self_run': '規則臨時允許的字串'})
    assert result.rc == 0
    print('SCHEMA_NEGATIVE_CONTROL changed artifact changes accepted type')


def test_comment_counter_detects_forbidden_mutation():
    client = make_client(card())
    client.update_card_body(10, card())
    client.write_project_field(('updateProjectV2ItemFieldValue', 'UpdateProjectV2ItemFieldValueInput',
                                {'projectId': 'P', 'itemId': 'item', 'fieldId': '狀態',
                                 'value': {'text': '完成'}}))
    assert [name for name, _ in client.calls if name in WRITES] == ['update_card_body', 'write_project_field']
    print('WRITE_NEGATIVE_CONTROL detected update_card_body and write_project_field')


# ── WF-003-R1.1-2：review 內部的 notes 消費者，其 D3 留痕逐字維持基線 ────────────

def nested_client(good):
    """issue() 第一次回合法卡（review 自己的驗卡面全過），第二次由 `_hints` 內層 `notes`
    重讀時回壞 JSON。⛔ 不改交回單、⛔ 不改角色，只換第二次讀到的 body。"""
    client = make_client(good)
    original, count = client.responses['issue'], [0]

    def issue(number):
        count[0] += 1
        row = original(number=number)
        return row if count[0] == 1 else dict(row, body='```json wf-card\n{壞掉\n```')

    client.responses['issue'] = issue
    return client, count


@pytest.mark.parametrize('role', ['reviewer', 'executor'])
def test_nested_notes_d3_still_posts_exactly_one_reject(tmp_path, role):
    """WF-003-R1.1-2 正向：`review._hints` 的內層 `notes` 落讀側 D3 ⇒ 恰一則
    first_line='wf:reject'、本文逐字 `拒收・D3・wf-card JSON 解析失敗`、rc=1、⛔ 無硬擋行、
    ⛔ 不貼 wf:return／wf:verdict——與基線 005bab29ae1c3a3fbfc4a3520c56aca198a565d8 逐字相同。

    被審 SHA eca85c52472c7933ff95a2fd9bb9abd0c5026c31 在同一替身下是 all_remote_writes=[]、
    零留言、printed 反而多一行 `硬擋・D3・wf-card JSON 解析失敗`。
    """
    root = make_root(tmp_path, project=False)
    client, count = nested_client(card(branch='wf/WF-001', source_sha='b' * 40))
    path = tmp_path / 'return.json'
    path.write_text('{}', encoding='utf-8')
    lines = []
    result = review(10, file=path, role=role, client=client, root=root, emit=lines.append)
    assert count[0] == 2, count                      # 內層確實重讀了一次，⛔ 不是走不到
    assert result.rc == 1 and result.reason == 'wf-card JSON 解析失敗'
    posted = [kwargs for name, kwargs in client.calls if name == 'post_comment']
    assert [kwargs['first_line'] for kwargs in posted] == ['wf:reject']
    assert posted[0]['body'] == '拒收・D3・' + result.reason
    assert [name for name, _ in client.calls if name in WRITES] == ['post_comment']
    assert [line for line in result.printed if line.startswith('硬擋・')] == []
    print('WF-003-R1.1-2', role, posted[0]['body'])


def test_the_same_nested_notes_is_a_local_hard_block_for_the_notes_verb(tmp_path):
    """WF-003-R1.1-2 負控：同一張壞卡直接跑 `notes` 動詞 ⇒ 本機硬擋、零留言。
    證明上一條拿到的一則 wf:reject 來自呼叫端契約的隔離，⛔ 不是把本機硬擋整個改回去。"""
    root = make_root(tmp_path, project=False)
    client = make_client('```json wf-card\n{壞掉\n```')
    lines = []
    result = notes(10, client=client, root=root, emit=lines.append)
    assert result.rc == 1 and result.reason == 'wf-card JSON 解析失敗'
    assert [name for name, _ in client.calls if name in WRITES] == []
    assert [line for line in lines if line.startswith('硬擋・')] == ['硬擋・D3・' + result.reason]


@pytest.mark.parametrize('variant', sorted(PERTURBATIONS))
def test_uncovered_hints_are_printer_independent(tmp_path, perturb, variant):
    """CLI-002：印法擾動下，`note_responses 未覆蓋：<id>` 行集合與未擾動時逐字相同。
    覆蓋率提示取的是 `_write.NotesResult.note_ids`，⛔ 不從 notes 的 printed 反解析。"""
    def run(name):
        root = make_root(tmp_path, name=name, project=False)
        _, lines, _, _ = invoke(tmp_path, root=root,
                                client=make_client(formal_card(), comments=CANDIDATE))
        return [line for line in lines if line.startswith('note_responses 未覆蓋：')]

    plain = run(f'a3-review-plain-{variant}')
    assert_prose_goes_blind(tmp_path, perturb, variant, f'a3-review-{variant}')
    shifted = run(f'a3-review-shifted-{variant}')
    assert shifted == plain and len(plain) > 5
    print('REVIEW_UNCOVERED', variant, len(plain), '筆逐字相同')
