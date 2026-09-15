"""消費 core/verbs.md §1 notes／§2／§3、core/naming.md §3／§4、
core/card-schema.md §1／§4、core/handoff.md 來源標記、core/enums.md stages／roles、
roles/conduct-common.md §1／§2、modules/pitfalls-13/module.md §1。所有遠端操作由手構替身接住。
"""
import ast
import dataclasses
import importlib.util
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess

import pytest

from .fakes import FakeGhClient
from wf.compose.blocks import load_blocks
from wf.verbs import _write
from wf.verbs._write import NotesResult, WriteResult
from wf.verbs.notes import ITEM, Note, notes, run
from wf.verbs.open import OpenResult


RULES = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / 'fixtures/notes'
WRITES = ('update_card_body', 'post_comment',
          'write_project_field', 'add_to_project', 'remove_from_project', 'close_issue')
ID_SHAPE = re.compile(r'^[FPT]-[^：]+-[0-9]{2}$')  # core/naming.md §4 的 id 形狀（複驗用，⛔ 不是 ITEM 的複製品）
ROLE_PREFIX = {'executor': 'F-執行者-', 'pm': 'F-PM-', 'reviewer': 'F-查核者-', 'requester': 'F-需求方-'}


def block(label, value):
    body = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return f'```json {label}\n{body}\n```\n'


def card(**changes):
    """完整的 `wf-card`：notes 依 verbs.md §2 D3 先驗整張卡面，殘卡會被整卡拒。"""
    return dict(schema_version=2, card_id='WF-001', source_issue=10, feature='', core_pain='',
                non_scope=[], stage_plan=[], stage='執行', state='進行中', list_convergence=[],
                service_goal='', tier=None, tier_basis=None, exec_capability=None,
                review_capability=None, db_scope=None, resources=[], when='', spec_version=1,
                iteration=0, acceptance=[], verification=[], parent=None, blocked=None,
                grilling=None, owner={'role': 'executor', 'actor': '某執行者'}, branch=None,
                source_sha=None, notes=[]) | changes


def make_root(tmp_path, *, stages=(), roles=(), modules=(), real=False,
              listed=(), project_stage=None, project=True):
    root = tmp_path / ('real' if real else 'synth')
    root.mkdir(parents=True)
    (root / 'core').symlink_to(RULES / 'core', target_is_directory=True)
    for name in ('stages', 'roles', 'modules'):
        if real:
            (root / name).symlink_to(RULES / name, target_is_directory=True)
        else:
            (root / name).mkdir()
    for name, chosen in (('stages', stages), ('roles', roles)):
        for item in chosen:
            shutil.copy(FIXTURES / name / item, root / name / item)
    for item in modules:
        shutil.copytree(FIXTURES / 'modules' / item, root / 'modules' / item)
    (root / '.wf').mkdir()
    (root / '.wf/modules.json').write_text(json.dumps(
        {'areas': ['WF'], 'modules': [{'name': name} for name in listed],
         'project': {'owner': 'fake', 'number': 1} if project else None}), encoding='utf-8')
    if project_stage is not None:
        (root / '.wf/stages').mkdir()
        shutil.copy(FIXTURES / 'project/implementation.md',
                    root / f'.wf/stages/{project_stage}.md')
    return root


def make_client(card_json, comments=(), items=()):
    body = card_json if isinstance(card_json, str) else '前言\n' + block('wf-card', card_json)
    row = {'number': 10, 'node_id': 'I10', 'state': 'open', 'body': body}
    return FakeGhClient(issue=row, issues=[row], comments=list(comments),
                        project={'id': 'PROJECT', 'fields': [], 'items': list(items)})


def emitted(client, root, **kwargs):
    lines = []
    result = notes(10, client=client, root=root, emit=lines.append, **kwargs)
    assert result.printed == tuple(lines)
    return result, lines


def numbered(lines):
    """回傳編號清單的 (序號, id) 序對；只認 '<n>. <id>：' 的行。"""
    hits = [re.match(r'^([0-9]+)\. ([^：]+)：', line) for line in lines]
    return [(int(hit[1]), hit[2]) for hit in hits if hit]


def roles_enum(root):
    """執行期讀合成樹 core/enums.md 的 roles 值域，⛔ 不重打常數。"""
    enums, = load_blocks(root).by_label('json wf-enums')
    return enums.data['roles']['enum']


ALL_ROLES = ['conduct-common.md', 'executor.md', 'pm.md', 'requester.md', 'reviewer.md']


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('禁止真實網路或子程序')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(subprocess, 'run', forbidden)


def test_six_segments_in_order_with_continuous_numbering(tmp_path):
    """A1：六段各至少 1 條 → ① 階段 F-執行-、② conduct-common F-共用-、③ 角色 F-執行者-、
    ④ 模組 F-demo-、⑤ 專案 P-、⑥ 卡面 T-，編號 1..n 連續、區間互不交錯。"""
    root = make_root(tmp_path, stages=['implementation.md'], roles=['conduct-common.md', 'executor.md'],
                     modules=['demo'], listed=['demo'], project_stage='執行')
    client = make_client(card(notes=[{'id': 'T-執行-01', 'text': '卡面條目',
                                      'origin': 'https://example.invalid/1'}]))
    result, lines = emitted(client, root)
    assert result.rc == 0
    assert numbered(lines) == [(1, 'F-執行-01'), (2, 'F-共用-01'), (3, 'F-共用-02'), (4, 'F-執行者-01'),
                               (5, 'F-demo-01'), (6, 'P-執行-01'), (7, 'T-執行-01')]
    assert list(result.note_ids) == [identifier for _, identifier in numbered(lines)]
    assert [name for name, _ in client.calls if name in WRITES] == []


def test_conduct_common_sits_between_stage_and_role_for_every_role(tmp_path):
    """A3／V2：四個角色（值域讀 core/enums.md）各自的組合都是 階段 → F-共用-* → 該角色，
    conduct-common ⛔ 不套角色過濾；相對沒有 conduct-common 的合成樹，每個組合恆 +N（N＝fixture 條數）。"""
    with_common = make_root(tmp_path / 'a', stages=['implementation.md'], roles=ALL_ROLES)
    without = make_root(tmp_path / 'b', stages=['implementation.md'],
                        roles=[name for name in ALL_ROLES if name != 'conduct-common.md'])
    common = ['F-共用-01', 'F-共用-02']
    deltas = set()
    for role in roles_enum(with_common):
        owner = {'role': role, 'actor': 'x'}
        _, lines = emitted(make_client(card(owner=owner)), with_common)
        ids = [identifier for _, identifier in numbered(lines)]
        assert ids == ['F-執行-01', *common, f'{ROLE_PREFIX[role]}01'], role
        _, baseline = emitted(make_client(card(owner=owner)), without)
        deltas.add(len(ids) - len(numbered(baseline)))
    assert deltas == {len(common)}
    _, everyone = emitted(make_client(card(owner=None)), with_common)  # owner null＝角色檔全印
    ids = [identifier for _, identifier in numbered(everyone)]
    assert ids[:3] == ['F-執行-01', *common] and ids.count('F-共用-01') == 1
    print('CONDUCT_COMMON 四角色 delta 集合', sorted(deltas))


def test_core_order_stages_then_roles_by_filename(tmp_path):
    """PM 預設：階段檔 → roles/ 依檔名字典序，檔內出現序。"""
    root = make_root(tmp_path, stages=['implementation.md', 'requirement.md'],
                     roles=['aaa-role.md', 'executor.md'])
    _, lines = emitted(make_client(card(owner=None)), root)  # owner null＝角色檔全印並註明（§3）
    assert numbered(lines) == [(1, 'F-執行-01'), (2, 'F-AAA-01'), (3, 'F-執行者-01')]
    assert '卡面 owner 未填，角色注意事項全印' in lines


def test_only_id_shaped_bullets_inside_the_section_are_read(tmp_path):
    """驗收 2：散文、無 id 條列、別階段、非兩位數 NN、§6 以外的行都不讀。
    A8 隔離負控：條文內文含 `-NN：` 時 id 仍止於第一個全形冒號（基線正則會捕成
    `F-共用-01：見 core/params.md P-x-99`）；既有六個負控行為不變。"""
    root = make_root(tmp_path, stages=['implementation.md'], roles=['conduct-common.md'])
    _, lines = emitted(make_client(card()), root)
    assert numbered(lines) == [(1, 'F-執行-01'), (2, 'F-共用-01'), (3, 'F-共用-02')]
    assert lines[1].startswith('2. F-共用-01：見 core/params.md P-x-99：該欄。 [來源: ')
    body = (FIXTURES / 'stages/implementation.md').read_text(encoding='utf-8')
    population = [line for line in body.splitlines()
                  if line.strip() and not line.startswith(('#', '-' * 3, 'name', 'when',
                                                           'non_scope', 'last_confirmed'))]
    rejected = [line for line in body.splitlines() if '⛔ 不該被讀' in line]
    assert len(rejected) == 5
    assert not any(any(text in line for line in lines) for text in rejected)
    isolated = ITEM.match('- F-共用-01：見 core/params.md P-x-99：該欄。')
    assert (isolated[1], isolated[2]) == ('F-共用-01', '見 core/params.md P-x-99：該欄。')
    for line in ('- F-執行-001：三位數。', '- F-執行-2：一位數。', '- F-執行-01:半形冒號。',
                 '- 執行-01：無前綴。', '- X-執行-01：X 前綴。', '  - F-執行-01：縮排。'):
        assert ITEM.match(line) is None, line
    for line in ('- P-執行-01：專案。', '- T-執行-01：卡面。', '- F-pitfalls-13-01：模組名含數字。'):
        assert ITEM.match(line) is not None, line
    print('母體：檔內非標題非 frontmatter 行', len(population), '行，明示不可讀',
          len(rejected), '行，輸出取 1 行；隔離負控 1 行、既有負控 6 行、正控 3 行')


def corpus_ids(root):
    """真規則語料：stages §6、roles §4、conduct-common §1／§2、modules §2 的全部 id（production 抽取）。"""
    from wf.context import rules_of
    from wf.verbs.notes import _file_notes
    rules = rules_of(root)
    found = []
    for relative in rules.iter_assets('stages/*.md'):
        found += _file_notes(rules, relative, '6', 'core')
    for relative in rules.iter_assets('roles/*.md'):
        found += _file_notes(rules, relative, '4', 'core')
    for heading in ('1', '2'):
        found += _file_notes(rules, 'roles/conduct-common.md', heading, 'core')
    for relative in rules.iter_assets('modules/*/module.md'):
        found += _file_notes(rules, relative, '2', 'module')
    return [note.id for note in found]


def test_every_corpus_id_is_still_read_under_the_narrow_item(tmp_path):
    """A8 正控（V3）：現行全部語料 id（含 conduct-common 的 F-共用-01…23）逐一仍被收，
    形狀複驗 0 例外、重複 0；conduct-common 的 id 恰為連號 01…23。"""
    root = make_root(tmp_path, real=True)
    ids = corpus_ids(root)
    assert ids and [identifier for identifier in ids if not ID_SHAPE.match(identifier)] == []
    assert len(ids) == len(set(ids))
    common = [identifier for identifier in ids if identifier.startswith('F-共用-')]
    assert common == [f'F-共用-{index:02d}' for index in range(1, 24)]
    assert not any('：' in identifier for identifier in ids)
    print('CORPUS_IDS', len(ids), '個，F-共用', len(common), '個，形狀例外 0')


def test_stage_prefix_separates_executor_role_from_execution_stage(tmp_path):
    """驗收 2：--stage 執行 取 F-執行-，尾端 - 把 F-執行者- 擋在階段來源外。"""
    root = make_root(tmp_path, stages=['implementation.md'], roles=['executor.md'])
    _, lines = emitted(make_client(card(stage='需求')), root, stage='執行')
    assert numbered(lines) == [(1, 'F-執行-01'), (2, 'F-執行者-01')]
    assert not any('F-執行者-91' in line for line in lines)


def test_source_marks_carry_origin_and_frontmatter(tmp_path):
    """A6：來源標記 `<kind>:<path>`——core／module 的 path 相對 rules root、project 相對
    project root、card＝完整 canonical Issue URL；T-／P- 無 frontmatter 省略後兩段。"""
    root = make_root(tmp_path, stages=['implementation.md'], modules=['demo'],
                     listed=['demo'], project_stage='執行')
    client = make_client(card(notes=[{'id': 'T-執行-01', 'text': '卡面條目',
                                      'origin': 'https://example.invalid/1'}]))
    _, lines = emitted(client, root)
    assert lines[0] == ('1. F-執行-01：核心階段條目。 [來源: core:stages/implementation.md'
                        '#6 · 注意事項 · implementation-fixture：合成順序與條列文法的樣本'
                        ' · confirmed 2026-09-08]')
    assert lines[1].endswith('[來源: module:modules/demo/module.md#2 · 注意事項'
                             ' · demo：合成順序樣本的假模組 · confirmed 2026-09-08]')
    assert lines[2].endswith('[來源: project:.wf/stages/執行.md]')
    assert lines[3].endswith('[來源: card:https://github.com/fake/repo/issues/10#notes]')
    for shape in ('core/core', 'core/stages', 'module/modules', 'project/.wf', 'card/issues'):
        assert not any(shape in line for line in lines), shape


def test_card_notes_keep_their_order(tmp_path):
    """驗收 5：卡面 notes 欄兩條照序印，來源標記＝card 的完整 Issue URL。"""
    root = make_root(tmp_path)
    entries = [{'id': 'T-執行-01', 'text': '先', 'origin': 'https://example.invalid/1'},
               {'id': 'T-執行-02', 'text': '後', 'origin': 'https://example.invalid/2'}]
    _, lines = emitted(make_client(card(notes=entries)), root)
    assert numbered(lines) == [(1, 'T-執行-01'), (2, 'T-執行-02')]
    assert all(line.endswith('[來源: card:https://github.com/fake/repo/issues/10#notes]') for line in lines)


def test_project_stage_file_missing_prints_nothing(tmp_path):
    """驗收 4：`.wf/stages/<階段>.md` 缺＝零條、⛔ 不印缺。"""
    present = make_root(tmp_path / 'a', project_stage='執行')
    absent = make_root(tmp_path / 'b')
    _, with_file = emitted(make_client(card()), present)
    _, without = emitted(make_client(card()), absent)
    assert numbered(with_file) == [(1, 'P-執行-01')]
    assert without == []


def test_enabled_module_notes_and_declaration_mismatch(tmp_path):
    """驗收 3／A4：真 escalation（宣告已是 {id} 物件）印四條；ghost 宣告的 F-ghost-02 未在 §2 印一行、rc=0。"""
    real = make_root(tmp_path / 'a', real=True, listed=['escalation'])
    result, lines = emitted(make_client(card()), real)
    assert result.rc == 0
    assert [i for _, i in numbered(lines) if i.startswith('F-escalation-')] == [
        'F-escalation-01', 'F-escalation-02', 'F-escalation-03', 'F-escalation-04']
    off = make_root(tmp_path / 'b', real=True, listed=[])
    _, quiet = emitted(make_client(card()), off)
    assert [i for _, i in numbered(quiet) if i.startswith('F-escalation-')] == []
    ghost = make_root(tmp_path / 'c', modules=['ghost'], listed=['ghost'])
    result, mismatch = emitted(make_client(card()), ghost)
    assert result.rc == 0
    assert '模組 ghost 宣告 F-ghost-02 未在 §2' in mismatch
    assert numbered(mismatch) == [(1, 'F-ghost-01')]


def load_reachability():
    spec = importlib.util.spec_from_file_location('reachability', RULES / '.github/scripts/reachability.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_module_declaration_id_roles_object_is_consumed(tmp_path):
    """A4／V7：兩個 consumer 對 {id, roles} 都不拋例外——notes.py 依 roles 過濾（缺席＝全角色），
    reachability.notes_errors 對帳仍相等（0 錯）；真 repo 的 11 個模組宣告同樣 0 錯。"""
    root = make_root(tmp_path, modules=['scoped'], listed=['scoped'])
    seen = {}
    for role in roles_enum(root):
        result, lines = emitted(make_client(card(owner={'role': role, 'actor': 'x'})), root)
        assert result.rc == 0
        seen[role] = [i for _, i in numbered(lines)]
    assert all('F-scoped-01' in ids for ids in seen.values())
    assert [role for role, ids in seen.items() if 'F-scoped-02' in ids] == ['reviewer']
    assert sorted(role for role, ids in seen.items() if 'F-scoped-03' in ids) == ['executor', 'pm']
    reachability = load_reachability()
    body = (FIXTURES / 'modules/scoped/module.md').read_text(encoding='utf-8')
    declared, = load_blocks(root).by_label('yaml wf-module')
    assert reachability.notes_errors('scoped', declared.data['adds']['notes'], body) == []
    for path in sorted((RULES / 'modules').glob('*/module.md')):
        text = path.read_text(encoding='utf-8')
        data = json.loads(reachability.MODBLOCK.search(text).group(1))
        assert reachability.notes_errors(data['name'], data['adds']['notes'], text) == [], path
        assert all(isinstance(item, dict) for item in data['adds']['notes']), path
    print('MODULE_ROLES', {role: len(ids) for role, ids in seen.items()})


SOURCE_MARK = re.compile(r'\[來源: ([a-z]+):([^ #\]]+)(?:#[^ \]]*)?(?: · [^\]]*)?\]')


def test_every_file_source_path_opens_from_its_declared_root(tmp_path, monkeypatch):
    """A6／V4：掃描面＝notes／brief --for executor／reviewer／closeout／review 在 fixture 上實際輸出的
    全部來源標記；kind≠card 者以宣告 root 逐一開啟成功率 100%，card 者＝完整 canonical Issue URL；
    ⛔ 不再出現 core/core、module/modules、project/.wf、card/issues 串接形狀。本機 git 子指令以替身取代。"""
    from .test_brief_modules import project_item
    from .test_brief_sections import block as brief_block, card as brief_card, issue_row, make_client as brief_client
    from .test_brief_sections import make_root as brief_root
    from wf.verbs.brief import brief
    from wf.verbs.review import review
    monkeypatch.setattr('wf.verbs.brief.merge_tree', lambda *a, **k: 0)
    monkeypatch.setattr('wf.verbs.closeout.merge_tree', lambda *a, **k: 0)
    monkeypatch.setattr('wf.verbs.review.rev_parse', lambda *a, **k: None)
    root = brief_root(tmp_path, listed=['identity', 'pitfalls-13'], contracts=['contract-ok.md'])
    shutil.copytree(FIXTURES / 'modules/scoped', root / 'modules/scoped')
    (root / '.wf/stages').mkdir()
    (root / '.wf/stages/執行.md').write_text('- P-執行-01：專案層條目。\n', encoding='utf-8')
    data = brief_card(owner={'role': 'executor', 'actor': 'me'}, resources=['file:a'], parent='WF-000',
                      parent_spec_version=1, branch='wf/WF-001', source_sha='b' * 40,
                      notes=[{'id': 'T-執行-01', 'text': '卡面', 'origin': 'https://example.invalid/2'}])
    rows = [issue_row(10, data),
            issue_row(11, brief_card(card_id='WF-002', source_issue=11, resources=['file:a'],
                                     owner={'role': 'executor', 'actor': 'other'})),
            issue_row(12, brief_card(card_id='WF-000', source_issue=12, spec_version=3))]
    comments = [{'id': 1, 'url': 'https://example.invalid/c1', 'author': 'a', 'created_at': '2026-09-01T00:00:00Z',
                 'body': brief_block('wf-note', {'id': 'T-執行-09', 'text': '候選', 'origin': 'https://example.invalid/9'})}]

    def client():
        return brief_client(rows=rows, items=[project_item(11, 'WF-002')], comments=comments,
                            pulls_for_branch=[])
    outputs = {'notes': []}
    notes(10, client=client(), root=root, emit=outputs['notes'].append)
    for target in ('executor', 'reviewer', 'closeout'):
        outputs[f'brief --for {target}'] = []
        assert brief(10, target=target, client=client(), root=root, emit=outputs[f'brief --for {target}'].append).rc == 0
    path = tmp_path / 'return.json'
    path.write_text('{}', encoding='utf-8')
    outputs['review --role executor'] = []
    assert review(10, file=path, role='executor', client=client(), root=root,
                  emit=outputs['review --role executor'].append).rc == 0
    marks, kinds = [], set()
    for verb, lines in outputs.items():
        for line in lines:
            for kind, where in SOURCE_MARK.findall(line):
                marks.append((verb, kind, where))
                kinds.add(kind)
    assert kinds == {'core', 'module', 'project', 'card'}
    unopenable = [(verb, kind, where) for verb, kind, where in marks
                  if kind != 'card' and not (root / where).is_file()]
    assert unopenable == []
    assert all(where == 'https://github.com/fake/repo/issues/10' for _, kind, where in marks if kind == 'card')
    for shape in ('core/core', 'module/modules', 'project/.wf', 'card/issues'):
        assert not any(shape in line for lines in outputs.values() for line in lines), shape
    print('SOURCE_MARKS', len(marks), '個；kind 分布',
          {kind: sum(1 for _, k, _ in marks if k == kind) for kind in sorted(kinds)},
          '；逐動詞', {verb: sum(1 for v, _, _ in marks if v == verb) for verb in outputs})


def test_compose_alone_performs_no_remote_write(tmp_path, monkeypatch):
    """A9／V9：直接跑組合函式（不經動詞 orchestration）⇒ 替身零呼叫、零遠端寫入、⛔ 不進對帳；
    正控：同一計數器對動詞 `notes` 會響（動詞層明確呼叫 reconcile_projection），且對直接寫入會響。"""
    from wf.compose.project_config import load_project_config
    from wf.context import rules_of
    from wf.verbs import notes as module
    from wf.verbs._common import module_activation
    from wf.verbs.notes import compose_notes
    root = make_root(tmp_path, stages=['implementation.md'], roles=['conduct-common.md', 'executor.md'],
                     modules=['demo'], listed=['demo'], project_stage='執行')
    data = card(notes=[{'id': 'T-執行-01', 'text': '卡面條目', 'origin': 'https://example.invalid/1'}])
    reconciled = []
    original = module.reconcile_projection
    monkeypatch.setattr(module, 'reconcile_projection',
                        lambda *a, **k: reconciled.append('reconcile_projection') or original(*a, **k))
    client = make_client(data)
    catalog = load_blocks(root)
    enabled = module_activation(catalog, load_project_config(root), data,
                                client=None, project=None, number=10).enabled
    printed = []
    items = compose_notes(rules_of(root), root, stage='執行', role='executor', enabled=enabled, card=data,
                          number=10, repo=client.repo, report=printed.append)
    assert [note.id for note in items] == ['F-執行-01', 'F-共用-01', 'F-共用-02', 'F-執行者-01',
                                           'F-demo-01', 'P-執行-01', 'T-執行-01']
    assert client.calls == [] and reconciled == [] and printed == []
    result, _ = emitted(client, root)  # 正控：動詞層才呼叫對帳
    assert result.rc == 0 and reconciled == ['reconcile_projection']
    assert [name for name, _ in client.calls if name in WRITES] == []  # 無投影不等 ⇒ 仍零寫入
    client.update_card_body(10, data)  # 計數器對直接寫入會響
    assert [name for name, _ in client.calls if name in WRITES] == ['update_card_body']
    print('COMPOSE_PURE 組合函式呼叫替身 0 次；動詞層 reconcile_projection 1 次')


def test_pitfalls_template_two_layers(tmp_path):
    """驗收 7：執行 13 行、需求 8 行、未啟用 0 行；族名逐字比對 module §1。"""
    text = (RULES / 'modules/pitfalls-13/module.md').read_text(encoding='utf-8')
    bullets = [line for line in text.splitlines() if line.startswith('- ')]
    everywhere = re.findall(r'`([^`]+)`', bullets[1])
    execution = re.findall(r'`([^`]+)`', bullets[2])
    assert (len(everywhere), len(execution)) == (8, 5)
    root = make_root(tmp_path / 'a', real=True, listed=['pitfalls-13'])
    _, execution_lines = emitted(make_client(card()), root, stage='執行')
    template = [line for line in execution_lines if line.startswith('13 族踩坑清冊 ')]
    assert template == [f'13 族踩坑清冊 {name}：已檢查／不適用／發現'
                        for name in everywhere + execution]
    _, requirement = emitted(make_client(card()), root, stage='需求')
    assert len([line for line in requirement if line.startswith('13 族踩坑清冊 ')]) == 8
    off = make_root(tmp_path / 'b', real=True, listed=[])
    _, quiet = emitted(make_client(card()), off)
    assert [line for line in quiet if line.startswith('13 族踩坑清冊 ')] == []


def test_run_parses_stage_flag(tmp_path):
    root = make_root(tmp_path, stages=['implementation.md'])
    assert run(['10', '--stage', '執行'], client=make_client(card(stage='需求')),
               root=root, catalog=load_blocks(root)) == 0


def candidate_comment(identifier='T-執行-09'):
    """一則合法的 wf-note 候選留言；候選 id ⛔ 不得進正式通道。"""
    return [{'id': 1, 'url': 'https://example.invalid/c1', 'author': 'a',
             'created_at': '2026-09-01T00:00:00Z',
             'body': block('wf-note', {'id': identifier, 'text': '候選條目',
                                       'origin': 'https://example.invalid/9'})}]


def test_success_result_carries_the_ordered_formal_ids(tmp_path):
    """CLI-002：rc==0 回 `_write.NotesResult`；note_ids 逐項、逐序等於編號行的 id。
    來源各 1 條的母體同 test_six_segments_in_order_with_continuous_numbering（無 conduct-common fixture）。"""
    root = make_root(tmp_path, stages=['implementation.md'], roles=['executor.md'],
                     modules=['demo'], listed=['demo'], project_stage='執行')
    client = make_client(card(notes=[{'id': 'T-執行-01', 'text': '卡面條目',
                                      'origin': 'https://example.invalid/1'}]),
                         comments=candidate_comment())
    result, lines = emitted(client, root)
    assert result.rc == 0 and isinstance(result, NotesResult)
    assert list(result.note_ids) == [identifier for _, identifier in numbered(lines)]
    assert [index for index, _ in numbered(lines)] == list(range(1, len(result.note_ids) + 1))
    assert result.note_ids == ('F-執行-01', 'F-執行者-01', 'F-demo-01', 'P-執行-01', 'T-執行-01')
    assert 'T-執行-09' not in result.note_ids  # 候選⛔ 不進正式通道
    assert [name for name, _ in client.calls if name in WRITES] == []


def holds_note(value):
    """遞迴查值裡有沒有 `notes.Note` 實例；容器只走 list／tuple／set／dict。"""
    if isinstance(value, Note):
        return True
    if isinstance(value, (list, tuple, set)):
        return any(holds_note(item) for item in value)
    if isinstance(value, dict):
        return any(holds_note(item) for item in value.values())
    return False


def module_imports(text):
    """模組級 import 的完整模組名集合（相對 import ⛔ 不計）。"""
    found = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level:
            found.add(node.module)
    return found


def test_note_source_shape_is_neither_exposed_nor_frozen(tmp_path):
    """CLI-002：公開的只有 str 的 id。Note 型別、text、mark、欄位序維持本模組私有——
    結果沒有任何欄位承載 Note，`_write.py` 也 ⛔ 不 import `wf.verbs.notes`。"""
    names = [field.name for field in dataclasses.fields(NotesResult)]
    assert names == ['rc', 'card', 'reason', 'rejection', 'printed', 'note_ids']
    root = make_root(tmp_path, stages=['implementation.md'], roles=['executor.md'])
    result, _ = emitted(make_client(card()), root)
    assert result.note_ids and all(type(item) is str for item in result.note_ids)
    assert not any(holds_note(getattr(result, name)) for name in names)
    assert holds_note((Note('T-執行-01', 'x', 'y'),))  # 負控：這個查法真的抓得到 Note
    imported = module_imports(Path(_write.__file__).read_text(encoding='utf-8'))
    assert 'wf.verbs.notes' not in imported, sorted(imported)
    assert 'wf.verbs.notes' in module_imports('from wf.verbs.notes import Note\n')  # 負控
    print('NOTES_PRIVACY _write.py 模組級 import：', sorted(imported))


def test_shared_positional_fields_are_unchanged():
    """CLI-002：共用五欄的欄位序不動，新欄只長在 NotesResult；`open.OpenResult` 的第六個
    位置參數仍是 unverified（WF-003 的位置實參因此 ⛔ 不被錯綁）。"""
    base = ['rc', 'card', 'reason', 'rejection', 'printed']
    assert [field.name for field in dataclasses.fields(WriteResult)] == base
    assert [field.name for field in dataclasses.fields(OpenResult)] == base + ['unverified']
    assert dataclasses.fields(OpenResult)[5].name == 'unverified'
    assert [field.name for field in dataclasses.fields(NotesResult)] == base + ['note_ids']
    # 負控：第六個位置參數確實落進 unverified，⛔ 不是被新欄接走
    assert OpenResult(0, None, '', None, (), ({'item': 'X'},)).unverified == ({'item': 'X'},)
    print('RESULT_FIELDS', [field.name for field in dataclasses.fields(NotesResult)])
