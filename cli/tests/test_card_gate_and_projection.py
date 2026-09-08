"""S16：讓 CLI 追上現行規則（astra 總檢查 FINAL-1～6）。

消費 core/verbs.md §1（open／edit／notes／brief／review 列）／§2（D3、對帳、snapshot 例外）／§3
第 1 條、core/card-schema.md §1／§5 `json wf-projection`、core/enums.md `tiers`。
每條各一正向與一負控（roles/conduct-common.md §1：先證明比對真的會響）；
所有 GitHub 操作由 cli/tests 既有替身接住，⛔ 不碰網路。
"""
import json
from pathlib import Path
import socket
import subprocess

import pytest

from wf.compose.blocks import load_blocks, projection
from wf.gh.client import GhError
from wf.gh.writes import WriteMixin, read_block
from wf.verbs import _write
from wf.verbs.brief import brief, _previous_findings
from wf.verbs.edit import edit
from wf.verbs.notes import notes
from wf.verbs.open import open_issue
from wf.verbs.review import review
from wf.verbs.snapshot import snapshot

from .test_brief_sections import block, card, make_client, make_root, WRITES
from .test_end_to_end import E2EClient
from .test_open_verb import expected_card, item, issue

RULES = Path(__file__).resolve().parents[2]
BOARD = {'階段': {'name': '執行'}, '狀態': {'name': '進行中'}, '級別': {'name': 'T3'},
         'owner': None, '卡ID': {'text': 'WF-001'}}


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(RULES)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('S16_NETWORK_DENIED')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(subprocess, 'run', forbidden)
    with pytest.raises(AssertionError, match='S16_NETWORK_DENIED'):
        subprocess.run(['gh', 'api', 'negative-control'])


def board_client(catalog, card_json, values=None, **responses):
    """板上有本卡的 E2EClient；values 給投影欄現值（None＝與卡面一致的空欄）。"""
    row = issue(10, card=card_json)
    entry = item(10) | {'id': 'ITEM', 'fieldValues': dict(BOARD if values is None else values)}
    client = E2EClient(catalog, [row], [entry])
    client.responses.setdefault('merge_base', 'b' * 40)
    client.responses.update(responses)
    return client


def sheet(tmp_path, data=None):
    path = tmp_path / 'return.json'
    path.write_text(json.dumps({} if data is None else data, ensure_ascii=False), encoding='utf-8')
    return path


def rejects(client):
    return [kwargs for name, kwargs in client.calls
            if name == 'post_comment' and kwargs['first_line'] == 'wf:reject']


def first_lines(client):
    return [kwargs['first_line'] for name, kwargs in client.calls if name == 'post_comment']


# ── FINAL-1：卡面 D3（鍵集合封閉、整卡拒）在 notes／brief／review ────────────────

def run_verb(name, tmp_path, root, client):
    lines = []
    if name == 'notes':
        return notes(10, client=client, root=root, emit=lines.append), lines
    if name == 'brief':
        return brief(10, target='executor', client=client, root=root, emit=lines.append), lines
    return review(10, file=sheet(tmp_path), role='executor', client=client, root=root,
                  emit=lines.append), lines


@pytest.mark.parametrize('verb', ['notes', 'brief', 'review'])
def test_illegal_card_key_is_rejected_once_by_every_verb(tmp_path, verb):
    """FINAL-1 正向：卡面多一個 `unexpected` 鍵 ⇒ rc≠0、恰一則 wf:reject、⛔ 無其他寫入。"""
    root = make_root(tmp_path, project=False)
    client = make_client(card(unexpected='非法鍵', branch='wf/WF-001', source_sha='b' * 40))
    result, _ = run_verb(verb, tmp_path, root, client)
    assert result.rc != 0
    writes = [name for name, _ in client.calls if name in WRITES]
    assert writes == ['post_comment'], writes
    assert first_lines(client) == ['wf:reject']
    assert rejects(client)[0]['body'].startswith('拒收・D3・')
    assert 'unexpected' in rejects(client)[0]['body']
    print('FINAL-1', verb, rejects(client)[0]['body'])


@pytest.mark.parametrize('verb', ['notes', 'brief', 'review'])
def test_removing_the_card_gate_lets_the_illegal_key_through(tmp_path, verb, monkeypatch):
    """FINAL-1 負控：把 check_card 換成不判的樁 ⇒ 同一張卡 rc=0，證明擋下來的正是這道驗證。"""
    monkeypatch.setattr(_write, 'check_card', lambda *args, **kwargs: None)
    for module in ('notes', 'brief', 'review'):
        monkeypatch.setattr(f'wf.verbs.{module}.check_card', lambda *a, **k: None)
    root = make_root(tmp_path, project=False)
    client = make_client(card(unexpected='非法鍵', branch='wf/WF-001', source_sha='b' * 40))
    result, _ = run_verb(verb, tmp_path, root, client)
    assert result.rc == 0, result.reason
    assert 'wf:reject' not in first_lines(client)
    print('FINAL-1 負控', verb, 'rc', result.rc, first_lines(client))


def test_review_posts_no_verdict_when_the_card_face_is_rejected(tmp_path):
    """FINAL-1：`review --role reviewer` 卡面不過時 ⛔ 不得貼 wf:verdict。"""
    root = make_root(tmp_path, project=False)
    client = make_client(card(unexpected=1, source_sha='b' * 40))
    result = review(10, file=sheet(tmp_path), role='reviewer', client=client, root=root,
                    emit=lambda line: None)
    assert result.rc != 0 and first_lines(client) == ['wf:reject']


# ── FINAL-2a：edit 的投影鍵回寫 ───────────────────────────────────────────────

def test_edit_writes_back_the_projection_when_a_projection_key_changes(tmp_path, catalog):
    """FINAL-2a 正向：`--set tier=` ⇒ 卡面與板上都變；`json wf-projection` 五欄全部回寫。"""
    client = board_client(catalog, card(tier='T3'))
    result = edit(10, 'tier="T4"', client=client, catalog=catalog,
                  project_owner='fake', project_number=1)
    assert result.rc == 0 and result.card['tier'] == 'T4'
    assert client.board['items'][0]['fieldValues']['級別'] == {'name': 'T4'}
    # S17：先算後寫之後 prepare_project_field 另含新舊卡的試算，故以實際寫入斷言五欄。
    written = [prepared[2]['fieldId'] for name, prepared in client.calls
               if name == 'write_project_field']
    assert written == list(projection(catalog))


def test_edit_leaves_the_board_alone_for_non_projection_keys(tmp_path, catalog):
    """FINAL-2a 負控：同一條路徑改非投影鍵 `feature` ⇒ 零投影欄寫入，板上級別不動。"""
    client = board_client(catalog, card(tier='T3'))
    result = edit(10, 'feature="改過"', client=client, catalog=catalog,
                  project_owner='fake', project_number=1)
    assert result.rc == 0
    # S17：試算（prepare_project_field）是讀不是寫；此列要的是零投影欄「寫入」。
    assert [name for name, _ in client.calls
            if name == 'write_project_field'] == []
    assert client.board['items'][0]['fieldValues']['級別'] == {'name': 'T3'}


# ── FINAL-2b：下一次動詞先對帳（snapshot 例外） ───────────────────────────────

@pytest.mark.parametrize('verb', ['notes', 'brief', 'review', 'edit'])
def test_next_verb_rewrites_the_drifted_projection_column(tmp_path, catalog, verb):
    """FINAL-2b 正向：卡面 T1／板上 T3 ⇒ 動詞先把板上重寫成 T1 並印那一行，rc=0、⛔ 不拒收。"""
    root = make_root(tmp_path)
    client = board_client(catalog, card(tier='T1', branch='wf/WF-001', source_sha='b' * 40))
    lines = []
    if verb == 'edit':
        result = edit(10, 'feature="改過"', client=client, catalog=catalog,
                      project_owner='fake', project_number=1, emit=lines.append)
    else:
        result, lines = run_verb(verb, tmp_path, root, client)
    assert result.rc == 0
    assert '重寫投影欄：級別' in lines, lines
    assert client.board['items'][0]['fieldValues']['級別'] == {'name': 'T1'}


@pytest.mark.parametrize('verb', ['notes', 'brief', 'review'])
def test_without_the_reconcile_call_the_drift_survives(tmp_path, catalog, verb, monkeypatch):
    """FINAL-2b 負控：拿掉對帳呼叫 ⇒ 板上仍是 T3、那一行不再出現。"""
    for module in ('notes', 'brief', 'review'):
        monkeypatch.setattr(f'wf.verbs.{module}.reconcile_projection', lambda *a, **k: None)
    root = make_root(tmp_path)
    client = board_client(catalog, card(tier='T1', branch='wf/WF-001', source_sha='b' * 40))
    result, lines = run_verb(verb, tmp_path, root, client)
    assert result.rc == 0
    assert not [line for line in lines if line.startswith('重寫投影欄：')]
    assert client.board['items'][0]['fieldValues']['級別'] == {'name': 'T3'}


def test_snapshot_only_prints_the_mismatch(tmp_path, catalog):
    """FINAL-2b 的例外（§2 末句）：同一組不等，`snapshot` 只印、⛔ 不重寫。"""
    root = make_root(tmp_path)
    client = board_client(catalog, card(tier='T1'))
    lines = []
    result = snapshot(client=client, root=root, catalog=catalog, out=tmp_path / 'out',
                      emit=lines.append)
    assert result.rc == 0
    assert not [name for name, _ in client.calls if name == 'write_project_field']
    assert client.board['items'][0]['fieldValues']['級別'] == {'name': 'T3'}
    assert not [line for line in lines if line.startswith('重寫投影欄：')]


# ── FINAL-3：未知不得冒充「無前輪」 ──────────────────────────────────────────

def boom(**kwargs):
    raise GhError('留言讀取失敗')


def previous_section(lines):
    from .test_brief_sections import sections
    return dict(sections(lines))['前輪 findings'][1:]


def findings_ctx(client):
    from types import SimpleNamespace
    return SimpleNamespace(card=card(iteration=2), number=10, client=client)


def test_unreadable_comments_print_unknown_not_no_previous(tmp_path):
    """FINAL-3 正向：`comments` 拋 GhError ⇒ 該列逐字印未能取得，⛔ 不印「無前輪」。"""
    client = make_client(card())
    client.responses['comments'] = boom
    assert _previous_findings(findings_ctx(client)) == ['未能取得前輪 findings：留言讀取失敗']


def test_readable_but_empty_is_still_no_previous(tmp_path):
    """FINAL-3 負控（同一函式、同一 ctx）：讀得到而確實沒有 ⇒ 逐字「無前輪」。"""
    assert _previous_findings(findings_ctx(make_client(card()))) == ['無前輪']


def test_unparsable_return_block_prints_unknown(tmp_path):
    """FINAL-3 正向二：`wf-return` 區塊壞掉 ⇒ 一樣印未能取得。"""
    root = make_root(tmp_path, project=False)
    bad = {'id': 1, 'url': 'https://example.invalid/c', 'author': 'a',
           'created_at': '2026-09-01T00:00:00Z', 'body': block('wf-return', '{壞掉')}
    lines = []
    brief(10, target='executor', client=make_client(card(), comments=[bad]), root=root,
          emit=lines.append)
    section = previous_section(lines)
    assert len(section) == 1 and section[0].startswith('未能取得前輪 findings：')
    assert '無前輪' not in lines


def test_readable_and_empty_still_prints_no_previous(tmp_path):
    """FINAL-3 負控：留言讀得到而確實沒有 ⇒ 逐字「無前輪」；證明上面兩案的差異來自讀取結果。"""
    root = make_root(tmp_path, project=False)
    lines = []
    brief(10, target='executor', client=make_client(card()), root=root, emit=lines.append)
    assert previous_section(lines) == ['無前輪']


# ── FINAL-4：角色檔只取 owner.role／--for 那份 ───────────────────────────────

def note_ids(lines):
    import re
    return [match[1] for match in
            (re.match(r'^[0-9]+\. ([FPT]-.+?-[0-9]{2})：', line) for line in lines) if match]


def test_notes_takes_only_the_owner_role_file(tmp_path):
    """FINAL-4 正向：executor 卡 ⇒ 有 F-執行者-*，⛔ 無 F-PM-*／F-查核者-*／F-需求方-*。"""
    root = make_root(tmp_path, project=False)
    owner = {'role': 'executor', 'actor': '某執行者'}
    _, lines = [], []
    notes(10, client=make_client(card(owner=owner)), root=root, emit=lines.append)
    ids = note_ids(lines)
    assert any(i.startswith('F-執行者-') for i in ids)
    assert [i for i in ids if i.startswith(('F-PM-', 'F-查核者-', 'F-需求方-'))] == []
    print('FINAL-4 母體：roles/*.md 共',
          len(list((RULES / 'roles').glob('*.md'))), '檔，取用 1 檔；印出 id', len(ids), '條')


def test_notes_owner_null_prints_every_role_file(tmp_path):
    """FINAL-4 負控：owner 為 null ⇒ 四個角色檔全印並註明，證明篩選確實在起作用。"""
    root = make_root(tmp_path, project=False)
    lines = []
    notes(10, client=make_client(card(owner=None)), root=root, emit=lines.append)
    ids = note_ids(lines)
    assert '卡面 owner 未填，角色注意事項全印' in lines
    for prefix in ('F-執行者-', 'F-PM-', 'F-查核者-', 'F-需求方-'):
        assert any(i.startswith(prefix) for i in ids), prefix


def test_brief_for_reviewer_takes_the_reviewer_role_file(tmp_path):
    """FINAL-4：`brief --for reviewer` 取查核者那份，⛔ 不取卡面 owner 的執行者那份。"""
    root = make_root(tmp_path, project=False)
    owner = {'role': 'executor', 'actor': '某執行者'}
    lines = []
    brief(10, target='reviewer', client=make_client(card(owner=owner)), root=root,
          emit=lines.append)
    ids = note_ids(lines)
    assert any(i.startswith('F-查核者-') for i in ids)
    assert [i for i in ids if i.startswith('F-執行者-')] == []


# ── FINAL-5：tier 降級而缺裁定或 kind 不符 ──────────────────────────────────

DOWNGRADE = 'tier 降級而缺 --ruling 或 kind≠tier_change'
RULING_URL = 'https://github.com/fake/repo/issues/10#issuecomment-9'


def ruling_client(catalog, card_json, kind=None):
    client = board_client(catalog, card_json)
    body = '散文\n' if kind is None else '散文\n' + block('wf-ruling', {'kind': kind})
    client.responses['comment'] = lambda **kwargs: {
        'id': 9, 'author': 'pm', 'body': body,
        'issue_url': 'https://api.github.com/repos/fake/repo/issues/10'}
    client.comment_from_url = lambda url: WriteMixin.comment_from_url(client, url)
    return client


@pytest.mark.parametrize('start,target,kind,expected', [
    ('T3', 'T1', None, True),      # 降級、無 --ruling
    ('T3', 'T1', 'stop', True),    # 降級、kind≠tier_change
    ('T3', 'T1', 'tier_change', False),
    ('T1', 'T3', None, False),     # 升級
    ('T1', 'T1', None, False)])    # 同值
def test_tier_downgrade_hint(tmp_path, catalog, capsys, start, target, kind, expected):
    """FINAL-5：降級而缺裁定或 kind 不符才印，只印不擋；升級與同值 ⛔ 不印（含負控四組）。"""
    client = ruling_client(catalog, card(tier=start), kind)
    result = edit(10, f'tier="{target}"', client=client, catalog=catalog,
                  ruling=None if kind is None else RULING_URL,
                  project_owner='fake', project_number=1)
    assert result.rc == 0
    assert (DOWNGRADE in capsys.readouterr().out) is expected
    assert (DOWNGRADE in result.printed) is expected


def test_tier_order_comes_from_the_enums_block(catalog):
    """FINAL-5 的值域來源：序取自 core/enums.md `tiers`，⛔ 不在程式碼裡重打。"""
    enums, = catalog.by_label('json wf-enums')
    assert enums.data['tiers']['enum'] == ['T0', 'T1', 'T2', 'T3', 'T4']
    source = Path(edit.__globals__['__file__']).read_text(encoding='utf-8')
    assert "'T0'" not in source and '"T4"' not in source


# ── FINAL-6：撤銷卡復板寫轉移記錄留言 ───────────────────────────────────────

@pytest.fixture
def open_root(tmp_path):
    (tmp_path / 'core').mkdir()
    (tmp_path / 'core/card-schema.md').write_text(
        (RULES / 'core/card-schema.md').read_text(encoding='utf-8'), encoding='utf-8')
    (tmp_path / '.wf').mkdir()
    (tmp_path / '.wf/modules.json').write_text(json.dumps(
        {'areas': ['WF'], 'modules': [], 'project': {'owner': 'fake', 'number': 1}}),
        encoding='utf-8')
    return tmp_path


def test_restore_writes_one_move_comment(open_root, catalog):
    """FINAL-6 正向：撤銷卡復板 ⇒ 恰一則 wf:move，本文形狀同 move 的「來源 → 目標」。"""
    old = expected_card(card_id='WF-027', iteration=7, stage='規劃', state='待確認')
    client = E2EClient(catalog, [issue(10, card=old)])
    result = open_issue(10, client=client, root=open_root, catalog=catalog, emit=lambda line: None)
    assert result.rc == 0
    moves = [kwargs for name, kwargs in client.calls
             if name == 'post_comment' and kwargs['first_line'] == 'wf:move']
    assert len(moves) == 1 and moves[0]['body'] == '清單 → 需求/待辦'
    assert read_block(client.rows[10]['body'], 'wf-card')['card_id'] == 'WF-027'


def test_new_card_writes_no_move_comment(open_root, catalog):
    """FINAL-6 負控：同一路徑但來源是清單項（新建卡）⇒ 一則 wf:move 都沒有。"""
    from .test_open_verb import intake
    row = issue(10, body='清單項散文\n' + block('wf-intake', intake()))
    client = E2EClient(catalog, [row])
    result = open_issue(10, client=client, root=open_root, catalog=catalog, emit=lambda line: None)
    assert result.rc == 0
    assert first_lines(client) == []
