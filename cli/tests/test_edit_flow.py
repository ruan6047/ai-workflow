"""消費 core/verbs.md §1 edit／§2、core/card-schema.md §1／§2、core/naming.md §3。"""
from copy import deepcopy
import hashlib
import json

import pytest

from wf.compose.blocks import Block, Catalog, projection
from wf.gh.client import NotFound, PermissionDenied, TransportError
from wf.gh.writes import WriteMixin
from wf.verbs._write import reconcile
from .test_compose_schema import ROOT, card, catalog
from .test_write_flow import body, mutations, simulated


def run(card, catalog, assignment, *, fake=None, **kwargs):
    from wf.verbs.edit import edit
    fake = fake or simulated(card, catalog)
    result = edit(1, assignment, client=fake, catalog=catalog, **kwargs)
    return result, fake


def rejected(result, fake, code, key=''):
    assert result.rc != 0
    comments = mutations(fake, 'post_comment')
    assert len(comments) == 1
    assert comments[0][1]['first_line'] == 'wf:reject'
    assert comments[0][1]['body'].startswith('拒收・' + code + '・')
    assert key in comments[0][1]['body']
    assert not mutations(fake, 'update_card_body')
    assert not mutations(fake, 'set_project_field')


@pytest.mark.parametrize('key,code', [('card_id', 'D3'), ('source_issue', 'D3'),
                                      ('stage', 'D1'), ('state', 'D1')])
@pytest.mark.parametrize('same', [False, True])
def test_forbidden_keys(card, catalog, key, code, same):
    value = card[key] if same else (2 if key == 'source_issue' else 'changed')
    result, fake = run(card, catalog, key + '=' + json.dumps(value))
    rejected(result, fake, code, key)


SPEC_VALUES = [('acceptance', ['驗收']), ('verification', [{'item': '驗證', 'who': '執行者'}]),
               ('non_scope', ['排除']), ('resources', ['a'])]


@pytest.mark.parametrize('key,value', SPEC_VALUES)
def test_spec_version(card, catalog, key, value):
    result, fake = run(card, catalog, key + '=' + json.dumps(value))
    assert result.rc == 0
    assert result.card[key] == value
    assert result.card['spec_version'] == card['spec_version'] + 1
    assert len(mutations(fake, 'post_comment')) == 1


@pytest.mark.parametrize('key,value', SPEC_VALUES + [('feature', '字串')])
def test_same_value_is_silent(card, catalog, key, value):
    card[key] = value
    result, fake = run(card, catalog, key + '=' + json.dumps(value))
    assert result.rc == 0 and result.card == card
    assert not mutations(fake)


def test_hash_and_non_spec_version(card, catalog):
    value = {'role': 'executor', 'actor': '繁體中文'}
    card['owner'] = {'actor': 'before', 'role': 'pm'}
    result, fake = run(card, catalog, 'owner=' + json.dumps(value))
    assert result.rc == 0 and result.card['spec_version'] == card['spec_version']
    hashes = [hashlib.sha256(json.dumps(v, sort_keys=True, ensure_ascii=False,
               separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
              for v in (card['owner'], value)]
    comment, = mutations(fake, 'post_comment')
    assert comment[1]['first_line'] == 'wf:edit'
    assert comment[1]['body'] == f'owner、{hashes[0]} → {hashes[1]}'


@pytest.mark.parametrize('bad', [False, True])
def test_notes_append(card, catalog, bad):
    card['notes'] = [{'id': 'T-需求-01', 'text': '原條文', 'origin': 'https://example.test/a'}]
    original = deepcopy(card)
    note = {'id': 'T-審核-02', 'text': '新條文', 'origin': 'https://example.test/b'}
    if bad:
        del note['origin']
    result, fake = run(card, catalog, 'notes+=' + json.dumps(note))
    if bad:
        rejected(result, fake, 'D3', 'origin')
    else:
        assert result.rc == 0 and result.card['notes'] == original['notes'] + [note]
        assert card == original


def test_notes_replace_is_allowed(card, catalog):
    card['notes'] = [{'id': 'T-需求-01', 'text': '原條文', 'origin': 'https://example.test'}]
    result, fake = run(card, catalog, 'notes=[]')
    assert result.rc == 0 and result.card['notes'] == []


@pytest.mark.parametrize('stage', ['需求', '審核'])
def test_review_comments(card, catalog, stage, capsys):
    card['stage'] = stage
    result, fake = run(card, catalog, 'feature="新值"')
    assert result.rc == 0
    comments = mutations(fake, 'post_comment')
    assert len(comments) == (2 if stage == '審核' else 1)
    assert all(c[1]['first_line'] == 'wf:edit' for c in comments)
    output = capsys.readouterr().out
    if stage == '審核':
        assert comments[1][1]['body'] == 'edit during review'
        assert '卡在審核階段' in output
    else:
        assert '卡在審核階段' not in output


@pytest.mark.parametrize('ruling', [None, 'missing', 'exists'])
def test_ruling(card, catalog, ruling, capsys):
    fake = simulated(card, catalog)
    fake.repo = 'fake/repo'
    url = None if ruling is None else 'https://github.com/fake/repo/issues/1#issuecomment-9'
    def comment(**kwargs):
        if ruling == 'missing':
            raise NotFound('missing')
        return {'issue_url': 'https://api.github.com/repos/fake/repo/issues/1'}
    fake.responses['comment'] = comment
    fake.comment_from_url = lambda u: WriteMixin.comment_from_url(fake, u)
    result, fake = run(card, catalog, 'feature="更新"', fake=fake, ruling=url)
    if ruling == 'missing':
        rejected(result, fake, 'D4', 'ruling')
    else:
        assert result.rc == 0
    assert ('無裁定連結' in capsys.readouterr().out) == (ruling is None)


def parent_fake(card, catalog, parents):
    fake = simulated(card, catalog)
    fake.repo = 'fake/repo'
    read_current = fake.responses['issue']
    fake.responses['issue'] = lambda number: read_current(number=number) if number == 1 else {'body': body(parents[number])}
    fake.responses['project'] = {'items': [
        {'id': str(n), 'isArchived': False, 'content': {'__typename': 'Issue', 'number': n,
         'repository': {'nameWithOwner': fake.repo}}} for n in parents]}
    return fake


@pytest.mark.parametrize('depth', [0, 1, 2, 3])
def test_parent_depth(card, catalog, depth, capsys):
    parents = {n: card | {'card_id': f'WF-{n:03}', 'source_issue': n,
               'parent': f'WF-{n+1:03}' if n < depth+1 else None} for n in range(2, depth+2)}
    fake = parent_fake(card, catalog, parents)
    result, fake = run(card, catalog, 'parent="WF-002"', fake=fake,
                       project_owner='owner', project_number=1)
    if depth == 0:
        rejected(result, fake, 'D4', 'parent')
    else:
        assert result.rc == 0 and result.card['parent'] == 'WF-002'
    assert ('上限 2' in capsys.readouterr().out) == (depth > 2)
    # D4 parent 盤點仍不取投影欄；§2 對帳另取五欄（本卡不在板上，對帳止於取不到 item_id）。
    calls = [kw['field_names'] for name, kw in fake.calls if name == 'project']
    assert calls == ([[]] if depth == 0 else [[], list(projection(catalog))])
    assert not mutations(fake, 'set_project_field')


def test_null_parent_needs_no_board(card, catalog):
    card['parent'] = 'WF-002'
    result, fake = run(card, catalog, 'parent=null')
    assert result.rc == 0 and result.card['parent'] is None
    assert not any(name == 'project' for name, kw in fake.calls)


def test_tier_defers_projection_without_project_config(card, catalog):
    """`.wf/modules.json` 無 project：投影鍵也只寫卡面，⛔ 不碰 Project（FINAL-2a 的降級路徑）。"""
    result, fake = run(card, catalog, 'tier="T3"')
    assert result.rc == 0
    assert not any(name in ('project', 'set_project_field') for name, kw in fake.calls)
    changed = reconcile(result.card, client=fake, catalog=catalog, project_owner='owner',
                        project_number=1, item_id='ITEM')
    assert changed == ['級別']


@pytest.mark.parametrize('plan,ok', [(['需求', '執行', '審核', '結案'], True),
    (['需求', '執行', '審核'], False), ([], True), (['需求', '審核', '執行', '結案'], False)])
def test_stage_plan(card, catalog, plan, ok, capsys):
    card['stage_plan'] = ['需求', '規劃', '執行', '審核', '結案']
    result, fake = run(card, catalog, 'stage_plan=' + json.dumps(plan))
    if ok:
        assert result.rc == 0 and result.card['stage_plan'] == plan
    else:
        rejected(result, fake, 'D3', 'stage_plan')
    assert 'stage_plan' not in capsys.readouterr().out


COUNTER_PRINT = '模組欄由 `move` 寫'


@pytest.mark.parametrize('key', ['escalation_count', 'new_counter'])
def test_declared_counters_print_and_write(card, catalog, key, capsys):
    """C09：adds.counters 欄由 edit 改＝印一行並照寫（宣告即印，不看啟用）；未宣告於 schema 的欄仍是 D3。"""
    module = {'name': 'fixture', 'adds': {'counters': [key]}}
    catalog = Catalog(catalog.blocks + [Block('yaml wf-module', module, '', catalog.blocks[0].source)], catalog.schemas)
    result, fake = run(card, catalog, key + '=1')
    assert COUNTER_PRINT in capsys.readouterr().out
    if key == 'escalation_count':
        assert result.rc == 0 and result.card[key] == 1
        assert mutations(fake, 'update_card_body')[0][1]['card_json'][key] == 1
        assert [kw['first_line'] for _, kw in mutations(fake, 'post_comment')] == ['wf:edit']
    else:
        rejected(result, fake, 'D3', key)  # 負控：schema 沒有的鍵仍拒


def test_non_counter_key_has_no_counter_print(card, catalog, capsys):
    """C09 負控：非計數欄不印「模組欄由 move 寫」。"""
    result, fake = run(card, catalog, 'feature="x"')
    assert result.rc == 0
    assert COUNTER_PRINT not in capsys.readouterr().out


def test_null_parent_card_block_is_skipped_then_d4(card, catalog, capsys):
    """第 9 條探針：板上父卡的 wf-card 區塊值為 null ⇒ 印略過、parent 視為不存在（D4）；負控＝合法父卡過。"""
    fake = parent_fake(card, catalog, {2: card | {'card_id': 'WF-002'}})
    read = fake.responses['issue']
    fake.responses['issue'] = lambda number: {'body': '```json wf-card\nnull\n```'} if number == 2 else read(number)
    result, fake = run(card, catalog, 'parent="WF-002"', fake=fake, project_owner='owner', project_number=1)
    rejected(result, fake, 'D4', 'parent')
    assert '略過無法解析的 issue #2' in capsys.readouterr().out
    fake = parent_fake(card, catalog, {2: card | {'card_id': 'WF-002'}})
    result, fake = run(card, catalog, 'parent="WF-002"', fake=fake, project_owner='owner', project_number=1)
    assert result.rc == 0 and '略過' not in capsys.readouterr().out


def test_card_id_lookup_skips_unparsable_issues(card, catalog, tmp_path, capsys):
    """第 9 條探針：以卡ID 查 issue 時，別的 issue 的 null／壞 JSON 區塊只略過並印，不擋。"""
    from wf.verbs.edit import main
    fake = simulated(card, catalog)
    fake.responses['issues'] = [{'number': 8, 'body': '```json wf-card\nnull\n```'},
                               {'number': 9, 'body': '```json wf-card\n{壞\n```'},
                               {'number': 1, 'body': body(card)}]
    assert main(['WF-001', '--set', 'feature="a"'], client=fake, catalog=catalog, root=tmp_path) == 0
    out = capsys.readouterr().out
    assert '略過無法解析的 issue #8' in out and '略過無法解析的 issue #9' in out
    assert mutations(fake, 'update_card_body')[0][1]['number'] == 1


@pytest.mark.parametrize('assignment', ['feature=unquoted', 'feature=', 'feature', 'feature=NaN',
    'feature=Infinity', 'feature=1e999', 'notes+={}', 'notes+=[]', 'feature+="x"', 'unknown=1',
    'stage_plan=null', 'iteration=true', 'resources=[1]'])
def test_invalid_set_is_d3(card, catalog, assignment):
    result, fake = run(card, catalog, assignment)
    rejected(result, fake, 'D3')


@pytest.mark.parametrize('exists', [True, False])
def test_source_sha(card, catalog, exists):
    fake = simulated(card, catalog)
    fake.responses['commit_exists'] = exists
    result, fake = run(card, catalog, 'source_sha=' + json.dumps('a' * 40), fake=fake)
    if exists:
        assert result.rc == 0 and result.card['source_sha'] == 'a' * 40
    else:
        rejected(result, fake, 'D4', 'source_sha')


@pytest.mark.parametrize('error', [PermissionDenied, TransportError])
def test_unknown_remote_failure_is_not_d4(card, catalog, error):
    fake = simulated(card, catalog)
    def fail(**kwargs):
        raise error('unknown')
    fake.responses['commit_exists'] = fail
    with pytest.raises(error):
        run(card, catalog, 'source_sha=' + json.dumps('a' * 40), fake=fake)
    assert not mutations(fake)


def test_readback_failure_has_no_edit_comment(card, catalog):
    fake = simulated(card, catalog, bad_body=True)
    result, fake = run(card, catalog, 'feature="new"', fake=fake)
    assert result.rc != 0 and result.reason == '回讀不等'
    assert [kw['first_line'] for name, kw in mutations(fake, 'post_comment')] == ['wf:reject']


def test_entrypoint_card_id_and_json_literal(card, catalog, tmp_path):
    from wf.verbs.edit import main
    fake = simulated(card, catalog)
    fake.responses['issues'] = [{'number': 9, 'body': '清單'}, {'number': 1, 'body': body(card)}]
    assert main(['WF-001', '--set', 'feature="a=b"'], client=fake, catalog=catalog, root=tmp_path) == 0
    assert mutations(fake, 'update_card_body')[0][1]['card_json']['feature'] == 'a=b'


def test_entrypoint_parent_uses_project_config(card, catalog, tmp_path):
    from wf.verbs.edit import main
    parent = card | {'card_id': 'WF-002', 'source_issue': 2}
    fake = parent_fake(card, catalog, {2: parent})
    config = tmp_path / '.wf'
    config.mkdir()
    (config / 'modules.json').write_text(json.dumps({'project': {'owner': 'configured', 'number': 7}}))
    assert main(['1', '--set', 'parent="WF-002"'], client=fake, catalog=catalog, root=tmp_path) == 0
    assert [kw for name, kw in fake.calls if name == 'project'] == [
        {'owner': 'configured', 'number': 7, 'field_names': []},
        {'owner': 'configured', 'number': 7, 'field_names': list(projection(catalog))}]


@pytest.mark.parametrize('excluded', ['archived', 'foreign', 'pull', 'draft'])
def test_parent_must_be_on_this_repo_board(card, catalog, excluded):
    fake = parent_fake(card, catalog, {2: card | {'card_id': 'WF-002'}})
    item = fake.responses['project']['items'][0]
    if excluded == 'archived':
        item['isArchived'] = True
    elif excluded == 'foreign':
        item['content']['repository']['nameWithOwner'] = 'other/repo'
    else:
        item['content']['__typename'] = 'PullRequest' if excluded == 'pull' else 'DraftIssue'
    result, fake = run(card, catalog, 'parent="WF-002"', fake=fake,
                       project_owner='owner', project_number=1)
    rejected(result, fake, 'D4', 'parent')


def test_runtime_schema_is_consumed(card, catalog):
    from dataclasses import replace
    changed = deepcopy(catalog.schemas['wf-card'].data)
    changed['properties']['feature']['type'] = 'integer'
    catalog = Catalog(catalog.blocks, dict(catalog.schemas, **{
        'wf-card': replace(catalog.schemas['wf-card'], data=changed)}))
    result, fake = run(card, catalog, 'feature=7')
    assert result.rc == 0 and result.card['feature'] == 7
    result, fake = run(card, catalog, 'feature="invalid"')
    rejected(result, fake, 'D3', 'feature')


def test_enabled_state_can_be_edited(card, catalog):
    card['state'] = '升級'
    result, fake = run(card, catalog, 'feature="valid"', enabled_modules=['escalation'])
    assert result.rc == 0


def test_invalid_ruling_syntax(card, catalog):
    fake = simulated(card, catalog)
    fake.repo = 'fake/repo'
    fake.comment_from_url = lambda url: WriteMixin.comment_from_url(fake, url)
    result, fake = run(card, catalog, 'feature="valid"', fake=fake, ruling='not-a-url')
    rejected(result, fake, 'D4', 'ruling')


def test_review_same_value_is_silent(card, catalog):
    card['stage'] = '審核'
    result, fake = run(card, catalog, 'feature=""')
    assert result.rc == 0 and not mutations(fake)


@pytest.mark.parametrize('bad', ['null', '{broken}', '{}\n```\n```json wf-card\n{}'])
def test_invalid_card_body(card, catalog, bad):
    fake = simulated(card, catalog)
    fake.responses['issue'] = {'body': '```json wf-card\n' + bad + '\n```'}
    result, fake = run(card, catalog, 'feature="valid"', fake=fake)
    rejected(result, fake, 'D3')
