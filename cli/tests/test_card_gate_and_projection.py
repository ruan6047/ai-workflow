"""讓 CLI 追上現行規則（astra 總檢查 FINAL-1～6）。

消費 core/verbs.md §1（open／edit／notes／brief／review 列）／§2（D3、對帳、snapshot 例外）／§3
第 1 條、core/card-schema.md §1／§5 `json wf-projection`、core/enums.md `tiers`。
每條各一正向與一負控（roles/conduct-common.md §1：先證明比對真的會響）；
所有 GitHub 操作由 cli/tests 既有替身接住，⛔ 不碰網路。
"""
from copy import deepcopy
import json
from pathlib import Path
import socket
import subprocess

import pytest

from wf.compose.blocks import load_blocks, projection
from wf.compose.schema import compose_schema
from wf.compose.validate import validate
from wf.gh.client import GhError
from wf.gh.writes import WriteMixin, read_block
from wf.verbs import _common, _write
from wf.verbs.brief import brief, _previous_findings
from wf.verbs.edit import edit
from wf.verbs.notes import notes
from wf.verbs.open import open_issue
from wf.verbs.review import review
from wf.verbs.snapshot import snapshot

from .test_brief_sections import block, card, make_client, make_root, WRITES
from .test_end_to_end import E2EClient
from .test_open_verb import VARIANTS, expected_card, item, issue, shape_variants

RULES = Path(__file__).resolve().parents[2]
BOARD = {'階段': {'name': '執行'}, '狀態': {'name': '進行中'}, '級別': {'name': 'T3'},
         'owner': None, '卡ID': {'text': 'WF-001'}}


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(RULES)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('CARD_GATE_NETWORK_DENIED')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(subprocess, 'run', forbidden)
    with pytest.raises(AssertionError, match='CARD_GATE_NETWORK_DENIED'):
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


LOCAL = ('notes', 'brief')  # WF-003：讀側 D3 ＝本機硬擋、遠端零寫入；review 的拒收逐字不變


def hard_blocks(lines):
    """本機硬擋行（core/verbs.md §2 `硬擋・<D 編號>・<原因>`）。"""
    return [line for line in lines if line.startswith('硬擋・')]


def assert_local_hard_block(client, result, lines, code='D3'):
    """讀側 D3 的三件事，斷言序固定：① 寫入呼叫集合為空（⛔ 不先取 writes[0]——零寫入下必
    IndexError，會把修好誤報成探針崩潰）② rc=1 ③ 本機恰一行硬擋，原因逐字等於 WriteResult.reason。"""
    assert [name for name, _ in client.calls if name in WRITES] == []
    assert result.rc == 1 and result.reason
    assert hard_blocks(lines) == [f'硬擋・{code}・{result.reason}']


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
    """FINAL-1 正向：卡面多一個 `unexpected` 鍵 ⇒ rc≠0、該卡動詞停。

    WF-003：notes／brief 的讀側 D3 改為本機硬擋＋遠端零寫入；review 逐字不變＝恰一則 wf:reject。
    """
    root = make_root(tmp_path, project=False)
    client = make_client(card(unexpected='非法鍵', branch='wf/WF-001', source_sha='b' * 40))
    result, lines = run_verb(verb, tmp_path, root, client)
    if verb in LOCAL:
        assert_local_hard_block(client, result, lines)
        assert 'unexpected' in result.reason
        print('FINAL-1', verb, hard_blocks(lines)[0])
        return
    assert result.rc != 0
    writes = [name for name, _ in client.calls if name in WRITES]
    assert writes == ['post_comment'], writes
    assert first_lines(client) == ['wf:reject']
    assert rejects(client)[0]['body'].startswith('拒收・D3・')
    assert 'unexpected' in rejects(client)[0]['body']
    print('FINAL-1', verb, rejects(client)[0]['body'])


@pytest.mark.parametrize('verb', ['notes', 'brief', 'review'])
def test_removing_the_card_gate_lets_the_illegal_key_through(tmp_path, verb, monkeypatch):
    """FINAL-1 負控：把兩道驗卡面（上界預驗與 check_card）都換成不判的樁 ⇒ 同一張卡 rc=0。

    WF-004 把非法鍵的攔截點前移到 enabled_modules 第一行的 prevalidate_card，
    只樁 check_card 已不足以讓非法鍵穿過；負控語義隨之收窄為「拿掉兩道就穿過」。
    """
    monkeypatch.setattr(_common, 'prevalidate_card', lambda *a, **k: None)
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
    result = edit(10, ['tier="T4"'], client=client, catalog=catalog,
                  project_owner='fake', project_number=1)
    assert result.rc == 0 and result.card['tier'] == 'T4'
    assert client.board['items'][0]['fieldValues']['級別'] == {'name': 'T4'}
    # 先算後寫之後 prepare_project_field 另含新舊卡的試算，故以實際寫入斷言五欄。
    written = [prepared[2]['fieldId'] for name, prepared in client.calls
               if name == 'write_project_field']
    assert written == list(projection(catalog))


def test_edit_leaves_the_board_alone_for_non_projection_keys(tmp_path, catalog):
    """FINAL-2a 負控：同一條路徑改非投影鍵 `feature` ⇒ 零投影欄寫入，板上級別不動。"""
    client = board_client(catalog, card(tier='T3'))
    result = edit(10, ['feature="改過"'], client=client, catalog=catalog,
                  project_owner='fake', project_number=1)
    assert result.rc == 0
    # 試算（prepare_project_field）是讀不是寫；此列要的是零投影欄「寫入」。
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
        result = edit(10, ['feature="改過"'], client=client, catalog=catalog,
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
    result = edit(10, [f'tier="{target}"'], client=client, catalog=catalog,
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


# ── WF-004：啟用判定前的上界預驗（core/card-schema.md §1 合成順序）────────────────

def victim_card(catalog, **changes):
    """notes／brief／review 三個動詞都能跑到底的合法卡；research 由 stage_plan 啟用。"""
    research, = (b.data for b in catalog.by_label('yaml wf-module') if b.data['name'] == 'research')
    enums, = catalog.by_label('json wf-enums')
    stage = research['enable_if']['stage']
    plan = [s for s in enums.data['stages']['enum'] if s in ('需求', stage, '規劃', '執行', '審核', '結案')]
    return card(stage_plan=plan, stage=stage, state=enums.data['states_core']['enum'][0],
                branch='wf/WF-001', source_sha='b' * 40) | changes


@pytest.mark.parametrize('verb', ['notes', 'brief', 'review'])
@pytest.mark.parametrize('variant', VARIANTS)
def test_prevalidation_precedes_enablement_for_every_victim_verb(tmp_path, catalog, monkeypatch,
                                                                 verb, variant):
    """8 敵意值 × 3 個受害動詞：上界預驗先擋 ⇒ rc=1、理由是 schema path，且 is_enabled 一次都
    沒被呼叫（A2）。留痕處置依動詞分：WF-003 後 notes／brief 是本機硬擋＋遠端零寫入，
    review 逐字不變＝恰一則 wf:reject 且首次留言前零寫入。

    基線行為＝stage_plan 為 None／5 時 is_enabled 拋未攔截的 TypeError（見負控）。
    """
    calls = []
    monkeypatch.setattr(_common, 'is_enabled',
                        lambda *a, **k: calls.append(a) or pytest.fail('⛔ 不得做啟用判定'))
    monkeypatch.setattr('wf.verbs.brief.is_enabled',
                        lambda *a, **k: calls.append(a) or pytest.fail('⛔ 不得做啟用判定'))
    changes, pointer = shape_variants(catalog)[variant]
    root = make_root(tmp_path, project=False)
    client = make_client(victim_card(catalog, **changes))
    result, lines = run_verb(verb, tmp_path, root, client)
    assert result.rc == 1
    assert calls == []
    if verb in LOCAL:
        assert_local_hard_block(client, result, lines)
    else:
        assert [name for name, _ in client.calls if name in WRITES] == ['post_comment']
        assert first_lines(client) == ['wf:reject']
        assert rejects(client)[0]['body'] == '拒收・D3・' + result.reason
    assert result.reason.startswith('/'), result.reason
    assert pointer in result.reason, result.reason
    print('WF-004', verb, variant, result.reason)


@pytest.mark.parametrize('verb', ['notes', 'brief', 'review'])
def test_prevalidation_stub_restores_the_typeerror(tmp_path, catalog, monkeypatch, verb):
    """負控：把 prevalidate_card 換成不判的樁 ⇒ stage_plan=5 重現基線的未攔截 TypeError。

    這道負控會響，才證明上界預驗不是零資訊的裝飾（F-規劃-03）。
    """
    monkeypatch.setattr(_common, 'prevalidate_card', lambda *a, **k: None)
    root = make_root(tmp_path, project=False)
    client = make_client(victim_card(catalog, stage_plan=5))
    with pytest.raises(TypeError, match="argument of type 'int' is not iterable"):
        run_verb(verb, tmp_path, root, client)
    print('WF-004 負控', verb, '樁掉 prevalidate_card ⇒ TypeError 重現')


@pytest.mark.parametrize('verb', ['notes', 'brief', 'review'])
def test_legal_module_state_is_not_rejected_by_the_superset(tmp_path, catalog, verb):
    """A3：上界＝全部宣告模組的 states 聯集 ⇒ 合法的 research state 不被誤拒。

    負控＝以零模組基底當上界（compose_schema(catalog,'wf-card') 不帶模組名），
    同一張卡會得到 /state: 不符合 anyOf；見下一條。
    """
    research, = (b.data for b in catalog.by_label('yaml wf-module') if b.data['name'] == 'research')
    state, = research['adds']['enums']['states']
    root = make_root(tmp_path, project=False)
    client = make_client(victim_card(catalog, state=state))
    result, _ = run_verb(verb, tmp_path, root, client)
    assert result.rc == 0, result.reason
    assert 'wf:reject' not in first_lines(client)   # review 成功時本來就會貼 wf:return
    print('WF-004 合法模組 state', verb, 'rc', result.rc, first_lines(client))


def test_zero_module_base_would_reject_the_legal_module_state(catalog):
    """A3 負控：上界若改用零模組基底，上一條那張合法卡就會被誤拒 ⇒ 「上界」三個字有資訊量。"""
    research, = (b.data for b in catalog.by_label('yaml wf-module') if b.data['name'] == 'research')
    state, = research['adds']['enums']['states']
    legal = victim_card(catalog, state=state)
    base = [f'{e.path}: {e.message}' for e in validate(legal, compose_schema(catalog, 'wf-card'))]
    superset = [f'{e.path}: {e.message}' for e in
                validate(legal, compose_schema(catalog, 'wf-card', _common.declared_module_names(catalog)))]
    assert base and all(row.startswith('/state: ') for row in base), base
    assert superset == []
    print('WF-004 零模組基底誤拒：', base, '／上界：', superset)


@pytest.mark.parametrize('verb', ['notes', 'brief', 'review'])
def test_exact_schema_still_rejects_a_disabled_module_state(tmp_path, catalog, verb):
    """A4：精確後驗 ⛔ 不得被上界取代——research 未啟用而卡面帶它的 state ⇒ 仍 D3 /state。

    同時是負控 ③：先斷言這張卡【通得過】上界預驗，⇒ 擋下它的只能是精確後驗；
    省掉精確後驗這張卡就會被放行。
    """
    research, = (b.data for b in catalog.by_label('yaml wf-module') if b.data['name'] == 'research')
    state, = research['adds']['enums']['states']
    stage = research['enable_if']['stage']
    legal = victim_card(catalog, state=state)
    disabled = legal | {'stage_plan': [s for s in legal['stage_plan'] if s != stage], 'stage': '執行'}
    _common.prevalidate_card(disabled, catalog)  # 不拋＝上界放行；擋下來的是後面那道
    client = make_client(disabled)
    result, lines = run_verb(verb, tmp_path, make_root(tmp_path, project=False), client)
    assert result.rc == 1
    if verb in LOCAL:  # WF-003：check_card 失敗在讀側動詞＝本機硬擋、遠端零寫入
        assert_local_hard_block(client, result, lines)
    else:
        assert first_lines(client) == ['wf:reject']
    assert '/state' in result.reason, result.reason
    print('WF-004 停用模組 state', verb, result.reason)


@pytest.mark.parametrize('verb', ['notes', 'brief', 'review'])
def test_reject_reason_names_only_the_real_path(tmp_path, catalog, verb):
    """A6：拒收理由 ⛔ 不得指認沒壞的欄。

    research 已啟用、state 合法而 parent=5 ⇒ 本文含 /parent、⛔ 不含 /state。
    回空集合 sentinel 的做法會在這裡多印一條虛假的 /state（append-only 的永久留言）。
    """
    research, = (b.data for b in catalog.by_label('yaml wf-module') if b.data['name'] == 'research')
    state, = research['adds']['enums']['states']
    root = make_root(tmp_path, project=False)
    client = make_client(victim_card(catalog, state=state, parent=5))
    result, lines = run_verb(verb, tmp_path, root, client)
    assert result.rc == 1
    if verb in LOCAL:  # WF-003：本機硬擋行取代 wf:reject 本文，指認的欄一樣不得多也不得少
        assert_local_hard_block(client, result, lines)
        body = hard_blocks(lines)[0]
    else:
        body = rejects(client)[0]['body']
    assert '/parent' in body, body
    assert '/state' not in body, body
    print('WF-004 指認正確欄', verb, body)


# ── WF-003：notes／brief 的三個直接讀側 D3 出口窮舉（2 × 3 ＝ 6 格）與負控 ──────────

EXITS = ('block_object', 'prevalidate_card', 'check_card')


def exit_client(catalog, exit_name):
    """三個直接讀側出口各一張固定壞卡；⛔ 不與其他維度做笛卡兒乘積。

    block_object＝wf-card 區塊解析或型別失敗；prevalidate_card＝啟用判定前的上界預驗失敗
    （CardShapeError）；check_card＝上界放行而精確 schema 擋下（模組未啟用而帶它的 state）。
    """
    if exit_name == 'block_object':
        return make_client('前言\n```json wf-card\n{壞掉\n```\n')
    if exit_name == 'prevalidate_card':
        return make_client(victim_card(catalog, stage_plan=5))
    research, = (b.data for b in catalog.by_label('yaml wf-module') if b.data['name'] == 'research')
    state, = research['adds']['enums']['states']
    stage = research['enable_if']['stage']
    legal = victim_card(catalog, state=state)
    disabled = legal | {'stage_plan': [s for s in legal['stage_plan'] if s != stage], 'stage': '執行'}
    _common.prevalidate_card(disabled, catalog)  # 不拋＝上界放行 ⇒ 擋下它的只能是 check_card
    return make_client(disabled)


@pytest.mark.parametrize('verb', LOCAL)
@pytest.mark.parametrize('exit_name', EXITS)
def test_every_read_side_d3_exit_is_a_local_hard_block(tmp_path, catalog, verb, exit_name):
    """WF-003 窮舉：2 個動詞 × 3 個直接讀側出口 ＝ 6 格，逐格寫入呼叫集合為空、rc=1、
    本機恰一行 `硬擋・D3・<原因>`；少於 6 格即代表出口母體宣稱不成立。"""
    root = make_root(tmp_path, project=False)
    client = exit_client(catalog, exit_name)
    result, lines = run_verb(verb, tmp_path, root, client)
    assert_local_hard_block(client, result, lines)
    print('WF-003 出口', exit_name, verb, hard_blocks(lines)[0])


@pytest.mark.parametrize('verb', LOCAL)
@pytest.mark.parametrize('exit_name', EXITS)
def test_read_side_exit_negative_control_is_caught_by_the_zero_write_assertion(
        tmp_path, catalog, monkeypatch, verb, exit_name):
    """WF-003 負控（6 格）：把 notes／brief 的本機硬擋處置換回 `_write.reject` ⇒ 零寫入斷言
    必須響，且響的原因是替身確實記錄到 post_comment(first_line='wf:reject')，
    ⛔ 不是 TypeError／IndexError／AttributeError 之類在斷言之前拋出的例外。"""
    root = make_root(tmp_path, project=False)
    client = exit_client(catalog, exit_name)
    for module in LOCAL:
        monkeypatch.setattr(f'wf.verbs.{module}.blocked',
                            lambda report, code, reason: _write.reject(client, 10, code, reason,
                                                                       tuple(report)))
    result, lines = run_verb(verb, tmp_path, root, client)
    assert result.rc == 1
    assert [kwargs['body'] for kwargs in rejects(client)] == ['拒收・D3・' + result.reason]
    with pytest.raises(AssertionError) as caught:
        assert_local_hard_block(client, result, lines)
    assert 'post_comment' in str(caught.value), str(caught.value)
    assert hard_blocks(lines) == []
    print('WF-003 負控', exit_name, verb, rejects(client)[0]['body'])


# ── WF-003-R1.1-1：內層 notes 的讀側 D3 ⛔ 不得排在外層對帳（首次投影寫入）之後 ──────

def drifting_nested_client(catalog, good):
    """板上級別 T3、卡面 T1（有漂移，對帳一旦跑就會寫板，肉眼可辨）；issue() 第一次回合法卡、
    第二次（內層 notes 重讀）回壞 JSON。⛔ 不用 project=False——那正是遮蔽外層對帳寫入的做法。"""
    client = board_client(catalog, good)
    original, count = client.responses['issue'], [0]

    def issue(number):
        count[0] += 1
        row = original(number=number)
        return row if count[0] == 1 else dict(row, body='```json wf-card\n{壞掉\n```')

    client.responses['issue'] = issue
    return client, count


def test_nested_notes_d3_leaves_the_board_untouched_with_a_live_project(tmp_path, catalog):
    """WF-003-R1.1-1 正向：Project 真的在、且卡面 T1／板上 T3 有漂移，內層 notes 第二次讀卡
    落 D3 ⇒ 寫入呼叫集合為空、板上級別仍 T3（⛔ 無寫一半的中間態）、本機恰一行硬擋、rc=1。

    被審 SHA eca85c52472c7933ff95a2fd9bb9abd0c5026c31 在同一替身下是
    all_remote_writes=['write_project_field']、板上級別 T3→T1、
    emit=['重寫投影欄：級別','硬擋・D3・wf-card JSON 解析失敗']。
    """
    root = make_root(tmp_path)  # project=True：Project 設定在，對帳會真的走到
    client, count = drifting_nested_client(catalog, card(tier='T1'))
    before = deepcopy(client.board['items'][0]['fieldValues'])
    lines = []
    result = brief(10, target='executor', client=client, root=root, catalog=catalog,
                   emit=lines.append)
    assert [name for name, _ in client.calls if name in WRITES] == []
    assert client.board['items'][0]['fieldValues'] == before
    assert before['級別'] == {'name': 'T3'}          # 漂移真的存在，⛔ 不是無事可對帳
    assert count[0] == 2, count                      # 內層確實重讀了一次，⛔ 不是走不到
    assert result.rc == 1 and result.reason == 'wf-card JSON 解析失敗'
    assert hard_blocks(lines) == ['硬擋・D3・' + result.reason]
    assert lines == hard_blocks(lines)               # ⛔ 未印「重寫投影欄：」＝對帳沒跑過
    print('WF-003-R1.1-1', lines, [n for n, _ in client.calls if n in WRITES])


def test_the_same_drift_is_still_reconciled_when_the_nested_read_succeeds(tmp_path, catalog):
    """WF-003-R1.1-1 負控：同一張漂移卡、同一條路徑，內層第二次讀卡改成合法 ⇒ 對帳照樣把板上
    重寫成 T1 並印那一行、rc=0。證明上一條擋下的是順序，⛔ 不是把對帳整個關掉。"""
    root = make_root(tmp_path)
    client = board_client(catalog, card(tier='T1'))
    lines = []
    result = brief(10, target='executor', client=client, root=root, catalog=catalog,
                   emit=lines.append)
    assert result.rc == 0
    assert '重寫投影欄：級別' in lines, lines
    assert client.board['items'][0]['fieldValues']['級別'] == {'name': 'T1'}
    assert hard_blocks(lines) == []
