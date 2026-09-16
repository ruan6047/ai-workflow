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
    def __init__(self, site):
        self.site, self.fired = site, 0

    def check(self, primitive):
        if primitive != self.site.primitive or not self.site.on_stack():
            return
        self.fired += 1
        raise TransportError(f'injected TransportError at {self.site}')


_INJECTING = {}


def _hook(base, name):
    def method(self, *args, **kwargs):
        if self.injector is not None:
            self.injector.check(name)
        return getattr(base, name)(self, *args, **kwargs)
    method.__name__ = name
    return method


def injecting(base):
    if base not in _INJECTING:
        body = {name: _hook(base, name) for name in MUTATIONS}
        _INJECTING[base] = type('Injecting' + base.__name__, (base,), body | {'injector': None})
    return _INJECTING[base]


def arm(client, site):
    """把既有替身換成帶注入能力的子類（同一個 instance，狀態全保留）。"""
    client.__class__ = injecting(client.__class__)
    client.injector = Injector(site)
    return client.injector


def performed(client):
    return [name for name, _ in client.calls if name in MUTATIONS]


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


def move_case(catalog, root, stage, state, to, *, client_class=MoveClient):
    current = expected_card(stage=stage, state=state, stage_plan=PLAN, iteration=7,
                            owner={'role': 'executor', 'actor': 'old'}, source_sha='a' * 40,
                            branch='old/branch')
    client = client_class(catalog, current)
    return client, (lambda c: move(10, to, client=c, root=root, catalog=catalog, emit=NOOP))


def open_case(catalog, root, body):
    client = MemoryClient(catalog, [issue(10, body=body)], [])
    return client, (lambda c: open_issue(10, client=c, root=root, catalog=catalog, emit=NOOP))


def scenarios(catalog, root, tmp_path):
    """(名稱, 產生器)；產生器回 (client, call)。次序＝找到站點時先試便宜的那些。"""
    executor = dict(branch='wf/WF-001', source_sha='b' * 40)
    return [
        ('edit_change', lambda: (simulated(card(), catalog),
                                 lambda c: edit(10, ['feature="改過"'], client=c, catalog=catalog, emit=NOOP))),
        ('edit_in_review', lambda: (simulated(card(stage='審核'), catalog),
                                    lambda c: edit(10, ['feature="改過"'], client=c, catalog=catalog, emit=NOOP))),
        ('move_stale_projection', lambda: move_case(catalog, root, '執行', '待辦', '執行/進行中',
                                                    client_class=StaleProjectionClient)),
        ('edit_reject', lambda: (simulated(card(), catalog),
                                 lambda c: edit(10, ['card_id="X"'], client=c, catalog=catalog, emit=NOOP))),
        ('move_terminal', lambda: move_case(catalog, root, '結案', '待確認', '結案/完成')),
        ('move_withdraw', lambda: move_case(catalog, root, '需求', '待確認', '清單')),
        ('open_intake', lambda: open_case(catalog, root, '前言\n' + block('wf-intake', intake()))),
        ('open_restore', lambda: open_case(catalog, root, block(
            'wf-card', expected_card(card_id='WF-027', stage='規劃', state='待辦', stage_plan=PLAN)))),
        ('notes_reconcile', lambda: (board_client(catalog, card(tier='T1', **executor)),
                                     lambda c: notes(10, client=c, root=root, emit=NOOP))),
        ('review_return', lambda: (board_client(catalog, card(**executor)),
                                   lambda c: review(10, file=sheet(tmp_path), role='executor',
                                                    client=c, root=root, emit=NOOP))),
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
        assert [entry.split('・')[0] for entry in result.completed_writes] == performed(client), (
            site, result.completed_writes, performed(client))
        print('INJECTED', site, '|', name, '| rc', result.rc, '| error_kind', result.error_kind,
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


def test_event_comment_failure_is_reported_in_the_receipt(catalog, root, tmp_path):
    """四處事件留言（`wf:move`×2、`wf:edit`×2、`wf:reject`）逐點注入：
    ①completed_writes 逐字列出該次之前已完成的原語；②next_action 逐字指出事件留言未貼出
    且 CLI ⛔ 不自動補發。母體為 0 ⇒ 判測具無效。"""
    assert EVENT_SITES, '事件留言寫入點母體為 0 ⇒ 測具無效'
    print('EVENT_SITE_POPULATION', len(EVENT_SITES),
          json.dumps(sorted({site.marker for site in EVENT_SITES})))
    for site in EVENT_SITES:
        name, client, result = reach(site, catalog, root, tmp_path)
        assert name is not None, site
        assert result.rc != 0 and result.phase == '事件留言', (site, result)
        assert [entry.split('・')[0] for entry in result.completed_writes] == performed(client), (
            site, result.completed_writes, performed(client))
        assert '事件留言未貼出' in result.next_action and 'CLI ⛔ 不自動補發' in result.next_action, result
        print('EVENT_SITE', site, '|', name, '| completed_writes',
              json.dumps(list(result.completed_writes), ensure_ascii=False),
              '| next_action', result.next_action)


def test_event_sites_are_silent_without_injection(catalog, root, tmp_path):
    """A7 負控①：不注入時，同一四個站點所在的場景⛔ 不得出現「事件留言未貼出」字樣；
    若不注入也印，該判定恆真、零資訊。"""
    seen = set()
    for site in EVENT_SITES:
        for name, build in scenarios(catalog, root, tmp_path):
            if (str(site), name) in seen:
                continue
            client, call = build()
            probe = arm(client, site)
            result = call(client)
            if not probe.fired:
                continue
            seen.add((str(site), name))
            client, call = build()
            clean = call(client)
            action = getattr(clean, 'next_action', '')
            assert '事件留言未貼出' not in action, (site, name, clean)
            print('EVENT_SITE_NEGATIVE', site, '|', name, '| next_action', repr(action))
            break
    assert len(seen) == len(EVENT_SITES), (seen, [str(s) for s in EVENT_SITES])
