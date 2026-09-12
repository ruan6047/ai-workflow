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
    result = edit(1, [assignment] if isinstance(assignment, str) else assignment,
                  client=fake, catalog=catalog, **kwargs)
    return result, fake


def rejected(result, fake, code, key=''):
    assert result.rc != 0
    comments = mutations(fake, 'post_comment')
    assert len(comments) == 1
    assert comments[0][1]['first_line'] == 'wf:reject'
    assert comments[0][1]['body'].startswith('拒收・' + code + '・')
    assert key in comments[0][1]['body']
    assert not mutations(fake, 'update_card_body')
    assert not mutations(fake, 'write_project_field')


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
    assert not mutations(fake, 'write_project_field')


def test_null_parent_needs_no_board(card, catalog):
    card['parent'] = 'WF-002'
    result, fake = run(card, catalog, 'parent=null')
    assert result.rc == 0 and result.card['parent'] is None
    assert not any(name == 'project' for name, kw in fake.calls)


def test_tier_defers_projection_without_project_config(card, catalog):
    """`.wf/modules.json` 無 project：投影鍵也只寫卡面，⛔ 不碰 Project（FINAL-2a 的降級路徑）。"""
    result, fake = run(card, catalog, 'tier="T3"')
    assert result.rc == 0
    assert not any(name in ('project', 'write_project_field') for name, kw in fake.calls)
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
    """adds.counters 欄由 edit 改＝印一行並照寫（宣告即印，不看啟用）；未宣告於 schema 的欄仍是 D3。"""
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
    """負控：非計數欄不印「模組欄由 move 寫」。"""
    result, fake = run(card, catalog, 'feature="x"')
    assert result.rc == 0
    assert COUNTER_PRINT not in capsys.readouterr().out


def test_null_parent_card_block_is_skipped_then_d4(card, catalog, capsys):
    """null 區塊探針：板上父卡的 wf-card 區塊值為 null ⇒ 印略過、parent 視為不存在（D4）；負控＝合法父卡過。"""
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
    """null 區塊探針：以卡ID 查 issue 時，別的 issue 的 null／壞 JSON 區塊只略過並印，不擋。"""
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


# ── CLI-003：一次 wf edit 多個 --set 的原子提交（core/verbs.md §1 edit 列／§2） ──

SHA40 = 'a' * 40
LONG_OWNER = 'owner=' + json.dumps({'role': 'executor', 'actor': 'a' * 1025}, ensure_ascii=False)


def card_face(fake, number=1):
    """假遠端當下的卡面 JSON（零寫入時＝原卡）。"""
    from wf.verbs._common import block_object
    return block_object(fake.responses['issue'](number=number)['body'], 'wf-card')


def edit_lines(fake):
    comment, = [kw for name, kw in mutations(fake, 'post_comment') if kw['first_line'] == 'wf:edit']
    return comment['body'].split('\n')


def wrote_nothing(result, fake, code, needle=''):
    """整次零寫入＋恰 1 則 wf:reject（A3／A4／A11 共用）。"""
    rejected(result, fake, code, needle)
    assert not [kw for name, kw in mutations(fake, 'post_comment')
                if kw['first_line'] == 'wf:edit']


def test_multi_set_one_write_one_comment(card, catalog):
    """A1：三個不同欄（含非投影鍵）一次提交 ⇒ 1 次 update_card_body、1 則 wf:edit、本文 3 列。"""
    result, fake = run(card, catalog, ['feature="甲"', 'when="乙"', 'tier="T3"'])
    assert result.rc == 0
    assert result.card['feature'] == '甲' and result.card['when'] == '乙'
    assert result.card['tier'] == 'T3'
    assert len(mutations(fake, 'update_card_body')) == 1
    comments = mutations(fake, 'post_comment')
    assert len(comments) == 1 and comments[0][1]['first_line'] == 'wf:edit'
    assert len(edit_lines(fake)) == 3


def test_multi_set_comment_lines_and_order(card, catalog):
    """A2：每列＝「<欄>、<原值 hash> → <新值 hash>」，列序＝argv 序；單欄本文＝基線單列無尾換行。"""
    from wf.verbs.edit import _hash  # F-執行者-04：import 驗證器，⛔ 不重打 sha256 常數
    argv = ['when="乙"', 'feature="甲"', 'service_goal="丙"']
    result, fake = run(card, catalog, argv)
    assert result.rc == 0
    expected = [f'when、{_hash(card["when"])} → {_hash("乙")}',
                f'feature、{_hash(card["feature"])} → {_hash("甲")}',
                f'service_goal、{_hash(card["service_goal"])} → {_hash("丙")}']
    comment, = mutations(fake, 'post_comment')
    assert comment[1]['body'] == '\n'.join(expected)
    result, fake = run(card, catalog, ['feature="甲"'])
    single, = mutations(fake, 'post_comment')
    assert single[1]['body'] == f'feature、{_hash(card["feature"])} → {_hash("甲")}'
    assert '\n' not in single[1]['body'] and not single[1]['body'].endswith('\n')


@pytest.mark.parametrize('argv,names', [
    (['feature="甲"', 'feature="乙"'], ['feature']),
    (['notes+={"id":"T-需求-01","text":"x","origin":"https://a.test"}', 'notes=[]'], ['notes']),
    (['notes=[]', 'notes+={"id":"T-需求-01","text":"x","origin":"https://a.test"}'], ['notes']),
    (['feature="甲"', 'when="乙"', 'when="丙"', 'feature="丁"'], ['when', 'feature']),
])
def test_duplicate_set_is_rejected_before_any_write(card, catalog, argv, names):
    """A3：正規化後同一卡面鍵出現 2 次以上 ⇒ 整次拒收、零寫入；重複欄名依第二次出現序逐字列出。"""
    result, fake = run(card, catalog, argv)
    wrote_nothing(result, fake, 'D3', '重複欄位：' + '、'.join(names))
    assert card_face(fake) == card


def test_duplicate_notes_append_and_replace_is_rejected(card, catalog):
    """A3：notes+ 與 notes 同鍵、兩個 notes+ 亦同鍵（需求方 2026-09-12 裁定：先正規化再判重）。"""
    note = json.dumps({'id': 'T-需求-01', 'text': 'x', 'origin': 'https://a.test'},
                      ensure_ascii=False)
    for argv in (['notes+=' + note, 'notes=[]'], ['notes+=' + note, 'notes+=' + note]):
        result, fake = run(card, catalog, argv)
        wrote_nothing(result, fake, 'D3', '重複欄位：notes')
        assert card_face(fake)['notes'] == card['notes']


FAILURES = {
    'a-缺等號': 'feature',
    'b-非法JSON': 'service_goal=unquoted',
    'c-欄名不在schema': 'unknown=1',
    'd-疊加後schema不過': 'resources=[1]',
    'e-D1禁寫': 'stage="執行"',
    'f-D3禁寫': 'card_id="WF-999"',
    'g-D4來源SHA': f'source_sha="{SHA40}"',
    'h-D4父卡': 'parent="WF-999"',
}
LEGAL = 'feature="合法"'


def failing_fake(card, catalog, case):
    if case == 'g-D4來源SHA':
        fake = simulated(card, catalog)
        fake.responses['commit_exists'] = False
        return fake, {}
    if case == 'h-D4父卡':
        return (parent_fake(card, catalog, {2: card | {'card_id': 'WF-002', 'source_issue': 2}}),
                {'project_owner': 'owner', 'project_number': 1})
    return simulated(card, catalog), {}


@pytest.mark.parametrize('case', list(FAILURES))
@pytest.mark.parametrize('legal_first', [True, False])
def test_partial_failure_writes_nothing(card, catalog, case, legal_first):
    """A4：八類失敗各一組 × 合法項在前／在後 ⇒ rc≠0、零卡面寫入、零投影寫入、零 wf:edit、恰 1 則 wf:reject。"""
    fake, kwargs = failing_fake(card, catalog, case)
    argv = [LEGAL, FAILURES[case]] if legal_first else [FAILURES[case], LEGAL]
    result, fake = run(card, catalog, argv, fake=fake, **kwargs)
    wrote_nothing(result, fake, 'D1' if case == 'e-D1禁寫' else
                  ('D4' if case.startswith(('g-', 'h-')) else 'D3'))
    assert card_face(fake)['feature'] != '合法'
    assert card_face(fake) == card


def test_spec_version_bumps_once_for_multi_spec_fields(card, catalog):
    """A5：四個規格欄一次提交 ⇒ spec_version 恰 +1；混入非規格欄不變；只改非規格欄 ⇒ +0。"""
    spec_argv = [key + '=' + json.dumps(value, ensure_ascii=False) for key, value in SPEC_VALUES]
    result, _ = run(card, catalog, spec_argv)
    assert result.rc == 0 and result.card['spec_version'] == card['spec_version'] + 1
    result, _ = run(card, catalog, spec_argv + ['feature="甲"'])
    assert result.rc == 0 and result.card['spec_version'] == card['spec_version'] + 1
    result, _ = run(card, catalog, ['feature="甲"', 'when="乙"'])
    assert result.rc == 0 and result.card['spec_version'] == card['spec_version']


def test_multi_set_value_with_equals_and_newline(card, catalog, tmp_path):
    """A6：值含 =／換行／JSON 陣列逐字寫入；且 edit.py 單檔只有一處 partition('=')、⛔ 無第二 parser。"""
    from wf.verbs.edit import main
    fake = simulated(card, catalog)
    fake.responses['issues'] = [{'number': 1, 'body': body(card)}]
    goal = '第一行\n第二行=x'
    assert main(['WF-001', '--set', 'feature="a=b"',
                 '--set', 'service_goal=' + json.dumps(goal, ensure_ascii=False),
                 '--set', 'resources=' + json.dumps(['file:a=b', 'file:c'], ensure_ascii=False)],
                client=fake, catalog=catalog, root=tmp_path) == 0
    written = mutations(fake, 'update_card_body')[0][1]['card_json']
    assert written['feature'] == 'a=b'
    assert written['service_goal'] == goal
    assert written['resources'] == ['file:a=b', 'file:c']
    source = (ROOT / 'cli/src/wf/verbs/edit.py').read_text(encoding='utf-8')
    assert source.count("partition('=')") == 1, source.count("partition('=')")
    assert "split('=')" not in source and 're.split' not in source


def test_multi_set_all_same_values_is_silent(card, catalog):
    """A7：全項等值 ⇒ rc=0、零寫入零留言；部分等值 ⇒ wf:edit 只列實際變動的欄。"""
    card['feature'], card['when'] = '甲', '乙'
    result, fake = run(card, catalog, ['feature="甲"', 'when="乙"'])
    assert result.rc == 0 and result.card == card
    assert not mutations(fake)
    result, fake = run(card, catalog, ['feature="甲"', 'when="丙"', 'service_goal="丁"'])
    assert result.rc == 0
    assert [line.split('、')[0] for line in edit_lines(fake)] == ['when', 'service_goal']


def test_multi_set_projection_written_once(catalog, capsys):
    """A8：變動鍵含投影鍵 ⇒ 五欄依 §2 序回寫恰 1 次；不含投影鍵 ⇒ ⛔ 不碰 Project；審核階段仍只另貼 1 則。"""
    from .test_brief_sections import card as brief_card
    from .test_card_gate_and_projection import board_client
    from wf.verbs.edit import edit
    client = board_client(catalog, brief_card(tier='T3'))
    result = edit(10, ['tier="T4"', 'feature="改過"'], client=client, catalog=catalog,
                  project_owner='fake', project_number=1, emit=lambda line: None)
    assert result.rc == 0 and result.card['tier'] == 'T4'
    written = [prepared[2]['fieldId'] for name, prepared in client.calls
               if name == 'write_project_field']
    assert written == list(projection(catalog))
    assert len([1 for name, _ in client.calls if name == 'update_card_body']) == 1


def test_multi_set_without_projection_key_leaves_the_board_alone(catalog):
    """A8 負控：多欄提交但變動鍵不含投影鍵 ⇒ 零 write_project_field，板上級別不動。"""
    from .test_brief_sections import card as brief_card
    from .test_card_gate_and_projection import board_client
    from wf.verbs.edit import edit
    client = board_client(catalog, brief_card(tier='T3'))
    result = edit(10, ['feature="改過"', 'when="乙"'], client=client, catalog=catalog,
                  project_owner='fake', project_number=1, emit=lambda line: None)
    assert result.rc == 0
    assert [name for name, _ in client.calls if name == 'write_project_field'] == []
    assert client.board['items'][0]['fieldValues']['級別'] == {'name': 'T3'}


def test_multi_set_during_review_posts_one_extra_comment(card, catalog):
    """A8：審核階段的多欄提交仍只另貼恰 1 則 edit during review（該次共 2 則）。"""
    card['stage'] = '審核'
    result, fake = run(card, catalog, ['feature="甲"', 'when="乙"'])
    assert result.rc == 0
    comments = mutations(fake, 'post_comment')
    assert [kw['first_line'] for _, kw in comments] == ['wf:edit', 'wf:edit']
    assert len(comments[0][1]['body'].split('\n')) == 2
    assert comments[1][1]['body'] == 'edit during review'


LAYER_PAIRS = {  # ①賦值語法 → ②重複欄位 → ③禁寫 → ④schema／stage_plan → ⑤D4 → ⑥投影預算與對帳
    '①×②': (['feature', 'when="甲"', 'when="乙"'], 'D3', '--set 須為欄=JSON'),
    '②×③': (['when="甲"', 'when="乙"', 'stage="執行"'], 'D3', '重複欄位：when'),
    '③×④': (['stage="執行"', 'unknown=1'], 'D1', 'stage 只由 move 寫'),
    '④×⑤': (['unknown=1', f'source_sha="{SHA40}"'], 'D3', 'unknown'),
    '⑤×⑥': ([f'source_sha="{SHA40}"', LONG_OWNER], 'D4', 'source_sha 不在遠端'),
}


@pytest.mark.parametrize('pair', list(LAYER_PAIRS))
def test_error_priority_across_layers(card, catalog, pair):
    """A11：相鄰層雙錯的正序與逆序，wf:reject 本文逐字相同且指向較前的層；兩序皆零寫入。"""
    argv, code, needle = LAYER_PAIRS[pair]
    bodies = []
    for order in (argv, list(reversed(argv))):
        fake = simulated(card, catalog)
        fake.responses['commit_exists'] = False
        result, fake = run(card, catalog, order, fake=fake)
        wrote_nothing(result, fake, code, needle)
        assert card_face(fake) == card
        bodies.append(mutations(fake, 'post_comment')[0][1]['body'])
    assert bodies[0] == bodies[1], bodies


def test_same_layer_reports_first_in_input_order(card, catalog):
    """A11：同層多錯回報 argv 中 --set 出現順序最前的那一個（③、④、⑤ 三層各一組正逆序）。"""
    for argv, code, needle in ((['stage="執行"', 'card_id="WF-999"'], 'D1', 'stage 只由 move 寫'),
                               (['card_id="WF-999"', 'stage="執行"'], 'D3', 'card_id 不可由 edit 改')):
        result, fake = run(card, catalog, argv)
        wrote_nothing(result, fake, code, needle)
    for first, second in (('alpha_unknown', 'beta_unknown'), ('beta_unknown', 'alpha_unknown')):
        result, fake = run(card, catalog, [first + '=1', second + '=2'])
        wrote_nothing(result, fake, 'D3', first)
        body_text = mutations(fake, 'post_comment')[0][1]['body']
        assert body_text.index(first) < body_text.index(second), body_text
    for argv, needle in (([f'source_sha="{SHA40}"', 'parent="WF-999"'], 'source_sha 不在遠端'),
                         (['parent="WF-999"', f'source_sha="{SHA40}"'], 'parent 不存在')):
        fake = parent_fake(card, catalog, {2: card | {'card_id': 'WF-002', 'source_issue': 2}})
        fake.responses['commit_exists'] = False
        result, fake = run(card, catalog, argv, fake=fake,
                           project_owner='owner', project_number=1)
        wrote_nothing(result, fake, 'D4', needle)
    result, fake = run(card, catalog, ['feature', 'when'])  # 同層兩個缺 = 分隔
    wrote_nothing(result, fake, 'D3', '--set 須為欄=JSON')


@pytest.mark.parametrize('bare', ['feature="A"', '', 'notes+=[]'])
def test_edit_rejects_bare_str_assignments(card, catalog, bare):
    """A12：第二參數為裸 str ⇒ 立即 TypeError 逸出，且零卡面寫入、零投影寫入、零留言（含零 wf:reject）。"""
    from wf.verbs.edit import edit
    fake = simulated(card, catalog)
    with pytest.raises(TypeError):
        edit(1, bare, client=fake, catalog=catalog)
    assert not mutations(fake)  # ⛔ 不以 rc≠0 當通過證據：逐字元迭代路徑的 rc 也非零
    assert not fake.calls


@pytest.mark.parametrize('seq', [list, tuple])
def test_edit_accepts_list_and_tuple(card, catalog, seq):
    """A12 正控：list 與 tuple 皆正常。"""
    from wf.verbs.edit import edit
    fake = simulated(card, catalog)
    result = edit(1, seq(['feature="甲"', 'when="乙"']), client=fake, catalog=catalog)
    assert result.rc == 0 and result.card['feature'] == '甲' and result.card['when'] == '乙'


def test_run_passes_argv_list_to_edit(monkeypatch, tmp_path):
    """A12：CLI 介面不變——run 以可重複 --set 收 argv，組成 list 後才傳入 edit()。"""
    from wf.verbs import edit as edit_module
    from wf.verbs._write import WriteResult
    seen = {}

    def spy(card, assignments, **kwargs):
        seen['assignments'] = assignments
        return WriteResult(0)

    monkeypatch.setattr(edit_module, 'edit', spy)
    assert edit_module.run(['WF-001', '--set', 'a=1', '--set', 'b=2'],
                           client=None, root=tmp_path, catalog=None) == 0
    assert type(seen['assignments']) is list and seen['assignments'] == ['a=1', 'b=2']
