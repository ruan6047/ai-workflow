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
from wf.gh.localgit import LocalGitFacts, RemoteFact, local_git_facts
from wf.gh.target import (PERMISSION_STATES, PermissionFact, RepositoryCandidate, RepositoryIdentity,
                          check_item_repository, item_ref, permission_fact, permission_facts,
                          resolve_repository, select_remotes, slug_of)
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
