"""S18：收 astra 複驗 FINAL3-1（共用對帳先寫後驗）。

消費 core/verbs.md §2「檢查先於首次遠端寫入：先純計算並驗證新內容，再開始第一次寫」、
同節「下一次動詞先對帳……不等＝以卡面 JSON 重寫該欄」與 D3、
core/card-schema.md §5 `json wf-projection`（欄名↔卡面鍵）、core/enums.md `tiers`。
反例逐字取自 astra 複驗表：卡面 stage／state 相對板上已漂移、板上第三欄「級別」缺 T1 選項。
每條各一正向一負控（roles/conduct-common.md §1）；GitHub 全由既有替身接住，⛔ 不碰網路。
"""
import socket
import subprocess

import pytest

from wf.compose.blocks import load_blocks, projection
from wf.compose.validate import _equal
from wf.gh.writes import WriteMixin
from wf.verbs import _write
from wf.verbs.edit import edit

from .test_brief_sections import card, make_root, WRITES
from .test_s16_contract import RULES, board_client, first_lines, rejects, run_verb

# 板上：階段／狀態與卡面（執行／進行中）不同，級別 T3 與卡面 T1 不同 ⇒ 三欄都要重寫。
DRIFTED = {'階段': {'name': '規劃'}, '狀態': {'name': '待辦'}, '級別': {'name': 'T3'},
           'owner': None, '卡ID': {'text': 'WF-001'}}
VERBS = ['review', 'notes', 'brief', 'edit']


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(RULES)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('S18_NETWORK_DENIED')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(subprocess, 'run', forbidden)
    with pytest.raises(AssertionError, match='S18_NETWORK_DENIED'):
        subprocess.run(['gh', 'api', 'negative-control'])


def drifted_client(catalog, *, tier_options=True):
    """卡面 T1／板上 T3 且階段、狀態同時漂移；tier_options=False ⇒ 板上級別缺 T1 選項。"""
    client = board_client(catalog, card(tier='T1', branch='wf/WF-001', source_sha='b' * 40),
                          dict(DRIFTED))
    if not tier_options:
        client.options['級別'] = [o for o in client.options['級別'] if o['name'] != 'T1']
    return client


def run_one(verb, tmp_path, root, client, catalog):
    if verb != 'edit':
        return run_verb(verb, tmp_path, root, client)
    lines = []
    return edit(10, 'feature="改過"', client=client, catalog=catalog, project_owner='fake',
                project_number=1, emit=lines.append), lines


def legacy_reconcile(card_json, *, client, catalog, project_owner, project_number, item_id):
    """負控：S17 之前的逐欄邊算邊寫（＝astra FINAL3-1 的反例來源），走正式的
    WriteMixin.set_project_field＝prepare 完一欄就寫一欄。"""
    project = client.project(project_owner, project_number, projection(catalog))
    actual = _write.projection_values(project, item_id)
    changed = []
    for name, value in _write.projected(card_json, catalog).items():
        if not _equal(actual.get(name), value):
            WriteMixin.set_project_field(client, project, item_id, name, value)
            changed.append(name)
    return changed


# ── FINAL3-1 正向：欄算不出 ⇒ 零業務寫入、單一 D3 拒收 ────────────────────────

@pytest.mark.parametrize('verb', VERBS)
def test_unresolvable_projection_column_writes_nothing_before_the_rejection(tmp_path, catalog, verb):
    """正向：板上級別缺 T1 選項 ⇒ 四支動詞 rc≠0、寫入序列只有 ['post_comment']、
    恰一則 wf:reject，且板上三欄（含已漂移的階段／狀態）一格都沒被改。"""
    root = make_root(tmp_path)
    client = drifted_client(catalog, tier_options=False)
    result, _ = run_one(verb, tmp_path, root, client, catalog)
    writes = [name for name, _ in client.calls if name in WRITES]
    assert result.rc != 0, result
    assert writes == ['post_comment'], writes
    assert first_lines(client) == ['wf:reject']
    assert rejects(client)[0]['body'].startswith('拒收・D3・')
    if verb != 'edit':  # 三支走共用對帳，拒收本文要指出是哪一欄算不出
        assert '級別' in rejects(client)[0]['body'], rejects(client)[0]['body']
    assert client.board['items'][0]['fieldValues'] == DRIFTED
    print('S18 FINAL3-1', verb, writes, rejects(client)[0]['body'])


@pytest.mark.parametrize('verb', ['review', 'notes', 'brief'])
def test_writing_each_column_as_it_is_resolved_breaks_the_same_three_cases(tmp_path, catalog, verb,
                                                                          monkeypatch):
    """負控：把「先算」拿掉（換回逐欄邊算邊寫）⇒ 同一輸入在拒收前就寫了板，
    重現 ['write_project_field', 'write_project_field', …]，上一條的斷言必 FAIL。"""
    monkeypatch.setattr(_write, 'reconcile', legacy_reconcile)
    root = make_root(tmp_path)
    client = drifted_client(catalog, tier_options=False)
    result, _ = run_one(verb, tmp_path, root, client, catalog)
    writes = [name for name, _ in client.calls if name in WRITES]
    assert result.rc != 0, result
    assert writes[:2] == ['write_project_field', 'write_project_field'], writes
    assert writes != ['post_comment']
    assert client.board['items'][0]['fieldValues']['階段'] == {'name': '執行'}
    print('S18 FINAL3-1 負控', verb, writes)


# ── 正控：欄都解析得出時，對帳照舊重寫並印 ──────────────────────────────────

@pytest.mark.parametrize('verb', VERBS)
def test_resolvable_columns_still_reconcile_the_whole_drift(tmp_path, catalog, verb):
    """正控：同一組漂移、級別選項齊全 ⇒ rc=0、印「重寫投影欄：階段、狀態、級別」、板上修好，
    證明上面兩條擋下的是「算不出」，不是把對帳整個關掉。"""
    root = make_root(tmp_path)
    client = drifted_client(catalog)
    result, lines = run_one(verb, tmp_path, root, client, catalog)
    assert result.rc == 0, result.reason
    assert '重寫投影欄：階段、狀態、級別' in lines, lines
    assert client.board['items'][0]['fieldValues']['級別'] == {'name': 'T1'}
    assert client.board['items'][0]['fieldValues']['階段'] == {'name': '執行'}
    assert client.board['items'][0]['fieldValues']['狀態'] == {'name': '進行中'}
