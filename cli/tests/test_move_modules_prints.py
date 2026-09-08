"""消費 modules/resource-lock/module.md §0–1、modules/initiative/module.md §0–1、
core/card-schema.md §5、core/verbs.md §1 move［3］／§2 末、stages/closeout.md F-結案-02／03。
S09 驗收 5–7：交集四案、parent_spec_version 三案、未實作 id；所有遠端讀取由 fake 接住。
"""
import json
from pathlib import Path

import pytest

from .fakes import FakeGhClient
from wf.compose.blocks import Catalog, load_blocks, projection, read_blocks
from wf.compose.project_config import load_project_config
from wf.gh.client import NotFound
from wf.verbs.move_modules import apply_counters, module_prints

RULES = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / 'fixtures'
REPO = 'fake/repo'
DISPATCH = ('執行/待辦', '執行/進行中')


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(RULES)


@pytest.fixture(scope='module')
def names(catalog):
    """投影欄名逐字取自 core/card-schema.md §5，⛔ 不在測試裡抄欄名。"""
    return {spec['key']: name for name, spec in projection(catalog).items()}


class Client(FakeGhClient):
    repo = REPO

    def __init__(self, bodies):
        self.bodies = bodies
        super().__init__(issue=lambda number: {'number': number, 'body': bodies[number]})


def block(card):
    return '```json wf-card\n' + json.dumps(card, ensure_ascii=False) + '\n```\n'


def card(**changes):
    return {'card_id': 'WF-001', 'owner': {'role': 'executor', 'actor': 'me'},
            'resources': [], 'parent': None, 'parent_spec_version': None} | changes


def item(names, number, card_id, state='進行中', owner='executor:other', **extra):
    return {'id': f'ITEM{number}', 'isArchived': False,
            'content': {'__typename': 'Issue', 'number': number,
                        'repository': {'nameWithOwner': REPO}},
            'fieldValues': {names['state']: {'name': state}, names['owner']: {'text': owner},
                            names['card_id']: {'text': card_id}}} | extra


def board(items):
    return {'id': 'PROJECT', 'title': 'T', 'url': 'u', 'fields': [], 'items': list(items)}


def prints(catalog, *, enabled, card_json, project=None, client=None, edge=DISPATCH, root=None):
    return module_prints(card_json, *edge, catalog=catalog, config=load_project_config(root or RULES),
                         enabled_names=enabled, project=project, client=client)


def test_no_live_card_means_module_disabled_and_silent(catalog, names):
    """現役卡母體為空時模組不啟用（§0 enable_if other_actor_card_in_state, min 1）。"""
    quiet = prints(catalog, enabled=[], card_json=card(resources=['file:a.py']),
                   project=board([item(names, 20, 'WF-002', state='待辦')]),
                   client=Client({20: block(card(card_id='WF-002', resources=['file:a.py']))}))
    assert not [line for line in quiet if '↔' in line or line == '無交集']


def test_live_card_without_overlap_prints_no_intersection(catalog, names):
    lines = prints(catalog, enabled=['resource-lock'], card_json=card(resources=['file:a.py']),
                   project=board([item(names, 20, 'WF-002')]),
                   client=Client({20: block(card(card_id='WF-002', resources=['file:b.py']))}))
    assert lines == ['無交集']


def test_overlap_prints_one_line_per_resource_and_card(catalog, names):
    lines = prints(catalog, enabled=['resource-lock'],
                   card_json=card(resources=['file:a.py', 'port:8080', 'file:c.py']),
                   project=board([item(names, 20, 'WF-002'), item(names, 21, 'WF-003')]),
                   client=Client({20: block(card(card_id='WF-002', resources=['port:8080', 'file:a.py'])),
                                  21: block(card(card_id='WF-003', resources=['file:c.py']))}))
    assert lines == ['file:a.py ↔ WF-002', 'port:8080 ↔ WF-002', 'file:c.py ↔ WF-003']


def test_db_schema_does_not_dominate_db_table(catalog, names):
    """§1 第 2 條：完全字串比對，db:<env>:schema ⛔ 不支配 db:<env>:table:<name>。"""
    lines = prints(catalog, enabled=['resource-lock'], card_json=card(resources=['db:dev:schema']),
                   project=board([item(names, 20, 'WF-002')]),
                   client=Client({20: block(card(card_id='WF-002', resources=['db:dev:table:x']))}))
    assert lines == ['無交集']


def test_exact_same_db_resource_still_intersects(catalog, names):
    """負控：同一字串照樣命中，證明上一測的「無交集」不是比對永遠不成立。"""
    lines = prints(catalog, enabled=['resource-lock'], card_json=card(resources=['db:dev:schema']),
                   project=board([item(names, 20, 'WF-002')]),
                   client=Client({20: block(card(card_id='WF-002', resources=['db:dev:schema']))}))
    assert lines == ['db:dev:schema ↔ WF-002']


def test_same_actor_and_archived_items_are_not_live(catalog, names):
    lines = prints(catalog, enabled=['resource-lock'], card_json=card(resources=['file:a.py']),
                   project=board([item(names, 20, 'WF-002', owner='pm:me'),
                                  item(names, 21, 'WF-003', isArchived=True),
                                  item(names, 22, 'WF-004', state='待確認')]),
                   client=Client({20: block(card(card_id='WF-002', resources=['file:a.py'])),
                                  21: block(card(card_id='WF-003', resources=['file:a.py'])),
                                  22: block(card(card_id='WF-004', resources=['file:a.py']))}))
    assert lines == ['無交集']


def test_unreadable_live_card_is_named_and_skipped(catalog, names):
    class Missing(Client):
        def issue(self, number):
            if number == 21:
                raise NotFound('404')
            return super().issue(number)

    lines = prints(catalog, enabled=['resource-lock'], card_json=card(resources=['file:a.py']),
                   project=board([item(names, 20, 'WF-002'), item(names, 21, 'WF-003')]),
                   client=Missing({20: block(card(card_id='WF-002', resources=['file:a.py'])), 21: ''}))
    assert lines == ['file:a.py ↔ WF-002', '無法讀取 WF-003 的 resources']


def test_unparsable_live_card_body_is_named_and_skipped(catalog, names):
    lines = prints(catalog, enabled=['resource-lock'], card_json=card(resources=['file:a.py']),
                   project=board([item(names, 20, 'WF-002')]),
                   client=Client({20: '```json wf-card\n{壞掉\n```\n'}))
    assert lines == ['無法讀取 WF-002 的 resources']


def test_non_dispatch_edge_prints_nothing(catalog, names):
    lines = prints(catalog, enabled=['resource-lock'], card_json=card(resources=['file:a.py']),
                   edge=('執行/進行中', '執行/待確認'),
                   project=board([item(names, 20, 'WF-002')]),
                   client=Client({20: block(card(card_id='WF-002', resources=['file:a.py']))}))
    assert lines == []


def test_missing_project_setting_is_reported_not_silent(catalog):
    """F-執行者-06：無 Project 設定時未評估，⛔ 不寫成沒有交集。"""
    lines = prints(catalog, enabled=[], card_json=card(resources=['file:a.py']), project=None)
    assert '無 Project 設定，未評估 resource-lock' in lines


def test_parent_spec_version_empty_prints_when_initiative_enabled(catalog):
    lines = prints(catalog, enabled=['initiative'], card_json=card(parent='WF-000'))
    assert 'parent_spec_version 空值' in lines


def test_registered_parent_spec_version_is_silent(catalog):
    lines = prints(catalog, enabled=['initiative'],
                   card_json=card(parent='WF-000', parent_spec_version=1))
    assert not any('parent_spec_version' in line for line in lines)


def test_no_parent_means_initiative_disabled_and_silent(catalog):
    lines = prints(catalog, enabled=[], card_json=card())
    assert not any('parent_spec_version' in line for line in lines)


@pytest.fixture(scope='module')
def fixture_catalog():
    return Catalog(read_blocks(FIXTURES, 'modules/nope/module.md'), {})


def test_declared_but_unregistered_ids_print_unimplemented(fixture_catalog):
    lines = module_prints(card(), *DISPATCH, catalog=fixture_catalog,
                          config=load_project_config(RULES), enabled_names=['nope'],
                          project=None, client=None)
    assert lines == ['未實作的模組印項／計數 nope_count', '未實作的模組印項／計數 nope']


def test_unregistered_counter_is_not_written_to_card(fixture_catalog):
    moved = apply_counters(card(), *DISPATCH, catalog=fixture_catalog,
                           config=load_project_config(RULES), enabled_names=['nope'])
    assert 'nope_count' not in moved


def test_module_without_counters_or_prints_keys_is_tolerated(catalog):
    """pitfalls-13 的 yaml 沒有 counters／move_prints 鍵＝空清單。"""
    declaration, = [b.data for b in catalog.by_label('yaml wf-module')
                    if b.data['name'] == 'pitfalls-13']
    assert 'counters' not in declaration['adds'] and 'move_prints' not in declaration['adds']
    assert prints(catalog, enabled=['pitfalls-13'], card_json=card(), project=board([])) == []
    assert 'escalation_count' not in apply_counters(
        card(), *DISPATCH, catalog=catalog, config=load_project_config(RULES),
        enabled_names=['pitfalls-13'])
