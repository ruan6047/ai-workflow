"""消費 core/verbs.md §1 notes／§2／§3、core/naming.md §3／§4、
core/card-schema.md §1／§4、core/handoff.md 來源標記、core/enums.md stages、
modules/pitfalls-13/module.md §1。所有遠端操作由手構替身接住。
"""
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess

import pytest

from .fakes import FakeGhClient
from wf.compose.blocks import load_blocks
from wf.verbs.notes import notes, run


RULES = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / 'fixtures/notes'
WRITES = ('update_card_body', 'post_comment',
          'write_project_field', 'add_to_project', 'remove_from_project', 'close_issue')


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


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('禁止真實網路或子程序')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(subprocess, 'run', forbidden)


def test_four_sources_in_order_with_continuous_numbering(tmp_path):
    """驗收 1：四來源各 1 條 → F(核心)、F(模組)、P、T，編號 1..n 連續。"""
    root = make_root(tmp_path, stages=['implementation.md'], roles=['executor.md'],
                     modules=['demo'], listed=['demo'], project_stage='執行')
    client = make_client(card(notes=[{'id': 'T-執行-01', 'text': '卡面條目',
                                      'origin': 'https://example.invalid/1'}]))
    result, lines = emitted(client, root)
    assert result.rc == 0
    assert numbered(lines) == [(1, 'F-執行-01'), (2, 'F-執行者-01'), (3, 'F-demo-01'),
                               (4, 'P-執行-01'), (5, 'T-執行-01')]
    assert [name for name, _ in client.calls if name in WRITES] == []


def test_core_order_stages_then_roles_by_filename(tmp_path):
    """PM 預設：階段檔 → roles/ 依檔名字典序，檔內出現序。"""
    root = make_root(tmp_path, stages=['implementation.md', 'requirement.md'],
                     roles=['aaa-role.md', 'executor.md'])
    _, lines = emitted(make_client(card(owner=None)), root)  # owner null＝角色檔全印並註明（§3）
    assert numbered(lines) == [(1, 'F-執行-01'), (2, 'F-AAA-01'), (3, 'F-執行者-01')]
    assert '卡面 owner 未填，角色注意事項全印' in lines


def test_only_id_shaped_bullets_inside_the_section_are_read(tmp_path):
    """驗收 2：散文、無 id 條列、別階段、非兩位數 NN、§6 以外的行都不讀。"""
    root = make_root(tmp_path, stages=['implementation.md'])
    _, lines = emitted(make_client(card()), root)
    assert numbered(lines) == [(1, 'F-執行-01')]
    body = (FIXTURES / 'stages/implementation.md').read_text(encoding='utf-8')
    population = [line for line in body.splitlines()
                  if line.strip() and not line.startswith(('#', '-' * 3, 'name', 'when',
                                                           'non_scope', 'last_confirmed'))]
    rejected = [line for line in body.splitlines() if '⛔ 不該被讀' in line]
    assert len(rejected) == 5
    assert not any(any(text in line for line in lines) for text in rejected)
    print('母體：檔內非標題非 frontmatter 行', len(population), '行，明示不可讀',
          len(rejected), '行，輸出取 1 行')


def test_stage_prefix_separates_executor_role_from_execution_stage(tmp_path):
    """驗收 2：--stage 執行 取 F-執行-，尾端 - 把 F-執行者- 擋在階段來源外。"""
    root = make_root(tmp_path, stages=['implementation.md'], roles=['executor.md'])
    _, lines = emitted(make_client(card(stage='需求')), root, stage='執行')
    assert numbered(lines) == [(1, 'F-執行-01'), (2, 'F-執行者-01')]
    assert not any('F-執行者-91' in line for line in lines)


def test_source_marks_carry_origin_and_frontmatter(tmp_path):
    """驗收 5 與 PM 預設：四值來源前綴；T- 無 frontmatter 省略後兩段。"""
    root = make_root(tmp_path, stages=['implementation.md'], modules=['demo'],
                     listed=['demo'], project_stage='執行')
    client = make_client(card(notes=[{'id': 'T-執行-01', 'text': '卡面條目',
                                      'origin': 'https://example.invalid/1'}]))
    _, lines = emitted(client, root)
    assert lines[0] == ('1. F-執行-01：核心階段條目。 [來源: core/stages/implementation.md'
                        '#6 · 注意事項 · implementation-fixture：合成順序與條列文法的樣本'
                        ' · confirmed 2026-09-08]')
    assert lines[1].endswith('[來源: module/modules/demo/module.md#2 · 注意事項'
                             ' · demo：合成順序樣本的假模組 · confirmed 2026-09-08]')
    assert lines[2].endswith('[來源: project/.wf/stages/執行.md]')
    assert lines[3].endswith('[來源: card/issues/10#notes]')


def test_card_notes_keep_their_order(tmp_path):
    """驗收 5：卡面 notes 欄兩條照序印，來源標記＝card。"""
    root = make_root(tmp_path)
    entries = [{'id': 'T-執行-01', 'text': '先', 'origin': 'https://example.invalid/1'},
               {'id': 'T-執行-02', 'text': '後', 'origin': 'https://example.invalid/2'}]
    _, lines = emitted(make_client(card(notes=entries)), root)
    assert numbered(lines) == [(1, 'T-執行-01'), (2, 'T-執行-02')]
    assert all(line.endswith('[來源: card/issues/10#notes]') for line in lines)


def test_project_stage_file_missing_prints_nothing(tmp_path):
    """驗收 4：`.wf/stages/<階段>.md` 缺＝零條、⛔ 不印缺。"""
    present = make_root(tmp_path / 'a', project_stage='執行')
    absent = make_root(tmp_path / 'b')
    _, with_file = emitted(make_client(card()), present)
    _, without = emitted(make_client(card()), absent)
    assert numbered(with_file) == [(1, 'P-執行-01')]
    assert without == []


def test_enabled_module_notes_and_declaration_mismatch(tmp_path):
    """驗收 3：真 escalation 印四條；ghost 宣告的 F-ghost-02 未在 §2 印一行、rc=0。"""
    real = make_root(tmp_path / 'a', real=True, listed=['escalation'])
    _, lines = emitted(make_client(card()), real)
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
