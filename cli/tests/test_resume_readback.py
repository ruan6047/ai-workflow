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

from wf.compose.blocks import load_blocks
from wf.gh.writes import LABELS, read_block
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


def open_on_board(catalog, root, body):
    """卡已在板上（item 已存在）時跑一次 `open`，回 (client, result, 印項)。"""
    client = MemoryClient(catalog, [issue(10, body=body)], [item(10)])
    lines = []
    return client, open_issue(10, client=client, root=root, catalog=catalog, emit=lines.append), lines


# (甲)(乙)(丙) 三組：卡面回讀分別是「無 wf-card」「與本次 plan 全等」「stage／state 不是本次目標」
CASES = {
    '甲・板上而卡面無 wf-card': (INTAKE, 0, ''),
    '乙・板上而卡面與本次 plan 全等': (block('wf-card', expected_card()), 0, ''),
    '丙・板上而卡面已被推進': (block('wf-card', expected_card(stage='規劃', state='待辦')), 1, '已在板上'),
}


@pytest.mark.parametrize('name', list(CASES))
def test_open_d2_branches_on_card_readback(catalog, root, name):
    body, rc, reason = CASES[name]
    client, result, lines = open_on_board(catalog, root, body)
    assert (result.rc, result.reason) == (rc, reason), (name, result)
    if name.startswith('丙'):
        assert written(client) == ['post_comment'], written(client)    # 只有那一則 wf:reject 留痕
    elif name.startswith('乙'):
        assert written(client) == [], (name, written(client))          # 全等＝收斂、⛔ 不重寫
        assert result.completed_writes, result
    else:
        assert 'add_to_project' not in written(client), written(client)  # 續作＝⛔ 不重複加板
        assert 'update_card_body' in written(client), written(client)
        assert any(entry.startswith('add_to_project') for entry in result.completed_writes), result
    print('OPEN_D2', name, '| rc', result.rc, '| reason', repr(result.reason),
          '| completed_writes', json.dumps(list(getattr(result, 'completed_writes', ())),
                                           ensure_ascii=False),
          '| 卡面回讀', json.dumps(read_block(client.rows[10]['body'], 'wf-card', required=False) is not None),
          '| 寫入', json.dumps(written(client)))


def test_open_d2_cases_do_not_collapse_into_one_verdict(catalog, root):
    """A5 負控：三組的 (rc, reason) ⛔ 不得全等——基線上實測三例都是 (1, '已在板上')，
    全等即代表分流沒生效。"""
    verdicts = []
    for name, (body, _, _) in CASES.items():
        _, result, _ = open_on_board(catalog, root, body)
        verdicts.append((result.rc, result.reason))
    assert len(set(verdicts)) > 1, verdicts
    print('OPEN_D2_VERDICTS', json.dumps(verdicts, ensure_ascii=False))


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
