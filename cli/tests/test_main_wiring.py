"""總入口接線：七動詞分派、未知動詞、設定不合法、repo 定位、`edit.run` 別名與不轉送 item_id。

消費 core/verbs.md §1 七列／§2、ADOPTION.md §2；S15 驗收 1／2／4。
所有 GitHub 操作走 cli/tests/fakes.py 的替身；⛔ 不碰網路、⛔ 不跑 `gh`。
"""
import inspect
import json

import pytest

from .fakes import FakeGhClient
from .test_compose_schema import ROOT, card, catalog
from .test_write_flow import mutations, simulated
from wf.verbs import brief, edit, move, notes, review, snapshot
from wf.verbs import open as open_verb
from wf.verbs.main import DISPATCH, VERBS, main, repo_slug

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
    """驗收 1（每個一案）：main 把 argv[1:]、client、root、catalog 交給該動詞的 run，並回傳其 rc。
    負控＝同時錄下其餘六個模組的 run，證明它們一次都沒被呼叫。"""
    calls = {name: recorder(monkeypatch, module) for name, module in MODULES.items()}
    client = FakeGhClient()
    assert main([verb, *ARGS[verb]], client=client, root=root) == 7
    argv, kwargs = calls[verb][0]
    assert argv == ARGS[verb]
    assert kwargs['client'] is client and kwargs['root'] is root
    assert kwargs['catalog'].by_label('json wf-enums')
    assert {name: len(rows) for name, rows in calls.items() if rows} == {verb: 1}
    assert client.calls == []


def test_real_verbs_are_reached_without_the_recorders(unadopted_root, tmp_path, capsys):
    """驗收 1 的負控：不打樁時 rc 由真動詞決定——這裡 snapshot 真的產出檔案。"""
    client = FakeGhClient(issues=[], project={'id': 'P', 'fields': [], 'items': []})
    assert main(['snapshot', '--out', str(tmp_path / 'out')], client=client, root=unadopted_root) == 0
    assert (tmp_path / 'out/snapshot.json').is_file()
    assert json.loads((tmp_path / 'out/snapshot.json').read_text(encoding='utf-8'))['cards'] == []
    assert '無 Project 設定' in capsys.readouterr().out


@pytest.mark.parametrize('argv', [[], ['nope'], ['closeout'], ['Open']])
def test_unknown_verb_prints_usage_rc2(argv, capsys, root):
    """驗收 1：未知動詞或無參數＝印用法、rc=2、⛔ 不建 client、⛔ 不讀設定。"""
    assert main(argv, root=root) == 2
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err.strip() == 'wf <open|move|edit|notes|brief|review|snapshot> …'


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
def test_repo_slug_from_git_config(tmp_path, url, slug):
    """repo 定位：`.git/config` 的 origin URL；⛔ 不跑 git 子指令（verbs/ 不得 import subprocess）。"""
    (tmp_path / '.git').mkdir()
    (tmp_path / '.git/config').write_text(
        f'[core]\n\tbare = false\n[remote "origin"]\n\turl = {url}\n\tfetch = +refs/*\n'
        '[remote "upstream"]\n\turl = https://github.com/other/repo.git\n', encoding='utf-8')
    assert repo_slug(tmp_path, env={}) == slug
    assert repo_slug(tmp_path, env={'GH_REPO': 'env/wins'}) == 'env/wins'


def test_repo_slug_missing_sources(tmp_path):
    """負控：沒有 .git/config 也沒有 GH_REPO ⇒ None；只有 upstream 也是 None。"""
    assert repo_slug(tmp_path, env={}) is None
    (tmp_path / '.git').mkdir()
    (tmp_path / '.git/config').write_text('[remote "upstream"]\n\turl = git@github.com:o/n.git\n',
                                          encoding='utf-8')
    assert repo_slug(tmp_path, env={}) is None


def test_missing_repo_prints_and_returns_nonzero(tmp_path, capsys, monkeypatch):
    """repo 取不到＝印一行 rc≠0，且 ⛔ 不建 GhClient、⛔ 不呼叫動詞。"""
    calls = recorder(monkeypatch, notes)
    assert main(['notes', 'WF-001'], root=tmp_path, env={}) != 0
    assert calls == [] and '未能取得 repo' in capsys.readouterr().err


def test_edit_run_is_the_unified_entry_and_main_is_an_alias():
    """驗收 2：`edit.run` 存在、`main` 為別名，簽名與其餘動詞的 run 對齊。"""
    assert edit.run is edit.main
    shared = ('argv', 'client', 'root', 'catalog')
    assert tuple(inspect.signature(edit.run).parameters)[:4] == shared
    for module in (open_verb, notes, brief, review, move):
        assert tuple(inspect.signature(module.run).parameters)[:4] == shared
    assert tuple(inspect.signature(snapshot.run).parameters) == shared


def assert_no_item_id(kwargs):
    """S07 查核 R1.7-02 的不變式：edit ⛔ 不轉送 item_id 給 write_card。"""
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
    result = edit_module.edit(1, 'feature="改過"', client=fake, catalog=catalog)
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
    result = edit.edit(1, 'feature="改過二"', client=fake, catalog=catalog)
    assert result.rc == 0
    assert [name for name, _ in fake.calls if 'project' in name] == []
