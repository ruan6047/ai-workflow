"""消費 core/dispatch.md `json wf-module-sections`、modules/resource-lock／initiative／identity §0，
以及 verbs/move_modules.py 的交集函式；段名逐字取自宣告，未啟用不印。
"""
from pathlib import Path
import re
import shutil

import pytest

from .test_brief_sections import (SOURCE, card, emitted, issue_row, make_client, make_root,
                                  sections, template)
from wf.compose.blocks import load_blocks
from wf.verbs.brief import MODULE_SECTIONS

MINE = {'role': 'executor', 'actor': 'me'}


def project_item(number, card_id, *, state='進行中', actor='other', archived=False):
    """core/card-schema.md §5 的五個投影欄；raw 形狀同 gh/client.project()。"""
    return {'id': f'ITEM{number}', 'isArchived': archived,
            'content': {'__typename': 'Issue', 'number': number, 'url': '',
                        'repository': {'nameWithOwner': 'fake/repo'}},
            'fieldValues': {'階段': {'text': '執行'}, '狀態': {'name': state},
                            '級別': {'name': 'T3'}, 'owner': {'text': f'executor:{actor}'},
                            '卡ID': {'text': card_id}}}


LISTED = ['identity', 'resource-lock']  # 兩者 scope=project ⇒ 先列入 .wf/modules.json 才談 enable_if


def promote(root, *names):
    """把 tmp root 內指定模組的 maturity 改成 ready。

    core/modules.md §3：`adds.handoff_sections` 與 `wf-module-sections` 都是自動能力七項之一 ⇒
    段要出現，模組必須是 ready。本檔測的是段名與段內容的接線，⛔ 不是成熟度本身；⛔ 不動 repo 內
    的規則，只改這份複本。非 ready 的零貢獻由 test_non_ready_modules_contribute_no_brief_sections 釘。
    """
    for name in names:
        path = root / f'modules/{name}/module.md'
        text = path.read_text(encoding='utf-8')
        assert '"maturity": "ready"' not in text, name
        path.write_text(re.sub(r'"maturity": "[a-z]+"', '"maturity": "ready"', text, count=1),
                        encoding='utf-8')
    return root


def wired(**changes):
    """三個模組同時啟用：板上有別人的進行中卡、卡有 parent、identity 列在專案設定。"""
    data = card(owner=MINE, resources=['file:a'], parent='WF-000',
                parent_spec_version=1, **changes)
    rows = [issue_row(10, data),
            issue_row(11, card(card_id='WF-002', source_issue=11, resources=['file:a', 'file:b'],
                               owner={'role': 'executor', 'actor': 'other'})),
            issue_row(12, card(card_id='WF-000', source_issue=12, spec_version=3))]
    return make_client(rows=rows, items=[project_item(11, 'WF-002')])


def test_enabled_modules_add_sections_named_verbatim(tmp_path):
    """驗收 7：段名逐字＝各模組 adds.handoff_sections，順序依 wf-module-sections.brief。"""
    root = promote(make_root(tmp_path, listed=LISTED), 'resource-lock', 'identity')
    declared, = load_blocks(root).by_label('json wf-module-sections')
    expected = [name for names in declared.data['brief'].values() for name in names]
    assert len(expected) == 4
    _, lines = emitted(wired(), root)
    names = [name for name, _ in sections(lines)]
    assert names[-4:] == expected
    assert '模組層未接線' not in lines
    body = dict(sections(lines))
    for title in expected:
        assert SOURCE.match(body[title][0]) and 'module:modules/' in body[title][0]


def test_module_section_contents(tmp_path):
    """驗收 7：資源宣告逐條、寫入集交集（move_modules 函式）、規格基線兩值並列、身分三格人填。"""
    root = promote(make_root(tmp_path, listed=LISTED), 'resource-lock', 'identity')
    declared, = load_blocks(root).by_label('json wf-module-sections')
    lock, initiative, identity = (declared.data['brief'][name] for name in
                                 ('resource-lock', 'initiative', 'identity'))
    _, lines = emitted(wired(), root)
    body = dict(sections(lines))
    assert body[lock[0]][1:] == ['file:a']
    assert body[lock[1]][1:] == ['file:a ↔ WF-002']
    assert body[initiative[0]][1:] == ['父卡 WF-000 spec_version：3', 'parent_spec_version：1']
    assert body[identity[0]][1:] == ['（人填）']


def test_no_intersection_and_missing_parent_are_reported(tmp_path):
    """負控：資源不相交印無；父卡不在板上印未找到父卡。"""
    root = promote(make_root(tmp_path, listed=LISTED), 'resource-lock', 'identity')
    data = card(owner=MINE, resources=['file:z'], parent='WF-404', parent_spec_version=2)
    rows = [issue_row(10, data),
            issue_row(11, card(card_id='WF-002', source_issue=11, resources=['file:a'],
                               owner={'role': 'executor', 'actor': 'other'}))]
    client = make_client(rows=rows, items=[project_item(11, 'WF-002')])
    _, lines = emitted(client, root)
    declared, = load_blocks(root).by_label('json wf-module-sections')
    body = dict(sections(lines))
    assert body[declared.data['brief']['resource-lock'][1]][1:] == ['無交集']
    assert body[declared.data['brief']['initiative'][0]][1] == '父卡 WF-404 spec_version：未找到父卡'


def test_null_parent_card_block_is_skipped(tmp_path):
    """null 區塊探針：父卡 issue 的 wf-card 值為 null ⇒ 印略過、父卡視為未找到（負控＝wired() 找得到）。"""
    root = make_root(tmp_path, listed=['identity'])
    data = card(owner=MINE, resources=[], parent='WF-000', parent_spec_version=2)
    rows = [issue_row(10, data), issue_row(12, '```json wf-card\nnull\n```\n')]
    _, lines = emitted(make_client(rows=rows), root)
    declared, = load_blocks(root).by_label('json wf-module-sections')
    body = dict(sections(lines))[declared.data['brief']['initiative'][0]]
    assert body[1:] == ['略過無法解析的 issue #12', '父卡 WF-000 spec_version：未找到父卡', 'parent_spec_version：2']
    _, wired_lines = emitted(wired(), root)
    assert '略過無法解析的 issue #12' not in wired_lines


@pytest.mark.parametrize('exclusion', ['archived', 'foreign'])
def test_archived_or_foreign_items_are_not_board_facts(tmp_path, exclusion):
    """整併：brief 的板上事實與 move／notes 同一函式——封存項或別 repo 的進行中卡⛔ 不撐起 resource-lock。"""
    root = promote(make_root(tmp_path, listed=LISTED), 'resource-lock', 'identity')
    other = project_item(11, 'WF-002', archived=exclusion == 'archived')
    if exclusion == 'foreign':
        other['content']['repository']['nameWithOwner'] = 'other/repo'
    rows = [issue_row(10, card(owner=MINE, resources=['file:a'])),
            issue_row(11, card(card_id='WF-002', source_issue=11, resources=['file:a'],
                               owner={'role': 'executor', 'actor': 'other'}))]
    _, lines = emitted(make_client(rows=rows, items=[other]), root)
    declared, = load_blocks(root).by_label('json wf-module-sections')
    assert set(declared.data['brief']['resource-lock']).isdisjoint(name for name, _ in sections(lines))
    _, live = emitted(make_client(rows=rows, items=[project_item(11, 'WF-002')]), root)  # 負控
    assert declared.data['brief']['resource-lock'][1] in dict(sections(live))


def test_non_ready_modules_contribute_no_brief_sections(tmp_path):
    """core/modules.md §3：resource-lock（experimental）與 identity（manual）即使列入 .wf/modules.json
    且 enable_if 成立，也⛔ 不貢獻派工單模組段；同一張卡在 promote 後這些段名就出現（負控在同題）。"""
    quiet = make_root(tmp_path, listed=LISTED, name='quiet')
    declared, = load_blocks(quiet).by_label('json wf-module-sections')
    non_ready = [title for name in ('resource-lock', 'identity')
                 for title in declared.data['brief'][name]]
    _, lines = emitted(wired(), quiet)
    names = [name for name, _ in sections(lines)]
    assert set(non_ready).isdisjoint(names), names
    assert declared.data['brief']['initiative'][0] in names  # ready 的 initiative 仍在
    loud = promote(make_root(tmp_path, listed=LISTED, name='loud'), 'resource-lock', 'identity')
    _, loud_lines = emitted(wired(), loud)
    assert set(non_ready) <= {name for name, _ in sections(loud_lines)}
    print('NON_READY_NO_BRIEF_SECTIONS', non_ready)


def test_disabled_modules_print_nothing(tmp_path):
    """驗收 7：沒有 parent、板上沒有別人的進行中卡、identity 未列 ⇒ 一個模組段都不印。"""
    root = make_root(tmp_path)
    declared, = load_blocks(root).by_label('json wf-module-sections')
    titles = {name for names in declared.data['brief'].values() for name in names}
    _, lines = emitted(make_client(card(owner=MINE)), root)
    names = [name for name, _ in sections(lines)]
    assert titles.isdisjoint(names) and len(names) == 13
    _, wired_lines = emitted(wired(), make_root(tmp_path, name='listed', listed=['identity']))
    assert not titles.isdisjoint(name for name, _ in sections(wired_lines))


def test_every_declared_brief_section_is_wired(tmp_path):
    """驗收 7：宣告的 brief 段名數量＝已接線的實作數；未接線會印模組層未接線。"""
    root = make_root(tmp_path, listed=['identity'])
    declared, = load_blocks(root).by_label('json wf-module-sections')
    pairs = {(name, index) for name, names in declared.data['brief'].items()
             for index in range(len(names))}
    assert pairs == set(MODULE_SECTIONS)


def test_module_note_roles_filter_and_absent_means_all_roles(tmp_path):
    """A4／V7：模組 §0 `adds.notes` 的 {id, roles}——`roles` 缺席的條目在四個角色的組合都出現；
    宣告 `roles` 的條目只在列名角色的組合出現。brief 只有 executor／reviewer 兩個 --for，其餘兩角色以
    `notes(for_role=…)` 取同一組合函式的輸出。"""
    from wf.verbs.notes import notes as notes_verb
    root = make_root(tmp_path, listed=['scoped'])
    shutil.copytree(Path(__file__).resolve().parent / 'fixtures/notes/modules/scoped', root / 'modules/scoped')
    enums, = load_blocks(root).by_label('json wf-enums')
    seen = {}
    for role in enums.data['roles']['enum']:
        if role in ('executor', 'reviewer'):
            _, lines = emitted(make_client(card(owner=MINE)), root, role)
            seen[role] = [item['id'] for item in template(lines)['note_responses']]
        else:
            seen[role] = list(notes_verb(10, client=make_client(card(owner=MINE)), root=root, for_role=role,
                                         emit=lambda line: None).note_ids)
    assert set(seen) == {'requester', 'pm', 'executor', 'reviewer'}
    assert all('F-scoped-01' in ids for ids in seen.values())
    assert [role for role, ids in seen.items() if 'F-scoped-02' in ids] == ['reviewer']
    assert sorted(role for role, ids in seen.items() if 'F-scoped-03' in ids) == ['executor', 'pm']
    assert 'F-scoped-02' not in seen['executor']  # brief --for executor 讀的是 executor 這份 requested role
    print('MODULE_ROLES', {role: [i for i in ids if i.startswith('F-scoped-')] for role, ids in seen.items()})
