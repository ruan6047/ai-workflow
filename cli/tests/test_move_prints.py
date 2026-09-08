"""消費 core/verbs.md §1 move 印項、core/ruling.md 必要鍵、core/tiers.md §1；S08 驗收。"""
import json

import pytest

from wf.gh.client import NotFound, PermissionDenied, TransportError
from wf.verbs.move import move
from .test_move_core import setup, catalog, deny_network, calls, reject, URL, SHA, PLAN
from .test_open_verb import block, expected_card, issue


@pytest.mark.parametrize('stage,state,to', [('需求', '待確認', '清單'),
    ('執行', '進行中', '阻塞'), ('結案', '待確認', '停止'),
    ('審核', '待確認', '結案/待確認'), ('審核', '待確認', '審核/退回')])
def test_missing_ruling_each_core_trigger(setup, stage, state, to):
    client, kwargs = setup(stage, state)
    result = move(10, to, **kwargs)
    assert result.rc == 0
    assert '缺 --ruling' in result.printed


def test_leaving_requirement_missing_creation_fields_from_source(setup):
    client, kwargs = setup('需求', '待確認', core_pain='', tier='T2', stage_plan=['需求', '執行', '審核', '結案'])
    result = move(10, '執行/待辦', **kwargs)
    assert result.rc == 0
    assert '缺欄清單：core_pain、feature、non_scope、list_convergence、tier_basis、exec_capability、review_capability、db_scope、resources、when、service_goal' in result.printed
    assert 'T2+ 而 stage_plan 缺規劃' in result.printed


@pytest.mark.parametrize('acceptance,verification,expected', [
    ([], [], ['acceptance 空', 'verification 空']),
    (['驗收'], [], ['verification 空']),
    ([], [{'item': '驗證', 'who': '人'}], ['acceptance 空']),
    (['驗收'], [{'item': '驗證', 'who': '人'}], [])])
def test_leaving_planning_acceptance_verification(setup, acceptance, verification, expected):
    client, kwargs = setup('規劃', '待確認', acceptance=acceptance, verification=verification)
    result = move(10, '執行/待辦', **kwargs)
    assert result.rc == 0
    assert [line for line in result.printed if line in ('acceptance 空', 'verification 空')] == expected


@pytest.mark.parametrize('grilling', [None, URL])
def test_t4_grilling_print(setup, grilling):
    client, kwargs = setup('規劃', '待確認', tier='T4', grilling=grilling)
    result = move(10, '執行/待辦', **kwargs)
    assert result.rc == 0
    assert ('T4 而 grilling 空' in result.printed) == (grilling is None)


@pytest.mark.parametrize('tier', ['T0', 'T1', 'T2', 'T3', 'T4', None])
def test_tier_planning_missing_only_print(setup, tier):
    client, kwargs = setup(tier=tier, stage_plan=['需求', '執行', '審核', '結案'])
    result = move(10, '進行中', **kwargs)
    assert result.rc == 0
    assert ('T2+ 而 stage_plan 缺規劃' in result.printed) == (tier in ('T2', 'T3', 'T4'))


@pytest.mark.parametrize('to,legal', [('需求/退回', True), ('清單', True),
    ('需求/阻塞', True), ('執行/待辦', False), ('規劃/待辦', False), ('結案/待確認', False)])
def test_empty_plan_requirement_edges_only(setup, to, legal):
    client, kwargs = setup('需求', '待確認', stage_plan=[])
    result = move(10, to, **kwargs)
    assert 'stage_plan 空（合成表只有需求階段）' in result.printed
    if legal:
        assert result.rc == 0
    else:
        reject(client, result, 'D1')


@pytest.mark.parametrize('body', ['wf:ruling\n准許；kind=stop',
    block('wf-note', {'text': 'wf-ruling kind=stop', 'origin': URL}),
    '```json wf-ruling\n{\n```'])
def test_prose_first_line_and_note_cannot_supply_ruling(setup, body):
    client, kwargs = setup('結案', '待確認')
    client.responses['comment']['body'] = body
    result = move(10, '停止', ruling=URL, **kwargs)
    assert result.rc == 0
    assert '裁定留言無 wf-return／wf-ruling 區塊' in result.printed
    assert '裁定留言作者：requester-account' in result.printed
    assert '缺 wf-ruling kind=stop' in result.printed


def test_other_card_prints_both_ids(setup):
    client, kwargs = setup(rows=[issue(20, expected_card(card_id='WF-020', source_issue=20))])
    client.responses['comment']['issue_url'] = 'https://api.github.com/repos/fake/repo/issues/20'
    result = move(10, '進行中', ruling=URL.replace('/10#', '/20#'), **kwargs)
    assert result.rc == 0
    assert '裁定留言不在本卡：WF-001、WF-020' in result.printed


@pytest.mark.parametrize('kind,missing', [('block', ['reason', 'waiting_on', 'unblock_condition']),
    ('stop', ['reason', 'revive_condition', 'reversal_handle']),
    ('withdraw', ['reason']), ('tier_change', ['reason']), ('signoff', ['reason']), ('other', ['reason'])])
def test_ruling_required_keys_each_kind(setup, kind, missing):
    client, kwargs = setup()
    client.responses['comment']['body'] = block('wf-ruling', {'kind': kind})
    result = move(10, '進行中', ruling=URL, **kwargs)
    assert result.rc == 0
    for key in missing:
        assert any(key in line for line in result.printed), (key, result.printed)
    client.calls.clear()
    client.responses['comment']['body'] = block('wf-ruling', {'kind': kind, **dict.fromkeys(missing, '')})
    result = move(10, '待確認', ruling=URL, **kwargs)
    assert result.rc == 0
    assert not any(line.startswith('wf-ruling') for line in result.printed)


@pytest.mark.parametrize('value', [{'kind': 'stop', 'reason': 1}, {'kind': 'unknown'},
                                  {'kind': []}, {'kind': {}}, [], 'stop'])
def test_ruling_type_and_enum_only_print(setup, value):
    client, kwargs = setup()
    client.responses['comment']['body'] = block('wf-ruling', value)
    result = move(10, '進行中', ruling=URL, **kwargs)
    assert result.rc == 0
    assert any(line.startswith('wf-ruling：') for line in result.printed)


@pytest.mark.parametrize('kind,to', [('block', '阻塞'), ('stop', '停止')])
def test_expected_kind_filled(setup, kind, to):
    client, kwargs = setup('結案', '待確認')
    ruling = {'kind': kind, 'reason': '', **({'waiting_on': '', 'unblock_condition': ''} if kind == 'block'
                                          else {'revive_condition': '', 'reversal_handle': ''})}
    client.responses['comment']['body'] = '任意首行\n' + block('wf-ruling', ruling) + '散文不解析'
    result = move(10, to, ruling=URL, **kwargs)
    assert result.rc == 0
    assert not any('缺' in line for line in result.printed)


@pytest.mark.parametrize('has_return', [False, True])
def test_leaving_review_expects_return_block(setup, has_return):
    client, kwargs = setup('審核', '待確認')
    if has_return:
        client.responses['comment']['body'] = 'wf:move\n' + block('wf-return', {'role': 'reviewer'})
    result = move(10, '結案/待確認', ruling=URL, **kwargs)
    assert result.rc == 0
    assert ('缺 wf-return 區塊' in result.printed) == (not has_return)


@pytest.mark.parametrize('url', ['not-a-url', 'https://github.com/other/repo/issues/10#issuecomment-1', URL])
def test_nonexistent_ruling_d4(setup, url):
    client, kwargs = setup()
    def not_found(**kwargs):
        raise NotFound('404')
    client.responses['comment'] = not_found
    reject(client, move(10, '進行中', ruling=url, **kwargs), 'D4')


@pytest.mark.parametrize('error', [PermissionDenied, TransportError])
@pytest.mark.parametrize('method,options', [('comment', {'ruling': URL}), ('commit_exists', {'source_sha': SHA})])
def test_unknown_remote_failure_not_claimed_d4(setup, error, method, options):
    client, kwargs = setup()
    def fail(**kwargs):
        raise error('not an existence result')
    client.responses[method] = fail
    with pytest.raises(error):
        move(10, '進行中', **options, **kwargs)
    assert not calls(client, 'post_comment')


def test_ruling_required_keys_reload_original(setup):
    client, kwargs = setup()
    path = kwargs['root'] / 'core/ruling.md'
    path.write_text(path.read_text().replace('block＝reason、waiting_on、unblock_condition', 'block＝reason、waiting_on、revive_condition'))
    client.responses['comment']['body'] = block('wf-ruling', {'kind': 'block', 'reason': '', 'waiting_on': ''})
    result = move(10, '阻塞', ruling=URL, **kwargs)
    assert result.rc == 0
    assert 'wf-ruling kind=block 缺必要鍵：revive_condition' in result.printed
    assert not any('unblock_condition' in line for line in result.printed)
    print('負控：原件 block 必要鍵改為 revive_condition，輸出隨原件改變')
