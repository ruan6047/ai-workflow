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


# ═══════════════════ main() 層共用：自舉工作區、板上有卡的替身、七動詞驅動 ═══════════════════
from .fakes import FakeGhClient  # noqa: E402
from .test_brief_sections import card as brief_card  # noqa: E402
from .test_card_gate_and_projection import BOARD  # noqa: E402
from .test_end_to_end import E2EClient  # noqa: E402
from .test_open_verb import block, intake, issue, item  # noqa: E402
from wf.verbs.main import main  # noqa: E402

SHA = 'b' * 40
MUTATIONS = ('update_card_body', 'post_comment', 'write_project_field', 'add_to_project',
             'remove_from_project', 'close_issue')
FAKE_REMOTE = 'https://github.com/fake/repo.git'  # slug＝FakeGhClient.repo，板上 item 的 nameWithOwner 才對得上


def workspace(tmp_path, *, project=True, name='W', git_remote=None, config=None):
    """自舉形狀：四個規則目錄 symlink＋`.wf`；git_remote 給定時另 init 並加 origin。"""
    root = rules_root(tmp_path, name)
    (root / '.wf').mkdir()
    (root / '.wf/modules.json').write_text(json.dumps(
        {'areas': ['WF'], 'modules': [], 'project': {'owner': 'fake', 'number': 1} if project else None}
        if config is None else config), encoding='utf-8')
    if git_remote is not None:
        env = git_env(tmp_path)
        git(root, 'init', '-q', '-b', 'main', env=env)
        git(root, 'remote', 'add', 'origin', git_remote, env=env)
    return root


def on_board_card(**changes):
    return brief_card(**{'branch': 'wf/WF-001', 'source_sha': SHA, 'stage_plan': ['需求', '執行', '審核', '結案'],
                         **changes})


def stateful(catalog, card_json=None, *, rows=(), items=None, **responses):
    """#10 帶卡且在板上（投影欄＝BOARD）、#11 是清單項；E2EClient 記住自己貼的留言。"""
    card_json = on_board_card() if card_json is None else card_json
    rows = [issue(10, card=card_json), issue(11, body='清單項\n' + block('wf-intake', intake())), *rows]
    items = [item(10) | {'fieldValues': dict(BOARD)}] if items is None else items  # id=ITEM10；open 新加的是 ITEM
    client = E2EClient(catalog, rows, items)
    client.responses.setdefault('merge_base', SHA)
    client.responses.update(responses)
    return client


def verb_args(tmp_path, ref='WF-001'):
    sheet = tmp_path / 'return.json'
    sheet.write_text('{}', encoding='utf-8')
    return {'open': ['11'], 'move': [ref, '--to', '待確認', '--source-sha', SHA],
            'edit': [ref, '--set', 'feature="改過"'], 'notes': [ref], 'brief': [ref, '--for', 'executor'],
            'review': [ref, '--file', str(sheet), '--role', 'executor'],
            'snapshot': ['--out', str(tmp_path / 'out')]}


def mutation_calls(client):
    return [name for name, _ in client.calls if name in MUTATIONS]


# ── V1：rules_root=R 與 project_root=P 不同時，規則資產全解析到 R、專案資產全解析到 P、兩集合不相交 ──
def test_external_dual_root_separates_rules_and_project_assets(tmp_path, monkeypatch, capsys):
    from wf.verbs import brief as brief_module, closeout as closeout_module
    rules = rules_root(tmp_path, 'R')
    project = project_root(tmp_path, 'P', config={'areas': ['WF'], 'modules': [], 'project': {'owner': 'fake', 'number': 1}},
                           remote=FAKE_REMOTE)
    catalog = load_blocks(FilesystemRulesSource(rules))
    opened, git_roots = [], []
    real_open = pathlib.Path.open

    def spy(self, *args, **kwargs):  # 記開檔的絕對路徑本身（⛔ 不 resolve：R 的規則目錄是 symlink，resolve 會跳到本 repo）
        opened.append(pathlib.Path(self).absolute())
        return real_open(self, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, 'open', spy)
    for module in (brief_module, closeout_module):
        monkeypatch.setattr(module, 'merge_tree',
                            lambda base, head, root='.', **k: git_roots.append(pathlib.Path(root).resolve()) or 0)
    client = stateful(catalog, pulls_for_branch=[{'number': 11}], is_ancestor=True,
                      pull_request={'merge_commit_sha': 'd' * 40, 'head': {'sha': 'c' * 40}},
                      ci_checks={'check_runs': [], 'statuses': []})
    prefix = ['--rules-root', str(rules)]
    args = verb_args(tmp_path)
    args['snapshot'] = []  # 缺省輸出目錄＝<project_root>/.wf/snapshot：證明 snapshot 輸出落在 P
    args['brief-reviewer'] = ['WF-001', '--for', 'reviewer']
    args['brief-closeout'] = ['WF-001', '--for', 'closeout']
    for name in ('notes', 'brief', 'brief-reviewer', 'brief-closeout', 'review', 'edit', 'move', 'open', 'snapshot'):
        verb = name.split('-')[0]
        assert main([*prefix, verb, *args[name]], client=client, root=project, env={}) == 0, (name, capsys.readouterr())
    capsys.readouterr()
    r_root, p_root = rules.resolve(), project.resolve()
    rule_opens = sorted({p.relative_to(r_root).as_posix() for p in opened if p.is_relative_to(r_root)})
    project_opens = sorted({p.relative_to(p_root).as_posix() for p in opened if p.is_relative_to(p_root)})
    others = sorted({str(p) for p in opened if not (p.is_relative_to(r_root) or p.is_relative_to(p_root))})
    assert rule_opens and all(path.split('/')[0] in RULE_DIRS for path in rule_opens), rule_opens
    assert project_opens and all(path.split('/')[0] == '.wf' for path in project_opens), project_opens
    assert '.wf/snapshot/snapshot.json' in project_opens and '.wf/modules.json' in project_opens
    assert others == [str((tmp_path / 'return.json').resolve())], others  # 只剩交回單檔（呼叫端給的絕對路徑）
    assert not [p for p in rule_opens if p.startswith('.wf')]
    assert not [p for p in project_opens if p.split('/')[0] in RULE_DIRS]
    assert git_roots and set(git_roots) == {p_root}  # git -C 工作樹＝P
    assert client.context.rules.identity == str(r_root) and client.context.project.root.canonical == str(p_root)
    print('V1 rule_opens', rule_opens)
    print('V1 project_opens', project_opens)
    # 負控：R／P 對調 ⇒ 每個動詞回 typed 錯誤 rc≠0（不是 KeyError／FileNotFoundError），零 API 讀取
    for name in ('notes', 'brief', 'review', 'edit', 'move', 'open', 'snapshot'):
        swapped = stateful(catalog)
        rc = main(['--rules-root', str(project), '--project-root', str(rules), name, *args[name]],
                  client=swapped, root=None, env={})
        err = capsys.readouterr().err
        assert rc == 1 and '缺 core' in err and 'Error' not in err and 'Traceback' not in err, (name, err)
        assert swapped.calls == []


# ── V5：main(root=R) 與無 root（cwd=R）的行為、rc、輸出相同；--rules-root 分流；旗標在動詞後必須失敗 ──
def test_invocation_shape_is_backward_compatible(tmp_path, monkeypatch, capsys):
    from wf.verbs import snapshot as snapshot_module
    rules = workspace(tmp_path, project=False, name='R')
    project = project_root(tmp_path, 'P', remote=FAKE_REMOTE)
    outputs = {}
    for name, kwargs in (('root', dict(root=rules)), ('cwd', {})):
        if name == 'cwd':
            monkeypatch.chdir(rules)
        client = FakeGhClient(issues=[])
        assert main(['snapshot', '--out', str(tmp_path / name)], client=client, env={}, **kwargs) == 0
        data = json.loads((tmp_path / name / 'snapshot.json').read_text(encoding='utf-8'))
        outputs[name] = (data | {'generated_at': None}, capsys.readouterr().out, client.context.project.root.canonical)
    assert outputs['root'] == outputs['cwd']
    assert outputs['root'][1] == '無 Project 設定\n' and outputs['root'][0]['cards'] == []  # 基線 fa884be 同形狀
    assert outputs['root'][2] == str(rules.resolve())
    opened = []
    real_open = pathlib.Path.open
    monkeypatch.setattr(pathlib.Path, 'open',
                        lambda self, *a, **k: opened.append(pathlib.Path(self).absolute()) or real_open(self, *a, **k))
    client = FakeGhClient(issues=[])
    assert main(['--rules-root', str(rules), 'snapshot', '--out', str(tmp_path / 'split')],
                client=client, root=project, env={}) == 0
    monkeypatch.setattr(pathlib.Path, 'open', real_open)
    assert client.context.rules.identity == str(rules.resolve()) and client.context.catalog.by_label('json wf-enums')
    assert client.context.project.root.canonical == str(project.resolve())
    assert any(p.is_relative_to(rules.resolve() / 'core') for p in opened)
    assert (project.resolve() / '.wf/modules.json') in opened
    assert not any(p.is_relative_to(project.resolve() / 'core') for p in opened)
    assert (tmp_path / 'split/snapshot.json').is_file()
    capsys.readouterr()
    seen = []
    monkeypatch.setattr(snapshot_module, 'run', lambda argv, **kwargs: seen.append(argv) or 0)
    assert main(['snapshot', '--rules-root', str(rules)], client=FakeGhClient(issues=[]), root=project, env={}) == 2
    assert seen == [] and capsys.readouterr().err.strip() == 'wf <open|move|edit|notes|brief|review|snapshot> …'


# ── V6：rules.path 以 project_root 為 base（.wf 為 base 指到不存在）；旗標各自勝過設定鍵；型別不合＝ProjectConfigError ──
def test_config_keys_precedence_and_relative_base(tmp_path, monkeypatch, capsys):
    from wf.context import RootError, resolve_path
    from wf.verbs import notes as notes_module
    env = git_env(tmp_path)
    config = {'areas': ['WF'], 'modules': [], 'project': None, 'rules': {'path': 'vendor/wf-rules'},
              'remote': 'upstream'}
    project = project_root(tmp_path, 'P6', config=config, env=env, remote=None)
    git(project, 'remote', 'add', 'origin', 'https://github.com/consumer/right.git', env=env)
    git(project, 'remote', 'add', 'upstream', 'https://github.com/parent/base.git', env=env)
    (project / 'vendor').mkdir()
    rules_root(project / 'vendor', 'wf-rules')
    other = rules_root(tmp_path, 'R6')
    seen = []
    monkeypatch.setattr(notes_module, 'run', lambda argv, **kwargs: seen.append(kwargs['context']) or 7)
    assert main(['notes', 'WF-001'], client=FakeGhClient(), root=project, env={}) == 7
    ctx = seen[-1]
    assert ctx.rules.identity == str((project / 'vendor/wf-rules').resolve())
    assert ctx.rules.provenance == Provenance('project_config', 'rules.path')
    assert ctx.repository.name_with_owner == 'parent/base' and ctx.repository.provenance.kind == 'project_config'
    assert_every_resolved_field_has_provenance(ctx)  # V4：bootstrap 產出的 Context 也全欄有 provenance
    with pytest.raises(RootError):  # 負控：以 .wf 為 base 會指到不存在路徑
        resolve_path('vendor/wf-rules', project / '.wf', Provenance('project_config', 'rules.path'))
    assert main(['--rules-root', str(other), '--remote', 'origin', 'notes', 'WF-001'],
                client=FakeGhClient(), root=project, env={}) == 7
    ctx = seen[-1]
    assert ctx.rules.identity == str(other.resolve()) and ctx.rules.provenance == Provenance('cli', '--rules-root')
    assert ctx.repository.name_with_owner == 'consumer/right'
    assert ctx.repository.provenance == Provenance('cli', '--remote origin')
    (project / '.wf/modules.json').write_text(json.dumps(config | {'rules': 'vendor/wf-rules'}), encoding='utf-8')
    capsys.readouterr()
    assert main(['notes', 'WF-001'], client=FakeGhClient(), root=project, env={}) == 1
    assert capsys.readouterr().err.startswith('.wf/modules.json 不合法：rules')
    (project / '.wf/modules.json').write_text(json.dumps(config | {'rules': {'path': 'vendor/absent'}}), encoding='utf-8')
    assert main(['notes', 'WF-001'], client=FakeGhClient(), root=project, env={}) == 1
    assert 'rules.path 不可讀' in capsys.readouterr().err
    print('V6 rules', ctx.rules.identity, ctx.repository)
