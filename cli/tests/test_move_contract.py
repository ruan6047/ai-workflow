"""消費 core/verbs.md §1 move／§2、core/enums.md 值域、modules/*/module.md §0；S08–S09 接點。"""
import ast
from copy import deepcopy
import json
import sys
from types import ModuleType

import pytest

from wf.compose.blocks import projection
from wf.compose.transitions import expand, universe
from wf.gh.client import NotFound
from wf.verbs.move import move
from .test_move_core import setup, catalog, deny_network, calls, reject, ROOT, WRITES, SHA
from .test_open_verb import issue, item, expected_card


@pytest.mark.parametrize('board_actor,new_actor,enabled', [('old', 'new', True),
    ('old', 'old', False), ('new', 'new', False), ('new', 'old', True)])
def test_s09_order_signatures_and_new_actor_facts(setup, monkeypatch, board_actor, new_actor, enabled):
    other = item(20)
    other['fieldValues'] = {'狀態': {'name': '進行中'}, 'owner': {'text': f'executor:{board_actor}'}}
    client, kwargs = setup(items=[other], rows=[issue(20, expected_card(card_id='WF-020'))],
                           modules=[{'name': 'escalation', 'params': {'escalate_after': 5}}])
    module = ModuleType('wf.verbs.move_modules')
    order = []

    def apply_counters(card, from_node, to_node, *, catalog, config, enabled_names):
        assert not [name for name, _ in client.calls if name in WRITES]
        assert (from_node, to_node) == ('執行/待辦', '執行/進行中')
        assert card['iteration'] == 8 and card['source_sha'] is None
        assert card['owner']['actor'] == new_actor
        assert ('resource-lock' in enabled_names) == enabled
        assert 'escalation' in enabled_names
        assert config['modules'] == [{'name': 'escalation', 'params': {'escalate_after': 5}}]
        assert catalog is kwargs['catalog']
        order.append('counters')
        return card | {'escalation_count': 5}

    def module_prints(card, from_node, to_node, *, catalog, config, enabled_names, project, client):
        assert order == ['counters']
        assert card['escalation_count'] == 5
        assert card['owner']['actor'] == new_actor
        assert not [name for name, _ in client.calls if name in WRITES]
        assert project == client.board
        order.append('prints')
        return ['S09 更新後計數：5']

    module.apply_counters, module.module_prints = apply_counters, module_prints
    monkeypatch.setitem(sys.modules, 'wf.verbs.move_modules', module)
    result = move(10, '進行中', actor=f'executor:{new_actor}', **kwargs)
    assert result.rc == 0
    assert order == ['counters', 'prints']
    assert result.card['escalation_count'] == 5
    assert result.printed == ('S09 更新後計數：5',)


def test_module_hooks_absent_before_d1(setup, monkeypatch):
    client, kwargs = setup()
    module = ModuleType('wf.verbs.move_modules')
    def forbidden(*args, **kwargs):
        pytest.fail('D1 前不得呼叫模組層')
    module.apply_counters = module.module_prints = forbidden
    monkeypatch.setitem(sys.modules, 'wf.verbs.move_modules', module)
    reject(client, move(10, '待確認', **kwargs), 'D1')


@pytest.mark.parametrize('project', [True, False])
def test_enabled_names_all_declarations_not_only_config(setup, monkeypatch, project):
    client, kwargs = setup(project=project, stage_plan=['需求', '研究', '規劃', '執行', '審核', '部署', '維護', '結案'],
                           parent='WF-002', db_scope='write', modules=[{'name': 'snapshot'}])
    module = ModuleType('wf.verbs.move_modules')
    def counters(card, from_node, to_node, *, catalog, config, enabled_names):
        assert enabled_names == {'research', 'deploy', 'maintenance', 'initiative', 'snapshot'}
        assert 'db-contract' not in enabled_names  # db_scope 不取代原件的 project_module_listed。
        return card
    def prints(card, from_node, to_node, *, catalog, config, enabled_names, project, client):
        assert (project is None) == (config['project'] is None)
        return []
    module.apply_counters, module.module_prints = counters, prints
    monkeypatch.setitem(sys.modules, 'wf.verbs.move_modules', module)
    assert move(10, '進行中', **kwargs).rc == 0


def test_schema_enums_and_transition_original_mutations(setup):
    client, kwargs = setup()
    altered = deepcopy(kwargs['catalog'])
    enums, = altered.by_label('json wf-enums')
    enums.data['roles']['enum'].append('test-role')
    kwargs['catalog'] = altered
    result = move(10, '進行中', actor='test-role:dynamic', **kwargs)
    assert result.rc == 0
    assert result.card['owner']['role'] == 'test-role'
    client, kwargs = setup()
    altered = deepcopy(kwargs['catalog'])
    machine, = altered.by_label('json wf-state-machine')
    machine.data['transitions'] = [row for row in machine.data['transitions']
                                   if (row['from'], row['to']) != ('*/待辦', 'same/進行中')]
    kwargs['catalog'] = altered
    reject(client, move(10, '進行中', **kwargs), 'D1')
    print('負控：規則 role 新值可寫；刪派工邊即 D1，來源規則確實控制行為')


@pytest.mark.parametrize('enabled', [False, True])
def test_escalation_transition_uses_config_and_expand(setup, enabled):
    client, kwargs = setup(state='退回', modules=[{'name': 'escalation'}] if enabled else [])
    result = move(10, '升級', **kwargs)
    if enabled:
        assert result.rc == 0 and result.card['state'] == '升級'
    else:
        reject(client, result, 'D1')


def test_plan_empty_edges_inventory_and_d1_oracle_negative_control(catalog, setup, monkeypatch):
    edges = expand([], [], catalog=catalog)
    nodes = universe([], [], catalog=catalog)
    assert {node.split('/')[0] for node in nodes} == {'需求', '清單'}
    print('空計畫節點母體：' + json.dumps(sorted(nodes), ensure_ascii=False))
    print('空計畫邊母體：' + json.dumps({key: sorted(value) for key, value in sorted(edges.items())}, ensure_ascii=False))
    client, kwargs = setup()
    monkeypatch.setattr('wf.verbs.move.is_legal_move', lambda *args: True)
    invalid = move(10, '待確認', **kwargs)
    with pytest.raises(AssertionError):
        reject(client, invalid, 'D1')
    print('負控：打壞 D1 偵測器為永真，表外邊拒收斷言會響')


def test_src_inventory_and_stdlib_negative_control():
    path = ROOT / 'cli/src/wf/verbs/move.py'
    source = path.read_text()
    tree = ast.parse(source, feature_version=(3, 11))
    def imported(text):
        names = []
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.append(node.module)
        return names
    def external(names):
        return [name for name in names if name.split('.')[0] not in sys.stdlib_module_names | {'wf'}]
    assert external(imported('import requests')) == ['requests']
    assert external(imported(source)) == []
    assert len(source.splitlines()) <= 280
    assert ast.get_docstring(tree)
    calls_in_source = [node.func.id for node in ast.walk(tree)
                       if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
    assert calls_in_source.count('load_project_config') == 1
    assert 'module_names' in calls_in_source and 'is_enabled' in calls_in_source
    assert not any(isinstance(node, ast.Constant) and isinstance(node.value, str) and 'modules.json' in node.value
                   for node in ast.walk(tree))
    print('負控外部依賴：' + json.dumps(external(imported('import requests'))))
    print('S08 匯入母體：' + json.dumps(imported(source)))
    print('S08 src 行數：', len(source.splitlines()))


def test_malformed_existing_schema_cannot_be_repaired_by_move(setup):
    client, kwargs = setup(extra='非法鍵')
    reject(client, move(10, '進行中', **kwargs), 'D3')


def test_terminal_missing_branch_and_unmerged_pr(setup):
    client, kwargs = setup('結案', '待確認', branch=None)
    result = move(10, '完成', **kwargs)
    assert result.rc == 0 and '分支未填' in result.printed
    client, kwargs = setup('結案', '待確認')
    client.responses.update(pulls_for_branch=[{'number': 20}],
        pull_request={'number': 20, 'head': {'sha': SHA}, 'merge_commit_sha': None}, ci_checks={})
    def absent(**kwargs):
        raise NotFound('branch absent')
    client.responses['branch_head'] = absent
    result = move(10, '完成', **kwargs)
    assert result.rc == 0
    assert 'merge SHA 未填' in result.printed and '分支不存在：old/branch' in result.printed
    assert not calls(client, 'is_ancestor')


def test_non_dispatch_actor_does_not_enable_new_actor_resource_lock(setup, monkeypatch):
    other = item(20)
    other['fieldValues'] = {'狀態': {'name': '進行中'}, 'owner': {'text': 'executor:old'}}
    client, kwargs = setup(state='進行中', items=[other])
    module = ModuleType('wf.verbs.move_modules')
    def counters(card, from_node, to_node, *, catalog, config, enabled_names):
        assert card['owner']['actor'] == 'old'
        assert 'resource-lock' not in enabled_names
        return card
    module.apply_counters = counters
    module.module_prints = lambda *args, **kwargs: []
    monkeypatch.setitem(sys.modules, 'wf.verbs.move_modules', module)
    assert move(10, '待確認', actor='executor:new', **kwargs).rc == 0


def test_archived_foreign_self_and_draft_items_not_board_facts(setup, monkeypatch):
    active = {'狀態': {'name': '進行中'}, 'owner': {'text': 'executor:someone'}}
    items = [item(20) | {'isArchived': True}, item(21, 'other/repo'),
             {'id': 'DRAFT', 'content': {'__typename': 'DraftIssue'}}]
    for row in items:
        row['fieldValues'] = active
    client, kwargs = setup(items=items)
    module = ModuleType('wf.verbs.move_modules')
    def counters(card, from_node, to_node, *, catalog, config, enabled_names):
        assert 'resource-lock' not in enabled_names
        return card
    module.apply_counters = counters
    module.module_prints = lambda *args, **kwargs: []
    monkeypatch.setitem(sys.modules, 'wf.verbs.move_modules', module)
    assert move(10, '進行中', actor='executor:new', **kwargs).rc == 0
