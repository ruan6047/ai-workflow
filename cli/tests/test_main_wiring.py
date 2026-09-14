"""總入口接線：七動詞分派、未知動詞、設定不合法、repo 定位（本機 remote／GH_REPO／注入 client）、
全域旗標前綴迴圈、共用 context、`edit.run` 別名與不轉送 item_id。

消費 core/verbs.md §1 七列／§2、ADOPTION.md §2。
所有 GitHub 操作走 cli/tests/fakes.py 的替身；⛔ 不碰網路、⛔ 不跑 `gh`（本機 git 只讀 tmp 內合成 repo 與本 repo）。
"""
import inspect
import json

import pytest

from .fakes import FakeGhClient
from .test_compose_schema import ROOT, card, catalog
from .test_context_roots import project_root
from .test_write_flow import mutations, simulated
from wf.verbs import brief, edit, move, notes, review, snapshot
from wf.verbs import open as open_verb
from wf.verbs.main import DISPATCH, GLOBAL_FLAGS, VERBS, global_flags, main

BOOTSTRAP_READS = ['repository', 'capability', 'bind_context']  # 本 repo 有 Project 設定 ⇒ 三筆

MODULES = {'open': open_verb, 'move': move, 'edit': edit, 'notes': notes,
           'brief': brief, 'review': review, 'snapshot': snapshot}
ARGS = {'open': ['10'], 'move': ['WF-001', '--to', '待辦'], 'edit': ['WF-001', '--set', 'feature="a"'],
        'notes': ['WF-001'], 'brief': ['WF-001', '--for', 'executor'],
        'review': ['WF-001', '--file', 'r.json', '--role', 'executor'], 'snapshot': ['--out', 'o']}


@pytest.fixture
def root():
    """規則檔的唯一居所＝repo 本身（唯讀）；本檔只讀規則，輸出一律寫 tmp。"""
    return ROOT


@pytest.fixture
def unadopted_root(tmp_path):
    """規則齊全但尚未接上框架的 repo：只連規則目錄、⛔ 不連 `.wf`。
    本 repo 自身已有 `.wf/modules.json`（它就是第一個採用專案），故⛔ 不能拿 ROOT 當「無 Project 設定」的樣本。"""
    target = tmp_path / 'unadopted'
    target.mkdir()
    for name in ('core', 'roles', 'stages', 'modules'):
        (target / name).symlink_to(ROOT / name, target_is_directory=True)
    return target


def recorder(monkeypatch, module):
    calls = []
    monkeypatch.setattr(module, 'run', lambda argv, **kwargs: calls.append((argv, kwargs)) or 7)
    return calls


def test_seven_verbs_are_the_dispatch_keys():
    """驗收 1：VERBS 仍是固定七值，且每個鍵指到自己的模組（⛔ 不是同一個佔位）。"""
    assert VERBS == ('open', 'move', 'edit', 'notes', 'brief', 'review', 'snapshot')
    assert DISPATCH == MODULES
    assert [module.__name__ for module in DISPATCH.values()] == [
        f'wf.verbs.{name}' for name in VERBS]
    assert all(callable(getattr(module, 'run')) for module in DISPATCH.values())


@pytest.mark.parametrize('verb', VERBS)
def test_each_verb_reaches_its_own_module(verb, root, monkeypatch):
    """驗收 1（每個一案）：main 把 argv[1:]、client、root、catalog、context 交給該動詞的 run，並回傳其 rc。
    負控＝同時錄下其餘六個模組的 run，證明它們一次都沒被呼叫；client 只有 bootstrap 的三筆呼叫。"""
    calls = {name: recorder(monkeypatch, module) for name, module in MODULES.items()}
    client = FakeGhClient()
    assert main([verb, *ARGS[verb]], client=client, root=root) == 7
    argv, kwargs = calls[verb][0]
    assert argv == ARGS[verb]
    assert kwargs['client'] is client and kwargs['root'] == root.resolve()
    assert kwargs['catalog'].by_label('json wf-enums')
    assert kwargs['context'] is client.context and kwargs['context'].static_identity_verified is True
    assert {name: len(rows) for name, rows in calls.items() if rows} == {verb: 1}
    assert [name for name, _ in client.calls] == BOOTSTRAP_READS


def test_all_seven_verbs_receive_the_same_context_object(root, monkeypatch):
    """同一 client 連跑七動詞：每次派到的 context 就是 client 綁定的那一個，且 repository 來自本 repo 的
    origin remote（本機 git 事實 → stable ID 經替身解析）；catalog 與 rules identity 一致。"""
    calls = {name: recorder(monkeypatch, module) for name, module in MODULES.items()}
    seen = []
    for verb in VERBS:
        client = FakeGhClient()
        assert main([verb, *ARGS[verb]], client=client, root=root) == 7
        _, kwargs = calls[verb][-1]
        seen.append(kwargs['context'])
        assert kwargs['context'] is client.context
    assert {ctx.repository.name_with_owner for ctx in seen} == {'ruan6047/ai-workflow'}
    assert {ctx.repository.provenance.kind for ctx in seen} == {'git'}
    assert {ctx.rules.identity for ctx in seen} == {str(root.resolve())}
    assert {ctx.project.root.canonical for ctx in seen} == {str(root.resolve())}
    assert all(ctx.git is not None and ctx.git.top_level for ctx in seen)
    print('CONTEXT_REPOSITORY', seen[0].repository)


def test_real_verbs_are_reached_without_the_recorders(unadopted_root, tmp_path, capsys):
    """驗收 1 的負控：不打樁時 rc 由真動詞決定——這裡 snapshot 真的產出檔案。"""
    client = FakeGhClient(issues=[], project={'id': 'P', 'fields': [], 'items': []})
    assert main(['snapshot', '--out', str(tmp_path / 'out')], client=client, root=unadopted_root) == 0
    assert (tmp_path / 'out/snapshot.json').is_file()
    assert json.loads((tmp_path / 'out/snapshot.json').read_text(encoding='utf-8'))['cards'] == []
    assert '無 Project 設定' in capsys.readouterr().out


@pytest.mark.parametrize('argv', [[], ['nope'], ['closeout'], ['Open'], ['--rules-root'], ['--bogus', 'x', 'notes'],
                                  ['--rules-root', 'x'], ['notes', '--rules-root', 'x'], ['snapshot', '--remote=o']])
def test_unknown_verb_prints_usage_rc2(argv, capsys, root, monkeypatch):
    """驗收 1：未知動詞、無參數、全域旗標形狀不對或寫在動詞之後＝印用法、rc=2、⛔ 不建 client、⛔ 不讀設定、
    ⛔ 不呼叫動詞（動詞 parse_args 從未看到全域旗標）。"""
    calls = {name: recorder(monkeypatch, module) for name, module in MODULES.items()}
    assert main(argv, root=root) == 2
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err.strip() == 'wf <open|move|edit|notes|brief|review|snapshot> …'
    assert not any(calls.values())


def test_global_flags_prefix_loop_shapes():
    """三旗標 `--x v` 與 `--x=v` 都收、重複以後者為準、只認動詞之前；其餘 argv 逐字留給動詞。"""
    assert GLOBAL_FLAGS == ('--project-root', '--rules-root', '--remote')
    assert global_flags(['--rules-root', 'R', '--remote=up', 'notes', 'WF-001', '--stage', '執行']) == (
        {'--rules-root': 'R', '--remote': 'up'}, ['notes', 'WF-001', '--stage', '執行'])
    assert global_flags(['--remote', 'a', '--remote', 'b', 'snapshot']) == ({'--remote': 'b'}, ['snapshot'])
    assert global_flags(['snapshot', '--out', 'o']) == ({}, ['snapshot', '--out', 'o'])
    assert global_flags(['--project-root']) is None and global_flags(['--nope', 'x', 'notes']) is None
    assert global_flags(['notes', 'WF-001', '--remote', 'x']) is None


def test_broken_project_config_prints_one_line_and_writes_nothing(tmp_path, capsys):
    """驗收 1：`.wf/modules.json` 壞 → 一行 rc≠0、0 則留言、⛔ 不貼 wf:reject。"""
    (tmp_path / '.wf').mkdir()
    (tmp_path / '.wf/modules.json').write_text('{壞', encoding='utf-8')
    client = FakeGhClient()
    rc = main(['notes', 'WF-001'], client=client, root=tmp_path)
    captured = capsys.readouterr()
    assert rc != 0 and captured.out == ''
    assert len(captured.err.strip().splitlines()) == 1
    assert captured.err.startswith('.wf/modules.json 不合法：')
    assert client.calls == []


def test_broken_project_config_negative_control(root, monkeypatch, capsys):
    """負控：同一路徑換成合法設定，那行就不再出現、動詞照樣被呼叫。"""
    calls = recorder(monkeypatch, notes)
    assert main(['notes', 'WF-001'], client=FakeGhClient(), root=root) == 7
    assert '不合法' not in capsys.readouterr().err and len(calls) == 1


@pytest.mark.parametrize('url,slug', [
    ('https://github.com/owner/name.git', 'owner/name'),
    ('https://github.com/owner/name', 'owner/name'),
    ('git@github.com:owner/name.git', 'owner/name'),
    ('ssh://git@github.com/owner/name/', 'owner/name')])
def test_repository_candidate_from_local_remote(tmp_path, url, slug, monkeypatch):
    """repo 定位：本機 git 事實（唯一 remote，名稱不必是 origin）→ 經替身以 stable ID 解析；
    GH_REPO 存在時只作核對（同 ID 即過），⛔ 不改變被選 remote。"""
    calls = recorder(monkeypatch, notes)
    root = project_root(tmp_path, remote=None)
    from .test_context_roots import git, git_env
    git(root, 'remote', 'add', 'mirror', url, env=git_env(tmp_path))
    for part in ('core', 'roles', 'stages', 'modules'):
        (root / part).symlink_to(ROOT / part, target_is_directory=True)
    client = FakeGhClient()
    assert main(['notes', 'WF-001'], client=client, root=root, env={}) == 7
    assert ('repository', {'slug': slug}) in client.calls and calls
    assert client.context.repository.provenance.detail == 'sole remote mirror'
    client = FakeGhClient()
    assert main(['notes', 'WF-001'], client=client, root=root, env={'GH_REPO': 'env/asserted'}) == 7
    assert [kw['slug'] for name, kw in client.calls if name == 'repository'] == [slug, 'env/asserted']
    assert client.context.repository.name_with_owner == slug


def test_missing_repo_prints_and_returns_nonzero(unadopted_root, capsys, monkeypatch):
    """repo 取不到（無 .git、無 GH_REPO、無注入 client）＝印一行 rc≠0，且 ⛔ 不建 GhClient、⛔ 不呼叫動詞。"""
    calls = recorder(monkeypatch, notes)
    assert main(['notes', 'WF-001'], root=unadopted_root, env={}) != 0
    assert calls == [] and '未能取得 repo' in capsys.readouterr().err


def test_edit_run_is_the_unified_entry_and_main_is_an_alias():
    """驗收 2：`edit.run` 存在、`main` 為別名，簽名與其餘動詞的 run 對齊；七個 run 都收 context（缺省 None）。"""
    assert edit.run is edit.main
    shared = ('argv', 'client', 'root', 'catalog')
    assert tuple(inspect.signature(edit.run).parameters)[:4] == shared
    for module in (open_verb, notes, brief, review, move):
        assert tuple(inspect.signature(module.run).parameters)[:4] == shared
    assert tuple(inspect.signature(snapshot.run).parameters) == shared + ('context',)
    for module in DISPATCH.values():
        assert inspect.signature(module.run).parameters['context'].default is None


def assert_no_item_id(kwargs):
    """不變式：edit ⛔ 不轉送 item_id 給 write_card。"""
    assert 'item_id' not in kwargs, kwargs


def test_edit_never_forwards_item_id_to_write_card(card, catalog, monkeypatch):
    """驗收 4：斷言呼叫參數本身（旗標那層不可證偽）；負控＝帶上 item_id 時檢查必 FAIL。"""
    from wf.verbs import edit as edit_module
    from wf.verbs._write import write_card as real
    seen = []

    def spy(card_json, projection_values=None, **kwargs):
        seen.append(kwargs)
        return real(card_json, projection_values, **kwargs)

    monkeypatch.setattr(edit_module, 'write_card', spy)
    fake = simulated(card, catalog)
    result = edit_module.edit(1, ['feature="改過"'], client=fake, catalog=catalog)
    assert result.rc == 0 and mutations(fake, 'update_card_body')
    assert len(seen) == 1
    assert_no_item_id(seen[0])
    assert seen[0]['write_projection'] is False
    assert seen[0]['number'] == 1
    with pytest.raises(AssertionError):
        assert_no_item_id(seen[0] | {'item_id': 'ITEM'})
    print('負控：帶 item_id 的同一組參數會讓不變式 FAIL；本次實際參數＝',
          json.dumps(sorted(seen[0]), ensure_ascii=False))


def test_edit_writes_no_projection_field(card, catalog):
    """驗收 4 的行為面：edit 一路走完不碰任何 Project 欄寫入或讀取。"""
    fake = simulated(card, catalog)
    result = edit.edit(1, ['feature="改過二"'], client=fake, catalog=catalog)
    assert result.rc == 0
    assert [name for name, _ in fake.calls if 'project' in name] == []
