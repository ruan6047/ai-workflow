"""收 astra 複驗 FINAL4-1：共用對帳在首次遠端寫入前驗投影值的 max_bytes。

消費 core/card-schema.md §5 `json wf-projection`（TEXT 欄 max_bytes，UTF-8 位元組）、
core/verbs.md §2 D3（投影 TEXT 欄超過 max_bytes）與「檢查先於首次遠端寫入」。
反例逐字取自 astra 複驗：舊卡 `owner.actor` = 'x'*1025 ⇒ 投影 `executor:`＋actor 共 1034 位元組；
新 owner 合法（`executor:new`，12 位元組）。每條各一正向一負控（roles/conduct-common.md §1）；
GitHub 全由既有替身接住，⛔ 不碰網路。
"""
import socket
import subprocess

import pytest

from wf.compose.blocks import load_blocks
from wf.verbs import _write
from wf.verbs.edit import edit
from wf.verbs.move import move
from wf.verbs.snapshot import snapshot

from .test_brief_sections import card, make_root, WRITES
from .test_card_gate_and_projection import RULES, board_client, first_lines, rejects, run_verb

OVERSIZED = {'role': 'executor', 'actor': 'x' * 1025}  # 投影值＝'executor:' + actor
OVERSIZED_BYTES = 1034
# 板上：owner 還空著，階段／級別與卡面不同 ⇒ 對帳一動手就會把超限 owner 送上板。
BOARD = {'階段': {'name': '規劃'}, '狀態': {'name': '待辦'}, '級別': {'name': 'T1'},
         'owner': None, '卡ID': {'text': 'WF-001'}}
PLAN = ['需求', '執行', '審核', '結案']
VERBS = ['review', 'notes', 'brief', 'edit', 'move']


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(RULES)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('PROJECTION_NETWORK_DENIED')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(subprocess, 'run', forbidden)
    with pytest.raises(AssertionError, match='PROJECTION_NETWORK_DENIED'):
        subprocess.run(['gh', 'api', 'negative-control'])


@pytest.fixture
def without_the_length_check(monkeypatch):
    """負控：把長度檢查拿掉＝換回被審版本的 projected（只組值、不驗 max_bytes），其餘一律不動。"""
    original = _write.projected
    monkeypatch.setattr(_write, 'projected',
                        lambda card_json, catalog, check=False: original(card_json, catalog))


def oversized_client(catalog, verb):
    """卡面舊 owner 已超限；`move` 要走派工邊，故卡面狀態用「待辦」。"""
    state = '待辦' if verb == 'move' else '進行中'
    return board_client(catalog, card(owner=OVERSIZED, state=state, stage_plan=PLAN,
                                      branch='wf/WF-001', source_sha='b' * 40), dict(BOARD))


def run_one(verb, tmp_path, root, client, catalog):
    lines = []
    if verb == 'edit':
        return edit(10, ['feature="改過"'], client=client, catalog=catalog, project_owner='fake',
                    project_number=1, emit=lines.append), lines
    if verb == 'move':  # 派工邊 執行/待辦 → 執行/進行中，--actor 給的新 owner 合法
        return move(10, '執行/進行中', client=client, root=root, catalog=catalog,
                    actor='executor:new', emit=lines.append), lines
    return run_verb(verb, tmp_path, root, client)


def field_writes(client):
    """每次投影欄寫入送出的值（None＝清空）；用來抓「超限值是否真的上了板」。"""
    return [prepared[2].get('value', {}).get('text') for name, prepared in client.calls
            if name == 'write_project_field']


def test_the_reference_owner_projects_to_1034_bytes():
    """反例自算：位元組數由字面算出，⛔ 不引用複驗報告裡的數字當權威。"""
    projected = f"{OVERSIZED['role']}:{OVERSIZED['actor']}"
    assert len(projected.encode('utf-8')) == OVERSIZED_BYTES
    print('OVERSIZED_BYTES', len(projected.encode('utf-8')))


# ── FINAL4-1 正向：超限舊投影值 ⇒ 零業務寫入的單一 D3 拒收 ──────────────────

@pytest.mark.parametrize('verb', VERBS)
def test_an_oversized_old_owner_is_rejected_before_the_first_write(tmp_path, catalog, verb):
    """正向：五支動詞各 rc≠0、寫入序列只有 ['post_comment']、恰一則帶欄名的 wf:reject，
    且板上五欄一格都沒被改。"""
    root = make_root(tmp_path)
    client = oversized_client(catalog, verb)
    result, _ = run_one(verb, tmp_path, root, client, catalog)
    writes = [name for name, _ in client.calls if name in WRITES]
    body = rejects(client)[0]['body']
    assert result.rc != 0, result
    assert writes == ['post_comment'], writes
    assert first_lines(client) == ['wf:reject']
    assert body.startswith('拒收・D3・') and 'owner' in body and 'max_bytes' in body, body
    assert client.board['items'][0]['fieldValues'] == BOARD
    print('FINAL4-1', verb, writes, body)


@pytest.mark.parametrize('verb', VERBS)
def test_without_the_length_check_the_oversized_owner_reaches_the_board(
        tmp_path, catalog, verb, without_the_length_check):
    """負控：拿掉長度檢查 ⇒ 同一輸入重現 1034 位元組的 owner 被寫上板，上一條必 FAIL。"""
    root = make_root(tmp_path)
    client = oversized_client(catalog, verb)
    run_one(verb, tmp_path, root, client, catalog)
    writes = [name for name, _ in client.calls if name in WRITES]
    sizes = [len(value.encode('utf-8')) for value in field_writes(client) if isinstance(value, str)]
    assert writes != ['post_comment'], writes
    assert OVERSIZED_BYTES in sizes, sizes
    print('FINAL4-1 負控', verb, writes[:3], sizes)


# ── 正控：owner 合法時，同一組漂移照舊對帳重寫並印 ────────────────────────────

@pytest.mark.parametrize('verb', VERBS)
def test_a_legal_owner_still_lets_the_whole_drift_reconcile(tmp_path, catalog, verb):
    """正控：owner 換成合法值（其餘完全相同）⇒ rc=0、對帳照舊把 owner 重寫上板，
    證明擋下來的是長度、不是把對帳整個關掉。"""
    root = make_root(tmp_path)
    state = '待辦' if verb == 'move' else '進行中'
    client = board_client(catalog, card(owner={'role': 'executor', 'actor': '甲'}, state=state,
                                        stage_plan=PLAN, branch='wf/WF-001', source_sha='b' * 40),
                          dict(BOARD))
    result, lines = run_one(verb, tmp_path, root, client, catalog)
    assert result.rc == 0, result.reason
    assert [line for line in lines if line.startswith('重寫投影欄：')], lines
    # move 之後另由 write_card 依 --actor 改寫成 executor:new，故看對帳當下送出的值。
    assert 'executor:甲' in field_writes(client), field_writes(client)
    print('FINAL4-1 正控', verb, field_writes(client),
          [line for line in lines if line.startswith('重寫投影欄：')])


# ── §2 末句的 snapshot 例外：唯讀對帳仍只印，長度門檻 ⛔ 不落在讀路徑上 ─────────

def test_snapshot_still_only_prints_the_oversized_projection(tmp_path, catalog):
    """驗收 4：同一張超限舊卡＋同一組漂移，`snapshot` 仍 rc=0、零遠端寫入、只印不等。"""
    root = make_root(tmp_path)
    client = oversized_client(catalog, 'snapshot')
    lines = []
    result = snapshot(client=client, root=root, catalog=catalog, out=tmp_path / 'out',
                      emit=lines.append)
    assert result.rc == 0, result
    assert [name for name, _ in client.calls if name in WRITES] == []
    assert client.board['items'][0]['fieldValues'] == BOARD
    assert [line for line in lines if line.startswith('WF-001 owner：')], lines
    print('驗收 4 snapshot', result.rc, [line for line in lines if 'owner' in line][0][:40])


def test_gating_the_read_path_would_break_the_snapshot_exception(tmp_path, catalog, monkeypatch):
    """驗收 4 負控：把長度門檻也套到唯讀對帳（projected 恆 check=True）⇒ snapshot 改成拒收，
    上一條必 FAIL；證明 check 旗標的預設值正是 §2 snapshot 例外的所在。"""
    original = _write.projected
    monkeypatch.setattr(_write, 'projected',
                        lambda card_json, catalog, check=False: original(card_json, catalog, True))
    monkeypatch.setattr('wf.verbs.snapshot.projected', lambda card_json, catalog: original(
        card_json, catalog, True))
    root = make_root(tmp_path)
    client = oversized_client(catalog, 'snapshot')
    with pytest.raises(ValueError, match='owner 超過 max_bytes'):
        snapshot(client=client, root=root, catalog=catalog, out=tmp_path / 'out',
                 emit=lambda line: None)
    print('驗收 4 負控 snapshot 讀路徑套門檻即炸')
