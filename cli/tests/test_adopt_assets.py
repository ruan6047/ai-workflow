"""WF-015：框架資產表、`install` 的兩個分支、未完成項的形狀，與 CI 來源資產的整檔 delta。
消費 core/adopt.md §2（資產表、單一 `path` 文法、兩個分支、未完成項鍵集合、CI delta）／§3 `install`。

資產名、來源檔與目標路徑三者皆由 `wf.verbs._adopt` `import` 或由 `core/adopt.md` §2 的資產表解析取得
（F-執行者-04 逐字「驗證器 `import` 使用，⛔ 不重打常數」）；兩側比對相等才成立。
合成 consumer 樹＝`test_adopt_gitlink.py` 的 `adopted_consumer`（`core/adopt.md` §0）。
`.github/workflows/ci.yml` 在本卡是唯讀端：本檔對它只讀、只比對，⛔ 不改。
本檔的 delta 比對母體是**兩個整檔**、⛔ 不經任何片段解析器——該層已隨本卡撤銷，其符號⛔ 不存在
（`test_the_fragment_locating_layer_is_retired` 直接對模組命名空間求證）。
"""
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from wf.verbs import _adopt, _adopt_manifest
from wf.verbs.main import main
from .fakes import FakeGhClient
from .test_adopt_gitlink import adopted_consumer
from .test_adoption_contract import ASSET_COLUMNS, asset_table, sections, synthetic
from .test_compose_schema import ROOT
from .test_context_roots import git_env

MERGE_BASE = '372fe7f3bcdea7d7681910938387fd36a730c369'
CI = '.github/workflows/ci.yml'
DELTA = '          submodules: true\n'
JOBS_ANCHOR = '\njobs:\n'
REQUIRED_JOBS = ('secret-scan', 'commit-trailer')    # A2 逐字要求必含其來源資產的兩個 job
EXCLUDED_JOBS = ('reachability', 'cli-tests')        # A2 明示排除的兩個 job
# 隨本卡撤銷的片段定位層：這些名字在 `_adopt` 與 `_adopt_manifest` 都⛔ 不得再存在。
# ⛔ 不得推出「改名即可保留」——判準是「CLI ⛔ 不在採用者既有檔案內做片段機械定位」，
# 本清單只是它的機械下界，另有兩個分支的行為判準把該機制的**行為**也擋掉。
RETIRED = ('split_lines', 'jobs_index', 'job_key_of', 'job_names', 'unsafe_job_lines', 'job_span',
           'job_text', 'skeleton_of', 'upsert_job', 'remove_jobs', 'fragment_of', 'CARRIER',
           'FRAGMENTS', 'FRAGMENT_SOURCE', 'MANAGED_ASSETS', 'JOB_KEY', 'JOBS_KEY', 'JOB_INDENT')


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


def run_step(consumer, step, client=None):
    client = FakeGhClient() if client is None else client
    rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', step],
              client=client, root=None, env={})
    return rc, client


def manifest_of(consumer):
    return json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))


def digests(root, skip=('.git', '.wf')):
    """(相對路徑 → sha256) 全樹快照；`.git/` 依 `core/adopt.md` §0 逐字排除，`.wf/` 另由 manifest 判準看。"""
    found = {}
    for path in sorted(Path(root).rglob('*')):
        relative = path.relative_to(root)
        if relative.parts[0] in skip:
            continue
        if path.is_symlink():
            found[relative.as_posix()] = 'symlink:' + str(Path(path).readlink())
        elif path.is_file():
            found[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif path.is_dir():
            found[relative.as_posix()] = 'dir'
    return found


def pending_items(out):
    """自 stdout 解析未完成項；⛔ 不以出現位置取，逐行以固定標記取。"""
    mark = f'{_adopt.STEP_PREFIX}・'
    found = []
    for line in out.splitlines():
        parts = line.split('・')
        if not line.startswith(mark) or len(parts) < 4 or parts[2] != _adopt.PENDING_MARK:
            continue
        found.append((parts[1], dict(cell.split('=', 1) for cell in parts[3:])))
    return found


def changed_files():
    """本卡分支對合併基底的 `git diff --name-only`；基底物件取不到時**失敗並印出原因**，⛔ 不 skip。"""
    done = subprocess.run(['git', '-C', str(ROOT), 'diff', '--name-only', f'{MERGE_BASE}..HEAD'],
                          capture_output=True, text=True)
    assert done.returncode == 0, (done.returncode, done.stderr)
    return [line for line in done.stdout.splitlines() if line]


# ── 撤銷面：片段定位層的符號⛔ 不得存在 ───────────────────────────────────────────
def test_the_fragment_locating_layer_is_retired():
    for name in RETIRED:
        assert not hasattr(_adopt, name), name
        assert not hasattr(_adopt_manifest, name), name
    assert all('#' not in path for path in _adopt.INSTALL_SET), _adopt.INSTALL_SET
    print('RETIRED', list(RETIRED), 'INSTALL_SET', list(_adopt.INSTALL_SET))


# ── A2 起首：宣告資產集合與實作常數獨立，且必含兩個 CI job 的來源資產 ────────────────
def test_the_declared_asset_set_has_an_independent_lower_bound(tmp_path, env, capsys):
    rows = asset_table()
    assert [row[0] for row in rows] == list(_adopt.ASSET_NAMES), rows
    assert [row[1] for row in rows] == [a.source for a in _adopt.ASSETS], rows
    assert [row[2] for row in rows] == [a.target for a in _adopt.ASSETS], rows
    assert len(ASSET_COLUMNS) == 4, ASSET_COLUMNS
    carriers = [a for a in _adopt.ASSETS if set(REQUIRED_JOBS) <= set(a.content)]
    assert len(carriers) == 1, [(a.name, a.content) for a in _adopt.ASSETS]
    declared = {name for a in _adopt.ASSETS for name in a.content}
    assert not declared & set(EXCLUDED_JOBS), sorted(declared)
    adoption = dict(sections((ROOT / 'ADOPTION.md').read_text(encoding='utf-8')))
    clause, = [row for row in adoption['1 · repo 前置'].splitlines()
               if row.startswith('- `required-status-checks`：')]
    for name in REQUIRED_JOBS:
        assert f'`{name}`' in clause, (name, clause)
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='asset-lower')
    rc, _ = run_step(consumer, 'install')
    capsys.readouterr()
    assert rc == 0
    registered = {e['path'] for e in _adopt.managed_entries(manifest_of(consumer))}
    for asset in _adopt.ASSETS:
        assert (consumer / asset.target).is_file(), asset.target
        assert asset.target in registered, (asset.target, sorted(registered))
    print('ASSET_TABLE', rows, 'required_clause', clause)


def test_the_asset_table_parser_is_effective(tmp_path):
    """負控（必須會響）：合成副本內刪掉表格任一列後，解析出的資產名集合必須少一項。"""
    for victim in _adopt.ASSET_NAMES:
        rules = synthetic(tmp_path, f'asset-{victim}')
        path = Path(rules.identity) / 'core/adopt.md'
        kept = [row for row in path.read_text(encoding='utf-8').splitlines()
                if not row.startswith(f'| `{victim}` |')]
        path.write_text('\n'.join(kept) + '\n', encoding='utf-8')
        names = {row[0] for row in asset_table(rules)}
        assert names == set(_adopt.ASSET_NAMES) - {victim}, (victim, names)
        print('NEGATIVE_CONTROL asset_table dropped', victim, '->', sorted(names))


# ── A2 ①②：install 恰兩個分支，⛔ 無第三種 ────────────────────────────────────────
def start_absent(consumer, victim):
    return None


def start_plain_file(consumer, victim):
    victim.parent.mkdir(parents=True, exist_ok=True)
    victim.write_bytes(b'consumer bytes\n# \xe6\x97\xa2\xe6\x9c\x89\n')
    return None


def start_symlink(consumer, victim):
    outside = consumer.parent / f'victim-{victim.name}'
    outside.write_text('採用者自己的檔，⛔ 不得被寫穿\n', encoding='utf-8')
    victim.parent.mkdir(parents=True, exist_ok=True)
    victim.symlink_to(outside)
    return outside


def start_directory(consumer, victim):
    victim.mkdir(parents=True, exist_ok=True)
    (victim / 'keep.txt').write_text('目錄內既有物\n', encoding='utf-8')
    return None


def start_consumer_owned(consumer, victim):
    """登記為 `consumer-owned` 但樹上⛔ 無該檔：單獨驗登記面那一半的分支 ②。"""
    return None


STARTS = {'absent': start_absent, 'plain_file': start_plain_file,
          'consumer_owned': start_consumer_owned, 'symlink': start_symlink,
          'directory': start_directory}


def prepare(consumer, start):
    outside = {}
    for asset in _adopt.ASSETS:
        found = STARTS[start](consumer, consumer / asset.target)
        if found is not None:
            outside[asset.target] = found
    if start == 'consumer_owned':
        _adopt.write_manifest(consumer, [_adopt.asset_entry(a.target, _adopt.OWNERSHIPS[1], '', '0')
                                         for a in _adopt.ASSETS], None)
    return outside


@pytest.mark.parametrize('start', list(STARTS))
def test_install_lands_whole_files_or_writes_nothing(tmp_path, env, capsys, start):
    """(a) ⛔ 無既有物 ⇒ 整檔落地、恰登記一項、位元組與來源檔逐一相等；
    (b)–(e) ⇒ 該路徑位元組與存在性不變、⛔ 不登記、各印一項未完成項。
    另驗宣告集合以外的路徑零影響（存在性＋SHA-256）。"""
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name=f'branch-{start}')
    outside = prepare(consumer, start)
    before, outside_before = digests(consumer), {k: v.read_bytes() for k, v in outside.items()}
    rc, client = run_step(consumer, 'install')
    out = capsys.readouterr().out
    assert rc == 0, out
    after, manifest = digests(consumer), manifest_of(consumer)
    registered = {e['path'] for e in _adopt.managed_entries(manifest)}
    # 允許面＝宣告的目標路徑，加上為了落地它們而建的祖先目錄（`digests` 把目錄也列進母體）
    targets = {t for t in _adopt.INSTALL_SET}
    targets |= {p.as_posix() for t in _adopt.INSTALL_SET for p in Path(t).parents if p.parts}
    assert {path for path in after if after[path] != before.get(path)} <= targets, (
        sorted(set(after) ^ set(before)), start)
    assert set(before) - set(after) == set(), sorted(set(before) - set(after))
    marks = [item for step, item in pending_items(out) if step == 'install']
    for asset in _adopt.ASSETS:
        target, source_text = consumer / asset.target, (Path(rules) / asset.source).read_bytes()
        if start == 'absent':
            assert target.read_bytes() == source_text, asset.target   # 正控：確有落地，⛔ 非恆零寫入
            assert asset.target in registered, (asset.target, sorted(registered))
            continue
        assert after.get(asset.target) == before.get(asset.target), (start, asset.target)
        assert asset.target not in registered, (start, asset.target, sorted(registered))
        assert [m for m in marks if m['target'] == asset.target], (start, marks)
    for path, victim in outside.items():
        assert victim.read_bytes() == outside_before[path], path   # 符號連結⛔ 不被寫穿
    assert len(marks) == (0 if start == 'absent' else len(_adopt.ASSETS)), (start, marks)
    print('BRANCH', start, 'registered', sorted(registered), 'pending', marks)


# ── A2 ③／A5 ③：未完成項的鍵集合封閉、四值⛔ 非空、規範定位解析得到實際節次 ──────────
def adoption_sections():
    return {head.split(' ')[0] for head, _ in sections((ROOT / 'ADOPTION.md').read_text(encoding='utf-8'))}


def check_pending(item):
    """回 (鍵集合封閉, 四值皆非空, 規範定位解析得到 ADOPTION.md 內實際存在的節次)。"""
    closed = tuple(item) == _adopt.PENDING_KEYS
    filled = all(isinstance(item.get(key), str) and item.get(key) for key in _adopt.PENDING_KEYS)
    section = item.get('section', '')
    number = section.split('§')[-1] if '§' in section else None
    return closed, filled, bool(number) and number in adoption_sections()


def test_every_pending_item_has_the_closed_shape(tmp_path, env, capsys):
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='pending-shape')
    prepare(consumer, 'plain_file')
    run_step(consumer, 'install')
    install_out = capsys.readouterr().out
    run_step(consumer, 'bootstrap')          # `.wf/modules.json` 由合成樹先建 ⇒ 既有起點
    run_step(consumer, 'bootstrap')          # 第二次：階段骨架也成既有起點
    found = pending_items(install_out) + pending_items(capsys.readouterr().out)
    assert {step for step, _ in found} == {'install', 'bootstrap'}, sorted({s for s, _ in found})
    assert len(found) >= len(_adopt.ASSETS) + 1, found
    for step, item in found:
        assert check_pending(item) == (True, True, True), (step, item)
    print('PENDING_SHAPE', len(found), 'keys', list(_adopt.PENDING_KEYS), 'items', found[:4])


@pytest.mark.parametrize('victim', _adopt.PENDING_KEYS)
def test_the_pending_shape_check_is_effective(victim):
    """負控（必須會響）：把任一必要鍵的值清空後，同一個檢查必須轉紅。"""
    good = _adopt.pending('src', 'dst', ('job',), 'ADOPTION.md §1')
    assert check_pending(good) == (True, True, True), good
    assert check_pending({**good, victim: ''}) != (True, True, True), victim
    assert check_pending({**good, 'section': 'ADOPTION.md §99'})[2] is False
    print('NEGATIVE_CONTROL pending blanked', victim)


# ── A2 末段：CI 來源資產與 ci.yml 的整檔 delta（母體＝兩個檔案，⛔ 不經片段解析器）────
def delta_result(ci_text, consumer_text):
    """回 (去掉的 delta 行數, 去掉後是否逐字等於 ci.yml 自 `jobs:` 起的同長度前綴, 該前綴)。"""
    tail = consumer_text.split(JOBS_ANCHOR, 1)[1]
    stripped = tail.replace(DELTA, '')
    anchor = ci_text.index(JOBS_ANCHOR) + len(JOBS_ANCHOR)
    return tail.count(DELTA), stripped == ci_text[anchor:anchor + len(stripped)], stripped


def ci_asset():
    asset, = [a for a in _adopt.ASSETS if set(REQUIRED_JOBS) <= set(a.content)]
    return asset


def test_the_ci_asset_differs_from_ci_yml_by_exactly_the_declared_delta():
    ci_text = (ROOT / CI).read_text(encoding='utf-8')
    consumer_text = (ROOT / ci_asset().source).read_text(encoding='utf-8')
    count, matched, stripped = delta_result(ci_text, consumer_text)
    assert (count, matched) == (2, True), (count, matched)
    for name in REQUIRED_JOBS:                # 前綴自 `  <job>:` 起，故補一個行首再比
        assert f'\n  {name}:\n' in '\n' + stripped, name
    for name in EXCLUDED_JOBS:
        assert f'\n  {name}:\n' not in '\n' + stripped, name
    assert CI not in changed_files(), CI      # 唯讀端：本卡分支⛔ 不改它
    print('DELTA lines', count, 'prefix_bytes', len(stripped), 'excluded', list(EXCLUDED_JOBS))


@pytest.mark.parametrize('side', ['ci', 'consumer'])
def test_the_delta_comparison_is_effective(side):
    """負控（必須會響）：在記憶體副本內改任一側的一行⛔ 非 delta 內容後，同一個判準必須轉紅。"""
    ci_text = (ROOT / CI).read_text(encoding='utf-8')
    consumer_text = (ROOT / ci_asset().source).read_text(encoding='utf-8')
    if side == 'ci':
        ci_text = ci_text.replace('timeout-minutes: 10', 'timeout-minutes: 11', 1)
    else:
        consumer_text = consumer_text.replace('timeout-minutes: 10', 'timeout-minutes: 11', 1)
    count, matched, _ = delta_result(ci_text, consumer_text)
    assert (count, matched) != (2, True), (side, count, matched)
    print('NEGATIVE_CONTROL delta', side, 'count', count, 'matched', matched)


# ── A2 末／A3 ⑥：manifest 雙向、鍵封閉、單一 `path` 文法 ─────────────────────────
def test_the_manifest_has_one_path_grammar_and_maps_both_ways(tmp_path, env, capsys):
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='manifest-shape')
    run_step(consumer, 'install')
    run_step(consumer, 'bootstrap')
    capsys.readouterr()
    manifest = manifest_of(consumer)
    paths = [entry['path'] for entry in manifest['assets']]
    assert len(paths) == len(set(paths)), sorted(paths)
    for entry in manifest['assets']:
        assert tuple(entry) == _adopt.ASSET_KEYS and len(_adopt.ASSET_KEYS) == 4, entry
        assert '#' not in entry['path'], entry
    registered = {e['path']: e for e in _adopt.managed_entries(manifest)}
    for target in _adopt.INSTALL_SET:                     # 方向一：宣告集合每項都有登記
        assert target in registered, (target, sorted(registered))
        assert _adopt.asset_digest(consumer, target) == registered[target]['digest'], target
    for path in registered:                               # 方向二：登記項都在樹上
        assert (consumer / path).is_file(), path
    print('MANIFEST paths', sorted(paths), 'managed', sorted(registered))


# ── 序 2 `R6.2-3`：父目錄符號連結 ⇒ install ⛔ 不跟隨、樹外零寫入 ────────────────────────
PARENT_LINKS = ('.github', '.wf/adopt')          # 兩個宣告集合各一：資產側與控制檔側


@pytest.mark.parametrize('link', PARENT_LINKS)
def test_install_never_follows_a_parent_symlink_out_of_the_tree(tmp_path, env, link):
    """新 A2 逐字「對任何符號連結⛔ 不建立、⛔ 不改寫、⛔ 不跟隨」。缺陷版只查目標**自身**
    `is_symlink()`，`target.parent.mkdir`／`write_bytes`（與控制檔的 `write_text`）仍沿父目錄連結
    寫到樹外：`.github` 連到 sibling ⇒ 樹外 2 檔、`.wf/adopt` 連到 sibling ⇒ 樹外 `manifest.json`，
    rc 均 0。判準是**樹外**目錄的檔案集合前後逐一相等，⛔ 不是看 stdout 說了什麼。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='parent-link-' + link.replace('/', '-'))
    outside = tmp_path / ('outside-' + link.replace('/', '-'))
    outside.mkdir()
    (consumer / link).parent.mkdir(parents=True, exist_ok=True)
    (consumer / link).symlink_to(outside)
    before = digests(outside, skip=())
    rc, _ = run_step(consumer, 'install')
    assert rc == 0                                            # ⛔ 不 raise：本動詞無拒收
    assert digests(outside, skip=()) == before, '樹外零位元組寫入'
    print('PARENT_LINK no_follow', link, 'outside', sorted(before))


def test_a_clean_tree_still_lands_both_assets(tmp_path, env):
    """`R6.2-3` 修法的正控：⛔ 無父連結時兩個宣告資產照樣整檔落地。
    ⛔ 不得以「一律零寫入」通過上一條——那會讓零跟隨判準恆真。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='no-parent-link')
    rc, _ = run_step(consumer, 'install')
    assert rc == 0
    landed = [target for target in _adopt.INSTALL_SET if (consumer / target).is_file()]
    assert landed == list(_adopt.INSTALL_SET), landed
    print('NO_PARENT_LINK landed', landed)
