"""消費 core/adopt.md §0–§5、core/verbs.md §1 `snapshot` 列（硬擋欄＝「—」：無拒收）／§2、
ADOPTION.md §1／§2。

首次採用生命週期五個 step 的本機落地與接線；manifest 與片段的純文字層住 `_adopt_manifest.py`，
診斷的純計算層住 `_adopt_reconcile.py`。本檔對 GitHub 與 Project 的 mutation 原語呼叫序列長度恆為 0：
⛔ 不 import `wf.gh.client`／`wf.gh.writes`、⛔ 不碰 client。

身分兩項由呼叫端（`verbs/main.py` 的 `bootstrap()`）把已解析到的物件傳進來；本層⛔ 不自 `Context`
取屬性——WF-015 對 `context.repository` 的消費面零改動（A24 的連帶條款）。
"""
import json
from pathlib import Path

from wf.compose.project_config import load_project_config
from wf.context import rules_of
from wf.verbs._adopt_manifest import (ASSET_KEYS, CARRIER, CONFIG_PATH, DEFECTS, FRAGMENT_SOURCE,
                                      FRAGMENTS, INSTALL_SET, MANAGED_ASSETS, MANIFEST_PATH,
                                      MANIFEST_SCHEMA, NO_MANIFEST, OWNERSHIPS, SEED_HOME, STAGE_DIR,
                                      TOP_KEYS, VERSION_HOME, asset_entry, defect_of, digest_of,
                                      entries_of, fragment_of, job_names, job_span, job_text, read_manifest,
                                      remove_jobs, self_digest, skeleton_of, upsert_job, write_manifest)
from wf.verbs._adopt_reconcile import (GIT_UNAVAILABLE, NOT_FILESYSTEM, NO_CHECKOUT, NO_HEAD,
                                       NO_INDEX, NO_SOURCE_COMMIT, NO_STAGES, NO_VERSION,
                                       OUTSIDE_PROJECT, PREFIX, RECONCILIATION_ITEMS,
                                       RULES_IS_PROJECT, SMOKE_ITEMS, STATIC_IDENTITY_ITEMS,
                                       STATUSES, UNRESOLVED, Row, asset_digest, framework_version,
                                       gitlink_facts, gitlink_relative, identity_rows, item_names,
                                       pins_of, preflight_rows, reconcile, render, smoke_rows,
                                       stages_of)

STEPS = ('install', 'preflight', 'bootstrap', 'smoke', 'deactivate')
STEP_PREFIX = '採用'
OUTSIDE_ROOT = '解析後⛔ 不在 project_root 之下，未刪除'
FOREIGN_JOB = '承載檔內有未登記為 framework-managed 的同名 job，未覆寫'
KEPT_OWNED = f'已登記為 {OWNERSHIPS[1]}，未覆寫'

# 本檔是 `_adopt` 層對外的單一名稱面：`_adopt_manifest` 與 `_adopt_reconcile` 的公開名在此轉出，
# 呼叫端與測試一律 `from wf.verbs import _adopt` 取用（F-執行者-04：`import` 使用、⛔ 不重打常數）。
__all__ = ['ASSET_KEYS', 'CARRIER', 'CONFIG_PATH', 'DEFECTS', 'FOREIGN_JOB', 'FRAGMENTS',
           'FRAGMENT_SOURCE', 'GIT_UNAVAILABLE', 'INSTALL_SET', 'KEPT_OWNED', 'MANAGED_ASSETS',
           'MANIFEST_PATH', 'MANIFEST_SCHEMA', 'NOT_FILESYSTEM', 'NO_CHECKOUT', 'NO_HEAD',
           'NO_INDEX', 'NO_MANIFEST', 'NO_SOURCE_COMMIT', 'NO_STAGES', 'NO_VERSION',
           'OUTSIDE_PROJECT', 'OUTSIDE_ROOT', 'OWNERSHIPS', 'PREFIX', 'RECONCILIATION_ITEMS',
           'RULES_IS_PROJECT', 'Row', 'SEED_HOME', 'SMOKE_ITEMS', 'STAGE_DIR',
           'STATIC_IDENTITY_ITEMS', 'STATUSES', 'STEPS', 'STEP_PREFIX', 'TOP_KEYS', 'UNRESOLVED',
           'VERSION_HOME', 'asset_digest', 'asset_entry', 'confined', 'defect_of', 'digest_of',
           'entries_of', 'fragment_of', 'framework_version', 'gitlink_facts', 'gitlink_relative',
           'identity_rows', 'item_names', 'job_names', 'job_span', 'job_text', 'pins_of',
           'preflight_rows',
           'print_scope', 'read_manifest', 'reconcile', 'remove_jobs', 'render', 'rules_of',
           'run_step', 'self_digest', 'skeleton_of', 'smoke_rows', 'stages_of', 'upsert_job',
           'write_manifest']


def print_scope(scope, emit=print):
    """`verbs/main.py` 三個 bootstrap 失敗分支共用：項名清單與 `--adopt preflight` 逐字相等，
    **逐項**由該分支實際已解析到的取源決定狀態（⛔ 不連坐、⛔ 不整列冒充 `unknown`）。"""
    for line in render(preflight_rows(scope.get('root'), scope.get('rules'), scope.get('config'),
                                      scope.get('repository'), scope.get('board'))):
        emit(line)


def _say(emit, step, subject, note):
    emit(f'{STEP_PREFIX}・{step}・{subject}・{note}')


def _install_files(root, source, owned, version, emit):
    entries = []
    for relative in MANAGED_ASSETS:
        if relative in owned:  # A8：既有 consumer-owned 登記項⛔ 不覆寫、⛔ 不雙重登記
            _say(emit, 'install', relative, KEPT_OWNED)
            continue
        try:
            data = source.read_text(relative).encode('utf-8')
        except Exception:  # 資產缺席：印一行並⛔ 不登記，⛔ 不外洩例外型別名
            _say(emit, 'install', relative, '資產缺席，未落地')
            continue
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_bytes(data)
        entries.append(asset_entry(relative, OWNERSHIPS[0], digest_of(data), version))
        _say(emit, 'install', relative, '已落地')
    return entries


def _install_fragments(root, source, owned, managed, version, emit):
    """片段自片段來源檔**逐字**落地；承載檔缺席時以該來源檔的頂層骨架建立它（⛔ 不另建第二個居所）。
    承載檔內有未登記為 framework-managed 的同名 job 時，本次對承載檔零寫入——刻意整批中止而⛔ 不只跳過
    該一個片段：判準要求「該情形下承載檔位元組逐一不變」，逐片段跳過仍會改到承載檔。"""
    carrier = root / CARRIER
    try:
        source_text = source.read_text(FRAGMENT_SOURCE)
    except Exception:
        _say(emit, 'install', FRAGMENT_SOURCE, '片段來源檔缺席，未落地')
        return []
    existed = carrier.is_file()
    text = carrier.read_text(encoding='utf-8') if existed else skeleton_of(source_text)
    if text is None:
        _say(emit, 'install', FRAGMENT_SOURCE, '片段來源檔⛔ 無頂層骨架，未落地')
        return []
    foreign = [n for n in FRAGMENTS
               if existed and n in set(job_names(text)) and f'{CARRIER}#{n}' not in managed]
    for name in foreign:
        _say(emit, 'install', f'{CARRIER}#{name}', FOREIGN_JOB)
    if foreign:
        return []
    entries = []
    for name in FRAGMENTS:
        if f'{CARRIER}#{name}' in owned:
            _say(emit, 'install', f'{CARRIER}#{name}', KEPT_OWNED)
            continue
        block = job_text(source_text, name)
        if block is None:
            _say(emit, 'install', f'{CARRIER}#{name}', '片段來源檔⛔ 無該 job，未落地')
            continue
        text = upsert_job(text, name, block)
        entries.append(asset_entry(f'{CARRIER}#{name}', OWNERSHIPS[0],
                                   digest_of(block.encode('utf-8')), version))
        _say(emit, 'install', f'{CARRIER}#{name}', '已落地')
    if not entries:
        return []
    carrier.parent.mkdir(parents=True, exist_ok=True)
    carrier.write_text(text, encoding='utf-8')
    if not existed or CARRIER in managed:  # 承載檔由 install 建立 ⇒ 整檔歸框架，deactivate 時整檔消失
        entries.append(asset_entry(CARRIER, OWNERSHIPS[0], digest_of(text.encode('utf-8')), version))
        _say(emit, 'install', CARRIER, '已建立' if not existed else '已更新')
    return entries


def step_install(root, rules, config, repository=None, board=None, emit=print, *, runner=None):
    """framework-managed 資產落地＋寫 manifest；既有的 `consumer-owned` 登記項原樣保留。
    落地**之前**先讀既有 manifest：⛔ 不得先寫再讀，那會讓 consumer 的位元組先被覆寫。"""
    root, source = Path(root), rules_of(rules)
    index, _, _, _ = gitlink_facts(str(root.resolve()), rules, config, runner=runner)
    version, _ = framework_version(rules)
    previous, _ = read_manifest(root)
    owned = {e['path'] for e in entries_of(previous, OWNERSHIPS[1])}
    managed = {e['path'] for e in entries_of(previous, OWNERSHIPS[0])}
    assets = _install_files(root, source, owned, version, emit)
    assets += _install_fragments(root, source, owned, managed, version, emit)
    kept = [e for e in entries_of(previous, OWNERSHIPS[1]) if e['path'] != MANIFEST_PATH]
    write_manifest(root, sorted([*assets, *kept], key=lambda e: e['path']), index, version)
    _say(emit, 'install', MANIFEST_PATH, f'source_commit={index}')
    return 0


def _stage_stub(stage):
    return (f'# {stage} · 專案層注意事項（P-）\n\n本檔＝本專案在「{stage}」階段的 P- 注意事項唯一居所'
            f'（`core/naming.md` §4）。條目形狀＝行首一個減號加一個半形空格、`P-{stage}-NN`、全形冒號、'
            f'條文；本檔⛔ 不帶 frontmatter。\n\n## 條目\n\n本檔目前⛔ 無條目。\n')


def _seed(root, rules):
    """`.wf/modules.json` 種子的唯一居所＝`ADOPTION.md` §2 的第一個 json 區塊（⛔ 不在本檔重打）。
    `rules` 鍵改寫成 bootstrap 當次解析到的 rules root（相對 project_root），使同一棵樹上⛔ 不帶
    旗標的 preflight 解析到同一個 rules root；規則就在 project_root 或在其外時寫 `null`。"""
    try:
        seed = json.loads(rules_of(rules).read_text(SEED_HOME).split('```json\n')[1].split('```')[0])
    except Exception:
        return None
    try:
        relative = Path(rules.identity).resolve().relative_to(Path(root).resolve())
    except (AttributeError, ValueError, OSError):
        return {**seed, 'rules': None}
    return {**seed, 'rules': {'path': relative.as_posix()} if relative.parts else None}


def step_bootstrap(root, rules, config=None, repository=None, board=None, emit=print, *, runner=None):
    """冪等：已存在的檔一律沿用、⛔ 不覆寫；建立的骨架以 `consumer-owned` 登記進 manifest。"""
    root, created, owned = Path(root), [], []
    seed, config_path = _seed(root, rules), root / CONFIG_PATH
    if not config_path.exists() and seed is not None:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(seed, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        created.append(CONFIG_PATH)
    elif not config_path.exists():
        _say(emit, 'bootstrap', CONFIG_PATH, '種子來源不可讀，未建立')
    owned += [CONFIG_PATH] if config_path.exists() else []
    for stage in stages_of(rules):
        relative = f'{STAGE_DIR}/{stage}.md'
        if not (root / relative).exists():
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text(_stage_stub(stage), encoding='utf-8')
            created.append(relative)
        owned.append(relative)
    version, _ = framework_version(rules)
    previous, _ = read_manifest(root)
    entries = [e for e in entries_of(previous, OWNERSHIPS[0]) if e['path'] != MANIFEST_PATH]
    for relative in sorted(owned):
        _say(emit, 'bootstrap', relative, '建立' if relative in created else '沿用')
        entries.append(asset_entry(relative, OWNERSHIPS[1],
                                   digest_of((root / relative).read_bytes()), version))
    source = (previous or {}).get('source_commit')
    write_manifest(root, sorted(entries, key=lambda e: e['path']),
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
    """刪除面封閉在 project_root 之內：絕對路徑、`..`、經符號連結越出者一律回 None。"""
    base = Path(root).resolve()
    try:
        resolved = (Path(root) / relative).resolve()
    except (OSError, RuntimeError):
        return None
    return resolved if resolved != base and base in resolved.parents else None


def _deactivate_files(root, entries, emit):
    for entry in entries:
        target = confined(root, entry['path'])
        if target is None:
            _say(emit, 'deactivate', entry['path'], OUTSIDE_ROOT)
            continue
        gone = target.is_file()
        if gone:
            target.unlink()
        _say(emit, 'deactivate', entry['path'], '已移除' if gone else '已不在樹上')


def _deactivate_fragments(root, entries, emit):
    carriers = {}
    for entry in entries:
        carrier, name = fragment_of(entry['path'])
        carriers.setdefault(carrier, []).append(name)
    for carrier, names in sorted(carriers.items()):
        target = confined(root, carrier)
        note = OUTSIDE_ROOT if target is None else (None if target.is_file() else '承載檔已不在樹上')
        if note is None:
            target.write_text(remove_jobs(target.read_text(encoding='utf-8'), names), encoding='utf-8')
        for name in names:
            _say(emit, 'deactivate', f'{carrier}#{name}', note or '已移除')


def step_deactivate(root, rules=None, config=None, repository=None, board=None, emit=print,
                    *, runner=None):
    """只看 manifest 的 `ownership` 欄，⛔ 不看路徑前綴、⛔ 不看副檔名；整檔項刪路徑、片段項只移除
    片段區間。整檔先於片段：承載檔本身是整檔項時它已消失，其片段⛔ 不再處置。"""
    root = Path(root)
    manifest, absent = read_manifest(root)
    if manifest is None:
        _say(emit, 'deactivate', MANIFEST_PATH, f'{absent}，本次零刪除')
        return 0
    managed = sorted(entries_of(manifest, OWNERSHIPS[0]), key=lambda e: e['path'])
    _deactivate_files(root, [e for e in managed if fragment_of(e['path']) is None], emit)
    _deactivate_fragments(root, [e for e in managed if fragment_of(e['path']) is not None], emit)
    for entry in sorted(entries_of(manifest, OWNERSHIPS[1]), key=lambda e: e['path']):
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
