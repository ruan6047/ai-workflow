"""WF-009 resolved target identity：消費 core/verbs.md §2、ADOPTION.md §2。
V7 remote precedence、V8 stable ID 合併、V9 GH_REPO assertion、V10 worktree／submodule 事實不折疊、
V11 default branch、V12 Project item stable ID、V13 permission 事實、V17 source_issue 與 duplicate。
本機 git fixture 全在 tmp_path 內以 `git init` 合成、全程無網路；GitHub 走 cli/tests/fakes.py 替身。
"""
import os
from pathlib import Path

import pytest

from wf.context import ContextError, Provenance, TargetIdentityError
from wf.gh.client import NotFound, PermissionDenied, TransportError
from wf.gh.localgit import LocalGitFacts, RemoteFact
from wf.gh.target import (PERMISSION_STATES, PermissionFact, RepositoryCandidate, RepositoryIdentity,
                          check_item_repository, item_ref, local_git_facts, permission_fact,
                          permission_facts, resolve_repository, select_remotes, slug_of)
from .test_context_roots import git, git_env

URLS = {'origin': 'https://github.com/consumer/right.git', 'fork': 'git@github.com:someone/fork.git',
        'upstream': 'ssh://git@github.com/parent/base/'}


def repo(tmp_path, name, remotes, *, upstream=None, env):
    """git init＋remote add＋一個空 commit；upstream＝把 main 的上游設到該 remote。"""
    root = tmp_path / name
    root.mkdir()
    git(root, 'init', '-q', '-b', 'main', env=env)
    git(root, 'commit', '-q', '--allow-empty', '-m', 'base', env=env)
    for remote in remotes:
        git(root, 'remote', 'add', remote, URLS[remote], env=env)
    if upstream is not None:
        git(root, 'update-ref', f'refs/remotes/{upstream}/main', 'HEAD', env=env)
        git(root, 'branch', '-q', '--set-upstream-to', f'{upstream}/main', env=env)
    return root


def lookup_by(ids):
    """注入 stable ID：slug → node_id；未列者以 slug 自身當 ID。"""
    def lookup(slug):
        return {'node_id': ids.get(slug, f'R_{slug}'), 'full_name': slug, 'default_branch': 'main'}
    return lookup


def candidates_of(facts, **selection):
    remotes, provenance = select_remotes(facts, **selection)
    return [RepositoryCandidate(slug_of(remote.fetch_url), Provenance(provenance.kind, f'{provenance.detail} {remote.name}'))
            for remote in remotes], provenance


# ── V7：①顯式 --remote ②設定鍵 ③upstream ④唯一 remote；多 remote 無 upstream 無設定＝fail-loud ──
def test_remote_precedence_explicit_then_config_then_upstream_then_sole(tmp_path, monkeypatch):
    env = git_env(tmp_path)
    monkeypatch.setattr(os, 'environ', env)
    sole = local_git_facts(repo(tmp_path, 'sole', ['upstream'], env=env))
    assert [r.name for r in sole.remotes] == ['upstream'] and not sole.remotes[0].is_upstream_of_current
    found, provenance = candidates_of(sole)
    assert [c.slug for c in found] == ['parent/base'] and provenance == Provenance('git', 'sole remote')
    with_upstream = local_git_facts(repo(tmp_path, 'up', ['origin', 'fork'], upstream='fork', env=env))
    found, provenance = candidates_of(with_upstream)
    assert [c.slug for c in found] == ['someone/fork'] and provenance == Provenance('git', 'current branch upstream')
    ambiguous = local_git_facts(repo(tmp_path, 'multi', ['origin', 'fork'], env=env))
    found, provenance = candidates_of(ambiguous)
    assert [c.slug for c in found] == ['someone/fork', 'consumer/right']  # 全部候選，序＝remote 名稱序
    assert provenance.detail == 'all remotes'
    with pytest.raises(TargetIdentityError, match='stable ID 不同'):
        resolve_repository(found, lookup=lookup_by({}))
    found, provenance = candidates_of(ambiguous, configured='fork')
    assert [c.slug for c in found] == ['someone/fork'] and provenance == Provenance('project_config', 'remote')
    found, provenance = candidates_of(ambiguous, explicit='origin', configured='fork')
    assert [c.slug for c in found] == ['consumer/right'] and provenance == Provenance('cli', '--remote')
    with pytest.raises(TargetIdentityError, match='remote 不存在：ghost'):
        select_remotes(ambiguous, explicit='ghost')
    assert select_remotes(None) == ((), Provenance('git', 'all remotes'))
    assert local_git_facts(tmp_path / 'not-a-repo') is None
    (tmp_path / 'not-a-repo').mkdir()
    assert local_git_facts(tmp_path / 'not-a-repo') is None
    print('V7 precedence', [(n, [r.name for r in f.remotes]) for n, f in
                           (('sole', sole), ('up', with_upstream), ('multi', ambiguous))])


# ── V8：URL 拼寫不同但 stable ID 相同 ⇒ 合併為一身分；ID 不同 ⇒ fail-loud 列出兩邊 ID 與 provenance ──
def test_candidates_merge_only_on_equal_stable_id():
    found = [RepositoryCandidate('Consumer/Right', Provenance('git', 'all remotes origin')),
             RepositoryCandidate('consumer/right', Provenance('git', 'all remotes mirror'))]
    identity, payload = resolve_repository(found, lookup=lookup_by({'Consumer/Right': 'R_same', 'consumer/right': 'R_same'}))
    assert identity == RepositoryIdentity('R_same', 'Consumer/Right', 'main',
                                          Provenance('git', 'all remotes origin（合併 Consumer/Right、consumer/right）'))
    assert payload['node_id'] == 'R_same'
    with pytest.raises(TargetIdentityError) as caught:
        resolve_repository(found, lookup=lookup_by({'Consumer/Right': 'R_one', 'consumer/right': 'R_two'}))
    message = str(caught.value)
    for needle in ('R_one', 'R_two', 'git:all remotes origin', 'git:all remotes mirror'):
        assert needle in message, message
    with pytest.raises(ContextError, match='未能取得 repo'):
        resolve_repository([], lookup=lookup_by({}))
    with pytest.raises(ContextError, match='無預設分支'):
        resolve_repository(found[:1], lookup=lambda slug: {'node_id': 'R', 'full_name': slug, 'default_branch': None})

    def failing(slug):
        raise TransportError('dial tcp')
    with pytest.raises(ContextError, match='未能解析 repository consumer/right'):
        resolve_repository(found[1:], lookup=failing)
    print('V8', message)


@pytest.mark.parametrize('url,slug', [
    ('https://github.com/a/b.git', 'a/b'), ('https://github.com/a/b', 'a/b'), ('git@github.com:a/b.git', 'a/b'),
    ('ssh://git@github.com/a/b/', 'a/b'), ('https://ghes.example.com/a/b.git', None), ('', None),
    ('https://github.com/a', None)])
def test_slug_only_for_github_dot_com(url, slug):
    assert slug_of(url) == slug


# ── V10：linked worktree 與 submodule：top-level／git-dir／common-dir 互不相同、皆絕對，全程本地 ──
def test_worktree_facts_are_not_collapsed(tmp_path, monkeypatch):
    env = git_env(tmp_path)
    monkeypatch.setattr(os, 'environ', env)
    source = tmp_path / 'source'
    source.mkdir()
    git(source, 'init', '-q', '-b', 'main', env=env)
    (source / 'README').write_text('x', encoding='utf-8')
    git(source, 'add', 'README', env=env)
    git(source, 'commit', '-q', '-m', 'init', env=env)
    bare = tmp_path / 'source.git'
    git(tmp_path, 'clone', '-q', '--bare', str(source), str(bare), env=env)
    consumer = tmp_path / 'consumer'
    consumer.mkdir()
    git(consumer, 'init', '-q', '-b', 'main', env=env)
    git(consumer, 'commit', '-q', '--allow-empty', '-m', 'base', env=env)
    git(consumer, '-c', 'protocol.file.allow=always', 'submodule', '-q', 'add', str(bare), 'sub', env=env)
    git(consumer, 'commit', '-q', '-m', 'add submodule', env=env)
    linked = tmp_path / 'linked-wt'
    git(consumer, 'worktree', 'add', '-q', str(linked), '-b', 'topic', env=env)
    monkeypatch.chdir(tmp_path)  # process cwd 與任何 repo 都不同：相對前綴一出現就會被抓到
    for root in (linked, consumer / 'sub', consumer):
        facts = local_git_facts(root)
        assert isinstance(facts, LocalGitFacts)
        triple = (facts.top_level, facts.git_dir, facts.git_common_dir)
        assert all(os.path.isabs(value) for value in triple), triple
        assert not any(value.startswith(('.', 'sub/')) for value in triple), triple
        assert Path(facts.top_level).resolve() == root.resolve()
        print('V10', root.name, triple)
    wt = local_git_facts(linked)
    assert len({wt.top_level, wt.git_dir, wt.git_common_dir}) == 3
    assert Path(wt.git_dir).resolve() == (consumer / '.git/worktrees' / linked.name).resolve()
    assert Path(wt.git_common_dir).resolve() == (consumer / '.git').resolve()
    assert wt.current_ref == 'refs/heads/topic' and len(wt.head_sha) == 40 and wt.remotes == ()
    sub = local_git_facts(consumer / 'sub')
    assert Path(sub.git_dir).resolve() == (consumer / '.git/modules/sub').resolve()
    assert sub.remotes == (RemoteFact('origin', str(bare), str(bare), True),)  # clone 的 main 追蹤 origin
    git(consumer, 'checkout', '-q', '--detach', env=env)
    assert local_git_facts(consumer).current_ref is None  # detached HEAD＝current ref 缺席，⛔ 不猜


# ── V13：permission 只產事實：七種輸入 → allowed／denied／unknown，四欄非空，state 在三值值域 ──
@pytest.mark.parametrize('value,state', [
    (True, 'allowed'), (False, 'denied'), (None, 'unknown'), ({'viewer_permission': 'WRITE'}, 'allowed'),
    (PermissionDenied('gh: Bad credentials (HTTP 401)'), 'unknown'),
    (PermissionDenied('gh: Forbidden (HTTP 403)'), 'denied'),
    (NotFound('gh: Not Found (HTTP 404)'), 'unknown'), (TransportError('dial tcp'), 'unknown')])
def test_permission_facts_are_pure_facts_with_four_fields(value, state):
    if isinstance(value, dict):  # repository permission hint（viewerPermission）走 permission_facts 的 payload 路徑
        fact, = permission_facts(value, None)
    else:
        fact = permission_fact('project', 'projectV2.viewerCanUpdate', value)
    assert isinstance(fact, PermissionFact) and fact.state == state
    assert all(getattr(fact, name) for name in ('subject', 'state', 'source', 'reason'))
    assert fact.state in PERMISSION_STATES
    both = permission_facts({'viewer_permission': 'READ'}, {'viewerCanUpdate': True})
    assert [(f.subject, f.state) for f in both] == [('repository', 'denied'), ('project', 'allowed')]
    assert [permission_facts({'viewer_permission': level}, None)[0].state
            for level in ('ADMIN', 'MAINTAIN', 'WRITE', 'TRIAGE', 'READ')] == ['allowed'] * 3 + ['denied'] * 2
    assert [f.state for f in permission_facts({}, {})] == ['unknown', 'unknown']
    print('V13', value if not isinstance(value, Exception) else type(value).__name__, '→', fact)


# ── V12（純函式面）：跨 repo Project 的 item，stable ID 等於 resolved 才過；owner 不同仍過；不同即 fail-loud ──
def test_project_item_repository_stable_id_pure_check():
    identity = RepositoryIdentity('R_right', 'consumer/right', 'main', Provenance('git', 'sole remote origin'))
    mine = item_ref({'id': 'I1', 'content': {'__typename': 'Issue', 'repository': {'id': 'R_right', 'nameWithOwner': 'other-owner/renamed'}}})
    check_item_repository(mine, identity)  # owner／名稱不同但 stable ID 相同＝同一 repo（改名或轉移）
    legacy = item_ref({'id': 'I2', 'content': {'__typename': 'Issue', 'repository': {'nameWithOwner': 'consumer/right'}}})
    check_item_repository(legacy, identity)  # 舊形狀無 id：退回 nameWithOwner 比對
    with pytest.raises(TargetIdentityError, match='I3 所屬 repository R_other ≠ resolved R_right'):
        check_item_repository(item_ref({'id': 'I3', 'content': {'__typename': 'Issue', 'repository': {'id': 'R_other', 'nameWithOwner': 'consumer/right'}}}), identity)
    with pytest.raises(TargetIdentityError, match='I4 所屬 repository x/y ≠ resolved consumer/right'):
        check_item_repository(item_ref({'id': 'I4', 'content': {'__typename': 'Issue', 'repository': {'nameWithOwner': 'x/y'}}}), identity)


# ═══════════════════ main() 層：V9／V11／V12／V13 執行期／V17 ═══════════════════
import json  # noqa: E402

from wf.compose.blocks import load_blocks  # noqa: E402
from wf.verbs.main import DISPATCH, main  # noqa: E402
from .fakes import FakeGhClient  # noqa: E402
from .test_context_roots import (SHA, mutation_calls, on_board_card, project_root, stateful,  # noqa: E402
                                 verb_args, workspace)
from .test_open_verb import issue, item  # noqa: E402

RULES = Path(__file__).resolve().parents[2]


def per_slug(slug):
    """注入 stable ID：每個 slug 各自一顆（拼寫不同＝不同 repo）。"""
    return {'node_id': f'R_{slug}', 'full_name': slug, 'default_branch': 'main', 'viewer_permission': 'ADMIN'}


def recorders(monkeypatch):
    calls = {}
    for name, module in DISPATCH.items():
        calls[name] = []
        monkeypatch.setattr(module, 'run', (lambda rows: lambda argv, **kwargs: rows.append(kwargs) or 7)(calls[name]))
    return calls


# ── V9：GH_REPO 是 assertion、不在 precedence 內 ──
def test_gh_repo_is_assertion_outside_precedence(tmp_path, monkeypatch, capsys):
    calls = recorders(monkeypatch)
    # (a) 無本機 identity ⇒ GH_REPO 成唯一候選並被採用
    rules = workspace(tmp_path, project=False, name='R9')
    client = FakeGhClient()
    assert main(['notes', 'WF-001'], client=client, root=rules, env={'GH_REPO': 'env/only'}) == 7
    assert [kw['slug'] for name, kw in client.calls if name == 'repository'] == ['env/only']
    assert client.context.repository.provenance == Provenance('env', 'GH_REPO')
    assert client.context.git is None
    capsys.readouterr()
    for rows in calls.values():
        rows.clear()
    # (b) 有本機 identity 且 GH_REPO 指向不同 stable ID ⇒ 七動詞逐一 rc≠0、零 mutation、動詞未被呼叫
    env = git_env(tmp_path)
    project = project_root(tmp_path, 'P9', env=env, remote='https://github.com/consumer/right.git')
    for part in ('core', 'roles', 'stages', 'modules'):
        (project / part).symlink_to(RULES / part, target_is_directory=True)
    args = verb_args(tmp_path)
    for verb in DISPATCH:
        client = FakeGhClient(repository=per_slug)
        rc = main([verb, *args[verb]], client=client, root=project, env={'GH_REPO': 'wrong/target'})
        err = capsys.readouterr().err
        assert rc == 1 and err == ('硬擋・D4・GH_REPO wrong/target 的 stable ID R_wrong/target ≠ resolved '
                                   'R_consumer/right（consumer/right）\n'), (verb, err)
        assert mutation_calls(client) == [] and calls[verb] == []
        assert [kw['slug'] for name, kw in client.calls if name == 'repository'] == ['consumer/right', 'wrong/target']
    # (c) 給定 --remote 時 GH_REPO 不改變被選 remote，只改變被核對的 assertion
    git(project, 'remote', 'add', 'fork', 'https://github.com/someone/fork.git', env=env)
    client = FakeGhClient(repository=per_slug)
    rc = main(['--remote', 'fork', 'notes', 'WF-001'], client=client, root=project, env={'GH_REPO': 'consumer/right'})
    err = capsys.readouterr().err
    assert rc == 1 and 'GH_REPO consumer/right 的 stable ID R_consumer/right ≠ resolved R_someone/fork' in err
    client = FakeGhClient(repository=per_slug)
    assert main(['--remote', 'fork', 'notes', 'WF-001'], client=client, root=project, env={'GH_REPO': 'someone/fork'}) == 7
    assert client.context.repository.name_with_owner == 'someone/fork'
    assert client.context.repository.provenance == Provenance('cli', '--remote fork')
    assert [kw['slug'] for name, kw in client.calls if name == 'repository'] == ['someone/fork', 'someone/fork']
    print('V9', client.context.repository)


# ── V11：default_branch='trunk' 的 fake repository metadata：brief 基線、closeout、review 回退全用 trunk ──
def test_default_branch_comes_from_resolved_repository(tmp_path, monkeypatch, capsys):
    from wf.verbs import brief as brief_module, closeout as closeout_module
    for module in (brief_module, closeout_module):
        monkeypatch.setattr(module, 'merge_tree', lambda *a, **k: 0)
    root = workspace(tmp_path, name='W11')
    catalog = load_blocks(root)
    trunk = lambda slug: per_slug(slug) | {'default_branch': 'trunk'}
    sheet = tmp_path / 'return.json'
    sheet.write_text('{}', encoding='utf-8')
    runs = [(['brief', 'WF-001', '--for', 'executor'], on_board_card()),
            (['brief', 'WF-001', '--for', 'reviewer'], on_board_card()),
            (['brief', 'WF-001', '--for', 'closeout'], on_board_card()),
            (['review', 'WF-001', '--file', str(sheet), '--role', 'executor'],
             on_board_card(stage='需求', state='待辦', branch=None, source_sha=None))]
    observed = []
    for argv, card in runs:
        client = stateful(catalog, card, repository=trunk, pulls_for_branch=[{'number': 11}], is_ancestor=True,
                          pull_request={'merge_commit_sha': 'd' * 40, 'head': {'sha': 'c' * 40}},
                          ci_checks={'check_runs': [], 'statuses': []})
        if argv[0] == 'review':
            client.board['items'][0]['fieldValues'] |= {'階段': {'name': '需求'}, '狀態': {'name': '待辦'}}
        assert main(argv, client=client, root=root, env={}) == 0, (argv, capsys.readouterr())
        assert client.context.repository.default_branch == 'trunk'
        for name, kw in client.calls:
            if name in ('branch_head', 'merge_base', 'is_ancestor'):
                observed.append((argv[0], name, kw))
    branches = [kw.get('branch', kw.get('base')) for _, name, kw in observed if name != 'merge_base'] + \
        [kw['base'] for _, name, kw in observed if name == 'merge_base']
    assert observed and 'main' not in branches
    assert 'trunk' in branches
    assert {name for _, name, _ in observed} == {'branch_head', 'merge_base', 'is_ancestor'}
    assert any(name == 'branch_head' and kw == {'branch': 'trunk'} for verb, name, kw in observed if verb == 'review')
    print('V11', observed)


# ── V12：跨 repo Project；item stable ID＝resolved 才過（owner 不同仍過）；不同即 fail-loud 零 mutation；project:null 印無 Project 設定 ──
def test_project_item_repository_stable_id_must_equal_resolved_repository(tmp_path, capsys):
    root = workspace(tmp_path, name='W12', config={'areas': ['WF'], 'modules': [], 'project': {'owner': 'other-owner', 'number': 3}})
    catalog = load_blocks(root)
    from .test_card_gate_and_projection import BOARD
    ours = item(10) | {'fieldValues': dict(BOARD)}
    ours['content']['repository'] = {'id': 'R_FAKE', 'nameWithOwner': 'fake/repo'}
    foreign = item(10, 'other/repo') | {'id': 'ITEM-OTHER', 'fieldValues': dict(BOARD)}
    foreign['content']['repository'] = {'id': 'R_OTHER', 'nameWithOwner': 'other/repo'}
    client = stateful(catalog, items=[foreign, ours])
    assert main(['edit', 'WF-001', '--set', 'feature="跨 repo 板"'], client=client, root=root, env={}) == 0
    assert 'update_card_body' in mutation_calls(client) and client.context.project_board.owner == 'other-owner'
    bad = item(10) | {'fieldValues': dict(BOARD)}
    bad['content']['repository'] = {'id': 'R_OTHER', 'nameWithOwner': 'fake/repo'}  # 名稱相同、stable ID 不同＝改名／轉移後的分裂腦
    for argv in (['edit', 'WF-001', '--set', 'feature="x"'], ['move', 'WF-001', '--to', '待確認', '--source-sha', SHA],
                 ['notes', 'WF-001'], ['brief', 'WF-001', '--for', 'executor']):
        client = stateful(catalog, items=[foreign, bad])
        rc = main(argv, client=client, root=root, env={})
        out = capsys.readouterr().out
        assert rc == 1 and any(line.startswith('硬擋・D4・Project item ITEM10 所屬 repository R_OTHER ≠ resolved R_FAKE')
                               for line in out.splitlines()), (argv, out)
        assert mutation_calls(client) == [], argv
    client = stateful(catalog)
    client.responses['repository'] = lambda slug: per_slug(slug) | {'node_id': 'R_RESOLVED'}  # open：add_to_project 回傳 R_FAKE ≠ resolved
    rc = main(['open', '11'], client=client, root=root, env={})
    out = capsys.readouterr().out
    assert rc == 1 and '硬擋・D4・Project item ITEM 所屬 repository R_FAKE ≠ resolved R_RESOLVED' in out
    assert mutation_calls(client) == ['add_to_project'] and '已完成的寫入：add_to_project item ITEM' in out
    plain = workspace(tmp_path, name='W12n', project=False)
    client = stateful(load_blocks(plain))
    assert main(['notes', 'WF-001'], client=client, root=plain, env={}) == 0
    assert '無 Project 設定' in capsys.readouterr().out and client.context.project_board is None


# ── V13（執行期）：同一 context 在 allowed／denied／unknown 三種事實下 static_identity_verified 與 rc 相同，零 mutation ──
@pytest.mark.parametrize('capability,state', [
    ({'id': 'PVT_1', 'viewerCanUpdate': True}, 'allowed'), ({'id': 'PVT_1', 'viewerCanUpdate': False}, 'denied'),
    ({'id': 'PVT_1'}, 'unknown')])
def test_permission_state_never_changes_static_gate_or_rc(tmp_path, capsys, capability, state):
    root = workspace(tmp_path, name='W13')
    client = stateful(load_blocks(root), capability=capability)
    assert main(['notes', 'WF-001'], client=client, root=root, env={}) == 0
    assert client.context.static_identity_verified is True
    facts = {fact.subject: fact for fact in client.context.permissions}
    assert facts['project'].state == state and facts['repository'].state == 'allowed'
    assert f'permission・project・{state}・projectV2.viewerCanUpdate・' in capsys.readouterr().err
    assert mutation_calls(client) == []


# ── V17：字串與數字 ref 都核對 source_issue；duplicate card_id 排序穩定、零寫入；snapshot 兩張都記入 ──
@pytest.mark.parametrize('ref', ['WF-001', '10'])
@pytest.mark.parametrize('verb', ['brief', 'notes', 'review', 'edit', 'move'])
def test_string_and_numeric_card_ref_both_verify_source_issue(tmp_path, capsys, verb, ref):
    root = workspace(tmp_path, name='W17')
    catalog = load_blocks(root)
    args = verb_args(tmp_path, ref)
    client = stateful(catalog, on_board_card(source_issue=999))
    rc = main([verb, *args[verb]], client=client, root=root, env={})
    out = capsys.readouterr().out
    assert rc == 1, (verb, ref, out)
    assert [line for line in out.splitlines() if line.startswith('硬擋・')] == ["硬擋・D3・source_issue 999 ≠ 承載 issue #10"]
    assert mutation_calls(client) == []
    control = stateful(catalog)
    assert main([verb, *args[verb]], client=control, root=root, env={}) == 0, (verb, ref, capsys.readouterr())
    assert not [line for line in capsys.readouterr().out.splitlines() if line.startswith('硬擋・')]


def test_duplicate_card_id_is_stable_and_zero_write(tmp_path, capsys):
    root = workspace(tmp_path, name='W17d')
    catalog = load_blocks(root)
    twin = issue(11, card=on_board_card(source_issue=11))  # #11 也帶 WF-001
    messages = {}
    for order in ('forward', 'reverse'):
        client = stateful(catalog, rows=[twin])
        rows = list(client.rows.values())
        client.responses['issues'] = lambda state, rows=rows: rows if order == 'forward' else rows[::-1]
        for verb, argv in (('notes', ['notes', 'WF-001']), ('edit', ['edit', 'WF-001', '--set', 'feature="x"'])):
            rc = main(argv, client=client, root=root, env={})
            out = capsys.readouterr().out
            assert rc == 1 and mutation_calls(client) == []
            messages.setdefault(verb, set()).add(next(line for line in out.splitlines() if line.startswith('硬擋・')))
    assert messages == {'notes': {'硬擋・D3・card_id WF-001 重複：issue [10, 11]'},
                        'edit': {'硬擋・D3・card_id WF-001 重複：issue [10, 11]'}}
    client = stateful(catalog, rows=[twin])
    assert main(['snapshot', '--out', str(tmp_path / 'snap')], client=client, root=root, env={}) == 0
    data = json.loads((tmp_path / 'snap/snapshot.json').read_text(encoding='utf-8'))
    assert sorted((row['card_id'], row['number']) for row in data['cards']) == [('WF-001', 10), ('WF-001', 11)]
    assert mutation_calls(client) == []
