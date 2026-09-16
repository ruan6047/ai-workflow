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

from .test_brief_sections import card, make_root
from .test_card_gate_and_projection import board_client
from .test_review_flow import strict_offline

ROOT = Path(__file__).resolve().parents[2]
EXECUTOR = dict(branch='wf/WF-001', source_sha='b' * 40)
ROLES = ('executor', 'reviewer')


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
