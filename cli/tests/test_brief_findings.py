"""消費 core/dispatch.md 前輪 findings 列、core/return.md `wf-return`（role／iteration／findings）、
core/verbs.md §2「CLI 只讀三種留言區塊」。S11 驗收 5。
"""
import json

from .test_brief_sections import block, card, emitted, make_client, make_root, sections

FINDING = {'finding_id': 'F-WF-001-1-01', 'severity': 'major', 'blocking': True,
           'status': 'open', 'finding_class': 'implementation', 'attribution': 'executor',
           'root_cause_id': 'RC-1', 'evidence': '證據', 'disposition': '處置'}


def comment(number, body):
    return {'id': number, 'url': f'https://example.invalid/c{number}', 'author': 'someone',
            'created_at': f'2026-09-0{number}T00:00:00Z', 'body': body}


def wf_return(iteration, role, findings):
    return block('wf-return', {'card_id': 'WF-001', 'iteration': iteration, 'role': role,
                               'source_sha': 'e' * 40, 'findings': findings})


def finding(**changes):
    return FINDING | changes


def previous(lines):
    return dict(sections(lines))['前輪 findings'][1:]


def test_only_the_previous_round_reviewer_findings_are_listed(tmp_path):
    """驗收 5：兩輪 reviewer 交回單（iteration 0、1），卡面 iteration=2 ⇒ 只印 iteration 1。"""
    root = make_root(tmp_path)
    comments = [comment(1, '散文\n' + wf_return(0, 'reviewer', [finding(evidence='舊輪')])),
                comment(2, '散文\n' + wf_return(1, 'reviewer', [finding(evidence='前輪一'),
                                                               finding(evidence='前輪二')])),
                comment(3, '散文\n' + wf_return(1, 'executor', [finding(evidence='執行者的')])),
                comment(4, '沒有區塊的留言')]
    _, lines = emitted(make_client(card(iteration=2), comments=comments), root)
    got = [json.loads(line) for line in previous(lines)]
    assert [item['evidence'] for item in got] == ['前輪一', '前輪二']
    assert got[0] == finding(evidence='前輪一')


def test_no_previous_round_prints_the_literal(tmp_path):
    """驗收 5：沒有相符的 wf-return ⇒ 逐字「無前輪」；iteration 0 也是這條路。"""
    root = make_root(tmp_path)
    _, lines = emitted(make_client(card(iteration=0)), root)
    assert previous(lines) == ['無前輪']
    comments = [comment(1, wf_return(5, 'reviewer', [finding()]))]
    _, other = emitted(make_client(card(iteration=2), comments=comments), root)
    assert previous(other) == ['無前輪']


def test_broken_return_block_does_not_break_the_brief(tmp_path):
    """負控：留言的 wf-return 壞 JSON 或重複時當成沒有，rc 仍 0（brief 無寫入）。"""
    root = make_root(tmp_path)
    comments = [comment(1, '```json wf-return\n{壞\n```\n'),
                comment(2, wf_return(1, 'reviewer', []) + wf_return(1, 'reviewer', [])),
                comment(3, wf_return(1, 'reviewer', [finding(evidence='好的')]))]
    result, lines = emitted(make_client(card(iteration=2), comments=comments), root)
    assert result.rc == 0
    assert [json.loads(line)['evidence'] for line in previous(lines)] == ['好的']
