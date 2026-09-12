"""端到端：一張卡從清單項走到 結案/完成，含一次退回，七動詞全部經總入口 `main` 分派。

消費 core/verbs.md §1 七列／§2、core/state-machine.md §3 轉移表、core/dispatch.md、
core/return.md schema。所有 GitHub 操作走 cli/tests/fakes.py 的替身
（MemoryClient 之上加留言存放），⛔ 不碰網路、⛔ 不錄真實 API。
"""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import socket
import subprocess

import pytest

from wf.compose.blocks import load_blocks
from wf.gh.writes import read_block
from wf.verbs.main import main
from .test_closeout_flow import checker
from .test_open_verb import MemoryClient, block, intake, issue

RULES = Path(__file__).resolve().parents[2]
SHA = 'e' * 40
PLAN = ['需求', '執行', '審核', '結案']
DENIED = {'gh', 'curl', 'wget', 'ssh'}


class E2EClient(MemoryClient):
    """MemoryClient 之上再記住自己貼的留言：前輪 findings 與裁定單要讀得回來。"""

    def __init__(self, catalog, issues, items=()):
        super().__init__(catalog, issues, items)
        enums, = catalog.by_label('json wf-enums')
        options = {'階段': enums.data['stages']['enum'],
                   '狀態': [value for key, spec in enums.data.items()
                            if key.startswith('state') for value in spec['enum']],
                   '級別': enums.data['tiers']['enum']}
        self.options = {name: [{'id': value, 'name': value} for value in values]
                        for name, values in options.items()}
        self.stored = {}
        self.responses.update(comments=lambda number: deepcopy(self.stored.get(number, [])),
                              commit_exists=True, pulls_for_branch=[], branch_head=SHA,
                              is_ancestor=True)

    def post_comment(self, number, first_line, body):
        result = super().post_comment(number, first_line, body)
        rows = self.stored.setdefault(number, [])
        index = len(rows) + 1
        rows.append({'id': index, 'author': 'fake-actor',
                     'url': f'https://github.com/{self.repo}/issues/{number}#issuecomment-{index}',
                     'created_at': f'2026-09-08T00:{index:02d}:00Z',
                     'issue_url': f'https://api.github.com/repos/{self.repo}/issues/{number}',
                     'body': first_line + '\n' + body})
        return result

    def first_lines(self):
        return [kwargs['first_line'] for name, kwargs in self.calls if name == 'post_comment']


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(RULES)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """本機 git（merge-tree）照跑，`gh` 與任何 socket 連線一律擋（conduct-common §1）。"""
    real = subprocess.run

    def guarded(argv, *args, **kwargs):
        assert not isinstance(argv, (str, bytes)) and Path(argv[0]).name not in DENIED, 'E2E_DENIED'
        return real(argv, *args, **kwargs)

    def refuse(*args, **kwargs):
        raise AssertionError('E2E_DENIED')

    monkeypatch.setattr(subprocess, 'run', guarded)
    monkeypatch.setattr(socket.socket, 'connect', refuse)


@pytest.fixture
def workspace(tmp_path, catalog):
    root = tmp_path / 'repo'
    for part in ('core', 'modules', 'stages', 'roles'):
        shutil.copytree(RULES / part, root / part)
    (root / '.wf').mkdir()
    (root / '.wf/modules.json').write_text(json.dumps(
        {'areas': ['WF'], 'modules': [], 'project': {'owner': 'fake', 'number': 1}}),
        encoding='utf-8')
    source = issue(10, body='清單項散文\n' + block('wf-intake', intake()))
    return E2EClient(catalog, [source]), root


def sheet(root, name, **changes):
    """交回單檔；`review` 自己補 card_id／iteration／role／source_sha（core/return.md）。"""
    data = {'self_run': [{'command': 'pytest', 'rc': 0, 'observed': '751 passed'}],
            'acceptance': [], 'unverified': [], 'note_responses': [], 'out_of_scope': []} | changes
    path = root / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return str(path)


def finding(identifier, disposition):
    return {'finding_id': identifier, 'severity': 'major', 'blocking': True, 'status': 'open',
            'finding_class': 'implementation', 'attribution': 'executor',
            'root_cause_id': 'RC-1', 'evidence': '證據', 'disposition': disposition}


def verdict(root, name, result, findings):
    return sheet(root, name, review_result=result, core_pain_resolved='yes',
                 reason='一句話理由', findings=findings)


class Flow:
    """每步經 `main` 分派、抓 stdout、斷言 rc 與卡面 stage/state。"""

    def __init__(self, client, root, capsys):
        self.client, self.root, self.capsys = client, root, capsys
        self.log = []

    def card(self):
        return read_block(self.client.rows[10]['body'], 'wf-card')

    def __call__(self, argv, *, at=None, rc=0):
        code = main(argv, client=self.client, root=self.root)
        out = self.capsys.readouterr().out
        assert code == rc, (argv, out)
        card = self.card()
        self.log.append((argv[0], f"{card['stage']}/{card['state']}", card['iteration']))
        if at is not None:
            assert f"{card['stage']}/{card['state']}" == at, (argv, card['stage'], card['state'])
        return out


def to_first_verdict(step, root):
    """open → … → 第一則 REQUEST_CHANGES 裁定單（退回之前的共用前半段）。"""
    step(['open', '10'], at='需求/待辦')
    step(['edit', 'WF-001', '--set', 'feature="端到端"'], at='需求/待辦')
    step(['edit', 'WF-001', '--set', f'stage_plan={json.dumps(PLAN, ensure_ascii=False)}'])
    # 查核者交回單的 source_sha 由 `review` 取自卡面（core/return.md required），先填。
    step(['edit', 'WF-001', '--set', f'source_sha="{SHA}"'])
    step(['notes', 'WF-001'])
    step(['brief', 'WF-001', '--for', 'executor'])
    step(['move', 'WF-001', '--to', '進行中', '--actor', 'executor:a'], at='需求/進行中')
    step(['review', 'WF-001', '--file', sheet(root, 'r1.json'), '--role', 'executor'])
    step(['move', 'WF-001', '--to', '待確認'], at='需求/待確認')
    step(['brief', 'WF-001', '--for', 'reviewer'])
    step(['review', 'WF-001', '--role', 'reviewer', '--file',
          verdict(root, 'v1.json', 'REQUEST_CHANGES', [finding('F-CLI-01', '補測')])])


def drive(client, root, capsys, *, current_verdict=True):
    """完整流程；回傳 (Flow, 退回後的 reviewer 派工單, 裁定單, snapshot 輸出)。

    `current_verdict=False` 只給負控用：拿掉 iteration=1 的查核裁決那一步。
    """
    step = Flow(client, root, capsys)
    to_first_verdict(step, root)
    step(['move', 'WF-001', '--to', '退回'], at='需求/退回')
    step(['move', 'WF-001', '--to', '進行中', '--actor', 'executor:a'], at='需求/進行中')
    step(['review', 'WF-001', '--file', sheet(root, 'r2.json'), '--role', 'executor'])
    step(['move', 'WF-001', '--to', '待確認'], at='需求/待確認')
    reviewer_brief = step(['brief', 'WF-001', '--for', 'reviewer'])
    step(['review', 'WF-001', '--role', 'reviewer', '--file',
          verdict(root, 'v2.json', 'APPROVE', [finding('F-CLI-02', '已修')])])
    step(['move', 'WF-001', '--to', '執行/待辦'], at='執行/待辦')
    step(['move', 'WF-001', '--to', '進行中', '--actor', 'executor:a'], at='執行/進行中')
    # FINAL-7：當輪（iteration=1）的執行者交回與查核裁決，結案訊息才有當輪作者／結果可引。
    step(['review', 'WF-001', '--file', sheet(root, 'r3.json'), '--role', 'executor'])
    step(['move', 'WF-001', '--to', '待確認', '--source-sha', SHA], at='執行/待確認')
    step(['move', 'WF-001', '--to', '審核/待辦'], at='審核/待辦')
    step(['move', 'WF-001', '--to', '進行中', '--actor', 'reviewer:r'], at='審核/進行中')
    step(['move', 'WF-001', '--to', '待確認'], at='審核/待確認')
    if current_verdict:
        step(['review', 'WF-001', '--role', 'reviewer', '--file',
              verdict(root, 'v3.json', 'APPROVE', [finding('F-CLI-03', '當輪通過')])])
    step(['move', 'WF-001', '--to', '結案/待確認'], at='結案/待確認')
    closeout = step(['brief', 'WF-001', '--for', 'closeout'])
    step(['move', 'WF-001', '--to', '完成'], at='結案/完成')
    snap = step(['snapshot', '--out', str(root / 'out')])
    return step, reviewer_brief, closeout, snap


def squash_message(closeout):
    """從 `brief --for closeout` 的 stdout 取出唯一一個 ```text 圍欄裡的 squash 訊息。"""
    assert closeout.count('```text') == 1, closeout
    return closeout.split('```text\n', 1)[1].split('\n```', 1)[0]


def assert_current_round_squash(closeout):
    """FINAL-7：結案訊息要咬住**當輪**（iteration=1）的被審 SHA、作者與 review_result，
    且 trailer 末端連續、鍵在 P5 集合。負控（拿掉當輪裁定）必須讓這裡 FAIL。"""
    assert '缺 Reviewed-by' not in closeout
    msg = squash_message(closeout)
    blocks = msg.split('\n\n')
    assert blocks[0] == 'WF-001 端到端'
    assert blocks[1] == f'被審 SHA：{SHA}\nfake-actor：APPROVE'
    assert msg.count('：APPROVE') == 1 and '：REQUEST_CHANGES' not in msg
    assert blocks[-1] == 'Reviewed-by: fake-actor'
    check = checker()
    assert not check.check('generated', msg)
    assert {line.split(':', 1)[0].lower() for line in blocks[-1].splitlines()} <= check.ALLOWED
    return msg


def test_current_round_closeout_evidence(workspace, capsys):
    """射程 1／驗收 5：iteration=1 有執行者交回與查核裁決後，結案 squash 訊息帶當輪證據。"""
    client, root = workspace
    _, _, closeout, _ = drive(client, root, capsys)
    msg = assert_current_round_squash(closeout)
    bad = msg + '\n見上（不是 trailer 行）'
    errors = checker().check('negative', bad)
    assert errors  # conduct-common §1：先證明 trailer 檢查器會響（末段混入非 trailer 行）
    print('TRAILER_NEGATIVE rc=1', errors)
    print('當輪 squash 訊息：', json.dumps(msg, ensure_ascii=False))


def test_negative_control_missing_the_current_round_verdict(workspace, capsys):
    """驗收 5 的負控：拿掉 iteration=1 的查核裁決 ⇒ 當輪 reviewer 數為 0、印「缺 Reviewed-by」，
    上一題的當輪斷言必 FAIL（證明它咬得住，不是恆真）。"""
    client, root = workspace
    _, _, closeout, _ = drive(client, root, capsys, current_verdict=False)
    with pytest.raises(AssertionError):
        assert_current_round_squash(closeout)
    assert '缺 Reviewed-by' in closeout
    msg = squash_message(closeout)
    assert msg.split('\n\n')[1] == f'被審 SHA：{SHA}'  # 沒有任何當輪作者／結果行
    assert 'Reviewed-by' not in msg
    print('負控：少了當輪裁定 ⇒ squash 訊息＝', json.dumps(msg, ensure_ascii=False))


def test_seven_verbs_one_card_one_return(workspace, capsys):
    """射程 4／驗收 5：全流程 rc=0、逐步 stage/state 正確、七動詞都經 `main` 走到。"""
    client, root = workspace
    step, reviewer_brief, closeout, _ = drive(client, root, capsys)
    assert {name for name, _, _ in step.log} == {
        'open', 'edit', 'notes', 'brief', 'move', 'review', 'snapshot'}
    assert [(name, node) for name, node, _ in step.log][:6] == [
        ('open', '需求/待辦'), ('edit', '需求/待辦'), ('edit', '需求/待辦'),
        ('edit', '需求/待辦'), ('notes', '需求/待辦'), ('brief', '需求/待辦')]
    assert [node for _, node, _ in step.log][-4:] == [
        '結案/待確認', '結案/待確認', '結案/完成', '結案/完成']
    assert step.card()['stage_plan'] == PLAN
    assert '## 基線' in reviewer_brief and 'squash 訊息' in closeout
    print('端到端步序：', json.dumps(step.log, ensure_ascii=False))


def test_iteration_increments_only_on_entering_execution(workspace, capsys):
    """射程 4：iteration 只在進 執行/進行中 +1；需求階段的退回再派不加。"""
    client, root = workspace
    step, _, _, _ = drive(client, root, capsys)
    assert [n for _, node, n in step.log if node == '執行/待辦'] == [0]
    # 進 執行/進行中 之後多一筆當輪執行者交回，兩筆都必須是 iteration=1（只加不減嚴格度）。
    assert [n for _, node, n in step.log if node == '執行/進行中'] == [1, 1]
    assert {n for _, node, n in step.log if node.startswith('需求')} == {0}
    assert step.card()['iteration'] == 1


def test_previous_findings_after_the_return(workspace, capsys):
    """射程 4／驗收 5：退回再派後，`brief --for reviewer` 印得出上一則 reviewer 的 finding。"""
    client, root = workspace
    _, reviewer_brief, _, _ = drive(client, root, capsys)
    assert 'F-CLI-01' in reviewer_brief
    assert '無前輪' not in reviewer_brief


def test_negative_control_missing_the_return_move(workspace, capsys):
    """驗收 5 的負控：拿掉 `move --to 退回` 那一步，再派就不在合成表內（D1）——
    rc≠0、貼一則 wf:reject，後續步驟與前輪 findings 斷言無從成立。"""
    client, root = workspace
    step = Flow(client, root, capsys)
    to_first_verdict(step, root)
    out = step(['move', 'WF-001', '--to', '進行中', '--actor', 'executor:a'], rc=1)
    assert '需求/待確認 → 需求/進行中 不在合成表內' in out
    assert client.first_lines().count('wf:reject') == 1
    assert step.card()['state'] == '待確認'
    print('負控：少了 需求/退回 那一步，再派 rc=1 並拒收')


def test_terminal_closes_the_issue_exactly_once(workspace, capsys):
    """射程 4：終態關 issue 恰一次；全程 0 則 wf:reject。"""
    client, root = workspace
    drive(client, root, capsys)
    assert [name for name, _ in client.calls].count('close_issue') == 1
    assert client.first_lines().count('wf:reject') == 0
    print('留言首行母體：', json.dumps(client.first_lines(), ensure_ascii=False))


def test_snapshot_reconciles_without_mismatch(workspace, capsys):
    """射程 4：`snapshot` 對帳無不等；負控＝手動改掉一個投影欄後對帳必有不等。"""
    client, root = workspace
    _, _, _, out = drive(client, root, capsys)
    data = json.loads((root / 'out/snapshot.json').read_text(encoding='utf-8'))
    assert data['mismatches'] == []
    assert [row['card_id'] for row in data['cards']] == ['WF-001']
    client.board['items'][0]['fieldValues']['狀態'] = {'name': '待辦'}
    main(['snapshot', '--out', str(root / 'out')], client=client, root=root)
    capsys.readouterr()
    broken = json.loads((root / 'out/snapshot.json').read_text(encoding='utf-8'))
    assert [row['field'] for row in broken['mismatches']] == ['狀態']
    print('負控：投影欄改成 待辦 後 mismatches＝', json.dumps(broken['mismatches'], ensure_ascii=False))


def test_offline_guard_negative_control():
    """conduct-common §1：先證明護欄會響。"""
    with pytest.raises(AssertionError, match='E2E_DENIED'):
        subprocess.run(['gh', 'api', 'unused'])
    with socket.socket() as connection:
        with pytest.raises(AssertionError, match='E2E_DENIED'):
            connection.connect(('127.0.0.1', 9))


def test_multi_set_edit_writes_once_through_main(workspace, capsys):
    """CLI-003：經 main dispatch 一次帶三個 --set ⇒ 恰 1 次 update_card_body、恰 1 則 3 列的 wf:edit。"""
    client, root = workspace
    step = Flow(client, root, capsys)
    step(['open', '10'], at='需求/待辦')
    before = len([1 for name, _ in client.calls if name == 'update_card_body'])
    step(['edit', 'WF-001', '--set', 'feature="多欄原子提交"', '--set', 'service_goal="服務目標"',
          '--set', f'stage_plan={json.dumps(PLAN, ensure_ascii=False)}'], at='需求/待辦')
    writes = [kw for name, kw in client.calls if name == 'update_card_body'][before:]
    edits = [kw for name, kw in client.calls
             if name == 'post_comment' and kw['first_line'] == 'wf:edit']
    assert len(writes) == 1, writes
    assert len(edits) == 1 and len(edits[0]['body'].split('\n')) == 3, edits
    assert step.card()['feature'] == '多欄原子提交'
    assert step.card()['service_goal'] == '服務目標' and step.card()['stage_plan'] == PLAN
