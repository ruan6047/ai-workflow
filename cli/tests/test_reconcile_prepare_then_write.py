"""收 astra 複驗 FINAL3-1（共用對帳先寫後驗）。

消費 core/verbs.md §2「檢查先於首次遠端寫入：先純計算並驗證新內容，再開始第一次寫」、
同節「下一次動詞先對帳……不等＝以卡面 JSON 重寫該欄」與 D3、
core/card-schema.md §5 `json wf-projection`（欄名↔卡面鍵）、core/enums.md `tiers`。
反例逐字取自 astra 複驗表：卡面 stage／state 相對板上已漂移、板上第三欄「級別」缺 T1 選項。
每條各一正向一負控（roles/conduct-common.md §1）；GitHub 全由既有替身接住，⛔ 不碰網路。
"""
from pathlib import Path
import socket
import subprocess

import pytest

from wf.compose.blocks import load_blocks, projection
from wf.compose.validate import _equal
from wf.verbs import _write
from wf.verbs import edit as edit_module
from wf.verbs.edit import edit
from wf.verbs.move import move

from .test_brief_sections import card, make_root, WRITES
from .test_card_gate_and_projection import RULES, board_client, first_lines, rejects, run_verb

# 板上：階段／狀態與卡面（執行／進行中）不同，級別 T3 與卡面 T1 不同 ⇒ 三欄都要重寫。
DRIFTED = {'階段': {'name': '規劃'}, '狀態': {'name': '待辦'}, '級別': {'name': 'T3'},
           'owner': None, '卡ID': {'text': 'WF-001'}}
VERBS = ['review', 'notes', 'brief', 'edit', 'move']


ALLOWED_GIT = {'rev-parse', 'log', 'diff'}  # review 的本機唯讀取源；⛔ 不含任何寫入型子指令


def git_subcommand(argv):
    """`git [全域旗標…] <子指令>` 的子指令；`-C` 另吃一個值。不是 git ⇒ None。"""
    if not argv or Path(argv[0]).name != 'git':
        return None
    rest = list(argv[1:])
    while rest:
        token = rest.pop(0)
        if token == '-C' and rest:
            rest.pop(0)
        elif not token.startswith('-'):
            return token
    return None


def strict_offline(monkeypatch, token):
    """嚴格放行（需求方 2026-09-14 裁定）：只有本機 git 的 rev-parse／log／diff 可跑——
    `review` 的本機分支頭比對與 git 附錄走 gh/localrev.py 這三個唯讀子指令（CLI-001）。
    字串型 shell command、gh／curl／wget／ssh、其他 git 子指令與任何其他子程序一律擋；
    socket 連線一律擋（roles/conduct-common.md §1）。"""
    real = subprocess.run

    def denied(*args, **kwargs):
        raise AssertionError(token)

    def guarded(argv, *args, **kwargs):
        if isinstance(argv, (str, bytes)) or git_subcommand([str(item) for item in argv]) not in ALLOWED_GIT:
            denied()
        return real(argv, *args, **kwargs)

    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(subprocess, 'run', guarded)


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(RULES)


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    strict_offline(monkeypatch, 'RECONCILE_NETWORK_DENIED')
    with pytest.raises(AssertionError, match='RECONCILE_NETWORK_DENIED'):
        subprocess.run(['gh', 'api', 'negative-control'])
    with pytest.raises(AssertionError, match='RECONCILE_NETWORK_DENIED'):
        subprocess.run('git rev-parse HEAD')          # 字串型 shell command
    with pytest.raises(AssertionError, match='RECONCILE_NETWORK_DENIED'):
        subprocess.run(['git', 'push', 'origin'])     # 寫入型 git 子指令
    with pytest.raises(AssertionError, match='RECONCILE_NETWORK_DENIED'):
        subprocess.run(['python', '-c', 'pass'])      # 其他子程序


def drifted_client(catalog, *, tier_options=True, state='進行中'):
    """卡面 T1／板上 T3 且階段、狀態同時漂移；tier_options=False ⇒ 板上級別缺 T1 選項。
    state 供 move 用：派工邊要求卡面停在 待辦（執行/待辦 → 執行/進行中）。"""
    client = board_client(catalog, card(tier='T1', state=state, branch='wf/WF-001',
                                        stage_plan=['需求', '執行', '審核', '結案'],
                                        source_sha='b' * 40), dict(DRIFTED))
    if not tier_options:
        client.options['級別'] = [o for o in client.options['級別'] if o['name'] != 'T1']
    return client


def run_one(verb, tmp_path, root, client, catalog):
    lines = []
    if verb == 'move':  # 派工邊 執行/待辦 → 執行/進行中；新卡欄同樣要先解析
        return move(10, '執行/進行中', client=client, root=root, catalog=catalog,
                    actor='executor:new', emit=lines.append), lines
    if verb != 'edit':
        return run_verb(verb, tmp_path, root, client)
    return edit(10, ['feature="改過"'], client=client, catalog=catalog, project_owner='fake',
                project_number=1, emit=lines.append), lines


def legacy_reconcile(card_json, *, client, catalog, project_owner, project_number, item_id):
    """負控：舊版的逐欄邊算邊寫（＝astra FINAL3-1 的反例來源）＝prepare 完一欄就寫一欄。"""
    project = client.project(project_owner, project_number, projection(catalog))
    actual = _write.projection_values(project, item_id)
    changed = []
    for name, value in _write.projected(card_json, catalog).items():
        if not _equal(actual.get(name), value):
            client.write_project_field(client.prepare_project_field(project, item_id, name, value))
            changed.append(name)
    return changed


# ── FINAL3-1 正向：欄算不出 ⇒ 零業務寫入、單一 D3 拒收 ────────────────────────

@pytest.mark.parametrize('verb', VERBS)
def test_unresolvable_projection_column_writes_nothing_before_the_rejection(tmp_path, catalog, verb):
    """正向：板上級別缺 T1 選項 ⇒ 四支動詞 rc≠0、寫入序列只有 ['post_comment']、
    恰一則 wf:reject，且板上三欄（含已漂移的階段／狀態）一格都沒被改。"""
    root = make_root(tmp_path)
    client = drifted_client(catalog, tier_options=False,
                            state='待辦' if verb == 'move' else '進行中')
    result, _ = run_one(verb, tmp_path, root, client, catalog)
    writes = [name for name, _ in client.calls if name in WRITES]
    assert result.rc != 0, result
    assert writes == ['post_comment'], writes
    assert first_lines(client) == ['wf:reject']
    assert rejects(client)[0]['body'].startswith('拒收・D3・')
    assert '級別' in rejects(client)[0]['body'], rejects(client)[0]['body']  # 四支都要指出哪一欄算不出
    assert client.board['items'][0]['fieldValues'] == DRIFTED
    print('FINAL3-1', verb, writes, rejects(client)[0]['body'])


@pytest.mark.parametrize('verb', ['review', 'notes', 'brief'])
def test_writing_each_column_as_it_is_resolved_breaks_the_same_three_cases(tmp_path, catalog, verb,
                                                                          monkeypatch):
    """負控：把「先算」拿掉（換回逐欄邊算邊寫）⇒ 同一輸入在拒收前就寫了板，
    重現 ['write_project_field', 'write_project_field', …]，上一條的斷言必 FAIL。"""
    monkeypatch.setattr(_write, 'reconcile', legacy_reconcile)
    root = make_root(tmp_path)
    client = drifted_client(catalog, tier_options=False,
                            state='待辦' if verb == 'move' else '進行中')
    result, _ = run_one(verb, tmp_path, root, client, catalog)
    writes = [name for name, _ in client.calls if name in WRITES]
    assert result.rc != 0, result
    assert writes[:2] == ['write_project_field', 'write_project_field'], writes
    assert writes != ['post_comment']
    assert client.board['items'][0]['fieldValues']['階段'] == {'name': '執行'}
    print('FINAL3-1 負控', verb, writes)


# ── 正控：欄都解析得出時，對帳照舊重寫並印 ──────────────────────────────────

@pytest.mark.parametrize('verb', VERBS)
def test_resolvable_columns_still_reconcile_the_whole_drift(tmp_path, catalog, verb):
    """正控：同一組漂移、級別選項齊全 ⇒ rc=0、印「重寫投影欄：階段、狀態、級別」、板上修好，
    證明上面兩條擋下的是「算不出」，不是把對帳整個關掉。"""
    root = make_root(tmp_path)
    client = drifted_client(catalog, state='待辦' if verb == 'move' else '進行中')
    result, lines = run_one(verb, tmp_path, root, client, catalog)
    assert result.rc == 0, result.reason
    expected = '重寫投影欄：階段、級別' if verb == 'move' else '重寫投影欄：階段、狀態、級別'
    assert expected in lines, lines  # move 的卡面停在 待辦＝板上值，狀態欄本來就不漂移, lines
    assert client.board['items'][0]['fieldValues']['級別'] == {'name': 'T1'}
    assert client.board['items'][0]['fieldValues']['階段'] == {'name': '執行'}
    assert client.board['items'][0]['fieldValues']['狀態'] == {'name': '進行中'}


def edit_without_the_field_name_wrapper():
    """負控用：把 edit 新卡欄位解析的欄名包裝拿掉（＝astra 複驗的被審版本），回傳該版 edit。"""
    source = Path(edit_module.__file__).read_text(encoding='utf-8')
    old = """            try:  # 算不出的欄，拒收本文要指得出是哪一欄（形狀同 _write.reconcile）
                client.prepare_project_field(board, item_id, name, field)
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f'{name} 投影欄無法解析：{exc}') from exc
"""
    bare = '            client.prepare_project_field(board, item_id, name, field)\n'
    assert source.count(old) == 1
    namespace = {'__name__': 'wf.verbs.edit_without_wrapper', '__file__': edit_module.__file__}
    exec(compile(source.replace(old, bare), edit_module.__file__, 'exec'), namespace)
    return namespace['edit']


def test_dropping_the_field_name_wrapper_loses_the_column_in_the_edit_rejection(tmp_path, catalog):
    """FINAL3-1 負控：同一反例走沒有包裝的 edit ⇒ 本文回到不帶欄名的裸例外，
    上一條對 edit 的『本文含級別』斷言必 FAIL。"""
    client = drifted_client(catalog, tier_options=False)
    result = edit_without_the_field_name_wrapper()(
        10, ['feature="改過"'], client=client, catalog=catalog, project_owner='fake',
        project_number=1, emit=lambda line: None)
    body = rejects(client)[0]['body']
    assert result.rc != 0
    assert body.startswith('拒收・D3・') and '級別' not in body, body
    print('FINAL3-1 edit 負控', body)
