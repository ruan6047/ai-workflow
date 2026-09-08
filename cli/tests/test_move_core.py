"""消費 core/verbs.md §1 move／§2、core/state-machine.md §3、core/naming.md §2；S08 驗收。"""
from copy import deepcopy
import json
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from wf.compose.blocks import load_blocks, projection
from wf.gh.client import NotFound, PermissionDenied, TransportError
from wf.gh.writes import WriteMixin, read_card
from wf.verbs._write import projected
from wf.verbs.move import move, run
from .test_open_verb import MemoryClient, expected_card, issue, item, block

ROOT = Path(__file__).resolve().parents[2]
SHA = 'a' * 40
URL = 'https://github.com/fake/repo/issues/10#issuecomment-1'
PLAN = ['需求', '規劃', '執行', '審核', '結案']
WRITES = {'update_card_body', 'write_project_field', 'remove_from_project', 'close_issue', 'post_comment'}


class MoveClient(MemoryClient):
    def __init__(self, catalog, current, rows=(), items=()):
        super().__init__(catalog, [issue(10, current), *rows], [item(10), *items])
        enums, = catalog.by_label('json wf-enums')
        states = [v for key, spec in enums.data.items() if key.startswith('state') for v in spec['enum']]
        states += [s for b in catalog.by_label('yaml wf-module') for s in b.data['adds']['enums']['states']]
        self.options = {key: [{'id': value, 'name': value} for value in values]
                        for key, values in {'階段': enums.data['stages']['enum'], '狀態': states,
                                            '級別': enums.data['tiers']['enum']}.items()}
        self.board['items'][0]['fieldValues'] = {
            key: None if value is None else {'text': value} for key, value in projected(current, catalog).items()}
        self.responses.update(commit_exists=True, pulls_for_branch=[], branch_head=SHA,
                              comment={'author': 'requester-account', 'issue_url': 'https://api.github.com/repos/fake/repo/issues/10',
                                       'body': block('wf-ruling', {'kind': 'other', 'reason': '原文'})})

    def comment_from_url(self, url):
        return WriteMixin.comment_from_url(self, url)

    def close_issue(self, number):
        result = super().close_issue(number)
        self.rows[number]['state'] = 'closed'
        return result

    def remove_from_project(self, project_id, item_id):
        result = super().remove_from_project(project_id, item_id)
        self.board['items'] = [i for i in self.board['items'] if i['id'] != item_id]
        return result


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(ROOT)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('S08_NETWORK_DENIED')
    monkeypatch.setattr(subprocess, 'run', forbidden)
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    # 即使日後 S09 進工作樹，核心測試仍明確模擬未接線。
    monkeypatch.setitem(sys.modules, 'wf.verbs.move_modules', None)


@pytest.fixture
def setup(tmp_path, catalog):
    (tmp_path / 'core').mkdir()
    for name in ('card-schema', 'ruling'):
        (tmp_path / f'core/{name}.md').write_text((ROOT / f'core/{name}.md').read_text())
    (tmp_path / '.wf').mkdir()

    def make(stage='執行', state='待辦', *, project=True, modules=(), rows=(), items=(), **changes):
        cfg = {'project': {'owner': 'fake', 'number': 1} if project else None,
               'modules': list(modules)}
        (tmp_path / '.wf/modules.json').write_text(json.dumps(cfg))
        current = expected_card(stage=stage, state=state, stage_plan=PLAN, iteration=7,
                                owner={'role': 'executor', 'actor': 'old'}, source_sha=SHA,
                                branch='old/branch') | changes
        client = MoveClient(catalog, current, rows, items)
        return client, dict(client=client, catalog=catalog, root=tmp_path, emit=lambda line: None)
    return make


def calls(client, name):
    return [data for method, data in client.calls if method == name]


def reject(client, result, code, *, after_write=False):
    assert result.rc != 0
    comments = calls(client, 'post_comment')
    assert len(comments) == 1
    assert comments[0]['first_line'] == 'wf:reject'
    assert comments[0]['body'].startswith(f'拒收・{code}・')
    if not after_write:
        assert [name for name, _ in client.calls if name in WRITES] == ['post_comment']


def test_legal_body_projection_order_and_log(setup, catalog):
    client, kwargs = setup()
    result = move('WF-001', '執行/進行中', actor='executor:new', **kwargs)
    assert result.rc == 0
    assert read_card(client.rows[10]['body']) == result.card
    assert result.card['stage'] == '執行' and result.card['state'] == '進行中'
    writes = [(name, value) for name, value in client.calls if name in WRITES]
    assert [name for name, _ in writes] == ['update_card_body', *['write_project_field'] * len(projection(catalog)), 'post_comment']
    assert writes[0][1]['card_json']['state'] == '進行中'
    assert writes[-1][1] == {'number': 10, 'first_line': 'wf:move', 'body': '執行/待辦 → 執行/進行中'}
    body_index = next(i for i, (name, _) in enumerate(client.calls) if name == 'update_card_body')
    field_index = max(i for i, (name, _) in enumerate(client.calls) if name == 'write_project_field')
    assert any(name == 'issue' for name, _ in client.calls[field_index + 1:])
    assert body_index < field_index
    assert '模組層未接線' in result.printed


@pytest.mark.parametrize('stage,state,to', [('執行', '待辦', '執行/待確認'),
    ('結案', '完成', '結案/待確認'), ('結案', '停止', '結案/待確認'),
    ('執行', '待確認', '清單'), ('需求', '待办', '需求/進行中')])
def test_illegal_and_terminal_edges(setup, stage, state, to):
    client, kwargs = setup(stage, state)
    reject(client, move(10, to, **kwargs), 'D3' if state == '待办' else 'D1')


@pytest.mark.parametrize('state', ['待辦', '退回'])
@pytest.mark.parametrize('role', ['requester', 'pm', 'executor', 'reviewer', None])
def test_dispatch_owner(setup, state, role):
    client, kwargs = setup(state=state)
    result = move(10, '執行/進行中', actor=f'{role}:new' if role else None, **kwargs)
    assert result.rc == 0
    assert result.card['owner'] == ({'role': role, 'actor': 'new'} if role else {'role': 'executor', 'actor': 'old'})
    assert ('未指定 actor' in result.printed) == (role is None)


@pytest.mark.parametrize('actor', ['invalid:new', 'executor', ':new'])
def test_actor_d3(setup, actor):
    client, kwargs = setup()
    reject(client, move(10, '進行中', actor=actor, **kwargs), 'D3')


def test_non_dispatch_actor_preserves_owner_without_print(setup):
    client, kwargs = setup(state='進行中')
    result = move(10, '待確認', actor='reviewer:new', source_sha=SHA, **kwargs)
    assert result.rc == 0
    assert result.card['owner'] == {'role': 'executor', 'actor': 'old'}
    assert result.printed == ('模組層未接線',)


@pytest.mark.parametrize('state', ['待辦', '退回', '升級'])
def test_iteration_sha_branch_every_execution_entry(setup, state):
    client, kwargs = setup(state=state, modules=[{'name': 'escalation'}])
    result = move(10, '執行/進行中', actor='executor:new', source_sha=SHA, **kwargs)
    assert result.rc == 0
    assert result.card['iteration'] == 8
    assert result.card['source_sha'] is None
    assert result.card['branch'] == 'wf/WF-001'
    assert result.card['owner']['actor'] == ('old' if state == '升級' else 'new')


@pytest.mark.parametrize('stage', ['需求', '規劃', '審核'])
def test_non_execution_keeps_iteration_sha_branch(setup, stage):
    client, kwargs = setup(stage)
    result = move(10, '進行中', **kwargs)
    assert result.rc == 0
    assert (result.card['iteration'], result.card['source_sha'], result.card['branch']) == (7, SHA, 'old/branch')


def test_handoff_writes_remote_sha(setup):
    client, kwargs = setup(state='進行中')
    new_sha = 'b' * 40
    result = move(10, '待確認', source_sha=new_sha, **kwargs)
    assert result.rc == 0
    assert result.card['source_sha'] == new_sha
    assert calls(client, 'commit_exists') == [{'sha': new_sha}]


@pytest.mark.parametrize('to', ['待確認', '阻塞'])
def test_sha_d4_any_edge(setup, to):
    client, kwargs = setup(state='進行中')
    client.responses['commit_exists'] = False
    reject(client, move(10, to, source_sha=SHA, **kwargs), 'D4')


@pytest.mark.parametrize('ruling', [URL, None])
def test_block_and_resume_only_original(setup, ruling):
    client, kwargs = setup(state='進行中')
    result = move(10, '阻塞', ruling=ruling, **kwargs)
    assert result.rc == 0
    assert result.card['blocked'] == {'from': '進行中', 'ruling': ruling}
    assert result.card['state'] == '阻塞'
    client.calls.clear()
    reject(client, move(10, '待確認', **kwargs), 'D1')
    client.calls.clear()
    result = move(10, '進行中', actor='executor:new', **kwargs)
    assert result.rc == 0
    assert result.card['blocked'] is None
    assert result.card['owner']['actor'] == 'old'
    assert result.card['iteration'] == 8 and result.card['source_sha'] is None


@pytest.mark.parametrize('ruling', [URL, None])
def test_withdraw_retains_body_and_removes_once(setup, ruling):
    client, kwargs = setup('需求', '待確認')
    before = read_card(client.rows[10]['body'])
    result = move(10, '清單', ruling=ruling, **kwargs)
    assert result.rc == 0
    assert result.card == before
    assert read_card(client.rows[10]['body']) == before
    assert calls(client, 'remove_from_project') == [{'project_id': 'PROJECT', 'item_id': 'ITEM10'}]
    assert client.board['items'] == []
    assert client.rows[10]['state'] == 'open'
    assert ('缺 --ruling' in result.printed) == (ruling is None)


@pytest.mark.parametrize('terminal', ['完成', '停止'])
def test_terminal_no_pr_close_once(setup, terminal):
    client, kwargs = setup('結案', '待確認')
    result = move(10, f'結案/{terminal}', **kwargs)
    assert result.rc == 0
    assert '無 PR' in result.printed
    assert any(line.startswith('分支 old/branch：') for line in result.printed)
    assert calls(client, 'pulls_for_branch') == [{'branch': 'old/branch'}]
    assert calls(client, 'close_issue') == [{'number': 10}]
    assert client.rows[10]['state'] == 'closed'
    assert ('缺 wf-ruling kind=stop' in result.printed) == (terminal == '停止')
    assert [name for name, _ in client.calls if name in WRITES][-2:] == ['close_issue', 'post_comment']


def test_terminal_pr_ci_ancestor_branch_status_only_print(setup):
    client, kwargs = setup('結案', '待確認')
    client.responses.update(pulls_for_branch=[{'number': 21}, {'number': 22}],
        pull_request=lambda number: {'number': number, 'state': 'open', 'merged': False,
                                    'mergeable': False, 'head': {'sha': SHA}, 'merge_commit_sha': 'b' * 40},
        ci_checks={'check_runs': [{'conclusion': 'failure'}], 'statuses': [{'state': 'failure'}]},
        is_ancestor=False)
    result = move(10, '完成', **kwargs)
    assert result.rc == 0
    assert calls(client, 'pull_request') == [{'number': 21}, {'number': 22}]
    assert calls(client, 'ci_checks') == [{'sha': SHA}, {'sha': SHA}]
    assert calls(client, 'is_ancestor') == [{'sha': 'b' * 40, 'branch': 'main'}] * 2
    assert sum('"conclusion": "failure"' in line for line in result.printed) == 2
    assert sum('是否 main 祖先：False' in line for line in result.printed) == 2
    assert calls(client, 'close_issue') == [{'number': 10}]


@pytest.mark.parametrize('mode', ['body', 'projection'])
def test_readback_mismatch_single_d3(setup, monkeypatch, mode):
    client, kwargs = setup()
    if mode == 'body':
        monkeypatch.setattr(client, 'update_card_body', lambda *a, **k: client.calls.append(('update_card_body', {})))
    else:
        monkeypatch.setattr(client, 'write_project_field', lambda *a: client.calls.append(('write_project_field', {})))
    result = move(10, '進行中', **kwargs)
    reject(client, result, 'D3', after_write=True)
    assert result.reason == '回讀不等'


@pytest.mark.parametrize('body', ['```json wf-card\n{\n```', block('wf-card', []), block('wf-card', None)])
def test_card_parse_d3(setup, body):
    client, kwargs = setup()
    client.rows[10]['body'] = body
    reject(client, move(10, '進行中', **kwargs), 'D3')


def test_illegal_plan_precedes_expand(setup, monkeypatch):
    client, kwargs = setup(stage_plan=['需求', '結案'])
    monkeypatch.setattr('wf.verbs.move.expand', lambda *a, **k: pytest.fail('不得先 expand'))
    reject(client, move(10, '進行中', **kwargs), 'D3')


def test_no_project_print_forwarded_and_projection_skipped(setup):
    client, kwargs = setup(project=False)
    result = move(10, '進行中', **kwargs)
    assert result.rc == 0
    assert result.printed.count('無 Project 設定') == 1
    assert not calls(client, 'project') and not calls(client, 'write_project_field')


def test_projection_reconciliation_then_body_write(setup):
    client, kwargs = setup()
    client.board['items'][0]['fieldValues']['狀態'] = {'name': '退回'}
    result = move(10, '進行中', **kwargs)
    assert result.rc == 0
    assert '重寫投影欄：狀態' in result.printed
    writes = [name for name, _ in client.calls if name in WRITES]
    assert writes[:2] == ['write_project_field', 'update_card_body']


def test_preflight_before_reconcile_mutation(setup):
    client, kwargs = setup()
    client.board['items'][0]['fieldValues']['狀態'] = {'name': '退回'}
    client.options['狀態'] = [o for o in client.options['狀態'] if o['name'] != '進行中']
    reject(client, move(10, '進行中', **kwargs), 'D3')


def test_argument_adapter(setup, capsys):
    client, kwargs = setup(project=False)
    kwargs.pop('emit')
    assert run(['10', '--to', '進行中', '--actor', 'executor:cli', '--source-sha', SHA, '--ruling', URL], **kwargs) == 0
    assert read_card(client.rows[10]['body'])['owner']['actor'] == 'cli'
    assert '無 Project 設定' in capsys.readouterr().out


def test_negative_controls_network_and_rejection_oracle(setup):
    with pytest.raises(AssertionError, match='S08_NETWORK_DENIED'):
        subprocess.run(['gh', 'api', 'negative-control'])
    with socket.socket() as connection:
        with pytest.raises(AssertionError, match='S08_NETWORK_DENIED'):
            connection.connect(('127.0.0.1', 9))
    client, kwargs = setup()
    good = move(10, '進行中', **kwargs)
    with pytest.raises(AssertionError):
        reject(client, good, 'D1')
    print('負控：網路與子程序均響 S08_NETWORK_DENIED；成功轉移冒充 D1 拒收被斷言抓到')
