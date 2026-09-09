"""消費 core/verbs.md §1／§2、core/card-schema.md §5、modules/resource-lock/module.md §0；
verbs/_common.py 的純讀函式與 tests/fakes.py 的 merge_base。
"""
import pytest

from .fakes import FakeGhClient
from .test_compose_schema import ROOT
from wf.compose.blocks import load_blocks, projection
from wf.gh.client import NotFound
from wf.gh.writes import CardBodyError
from wf.verbs import _common as common
from wf.verbs._write import _prepare, _values, prepare_card, projection_values


def block(label, raw):
    return f'```json {label}\n{raw}\n```\n'


def issue(number, body):
    return {'number': number, 'body': body}


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(ROOT)


@pytest.mark.parametrize('body,expected', [
    ('散文', None), (block('wf-card', '{"a": 1}'), {'a': 1})])
def test_block_object_absent_or_object(body, expected):
    assert common.block_object(body, 'wf-card', required=False) == expected


@pytest.mark.parametrize('raw', ['null', '[]', '"x"', '3'])
def test_block_object_present_non_object_raises(raw):
    with pytest.raises(CardBodyError, match='不是物件'):
        common.block_object(block('wf-card', raw), 'wf-card', required=False)


def test_block_object_required_missing_raises_like_read_card():
    with pytest.raises(CardBodyError, match='缺少'):
        common.block_object('散文', 'wf-card')
    assert common.block_object(None, 'wf-card', required=False) is None


def test_card_number_int_passthrough_and_lookup_with_skips():
    client = FakeGhClient(issues=[issue(8, block('wf-card', 'null')), issue(9, block('wf-card', '{壞')),
                                  issue(7, block('wf-card', '{"card_id": "WF-007"}'))])
    assert common.card_number(7, client) == (7, [])
    assert common.card_number('7', client) == (7, [])
    assert not client.calls  # 數字不掃描
    assert common.card_number('WF-007', client) == (7, [8, 9])
    assert client.calls == [('issues', {'state': 'all'})]
    with pytest.raises(NotFound):
        common.card_number('WF-404', client)


def content(number, repo='fake/repo', typename='Issue', archived=False):
    return {'id': f'ITEM{number}', 'isArchived': archived,
            'content': {'__typename': typename, 'number': number, 'repository': {'nameWithOwner': repo}}}


def test_board_items_filters_and_archived_switch():
    project = {'items': [content(1), content(2, archived=True), content(3, repo='other/repo'),
                         content(4, typename='PullRequest'), {'id': 'D', 'content': {'__typename': 'DraftIssue'}}]}
    assert list(common.board_items(project, 'fake/repo')) == [1]
    assert list(common.board_items(project, 'fake/repo', include_archived=True)) == [1, 2]
    assert list(common.board_items(project)) == [1, 3]
    assert common.board_items(None, 'fake/repo') == {}


def test_board_cards_skips_unparsable_and_excludes_archived():
    bodies = {1: block('wf-card', '{"card_id": "WF-001"}'), 2: block('wf-card', 'null'),
              5: block('wf-card', '{"card_id": "WF-005"}')}
    client = FakeGhClient(issue=lambda number: {'body': bodies[number]})
    project = {'items': [content(1), content(2), content(5, archived=True)]}
    cards, skipped = common.board_cards(client, project)
    assert list(cards) == ['WF-001'] and cards['WF-001'][0] == 1 and skipped == [2]


def test_board_facts_shape_and_exclusions(catalog):
    names = {spec['key']: name for name, spec in projection(catalog).items()}
    def row(number, state, owner, **extra):
        return content(number, **extra) | {'fieldValues': {
            names['state']: {'name': state}, names['owner']: None if owner is None else {'text': owner}}}
    project = {'items': [row(1, '進行中', 'executor:a'), row(2, '進行中', 'executor:b', archived=True),
                         row(3, '待辦', None), row(4, '進行中', 'executor:'), row(9, '進行中', 'executor:self')]}
    facts = common.board_facts(project, catalog, self_number=9, repo='fake/repo')
    assert facts == [{'state': '進行中', 'owner_actor': 'a'}, {'state': '待辦', 'owner_actor': None},
                     {'state': '進行中', 'owner_actor': None}]


@pytest.mark.parametrize('parent,cards,expected', [
    (None, {}, (0, None)),
    ('B', {'B': (2, {'card_id': 'B', 'parent': None})}, (1, None)),
    ('B', {'B': (2, {'card_id': 'B', 'parent': 'C'}), 'C': (3, {'card_id': 'C', 'parent': 'D'}),
           'D': (4, {'card_id': 'D', 'parent': None})}, (3, None)),
    ('B', {'B': (2, {'card_id': 'B', 'parent': 'A'})}, (1, '循環')),
    ('A', {}, (0, '循環')),
    ('B', {'B': (2, {'card_id': 'B', 'parent': 'Z'})}, (1, 'Z')),
    ('Z', {}, (0, 'Z'))])
def test_chain_depth(parent, cards, expected):
    assert common.chain_depth({'card_id': 'A', 'parent': parent}, cards) == expected


def test_comment_blocks_author_issue_and_errors():
    comment = {'author': 'who', 'issue_url': 'https://api.github.com/repos/fake/repo/issues/20',
               'body': block('wf-ruling', '{"kind": "stop"}') + block('wf-return', '{壞')}
    found = common.comment_blocks(comment)
    assert (found['author'], found['issue']) == ('who', 20)
    assert found['blocks'] == {'wf-return': (False, None), 'wf-ruling': (True, {'kind': 'stop'})}
    assert found['errors'] == ['wf-return JSON 解析失敗']
    bare = common.comment_blocks({'body': block('wf-return', 'null')}, ('wf-return',))
    assert bare == {'author': None, 'issue': None, 'blocks': {'wf-return': (True, None)}, 'errors': []}


def test_missing_fields_reads_the_live_table():
    card = {'core_pain': 0, 'feature': '', 'resources': []}
    missing = common.missing_fields(card, ROOT)
    assert 'core_pain' not in missing and 'feature' in missing and 'resources' in missing


def test_parse_args_and_printer():
    args = common.parse_args('wf x', ['7', '--flag', 'v'], ('n', {'type': int}), ('--flag', {}))
    assert (args.n, args.flag) == (7, 'v')
    with pytest.raises(SystemExit):
        common.parse_args('wf x', ['--nope'], ('n', {'type': int}))
    seen = []
    report = common.Printer(seen.append)
    report('一')
    report('二')
    assert seen == ['一', '二'] and tuple(report) == ('一', '二')


def test_write_public_names_and_aliases():
    assert _prepare is prepare_card and _values is projection_values
    project = {'items': [{'id': 'X', 'fieldValues': {'a': {'text': 't'}, 'b': {'name': 'n'}, 'c': None}}]}
    assert projection_values(project, 'X') == {'a': 't', 'b': 'n', 'c': None}
    assert common.field_values({'fieldValues': None}) == {}


def test_fake_client_has_merge_base_and_repo():
    client = FakeGhClient(merge_base='b' * 40)
    assert client.merge_base('main', 'feat') == 'b' * 40
    assert client.calls == [('merge_base', {'base': 'main', 'head': 'feat'})]
    assert client.repo == 'fake/repo'
