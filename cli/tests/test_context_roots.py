"""WF-009 雙 root 與 RulesSource：消費 core/verbs.md §2、ADOPTION.md §2。
V1 雙 root 隔離、V2 transport-agnostic、V3 嚴格 canonicalize、V4 provenance 全欄覆蓋、
V5 invocation 向後相容、V6 設定鍵 precedence 與相對 base，另加 public_contract digest 決定性。
所有 GitHub 操作走 cli/tests/fakes.py 的替身；本機 git 只在 tmp_path 內合成、⛔ 不碰網路。
"""
from dataclasses import fields, is_dataclass, replace
import fnmatch
from importlib.resources import as_file, files
import json
import os
import pathlib
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import pytest

from wf.compose.blocks import load_blocks
from wf.compose.project_config import ProjectConfigError, load_project_config
from wf.context import (PROVENANCE_KINDS, Context, FilesystemRulesSource, ProjectRoot, Provenance,
                        Resolved, RulesSource, RulesSourceError, contract_digest, open_rules_source,
                        public_contract)
from .test_compose_schema import ROOT

RULE_DIRS = ('core', 'roles', 'stages', 'modules')
GIT_ENV = {'GIT_CONFIG_NOSYSTEM': '1', 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@x',
           'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@x', 'GIT_TERMINAL_PROMPT': '0'}


def git_env(tmp_path):
    """本機 git 只讀合成 fixture：全域設定指到 tmp 內空檔，⛔ 不受開發機 insteadOf／預設分支影響。"""
    empty = tmp_path / 'gitconfig-empty'
    empty.touch()
    return {**os.environ, **GIT_ENV, 'GIT_CONFIG_GLOBAL': str(empty)}


def git(root, *args, env):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, check=True,
                          env=env).stdout.strip()


def rules_root(tmp_path, name='R'):
    """只 symlink 四個規則目錄（沿用 test_main_wiring.py unadopted_root 的形狀）。"""
    target = tmp_path / name
    target.mkdir()
    for part in RULE_DIRS:
        (target / part).symlink_to(ROOT / part, target_is_directory=True)
    return target


def project_root(tmp_path, name='P', *, config=None, env=None, remote='https://github.com/consumer/right.git'):
    """只有 `.wf` 與 `.git`：git init＋一個 remote（無 upstream）；config 缺省無 Project。"""
    target = tmp_path / name
    (target / '.wf').mkdir(parents=True)
    (target / '.wf/modules.json').write_text(json.dumps(
        {'areas': ['WF'], 'modules': [], 'project': None} if config is None else config), encoding='utf-8')
    env = git_env(tmp_path) if env is None else env
    git(target, 'init', '-q', '-b', 'main', env=env)
    if remote is not None:
        git(target, 'remote', 'add', 'origin', remote, env=env)
    return target


class TraversableRulesSource:
    """V2 的 zip adapter：只靠 importlib.resources 的 Traversable（列舉、讀內容），⛔ 不落地成目錄。"""

    def __init__(self, root, identity):
        self._root, self.identity = root, identity
        self.provenance = Provenance('cli', 'zip fixture')

    def iter_assets(self, pattern):
        parts = pattern.split('/')

        def walk(node, prefix, index):
            for child in node.iterdir():
                if not fnmatch.fnmatchcase(child.name, parts[index]):
                    continue
                path = prefix + child.name
                if index == len(parts) - 1:
                    if child.is_file():
                        yield path
                elif child.is_dir():
                    yield from walk(child, path + '/', index + 1)

        return sorted(walk(self._root, '', 0))

    def read_text(self, relative):
        node = self._root
        for part in relative.split('/'):
            node = node / part
        with node.open('r', encoding='utf-8', newline='') as handle:
            return handle.read()


def zipped_rules(tmp_path, package='wf009_rules_fixture'):
    archive = tmp_path / 'rules.zip'
    with zipfile.ZipFile(archive, 'w') as zipped:
        zipped.writestr(f'{package}/__init__.py', '')
        for pattern in ('core/*.md', 'modules/*/module.md'):
            for path in sorted(ROOT.glob(pattern)):
                zipped.write(path, f'{package}/{path.relative_to(ROOT).as_posix()}')
    return archive, package


# ── V2：同一份規則經檔案系統與 zip（importlib.resources）載入，block 清單與 schema $id 索引逐字相等 ──
def test_rules_source_capability_contract_is_transport_agnostic(tmp_path, monkeypatch):
    archive, package = zipped_rules(tmp_path)
    monkeypatch.syspath_prepend(str(archive))
    monkeypatch.delitem(sys.modules, package, raising=False)
    traversable = files(package)
    assert not isinstance(traversable, pathlib.Path)  # zip 下 files() 是 zipfile 的 Traversable
    source = TraversableRulesSource(traversable, f'zip:{archive}')
    filesystem = load_blocks(FilesystemRulesSource(ROOT))
    zipped = load_blocks(source)
    assert [(b.label, b.data, b.raw, b.source) for b in zipped.blocks] == \
        [(b.label, b.data, b.raw, b.source) for b in filesystem.blocks]
    assert zipped.schemas == filesystem.schemas and set(zipped.schemas) == {
        'wf-card', 'wf-contract', 'wf-intake', 'wf-note', 'wf-return', 'wf-ruling'}
    assert source.iter_assets('core/*.md') == FilesystemRulesSource(ROOT).iter_assets('core/*.md')
    with as_file(traversable) as materialized:
        assert materialized.is_dir() and (materialized / 'core').is_dir()
    assert not materialized.exists()  # as_file 的落地只活在 context 內：operation-lifetime，⛔ 無永久 materialization
    for name in ('path', 'materialize', '__fspath__'):
        assert not hasattr(source, name) and name not in vars(RulesSource)
    print('V2 blocks', len(zipped.blocks), 'schemas', sorted(zipped.schemas))


# ── V3：symlink 別名、含 ..、相對路徑 → 同一 canonical identity；broken symlink 與缺 sentinel typed 失敗 ──
def test_filesystem_rules_source_canonicalizes_strictly(tmp_path, monkeypatch):
    real = tmp_path / 'rules'
    (real / 'core').mkdir(parents=True)
    (real / 'core/x.md').write_text('---\nname: x\nwhen: w\nnon_scope: n\nlast_confirmed: 2026-09-01\n---\n',
                                   encoding='utf-8')
    (tmp_path / 'alias').symlink_to(real, target_is_directory=True)
    monkeypatch.chdir(tmp_path)
    identities = {str(kind): FilesystemRulesSource(path).identity for kind, path in (
        ('alias', tmp_path / 'alias'), ('dotdot', tmp_path / 'rules' / 'core' / '..'), ('relative', 'rules'))}
    assert set(identities.values()) == {str(real.resolve())}, identities
    assert open_rules_source('alias', Provenance('cli', '--rules-root')).identity == str(real.resolve())
    (tmp_path / 'broken').symlink_to(tmp_path / 'missing')
    with pytest.raises(RulesSourceError, match='rules root 不可讀'):
        FilesystemRulesSource(tmp_path / 'broken')
    (tmp_path / 'nocore').mkdir()
    with pytest.raises(RulesSourceError, match='缺 core'):
        open_rules_source(tmp_path / 'nocore', Provenance('cli', '--rules-root'))
    with pytest.raises(RulesSourceError, match='規則資產不可讀'):
        FilesystemRulesSource(real).read_text('core/absent.md')
    print('V3 identities', identities)


# ── V4：以 dataclasses.fields 列舉 Context 的 resolved 欄位，每個有非空 provenance 且 kind 在值域 ──
def provenances(value):
    """遞迴收集帶 provenance 的值物件（dataclass 欄位與 tuple 逐一走訪，⛔ 不手抄欄名）。"""
    if hasattr(value, 'provenance'):
        yield value.provenance
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            yield from provenances(getattr(value, field.name))
    elif isinstance(value, tuple):
        for item in value:
            yield from provenances(item)


def assert_every_resolved_field_has_provenance(context):
    bearing = ('Resolved', 'ProjectRoot', 'RulesSource', 'RepositoryIdentity', 'ProjectIdentity')
    expected = {f.name for f in fields(Context) if any(name in str(f.type) for name in bearing)}
    assert expected >= {'project', 'rules', 'invocation_cwd', 'repository', 'project_board'}
    seen = {}
    for field in fields(Context):
        value = getattr(context, field.name)
        found = list(provenances(value))
        if field.name in expected and value is not None:
            assert found, f'{field.name} 缺 provenance'
        for provenance in found:
            assert provenance.kind in PROVENANCE_KINDS and provenance.detail, (field.name, provenance)
        seen[field.name] = [(p.kind, p.detail) for p in found]
    return seen


def synthetic_context(tmp_path):
    from wf.gh.target import PermissionFact, ProjectIdentity, RepositoryIdentity
    rules = rules_root(tmp_path)
    source = open_rules_source(rules, Provenance('cli', '--rules-root'))
    root = Resolved('.', str(tmp_path), str(tmp_path.resolve()), Provenance('default', 'invocation cwd'))
    project = ProjectRoot(root, str(tmp_path / '.wf/modules.json'), {'project': None},
                          Provenance('project_config', '.wf/modules.json'))
    return Context(project, source, load_blocks(source), None,
                   RepositoryIdentity('R_1', 'a/b', 'main', Provenance('git', 'sole remote origin')),
                   ProjectIdentity('PVT_1', 'a', 1, Provenance('api', 'projectV2.id')),
                   (PermissionFact('repository', 'unknown', 'repository.permissions.push', '缺欄位'),),
                   root, True)


def test_resolved_values_carry_raw_base_canonical_and_provenance(tmp_path):
    context = synthetic_context(tmp_path)
    seen = assert_every_resolved_field_has_provenance(context)
    for resolved in (context.project.root, context.invocation_cwd):
        assert {f.name for f in fields(resolved)} == {'raw', 'base', 'canonical', 'provenance'}
    print('V4 provenance', json.dumps(seen, ensure_ascii=False))
    stripped = replace(context, invocation_cwd=SimpleNamespace(raw='.', base='.', canonical='.'))
    with pytest.raises(AssertionError, match='invocation_cwd 缺 provenance'):  # 負控：缺 provenance 必被抓到
        assert_every_resolved_field_has_provenance(stripped)
    bad_kind = replace(context, invocation_cwd=replace(context.invocation_cwd,
                                                       provenance=Provenance('guess', 'x')))
    with pytest.raises(AssertionError):
        assert_every_resolved_field_has_provenance(bad_kind)


# ── public_contract／contract_digest：兩次相同、只含 JSON primitive、Protocol 成員與簽章都在 schema 內 ──
def primitives_only(value):
    if isinstance(value, dict):
        return all(isinstance(k, str) and primitives_only(v) for k, v in value.items())
    return isinstance(value, (str, int, float, bool)) or value is None or (
        isinstance(value, list) and all(primitives_only(v) for v in value))


def test_public_contract_digest_is_deterministic():
    first, second = public_contract(), public_contract()
    assert first == second and primitives_only(first)
    assert contract_digest() == contract_digest() == __import__('hashlib').sha256(json.dumps(
        first, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()
    assert set(first) == {'Context', 'ProjectRoot', 'Resolved', 'Provenance', 'LocalGitFacts', 'RemoteFact',
                          'RepositoryIdentity', 'ProjectIdentity', 'TargetIssue', 'ProjectItemRef',
                          'PermissionFact', 'RulesSource'}
    assert not is_dataclass(RulesSource) and fields(Context)  # Protocol 不是 dataclass：fields 取不到它
    assert first['RulesSource']['attributes'] == {'identity': 'str', 'provenance': 'Provenance'}
    assert set(first['RulesSource']['methods']) == {'iter_assets', 'read_text'}
    assert 'pattern' in first['RulesSource']['methods']['iter_assets']
    assert 'relative' in first['RulesSource']['methods']['read_text']
    assert set(first['Context']) == {f.name for f in fields(Context)}
    print('CONTRACT_DIGEST', contract_digest())
    print('CONTRACT', json.dumps(first, sort_keys=True, ensure_ascii=False))


# ── V6（設定鍵型別）：rules／remote 不合型別 ⇒ ProjectConfigError；合法值原樣進 cfg（precedence 與相對 base 見 V6 主測試）──
@pytest.mark.parametrize('raw,reason', [
    ({'rules': 'vendor/wf-rules'}, 'rules'), ({'rules': {'path': ''}}, 'rules'), ({'rules': {'path': 1}}, 'rules'),
    ({'rules': {'path': 'x', 'extra': 1}}, 'rules'), ({'rules': {}}, 'rules'),
    ({'remote': 7}, 'remote'), ({'remote': ''}, 'remote'), ({'remote': 'https://github.com/a/b.git'}, 'remote'),
    ({'remote': 'x@github.com:a/b.git'}, 'remote')])
def test_config_keys_reject_wrong_types(tmp_path, raw, reason):
    (tmp_path / '.wf').mkdir()
    (tmp_path / '.wf/modules.json').write_text(json.dumps(raw), encoding='utf-8')
    with pytest.raises(ProjectConfigError, match=reason):
        load_project_config(tmp_path)


def test_config_keys_accept_null_and_valid_values(tmp_path):
    (tmp_path / '.wf').mkdir()
    (tmp_path / '.wf/modules.json').write_text(
        json.dumps({'rules': {'path': 'vendor/wf-rules'}, 'remote': 'upstream'}), encoding='utf-8')
    cfg = load_project_config(tmp_path)
    assert cfg['rules'] == {'path': 'vendor/wf-rules'} and cfg['remote'] == 'upstream'
    (tmp_path / '.wf/modules.json').write_text(json.dumps({'rules': None, 'remote': None}), encoding='utf-8')
    cfg = load_project_config(tmp_path)
    assert cfg['rules'] is None and cfg['remote'] is None
