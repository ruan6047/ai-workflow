"""消費 core/verbs.md §2（重跑身分比對與回讀分流）、§1 review／open／move 列。

A4：同一份交回單、同一 card_id／iteration／role 連跑兩次 `review --file --role <role>`，
第二次⛔ 不新增 `wf-return` 區塊、rc=0，並印一行指出卡上已存在等同交回單；改動任一欄後照常新增。
判定證據只取卡上既有 `wf-return` 區塊（在 `wf.gh.writes.LABELS` 內），⛔ 不讀散文、⛔ 不讀首行。

替身的 `comments()` 具狀態（看得見自己上一跑貼出的留言），否則測的是替身而不是 CLI；
負控之一就是把它換成無狀態的那一版。
"""
import json
from pathlib import Path
import socket
import subprocess

import pytest

from wf.compose.blocks import load_blocks, projection
from wf.gh.client import TransportError
from wf.gh.writes import LABELS, read_block
from wf.verbs._common import field_values
from wf.verbs._write import projected
from wf.verbs.review import IDENTICAL_RETURN, review

from wf.verbs.move import move
from wf.verbs.open import open_issue

from .test_brief_sections import card, make_root
from .test_card_gate_and_projection import board_client
from .test_move_core import MoveClient
from .test_open_verb import MemoryClient, block, expected_card, intake, issue, item
from .test_review_flow import strict_offline

ROOT = Path(__file__).resolve().parents[2]
EXECUTOR = dict(branch='wf/WF-001', source_sha='b' * 40)
ROLES = ('executor', 'reviewer')
PLAN = ['需求', '規劃', '執行', '審核', '結案']
INTAKE = '前言\n' + block('wf-intake', intake())
MUTATIONS = ('add_to_project', 'update_card_body', 'write_project_field',
             'remove_from_project', 'close_issue', 'post_comment')


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(ROOT)


@pytest.fixture(scope='module')
def root(tmp_path_factory):
    return make_root(tmp_path_factory.mktemp('rules'))


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    strict_offline(monkeypatch, 'RESUME_NETWORK_DENIED')
    with pytest.raises(AssertionError, match='RESUME_NETWORK_DENIED'):
        subprocess.run(['gh', 'api', 'negative-control'])
    monkeypatch.setattr(socket.socket, 'connect', lambda *a, **k: (_ for _ in ()).throw(
        AssertionError('RESUME_NETWORK_DENIED')))


def return_blocks(client, number=10):
    """卡上（＝替身存下來的留言）真的存在幾個 `wf-return` 區塊。"""
    assert 'wf-return' in LABELS
    return [read_block(row['body'], 'wf-return', required=False)
            for row in client.stored.get(number, [])
            if read_block(row['body'], 'wf-return', required=False) is not None]


def run_twice(catalog, root, tmp_path, role, *, change=None, stateless=False):
    client = board_client(catalog, card(**EXECUTOR))
    if stateless:  # 負控：替身看不見自己上一跑貼的留言 ⇒ 判定沒有讀遠端就會照樣收斂
        client.responses['comments'] = []
    path = tmp_path / f'return-{role}.json'
    path.write_text(json.dumps({}, ensure_ascii=False), encoding='utf-8')
    first, second = [], []
    firstrun = review(10, file=path, role=role, client=client, root=root, emit=first.append)
    if change is not None:
        path.write_text(json.dumps(change, ensure_ascii=False), encoding='utf-8')
    secondrun = review(10, file=path, role=role, client=client, root=root, emit=second.append)
    return client, (firstrun, first), (secondrun, second)


@pytest.mark.parametrize('role', ROLES)
def test_identical_return_is_not_posted_twice(catalog, root, tmp_path, role):
    client, (first, _), (second, lines) = run_twice(catalog, root, tmp_path, role)
    assert first.rc == 0 and second.rc == 0
    blocks = return_blocks(client)
    assert len(blocks) == 1, blocks
    assert IDENTICAL_RETURN in lines, lines
    posted = [kwargs['first_line'] for name, kwargs in client.calls if name == 'post_comment']
    assert posted == ['wf:return' if role == 'executor' else 'wf:verdict'], posted
    print('RERUN_CONVERGES', role, '| wf-return 區塊數', len(blocks), '| rc', first.rc, second.rc,
          '| 第二跑', json.dumps([line for line in lines if line == IDENTICAL_RETURN],
                              ensure_ascii=False))


@pytest.mark.parametrize('role', ROLES)
def test_changed_return_is_posted_again(catalog, root, tmp_path, role):
    """負控①：改動交回單任一欄之後的第二跑必須照常新增區塊。"""
    client, _, (second, lines) = run_twice(catalog, root, tmp_path, role,
                                           change={'mistakes': [{'what': '改過一欄', 'when': '第二跑',
                                                                  'impact': '無', 'fix': '無'}]})
    assert second.rc == 0
    blocks = return_blocks(client)
    assert len(blocks) == 2, blocks
    assert IDENTICAL_RETURN not in lines, lines
    print('RERUN_DIFFERS', role, '| wf-return 區塊數', len(blocks))


@pytest.mark.parametrize('role', ROLES)
def test_stateless_comments_break_the_convergence(catalog, root, tmp_path, role):
    """負控②：把替身換成無狀態 `comments()` 之後，第二跑必須照常新增區塊——
    若仍收斂，代表判定沒有讀遠端，測具無效。"""
    client, _, (second, lines) = run_twice(catalog, root, tmp_path, role, stateless=True)
    assert second.rc == 0
    blocks = return_blocks(client)
    assert len(blocks) == 2, blocks
    assert IDENTICAL_RETURN not in lines, lines
    print('RERUN_STATELESS', role, '| wf-return 區塊數', len(blocks))


# ── A5：`open` D2 與 `move` D1 的回讀分流 ──────────────────────────────────────

def written(client):
    return [name for name, _ in client.calls if name in MUTATIONS]


def board_item(catalog, filled=None):
    """板上那一項。filled 給定＝把五個投影欄填成該卡的投影值（上一次已整批寫完）；
    None＝五欄留空（上一次只完成 add_to_project／卡面 JSON，投影欄還沒寫）。
    形狀走 `_common.field_values` 讀得懂的 `{'text': …}`／None，⛔ 不另造一套投影欄形狀。"""
    entry = item(10)
    if filled is not None:
        entry['fieldValues'] = {name: None if value is None else {'text': value}
                                for name, value in projected(filled, catalog).items()}
    return entry


def open_on_board(catalog, root, body, filled=None):
    """卡已在板上（item 已存在）時跑一次 `open`，回 (client, result, 印項)。"""
    client = MemoryClient(catalog, [issue(10, body=body)], [board_item(catalog, filled)])
    lines = []
    return client, open_issue(10, client=client, root=root, catalog=catalog, emit=lines.append), lines


EQUAL = expected_card()
# 四組：回讀證據面＝卡面 `wf-card` 區塊 ∧ 五個投影欄（A5「本次 write plan 中每一個已宣告原語
# 各自的可回讀狀態」）。(戊) 是查核序 1 finding WF-016-R1.1-001 的形狀：卡面已寫成、投影欄仍為空。
CASES = {
    '甲・板上而卡面無 wf-card': (INTAKE, None, 0, ''),
    '乙・板上而卡面與五個投影欄都與本次 plan 全等': (block('wf-card', EQUAL), EQUAL, 0, ''),
    '丙・板上而卡面已被推進': (block('wf-card', expected_card(stage='規劃', state='待辦')), None, 1, '已在板上'),
    '戊・板上而卡面全等、五個投影欄尚未寫完': (block('wf-card', EQUAL), None, 0, ''),
}


@pytest.mark.parametrize('name', list(CASES))
def test_open_d2_branches_on_card_readback(catalog, root, name):
    body, filled, rc, reason = CASES[name]
    client, result, lines = open_on_board(catalog, root, body, filled)
    assert (result.rc, result.reason) == (rc, reason), (name, result)
    if name.startswith('丙'):
        assert written(client) == ['post_comment'], written(client)    # 只有那一則 wf:reject 留痕
    elif name.startswith('乙'):
        assert written(client) == [], (name, written(client))          # 全等＝收斂、⛔ 不重寫
        assert result.completed_writes, result
    elif name.startswith('戊'):
        # 卡面全等但五欄還沒寫完 ⇒ 回讀是 plan 的前綴：續作剩餘的投影欄寫入，⛔ 不判收斂。
        assert 'add_to_project' not in written(client), written(client)
        assert written(client).count('write_project_field') == len(projection(catalog)), written(client)
        assert any(entry.startswith('add_to_project') for entry in result.completed_writes), result
        assert any(entry.startswith('update_card_body') for entry in result.completed_writes), result
    else:
        assert 'add_to_project' not in written(client), written(client)  # 續作＝⛔ 不重複加板
        assert 'update_card_body' in written(client), written(client)
        assert any(entry.startswith('add_to_project') for entry in result.completed_writes), result
    print('OPEN_D2', name, '| rc', result.rc, '| reason', repr(result.reason),
          '| completed_writes', json.dumps(list(getattr(result, 'completed_writes', ())),
                                           ensure_ascii=False),
          '| 卡面回讀', json.dumps(read_block(client.rows[10]['body'], 'wf-card', required=False) is not None),
          '| 投影欄回讀', json.dumps(field_values(client.board['items'][0]), ensure_ascii=False),
          '| 寫入', json.dumps(written(client)))


def test_open_d2_cases_do_not_collapse_into_one_verdict(catalog, root):
    """A5 負控：四組的 (rc, reason, 寫入序列) ⛔ 不得全等——基線上實測三例都是 (1, '已在板上')，
    全等即代表分流沒生效。"""
    verdicts = []
    for name, (body, filled, _, _) in CASES.items():
        client, result, _ = open_on_board(catalog, root, body, filled)
        verdicts.append((result.rc, result.reason, tuple(written(client))))
    assert len(set(verdicts)) > 1, verdicts
    print('OPEN_D2_VERDICTS', json.dumps([[rc, reason, list(seq)] for rc, reason, seq in verdicts],
                                         ensure_ascii=False))


def test_open_d2_converges_only_when_the_projection_is_also_equal(catalog, root):
    """A5 負控（查核序 1 finding WF-016-R1.1-001）：(乙)(戊) 只差在五個投影欄有沒有寫完，
    兩者的寫入序列⛔ 不得相同——相同即代表投影欄沒被讀進完成判定。"""
    equal, equal_result, _ = open_on_board(catalog, root, block('wf-card', EQUAL), EQUAL)
    prefix, prefix_result, _ = open_on_board(catalog, root, block('wf-card', EQUAL), None)
    assert written(equal) == [], written(equal)
    assert written(prefix) != [], written(prefix)
    assert field_values(prefix.board['items'][0]) == projected(EQUAL, catalog), (
        field_values(prefix.board['items'][0]))
    print('OPEN_D2_PROJECTION_EVIDENCE | 五欄全等', json.dumps(written(equal)),
          '| 五欄未寫完', json.dumps(written(prefix)),
          '| rc', equal_result.rc, prefix_result.rc)


def move_case(catalog, root, *, drift=False):
    current = expected_card(stage='執行', state='進行中', stage_plan=PLAN, iteration=7,
                            owner={'role': 'executor', 'actor': 'old'}, source_sha='a' * 40,
                            branch='old/branch')
    client = MoveClient(catalog, current)
    if drift:  # 上一次只寫完卡面 JSON，五個投影欄還沒整批寫完
        client.board['items'][0]['fieldValues']['級別'] = {'name': 'T3'}
    lines = []
    return client, lines, current


def test_move_d1_converges_when_the_card_face_is_already_the_target(catalog, root):
    """重跑 `move --to <卡面已在的節點>`：回讀與本次目標全等 ⇒ rc=0 收斂、零遠端寫入。"""
    client, lines, _ = move_case(catalog, root)
    result = move(10, '執行/進行中', client=client, root=root, catalog=catalog, emit=lines.append)
    assert result.rc == 0 and written(client) == [], (result, written(client))
    assert result.completed_writes and any('update_card_body' in e for e in result.completed_writes)
    assert any('收斂' in line for line in lines), lines
    print('MOVE_D1_CONVERGE rc', result.rc, '| completed_writes',
          json.dumps(list(result.completed_writes), ensure_ascii=False), '|', json.dumps(lines, ensure_ascii=False))


def test_move_d1_resumes_the_remaining_projection_writes(catalog, root):
    """同一重跑但投影欄還沒整批寫完：回讀是本次 plan 的前綴 ⇒ 續作剩餘寫入並列出已完成項。"""
    client, lines, _ = move_case(catalog, root, drift=True)
    result = move(10, '執行/進行中', client=client, root=root, catalog=catalog, emit=lines.append)
    assert result.rc == 0
    assert written(client) == ['write_project_field'], written(client)
    assert [e for e in result.completed_writes if e.startswith('write_project_field')], result
    assert any(line.startswith('續作剩餘寫入・投影欄：') for line in lines), lines
    print('MOVE_D1_RESUME rc', result.rc, '| completed_writes',
          json.dumps(list(result.completed_writes), ensure_ascii=False), '|', json.dumps(lines, ensure_ascii=False))


def test_move_d1_keeps_the_baseline_refusal_for_a_real_illegal_edge(catalog, root):
    """A5 負控：卡面回讀不是本次目標時，D1 的編號與逐字理由維持基線。"""
    client, lines, _ = move_case(catalog, root)
    result = move(10, '結案/完成', client=client, root=root, catalog=catalog, emit=lines.append)
    assert result.rc == 1 and result.reason == '執行/進行中 → 結案/完成 不在合成表內', result
    assert written(client) == ['post_comment'], written(client)   # 只有那一則 wf:reject
    print('MOVE_D1_REFUSE', repr(result.reason))


# ── A5（丁）：終態 `move` 的第三個合取項——承載 issue 的 state 必須為 `closed` ─────────

def terminal_move_case(catalog, root, *, closed=False, client_class=MoveClient):
    """終態 `move` 重跑：卡面 `wf-card` 已是 結案/完成、五個投影欄也已寫成，差別只在承載 issue。
    closed=False＝上一次 `close_issue` 之前失敗（issue 仍 open）；True＝上一次已整批完成。"""
    current = expected_card(stage='結案', state='完成', stage_plan=PLAN, iteration=7,
                            owner={'role': 'executor', 'actor': 'old'}, source_sha='a' * 40,
                            branch='old/branch')
    client = client_class(catalog, current)
    if closed:
        client.rows[10]['state'] = 'closed'
    return client, []


def test_terminal_move_resumes_close_issue_when_the_issue_is_still_open(catalog, root):
    """(丁)：卡面與五欄全等而承載 issue 仍為 open ⇒ ⛔ 不得判收斂，一律判為 plan 的前綴並續作
    `close_issue`。依查核序 1 finding WF-016-R1.1-002 逐字「現行規劃把完成條件縮成卡面與投影
    而漏掉尚未完成的 close」。"""
    client, lines = terminal_move_case(catalog, root)
    assert client.issue_is_open(10) is True
    result = move(10, '結案/完成', client=client, root=root, catalog=catalog, emit=lines.append)
    assert result.rc == 0, (result, lines)
    assert written(client) == ['close_issue'], written(client)
    assert client.issue_is_open(10) is False, '替身的 issue state 必須具狀態，否則測的是替身'
    assert any(e.startswith('update_card_body') for e in result.completed_writes), result
    assert any(e.startswith('close_issue') for e in result.completed_writes), result
    print('MOVE_TERMINAL_RESUME rc', result.rc, '| issue state 回讀 open',
          '| completed_writes', json.dumps(list(result.completed_writes), ensure_ascii=False),
          '|', json.dumps(lines, ensure_ascii=False))


def test_terminal_move_converges_when_the_issue_is_already_closed(catalog, root):
    """A5 負控①：把 (丁) 的前置改成 issue 已為 `closed` 後重跑，必須判 rc=0 收斂且該次⛔ 不再
    呼叫 `close_issue`。"""
    client, lines = terminal_move_case(catalog, root, closed=True)
    assert client.issue_is_open(10) is False
    result = move(10, '結案/完成', client=client, root=root, catalog=catalog, emit=lines.append)
    assert result.rc == 0 and written(client) == [], (result, written(client))
    assert any('收斂' in line for line in lines), lines
    print('MOVE_TERMINAL_CONVERGE rc', result.rc, '| issue state 回讀 closed',
          '| completed_writes', json.dumps(list(result.completed_writes), ensure_ascii=False),
          '|', json.dumps(lines, ensure_ascii=False))


def test_terminal_move_open_and_closed_do_not_collapse(catalog, root):
    """A5 負控①（續）：兩種前置若得到相同的 (rc, completed_writes)，代表 issue 狀態沒被讀進判定。"""
    still_open, lines = terminal_move_case(catalog, root)
    first = move(10, '結案/完成', client=still_open, root=root, catalog=catalog, emit=lines.append)
    already, other = terminal_move_case(catalog, root, closed=True)
    second = move(10, '結案/完成', client=already, root=root, catalog=catalog, emit=other.append)
    assert (first.rc, tuple(first.completed_writes)) != (second.rc, tuple(second.completed_writes))
    print('MOVE_TERMINAL_VERDICTS | open', json.dumps(
        [first.rc, list(first.completed_writes), written(still_open)], ensure_ascii=False),
          '| closed', json.dumps(
        [second.rc, list(second.completed_writes), written(already)], ensure_ascii=False))


def test_terminal_move_negative_control_issue_is_open_pinned_true(catalog, root, monkeypatch):
    """A5 負控②：把替身的 `issue_is_open` 改為恆 `True` 之後，(丁) 的收斂案例（前置 `closed`）
    必須轉紅——本測試逐字記下該變異下收斂斷言不再成立（改呼叫 `close_issue`）。
    仍收斂即代表判定沒讀 issue state。"""
    monkeypatch.setattr(MoveClient, 'issue_is_open', lambda self, number: True)
    client, lines = terminal_move_case(catalog, root, closed=True)
    result = move(10, '結案/完成', client=client, root=root, catalog=catalog, emit=lines.append)
    assert written(client) == ['close_issue'], written(client)
    print('MOVE_TERMINAL_MUTATION issue_is_open≡True | rc', result.rc,
          '| 寫入', json.dumps(written(client)))


class CloseFailsClient(MoveClient):
    """`close_issue` 一律拋 TransportError：續作 `close_issue` 再失敗的那一條路。"""

    def close_issue(self, number):
        raise TransportError(f'injected TransportError at close_issue #{number}')


def test_terminal_move_reports_the_receipt_when_close_issue_fails_again(catalog, root):
    """(丁) 續作時 `close_issue` 本身再失敗：rc≠0，`completed_writes` 列出回讀證據確認已完成的
    `update_card_body`，`next_action` 指出 issue 尚未關閉且需重跑同一 `move`。"""
    client, lines = terminal_move_case(catalog, root, client_class=CloseFailsClient)
    result = move(10, '結案/完成', client=client, root=root, catalog=catalog, emit=lines.append)
    assert result.rc != 0 and result.error_kind == 'transport', result
    assert any(e.startswith('update_card_body') for e in result.completed_writes), result
    assert not any(e.startswith('close_issue') for e in result.completed_writes), result
    assert 'issue 尚未關閉' in result.next_action and 'move' in result.next_action, result
    print('MOVE_TERMINAL_CLOSE_FAILS rc', result.rc, '| completed_writes',
          json.dumps(list(result.completed_writes), ensure_ascii=False),
          '| next_action', result.next_action)


def test_previously_confirmed_projection_remains_in_close_retry_receipt(catalog, root):
    """查核序 2 finding WF-016-R1.1-002 的形狀：同一終態操作**連續兩次** `close_issue` 失敗。

    第二跑走 `_ops.move_resume`（卡面已是本次目標 ⇒ 轉移不合法而 from==to），此時五個投影欄的
    回讀證據已經與卡面全等（第一跑寫成的），本次因此零投影寫入。A5 逐字要的是「已完成的前綴」
    ——`completed_writes` 必須列出回讀證據確認已完成的 `update_card_body` **與五個
    `write_project_field`**，⛔ 不是只列本次已完成的那些。
    """
    current = expected_card(stage='結案', state='待確認', stage_plan=PLAN, iteration=7,
                            owner={'role': 'executor', 'actor': 'old'}, source_sha='a' * 40,
                            branch='old/branch')
    client = CloseFailsClient(catalog, current)
    first_lines, second_lines = [], []
    first = move(10, '結案/完成', client=client, root=root, catalog=catalog, emit=first_lines.append)
    first_writes = written(client)
    assert first.rc != 0 and first.error_kind == 'transport', (first, first_lines)
    assert first_writes.count('write_project_field') == len(projection(catalog)), first_writes
    client.calls.clear()
    second = move(10, '結案/完成', client=client, root=root, catalog=catalog, emit=second_lines.append)
    second_writes = written(client)
    assert second.rc != 0 and second.error_kind == 'transport', (second, second_lines)
    assert client.issue_is_open(10) is True, '替身的 issue state 必須具狀態'
    assert second_writes == [], second_writes          # 本次零寫入：卡面與五欄回讀都已全等
    fields = [entry for entry in second.completed_writes if entry.startswith('write_project_field')]
    assert any(entry.startswith('update_card_body') for entry in second.completed_writes), second
    assert len(fields) == len(projection(catalog)), (fields, second.completed_writes)
    assert not any(entry.startswith('close_issue') for entry in second.completed_writes), second
    print('MOVE_TERMINAL_CLOSE_RETRY | 第一跑 completed_writes',
          json.dumps(list(first.completed_writes), ensure_ascii=False),
          '| 第一跑寫入', json.dumps(first_writes),
          '| 第二跑 completed_writes', json.dumps(list(second.completed_writes), ensure_ascii=False),
          '| 第二跑寫入', json.dumps(second_writes),
          '| next_action', second.next_action)
