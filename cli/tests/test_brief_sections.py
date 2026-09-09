"""消費 core/dispatch.md（表、末段樣板）、core/handoff.md 每段首行、
core/params.md rule_confirm_days、core/return.md schema required、core/verbs.md §1 brief 列／§2。
所有遠端操作由手構替身接住，⛔ 不碰真實網路。
本檔另供 test_brief_reviewer.py 與 test_brief_modules.py 取用共用替身與 root 建置。
"""
from datetime import date, timedelta
import json
from pathlib import Path
import re
import shutil
import socket

import pytest

from .fakes import FakeGhClient
from wf.compose.blocks import load_blocks
from wf.compose.schema import compose_schema
from wf.compose.validate import validate
from wf.verbs.brief import TEMPLATE_HEAD, _rows, brief

RULES = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / 'fixtures/brief'
TODAY = date(2026, 9, 8)
WRITES = ('update_card_body', 'post_comment', 'write_project_field',
          'add_to_project', 'remove_from_project', 'close_issue')
SOURCE = re.compile(r'^\[來源: (core|module|project|card)/[^ ]+ · [^：]+：.+ · '
                    r'confirmed \d{4}-\d{2}-\d{2}\]( ⚠️)?$')
NUMBERED = re.compile(r'^([0-9]+)\. ([^：]+)：')


class Client(FakeGhClient):
    """fakes.FakeGhClient 已含 merge_base 與 repo；子類保留給本檔既有引用。"""


def card(**changes):
    return dict(schema_version=2, card_id='WF-001', source_issue=10, feature='功能',
                core_pain='核心痛點逐字；含分號', non_scope=['非射程一', '非射程二'],
                stage_plan=[], stage='執行', state='進行中', list_convergence=[],
                service_goal='', tier='T3',
                tier_basis={'sensitive': [], 'recoverable': 'reversible', 'blast': 'file'},
                exec_capability={'level': '主力型', 'reason': '執行理由'},
                review_capability={'level': '高階型', 'reason': '查核理由'},
                db_scope=None, resources=[], when='卡的 when', spec_version=1, iteration=2,
                acceptance=['第一條；含分號', '第二條\n含換行'], verification=[], parent=None,
                blocked=None, grilling=None, owner=None, branch=None, source_sha=None,
                notes=[]) | changes


def block(label, value):
    body = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return f'```json {label}\n{body}\n```\n'


def issue_row(number, card_json):
    body = card_json if isinstance(card_json, str) else '散文\n' + block('wf-card', card_json)
    return {'number': number, 'node_id': f'I{number}', 'state': 'open', 'body': body}


def make_client(card_json=None, *, comments=(), items=(), rows=None, **responses):
    rows = [issue_row(10, card_json)] if rows is None else rows
    index = {row['number']: row for row in rows}
    responses = {'branch_head': 'a' * 40, 'merge_base': 'b' * 40, 'commit_exists': True,
                 **responses}
    return Client(issue=lambda number: index[number], issues=rows, comments=list(comments),
                  project={'id': 'PROJECT', 'fields': [], 'items': list(items)}, **responses)


def make_root(tmp_path, *, listed=(), project=True, contracts=(), confirmed=None, name='root'):
    """真規則檔複製一份到 tmp，讓過期與契約案例能改檔；⛔ 不動 repo 內的規則。"""
    root = tmp_path / name
    for part in ('core', 'modules', 'stages', 'roles'):
        shutil.copytree(RULES / part, root / part)
    (root / '.wf').mkdir()
    (root / '.wf/modules.json').write_text(json.dumps(
        {'areas': ['WF'], 'modules': [{'name': item} for item in listed],
         'project': {'owner': 'fake', 'number': 1} if project else None}), encoding='utf-8')
    if contracts:
        (root / '.wf/contracts').mkdir()
        for source in contracts:
            shutil.copy(FIXTURES / source, root / '.wf/contracts' / source)
    if confirmed is not None:
        path = root / 'core/dispatch.md'
        path.write_text(re.sub(r'^last_confirmed: .*$', f'last_confirmed: {confirmed}',
                               path.read_text(encoding='utf-8'), count=1, flags=re.M),
                        encoding='utf-8')
    return root


def emitted(client, root, target='executor', **kwargs):
    lines = []
    result = brief(10, target=target, client=client, root=root, emit=lines.append,
                   today=TODAY, **kwargs)
    assert result.printed == tuple(lines)
    return result, lines


def sections(lines):
    """[(段名, [首行, 內容行…])]；樣板不是段，以 TEMPLATE_HEAD 為界。"""
    out = []
    for line in lines:
        if line == TEMPLATE_HEAD:
            break
        if line.startswith('## '):
            out.append((line[3:], []))
        elif out:
            out[-1][1].append(line)
    return out


def template(lines):
    return json.loads(lines[lines.index(TEMPLATE_HEAD) + 1])


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('禁止真實網路')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)


def test_section_order_follows_the_dispatch_table(tmp_path):
    """驗收 1：段序逐字對表；executor 少一列（查核序），reviewer 全列。"""
    root = make_root(tmp_path)
    rows = _rows(root)
    assert len(rows) == 15
    fixed = [row[0] for row in rows if row[1] == 'CLI' or row[1].startswith('人')]
    assert len(fixed) == 14
    skipped = [row[0] for row in rows if '`--for executor` 不印' in row[2]]
    assert skipped == ['查核序']
    _, executor = emitted(make_client(card()), root)
    _, reviewer = emitted(make_client(card()), root, 'reviewer')
    names = [name for name, _ in sections(executor)]
    review_names = [name for name, _ in sections(reviewer)]
    assert review_names == fixed  # 未啟用模組 ⇒ 表末「模組段」列展開 0 個段名
    assert names == [name for name in fixed if name not in skipped]
    assert (len(names), len(review_names)) == (13, 14)


def test_human_sections_print_only_name_and_marker(tmp_path):
    """驗收 1：人填 5 段只有段名＋（人填）；CLI 段是負控。"""
    root = make_root(tmp_path)
    _, lines = emitted(make_client(card()), root, 'reviewer')
    human = [row[0] for row in _rows(root) if row[1].startswith('人')]
    assert len(human) == 5
    body = dict(sections(lines))
    for name in human:
        assert body[name][1:] == ['（人填）'], name
    assert body['卡與身分'][1:] != ['（人填）']


def test_every_section_first_line_is_a_source_line(tmp_path):
    """驗收 2：每段首行合 handoff.md 格式；附兩個負控證明樣式會響。"""
    root = make_root(tmp_path)
    _, lines = emitted(make_client(card()), root, 'reviewer')
    got = sections(lines)
    assert len(got) == 14
    for name, content in got:
        assert SOURCE.match(content[0]), (name, content[0])
    assert SOURCE.match('[來源: core/core/dispatch.md · dispatch：何時 · confirmed 2026-09-07]')
    assert not SOURCE.match('[來源: 亂寫]')
    assert not SOURCE.match('[來源: other/core/dispatch.md · a：b · confirmed 2026-09-07]')


@pytest.mark.parametrize('days,flagged', [(0, False), (90, False), (91, True), (100, True)])
def test_stale_rule_file_is_flagged(tmp_path, days, flagged):
    """驗收 2：last_confirmed 超過 rule_confirm_days（90 天種子）才標 ⚠️。"""
    root = make_root(tmp_path, name=f'root{days}',
                     confirmed=(TODAY - timedelta(days=days)).isoformat())
    _, lines = emitted(make_client(card()), root)
    first = sections(lines)[0][1][0]
    assert first.endswith(' ⚠️') is flagged, first


def test_threshold_is_read_from_params_not_hardcoded(tmp_path):
    """驗收 2：把 params.md 的現值改成 0 天 → 一天前確認的檔也 ⚠️；移掉該列 → 印未能讀取。"""
    root = make_root(tmp_path, confirmed=(TODAY - timedelta(days=1)).isoformat())
    path = root / 'core/params.md'
    text = path.read_text(encoding='utf-8')
    path.write_text(re.sub(r'^\| rule_confirm_days \| 90 天', '| rule_confirm_days | 0 天',
                           text, count=1, flags=re.M), encoding='utf-8')
    _, lines = emitted(make_client(card()), root)
    assert sections(lines)[0][1][0].endswith(' ⚠️')
    path.write_text(re.sub(r'^\| rule_confirm_days .*$', '', text, count=1, flags=re.M),
                    encoding='utf-8')
    _, lines = emitted(make_client(card()), root)
    assert lines[0] == '未能讀取 rule_confirm_days，未評估過期'
    assert not sections(lines)[0][1][0].endswith(' ⚠️')


def test_card_facts_and_verbatim_content(tmp_path):
    """驗收 3：核心痛點、驗收條件（含分號與換行）、非射程逐字；卡與身分八列。"""
    root = make_root(tmp_path)
    data = card()
    _, lines = emitted(make_client(data), root)
    body = dict(sections(lines))
    assert body['核心痛點'][1:] == [data['core_pain']]
    assert body['驗收條件'][1:] == data['acceptance']
    assert body['非射程'][1:] == data['non_scope']
    assert body['卡與身分'][1:] == ['card_id：WF-001', 'source_issue：10', 'tier：T3',
                                    'stage：執行', 'iteration：2', 'parent：null',
                                    'when：卡的 when', 'from：pm · to：executor']
    assert body['能力層級建議'][1:] == ['exec_capability.level：主力型', 'exec_capability.reason：執行理由']
    _, review = emitted(make_client(data), root, 'reviewer')
    assert dict(sections(review))['能力層級建議'][1:] == ['review_capability.level：高階型',
                                                         'review_capability.reason：查核理由']


def test_capability_prints_level_and_reason_not_tier_basis(tmp_path):
    """能力層級段印 <欄>.level 與 <欄>.reason（schema $defs/capability required），⛔ 不印 tier_basis；
    欄為 null 時兩列印 null（負控：不因欄空而消失）。"""
    root = make_root(tmp_path)
    _, lines = emitted(make_client(card(exec_capability=None)), root)
    body = dict(sections(lines))['能力層級建議']
    assert body[1:] == ['exec_capability.level：null', 'exec_capability.reason：null']
    assert not any('tier_basis' in line for line in body)


def test_notes_section_is_the_notes_verb_output(tmp_path):
    """驗收 9：注意事項段逐行搬 notes 的清單；候選也在，但不進樣板 id。"""
    from wf.verbs.notes import notes as notes_verb
    root = make_root(tmp_path)
    note = {'text': '候選條目', 'origin': 'https://example.invalid/1'}
    comments = [{'id': 1, 'url': 'https://example.invalid/c1', 'author': 'a',
                 'created_at': '2026-09-01T00:00:00Z', 'body': block('wf-note', note)}]
    data = card(notes=[{'id': 'T-執行-01', 'text': '卡面條目',
                        'origin': 'https://example.invalid/2'}])
    _, lines = emitted(make_client(data, comments=comments), root)
    expected = notes_verb(10, client=make_client(data, comments=comments), root=root,
                          for_role='executor', emit=lambda line: None).printed
    body = dict(sections(lines))
    assert body['注意事項'][1:] == list(expected)
    candidates = [line for line in expected if line.startswith('候選')]
    assert len(candidates) == 1
    ids = [match[2] for match in map(NUMBERED.match, expected) if match]
    assert 'T-執行-01' in ids and len(ids) > 5
    assert [item['id'] for item in template(lines)['note_responses']] == ids


def test_template_carries_required_keys_and_acceptance(tmp_path):
    """驗收 9：樣板預填四鍵與 acceptance 條文，其餘 required 留空。"""
    root = make_root(tmp_path)
    data = card()
    _, lines = emitted(make_client(data), root)
    body = template(lines)
    required = load_blocks(root).schemas['wf-return'].data['required']
    assert set(required) <= set(body) and 'source_sha' in required
    assert (body['card_id'], body['iteration'], body['role']) == ('WF-001', 2, 'executor')
    assert [item['text'] for item in body['acceptance']] == data['acceptance']
    assert all(item['method'] == item['evidence'] == item['falsifier'] == '' for item in body['acceptance'])
    assert body['source_sha'] == ''
    _, review = emitted(make_client(data), root, 'reviewer')
    assert template(review)['role'] == 'reviewer'


def test_contract_blocks_three_cases(tmp_path):
    """驗收 6：合法逐條、不合 schema 印且不採用、無區塊印專案層未宣告。"""
    schema = compose_schema(load_blocks(RULES), 'wf-contract')
    assert validate({'side_effects': ['a']}, schema) == []
    assert validate({'side_effects': '不是陣列'}, schema)  # 負控：檢查器會響
    good = make_root(tmp_path, name='good', contracts=['contract-ok.md'])
    _, lines = emitted(make_client(card()), good)
    assert dict(sections(lines))['副作用入口'][1:] == ['build：重建容器 wf-dev',
                                                       'migration：改 schema public']
    both = make_root(tmp_path, name='both', contracts=['contract-ok.md', 'contract-bad.md'])
    _, lines = emitted(make_client(card()), both)
    content = dict(sections(lines))['副作用入口'][1:]
    assert content[0] == '契約檔不合 schema：contract-bad.md'
    assert '不是陣列' not in content
    for name, contracts in (('none', ['contract-none.md']), ('empty', [])):
        root = make_root(tmp_path, name=name, contracts=contracts)
        _, lines = emitted(make_client(card()), root)
        assert dict(sections(lines))['副作用入口'][1:] == ['專案層未宣告']


def test_broken_card_json_is_d3_with_one_reject_comment(tmp_path):
    """驗收 10／verbs.md §1 brief 硬擋：卡面 JSON 解析失敗＝D3，一則 wf:reject。"""
    root = make_root(tmp_path)
    client = make_client('前言\n```json wf-card\n{壞掉\n```\n')
    result = brief(10, target='executor', client=client, root=root, emit=lambda line: None)
    assert result.rc == 1
    assert [name for name, _ in client.calls if name in WRITES] == ['post_comment']
    call = dict(client.calls[-1][1])
    assert call['first_line'] == 'wf:reject' and call['body'].startswith('拒收・D3・')


def test_null_card_block_is_d3(tmp_path):
    """null 區塊探針：本卡 wf-card 區塊值為 null ⇒ D3 一則 wf:reject（訊息含「不是物件」）。"""
    root = make_root(tmp_path)
    client = make_client('前言\n```json wf-card\nnull\n```\n')
    result = brief(10, target='executor', client=client, root=root, emit=lambda line: None)
    assert result.rc == 1 and '不是物件' in result.reason
    assert [name for name, _ in client.calls if name in WRITES] == ['post_comment']


def test_card_id_lookup_skips_null_issue_and_prints(tmp_path):
    """null 區塊探針（card_number）：以卡ID 呼叫 brief，別的 issue 的 null 區塊只略過並印在最前。"""
    root = make_root(tmp_path)
    rows = [issue_row(3, '```json wf-card\nnull\n```\n'), issue_row(10, card())]
    lines = []
    result = brief('WF-001', target='executor', client=make_client(rows=rows), root=root, emit=lines.append)
    assert result.rc == 0 and lines[0] == '略過無法解析的 issue #3'


def test_healthy_run_writes_nothing(tmp_path):
    """驗收 10：正常路徑對 GitHub 零寫入（上一個測試是會響的負控）。"""
    root = make_root(tmp_path, contracts=['contract-ok.md'])
    client = make_client(card())
    result, _ = emitted(client, root, 'reviewer')
    assert result.rc == 0
    assert [name for name, _ in client.calls if name in WRITES] == []
