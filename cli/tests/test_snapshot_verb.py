"""消費 core/verbs.md §1 snapshot 列（硬擋欄＝「—」）／§2（對帳例外、D3 末句的 snapshot 例外）、
core/card-schema.md §1 (b)／§2／§4／§5、core/return.md、roles/pm.md F-PM-04。
本檔所有遠端操作由手構替身接住；⛔ 不碰真實網路。
"""
import json
from pathlib import Path
import socket
import subprocess

import pytest

from .fakes import FakeGhClient
from wf.compose.enable import UnknownEnableKindError
from wf.compose.blocks import load_blocks, projection
from wf.verbs._write import projected
from wf.verbs.snapshot import run, snapshot

RULES = Path(__file__).resolve().parents[2]
NOW = '2026-09-08T00:00:00+00:00'
# snapshot 的「寫」欄只有本機兩檔：任一遠端寫入都算違規，post_comment（含 wf:reject）也是。
WRITES = ('update_card_body', 'write_project_field', 'post_comment',
          'add_to_project', 'remove_from_project', 'close_issue')


def block(label, value, raw=None):
    body = json.dumps(value, ensure_ascii=False) if raw is None else raw
    return f'```json {label}\n{body}\n```\n'


def card(card_id='WF-001', **changes):
    # 獨立逐鍵 oracle；⛔ 不用被測程式組預期值。
    return dict(schema_version=2, card_id=card_id, source_issue=10, feature='',
                core_pain='', non_scope=[], stage_plan=[], stage='需求', state='待辦',
                list_convergence=[], service_goal='', tier=None, tier_basis=None,
                exec_capability=None, review_capability=None, db_scope=None,
                resources=[], when='', spec_version=1, iteration=0, acceptance=[],
                verification=[], parent=None, blocked=None, grilling=None,
                owner=None, branch=None, source_sha=None, notes=[]) | changes


def issue(number, value=None, *, state='open', body=None):
    return {'number': number, 'state': state,
            'body': block('wf-card', value) if body is None else body}


def comment(number, ident, label=None, value=None, *, raw=None, created_at='2026-09-01T00:00:00Z'):
    body = 'wf:note\n散文' if label is None else f'首行\n{block(label, value, raw)}'
    return {'id': ident, 'url': f'https://github.com/fake/repo/issues/{number}#issuecomment-{ident}',
            'author': 'someone', 'created_at': created_at, 'body': body}


def fields(catalog, values):
    """把 {欄名: 值} 轉成 Project 的 fieldValues 形狀（TEXT 有 max_bytes、其餘單選）。"""
    spec = projection(catalog)
    return {name: (None if values.get(name) is None
                   else {'text': values[name]} if 'max_bytes' in spec[name]
                   else {'name': values[name]})
            for name in spec}


def item(number, catalog, values, repo='fake/repo'):
    return {'id': f'ITEM{number}', 'isArchived': False,
            'content': {'__typename': 'Issue', 'number': number,
                        'repository': {'nameWithOwner': repo}},
            'fieldValues': fields(catalog, values)}


def on_board(number, value, catalog, **overrides):
    return item(number, catalog, projected(value, catalog) | overrides)


class Client(FakeGhClient):
    repo = 'fake/repo'


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(RULES)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('S14 禁止真實網路或子程序')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(subprocess, 'run', forbidden)


@pytest.fixture
def setup(tmp_path, catalog):
    def make(issues=(), items=(), comments=None, project=True, modules=()):
        (tmp_path / '.wf').mkdir(exist_ok=True)
        config = {'areas': ['WF'], 'modules': [{'name': name} for name in modules],
                  'project': {'owner': 'fake', 'number': 1} if project else None}
        (tmp_path / '.wf/modules.json').write_text(json.dumps(config), encoding='utf-8')
        board = {'id': 'PROJECT', 'items': list(items), 'fields': []}
        table = dict(comments or {})
        client = Client(issues=lambda state: list(issues),
                        project=lambda **kwargs: board,
                        comments=lambda number: list(table.get(number, [])))
        return client, dict(client=client, root=tmp_path, catalog=catalog,
                            now=NOW, emit=lambda line: None)
    return make


def posted_comments(client):
    return [data for name, data in client.calls if name == 'post_comment']


def assert_read_only(client):
    assert [name for name, _ in client.calls if name in WRITES] == []


def outputs(tmp_path):
    """兩個本機輸出檔的內容（不存在即讓測試在 read_text 就紅）。"""
    directory = tmp_path / '.wf/snapshot'
    return (json.loads((directory / 'snapshot.json').read_text(encoding='utf-8')),
            (directory / 'snapshot.md').read_text(encoding='utf-8'))


# 驗收 1：母體＝帶 wf-card 的全部 issue（含撤銷卡與終態關閉卡），無區塊者不算。
def population(catalog):
    cards = [card('WF-001'), card('WF-002', tier='T1'),
             card('WF-003', stage='結案'), card('WF-004', stage='結案', state='完成')]
    issues = [issue(1, cards[0]), issue(2, cards[1]), issue(3, cards[2]),
              issue(4, cards[3], state='closed'), issue(5, body='一般 issue，無區塊')]
    items = [on_board(1, cards[0], catalog), on_board(2, cards[1], catalog)]
    return cards, issues, items


def test_population_counts_every_card_block(setup, catalog):
    cards, issues, items = population(catalog)
    client, kwargs = setup(issues=issues, items=items)
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert [row['card_id'] for row in result.data['cards']] == [c['card_id'] for c in cards]
    assert [row['number'] for row in result.data['cards']] == [1, 2, 3, 4]
    assert [row['state_open'] for row in result.data['cards']] == [True, True, True, False]
    assert [row['projection'] is not None for row in result.data['cards']] == [True, True, False, False]
    assert posted_comments(client) == []
    assert result.data['invalid_cards'] == []
    assert_read_only(client)
    print('母體：issue 共', len(issues), '帶 wf-card 者', len(result.data['cards']))


# 驗收 2：壞卡進 invalid_cards（帶原始 body），rc=0、零遠端寫入、合法卡照常輸出。
def test_bad_card_json_goes_to_invalid_cards(setup, catalog, tmp_path):
    _, issues, items = population(catalog)
    issues[1] = issue(2, body=block('wf-card', None, raw='{壞掉的 JSON'))
    client, kwargs = setup(issues=issues, items=items)
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert posted_comments(client) == []
    assert [row['number'] for row in result.data['cards']] == [1, 3, 4]
    assert [bad['number'] for bad in result.data['invalid_cards']] == [2]
    assert result.data['invalid_cards'][0]['body'] == issues[1]['body']  # 原始 body 逐字留存
    assert result.data['invalid_cards'][0]['reason']
    # §1 印欄：卡面不合法的 issue 號與原因；⛔ 不只驗「寫」欄而放掉「印」欄。
    assert result.printed == (
        f"#2 卡面不合法：{result.data['invalid_cards'][0]['reason']}",)
    written, text = outputs(tmp_path)
    assert written == result.data
    section = text.split('## 壞卡', 1)[1].split('\n##', 1)[0]
    assert f"#2：{result.data['invalid_cards'][0]['reason']}" in section  # 號與原因都要在
    assert_read_only(client)


def test_unclosed_block_and_duplicate_are_invalid_cards(setup):
    for body in ('```json wf-card\n{}\n', block('wf-card', card()) + block('wf-card', card())):
        client, kwargs = setup(issues=[issue(1, body=body)])
        result = snapshot(**kwargs)
        assert result.rc == 0
        assert [bad['number'] for bad in result.data['invalid_cards']] == [1]
        assert result.data['invalid_cards'][0]['body'] == body
        assert result.data['cards'] == []
        assert posted_comments(client) == []
        assert_read_only(client)


# core/card-schema.md §1（wf-card 是 object）：區塊在而值為 null（或任何非物件）＝存在的壞卡，不是「沒有卡」。
def test_null_card_block_is_invalid_card(setup, catalog, tmp_path):
    _, issues, items = population(catalog)
    issues[1] = issue(2, None)  # 區塊內容逐字 null
    assert '```json wf-card\nnull\n```' in issues[1]['body']
    client, kwargs = setup(issues=issues, items=items)
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert posted_comments(client) == []
    assert [bad['number'] for bad in result.data['invalid_cards']] == [2]
    assert '不是物件' in result.data['invalid_cards'][0]['reason']
    assert result.data['invalid_cards'][0]['body'] == issues[1]['body']
    assert [row['number'] for row in result.data['cards']] == [1, 3, 4]
    written, _ = outputs(tmp_path)
    assert written == result.data
    assert_read_only(client)


@pytest.mark.parametrize('value', [None, [], ['a'], 'null', 3, True])
def test_non_object_card_block_is_invalid_card(setup, value):
    client, kwargs = setup(issues=[issue(1, value)])
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert posted_comments(client) == []
    assert result.data['cards'] == []
    assert '不是物件' in result.data['invalid_cards'][0]['reason']
    assert_read_only(client)


# 驗收 3：core schema——宣告模組欄恆合法（(b)）；模組狀態值未合成即不合法。
def test_declared_module_field_passes_without_enabling(setup, catalog):
    client, kwargs = setup(issues=[issue(1, card(escalation_count=2))],
                           items=[on_board(1, card(), catalog)])
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert result.data['cards'][0]['card']['escalation_count'] == 2
    assert result.data['invalid_cards'] == []
    assert posted_comments(client) == []


def test_module_state_value_outside_core_schema_is_invalid_card(setup):
    """escalation 未列於專案設定 ⇒ 升級 不在合成 schema：進 invalid_cards，⛔ 不拒收。"""
    client, kwargs = setup(issues=[issue(1, card(state='升級'))])
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert posted_comments(client) == []
    assert [bad['number'] for bad in result.data['invalid_cards']] == [1]
    assert '/state' in result.data['invalid_cards'][0]['reason']
    assert_read_only(client)


def test_enabled_module_state_value_passes_composed_schema(setup, catalog):
    """模組合成 schema 依 is_enabled 判定——escalation 啟用時板上 state=升級 的卡是合法卡。"""
    value = card(state='升級', escalation_count=3)
    client, kwargs = setup(issues=[issue(1, value)], items=[on_board(1, value, catalog)], modules=['escalation'])
    result = snapshot(**kwargs)
    assert result.rc == 0 and posted_comments(client) == []
    assert result.data['cards'][0]['card']['state'] == '升級'
    assert result.data['invalid_cards'] == []
    assert_read_only(client)


@pytest.mark.parametrize('plan,accepted', [(['需求', '研究', '執行', '審核', '結案'], True), ([], False)])
def test_stage_plan_enabled_module_state(setup, plan, accepted):
    """enable_if 依卡面（stage_plan_has 研究）⇒ 不可判定 只在該卡的 stage_plan 含研究時合法；
    不合法時走 invalid_cards 而非拒收，故兩邊都是 rc=0、零留言。"""
    client, kwargs = setup(issues=[issue(1, card(state='不可判定', stage='研究', stage_plan=plan))])
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert (result.data['cards'] != []) is accepted
    assert (result.data['invalid_cards'] == []) is accepted
    assert posted_comments(client) == []
    assert_read_only(client)


def test_unknown_key_is_invalid_card(setup):
    client, kwargs = setup(issues=[issue(1, card(不存在的鍵=1))])
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert [bad['number'] for bad in result.data['invalid_cards']] == [1]
    assert result.data['cards'] == []
    assert posted_comments(client) == []
    assert_read_only(client)


# core/verbs.md §2 D3 末句＋§1：原因字串帶 utf-8 無法編碼的字元（逐字轉義的孤立代理碼點）
# 仍要落兩檔、合法卡照常輸出；⛔ 不得只捕捉例外後跳過輸出。
LONE_SURROGATE = '\ud800'


def test_unencodable_reason_still_writes_both_outputs(setup, catalog, tmp_path):
    _, issues, items = population(catalog)
    issues[1] = issue(2, card('WF-002', **{LONE_SURROGATE: 1}))
    client, kwargs = setup(issues=issues, items=items)
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert [row['number'] for row in result.data['cards']] == [1, 3, 4]  # 前後的合法卡不受影響
    bad, = result.data['invalid_cards']
    assert bad['number'] == 2
    assert bad['reason'] == f'/{LONE_SURROGATE}: 不符合 additionalProperties'
    written, text = outputs(tmp_path)  # 兩檔都要在且可回讀，⛔ 不得是 0 位元組或缺檔
    assert written == result.data  # 落檔的轉義回讀後逐字等值：body 與 reason 都對得回去
    assert written['invalid_cards'][0]['body'] == issues[1]['body']
    section = text.split('## 壞卡', 1)[1].split('\n##', 1)[0]
    assert '#2' in section and '\\ud800' in section  # Markdown 同樣不中斷，原因照樣列出
    assert posted_comments(client) == []
    assert_read_only(client)


def test_unencodable_reason_does_not_break_emit(setup, catalog):
    """§1 印欄與落檔同一條邊界：真實入口的 emit=print 也會撞上不可編碼字元。
    印出去的那行要能編碼，`printed` 仍留原因的逐字原樣。"""
    _, issues, items = population(catalog)
    issues[1] = issue(2, card('WF-002', **{LONE_SURROGATE: 1}))
    client, kwargs = setup(issues=issues, items=items)
    emitted = []
    kwargs['emit'] = lambda line: emitted.append(line.encode('utf-8'))
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert emitted == ['#2 卡面不合法：/\\ud800: 不符合 additionalProperties'.encode('utf-8')]
    assert result.printed == (
        f"#2 卡面不合法：{result.data['invalid_cards'][0]['reason']}",)
    assert_read_only(client)


# 驗收 2b：母體＝cards ∪ invalid_cards；混合、全壞與已關閉的壞卡都不掉。
def test_mixed_valid_and_invalid_cards_keep_population(setup, catalog, tmp_path):
    _, issues, items = population(catalog)
    issues[1] = issue(2, card('WF-002', 不存在的鍵=1))
    issues[2] = issue(3, body=block('wf-card', None, raw='{壞掉的 JSON'))
    client, kwargs = setup(issues=issues, items=items)
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert result.data['cards'] != [] and result.data['invalid_cards'] != []
    numbers = ([row['number'] for row in result.data['cards']]
               + [bad['number'] for bad in result.data['invalid_cards']])
    assert sorted(numbers) == [1, 2, 3, 4]  # issue 5 無 wf-card 區塊，不在母體
    written, _ = outputs(tmp_path)
    assert written == result.data
    assert_read_only(client)


def test_every_card_invalid_still_writes_both_outputs(setup, tmp_path):
    broken = [issue(number, body=block('wf-card', None, raw='{壞掉的 JSON'))
              for number in (1, 2, 3, 4)]
    client, kwargs = setup(issues=broken)
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert result.data['cards'] == []
    assert [bad['number'] for bad in result.data['invalid_cards']] == [1, 2, 3, 4]
    written, text = outputs(tmp_path)
    assert written == result.data
    assert '## 壞卡' in text and '#4' in text
    assert posted_comments(client) == []
    assert_read_only(client)


def test_schema_compose_crash_still_lands_in_invalid_cards(setup, catalog, tmp_path):
    """合成 schema 讀的是尚未驗過的卡面：`stage_plan` 非可迭代時 enable.py 會拋 TypeError。
    §1「⛔ 不從盤點母體排除」要求它照樣進 invalid_cards，⛔ 不得中斷整次盤點。"""
    _, issues, items = population(catalog)
    issues[1] = issue(2, body=block('wf-card', card('WF-002', stage_plan=5)))
    client, kwargs = setup(issues=issues, items=items)
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert [row['number'] for row in result.data['cards']] == [1, 3, 4]
    assert [bad['number'] for bad in result.data['invalid_cards']] == [2]
    reason = result.data['invalid_cards'][0]['reason']  # 釘內容，⛔ 不釘例外類別
    assert 'stage_plan' in reason or reason.startswith('schema 合成或驗證失敗：')
    assert result.data['invalid_cards'][0]['body'] == issues[1]['body']
    written, text = outputs(tmp_path)
    assert written == result.data
    assert '#2' in text.split('## 壞卡', 1)[1]
    assert_read_only(client)


def test_closed_bad_card_is_in_invalid_cards(setup, catalog):
    _, issues, items = population(catalog)
    issues[3] = issue(4, card('WF-004', 不存在的鍵=1), state='closed')  # 母體含 state='all'
    client, kwargs = setup(issues=issues, items=items)
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert [bad['number'] for bad in result.data['invalid_cards']] == [4]
    assert [name for name, kwargs_ in client.calls if name == 'issues'] == ['issues']
    assert [kwargs_['state'] for name, kwargs_ in client.calls if name == 'issues'] == ['all']
    assert_read_only(client)


# 驗收 4：對帳只印不重寫。
def test_reconcile_prints_and_never_writes(setup, catalog):
    value = card('WF-007', tier='T2', owner={'role': 'executor', 'actor': '甲'})
    client, kwargs = setup(issues=[issue(1, value)],
                           items=[on_board(1, value, catalog, 級別='T1')])
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert result.printed == ('WF-007 級別：卡面=T2 投影=T1',)
    assert result.data['mismatches'] == [
        {'card_id': 'WF-007', 'number': 1, 'field': '級別', 'card': 'T2', 'projection': 'T1'}]
    assert [name for name, _ in client.calls if name == 'write_project_field'] == []
    assert_read_only(client)


def test_reconcile_equal_projection_has_no_mismatch(setup, catalog):
    value = card('WF-007', tier='T2', owner={'role': 'executor', 'actor': '甲'})
    client, kwargs = setup(issues=[issue(1, value)], items=[on_board(1, value, catalog)])
    result = snapshot(**kwargs)
    assert result.data['mismatches'] == []
    assert result.printed == ()


# 驗收 5：候選只收 wf-note 區塊；壞區塊記 invalid、⛔ 不擋。
def test_candidates_and_invalid(setup, catalog):
    note = {'text': '候選一句', 'origin': 'https://github.com/fake/repo/issues/1'}
    comments = {1: [comment(1, 11, 'wf-note', note),
                    comment(1, 12, 'wf-note', None, raw='{壞區塊'),
                    comment(1, 13)]}
    client, kwargs = setup(issues=[issue(1, card())], comments=comments)
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert [c['note'] for c in result.data['candidates']] == [note]
    assert [c['comment_url'] for c in result.data['candidates']] == [comment(1, 11)['url']]
    assert [c['comment_url'] for c in result.data['invalid_candidates']] == [comment(1, 12)['url']]
    assert_read_only(client)


def test_note_failing_schema_is_invalid(setup):
    comments = {1: [comment(1, 11, 'wf-note', {'text': '', 'origin': 'https://x/1'})]}
    _, kwargs = setup(issues=[issue(1, card())], comments=comments)
    result = snapshot(**kwargs)
    assert result.data['candidates'] == []
    assert result.data['invalid_candidates'][0]['reason'].startswith('/text')


# S14b／R1.14-1：wf-note 為 null 的留言仍是候選母體的一員，URL ⛔ 不能消失。
@pytest.mark.parametrize('value', [None, [], 'null', 7])
def test_non_object_note_block_is_invalid_candidate(setup, value):
    comments = {1: [comment(1, 11, 'wf-note', value)]}
    _, kwargs = setup(issues=[issue(1, card())], comments=comments)
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert result.data['candidates'] == []
    assert [c['comment_url'] for c in result.data['invalid_candidates']] == [comment(1, 11)['url']]
    assert '不是物件' in result.data['invalid_candidates'][0]['reason']


def test_null_return_block_does_not_cite(setup):
    comments = {1: [comment(1, 21, 'wf-return', None)]}
    _, kwargs = setup(issues=[issue(1, card())], comments=comments)
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert result.data['last_cited'] == {}


# 驗收 6：last_cited 取最後一次被引用的留言。
def _return(ids):
    return {'card_id': 'WF-001', 'iteration': 1, 'role': 'executor',
            'source_sha': '0' * 40, 'note_responses': [{'id': i, 'value': 'followed'} for i in ids]}


@pytest.mark.parametrize('order', [(0, 1), (1, 0)])
def test_last_cited_takes_latest_comment(setup, order):
    early = comment(1, 21, 'wf-return', _return(['F-PM-01']), created_at='2026-09-01T00:00:00Z')
    late = comment(1, 22, 'wf-return', _return(['F-PM-01', 'F-執行者-03']),
                   created_at='2026-09-05T00:00:00Z')
    rows = [early, late]
    comments = {1: [rows[order[0]], rows[order[1]]]}
    _, kwargs = setup(issues=[issue(1, card())], comments=comments)
    result = snapshot(**kwargs)
    assert result.data['last_cited'] == {
        'F-PM-01': {'card_id': 'WF-001', 'comment_url': late['url'],
                    'created_at': '2026-09-05T00:00:00Z'},
        'F-執行者-03': {'card_id': 'WF-001', 'comment_url': late['url'],
                        'created_at': '2026-09-05T00:00:00Z'}}


def test_last_cited_empty_without_returns(setup):
    _, kwargs = setup(issues=[issue(1, card())], comments={1: [comment(1, 13)]})
    assert snapshot(**kwargs).data['last_cited'] == {}


# 驗收 7：無 Project 設定 ⇒ 對帳整段略過。
def test_no_project_config(setup, catalog):
    _, issues, items = population(catalog)
    client, kwargs = setup(issues=issues, items=items, project=False)
    result = snapshot(**kwargs)
    assert result.rc == 0
    assert result.printed == ('無 Project 設定',)
    assert result.data['mismatches'] == []
    assert result.data['baseline']['project'] is None
    assert [name for name, _ in client.calls if name == 'project'] == []
    assert all(row['projection'] is None for row in result.data['cards'])
    assert_read_only(client)


# 驗收 8：本機兩檔可回讀；Markdown 含每張卡ID；--out 可改目錄。
def test_outputs_are_readable(setup, catalog, tmp_path):
    _, issues, items = population(catalog)
    client, kwargs = setup(issues=issues, items=items)
    result = snapshot(**kwargs)
    written = json.loads((tmp_path / '.wf/snapshot/snapshot.json').read_text(encoding='utf-8'))
    assert written == result.data
    assert written['generated_at'] == NOW
    assert written['baseline'] == {'repo': 'fake/repo', 'project': {'owner': 'fake', 'number': 1}}
    text = (tmp_path / '.wf/snapshot/snapshot.md').read_text(encoding='utf-8')
    missing = [row['card_id'] for row in written['cards'] if row['card_id'] not in text]
    assert missing == []
    print('Markdown 覆蓋卡ID：', len(written['cards']), '缺', len(missing))


def test_run_accepts_out_dir(setup, catalog, tmp_path):
    _, issues, items = population(catalog)
    client, kwargs = setup(issues=issues, items=items)
    target = tmp_path / '別的目錄'
    assert run(['--out', str(target)], client=client, root=kwargs['root'], catalog=catalog) == 0
    assert json.loads((target / 'snapshot.json').read_text(encoding='utf-8'))['cards']
    assert not (tmp_path / '.wf/snapshot').exists()


def test_overwrites_previous_output(setup, catalog, tmp_path):
    _, issues, items = population(catalog)
    _, kwargs = setup(issues=issues, items=items)
    (tmp_path / '.wf/snapshot').mkdir(parents=True)
    (tmp_path / '.wf/snapshot/snapshot.json').write_text('舊內容', encoding='utf-8')
    snapshot(**kwargs)
    assert json.loads((tmp_path / '.wf/snapshot/snapshot.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('break_module, error', [
    # kind 分派類：探針的 schema({}) 那半邊接得住。
    (lambda data: data.__setitem__('enable_if', {'kind': 'typo_kind'}), UnknownEnableKindError),
    # adds 類：啟用集為空時讀不到，非得靠探針的「全部宣告模組」那半邊。
    (lambda data: data['adds'].pop('enums'), KeyError),
])
def test_catalog_defect_raises_before_the_per_card_loop(setup, catalog, tmp_path,
                                                       break_module, error):
    """探針負控：catalog 自身缺陷⛔ 不得被逐卡 except 誤記成每張卡的「卡面不合法」——
    必須在迴圈前炸，且⛔ 不留下任何本機輸出、⛔ 不寫遠端。兩個案例分別打中探針的兩半。
    隱含契約：`is_enabled` 每種 kind 對 `card={}` 必須安全，新 kind ⛔ 不得對 `_field`
    的 None 做包含／空值以外的運算，否則探針會反過來打死健康 repo。"""
    broken = load_blocks(RULES)
    block, = [b for b in broken.by_label('yaml wf-module') if b.data['name'] == 'deploy']
    break_module(block.data)
    _, issues, items = population(catalog)
    client, kwargs = setup(issues=issues, items=items)
    kwargs['catalog'] = broken
    with pytest.raises(error):
        snapshot(**kwargs)
    assert not (tmp_path / '.wf/snapshot/snapshot.json').exists()
    assert_read_only(client)
