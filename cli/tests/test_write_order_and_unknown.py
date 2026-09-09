"""收 astra 複驗開著的兩條（FINAL2-1 順序回歸、FINAL-3 未知不得冒充事實）。

消費 core/verbs.md §2「檢查先於首次遠端寫入：先純計算並驗證新內容，再開始第一次寫」、
同節 D3／D4、對帳與「其餘一律印」，core/card-schema.md §5 `json wf-projection` 的
`max_bytes`，roles/executor.md F-執行者-06（證不出來⛔ 不寫成沒有）。
每條各一正向一負控（roles/conduct-common.md §1）；GitHub 全由既有替身接住，⛔ 不碰網路。
"""
import json
import socket
import subprocess

import pytest

from wf.compose.blocks import load_blocks, projection
from wf.gh.client import GhError
from wf.verbs import _write
from wf.verbs.brief import brief
from wf.verbs.edit import edit
from wf.verbs.review import review

from .test_brief_sections import block, card, make_client, make_root, WRITES
from .test_card_gate_and_projection import RULES, board_client, first_lines, previous_section, rejects, sheet

LOCATION = {'owner': 'fake', 'number': 1}
REWRITE = '重寫投影欄：級別'
LONG_ACTOR = {'role': 'executor', 'actor': 'a' * 1025}  # 投影值 executor:… > max_bytes 1024


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(RULES)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('WRITE_ORDER_NETWORK_DENIED')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(subprocess, 'run', forbidden)
    with pytest.raises(AssertionError, match='WRITE_ORDER_NETWORK_DENIED'):
        subprocess.run(['gh', 'api', 'negative-control'])


# ── FINAL2-1：對帳（會寫投影欄）⛔ 不得搶在完整驗證之前 ────────────────────────
# 三個反例逐字取自 astra 複驗表：卡面 T1／板上 T3，拒收前板上都已變 T1。

CASES = ['review-非法鍵', 'review-branch-null', 'edit-owner-超長']


def case_client(case, catalog):
    """三案共用：板上 T3、卡面 T1（有漂移，對帳一旦跑就會寫板，肉眼可辨）。"""
    if case == 'review-非法鍵':
        return board_client(catalog, card(tier='T1', source_sha='b' * 40))
    if case == 'review-branch-null':
        return board_client(catalog, card(tier='T1', stage='執行', branch=None))
    return board_client(catalog, card(tier='T1'))


def run_case(case, tmp_path, root, client, catalog):
    lines = []
    if case == 'review-非法鍵':
        result = review(10, file=sheet(tmp_path, {'unknown': '非法'}), role='reviewer',
                        client=client, root=root, emit=lines.append)
    elif case == 'review-branch-null':
        result = review(10, file=sheet(tmp_path), role='executor',
                        client=client, root=root, emit=lines.append)
    else:
        result = edit(10, 'owner=' + json.dumps(LONG_ACTOR, ensure_ascii=False), client=client,
                      catalog=catalog, project_owner='fake', project_number=1, emit=lines.append)
    return result, lines


@pytest.mark.parametrize('case', CASES)
def test_no_board_write_happens_before_the_rejection(tmp_path, catalog, case):
    """FINAL2-1 正向：三案 rc≠0、寫入序列只有 ['post_comment']、恰一則 wf:reject、板上仍 T3。"""
    root = make_root(tmp_path)
    client = case_client(case, catalog)
    result, _ = run_case(case, tmp_path, root, client, catalog)
    writes = [name for name, _ in client.calls if name in WRITES]
    assert result.rc != 0, result
    assert writes == ['post_comment'], writes
    assert first_lines(client) == ['wf:reject']
    assert rejects(client)[0]['body'].startswith('拒收・')
    assert client.board['items'][0]['fieldValues']['級別'] == {'name': 'T3'}
    print('FINAL2-1', case, writes, rejects(client)[0]['body'])


def hoist_reconcile(monkeypatch, catalog):
    """負控：把對帳搬回舊版的位置——review 於 check_card 之後就對帳；
    edit 拿掉先算驗證（prepare_card 換成不驗的樁），對帳於是又排到驗證之前。"""
    real = _write.check_card

    def early(card_json, *, client, number, catalog, enabled_modules=(), printed=()):
        failed = real(card_json, client=client, number=number, catalog=catalog,
                      enabled_modules=enabled_modules, printed=printed)
        if failed is None:
            _write.reconcile_projection(
                card_json, client=client, catalog=catalog, location=LOCATION,
                project=client.project('fake', 1, projection(catalog)), number=number,
                report=lambda line: None)
        return failed

    monkeypatch.setattr('wf.verbs.review.check_card', early)
    monkeypatch.setattr('wf.verbs.edit.prepare_card', lambda card_json, *args: (card_json, {}))


@pytest.mark.parametrize('case', CASES)
def test_hoisting_the_reconcile_writes_the_board_before_the_rejection(tmp_path, catalog, case,
                                                                     monkeypatch):
    """FINAL2-1 負控：把對帳搬回驗證之前 ⇒ 同三案在拒收前就寫了板（舊版回歸重現），
    證明上一條擋下的正是這個順序，不是別的東西。"""
    hoist_reconcile(monkeypatch, catalog)
    root = make_root(tmp_path)
    client = case_client(case, catalog)
    result, _ = run_case(case, tmp_path, root, client, catalog)
    writes = [name for name, _ in client.calls if name in WRITES]
    assert result.rc != 0, result
    assert 'write_project_field' in writes, writes  # 對帳走 prepare→write
    assert writes != ['post_comment']
    assert client.board['items'][0]['fieldValues']['級別'] == {'name': 'T1'}
    print('FINAL2-1 負控', case, writes)


@pytest.mark.parametrize('verb', ['review', 'edit'])
def test_valid_input_still_reconciles_the_drifted_column(tmp_path, catalog, verb):
    """FINAL2-1 正控：合法輸入且板上有漂移 ⇒ 仍印「重寫投影欄：級別」且板上修好，rc=0。"""
    root = make_root(tmp_path)
    client = board_client(catalog, card(tier='T1', branch='wf/WF-001', source_sha='b' * 40))
    lines = []
    if verb == 'review':
        result = review(10, file=sheet(tmp_path), role='executor', client=client, root=root,
                        emit=lines.append)
        assert first_lines(client) == ['wf:return']
    else:
        result = edit(10, 'feature="改過"', client=client, catalog=catalog,
                      project_owner='fake', project_number=1, emit=lines.append)
    assert result.rc == 0, result.reason
    assert REWRITE in lines, lines
    assert client.board['items'][0]['fieldValues']['級別'] == {'name': 'T1'}


# ── FINAL-3：候選掃描接例外、非物件前輪區塊＝未知 ────────────────────────────

def boom(**kwargs):
    raise GhError('留言讀取失敗')


def unreadable_client():
    client = make_client(card())
    client.responses['comments'] = boom
    return client


def test_whole_brief_survives_persistently_unreadable_comments(tmp_path):
    """FINAL-3 正向 (a)：整支 brief（不是只對內部函式）在 comments 持續拋 GhError 時
    rc=0、⛔ 不拋例外；候選與前輪兩列都逐字印未能取得，⛔ 不含「無前輪」。"""
    root = make_root(tmp_path, project=False)
    lines = []
    result = brief(10, target='executor', client=unreadable_client(), root=root, emit=lines.append)
    assert result.rc == 0
    assert '未能取得候選：留言讀取失敗' in lines, lines
    assert '未能取得前輪 findings：留言讀取失敗' in lines, lines
    assert '無前輪' not in lines
    print('FINAL-3 (a) rc', result.rc)


def test_without_the_candidate_guard_the_whole_brief_crashes(tmp_path):
    """FINAL-3 負控 (a)：把候選掃描的接例外拿掉 ⇒ 同一輸入整支 brief 直接拋 GhError。"""
    from wf.verbs import notes as notes_module
    guard = notes_module.read_comments
    notes_module.read_comments = lambda client, number, report, label: client.comments(number)
    try:
        root = make_root(tmp_path, project=False)
        with pytest.raises(GhError, match='留言讀取失敗'):
            brief(10, target='executor', client=unreadable_client(), root=root,
                  emit=lambda line: None)
    finally:
        notes_module.read_comments = guard


def comment_with(raw):
    return [{'id': 1, 'url': 'https://example.invalid/c', 'author': 'a',
             'created_at': '2026-09-01T00:00:00Z', 'body': block('wf-return', raw)}]


@pytest.mark.parametrize('raw', ['null', '"text"', '[]'])
def test_non_object_previous_block_is_unknown_not_no_previous(tmp_path, raw):
    """FINAL-3 正向 (b)：前輪區塊存在但值為 null／字串／陣列 ⇒ 各印未能取得，⛔ 不印「無前輪」。"""
    root = make_root(tmp_path, project=False)
    lines = []
    brief(10, target='executor', client=make_client(card(), comments=comment_with(raw)),
          root=root, emit=lines.append)
    assert previous_section(lines) == ['未能取得前輪 findings：wf-return 不是物件'], lines
    assert '無前輪' not in lines


def test_readable_and_genuinely_absent_still_prints_no_previous(tmp_path):
    """FINAL-3 正控 (c)：留言讀得到而真的沒有前輪 ⇒ 仍逐字「無前輪」，
    證明上面兩案的差異來自讀取結果，不是把整列改口。"""
    root = make_root(tmp_path, project=False)
    lines = []
    brief(10, target='executor', client=make_client(card()), root=root, emit=lines.append)
    assert previous_section(lines) == ['無前輪']
    assert not [line for line in lines if line.startswith('未能取得')]
