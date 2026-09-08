"""消費 core/verbs.md §1 notes／§2、core/naming.md §3、core/card-schema.md §4、
core/enums.md stages；roles/conduct-common.md §1 的負控。S10 驗收 6、8、9、10。
"""
import json
from pathlib import Path
import socket
import subprocess

import pytest

from .test_notes_verb import (WRITES, block, card, deny_network, emitted,  # noqa: F401
                              make_client, make_root, numbered)
from wf.verbs.notes import notes


def comment(identifier, body):
    return {'id': identifier, 'url': f'https://github.com/fake/repo/issues/10#issuecomment-{identifier}',
            'author': 'someone', 'created_at': '2026-09-08T00:00:00Z', 'body': 'wf:note\n' + body}


def test_candidates_listed_and_bad_blocks_reported(tmp_path):
    """驗收 6：合法者列候選、壞區塊印不合法、純散文留言⛔ 不列。"""
    root = make_root(tmp_path)
    good = {'text': '候選條目', 'origin': 'https://example.invalid/1'}
    comments = [comment(1, block('wf-note', good)),
                comment(2, block('wf-note', '{壞掉的 JSON')),
                comment(3, block('wf-note', {'text': '缺 origin'})),
                comment(4, '只有散文，沒有區塊。')]
    client = make_client(card(), comments=comments)
    result, lines = emitted(client, root)
    assert result.rc == 0
    assert lines == ['候選：候選條目｜https://example.invalid/1｜'
                     'https://github.com/fake/repo/issues/10#issuecomment-1',
                     '候選 https://github.com/fake/repo/issues/10#issuecomment-2 區塊不合法',
                     '候選 https://github.com/fake/repo/issues/10#issuecomment-3 區塊不合法']
    assert [name for name, _ in client.calls if name in WRITES] == []
    print('留言母體 4 則：1 合法、2 不合法、1 無區塊')


def test_candidate_positive_control_needs_a_block(tmp_path):
    """負控：同一則留言拿掉區塊後就不再出現候選行，證明比對真的會響。"""
    root = make_root(tmp_path)
    payload = block('wf-note', {'text': 'x', 'origin': 'https://example.invalid/1'})
    _, with_block = emitted(make_client(card(), comments=[comment(1, payload)]), root)
    _, without = emitted(make_client(card(), comments=[comment(1, '散文')]), root)
    assert len(with_block) == 1 and without == []


def test_unknown_stage_falls_back_to_card_stage(tmp_path):
    """驗收 8：非法 --stage 印一行、回退卡當前階段、rc=0、零遠端寫入。"""
    root = make_root(tmp_path, stages=['implementation.md', 'requirement.md'])
    client = make_client(card(stage='執行'))
    result, lines = emitted(client, root, stage='不存在的階段')
    assert result.rc == 0
    assert lines[0] == '階段 不存在的階段 不在 enums.stages，改用卡當前階段'
    assert numbered(lines) == [(1, 'F-執行-01')]
    assert [name for name, _ in client.calls if name in WRITES] == []


def test_default_stage_is_the_card_stage(tmp_path):
    """驗收 8：`--stage` 缺省＝卡當前 stage。"""
    root = make_root(tmp_path, stages=['implementation.md', 'requirement.md'])
    _, lines = emitted(make_client(card(stage='需求')), root)
    assert numbered(lines) == [(1, 'F-需求-01')]


def test_no_project_prints_resource_lock_notice(tmp_path):
    """本片 PM 預設：project=None 時 board_facts=() 並印一行。"""
    root = make_root(tmp_path, project=False)
    client = make_client(card())
    _, lines = emitted(client, root)
    assert lines == ['無 Project 設定，未評估 resource-lock']
    assert not any(name == 'project' for name, _ in client.calls)


def test_d3_on_broken_card_json(tmp_path):
    """驗收 9：卡面 JSON 壞 → rc≠0、恰一則 wf:reject、無其他寫入。"""
    root = make_root(tmp_path, stages=['implementation.md'])
    client = make_client('前言\n' + block('wf-card', '{壞掉的 JSON'))
    result = notes(10, client=client, root=root, emit=lambda line: None)
    assert result.rc != 0
    writes = [(name, data) for name, data in client.calls if name in WRITES]
    assert [name for name, _ in writes] == ['post_comment']
    assert writes[0][1]['first_line'] == 'wf:reject'
    assert writes[0][1]['body'].startswith('拒收・D3・')


def test_null_card_block_is_d3(tmp_path):
    """第 9 條探針：本卡 wf-card 值為 null ⇒ D3 一則 wf:reject（不是物件）。"""
    root = make_root(tmp_path, stages=['implementation.md'])
    client = make_client('前言\n```json wf-card\nnull\n```\n')
    result = notes(10, client=client, root=root, emit=lambda line: None)
    assert result.rc != 0 and '不是物件' in result.reason
    assert [name for name, _ in client.calls if name in WRITES] == ['post_comment']


@pytest.mark.parametrize('value', ['null', '[]', '"x"'])
def test_null_note_block_is_an_invalid_candidate(tmp_path, value):
    """第 9 條探針：wf-note 區塊值為 null／非物件＝不合法候選（URL 不消失），⛔ 不是沒有候選。"""
    root = make_root(tmp_path)
    _, lines = emitted(make_client(card(), comments=[comment(1, block('wf-note', value))]), root)
    assert lines == ['候選 https://github.com/fake/repo/issues/10#issuecomment-1 區塊不合法']


def test_card_id_lookup_skips_null_issue_and_prints(tmp_path):
    """第 9 條探針（card_number）：以卡ID 呼叫 notes，別的 issue 的 null 區塊只略過並印一行。"""
    root = make_root(tmp_path, stages=['implementation.md'])
    client = make_client(card())
    client.responses['issues'] = [{'number': 3, 'body': '```json wf-card\nnull\n```'}, client.responses['issue']]
    result = notes('WF-001', client=client, root=root, emit=lambda line: None)
    assert result.rc == 0 and result.printed[0] == '略過無法解析的 issue #3'


def test_d3_positive_control_valid_card_writes_nothing(tmp_path):
    """負控：同一路徑換成合法卡面即不寫 wf:reject。"""
    root = make_root(tmp_path, stages=['implementation.md'])
    client = make_client(card())
    assert notes(10, client=client, root=root, emit=lambda line: None).rc == 0
    assert [name for name, _ in client.calls if name in WRITES] == []


def test_source_is_within_the_line_budget():
    """驗收 10：本片 src ≤200 行。"""
    from wf.verbs import notes as module
    assert len(Path(module.__file__).read_text(encoding='utf-8').splitlines()) <= 200
