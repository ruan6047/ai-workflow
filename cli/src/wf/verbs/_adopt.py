"""消費 core/adopt.md §0–§5、core/verbs.md §1 `snapshot` 列（硬擋欄＝「—」：無拒收）／§2、
ADOPTION.md §1／§2／§5。首次採用生命週期五個 step 的本機落地與接線；manifest 與框架資產的宣告住
`_adopt_manifest.py`，診斷的純計算層住 `_adopt_reconcile.py`。本檔對 GitHub 與 Project 的 mutation
原語呼叫序列長度恆為 0：⛔ 不 import `wf.gh.client`／`wf.gh.writes`、⛔ 不碰 client。身分兩項由呼叫端
（`verbs/main.py` 的 `bootstrap()`）把已解析到的物件傳進來；本層⛔ 不自 `Context` 取屬性——WF-015 對
`context.repository` 的消費面零改動。

**CLI ⛔ 不推導採用者 YAML 的插入／移除區間**：`install` 只有整檔落地與零寫入兩個分支，既有物一律零
位元組寫入並交出未完成項，整合由執行者 AI 做、查核者核對（`core/adopt.md` 開頭）。⛔ 不得推出「零
寫入＝採用失敗」——它是把所有權留在採用者手上。
"""
import json
from pathlib import Path

from wf.compose.project_config import load_project_config
from wf.context import rules_of
from wf.verbs._adopt_manifest import (ASSET_KEYS, ASSET_NAMES, ASSETS, CONFIG_PATH, DEFECTS, EXIT_SECTION,
                                      INSTALL_SET, MANIFEST_PATH, MANIFEST_SCHEMA, NO_MANIFEST, OWNERSHIPS,
                                      PENDING_KEYS, SEED_HOME, STAGES_HOME, STAGE_DIR, TOP_KEYS,
                                      VERSION_HOME, Asset, asset_entry, defect_of, digest_of, entries_of,
                                      is_legacy, legacy_entries, managed_entries, pending, read_manifest,
                                      self_digest, write_manifest)
from wf.verbs._adopt_reconcile import (AI_EVIDENCE, GIT_UNAVAILABLE, NOT_FILESYSTEM, NO_CHECKOUT, NO_HEAD,
                                       NO_INDEX, NO_SOURCE_COMMIT, NO_STAGES, NO_VERSION, OUTSIDE_PROJECT,
                                       PREFIX, RECONCILIATION_ITEMS, RULES_IS_PROJECT, SMOKE_AI_ITEMS,
                                       SMOKE_ITEMS, STATIC_IDENTITY_ITEMS, STATUSES, UNRESOLVED, Row,
                                       asset_digest, framework_version, gitlink_facts, gitlink_relative,
                                       identity_rows, item_names, pins_of, preflight_rows, reconcile, render,
                                       smoke_rows, stages_of)

STEPS = ('install', 'preflight', 'bootstrap', 'smoke', 'deactivate')
STEP_PREFIX = '採用'
PENDING_MARK = '未完成項'
OUTSIDE_ROOT = '解析後⛔ 不在 project_root 之下，未刪除'
# 登記路徑是符號連結：解析後再刪是刪錯對象 ⇒ deactivate 零處置。⛔ 不得推出「該路徑越界」——
# 那是 OUTSIDE_ROOT，兩者是不同判準（`core/adopt.md` §5 末兩條）。
SYMLINK_PATH = '該路徑在樹上是符號連結，未移除、未跟隨'
LEGACY_KEPT = f'legacy 登記項，CLI ⛔ 不處置、⛔ 不重寫，依 {EXIT_SECTION} 由 AI 依證據處理'
ABSENT_SOURCE = '來源資產缺席，未落地'
NO_SEED = '種子來源不可讀，未建立'

# 本檔是 `_adopt` 層對外的單一名稱面：`_adopt_manifest` 與 `_adopt_reconcile` 的公開名在此轉出，
# 呼叫端與測試一律 `from wf.verbs import _adopt` 取用（F-執行者-04：`import` 使用、⛔ 不重打常數）。
__all__ = ['ABSENT_SOURCE', 'AI_EVIDENCE', 'ASSETS', 'ASSET_KEYS', 'ASSET_NAMES', 'Asset', 'CONFIG_PATH',
           'DEFECTS', 'EXIT_SECTION', 'GIT_UNAVAILABLE', 'INSTALL_SET', 'LEGACY_KEPT', 'MANIFEST_PATH',
           'MANIFEST_SCHEMA', 'NOT_FILESYSTEM', 'NO_CHECKOUT', 'NO_HEAD', 'NO_INDEX', 'NO_MANIFEST',
           'NO_SEED', 'NO_SOURCE_COMMIT', 'NO_STAGES', 'NO_VERSION', 'OUTSIDE_PROJECT', 'OUTSIDE_ROOT',
           'OWNERSHIPS', 'PENDING_KEYS', 'PENDING_MARK', 'PREFIX', 'RECONCILIATION_ITEMS',
           'RULES_IS_PROJECT', 'Row', 'SEED_HOME', 'SMOKE_AI_ITEMS', 'SMOKE_ITEMS', 'STAGES_HOME',
           'STAGE_DIR', 'STATIC_IDENTITY_ITEMS', 'STATUSES', 'STEPS', 'STEP_PREFIX', 'SYMLINK_PATH',
           'TOP_KEYS', 'UNRESOLVED', 'VERSION_HOME', 'asset_digest', 'asset_entry', 'confined',
           'defect_of', 'digest_of', 'entries_of', 'framework_version', 'gitlink_facts',
           'gitlink_relative', 'identity_rows', 'is_legacy', 'item_names', 'legacy_entries',
           'managed_entries', 'pending', 'pins_of', 'preflight_rows', 'print_scope', 'read_manifest',
           'reconcile', 'render', 'rules_of', 'run_step', 'self_digest', 'smoke_rows', 'stages_of',
           'write_manifest']


def print_scope(scope, emit=print):
    """`verbs/main.py` 三個 bootstrap 失敗分支共用：項名清單與 `--adopt preflight` 逐字相等，**逐項**由該分支實際已解析到的取源決定狀態（⛔ 不連坐）。"""
    for line in render(preflight_rows(scope.get('root'), scope.get('rules'), scope.get('config'),
                                      scope.get('repository'), scope.get('board'))):
        emit(line)


def _say(emit, step, subject, note):
    emit(f'{STEP_PREFIX}・{step}・{subject}・{note}')


def _pending(emit, step, item):
    """未完成項落 stdout，鍵序固定為 `PENDING_KEYS`。⛔ 不摘要、⛔ 不合併多項成一行。"""
    emit(f'{STEP_PREFIX}・{step}・{PENDING_MARK}・'
         + '・'.join(f'{key}={item[key]}' for key in PENDING_KEYS))


def _occupied(target, relative, owned):
    """§2 分支 ②：目標路徑上有既有物（一般檔、目錄、符號連結皆是），或該路徑已是 `consumer-owned`
    登記項。`is_symlink()` 單獨判是刻意的：斷掉的符號連結 `exists()` 為 False，但它仍是既有物。
    **⛔ 不讀該路徑的內容、⛔ 不解析其內部結構**——分支只看「有沒有東西在那裡」。"""
    return target.is_symlink() or target.exists() or relative in owned


def _install_assets(root, source, owned, version, emit):
    """`core/adopt.md` §2 的兩個分支，⛔ 無第三種。回新登記項（只含分支 ① 落地的那些）。"""
    entries = []
    for asset in ASSETS:
        target = root / asset.target
        if _occupied(target, asset.target, owned):
            _pending(emit, 'install',
                     pending(asset.source, asset.target, asset.content, asset.section))
            continue
        try:  # 來源資產本身缺席：印一行、⛔ 不登記，⛔ 不外洩例外型別名
            data = source.read_text(asset.source).encode('utf-8')
        except Exception:
            _say(emit, 'install', asset.source, ABSENT_SOURCE)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append(asset_entry(asset.target, OWNERSHIPS[0], digest_of(data), version))
        _say(emit, 'install', asset.target, '已落地')
    return entries


def step_install(root, rules, config, repository=None, board=None, emit=print, *, runner=None):
    """框架資產整檔落地＋寫 manifest；既有的 `consumer-owned` 與 legacy 登記項原樣保留。
    落地**之前**先讀既有 manifest：⛔ 不得先寫再讀，那會讓 consumer 的位元組先被覆寫。"""
    root, source = Path(root), rules_of(rules)
    index, _, _, _ = gitlink_facts(str(root.resolve()), rules, config, runner=runner)
    version, _ = framework_version(rules)
    previous, _ = read_manifest(root)
    owned = {entry['path'] for entry in entries_of(previous, OWNERSHIPS[1])}
    assets = _install_assets(root, source, owned, version, emit)
    # legacy 項逐字留在 manifest 內（⛔ 不重寫、⛔ 不刪除），並在本次輸出列出一次。
    kept = [entry for entry in (previous or {}).get('assets') or []
            if entry['path'] != MANIFEST_PATH
            and (entry['ownership'] == OWNERSHIPS[1] or is_legacy(entry['path']))]
    for entry in legacy_entries(previous):
        _say(emit, 'install', entry['path'], LEGACY_KEPT)
    write_manifest(root, sorted([*assets, *kept], key=lambda entry: entry['path']), index, version)
    _say(emit, 'install', MANIFEST_PATH, f'source_commit={index}')
    return 0


def _stage_stub(stage):
    return (f'# {stage} · 專案層注意事項（P-）\n\n本檔＝本專案在「{stage}」階段的 P- 注意事項唯一居所'
            f'（`core/naming.md` §4）。條目形狀＝行首一個減號加一個半形空格、`P-{stage}-NN`、全形冒號、'
            f'條文；本檔⛔ 不帶 frontmatter。\n\n## 條目\n\n本檔目前⛔ 無條目。\n')


def _seed(root, rules):
    """`.wf/modules.json` 種子的唯一機器可讀居所＝`SEED_HOME`（⛔ 不在本檔重打、⛔ 不以文件內第 N 個
    json 圍欄或散文行首字串定位）。`rules` 鍵改寫成 bootstrap 當次解析到的 rules root（相對
    project_root），使同一棵樹上⛔ 不帶旗標的 preflight 解析到同一個 rules root；規則就在
    project_root 或在其外時寫 `null`。"""
    try:
        seed = json.loads(rules_of(rules).read_text(SEED_HOME))
    except Exception:
        return None
    try:
        relative = Path(rules.identity).resolve().relative_to(Path(root).resolve())
    except (AttributeError, ValueError, OSError):
        return {**seed, 'rules': None}
    return {**seed, 'rules': {'path': relative.as_posix()} if relative.parts else None}


def _bootstrap_config(root, seed, emit):
    """`.wf/modules.json`：已存在 ⇒ 位元組不變＋一項未完成項；⛔ 不存在且種子可讀 ⇒ 建立。"""
    config_path = root / CONFIG_PATH
    if config_path.exists():
        if seed is None:  # 既有檔位元組不變，但種子不可讀 ⇒ 交不出非空的必要內容識別
            _say(emit, 'bootstrap', CONFIG_PATH, NO_SEED)
        else:
            _pending(emit, 'bootstrap', pending(SEED_HOME, CONFIG_PATH, tuple(seed), 'ADOPTION.md §2'))
        return False
    if seed is None:
        _say(emit, 'bootstrap', CONFIG_PATH, NO_SEED)
        return False
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(seed, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return True


def step_bootstrap(root, rules, config=None, repository=None, board=None, emit=print, *, runner=None):
    """冪等：已存在的路徑一律位元組不變、⛔ 不覆寫、⛔ 不合併，並各交一項未完成項；建立的骨架以
    `consumer-owned` 登記進 manifest。"""
    root, created, owned = Path(root), [], []
    if _bootstrap_config(root, _seed(root, rules), emit):
        created.append(CONFIG_PATH)
    owned += [CONFIG_PATH] if (root / CONFIG_PATH).exists() else []
    for stage in stages_of(rules):
        relative = f'{STAGE_DIR}/{stage}.md'
        if (root / relative).exists():
            _pending(emit, 'bootstrap', pending(STAGES_HOME, relative, (stage,), 'ADOPTION.md §4'))
        else:
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text(_stage_stub(stage), encoding='utf-8')
            created.append(relative)
        owned.append(relative)
    version, _ = framework_version(rules)
    previous, _ = read_manifest(root)
    entries = [entry for entry in (previous or {}).get('assets') or []
               if entry['path'] != MANIFEST_PATH
               and (entry['ownership'] == OWNERSHIPS[0] or is_legacy(entry['path']))]
    for relative in sorted(owned):
        _say(emit, 'bootstrap', relative, '建立' if relative in created else '沿用')
        entries.append(asset_entry(relative, OWNERSHIPS[1],
                                   digest_of((root / relative).read_bytes()), version))
    source = (previous or {}).get('source_commit')
    write_manifest(root, sorted(entries, key=lambda entry: entry['path']),
                   source if isinstance(source, str) else None, version)
    return 0


def step_preflight(root, rules, config, repository=None, board=None, emit=print, *, runner=None):
    for line in render(preflight_rows(root, rules, config, repository, board, runner=runner)):
        emit(line)
    return 0


def step_smoke(root, rules, config=None, repository=None, board=None, emit=print, *, runner=None):
    for line in render(smoke_rows(root, rules, config)):
        emit(line)
    return 0


def confined(root, relative):
    """刪除面封閉在 project_root 之內：絕對路徑、`..`、經符號連結越出者一律回 None。回**⛔ 未解析**的
    `project_root / relative` 本身而⛔ 不是 `resolve()` 後的目標——回目標會在登記路徑是樹內符號連結時刪錯對象（§5）。"""
    base = Path(root).resolve()
    literal = Path(root) / relative
    if literal.name in ('', '.', '..'):
        return None
    try:
        location = literal.parent.resolve() / literal.name
    except (OSError, RuntimeError):
        return None
    return literal if location != base and base in location.parents else None


def step_deactivate(root, rules=None, config=None, repository=None, board=None, emit=print,
                    *, runner=None):
    """只看 manifest 的 `ownership` 欄，⛔ 不看路徑前綴、⛔ 不看副檔名。全樹的差異只有一類：
    `framework-managed` 的**整檔**登記路徑消失。legacy 項與 `consumer-owned` 項逐項列出、零處置。"""
    root = Path(root)
    manifest, absent = read_manifest(root)
    if manifest is None:
        _say(emit, 'deactivate', MANIFEST_PATH, f'{absent}，本次零刪除')
        return 0
    for entry in sorted(managed_entries(manifest), key=lambda entry: entry['path']):
        target = confined(root, entry['path'])
        # 框架⛔ 不落地符號連結 ⇒ 樹上是連結就是 consumer 的，連同其指向的目標一律零處置
        note = OUTSIDE_ROOT if target is None else (SYMLINK_PATH if target.is_symlink() else None)
        if note is not None:
            _say(emit, 'deactivate', entry['path'], note)
            continue
        gone = target.is_file()
        if gone:
            target.unlink()
        _say(emit, 'deactivate', entry['path'], '已移除' if gone else '已不在樹上')
    for entry in legacy_entries(manifest):
        _say(emit, 'deactivate', entry['path'], LEGACY_KEPT)
    for entry in sorted(entries_of(manifest, OWNERSHIPS[1]), key=lambda entry: entry['path']):
        if not is_legacy(entry['path']):
            _say(emit, 'deactivate', entry['path'], f'{OWNERSHIPS[1]}，保留')
    adopt_dir = (root / MANIFEST_PATH).parent
    if adopt_dir.is_dir() and not any(adopt_dir.iterdir()):
        adopt_dir.rmdir()
    return 0


STEP_FUNCTIONS = {'install': step_install, 'preflight': step_preflight, 'bootstrap': step_bootstrap,
                  'smoke': step_smoke, 'deactivate': step_deactivate}


def run_step(step, *, root, rules=None, config=None, repository=None, board=None,
             emit=print, runner=None, **_ignored):
    """`snapshot --adopt <step>` 的唯一入口。rc 恆 0：`core/verbs.md` §1 `snapshot` 列硬擋欄逐字為「—」
    ——本動詞無拒收，結果逐項印、由人或 AI 判（第零條）。`repository`／`board` 缺席時身分兩項標
    `unknown`，其餘項照樣逐項判：⛔ 無遠端身分⛔ 不使本機 step 失敗。"""
    rules = rules_of(rules if rules is not None else root)
    config = load_project_config(root) if config is None else config
    return STEP_FUNCTIONS[step](root, rules, config, repository, board, emit, runner=runner)
