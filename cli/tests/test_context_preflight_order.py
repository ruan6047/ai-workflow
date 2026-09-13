"""WF-009 static gate 與 operation-level preconditions 的時序：消費 core/verbs.md §2。
V14 static gate 不讀 permission 事實（ast＋執行期三態）、V15 六個 mutation 原語全部被 gate（ast 列舉）、
V16 static gate 與三項 operation precondition 各自先於自己的第一個 mutation（spy 呼叫序）。
GitHub 走 cli/tests/fakes.py 替身；本機 git 只在 tmp_path 合成。
"""
import ast
import json

import pytest

from .test_compose_schema import ROOT

WRITES = ROOT / 'cli/src/wf/gh/writes.py'
CONTEXT = ROOT / 'cli/src/wf/context.py'
GATE = '_verified'
PERMISSION_WORDS = {'state', 'states', 'permissions', 'permission', 'PermissionFact', 'allowed', 'denied',
                    'unknown', 'viewer_permission', 'viewerCanUpdate', 'viewerPermission'}


def class_methods(tree, name):
    cls, = (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name)
    return {node.name: node for node in cls.body if isinstance(node, ast.FunctionDef)}


def self_calls(function):
    """方法內 `self.<name>(…)` 的名稱與 `_request(…, method=…)` 的 method 字面。"""
    names, methods = set(), set()
    for node in ast.walk(function):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
                isinstance(node.func.value, ast.Name) and node.func.value.id == 'self':
            names.add(node.func.attr)
            if node.func.attr == '_request':
                methods.update(kw.value.value for kw in node.keywords
                               if kw.arg == 'method' and isinstance(kw.value, ast.Constant))
    return names, methods


def mutation_primitives(methods):
    """會走到 _request(method='PATCH'/'POST') 或 _mutation 的方法（沿 self.* 呼叫圖遞移閉包），取公開名。"""
    direct = {name for name, node in methods.items() if self_calls(node)[1] & {'PATCH', 'POST'}}
    reaching = set(direct)
    changed = True
    while changed:
        changed = False
        for name, node in methods.items():
            if name not in reaching and self_calls(node)[0] & (reaching | {'_mutation'}):
                reaching.add(name)
                changed = True
    return {name for name in reaching if not name.startswith('_')}


def gated(methods):
    return {name for name, node in methods.items() if any(
        isinstance(node_, ast.Call) and isinstance(node_.func, ast.Name) and node_.func.id == GATE
        for node_ in ast.walk(node))}


# ── V15：ast 自動列舉 WriteMixin 的 mutation 原語集合，與被 gate 的集合逐字相等（印出兩集合）──
def test_every_remote_mutation_primitive_is_gated_by_static_identity():
    methods = class_methods(ast.parse(WRITES.read_text(encoding='utf-8')), 'WriteMixin')
    primitives, guarded = mutation_primitives(methods), gated(methods)
    print('MUTATION_PRIMITIVES', sorted(primitives))
    print('GATED', sorted(guarded))
    assert primitives == guarded == {'update_card_body', 'post_comment', 'write_project_field',
                                     'add_to_project', 'remove_from_project', 'close_issue'}
    for name in primitives:  # gate 呼叫是該方法的第一個陳述：⛔ 不在請求之後才讀
        first = methods[name].body[0]
        while isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):  # 跳過 docstring
            first = methods[name].body[methods[name].body.index(first) + 1]
        assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Call) and first.value.func.id == GATE, name
    rogue = ast.parse(
        'class WriteMixin:\n'
        '    def stealthy_patch(self, number):\n'
        "        return self._request(f'x/{number}', method='PATCH', payload={})\n"
        '    def via_helper(self):\n'
        '        return self._mutation(1, 2, 3, 4)\n'
        '    def readonly(self):\n'
        "        return self._request('x', method='GET')\n")
    rogue_methods = class_methods(rogue, 'WriteMixin')
    assert mutation_primitives(rogue_methods) == {'stealthy_patch', 'via_helper'}  # 負控：未 gate 的 mutation 抓得到
    assert gated(rogue_methods) == set()
    assert mutation_primitives(rogue_methods) != gated(rogue_methods)


# ── V14：static gate 與其判定函式可達路徑的判斷式不出現 PermissionFact 欄位名 ──
def decision_words(function):
    """判斷式（if／while／ifexp／assert／return／布林與比較運算）內出現的名稱與屬性名。"""
    words = set()
    for node in ast.walk(function):
        tests = []
        if isinstance(node, (ast.If, ast.While, ast.IfExp)):
            tests.append(node.test)
        elif isinstance(node, ast.Assert):
            tests.append(node.test)
        elif isinstance(node, ast.Return) and node.value is not None:
            tests.append(node.value)
        elif isinstance(node, (ast.BoolOp, ast.Compare)):
            tests.append(node)
        for test in tests:
            for leaf in ast.walk(test):
                if isinstance(leaf, ast.Name):
                    words.add(leaf.id)
                elif isinstance(leaf, ast.Attribute):
                    words.add(leaf.attr)
                elif isinstance(leaf, ast.Constant) and isinstance(leaf.value, str):
                    words.add(leaf.value)
    return words


def reachable_functions(tree, roots):
    """從 roots 出發、同一檔內被呼叫的函式（Name 呼叫）遞移閉包。"""
    functions = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    seen, stack = {}, list(roots)
    while stack:
        name = stack.pop()
        if name in seen or name not in functions:
            continue
        seen[name] = functions[name]
        stack.extend(node.func.id for node in ast.walk(functions[name])
                     if isinstance(node, ast.Call) and isinstance(node.func, ast.Name))
    return seen


def test_static_gate_does_not_depend_on_permission_state():
    writes = ast.parse(WRITES.read_text(encoding='utf-8'))
    context = ast.parse(CONTEXT.read_text(encoding='utf-8'))
    functions = {**reachable_functions(writes, [GATE]), **reachable_functions(context, ['static_identity_verified'])}
    assert set(functions) >= {GATE, 'static_identity_verified'}
    words = {name: decision_words(node) for name, node in functions.items()}
    print('GATE_DECISION_WORDS', json.dumps({k: sorted(v) for k, v in words.items()}, ensure_ascii=False))
    for name, found in words.items():
        assert not (found & PERMISSION_WORDS), (name, found & PERMISSION_WORDS)
    assert 'static_identity_verified' in words[GATE]
    sloppy = ast.parse(
        'def _verified(client):\n'
        "    context = getattr(client, 'context', None)\n"
        "    if context is None or context.permissions[0].state == 'denied':\n"
        "        raise ContextNotVerified('x')\n")
    assert decision_words(reachable_functions(sloppy, [GATE])[GATE]) & PERMISSION_WORDS == {
        'permissions', 'state', 'denied'}  # 負控：讀 fact.state 的分支必被抓到


# ═══════════════════ V16：static gate 與三項 operation precondition 各自先於自己的第一個 mutation ═══════════════════
import sys  # noqa: E402

from wf.compose.blocks import load_blocks  # noqa: E402
from wf.verbs.main import DISPATCH, main  # noqa: E402
from .test_context_roots import (FAKE_REMOTE, MUTATIONS, mutation_calls, on_board_card, stateful,  # noqa: E402
                                 verb_args, workspace)
from .test_open_verb import issue  # noqa: E402

PRECONDITIONS = {'verify_source_issue': 'precondition:source_issue', 'card_number': 'precondition:duplicate',
                 'check_item_repository': 'precondition:item_repository'}


def instrument(monkeypatch, client):
    """把三項 precondition 的呼叫記進同一份 client.calls 序列（動詞模組各自 import 了名稱，逐模組替換）。"""
    for module_name, module in list(sys.modules.items()):
        if not module_name.startswith('wf.'):
            continue
        for name, marker in PRECONDITIONS.items():
            original = getattr(module, name, None)
            if original is None or not callable(original):
                continue

            def wrapped(*args, _original=original, _marker=marker, **kwargs):
                result = _original(*args, **kwargs)
                client.calls.append((_marker, {}))
                return result
            monkeypatch.setattr(module, name, wrapped)


def sequence(client):
    return [name for name, _ in client.calls]


def assert_order(seq, *, verb):
    """(a) bind_context 先於全部 mutation；(b) source_issue、(c) duplicate 先於該動詞第一個 mutation；
    (d) item_repository 先於第一個 write_project_field；三者彼此不要求先後但全晚於 static gate。"""
    first_mutation = next((i for i, name in enumerate(seq) if name in MUTATIONS), None)
    first_field = next((i for i, name in enumerate(seq) if name == 'write_project_field'), None)
    gate = seq.index('bind_context')
    if first_mutation is not None:
        assert gate < first_mutation, (verb, seq)
    for marker, boundary in (('precondition:source_issue', first_mutation), ('precondition:duplicate', first_mutation),
                             ('precondition:item_repository', first_field)):
        if marker in seq:
            assert seq.index(marker) > gate, (verb, marker, seq)
            if boundary is not None:
                assert seq.index(marker) < boundary, (verb, marker, seq)


def test_static_gate_and_each_operation_precondition_precede_their_own_mutation(tmp_path, monkeypatch, capsys):
    root = workspace(tmp_path, name='W16')
    catalog = load_blocks(root)
    args = verb_args(tmp_path)
    expected_markers = {'open': {'precondition:item_repository'},
                        'move': {'precondition:source_issue', 'precondition:duplicate', 'precondition:item_repository'},
                        'edit': {'precondition:source_issue', 'precondition:duplicate', 'precondition:item_repository'},
                        'notes': {'precondition:source_issue', 'precondition:duplicate', 'precondition:item_repository'},
                        'brief': {'precondition:source_issue', 'precondition:duplicate', 'precondition:item_repository'},
                        'review': {'precondition:source_issue', 'precondition:duplicate', 'precondition:item_repository'},
                        'snapshot': set()}
    sequences = {}
    for verb in DISPATCH:
        client = stateful(catalog)
        instrument(monkeypatch, client)
        assert main([verb, *args[verb]], client=client, root=root, env={}) == 0, (verb, capsys.readouterr())
        seq = sequence(client)
        assert_order(seq, verb=verb)
        assert {name for name in seq if name.startswith('precondition:')} >= expected_markers[verb], (verb, seq)
        if verb in ('open', 'move', 'edit', 'review'):
            assert any(name in MUTATIONS for name in seq), (verb, seq)  # 成功路徑真的有 mutation 可比序
        else:
            assert mutation_calls(client) == [], (verb, seq)
        sequences[verb] = seq
        print('V16', verb, seq)
    assert mutation_calls(stateful(catalog)) == []
    # 四種失敗路徑：各自 mutation 呼叫數為 0；snapshot 全程為 0。static gate 的失敗要有本機身分（有 remote 的
    # 工作區）讓 GH_REPO 只作核對；open 的目標是清單項 #11、其新 item 由 add_to_project 回傳，故後三種不影響它。
    gated_root = workspace(tmp_path, name='W16g', git_remote=FAKE_REMOTE)
    failures = {
        'static-gate': (lambda: stateful(catalog), gated_root, {'GH_REPO': 'wrong/target'}, lambda c: c.responses.update(
            repository=lambda slug: {'node_id': f'R_{slug}', 'full_name': slug, 'default_branch': 'main',
                                     'viewer_permission': 'ADMIN'})),
        'source_issue': (lambda: stateful(catalog, on_board_card(source_issue=999)), root, {}, lambda c: None),
        'duplicate': (lambda: stateful(catalog, rows=[issue(12, card=on_board_card(source_issue=12))]), root, {},
                      lambda c: None),
        'item_repository': (lambda: stateful(catalog), root, {}, lambda c: c.board['items'][0]['content'].__setitem__(
            'repository', {'id': 'R_OTHER', 'nameWithOwner': 'fake/repo'})),
    }
    for label, (make, at, env, tweak) in failures.items():
        for verb in DISPATCH:
            client = make()
            tweak(client)
            rc = main([verb, *args[verb]], client=client, root=at, env=env)
            capsys.readouterr()
            expected_rc = 1 if label == 'static-gate' else 0 if verb in ('snapshot', 'open') else 1
            assert rc == expected_rc, (label, verb, rc, sequence(client))
            if rc:
                assert mutation_calls(client) == [], (label, verb, sequence(client))
            if verb == 'snapshot':
                assert mutation_calls(client) == [], (label, verb)
    # 負控：把任一 precondition 挪到其 mutation 之後，對應子斷言必須變紅
    for marker in ('precondition:source_issue', 'precondition:duplicate', 'precondition:item_repository'):
        seq = list(sequences['move'])
        seq.remove(marker)
        boundary = 'write_project_field' if marker.endswith('item_repository') else next(n for n in seq if n in MUTATIONS)
        seq.insert(seq.index(boundary) + 1, marker)
        with pytest.raises(AssertionError):
            assert_order(seq, verb='move')
    seq = list(sequences['move'])
    seq.remove('bind_context')
    seq.insert(seq.index('update_card_body') + 1, 'bind_context')
    with pytest.raises(AssertionError):
        assert_order(seq, verb='move')
