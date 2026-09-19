"""WF-015 K7①：gitlink 取源原語的十種形狀＋負控。消費 core/adopt.md §1。

被測物＝`wf.gh.target.gitlink_sha`（索引側／HEAD 側）與 `wf.verbs._adopt.gitlink_facts`（加上簽出側的
`top_level` 守門）。本檔的 git fixture 全在 `tmp_path` 內以 `git init` 合成、全程無網路；⛔ 不依賴本 repo
的歷史存在（F-規劃-09 逐字「測試⛔ 不依賴 repo 歷史存在；判準在合成樹上驗」）。
刻意住新檔：`cli/tests/test_context_target.py` 是 WF-009／CLI-001 的契約面且含一條 stderr 全等斷言，
⛔ 不動它；本檔的 submodule 配方與該檔 V10 同形，⛔ 不改該檔。
本檔另提供其餘 `test_adopt_*.py` 共用的合成樹建構子（framework_tree／adopted_consumer）。
"""
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from wf.gh.localgit import LocalGitUnavailable
from wf.gh.target import GITLINK_MODE, gitlink_sha, local_git_facts
from wf.verbs import _adopt
from .test_compose_schema import ROOT
from .test_context_roots import RULE_DIRS, git, git_env

COPIED = ('cli/pyproject.toml', 'ADOPTION.md', '.github/scripts/trailer_check.py',
          _adopt.FRAGMENT_SOURCE)  # 片段來源檔：`core/adopt.md` §2 片段表，⛔ 不重打路徑
RULES_PATH = 'vendor/wf'


def framework_tree(root):
    """合成 rules source：四個規則目錄與三個被測檔全是**複本**（⛔ 不 symlink 回本 repo）——
    測試要能就地改 `cli/pyproject.toml` 的版本值，且它會被當成 submodule 內容 commit 進合成倉庫。"""
    for part in RULE_DIRS:
        shutil.copytree(ROOT / part, Path(root) / part)
    for relative in COPIED:
        (Path(root) / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / relative, Path(root) / relative)
    return Path(root)


def framework_repo(tmp_path, env, name='fw'):
    """把合成的 rules source 做成一顆可當 submodule 來源的 bare 倉庫。
    回 (bare 路徑, 較新的 commit, 較舊的 commit)：`submodule add` 簽出的是預設分支頭＝較新那顆。"""
    work = framework_tree(tmp_path / name)
    git(work, 'init', '-q', '-b', 'main', env=env)
    git(work, 'add', '-A', env=env)
    git(work, 'commit', '-q', '-m', 'framework v1', env=env)
    first = git(work, 'rev-parse', 'HEAD', env=env)
    (work / 'core/MARK.md').write_text('# 第二顆 commit 用的標記\n', encoding='utf-8')
    git(work, 'add', '-A', env=env)
    git(work, 'commit', '-q', '-m', 'framework v2', env=env)
    second = git(work, 'rev-parse', 'HEAD', env=env)
    bare = tmp_path / f'{name}.git'
    git(tmp_path, 'clone', '-q', '--bare', str(work), str(bare), env=env)
    return bare, second, first


def adopted_consumer(tmp_path, env, *, name='consumer', areas=('APP',)):
    """canonical install mode：superproject 內一顆真 submodule 當 rules source，
    `.wf/modules.json` 的 `rules.path` 逐字指向它。
    回 (consumer, rules_root, bare, installed, other)：`installed`＝安裝當下 gitlink 指的那顆，
    `other`＝同一顆 rules source 的另一個 commit（測試用來造漂移）。"""
    bare, installed, other = framework_repo(tmp_path, env, name=f'{name}-fw')
    consumer = tmp_path / name
    consumer.mkdir()
    git(consumer, 'init', '-q', '-b', 'main', env=env)
    git(consumer, 'commit', '-q', '--allow-empty', '-m', 'base', env=env)
    git(consumer, '-c', 'protocol.file.allow=always', 'submodule', '-q', 'add', str(bare), RULES_PATH, env=env)
    (consumer / '.wf').mkdir(exist_ok=True)
    (consumer / '.wf/modules.json').write_text(json.dumps(
        {'modules': [], 'areas': list(areas), 'project': None, 'rules': {'path': RULES_PATH}},
        ensure_ascii=False), encoding='utf-8')
    git(consumer, 'add', '-A', env=env)
    git(consumer, 'commit', '-q', '-m', 'adopt', env=env)
    return consumer, consumer / RULES_PATH, bare, installed, other


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


# ── 形狀 1–4：索引側／HEAD 側／簽出側三者會分歧，逐一實證 ────────────────────────────
def test_consistent_tree_reports_the_same_sha_on_all_three_sides(tmp_path, env):
    consumer, rules, _, installed, _ = adopted_consumer(tmp_path, env)
    index, head = gitlink_sha(consumer, RULES_PATH)
    facts = local_git_facts(rules)
    assert index == head == facts.head_sha == installed, (index, head, facts.head_sha, installed)
    assert len(index) == 40
    print('SHAPE consistent', index, head, facts.head_sha)


def test_staged_only_is_visible_on_the_index_side_and_not_on_the_head_side(tmp_path, env):
    """索引側是權威取源的理由：只暫存未 commit 時，單靠 `ls-tree HEAD` ⛔ 不診斷這個變化。"""
    consumer, rules, _, installed, other = adopted_consumer(tmp_path, env)
    git(rules, 'checkout', '-q', other, env=env)
    git(consumer, 'add', RULES_PATH, env=env)
    index, head = gitlink_sha(consumer, RULES_PATH)
    assert index == other and head == installed and index != head, (index, head)
    print('SHAPE staged_only', index, head)


def test_dirty_checkout_is_invisible_on_both_gitlink_sides(tmp_path, env):
    """簽出側是第三個必要取源的理由：索引與 HEAD 兩側都看不見簽出漂移。"""
    consumer, rules, _, installed, other = adopted_consumer(tmp_path, env)
    git(rules, 'checkout', '-q', other, env=env)
    index, head = gitlink_sha(consumer, RULES_PATH)
    facts = local_git_facts(rules)
    assert index == head == installed and facts.head_sha == other, (index, head, facts.head_sha)
    print('SHAPE dirty_checkout', index, head, facts.head_sha)


def test_uninitialised_submodule_is_blocked_by_the_top_level_guard(tmp_path, env, capsys):
    """規劃階段實測到的陷阱：對**未初始化**的子模組目錄直接讀 HEAD 會成功並回 superproject 自己的
    HEAD。負控＝naive 讀法確實踩到（必須會響），正控＝`top_level` 守門把它擋成 None。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env)
    clone = tmp_path / 'fresh'
    git(tmp_path, '-c', 'protocol.file.allow=always', 'clone', '-q', str(consumer), str(clone), env=env)
    empty = clone / RULES_PATH
    assert empty.is_dir() and not any(empty.iterdir())  # 未初始化＝目錄在、內容空
    parent_head = git(clone, 'rev-parse', 'HEAD', env=env)
    naive = local_git_facts(empty)  # 負控：⛔ 不加守門就會走上去讀到 superproject 的 HEAD
    assert naive is not None and naive.head_sha == parent_head, (naive, parent_head)
    print('WALK_UP_TRAP_CONFIRMED', naive.head_sha == parent_head, 'PARENT_HEAD', parent_head)
    index, head = gitlink_sha(clone, RULES_PATH)
    assert index == head and len(index) == 40 and index != parent_head
    config = json.loads((clone / '.wf/modules.json').read_text(encoding='utf-8'))
    from wf.context import FilesystemRulesSource, Provenance
    rules = FilesystemRulesSource(empty, Provenance('project_config', 'rules.path'))
    got_index, got_head, checkout, reason = _adopt.gitlink_facts(str(clone.resolve()), rules, config)
    assert (got_index, got_head, checkout, reason) == (index, head, None, None)
    print('GUARD_BLOCKS_UNINIT', checkout is None)


def test_the_guard_still_allows_an_initialised_submodule(tmp_path, env):
    """守門的負控之負控：已初始化時守門⛔ 不誤擋（否則 `gitlink-checkout` 恆為 unknown）。"""
    consumer, rules, _, installed, _ = adopted_consumer(tmp_path, env)
    from wf.context import FilesystemRulesSource, Provenance
    config = json.loads((consumer / '.wf/modules.json').read_text(encoding='utf-8'))
    source = FilesystemRulesSource(rules, Provenance('project_config', 'rules.path'))
    index, head, checkout, reason = _adopt.gitlink_facts(str(consumer.resolve()), source, config)
    assert (index, head, checkout, reason) == (installed, installed, installed, None)
    print('GUARD_ALLOWS_INIT', checkout)


# ── 形狀 5–9：五種事實缺席，一律回 None、⛔ 不 raise ────────────────────────────────
def test_absent_facts_return_none_on_both_sides(tmp_path, env):
    plain = tmp_path / 'plain'
    (plain / 'sub').mkdir(parents=True)
    git(plain, 'init', '-q', '-b', 'main', env=env)
    (plain / 'sub/a.txt').write_text('x', encoding='utf-8')
    git(plain, 'add', '-A', env=env)
    git(plain, 'commit', '-q', '-m', 'plain', env=env)
    empty = tmp_path / 'empty'
    empty.mkdir()
    git(empty, 'init', '-q', '-b', 'main', env=env)          # 尚無 commit
    (empty / 'x.txt').write_text('x', encoding='utf-8')
    git(empty, 'add', '-A', env=env)
    nongit = tmp_path / 'nongit'
    nongit.mkdir()
    bare = tmp_path / 'bare.git'
    git(tmp_path, 'init', '-q', '--bare', str(bare), env=env)
    cases = {'not_a_submodule': (plain, 'sub'), 'missing_path': (plain, 'nope'),
             'no_commit_yet': (empty, 'x.txt'), 'non_worktree': (nongit, 'sub'), 'bare': (bare, 'sub')}
    for name, (root, relative) in cases.items():
        got = gitlink_sha(root, relative)
        assert got == (None, None), (name, got)
        print('SHAPE', name, got)
    assert len(cases) == 5


def test_git_unavailable_raises_instead_of_returning_none(tmp_path):
    """唯一該 raise 的那一種：git 不可執行（同 `local_git_facts` 的既有宣告）。"""
    def broken(*args, **kwargs):
        raise OSError('git not found')

    with pytest.raises(LocalGitUnavailable):
        gitlink_sha(tmp_path, 'anything', runner=broken)
    print('SHAPE git_unavailable raised LocalGitUnavailable')


def test_the_reader_is_effective_and_the_mode_constant_is_not_retyped(tmp_path, env):
    """負控：把 mode 常數換成別的值後索引側必須變成 None（證明比對的真的是 mode 160000）。"""
    consumer, _, _, installed, _ = adopted_consumer(tmp_path, env)
    assert GITLINK_MODE == '160000' and gitlink_sha(consumer, RULES_PATH)[0] == installed
    raw = subprocess.run(('git', '-C', str(consumer), 'ls-files', '-s', '--', RULES_PATH),
                         capture_output=True, text=True, check=True, env=env).stdout
    assert raw.split()[0] == GITLINK_MODE, raw
    from wf.gh import target
    assert target._gitlink_of(raw.replace(GITLINK_MODE, '100644'), 1) is None
    print('NEGATIVE_CONTROL mode_swapped -> None', repr(raw.strip()))


def test_the_three_branches_of_rules_root_location(tmp_path, env):
    """core/adopt.md §1 的三個分支＋一條邊界：取不到路徑時四列的理由是固定措辭、⛔ 不含例外類別名。"""
    from wf.context import FilesystemRulesSource, Provenance
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env)
    config = json.loads((consumer / '.wf/modules.json').read_text(encoding='utf-8'))
    canonical = str(consumer.resolve())
    declared = FilesystemRulesSource(rules, Provenance('project_config', 'rules.path'))
    assert _adopt.gitlink_relative(canonical, declared, config) == (RULES_PATH, None)
    flagged = FilesystemRulesSource(rules, Provenance('cli', '--rules-root'))
    assert _adopt.gitlink_relative(canonical, flagged, config) == (RULES_PATH, None)
    outside = FilesystemRulesSource(framework_tree(tmp_path / 'outside'), Provenance('cli', '--rules-root'))
    assert _adopt.gitlink_relative(canonical, outside, config) == (None, _adopt.OUTSIDE_PROJECT)
    same = FilesystemRulesSource(consumer, Provenance('default', 'project_root'))
    assert _adopt.gitlink_relative(canonical, same, config) == (None, _adopt.RULES_IS_PROJECT)
    class NotFilesystem:  # RulesSource Protocol 恰四成員、⛔ 無 path ⇒ 定位不到 gitlink
        identity, provenance = 'zip://x', Provenance('cli', 'zip fixture')
    assert _adopt.gitlink_relative(canonical, NotFilesystem(), config) == (None, _adopt.NOT_FILESYSTEM)
    for reason in (_adopt.OUTSIDE_PROJECT, _adopt.RULES_IS_PROJECT, _adopt.NOT_FILESYSTEM):
        assert 'Error' not in reason and 'Traceback' not in reason, reason
    print('BRANCHES rules.path/--rules-root/outside/project_root/not-filesystem all resolved')


# ── A18：`pin` ⛔ 不與 gitlink SHA 直接比相等，且⛔ 不做 SHA→版本值映射 ─────────────
import ast  # noqa: E402（本段的判準只用到標準庫 AST；放在此處與上面的 gitlink 形狀分段）

from .test_gh_scope import imports  # noqa: E402（import 集合的解析只有一個居所，⛔ 不重打）

ADOPT_SOURCES = 'cli/src/wf/verbs/_adopt*.py'
SHA_SOURCES = ('index', 'head', 'checkout', 'source_commit', 'gitlink', 'sha')
OBJECT_DB = ('cat-file', 'git show', 'rev-parse', 'ls-tree')


def _mentions(node, needles):
    """該運算式的任一識別名／字面是否命中 needles（下界式判定：命中即記為一個站點）。"""
    text = ast.dump(node)
    return any(f"'{needle}'" in text or f'"{needle}"' in text for needle in needles)


def pin_sha_comparison_sites(text):
    """把 `pin` 與 gitlink SHA 取源（或 40 碼 hex 字面）作 `==`／`!=` 的站點。"""
    sites = []
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(op, (ast.Eq, ast.NotEq)) for op in node.ops):
            continue
        sides = [node.left, *node.comparators]
        hexes = [s for s in sides if isinstance(s, ast.Constant)
                 and isinstance(s.value, str) and len(s.value) == 40
                 and all(c in '0123456789abcdef' for c in s.value)]
        if any(_mentions(s, ('pin',)) for s in sides) and (
                hexes or any(_mentions(s, SHA_SOURCES) for s in sides)):
            sites.append(ast.dump(node))
    return sites


def test_the_pin_is_never_compared_against_a_gitlink_sha():
    """掃描面＝`cli/src/wf/verbs/_adopt*.py` 的呼叫圖；明示排除測試替身。"""
    sources = sorted(ROOT.glob(ADOPT_SOURCES))
    assert len(sources) == 3, [p.name for p in sources]
    for path in sources:
        text = path.read_text(encoding='utf-8')
        sites = pin_sha_comparison_sites(text)
        assert sites == [], (path.name, sites)
        for needle in OBJECT_DB:       # ⛔ 無為了還原版本字串而讀子模組物件庫的站點
            assert needle not in text, (path.name, needle)
        assert 'subprocess' not in imports(text), path.name   # ⛔ 不自開子程序
        print('A18 clean', path.relative_to(ROOT).as_posix(), len(text.splitlines()), 'lines')


def test_the_pin_sha_scanner_is_effective():
    """負控（必須會響）：注入一處 `pin` 與 40 碼 SHA 的相等比較後，掃描器必須命中。"""
    injected = ("def probe(entry, index):\n"
                "    if entry['pin'] == '" + '0' * 40 + "':\n"
                "        return True\n"
                "    return entry['pin'] != index\n")
    sites = pin_sha_comparison_sites(injected)
    assert len(sites) == 2, sites
    print('NEGATIVE_CONTROL pin_sha_sites', len(sites))
