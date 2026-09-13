"""消費 core/verbs.md §1 notes／§2、core/naming.md §3、core/card-schema.md §4、
core/enums.md stages；roles/conduct-common.md §1 的負控。
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
    good = {'id': 'T-執行-01', 'text': '候選條目', 'origin': 'https://example.invalid/1'}
    comments = [comment(1, block('wf-note', good)),
                comment(2, block('wf-note', '{壞掉的 JSON')),
                comment(3, block('wf-note', {'text': '缺 origin'})),
                comment(4, '只有散文，沒有區塊。')]
    client = make_client(card(), comments=comments)
    result, lines = emitted(client, root)
    assert result.rc == 0
    assert lines == ['候選：候選條目｜https://example.invalid/1｜'
                     'https://github.com/fake/repo/issues/10#issuecomment-1',
                     '候選 https://github.com/fake/repo/issues/10#issuecomment-2 區塊 1 '
                     '不合法：wf-note JSON 解析失敗',
                     '候選 https://github.com/fake/repo/issues/10#issuecomment-3 區塊 1 '
                     '不合法：/id: required; /origin: required']
    assert [name for name, _ in client.calls if name in WRITES] == []
    print('留言母體 4 則：1 合法、2 不合法、1 無區塊')


def test_candidate_positive_control_needs_a_block(tmp_path):
    """負控：同一則留言拿掉區塊後就不再出現候選行，證明比對真的會響。"""
    root = make_root(tmp_path)
    payload = block('wf-note', {'id': 'T-執行-01', 'text': 'x', 'origin': 'https://example.invalid/1'})
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
    """PM 預設：project=None 時 board_facts=() 並印一行。"""
    root = make_root(tmp_path, project=False)
    client = make_client(card())
    _, lines = emitted(client, root)
    assert lines == ['無 Project 設定，未評估 resource-lock']
    assert not any(name == 'project' for name, _ in client.calls)


def hard_blocks(lines):
    """本機硬擋行（core/verbs.md §2 `硬擋・<D 編號>・<原因>`）。"""
    return [line for line in lines if line.startswith('硬擋・')]


def test_d3_on_broken_card_json(tmp_path):
    """驗收 9／WF-003：卡面 JSON 壞＝讀側 D3 ⇒ rc≠0、遠端零寫入、本機恰一行 `硬擋・D3・<原因>`。

    斷言序＝先驗寫入呼叫集合為空，再從本機行讀 D 編號與原因；⛔ 不先取 writes[0]（零寫入下
    必 IndexError，會把修好誤報成崩潰）。基線 005bab29ae1c3a3fbfc4a3520c56aca198a565d8 在
    同一輸入下是一則 post_comment(first_line='wf:reject', body='拒收・D3・…')、stdout 零行。
    """
    root = make_root(tmp_path, stages=['implementation.md'])
    client = make_client('前言\n' + block('wf-card', '{壞掉的 JSON'))
    lines = []
    result = notes(10, client=client, root=root, emit=lines.append)
    assert [name for name, _ in client.calls if name in WRITES] == []
    assert result.rc == 1 and result.reason
    assert hard_blocks(lines) == ['硬擋・D3・' + result.reason]


def test_null_card_block_is_d3(tmp_path):
    """null 區塊探針／WF-003：本卡 wf-card 值為 null ⇒ 讀側 D3 本機硬擋（不是物件）、遠端零寫入。"""
    root = make_root(tmp_path, stages=['implementation.md'])
    client = make_client('前言\n```json wf-card\nnull\n```\n')
    lines = []
    result = notes(10, client=client, root=root, emit=lines.append)
    assert [name for name, _ in client.calls if name in WRITES] == []
    assert result.rc == 1 and '不是物件' in result.reason
    assert hard_blocks(lines) == ['硬擋・D3・' + result.reason]


@pytest.mark.parametrize('value', ['null', '[]', '"x"'])
def test_null_note_block_is_an_invalid_candidate(tmp_path, value):
    """null 區塊探針：wf-note 區塊值為 null／非物件＝不合法候選（URL 不消失），⛔ 不是沒有候選。"""
    root = make_root(tmp_path)
    _, lines = emitted(make_client(card(), comments=[comment(1, block('wf-note', value))]), root)
    assert lines == ['候選 https://github.com/fake/repo/issues/10#issuecomment-1 區塊 1 '
                     '不合法：wf-note 不是物件']


def test_card_id_lookup_skips_null_issue_and_prints(tmp_path):
    """null 區塊探針（card_number）：以卡ID 呼叫 notes，別的 issue 的 null 區塊只略過並印一行。"""
    root = make_root(tmp_path, stages=['implementation.md'])
    client = make_client(card())
    client.responses['issues'] = [{'number': 3, 'body': '```json wf-card\nnull\n```'}, client.responses['issue']]
    result = notes('WF-001', client=client, root=root, emit=lambda line: None)
    assert result.rc == 0 and result.printed[0] == '略過無法解析的 issue #3'


def test_d3_positive_control_valid_card_writes_nothing(tmp_path):
    """負控：同一路徑換成合法卡面即 rc=0 且無硬擋行（零寫入兩邊都成立，故另比硬擋行）。"""
    root = make_root(tmp_path, stages=['implementation.md'])
    client = make_client(card())
    lines = []
    assert notes(10, client=client, root=root, emit=lines.append).rc == 0
    assert [name for name, _ in client.calls if name in WRITES] == []
    assert hard_blocks(lines) == []


URL = 'https://github.com/fake/repo/issues/10#issuecomment-1'


def item(index, **changes):
    """三鍵齊全的合法 wf-note；changes 只動指定鍵，⛔ 不重打整份。"""
    return {'id': f'T-執行-{index:02d}', 'text': f'條目{index}',
            'origin': f'https://example.invalid/{index}'} | changes


def only_candidates(lines):
    return [line for line in lines if line.startswith('候選')]


# A1：一則留言 N 個區塊（N=0／1／4）逐區塊獨立成候選，序號 1 起依出現序。
@pytest.mark.parametrize('count', [0, 1, 4])
def test_zero_one_many_wf_note_blocks_per_comment(tmp_path, count):
    root = make_root(tmp_path)
    rows = [item(i) for i in range(1, count + 1)]
    body = ''.join(block('wf-note', row) for row in rows) or '只有散文，沒有區塊。'
    client = make_client(card(), comments=[comment(1, body)])
    result, lines = emitted(client, root)
    assert result.rc == 0
    assert lines == [f"候選：{row['text']}｜{row['origin']}｜{URL}" for row in rows]
    assert len(lines) == count
    assert [name for name, _ in client.calls if name in WRITES] == []
    print('MULTI_BLOCK', count, '個區塊 →', len(lines), '個候選行')


# A1／A3：壞兄弟⛔ 不遮蔽合法區塊；三類壞各自帶序號與原因；fence 未閉合只得留言級一行。
def test_bad_sibling_does_not_mask_valid_or_comment_level(tmp_path):
    root = make_root(tmp_path)
    body = (block('wf-note', item(1)) + block('wf-note', '{壞掉的 JSON')
            + block('wf-note', '[]') + block('wf-note', item(4, id='bad')))
    _, lines = emitted(make_client(card(), comments=[comment(1, body)]), root)
    assert lines == [
        f"候選：{item(1)['text']}｜{item(1)['origin']}｜{URL}",
        f'候選 {URL} 區塊 2 不合法：wf-note JSON 解析失敗',
        f'候選 {URL} 區塊 3 不合法：wf-note 不是物件',
        f'候選 {URL} 區塊 4（id=bad） 不合法：/id: pattern']
    unterminated = block('wf-note', item(1)).removesuffix('```\n')
    _, only = emitted(make_client(card(), comments=[comment(1, unterminated)]), root)
    assert only == [f'候選 {URL} wf-note 區塊未閉合']  # ⛔ 無任何區塊級項目


# A4：三鍵全同才算已正式化並略過；只差一鍵者仍列候選。
def test_exact_three_key_dedupe_prints_skip_line(tmp_path):
    root = make_root(tmp_path)
    formal = item(1)
    body = (block('wf-note', formal) + block('wf-note', item(1, text='不同文字'))
            + block('wf-note', item(1, id='T-執行-09')))
    _, lines = emitted(make_client(card(notes=[formal]), comments=[comment(1, body)]), root)
    assert numbered(lines) == [(1, 'T-執行-01')]  # 正式清單的印法⛔ 不變
    assert only_candidates(lines) == [
        f"候選 {URL} 區塊 1（id={formal['id']}）已正式化，略過",
        f"候選：不同文字｜{formal['origin']}｜{URL}",
        f"候選：{formal['text']}｜{formal['origin']}｜{URL}"]
    # 負控：卡面 notes 清空後同一則留言的三個區塊全成候選、零略過行。
    _, without = emitted(make_client(card(), comments=[comment(1, body)]), root)
    assert [line for line in without if '已正式化' in line] == []
    assert len(only_candidates(without)) == 3


def test_source_is_within_the_line_budget():
    """驗收 10：src ≤200 行。"""
    from wf.verbs import notes as module
    assert len(Path(module.__file__).read_text(encoding='utf-8').splitlines()) <= 200
