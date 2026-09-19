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
from types import SimpleNamespace

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


def test_the_fake_dry_run_gate_delegates_to_the_production_gate(monkeypatch):
    """F-執行者-04 逐字「驗證器 `import` 使用，⛔ 不重打常數」在替身側的釘子。

    `cli/tests/fakes.py` import 的是兩版共有的**模組** `wf.gh.writes`，判定與 item id 都在呼叫時
    才向該模組取（不 from-import 名字的理由＝A8 的共用場景建構碼必須能在基線樹
    f69f6216e575ec881222fc20549685795e2fc1c8 上載入，見 fakes.py 就地註解）。

    本測試證明那是**委派**而不是複製：把生產側的判定或常數換掉，替身必須跟著換。②③ 兩個變異
    負控對「在替身重打一份」的寫法會原地不動，故那種寫法會讓本測試轉紅。
    ④ 另釘基線邊界：`wf.gh.writes` ⛔ 無 `dry_run` 屬性時（＝基線樹的實際形狀）替身回 False，
    且該默認值逐字⛔ 只適用 `--dry-run` 這一個功能，⛔ 不是跨版本功能缺席的通則。"""
    from wf.gh import writes
    from . import fakes
    production = writes.dry_run
    # 替身⛔ 不得自己定義一份生產常數／判定式的副本（重打的寫法會讓這一條轉紅）。
    assert not hasattr(fakes, 'DRY_RUN_ITEM'), '替身重打了生產常數 DRY_RUN_ITEM'
    # ① 逐值等價。`設為 None` 是 iteration 3 那五探針的漏網形狀（只在 None 漂移的變異穿得過去）。
    states = {'未設': SimpleNamespace(), '設為 True': SimpleNamespace(dry_run=True),
              '設為 False': SimpleNamespace(dry_run=False), '設為 0': SimpleNamespace(dry_run=0),
              '設為 None': SimpleNamespace(dry_run=None),
              '設為非空字串': SimpleNamespace(dry_run='x')}
    for label, probe in states.items():
        assert fakes.dry_run(probe) == production(probe), (label, probe)
        print('FAKE_GATE_EQUIVALENCE', label, json.dumps(production(probe)))
    # ② 判定式變異負控：恆 True 與恆 False **兩個都實作**（⛔ 不只寫在 docstring 裡）。
    for label, mutant, constant in (('恆 True', lambda client: True, True),
                                    ('恆 False', lambda client: False, False)):
        with monkeypatch.context() as patch:
            patch.setattr(writes, 'dry_run', mutant)
            followed = {name: fakes.dry_run(probe) for name, probe in states.items()}
        assert set(followed.values()) == {constant}, (label, followed)
        differing = [name for name, probe in states.items() if production(probe) != constant]
        assert differing, f'{label} 與未變異的生產碼全等 ⇒ 該負控零資訊'
        print('FAKE_GATE_MUTANT', label, '| 替身跟著變異的狀態數', len(followed),
              '| 與未變異生產碼不同值的狀態', json.dumps(differing, ensure_ascii=False))
    # ③ 常數變異負控：換掉生產側的 DRY_RUN_ITEM，替身 add_to_project 的 item id 必須跟著換。
    sentinel = '(dry-run-sentinel)'
    client = fakes.FakeGhClient()
    client.dry_run = True
    with monkeypatch.context() as patch:
        patch.setattr(writes, 'DRY_RUN_ITEM', sentinel)
        drifted = client.add_to_project('PVT', 'I_1')['data']['addProjectV2ItemById']['item']['id']
    restored = client.add_to_project('PVT', 'I_1')['data']['addProjectV2ItemById']['item']['id']
    assert (drifted, restored) == (sentinel, writes.DRY_RUN_ITEM), (drifted, restored)
    assert client.calls == [], client.calls   # `--dry-run` 路徑⛔ 不記 calls
    print('FAKE_GATE_ITEM_DRIFT', json.dumps([drifted, restored]))
    # ④ 基線邊界：屬性缺席 ⇒ 回 False（＝基線⛔ 無 dry-run 功能、A8 場景一律不帶該旗標）。
    with monkeypatch.context() as patch:
        patch.delattr(writes, 'dry_run')
        absent = [fakes.dry_run(probe) for probe in states.values()]
    assert absent == [False] * len(states), absent
    print('FAKE_GATE_BASELINE_FALLBACK 屬性缺席時的回值', json.dumps(absent),
          '| 邊界逐字：此默認值⛔ 只適用 --dry-run 這一個功能，⛔ 不推廣成跨版本功能的通則')
