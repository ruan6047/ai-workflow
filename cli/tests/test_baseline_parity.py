"""消費 core/verbs.md §2（回讀分流、留痕、寫入順序）。

A8：對 A1 母體（同一份 AST 枚舉的可達遠端寫入呼叫點，⛔ 不重打、⛔ 不另立站點清單）的每一個
站點，其同一場景在**不注入**時的五欄行為，在基線 f69f6216e575ec881222fc20549685795e2fc1c8 與
本卡 landing 之間，除本檔宣告表逐欄列明為「核可變更」者外，逐欄逐字相同。

五欄固定為 `rc`／`D 編號`／`逐字理由`／`wf:reject 留痕有無`／`原語序列`（`COLUMNS`）。

做法：同一次 pytest 執行內以**兩個隔離子行程**分別載入基線與被審版的 `cli/src`（各自獨立直譯器
行程與 `sys.path`，⛔ 不在同一行程內改 `sys.modules`）。基線樹以 `git archive` 於測試期取出至
tmp（⛔ 不 checkout、⛔ 不建 worktree、⛔ 不動 stash）。兩個子行程**共用同一份場景建構碼**
——`test_remote_ops_envelope` 的 `scenarios`／`scenario_named`／`measured`，那一份碼⛔ 不
import 任一只存在於被審版的名字（`wf.verbs._ops`、`wf.gh.writes.dry_run`、
`wf.gh.writes.DRY_RUN_ITEM` 已分別改成函式內 import 與 `cli/tests/fakes.py` 的狀態讀取介面），
⛔ 不為基線另寫第二份場景表。

⛔ 不得 skip：基線 SHA 的 git 物件在本機取不到時本檔**失敗並印出原因**，⛔ 不降級成只跑被審版
（CI 的 `cli-tests` job 因此帶 `fetch-depth: 0`）。
"""
import json
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
TESTS_PARENT = str(ROOT / 'cli')
MEASURED_SRC = str(ROOT / 'cli/src')
BASELINE_SHA = 'f69f6216e575ec881222fc20549685795e2fc1c8'
COLUMNS = ('rc', 'D', 'reason', 'reject', 'mutations')
ENUMERATION = ('uv run --extra dev pytest cli/tests/test_baseline_parity.py'
               '::test_no_injection_behaviour_matches_baseline_except_declared_changes -q -s')
ROW, PATHLINE, NAMES = 'PARITY_ROW ', 'PARITY_TREE ', 'PARITY_NAMES '

# ── 宣告表 ────────────────────────────────────────────────────────────────────
# 分類與各欄預期在**執行被審版之前**由 A5 與 core/verbs.md §2 的條文推得並寫死於此，
# ⛔ 不得由任何一次實測結果反推分類、反推預期或生成預期。
#
# 類別 (甲)＝未被 A5 改變的場景：兩版五欄逐欄逐字相同（本表⛔ 不寫死它們的值——寫死等於把某一
#   次實測結果搬進宣告表，判準是「兩版相等」而不是「等於某個數字」）。
# 類別 (乙)＝A5 明定改變的場景：基線的實測須逐欄等於 `old`、被審版的實測須逐欄等於 `new`，且
#   只允許 `changed` 列明的那幾欄有差異，未列明的欄仍須兩版逐字相同。
#
# 為什麼只有 `move_terminal_resume` 是 (乙)：A5 改的是 `open` 的 D2 與 `move` 的 D1 兩個**回讀
# 分流點**。A1 母體的十一個場景中，四個 `open` 場景的板上⛔ 無本卡的 item（`open_case` 建的替身
# items 為空），D2 的在板分支一次都到不了；`move_stale_projection`／`move_terminal`／
# `move_withdraw` 的轉移在合成表內，`move_resume` 逐字「if legal: return None」⇒ 原路往下跑；
# `edit`／`notes`／`review` 三個動詞不在 A5 的掃描面（A5 逐字「掃描面＝`open`、`move` 兩動詞」）。
# 只有 `move_terminal_resume` 的 `結案/完成 → 結案/完成` 同時滿足「轉移不在合成表內」與
# 「from == to」，落在 A5 新增的那一條分流上。
DECLARED = {
    'edit_change': {'class': '甲'},
    'edit_in_review': {'class': '甲'},
    'move_stale_projection': {'class': '甲'},
    'edit_reject': {'class': '甲'},
    'move_terminal': {'class': '甲'},
    'move_withdraw': {'class': '甲'},
    'open_intake': {'class': '甲'},
    'open_restore': {'class': '甲'},
    'notes_reconcile': {'class': '甲'},
    'review_return': {'class': '甲'},
    'move_terminal_resume': {
        'class': '乙',
        # 依據條文逐字片段（A5）
        'clause': ('回讀為 plan 的前綴（任一已宣告原語的回讀證據顯示尚未完成）＝續作剩餘寫入並在 '
                   '`completed_writes` 列出已完成項；其餘＝維持基線 '
                   'f69f6216e575ec881222fc20549685795e2fc1c8 的原 D 編號與原逐字理由（`已在板上`、'
                   '`<from> → <to> 不在合成表內`）。**終態 `move` 的完成條件逐字＝卡面 `wf-card` 的 '
                   '`stage`／`state` 等於本次目標 ∧ 五個投影欄與卡面 JSON 全等 ∧ 承載 issue 的 state '
                   '為 `closed`；三者同時成立才判 rc=0 收斂。**只要 issue 仍為 `open`，即使卡面與五欄'
                   '全等也⛔ 不得判收斂，一律判為 plan 的前綴並續作 `close_issue`'),
        # 具體前置
        'setup': ('`move --to 結案/完成`；卡面 `wf-card` 已是 結案/完成、五個投影欄已與卡面 JSON 全等、'
                  '承載 issue 仍為 `open`（`test_remote_ops_envelope.scenarios` 的 `move_terminal_resume`）'),
        # 舊結果五欄：基線⛔ 無回讀分流，`結案/完成 → 結案/完成` 不在合成表內 ⇒ D1 拒收，
        # 依 §2 留痕條寫一則 `wf:reject` 留言（該次唯一的遠端寫入原語）。
        'old': {'rc': 1, 'D': 'D1', 'reason': '結案/完成 → 結案/完成 不在合成表內',
                'reject': True, 'mutations': ['post_comment']},
        # 新預期五欄：卡面與五欄全等 ⇒ 對帳零投影寫入；issue 仍 open ⇒ 判為 plan 的前綴並續作
        # `close_issue`，收據路徑 rc=0、⛔ 不拒收、⛔ 不留痕。
        'new': {'rc': 0, 'D': None, 'reason': '', 'reject': False, 'mutations': ['close_issue']},
        'changed': ('rc', 'D', 'reason', 'reject', 'mutations'),
    },
}


# ── 子行程側 ──────────────────────────────────────────────────────────────────

class _Patcher:
    """`monkeypatch` 在子行程裡的最小替身（`strict_offline` 只用三參數 `setattr`）：
    子行程用完即退，⛔ 不需還原。"""

    def setattr(self, target, name, value):
        setattr(target, name, value)


def subprocess_main():
    """由父行程以 `python -c` 在隔離子行程內呼叫，跑不注入的同一份共用場景建構碼。

    ⛔ 不 import 任一只存在於被審版的名字：場景建構碼取自 `tests.test_remote_ops_envelope`
    （兩版共用的同一份），版本差異只經 `cli/tests/fakes.py` 那個在兩版都存在的狀態讀取介面。"""
    import tempfile
    import wf
    from wf.compose.blocks import load_blocks
    from wf.verbs import _write
    from .test_brief_sections import make_root
    from .test_remote_ops_envelope import measured, scenarios
    from .test_review_flow import strict_offline

    _write._ITEM_LOOKUP_INTERVAL = 0  # 有界唯讀重試的間隔歸零（同 conftest 的 autouse fixture）
    strict_offline(_Patcher(), 'PARITY_NETWORK_DENIED')
    print(PATHLINE + json.dumps(str(Path(wf.__file__).resolve().parent)))
    catalog = load_blocks(ROOT)
    root = make_root(Path(tempfile.mkdtemp()))
    names = [name for name, _ in scenarios(catalog, root, Path(tempfile.mkdtemp()))]
    print(NAMES + json.dumps(names, ensure_ascii=False))
    for name in names:
        row = measured(name, catalog, root, Path(tempfile.mkdtemp()))
        print(ROW + json.dumps([name, {key: row[key] for key in COLUMNS}], ensure_ascii=False))


# ── 父行程側 ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope='module')
def catalog():
    from wf.compose.blocks import load_blocks
    return load_blocks(ROOT)


@pytest.fixture(scope='module')
def root(tmp_path_factory):
    from .test_brief_sections import make_root
    return make_root(tmp_path_factory.mktemp('rules'))


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """父行程這一側的離線護欄（子行程另有自己的一份，見 `subprocess_main`）。"""
    import socket
    from .test_review_flow import strict_offline
    strict_offline(monkeypatch, 'PARITY_NETWORK_DENIED')
    with pytest.raises(AssertionError, match='PARITY_NETWORK_DENIED'):
        subprocess.run(['gh', 'api', 'negative-control'])
    monkeypatch.setattr(socket.socket, 'connect', lambda *a, **k: (_ for _ in ()).throw(
        AssertionError('PARITY_NETWORK_DENIED')))


# 本檔的兩種子程序刻意在**模組載入時**取下真的 `subprocess.run`：① `git cat-file`／`git archive`
# 唯讀取基線樹（⛔ 不 checkout、⛔ 不建 worktree、⛔ 不動 stash、⛔ 不走網路）；② `python -c` 起
# 隔離子行程。autouse 的 `offline` 護欄擋的是**動詞路徑上**的子程序（`reach` 在父行程內實跑動詞），
# 兩者刻意分開，否則護欄的安裝順序會決定本檔跑不跑得起來。隔離子行程自己另有一份護欄
# （`subprocess_main` 內的 `strict_offline`）。⛔ 不得推出「本檔可以繞過離線紀律」——這兩種子程序
# 逐字只有上列兩個唯讀 git 子指令與本直譯器自身，⛔ 無 `fetch`／`clone`／`push`／`gh`／`curl`。
_SPAWN = subprocess.run


def git(*argv):
    return _SPAWN(['git', '-C', str(ROOT), *argv], capture_output=True, text=False)


def baseline_src(tmp_path):
    """`git archive <SHA> cli/src` 取基線樹至 tmp。⛔ 不 checkout、⛔ 不建 worktree、⛔ 不動 stash。
    物件取不到時**失敗並印出原因**，⛔ 不 skip、⛔ 不降級成只跑被審版。"""
    probe = git('cat-file', '-e', f'{BASELINE_SHA}^{{commit}}')
    if probe.returncode != 0:
        pytest.fail(f'基線 {BASELINE_SHA} 的 git 物件在本機取不到：'
                    f'`git -C {ROOT} cat-file -e {BASELINE_SHA}^{{commit}}` rc={probe.returncode}、'
                    f'stderr={probe.stderr.decode("utf-8", "replace").strip()!r}。'
                    'A8 逐字⛔ 不得 skip、⛔ 不得降級成只跑被審版；CI 的 cli-tests job 須帶 '
                    'fetch-depth: 0 才抓得到這顆物件。')
    archive = git('archive', BASELINE_SHA, 'cli/src')
    assert archive.returncode == 0, archive.stderr.decode('utf-8', 'replace')
    path = tmp_path / 'baseline'
    path.mkdir()
    (tmp_path / 'baseline.tar').write_bytes(archive.stdout)
    with tarfile.open(tmp_path / 'baseline.tar') as tar:
        tar.extractall(path, filter='data')
    return str(path / 'cli/src')


DRIVER = ('import sys\n'
          'sys.path.insert(0, {tests!r})\n'
          'sys.path.insert(0, {src!r})\n'
          'from tests.test_baseline_parity import subprocess_main\n'
          'subprocess_main()\n')


def run_tree(src, label, sha):
    """一個隔離子行程：獨立直譯器行程與 `sys.path`，`wf` 只從 `src` 載入。"""
    proc = _SPAWN([sys.executable, '-c', DRIVER.format(tests=TESTS_PARENT, src=src)],
                  capture_output=True, text=True, cwd=str(ROOT))
    assert proc.returncode == 0, (label, src, proc.stdout, proc.stderr)
    loaded, names, rows = None, None, {}
    for line in proc.stdout.splitlines():
        if line.startswith(PATHLINE):
            loaded = json.loads(line[len(PATHLINE):])
        elif line.startswith(NAMES):
            names = json.loads(line[len(NAMES):])
        elif line.startswith(ROW):
            name, row = json.loads(line[len(ROW):])
            rows[name] = row
    print(f'PARITY_SUBPROCESS {label} | 宣告載入 {src} | 實際載入的 wf 套件路徑 {loaded} '
          f'| 該樹的來源 SHA {sha} | 場景數 {len(rows)}')
    # 推翻④：子行程實際載入的版本與其宣告不符 ⇒ ⛔ 不得判本條有效。
    assert loaded is not None and Path(loaded) == Path(src) / 'wf', (label, src, loaded)
    assert names and set(names) == set(rows), (label, names, sorted(rows))
    return loaded, names, rows


@pytest.fixture(scope='module')
def trees(tmp_path_factory):
    head = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                          capture_output=True, text=True)
    head_sha = head.stdout.strip() + '（被審版子行程載入的是工作樹上的 cli/src，⛔ 不是該 SHA 的檔案）'
    return {'基線': run_tree(baseline_src(tmp_path_factory.mktemp('parity')), '基線', BASELINE_SHA),
            '被審版': run_tree(MEASURED_SRC, '被審版', head_sha)}


def differences(name, base, head):
    """一個場景的五欄比對結果：回不符合宣告表的欄逐字說明（空＝相符）。"""
    entry = DECLARED[name]
    if entry['class'] == '甲':
        return [f'{name}・{column}・(甲) 類兩版須逐字相同：基線 {base[column]!r} vs 被審版 {head[column]!r}'
                for column in COLUMNS if base[column] != head[column]]
    found = []
    for column in COLUMNS:
        if base[column] != entry['old'][column]:
            found.append(f'{name}・{column}・基線實測與宣告表舊結果不符：'
                         f'{base[column]!r} vs {entry["old"][column]!r}')
        if head[column] != entry['new'][column]:
            found.append(f'{name}・{column}・被審版實測與宣告表新預期不符：'
                         f'{head[column]!r} vs {entry["new"][column]!r}')
        if column not in entry['changed'] and base[column] != head[column]:
            found.append(f'{name}・{column}・未列明為變更卻在兩版之間有差異：'
                         f'{base[column]!r} vs {head[column]!r}')
    return found


def compare(base_rows, head_rows, table_class):
    """逐場景比對；table_class 給定時以它覆寫該場景的宣告類別（負控①用）。"""
    found = []
    for name in sorted(base_rows):
        entry = dict(DECLARED[name])
        if name in table_class:
            entry['class'] = table_class[name]
        saved, DECLARED[name] = DECLARED[name], entry
        try:
            found += differences(name, base_rows[name], head_rows[name])
        finally:
            DECLARED[name] = saved
    return found


def test_no_injection_behaviour_matches_baseline_except_declared_changes(trees, catalog, root,
                                                                         tmp_path):
    """A8 本體：兩個隔離子行程的五欄逐場景比對，只允許宣告表列明的差異。

    另驗 A1 母體的覆蓋（推翻④）：A1 母體的每一個站點都必須有一個場景在本條跑過一次；
    站點清單由 `test_remote_ops_envelope.SITES` import 取得，⛔ 不重打、⛔ 不另立。"""
    from .test_remote_ops_envelope import SITES, reach
    (_, base_names, base_rows), (_, head_names, head_rows) = trees['基線'], trees['被審版']
    # 推翻④：兩版跑的場景前置不一致 ⇒ ⛔ 不得判本條有效。
    assert base_names == head_names, (base_names, head_names)
    assert set(base_rows) == set(DECLARED), (sorted(base_rows), sorted(DECLARED))
    groups = {'甲': [], '乙': []}
    for site in SITES:
        name, _, _ = reach(site, catalog, root, tmp_path)
        assert name is not None, site               # 推翻④：站點未被覆蓋
        assert name in base_rows, (str(site), name, sorted(base_rows))
        groups[DECLARED[name]['class']].append(str(site))
    assert len(groups['甲']) + len(groups['乙']) == len(SITES), groups
    for name in sorted(base_rows):
        entry = DECLARED[name]
        print('PARITY', name, '|', entry['class'],
              '| 基線五欄', json.dumps(base_rows[name], ensure_ascii=False),
              '| 被審版五欄', json.dumps(head_rows[name], ensure_ascii=False),
              '| 宣告表對應列', json.dumps(
                  {key: entry[key] for key in ('class', 'clause', 'setup', 'old', 'new', 'changed')
                   if key in entry}, ensure_ascii=False))
    found = compare(base_rows, head_rows, {})
    assert not found, found
    print('PARITY_POPULATION A1 母體站點數', len(SITES), '| 場景數', len(base_rows))
    for kind, label in (('甲', '未被 A5 改變'), ('乙', 'A5 明定改變')):
        print(f'PARITY_CLASS ({kind}) {label} 站點數', len(groups[kind]),
              json.dumps(groups[kind], ensure_ascii=False), '| 枚舉指令', ENUMERATION)
        if not groups[kind]:
            print(f'PARITY_CLASS_EMPTY ({kind}) 類站點數為 0；產生該數字的枚舉指令＝' + ENUMERATION)


def test_parity_negative_control_declared_change_relabelled(trees):
    """A8 負控①：把宣告表中任一「核可變更」列改標成「未變更」（乙 → 甲）後，該場景必須轉紅。
    仍全綠即代表本條沒在比該欄，判測具無效、⛔ 不判本條成立。"""
    (_, _, base_rows), (_, _, head_rows) = trees['基線'], trees['被審版']
    changed = [name for name, entry in DECLARED.items() if entry['class'] == '乙']
    assert changed, '宣告表⛔ 無「核可變更」列 ⇒ 本負控零資訊'
    for name in changed:
        found = compare({name: base_rows[name]}, {name: head_rows[name]}, {name: '甲'})
        assert found, (name, base_rows[name], head_rows[name])
        print('PARITY_NEGATIVE_RELABEL', name, '| 改標成 (甲) 後轉紅的欄',
              json.dumps(found, ensure_ascii=False))


def test_parity_negative_control_baseline_subprocess_loads_the_measured_tree(trees):
    """A8 負控②：把基線子行程改成載入被審版（兩邊同版）後，(乙) 類的場景必須轉紅。
    仍全綠即代表本條沒真的跑基線，判測具無效、⛔ 不判本條成立。
    本負控**真的再起一個子行程**載入被審版的 `cli/src`，⛔ 不以「拿被審版那一跑的輸出當基線」代替。"""
    _, _, head_rows = trees['被審版']
    _, _, fake_base = run_tree(MEASURED_SRC, '負控②：基線子行程改載被審版', '同被審版')
    changed = [name for name, entry in DECLARED.items() if entry['class'] == '乙']
    assert changed, '(乙) 類為空 ⇒ 本負控零資訊'
    for name in changed:
        found = compare({name: fake_base[name]}, {name: head_rows[name]}, {})
        assert found, (name, fake_base[name], head_rows[name])
        print('PARITY_NEGATIVE_SAME_TREE', name, '| 兩邊同版時轉紅的欄',
              json.dumps(found, ensure_ascii=False))


def test_baseline_object_is_required_and_never_skipped(tmp_path):
    """A8 逐字禁止 skip 的測具有效性：`git archive` 取不到基線物件時本檔必須**失敗並印出原因**。
    以一顆不存在的 SHA 走同一條路徑，斷言它走的是 `pytest.fail`（Failed）而⛔ 不是 skip。"""
    import unittest.mock
    missing = '0' * 40
    with unittest.mock.patch.object(sys.modules[__name__], 'BASELINE_SHA', missing):
        with pytest.raises(BaseException) as caught:
            baseline_src(tmp_path)
    assert caught.typename == 'Failed', caught.typename
    assert 'Skipped' not in caught.typename, caught.typename
    message = str(caught.value)
    assert missing in message and '⛔ 不得 skip' in message, message
    print('PARITY_MISSING_OBJECT_FAILS', caught.typename, '|', ' '.join(message.split()))
