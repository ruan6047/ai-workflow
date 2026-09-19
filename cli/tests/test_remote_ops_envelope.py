"""消費 core/verbs.md §2（共同失敗出口與部分完成收據）、core/naming.md §3 首行標記。

A1：`cli/src/wf/verbs/*.py` 內六個 mutation 原語的全部呼叫點，逐點注入
`wf.gh.client.TransportError` 後動詞一律回結果物件（rc≠0）、例外⛔ 不逸出，且結果物件帶
error_kind／phase／retryable／completed_writes／next_action 五鍵。
A7：`wf:move`／`wf:edit`／`wf:reject` 四處事件留言呼叫點的收據與 next_action。

母體一律在測試內以 AST 枚舉，⛔ 不重打站點清單；注入以「目標呼叫點的 frame 是否就在當前堆疊上」
定位，⛔ 不比對函式名、⛔ 不比對關鍵字。所有 GitHub 操作走既有替身，⛔ 不碰網路。
"""
import ast
import inspect
import json
from pathlib import Path
import socket
import subprocess

import pytest

from wf.compose.blocks import load_blocks
from wf.gh import writes as gh_writes
from wf.gh.client import GhError, TransportError
from wf.verbs._ops import EQUAL_SILENT, EVENT_HEAD, EVENT_NEXT, EVENT_PHASE
from wf.verbs.edit import edit
from wf.verbs.move import move
from wf.verbs.notes import notes
from wf.verbs.open import open_issue
from wf.verbs.review import review

from .test_brief_sections import card, make_root
from .test_card_gate_and_projection import board_client, sheet
from .test_move_core import MoveClient
from .test_open_verb import MemoryClient, block, expected_card, intake, issue
from .test_review_flow import strict_offline
from .test_write_flow import simulated

ROOT = Path(__file__).resolve().parents[2]
VERBS_DIR = ROOT / 'cli/src/wf/verbs'
EVENT_MARKERS = ('wf:move', 'wf:edit', 'wf:reject')
FIVE_KEYS = ('error_kind', 'phase', 'retryable', 'completed_writes', 'next_action')
PLAN = ['需求', '規劃', '執行', '審核', '結案']
NOOP = (lambda line: None)
ISSUE = 10  # 全部場景的承載 issue 號；收據裡的 issue 號由該次執行格式化


# ── 母體：六原語與呼叫點，全部由 AST 枚舉 ──────────────────────────────────────

def mutation_methods():
    """`wf.gh.writes` 中呼叫 `_verified` 的 method＝六個 mutation 原語。"""
    tree = ast.parse((ROOT / 'cli/src/wf/gh/writes.py').read_text(encoding='utf-8'))
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if any(isinstance(call, ast.Call) and getattr(call.func, 'id', None) == '_verified'
               for call in ast.walk(node)):
            found.add(node.name)
    return found


MUTATIONS = frozenset(mutation_methods())


class Site:
    """一個遠端寫入呼叫點：檔、原語、行區間，post_comment 另記首行標記字面。"""

    def __init__(self, path, primitive, node):
        self.path, self.primitive = path, primitive
        self.lineno, self.end_lineno = node.lineno, node.end_lineno
        marker = node.args[1] if primitive == 'post_comment' and len(node.args) > 1 else None
        self.marker = marker.value if isinstance(marker, ast.Constant) else None

    @property
    def event(self):
        return self.marker in EVENT_MARKERS

    def on_stack(self):
        frame = inspect.currentframe()
        while frame is not None:
            if (frame.f_code.co_filename == str(self.path)
                    and self.lineno <= frame.f_lineno <= self.end_lineno):
                return True
            frame = frame.f_back
        return False

    def __str__(self):
        return f'{self.path.name}:{self.lineno} {self.primitive}' + (f' [{self.marker}]' if self.marker else '')


def write_sites():
    """母體＝`cli/src/wf/verbs/*.py` 內 `client.<原語>(…)` 的呼叫點；原語名取自 AST 枚舉的六原語。"""
    sites = []
    for path in sorted(VERBS_DIR.glob('*.py')):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in MUTATIONS
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == 'client'):
                sites.append(Site(path, node.func.attr, node))
    return sites


SITES = write_sites()


# ── 注入：在既有替身上加能力，⛔ 不另起一套替身 ────────────────────────────────

class Injector:
    """after=False＝(生效前失敗)：⛔ 不讓原語跑到替身就拋；
    after=True＝(生效後失敗)：**先**讓原語真的跑完（替身把該留言存進自己的狀態）再拋同一
    `TransportError`，＝留言已寫入遠端、只是回應遺失。CLI 從例外本身分辨不出這兩者，
    A7 負控③ 就是拿兩者的收據逐字比對。"""

    def __init__(self, site, after=False):
        self.site, self.after, self.fired = site, after, 0

    def matches(self, primitive):
        return primitive == self.site.primitive and self.site.on_stack()


_INJECTING = {}


def _hook(base, name):
    def method(self, *args, **kwargs):
        injector = self.injector
        if injector is not None and injector.matches(name):
            if injector.after:
                getattr(base, name)(self, *args, **kwargs)
            injector.fired += 1
            raise TransportError(f'injected TransportError at {injector.site}')
        return getattr(base, name)(self, *args, **kwargs)
    method.__name__ = name
    return method


def injecting(base):
    if base not in _INJECTING:
        body = {name: _hook(base, name) for name in MUTATIONS}
        _INJECTING[base] = type('Injecting' + base.__name__, (base,), body | {'injector': None})
    return _INJECTING[base]


def arm(client, site, after=False):
    """把既有替身換成帶注入能力的子類（同一個 instance，狀態全保留）。"""
    client.__class__ = injecting(client.__class__)
    client.injector = Injector(site, after)
    return client.injector


def performed(client):
    return [name for name, _ in client.calls if name in MUTATIONS]


def receipt_split(result, client):
    """收據拆成（回讀證據確認已完成的那些, 本次執行實際發出的那些）並斷言後者逐一相符。

    `completed_writes` ＝ `_ops.WriteLedger.observed` ＋ 本次帳本：前者只在續作路徑上非空
    （例：終態 `move` 重跑時卡面已寫成，`update_card_body` 由回讀證據確認、⛔ 不是本次發的請求），
    後者必須與替身實際收到的原語序列逐字同序。⛔ 不把本次沒發生的請求算成本次已完成。"""
    done = performed(client)
    kinds = [entry.split('・')[0] for entry in result.completed_writes]
    cut = len(kinds) - len(done)
    assert kinds[cut:] == done, (kinds, done)
    return kinds[:cut], done


# ── 場景：每個動詞至少一條可跑通的路徑 ────────────────────────────────────────

@pytest.fixture(scope='module')
def catalog():
    return load_blocks(ROOT)


@pytest.fixture(scope='module')
def root(tmp_path_factory):
    return make_root(tmp_path_factory.mktemp('rules'))


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    strict_offline(monkeypatch, 'ENVELOPE_NETWORK_DENIED')
    with pytest.raises(AssertionError, match='ENVELOPE_NETWORK_DENIED'):
        subprocess.run(['gh', 'api', 'negative-control'])
    monkeypatch.setattr(socket.socket, 'connect', lambda *a, **k: (_ for _ in ()).throw(
        AssertionError('ENVELOPE_NETWORK_DENIED')))


class StaleProjectionClient(MoveClient):
    """投影欄寫進去但板上只反映第一欄 ⇒ write_card 的回讀不等，走 post-write 的 D3 拒收。
    刻意：`_write.reject` 的 `wf:reject` 呼叫點要有「之前已完成卡面 JSON 與投影欄寫入」的那一種到達路徑。"""

    written = 0

    def write_project_field(self, prepared):
        self.written += 1
        if self.written > 1:
            self.calls.append(('write_project_field', prepared))
            return None
        return super().write_project_field(prepared)


def move_case(catalog, root, stage, state, to, *, client_class=MoveClient, emit=NOOP):
    current = expected_card(stage=stage, state=state, stage_plan=PLAN, iteration=7,
                            owner={'role': 'executor', 'actor': 'old'}, source_sha='a' * 40,
                            branch='old/branch')
    client = client_class(catalog, current)
    return client, (lambda c: move(10, to, client=c, root=root, catalog=catalog, emit=emit))


def open_case(catalog, root, body, emit=NOOP):
    client = MemoryClient(catalog, [issue(10, body=body)], [])
    return client, (lambda c: open_issue(10, client=c, root=root, catalog=catalog, emit=emit))


def scenarios(catalog, root, tmp_path, emit=NOOP):
    """(名稱, 產生器)；產生器回 (client, call)。次序＝找到站點時先試便宜的那些。"""
    executor = dict(branch='wf/WF-001', source_sha='b' * 40)
    return [
        ('edit_change', lambda: (simulated(card(), catalog),
                                 lambda c: edit(10, ['feature="改過"'], client=c, catalog=catalog, emit=emit))),
        ('edit_in_review', lambda: (simulated(card(stage='審核'), catalog),
                                    lambda c: edit(10, ['feature="改過"'], client=c, catalog=catalog, emit=emit))),
        ('move_stale_projection', lambda: move_case(catalog, root, '執行', '待辦', '執行/進行中',
                                                    client_class=StaleProjectionClient, emit=emit)),
        ('edit_reject', lambda: (simulated(card(), catalog),
                                 lambda c: edit(10, ['card_id="X"'], client=c, catalog=catalog, emit=emit))),
        ('move_terminal', lambda: move_case(catalog, root, '結案', '待確認', '結案/完成', emit=emit)),
        # 終態 `move` 的重跑：卡面與五欄都已是 結案/完成、承載 issue 仍 open ⇒ `_ops.move_resume`
        # 續作 `close_issue`（core/verbs.md §2 move D1 分流條的第三個合取項）。該呼叫點只在這一條
        # 路徑上可達，⛔ 不與 move.py 的終態 close_issue 共用場景。
        ('move_terminal_resume', lambda: move_case(catalog, root, '結案', '完成', '結案/完成', emit=emit)),
        ('move_withdraw', lambda: move_case(catalog, root, '需求', '待確認', '清單', emit=emit)),
        ('open_intake', lambda: open_case(catalog, root, '前言\n' + block('wf-intake', intake()), emit)),
        ('open_restore', lambda: open_case(catalog, root, block(
            'wf-card', expected_card(card_id='WF-027', stage='規劃', state='待辦', stage_plan=PLAN)), emit)),
        ('notes_reconcile', lambda: (board_client(catalog, card(tier='T1', **executor)),
                                     lambda c: notes(10, client=c, root=root, emit=emit))),
        ('review_return', lambda: (board_client(catalog, card(**executor)),
                                   lambda c: review(10, file=sheet(tmp_path), role='executor',
                                                    client=c, root=root, emit=emit))),
    ]


def reach(site, catalog, root, tmp_path):
    """逐一試場景，回第一個真的打到該站點的那一次 (名稱, client, result)。"""
    for name, build in scenarios(catalog, root, tmp_path):
        client, call = build()
        injector = arm(client, site)
        result = call(client)
        if injector.fired:
            return name, client, result
    return None, None, None


def scenario_named(name, catalog, root, tmp_path, emit=NOOP):
    """依名稱重建同一個場景（新的 client，狀態⛔ 不跨次沿用）。"""
    build, = (builder for other, builder in scenarios(catalog, root, tmp_path, emit)
              if other == name)
    return build()


# ── A1 ────────────────────────────────────────────────────────────────────────

def test_mutation_primitive_population_matches_the_declared_tuple():
    """AST 枚舉出的六原語＝`wf.gh.writes.MUTATIONS`（生產碼的唯一居所，⛔ 不重打）。
    負控：把宣告的那一組去掉任一個就不相等。"""
    assert MUTATIONS == set(gh_writes.MUTATIONS), (MUTATIONS, gh_writes.MUTATIONS)
    assert MUTATIONS != set(gh_writes.MUTATIONS[1:])
    print('MUTATIONS_DECLARED', json.dumps(sorted(gh_writes.MUTATIONS)))


def test_every_reachable_write_site_returns_an_outcome(catalog, root, tmp_path):
    """逐站點注入 TransportError：例外⛔ 不逸出、rc≠0、五鍵齊備、completed_writes 逐字等於
    該次注入之前替身實際收到的原語序列。負控＝不注入時零 outcome。"""
    assert len(SITES) > 0, '母體為 0 ⇒ 測具無效'
    print('WRITE_SITE_POPULATION', len(SITES), 'MUTATIONS', json.dumps(sorted(MUTATIONS)))
    for site in SITES:
        print('WRITE_SITE', site)
    unreached = []
    for site in SITES:
        name, client, result = reach(site, catalog, root, tmp_path)
        if name is None:
            unreached.append(str(site))
            continue
        assert result.rc != 0, (site, name, result)
        for key in FIVE_KEYS:
            assert hasattr(result, key), (site, key)
        assert result.error_kind == 'transport' and result.retryable is True, (site, result)
        assert result.next_action, (site, result)
        observed, _ = receipt_split(result, client)
        print('INJECTED', site, '|', name, '| 回讀證據確認', json.dumps(observed),
              '| rc', result.rc, '| error_kind', result.error_kind,
              '| phase', result.phase, '| completed_writes',
              json.dumps(list(result.completed_writes), ensure_ascii=False))
    assert not unreached, unreached
    print('WRITE_SITES_COVERED', len(SITES))


def test_no_injection_yields_no_outcome(catalog, root, tmp_path):
    """A1 負控：同一組場景不注入時⛔ 不得出現任何 outcome，`next_action` 一律為空。
    負控不響即判測具無效（roles/conduct-common.md §1 F-共用-05）。"""
    for name, build in scenarios(catalog, root, tmp_path):
        client, call = build()
        result = call(client)
        assert getattr(result, 'error_kind', None) is None, (name, result)
        assert getattr(result, 'next_action', '') == '', (name, result)
        print('NO_INJECTION', name, 'rc', result.rc, 'mutations', json.dumps(performed(client)))


def test_read_path_failures_still_propagate(catalog, root):
    """邊界負控：本卡只收斂六原語的寫入失敗；讀取路徑的 GhError 仍照基線往上拋，
    ⛔ 不得推出「所有 API 失敗都被吞掉」。"""
    client, call = open_case(catalog, root, '前言\n' + block('wf-intake', intake()))
    client.responses['issues'] = lambda state: (_ for _ in ()).throw(GhError('讀取失敗'))
    with pytest.raises(GhError, match='讀取失敗'):
        call(client)
    print('READ_PATH_STILL_RAISES GhError')


# ── A7 ────────────────────────────────────────────────────────────────────────

EVENT_SITES = [site for site in SITES if site.event]
# A7 ③ 的可機械執行判準：斷言該留言遠端狀態已確定的四個字串，`next_action` 與該次 stdout 全文
# 都⛔ 不得含任何一個（子字串比對）。⛔ 不重打措辭：`_ops.EVENT_NEXT` 的骨架刻意不含這四者。
FORBIDDEN = ('未貼出', '已貼出', '未送出', '已送出')
MODES = ((False, '生效前失敗'), (True, '生效後失敗'))


def event_run(site, name, catalog, root, tmp_path, after):
    """同一站點跑一次：回 (result, 該次 stdout 全文, 替身實際收到的原語序列)。"""
    lines = []
    client, call = scenario_named(name, catalog, root, tmp_path, lines.append)
    injector = arm(client, site, after=after)
    result = call(client)
    assert injector.fired, (site, name, after)
    return result, lines, performed(client)


def test_event_comment_failure_is_reported_in_the_receipt(catalog, root, tmp_path):
    """四處事件留言（`wf:move`×2、`wf:edit`×2、`wf:reject`）逐點以兩種替身各跑一次：
    ①`completed_writes` 逐字列出該次注入之前已完成的遠端寫入原語，該次失敗的 `post_comment`
    本身⛔ 不列入——即使 (生效後失敗) 下它其實已經到達替身；②`next_action` 逐字指出該事件留言
    結果不明；③`next_action` 與 stdout 全文⛔ 不得含 FORBIDDEN 四字串。
    負控③：兩種替身的 `next_action` 與 stdout 必須逐字相同。母體為 0 ⇒ 判測具無效。"""
    assert EVENT_SITES, '事件留言寫入點母體為 0 ⇒ 測具無效'
    print('EVENT_SITE_POPULATION', len(EVENT_SITES),
          json.dumps(sorted({site.marker for site in EVENT_SITES})))
    for site in EVENT_SITES:
        name, _, _ = reach(site, catalog, root, tmp_path)
        assert name is not None, site
        receipts = {}
        for after, label in MODES:
            result, lines, done = event_run(site, name, catalog, root, tmp_path, after)
            assert result.rc != 0 and result.phase == EVENT_PHASE, (site, label, result)
            if after:  # (生效後失敗)：替身已收到該則留言，但它⛔ 不進 completed_writes
                assert done and done[-1] == 'post_comment', (site, label, done)
                done = done[:-1]
            kinds = [entry.split('・')[0] for entry in result.completed_writes]
            assert kinds[len(kinds) - len(done):] == done, (site, label, kinds, done)
            # 該次失敗的 post_comment 本身⛔ 不列入：(生效後失敗) 下它其實已到達替身，
            # done 已把它去掉，兩邊的 post_comment 筆數仍須相等。同一站點所在路徑上**先前成功**
            # 的同標記留言⛔ 不因此被排除（`edit` 在審核階段會貼兩則 wf:edit）。
            assert kinds.count('post_comment') == done.count('post_comment'), (
                site, label, kinds, done)
            assert result.next_action == EVENT_NEXT.format(
                marker=site.marker, issue=f'#{ISSUE}'), (site, label, result.next_action)
            for banned in FORBIDDEN:
                assert banned not in result.next_action, (site, label, banned)
                assert not [line for line in lines if banned in line], (site, label, banned)
            receipts[label] = (result.next_action, tuple(lines))
            print('EVENT_SITE', site, '|', name, '|', label, '| completed_writes',
                  json.dumps(list(result.completed_writes), ensure_ascii=False),
                  '| next_action', result.next_action)
        first, second = (receipts[label] for _, label in MODES)
        assert first == second, (site, first, second)   # 負控③
        print('EVENT_SITE_AMBIGUITY', site, '| 兩種替身的 next_action 與 stdout 逐字相同',
              json.dumps(list(second[1]), ensure_ascii=False))


def test_event_sites_are_silent_without_injection(catalog, root, tmp_path):
    """A7 負控①：不注入時，同一四個站點所在的場景⛔ 不得出現「事件留言寫入無回應・結果不明」
    字樣；若不注入也印，該判定恆真、零資訊。"""
    seen = set()
    for site in EVENT_SITES:
        name, _, _ = reach(site, catalog, root, tmp_path)
        assert name is not None, site
        lines = []
        client, call = scenario_named(name, catalog, root, tmp_path, lines.append)
        clean = call(client)
        action = getattr(clean, 'next_action', '')
        assert EVENT_HEAD not in action, (site, name, clean)
        assert not [line for line in lines if EVENT_HEAD in line], (site, name, lines)
        seen.add(str(site))
        print('EVENT_SITE_NEGATIVE', site, '|', name, '| next_action', repr(action))
    assert len(seen) == len(EVENT_SITES), (seen, [str(s) for s in EVENT_SITES])


def test_the_unknown_event_line_is_not_the_equal_silent_line():
    """A7 ／裁定 G8 甲：失敗路徑那一行與等值沉默那一行**逐字是兩行不同的字串**，
    且前者⛔ 不含後者為子字串——否則 A7 負控②（非等值路徑⛔ 不得印 G8 那一行）會被架空。"""
    rendered = EVENT_NEXT.format(marker='wf:edit', issue=f'#{ISSUE}')
    assert rendered != EQUAL_SILENT
    assert EQUAL_SILENT not in rendered and rendered not in EQUAL_SILENT
    assert rendered.startswith('事件留言寫入無回應・結果不明：')
    assert EQUAL_SILENT.startswith('事件留言結果不明：')
    for banned in FORBIDDEN:
        assert banned not in rendered and banned not in EQUAL_SILENT, banned
    print('EVENT_LINE_SHAPES', json.dumps([rendered, EQUAL_SILENT], ensure_ascii=False))
