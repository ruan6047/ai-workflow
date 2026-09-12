"""消費 core/verbs.md §1 open／§2、core/card-schema.md §1–3／§5、
core/naming.md §1、core/state-machine.md §3、modules/initiative/module.md §0–1。
本檔所有遠端操作由具狀態 fake 接住。
"""
from copy import deepcopy
import ast
import json
from pathlib import Path
import socket
import subprocess

import pytest

from .fakes import FakeGhClient
from wf.compose.blocks import load_blocks, projection
from wf.compose.schema import compose_schema
from wf.compose.validate import validate
from wf.gh.writes import WriteMixin, read_block
from wf.verbs import _write
from wf.verbs.open import missing_fields, open_issue, run


RULES = Path(__file__).resolve().parents[2]


def block(label, value):
    return f'```json {label}\n{json.dumps(value, ensure_ascii=False)}\n```\n'


def intake(observation='逐字痛點\n  保留空白'):
    return {'source': '', 'observation': observation,
            'dedupe': {'keywords': [], 'hits': []}, 'repo': ''}


def expected_card(**changes):
    # 獨立逐鍵 oracle；不能用被測初始化器組預期值。
    return dict(schema_version=2, card_id='WF-001', source_issue=10,
                feature='', core_pain=intake()['observation'], non_scope=[],
                stage_plan=[], stage='需求', state='待辦', list_convergence=[],
                service_goal='', tier=None, tier_basis=None, exec_capability=None,
                review_capability=None, db_scope=None, resources=[], when='',
                spec_version=1, iteration=0, acceptance=[], verification=[],
                parent=None, blocked=None, grilling=None, owner=None, branch=None,
                source_sha=None, notes=[]) | changes


def issue(number, card=None, body=None):
    return {'number': number, 'node_id': f'I{number}', 'state': 'open',
            'body': body if body is not None else block('wf-card', card)}


def item(number, repo='fake/repo'):
    return {'id': f'ITEM{number}', 'content': {'__typename': 'Issue', 'number': number,
            'repository': {'nameWithOwner': repo}}, 'fieldValues': {}}


class MemoryClient(FakeGhClient):
    repo = 'fake/repo'

    def __init__(self, catalog, issues, items=(), comments=(), hide_rounds=0):
        self.rows = {row['number']: deepcopy(row) for row in issues}
        self.options = {'階段': [{'id': 'stage-initial', 'name': '需求'}],
                        '狀態': [{'id': 'state-initial', 'name': '待辦'}], '級別': []}
        self.board = {'id': 'PROJECT', 'items': deepcopy(list(items)), 'fields': [
            {'id': name, 'name': name, 'dataType': 'SINGLE_SELECT' if name in self.options else 'TEXT'}
            for name in projection(catalog)]}
        # 最終一致性模型：add_to_project 之後 self.board 就有那一項（投影欄照樣寫得進去），
        # 只是接下來的前 hide_rounds 次查詢回應把它藏起來；None ＝一直不可見。
        # 預設 0 ＝不延遲：⛔ 不讓延遲變成所有既有案例的預設行為。
        self.hide_rounds, self.hidden = hide_rounds, None
        super().__init__(issue=lambda number: self.rows[number],
                         issues=lambda state: list(self.rows.values()),
                         project=self.query_board, comments=list(comments))

    def query_board(self, **kwargs):
        if self.hidden is None or self.hide_rounds == 0:
            return self.board
        if self.hide_rounds is not None:
            self.hide_rounds -= 1
        return self.board | {'items': [row for row in self.board['items'] if row['id'] != self.hidden]}

    def add_to_project(self, project_id, issue_id):
        result = super().add_to_project(project_id, issue_id)
        number, = (n for n, row in self.rows.items() if row['node_id'] == issue_id)
        self.board['items'].append(item(number) | {'id': 'ITEM'})
        self.hidden = 'ITEM'
        return result

    def prepare_project_field(self, project, item_id, name, value):
        self.calls.append(('prepare_project_field', {'name': name, 'item_id': item_id}))
        return WriteMixin.prepare_project_field(self, project, item_id, name, value)

    def update_card_body(self, number, card_json, create=False):
        super().update_card_body(number, card_json, create=create)
        return WriteMixin.update_card_body(self, number, card_json, create=create)

    def _request(self, endpoint, *, method=None, payload=None, query=None, variables=None):
        if query is not None:
            assert endpoint == 'graphql'
            self.calls.append(('read_options', deepcopy(variables)))
            return {'data': {'node': {'options': deepcopy(self.options[variables['id']])}}}
        assert method == 'PATCH'
        number = int(endpoint.rsplit('/', 1)[1])
        self.rows[number]['body'] = payload['body']
        return deepcopy(self.rows[number])

    def write_project_field(self, prepared):
        self.calls.append(('write_project_field', deepcopy(prepared)))
        operation, _, inputs = prepared
        row, = (i for i in self.board['items'] if i['id'] == inputs['itemId'])
        value = None if operation.startswith('clear') else inputs['value']
        if value is not None and 'singleSelectOptionId' in value:
            option, = (o for o in self.options[inputs['fieldId']] if o['id'] == value['singleSelectOptionId'])
            value = {'name': option['name']}
        row['fieldValues'][inputs['fieldId']] = value


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(RULES)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('禁止真實網路或子程序')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(subprocess, 'run', forbidden)


@pytest.fixture
def setup(tmp_path, catalog):
    (tmp_path / 'core').mkdir()
    (tmp_path / 'core/card-schema.md').write_text(
        (RULES / 'core/card-schema.md').read_text(encoding='utf-8'), encoding='utf-8')
    (tmp_path / '.wf').mkdir()

    def make(*, areas=('WF',), project=True, rows=(), items=(), comments=(), body=None, modules=(),
             hide_rounds=0):
        cfg = {'areas': list(areas), 'modules': list(modules),
               'project': {'owner': 'fake', 'number': 1} if project else None}
        (tmp_path / '.wf/modules.json').write_text(json.dumps(cfg), encoding='utf-8')
        source = issue(10, body=body if body is not None else '前言\n' + block('wf-intake', intake()) + '後記\n')
        client = MemoryClient(catalog, [source, *rows], items, comments, hide_rounds)
        return client, dict(client=client, root=tmp_path, catalog=catalog, emit=lambda line: None)
    return make


def assert_reject(client, result, code):
    writes = [name for name, _ in client.calls if name in
              ('add_to_project', 'update_card_body', 'write_project_field')]
    rejects = [data for name, data in client.calls if name == 'post_comment']
    assert result.rc != 0
    assert writes == []
    assert len(rejects) == 1
    assert rejects[0]['first_line'] == 'wf:reject'
    assert rejects[0]['body'].startswith(f'拒收・{code}・')


def test_intake_initial_keys_schema_body_and_five_fields(setup, catalog):
    client, kwargs = setup(comments=[{'body': '不解析留言'}])
    before = client.rows[10]['body']
    result = open_issue(10, **kwargs)
    assert result.rc == 0
    assert result.card == expected_card()
    assert set(result.card) == set(compose_schema(catalog, 'wf-card')['required'])
    assert validate(result.card, compose_schema(catalog, 'wf-card')) == []
    assert client.rows[10]['body'].startswith(before)
    assert read_block(client.rows[10]['body'], 'wf-intake') == intake()
    fields = client.board['items'][0]['fieldValues']
    assert fields == {'階段': {'name': '需求'}, '狀態': {'name': '待辦'}, '級別': None,
                      'owner': None, '卡ID': {'text': 'WF-001'}}
    names = [name for name, _ in client.calls]
    mutations = [name for name in names if name in ('add_to_project', 'update_card_body', 'write_project_field')]
    assert mutations == ['add_to_project', 'update_card_body', *['write_project_field'] * len(projection(catalog))]
    assert names.index('prepare_project_field') < names.index('add_to_project')
    assert names[-2:] == ['issue', 'project']
    assert '1 則留言，開卡前讀全部（F-需求-02）' in result.printed
    print('初值逐鍵母體：', json.dumps(sorted(result.card), ensure_ascii=False))
    print('寫入序列：', json.dumps(mutations, ensure_ascii=False))


def test_restore_preserves_every_key_except_initial(setup):
    old = expected_card(card_id='WF-027', iteration=7, stage='規劃', state='待確認',
                        feature='既有', spec_version=8, acceptance=['原文'], worktree='/tmp/kept')
    client, kwargs = setup(body=block('wf-card', old))
    result = open_issue(10, **kwargs)
    assert result.rc == 0
    assert result.card == old | {'stage': '需求', 'state': '待辦'}
    assert not any(name == 'comments' for name, _ in client.calls)


@pytest.mark.parametrize('body', [None, block('wf-card', expected_card())])
def test_d2_already_on_board(setup, body):
    client, kwargs = setup(body=body, items=[item(10)])
    assert_reject(client, open_issue(10, **kwargs), 'D2')


def test_d2_archived_item_is_still_on_board(setup):
    """封存（isArchived）的 Project 項仍在板上 ⇒ D2 照拒；⛔ 不改（core/verbs.md §2 D2）。"""
    body = block('wf-card', expected_card(stage='結案', state='完成'))
    client, kwargs = setup(body=body, items=[item(10) | {'isArchived': True}])
    assert_reject(client, open_issue(10, **kwargs), 'D2')


def test_d2_plain_issue(setup):
    client, kwargs = setup(body='一般 issue')
    assert_reject(client, open_issue(10, **kwargs), 'D2')


@pytest.mark.parametrize('areas,area,valid', [(['WF'], None, True),
    (['WF', 'CLI'], None, False), (['WF'], 'OPS', False), (['WF', 'CLI'], 'CLI', True), ([], None, False)])
def test_area_cases(setup, areas, area, valid):
    client, kwargs = setup(areas=areas)
    result = open_issue(10, area=area, **kwargs)
    if valid:
        assert result.rc == 0
        assert result.card['card_id'] == f'{area or areas[0]}-001'
    else:
        assert_reject(client, result, 'D3')


def test_numbering_all_repo_including_withdrawn_terminal_and_plain(setup):
    rows = [issue(1, expected_card(card_id='WF-001', source_issue=1)),
            issue(3, expected_card(card_id='WF-003', source_issue=3, stage='結案', state='完成')),
            issue(2, expected_card(card_id='WF-005', source_issue=2)) | {'state': 'closed'},
            issue(4, body='無區塊')]
    client, kwargs = setup(rows=rows, items=[item(1), item(3)])
    result = open_issue(10, **kwargs)
    # 撤銷卡（closed、不在板）持有最大序號：若母體排除它，序號會回退成 WF-004（重用）
    assert result.card['card_id'] == 'WF-006'
    assert [args for name, args in client.calls if name == 'issues'] == [{'state': 'all'}]


@pytest.mark.parametrize('existing,expected', [('WF-999', 'WF-1000'), ('CLI-999', 'WF-001')])
def test_numbering_cross_area_and_width(setup, existing, expected):
    # 同 area 到 999 仍進位到四位數；別的 area 的號 ⛔ 不進本 area 的池（core/naming.md §1 序號池四件）
    client, kwargs = setup(rows=[issue(1, expected_card(card_id=existing))])
    assert open_issue(10, **kwargs).card['card_id'] == expected


@pytest.mark.parametrize('project,exists,on_board,valid', [
    (True, False, False, False), (True, True, False, False),
    (True, True, True, True), (False, False, False, False), (False, True, False, True)])
def test_parent_existence_and_deferred(setup, project, exists, on_board, valid):
    rows = [issue(1, expected_card(card_id='WF-001', source_issue=1, spec_version=4))] if exists else []
    client, kwargs = setup(project=project, rows=rows, items=[item(1)] if on_board else [])
    result = open_issue(10, parent='WF-001', **kwargs)
    if not valid:
        assert_reject(client, result, 'D4')
    else:
        assert result.rc == 0
        assert result.card['parent_spec_version'] == 4
        assert '鏈深：1' in result.printed
        if not project:
            assert '無 Project 設定，未驗 parent 在板' in result.printed
            assert any(row['item'] == 'parent WF-001 在板' and row['kind'] == 'deferred'
                       for row in result.unverified)


def test_depth_three_only_prints(setup):
    rows = [issue(n, expected_card(card_id=f'WF-{n:03}', source_issue=n,
            parent=f'WF-{n - 1:03}' if n > 1 else None)) for n in range(1, 4)]
    client, kwargs = setup(rows=rows, items=[item(n) for n in range(1, 4)])
    result = open_issue(10, parent='WF-003', **kwargs)
    assert result.rc == 0
    assert '鏈深：3' in result.printed
    assert '上限 2' in result.printed


def test_missing_fields_exact_and_filled_negative_control(setup):
    client, kwargs = setup()
    result = open_issue(10, **kwargs)
    expected = ['feature', 'non_scope', 'stage_plan', 'list_convergence', 'tier',
                'tier_basis', 'exec_capability', 'review_capability', 'db_scope',
                'resources', 'when', 'service_goal']
    assert missing_fields(result.card, kwargs['root']) == expected
    changed = result.card | {'feature': '已填'}
    assert missing_fields(changed, kwargs['root']) == expected[1:]
    assert '缺欄清單：' + '、'.join(expected) in result.printed
    print('負控：feature 填上後，缺欄清單逐字少 feature')


@pytest.mark.parametrize('body', [block('wf-intake', intake() | {'extra': '非法鍵'}),
    '```json wf-intake\n{\n```\n', block('wf-card', expected_card(extra=True)),
    block('wf-card', expected_card(stage_plan=['需求', '結案'])),
    block('wf-card', expected_card(source_issue='10'))])
def test_d3_invalid_data_before_any_write(setup, body):
    client, kwargs = setup(body=body)
    assert_reject(client, open_issue(10, **kwargs), 'D3')


def test_project_field_resolution_before_add_negative_control(setup):
    client, kwargs = setup()
    client.board['fields'].pop()
    result = open_issue(10, **kwargs)
    assert_reject(client, result, 'D3')
    print('負控：移除投影欄 → D3，卡面與 Project 寫入 0，wf:reject 1')


def test_no_project_prints_skips_projection_and_tracks_deferral(setup):
    client, kwargs = setup(project=False)
    result = open_issue(10, **kwargs)
    assert result.rc == 0
    assert result.printed.count('無 Project 設定') == 1
    assert not any(name in ('project', 'add_to_project', 'write_project_field') for name, _ in client.calls)
    assert any(row['item'] == 'D2 在板判定' for row in result.unverified)
    assert any(row['item'] == '跨 session 發號原子性' for row in result.unverified)
    assert '清單項留言數：0' in result.printed
    assert not any('開卡前讀全部' in line for line in result.printed)


@pytest.mark.parametrize('label', ['wf-card', 'wf-intake'])
def test_null_block_on_the_source_issue_is_d3(setup, label):
    """null 區塊探針：清單項／撤銷卡的區塊值為 null ⇒ D3（不是「沒有區塊」的 D2）。"""
    client, kwargs = setup(body=f'前言\n```json {label}\nnull\n```\n')
    result = open_issue(10, **kwargs)
    assert_reject(client, result, 'D3')
    assert '不是物件' in result.reason


def test_null_block_on_another_issue_is_skipped_with_print(setup):
    """null 區塊探針：發號掃描遇到別的 issue 的 null 區塊 ⇒ 印略過、不擋、序號不受影響（負控＝合法卡計入序號）。"""
    rows = [issue(1, expected_card(card_id='WF-003', source_issue=1)), issue(2, body='```json wf-card\nnull\n```')]
    client, kwargs = setup(rows=rows, items=[item(1)])
    result = open_issue(10, **kwargs)
    assert result.rc == 0 and result.card['card_id'] == 'WF-004'
    assert '略過無法解析的 issue #2' in result.printed


def test_other_repository_item_does_not_block(setup):
    client, kwargs = setup(items=[item(10, 'other/repo')])
    assert open_issue(10, **kwargs).rc == 0


def test_initial_state_and_required_table_from_live_rules(setup, catalog):
    _, kwargs = setup(project=False)
    altered = deepcopy(catalog)
    machine, = (b for b in altered.blocks if b.label == 'json wf-state-machine')
    machine.data['initial'] = '規劃/待確認'
    kwargs['catalog'] = altered
    path = kwargs['root'] / 'core/card-schema.md'
    path.write_text(path.read_text().replace('| service_goal | 需求方 | 建卡 |',
                                            '| service_goal | 需求方 | 離開規劃前 |'))
    result = open_issue(10, **kwargs)
    assert (result.card['stage'], result.card['state']) == ('規劃', '待確認')
    assert 'service_goal' not in missing_fields(result.card, kwargs['root'])


def test_network_guard_negative_control():
    with pytest.raises(AssertionError, match='禁止真實網路'):
        subprocess.run(['gh', 'api', 'unused'])
    with socket.socket() as connection:
        with pytest.raises(AssertionError, match='禁止真實網路'):
            connection.connect(('127.0.0.1', 9))
    print('負控：subprocess.run 與 socket.connect 均被禁止')


def test_run_argument_adapter(setup, capsys):
    client, kwargs = setup(project=False, areas=['WF', 'CLI'])
    kwargs.pop('emit')
    assert run(['10', '--area', 'CLI'], **kwargs) == 0
    assert read_block(client.rows[10]['body'], 'wf-card')['card_id'] == 'CLI-001'
    assert '無 Project 設定' in capsys.readouterr().out


def test_restore_parent_and_version_are_preserved(setup):
    old = expected_card(card_id='WF-005', iteration=4, parent='WF-001', parent_spec_version=2)
    rows = [issue(1, expected_card(card_id='WF-001', spec_version=9)),
            issue(2, expected_card(card_id='WF-002', spec_version=8))]
    client, kwargs = setup(body=block('wf-card', old), rows=rows, items=[item(1), item(2)])
    result = open_issue(10, parent='WF-002', area='WF', **kwargs)
    assert result.rc == 0
    assert result.card == old
    assert any('保留既有 JSON' in line for line in result.printed)


def test_restore_invalid_explicit_area_is_d3(setup):
    client, kwargs = setup(body=block('wf-card', expected_card()))
    assert_reject(client, open_issue(10, area='OPS', **kwargs), 'D3')


@pytest.mark.parametrize('parent', ['WF-001', 'WF-999'])
def test_cyclic_or_incomplete_ancestor_chain_only_prints(setup, parent):
    rows = [issue(1, expected_card(card_id='WF-001', source_issue=1, parent=parent))]
    client, kwargs = setup(rows=rows, items=[item(1)])
    result = open_issue(10, parent='WF-001', **kwargs)
    assert result.rc == 0
    assert any(row['item'] == '鏈深' and row['kind'] == 'cannot' for row in result.unverified)


def test_enabled_modules_use_names_from_project_config(setup):
    client, kwargs = setup(modules=[{'name': 'snapshot', 'params': {'schedule': 'daily'}}])
    assert open_issue(10, **kwargs).rc == 0


def test_unfilled_intake_values_are_printed_not_rejected(setup):
    client, kwargs = setup(body=block('wf-intake', intake('')))
    result = open_issue(10, **kwargs)
    assert result.rc == 0
    assert result.card['core_pain'] == ''
    assert 'core_pain' in missing_fields(result.card, kwargs['root'])


def test_readback_mismatch_is_single_d3_after_write(setup):
    client, kwargs = setup()
    client.write_project_field = lambda prepared: client.calls.append(('write_project_field', prepared))
    result = open_issue(10, **kwargs)
    assert result.rc != 0
    assert result.reason == '回讀不等'
    assert len([n for n, _ in client.calls if n == 'post_comment']) == 1
    assert len([n for n, _ in client.calls if n == 'update_card_body']) == 1


def test_source_inventory_and_config_reader_negative_control():
    path = RULES / 'cli/src/wf/verbs/open.py'
    source = path.read_text(encoding='utf-8')
    tree = ast.parse(source, feature_version=(3, 11))
    calls = [node.func.id for node in ast.walk(tree)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
    def config_literals(text):
        return [node.value for node in ast.walk(ast.parse(text))
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
                and 'modules.json' in node.value]
    assert config_literals("path = '.wf/modules.json'") == ['.wf/modules.json']
    assert config_literals(source) == []
    assert calls.count('load_project_config') == 1
    assert 'module_names' in calls
    imported = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    imported += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
    assert all(name.split('.')[0] in {'argparse', 'copy', 'dataclasses', 'pathlib', 're', 'wf'} for name in imported)
    print('匯入母體：', json.dumps(imported, ensure_ascii=False))
    print('負控 modules.json 字面：', config_literals("path = '.wf/modules.json'"))
    print('modules.json 字面：', config_literals(source))


@pytest.mark.parametrize('hide_rounds,visible', [(1, True), (2, True), (None, False)])
@pytest.mark.parametrize('restore', [False, True])
def test_added_item_hidden_by_eventually_consistent_query(setup, monkeypatch, hide_rounds, visible, restore):
    """最終一致性探針：add_to_project 之後伺服端已經有那一項（投影欄照樣寫得進去），
    只是查詢回應暫時看不到它。新卡與 v2 撤銷卡復板都 ⛔ 不該去查剛加的 item；
    回讀階段查不到則走有界唯讀重試，耗盡才依契約拒收並印出已完成的寫入。"""
    # 只免掉等待，次數仍由常數決定；raising=False 讓還原修法的負控失敗在斷言上，不是在這一行。
    monkeypatch.setattr('wf.verbs._write._ITEM_LOOKUP_INTERVAL', 0, raising=False)
    old = expected_card(card_id='WF-009', iteration=3, feature='既有')
    client, kwargs = setup(body=block('wf-card', old) if restore else None, hide_rounds=hide_rounds)
    result = open_issue(10, **kwargs)
    names = [name for name, _ in client.calls]
    fields = list(projection(kwargs['catalog']))
    assert names.count('add_to_project') == 1  # 重試唯讀：⛔ 不重跑任何寫入
    assert names.count('update_card_body') == 1
    assert names.count('write_project_field') == len(fields)
    comments = [data for name, data in client.calls if name == 'post_comment']
    if visible:
        assert result.rc == 0
        assert result.card == (old | {'stage': '需求', 'state': '待辦'} if restore else expected_card())
        assert client.board['items'][0]['fieldValues']['卡ID'] == {'text': old['card_id'] if restore else 'WF-001'}
        assert [row['first_line'] for row in comments] == (['wf:move'] if restore else [])
        assert names.count('project') == 2 + hide_rounds  # 開卡前 1 次＋回讀重抓到看得見為止
    else:
        assert result.rc != 0
        assert [row['first_line'] for row in comments] == ['wf:reject']
        assert comments[0]['body'] == '拒收・D3・' + result.reason
        assert result.reason.startswith('Project 查不到 item ITEM')
        assert '已完成的寫入：卡面 JSON' in result.printed
        assert '已完成的寫入：投影欄 ' + '、'.join(fields) in result.printed
        assert names.count('project') == 2 + _write._ITEM_LOOKUP_ATTEMPTS  # 有界：⛔ 不無限等
    print('延遲輪數：', hide_rounds, '／project 查詢次數：', names.count('project'), '／rc：', result.rc)


def test_missing_single_select_option_before_project_add(setup):
    client, kwargs = setup()
    client.options['狀態'] = []
    assert_reject(client, open_issue(10, **kwargs), 'D3')


# ── WF-004：啟用判定前的上界預驗（core/card-schema.md §1 合成順序）────────────────

def shape_variants(catalog):
    """8 個敵意卡面值 → (卡面改動, 期望的 JSON pointer)。

    合法部分逐值由 catalog 取（F-執行者-04）：4 個讀未驗卡面的 enable_if kind 各自讀哪個欄、
    以及那些欄的合法值，唯一居所都是 modules/*/module.md §0 與 core/enums.md；這裡只把型別弄壞。
    """
    modules = {block.data['name']: block.data for block in catalog.by_label('yaml wf-module')}
    enums, = catalog.by_label('json wf-enums')
    stage = modules['research']['enable_if']['stage']            # stage_plan_has 讀 stage_plan
    parent_field = modules['initiative']['enable_if']['field']   # field_nonempty 讀 parent
    sensitive = modules['stat-redline']['enable_if']['value']    # field_contains 讀 tier_basis.sensitive
    role = enums.data['roles']['enum'][0]                        # other_actor_card_in_state 讀 owner.actor
    basis = {'sensitive': sensitive, 'recoverable': enums.data['recoverable']['enum'][0],
             'blast': enums.data['blast']['enum'][0]}
    return {
        'stage_plan_none': ({'stage_plan': None}, '/stage_plan'),
        'stage_plan_int': ({'stage_plan': 5}, '/stage_plan'),
        'stage_plan_string': ({'stage_plan': stage}, '/stage_plan'),
        'parent_int': ({parent_field: 5}, '/' + parent_field),
        'tier_basis_string': ({'tier_basis': sensitive}, '/tier_basis'),
        'sensitive_string': ({'tier_basis': basis}, '/tier_basis/sensitive'),
        'owner_string': ({'owner': f'{role}:same'}, '/owner'),
        'owner_actor_int': ({'owner': {'role': role, 'actor': 5}}, '/owner/actor'),
    }


VARIANTS = sorted(shape_variants(load_blocks(RULES)))


@pytest.mark.parametrize('variant', VARIANTS)
def test_prevalidation_precedes_parent_d4(setup, catalog, monkeypatch, variant):
    """8 敵意值：open 的上界預驗在 parent D4 與啟用判定之前 ⇒ D3＋schema path，⛔ 無 Python 內部字串。"""
    monkeypatch.setattr('wf.verbs.open.is_enabled',
                        lambda *a, **k: pytest.fail('上界預驗未過時 ⛔ 不得做啟用判定'))
    changes, pointer = shape_variants(catalog)[variant]
    client, kwargs = setup(body=block('wf-card', expected_card(**changes)))
    result = open_issue(10, **kwargs)
    assert_reject(client, result, 'D3')
    assert result.reason.startswith('/'), result.reason
    assert pointer in result.reason, result.reason
    print('WF-004 open', variant, result.reason)


def test_v1_restore_rejects_on_schema_version_const(setup):
    """§2.3 的刻意理由變更：v1 撤銷卡復板由「無投影欄可回填 stage/state」改落 /schema_version。

    兩者同為 D3、同為零寫入；需求方 2026-09-12 wf:ruling 已核可，且裁定 ⛔ 不加保留舊訊息的分支。
    """
    client, kwargs = setup(body=block('wf-card', expected_card(schema_version=1)))
    result = open_issue(10, **kwargs)
    assert_reject(client, result, 'D3')
    assert result.reason.startswith('/schema_version: '), result.reason
    assert '無投影欄可回填 stage/state' not in result.reason
    print('WF-004 v1 復板理由：', result.reason)
