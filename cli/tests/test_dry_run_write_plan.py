"""消費 core/verbs.md §2（write plan 與 `--dry-run`）、§1 七動詞。

A3：`open`／`move`／`edit`／`review`／`notes`／`brief` 六個動詞帶 `--dry-run` 時，六個 mutation
原語的呼叫序列長度為 0；同一場景不帶旗標時實際發生的 mutation 序列，與帶旗標時印出的
write plan 在原語名與順序上逐一相符。

原語清單由 AST 從 `wf.gh.writes` 枚舉（`test_remote_ops_envelope.MUTATIONS`），⛔ 不重打；
記錄型替身＝`cli/tests/fakes.py` 既有的 `calls`，⛔ 不另起一套替身。
`snapshot` 在基線 f69f6216e575ec881222fc20549685795e2fc1c8 的可達遠端寫入呼叫點為 0，本條不適用。
"""
import json
from pathlib import Path
import socket
import subprocess

import pytest

from wf.compose.blocks import load_blocks
from wf.verbs.brief import brief
from wf.verbs.edit import edit
from wf.verbs.main import BOOLEAN_FLAGS, global_flags
from wf.verbs.notes import notes
from wf.verbs.review import review

from .test_brief_sections import card, make_root
from .test_card_gate_and_projection import board_client, sheet
from .test_open_verb import block, intake
from .test_remote_ops_envelope import MUTATIONS, move_case, open_case, performed
from .test_review_flow import git_subcommand
from .test_write_flow import simulated

ROOT = Path(__file__).resolve().parents[2]
NOOP = (lambda line: None)
PLAN_PREFIX = 'write plan・'
EXECUTOR = dict(branch='wf/WF-001', source_sha='b' * 40)


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(ROOT)


@pytest.fixture(scope='module')
def root(tmp_path_factory):
    return make_root(tmp_path_factory.mktemp('rules'))


# `brief --for closeout` 另走 `git merge-tree`（唯讀）；其餘與 test_review_flow 的嚴格放行同一組。
ALLOWED_GIT = {'rev-parse', 'log', 'diff', 'merge-tree'}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """只放行本機唯讀 git 子指令；gh／curl／wget／ssh、字串型 shell command 與 socket 一律擋。"""
    real = subprocess.run

    def denied(*args, **kwargs):
        raise AssertionError('DRY_RUN_NETWORK_DENIED')

    def guarded(argv, *args, **kwargs):
        if isinstance(argv, (str, bytes)) or git_subcommand([str(i) for i in argv]) not in ALLOWED_GIT:
            denied()
        return real(argv, *args, **kwargs)

    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(subprocess, 'run', guarded)
    with pytest.raises(AssertionError, match='DRY_RUN_NETWORK_DENIED'):
        subprocess.run(['gh', 'api', 'negative-control'])
    with pytest.raises(AssertionError, match='DRY_RUN_NETWORK_DENIED'):
        subprocess.run(['git', 'push', 'origin'])


def cases(catalog, root, tmp_path):
    """六個動詞各一條會真的產生 mutation 的場景（產生器回 (client, call)）。"""
    return {
        'open': lambda: open_case(catalog, root, '前言\n' + block('wf-intake', intake())),
        'move': lambda: move_case(catalog, root, '結案', '待確認', '結案/完成'),
        'edit': lambda: (simulated(card(), catalog),
                         lambda c: edit(10, ['feature="改過"'], client=c, catalog=catalog, emit=NOOP)),
        'review': lambda: (board_client(catalog, card(**EXECUTOR)),
                           lambda c: review(10, file=sheet(tmp_path), role='executor',
                                            client=c, root=root, emit=NOOP)),
        'notes': lambda: (board_client(catalog, card(tier='T1', **EXECUTOR)),
                          lambda c: notes(10, client=c, root=root, emit=NOOP)),
        'brief --for closeout': lambda: (
            board_client(catalog, card(tier='T1', **EXECUTOR)),
            lambda c: brief(10, target='closeout', client=c, root=root, emit=NOOP)),
        # 一般 brief（非 closeout）先跑內層 `notes`，內層自己也對帳一次 ⇒ 同一次執行對同一欄
        # 會經過兩次對帳。查核序 1 finding WF-016-R1.1-003 逐字：「brief(target="reviewer")
        # 遇級別投影不等：dry-run rc=0、實際寫入=[]、plan=[write_project_field,write_project_field]；
        # 不帶旗標 rc=0、實際寫入=[write_project_field]」。板上級別＝T3、卡面＝T1 即該形狀。
        # A3 與新增條文未排除一般 brief，故⛔ 不以只測 closeout 取代契約。
        'brief --for reviewer': lambda: (
            board_client(catalog, card(tier='T1', **EXECUTOR)),
            lambda c: brief(10, target='reviewer', client=c, root=root, emit=NOOP)),
    }


def plan_of(result):
    """從印項取 write plan 的原語序列；表頭那一行⛔ 不算進序列。"""
    rows = [line for line in result.printed if line.startswith(PLAN_PREFIX)]
    assert rows and rows[0].endswith('本次遠端 mutation 0 次'), rows
    return [line.split('・')[2] for line in rows[1:]]


def test_dry_run_emits_plan_and_writes_nothing(catalog, root, tmp_path):
    for verb, build in cases(catalog, root, tmp_path).items():
        client, call = build()
        client.dry_run = True  # 全域旗標在總入口掛的那一顆布林（verbs/main.py）
        dry = call(client)
        assert performed(client) == [], (verb, performed(client))
        plan = plan_of(dry)

        client, call = build()
        wet = call(client)
        actual = performed(client)
        assert actual, f'{verb}：不帶旗標序列為 0 ⇒ 替身沒在記錄，測具無效'
        assert not [line for line in wet.printed if line.startswith(PLAN_PREFIX)], wet.printed
        assert plan == actual, (verb, plan, actual)
        print('DRY_RUN', verb, '| plan', json.dumps(plan), '| actual', json.dumps(actual),
              '| rc', dry.rc, wet.rc)
    print('DRY_RUN_VERBS', json.dumps(sorted(cases(catalog, root, tmp_path))),
          'MUTATIONS', json.dumps(sorted(MUTATIONS)))


def test_dry_run_is_a_global_flag_not_a_per_verb_one():
    """裁定 G4：`--dry-run` 是總入口的全域旗標，動詞之後出現＝用法錯（rc=2 的那條路）。"""
    assert BOOLEAN_FLAGS == ('--dry-run',)
    assert global_flags(['--dry-run', 'move', 'WF-001', '--to', '執行/進行中']) == (
        {'--dry-run': True}, ['move', 'WF-001', '--to', '執行/進行中'])
    assert global_flags(['--rules-root', 'R', '--dry-run', 'notes', 'WF-001']) == (
        {'--rules-root': 'R', '--dry-run': True}, ['notes', 'WF-001'])
    assert global_flags(['notes', 'WF-001', '--dry-run']) is None       # 動詞之後＝⛔ 不傳給動詞
    assert global_flags(['--dry-run=1', 'notes', 'WF-001']) is None     # 無值旗標⛔ 不收 `=`
    print('DRY_RUN_FLAG_SHAPES ok')
