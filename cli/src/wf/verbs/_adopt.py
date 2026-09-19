"""消費 core/adopt.md §1–§5、core/verbs.md §1 `snapshot` 列（硬擋欄＝「—」：無拒收）／§2、ADOPTION.md §1／§2。

首次採用生命週期五個 step 的純計算與本機落地；`snapshot.py` 只做接線。本檔對 GitHub 與 Project 的
mutation 原語呼叫序列長度恆為 0：⛔ 不 import `wf.gh.client`／`wf.gh.writes`、⛔ 不碰 client。本機 git 的
唯一取源是 `wf.gh.target`（`gitlink_sha` 與既有 `local_git_facts`）——`gh/` 是唯一可 import subprocess 的層
（`cli/tests/test_gh_scope.py`），故本檔⛔ 不自開子程序。單一清單常數：`STATIC_IDENTITY_ITEMS`＋
`RECONCILIATION_ITEMS` 經 `item_names()` 產出項名清單，`--adopt preflight` 與 `verbs/main.py` 三個 bootstrap
失敗分支共用同一份；⛔ 不重打。
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tomllib

from wf.compose.blocks import load_blocks
from wf.compose.project_config import load_project_config
from wf.context import FilesystemRulesSource, rules_of
from wf.gh.localgit import LocalGitUnavailable
from wf.gh.target import gitlink_sha, local_git_facts

STEPS = ('install', 'preflight', 'bootstrap', 'smoke', 'deactivate')
STATUSES, OWNERSHIPS = ('ok', 'fail', 'unknown'), ('framework-managed', 'consumer-owned')
STATIC_IDENTITY_ITEMS = ('roots', 'repository', 'configured Project')
RECONCILIATION_ITEMS = ('framework-version', 'framework-commit', 'gitlink-committed', 'gitlink-checkout')
SMOKE_ITEMS = ('adopt-manifest', 'managed-assets', 'version-pin', 'project-config', 'stage-notes')
ASSET_KEYS = ('path', 'ownership', 'digest', 'pin')
MANIFEST_PATH, MANIFEST_SCHEMA = '.wf/adopt/manifest.json', 'wf-adopt-manifest'
VERSION_HOME, SEED_HOME = 'cli/pyproject.toml', 'ADOPTION.md'
MANAGED_ASSETS = ('.github/scripts/trailer_check.py',)
STAGE_DIR, CONFIG_PATH = '.wf/stages', '.wf/modules.json'
PREFIX, STEP_PREFIX = '採用診斷', '採用'
# 固定措辭：理由字串⛔ 不得含例外類別名（⛔ 不得出現 `Error`、`Traceback` 子字串）——把例外物件轉成字串印出
# 等於把實作細節當成診斷結果。⛔ 不得推出「例外可以照原樣落到輸出」。
UNAVAILABLE = 'bootstrap 未成功，此項不可得'
NO_MANIFEST, NO_SOURCE_COMMIT = 'manifest 不存在或不可解析', 'manifest ⛔ 無 source_commit'
NO_VERSION, GIT_UNAVAILABLE = '現行版本值不可讀', 'git 不可執行'
NO_INDEX, NO_HEAD = 'gitlink 索引側不可得', 'gitlink HEAD 側不可得'
NO_CHECKOUT = '子模組簽出 HEAD 不可得或未初始化'
OUTSIDE_PROJECT, RULES_IS_PROJECT = '規則來源在專案根目錄之外', '規則來源就在專案根目錄，⛔ 無 gitlink'
NOT_FILESYSTEM = '規則來源⛔ 不是檔案系統轉接器'


@dataclass(frozen=True)
class Row:  # 一列診斷；`reason` ⛔ 不帶例外物件、⛔ 不帶堆疊
    name: str
    status: str
    reason: str


def item_names(module_lines=()):
    """preflight 與失敗聚合共用的項名清單（單一居所）。模組列是資料相依的：preflight 可達時
    `ModuleValidation.lines` 必為空，三個失敗分支以空序列呼叫 ⇒ 兩側項名集合逐字相等。"""
    return (*STATIC_IDENTITY_ITEMS, *module_lines, *RECONCILIATION_ITEMS)


def render(rows, prefix=PREFIX):
    return [f'{prefix}・{row.name}・{row.status}・{row.reason}' for row in rows]


def print_unavailable(emit=print, module_lines=()):
    """bootstrap 未成功：項名齊備、一律標 `unknown`（卡面 `non_scope` 逐字「不可證明者明列 unknown」）。"""
    for line in render(Row(name, 'unknown', UNAVAILABLE) for name in item_names(module_lines)):
        emit(line)


def digest_of(data):
    """內容摘要的唯一口徑：`sha256:<hex>`，對 bytes 算。⛔ 不比對 mtime、⛔ 不比對大小。"""
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def self_digest(manifest):
    """manifest 自身那項的摘要前像＝把自己那項的 `digest` 換成空字串後的 canonical JSON。刻意如此：摘要
    自指算不出定值，而 manifest 又必須被登記。⛔ 不得推出「這個摘要涵蓋檔案位元組」——它釘的是內部一致性。"""
    blanked = {**manifest, 'assets': [dict(e, digest='') if e.get('path') == MANIFEST_PATH else e
                                      for e in manifest.get('assets') or []]}
    return digest_of(json.dumps(blanked, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


def read_manifest(root):
    """回 (manifest|None, 理由|None)。不存在或 JSON 不合法一律回 None＋固定理由，⛔ 不 raise。"""
    try:
        value = json.loads((Path(root) / MANIFEST_PATH).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None, NO_MANIFEST
    shaped = isinstance(value, dict) and isinstance(value.get('assets'), list)
    return (value, None) if shaped else (None, NO_MANIFEST)


def write_manifest(root, assets, source_commit, pin):
    """assets＝已排序的四鍵項（⛔ 不含 manifest 自身）；本函式補上 manifest 自身那一項後落檔。"""
    entries = [*assets, {'path': MANIFEST_PATH, 'ownership': OWNERSHIPS[0], 'digest': '', 'pin': pin}]
    manifest = {'schema': MANIFEST_SCHEMA, 'source_commit': source_commit, 'assets': entries}
    entries[-1]['digest'] = self_digest(manifest)
    (path := Path(root) / MANIFEST_PATH).parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def entries_of(manifest, ownership):
    return [entry for entry in (manifest or {}).get('assets') or []
            if isinstance(entry, dict) and entry.get('ownership') == ownership]


def pins_of(manifest):
    """core/adopt.md §2 的彙整規則四條；回 (唯一版本值|None, 狀態, 理由)。⛔ 不以部分資料判 ok。"""
    if manifest is None:
        return None, 'unknown', NO_MANIFEST
    entries = manifest.get('assets') or []
    absent = sorted(str(e.get('path')) for e in entries if not isinstance(e.get('pin'), str) or not e['pin'])
    if absent:
        return None, 'unknown', f'{len(absent)} 項缺 pin：{"、".join(absent)}'
    values = sorted({entry['pin'] for entry in entries})
    if len(values) != 1:
        return (None, 'unknown', 'manifest ⛔ 無資產項') if not values \
            else (None, 'fail', f'pin 混合：{"、".join(values)}')
    return values[0], 'ok', f'pin 唯一：{values[0]}'


def framework_version(rules):
    """版本值唯一居所＝rules source 的 `cli/pyproject.toml` `[project] version`；取不到一律回 (None, 固定
    理由)，⛔ 不猜、⛔ 不回退到別的居所。"""
    try:
        text = rules_of(rules).read_text(VERSION_HOME)
        value = tomllib.loads(text).get('project', {}).get('version')
    except Exception:  # 讀取失敗與 TOML 不合法都只當事實缺席；⛔ 不把例外型別名外洩到輸出
        return None, NO_VERSION
    return (value, None) if isinstance(value, str) and value else (None, NO_VERSION)


def gitlink_relative(project_canonical, rules, config):
    """core/adopt.md §1 的三個分支＋一條邊界；回 (相對路徑|None, 理由|None)。"""
    if not isinstance(rules, FilesystemRulesSource):
        return None, NOT_FILESYSTEM
    if rules.provenance.kind == 'project_config':
        declared = ((config or {}).get('rules') or {}).get('path')
        return (declared, None) if declared else (None, RULES_IS_PROJECT)
    if rules.provenance.kind == 'default':
        return None, RULES_IS_PROJECT
    try:
        relative = Path(rules.identity).relative_to(project_canonical)
    except ValueError:
        return None, OUTSIDE_PROJECT
    return (relative.as_posix(), None) if relative.parts else (None, RULES_IS_PROJECT)


def gitlink_facts(project_canonical, rules, config, *, runner=None):
    """回 (索引側, HEAD 側, 簽出側, 理由|None)。簽出側必須通過 `top_level` 守門才採信：對未初始化的子模組目錄
    直接讀 HEAD 會成功並回 superproject 自己的 HEAD。⛔ 不得推出「目錄存在就代表子模組已初始化」。"""
    relative, reason = gitlink_relative(project_canonical, rules, config)
    if relative is None:
        return None, None, None, reason
    try:
        index, head = gitlink_sha(project_canonical, relative, runner=runner)
        facts = local_git_facts(rules.identity, runner=runner)
    except LocalGitUnavailable:
        return None, None, None, GIT_UNAVAILABLE
    guarded = facts is not None and facts.head_sha and Path(facts.top_level) == Path(rules.identity)
    return index, head, (facts.head_sha if guarded else None), None


def _pair(name, left, right, missing):
    if left is None or right is None:
        return Row(name, 'unknown', missing)
    return Row(name, 'ok', f'兩側相同：{left}') if left == right \
        else Row(name, 'fail', f'不同：{left} ≠ {right}')


def reconcile(manifest, version, index, head, checkout, reason=None):
    """core/adopt.md §1 的四列，逐列只比同一種識別粒度。`reason`＝gitlink 取源不可得時的固定理由。
    ⛔ 不把 `pin`（版本字串）與 gitlink SHA 直接比相等；⛔ 不做 SHA→版本值 映射。"""
    pin, status, detail = pins_of(manifest)
    if status != 'ok':
        rows = [Row(RECONCILIATION_ITEMS[0], status, detail)]
    else:
        rows = [_pair(RECONCILIATION_ITEMS[0], pin, version, NO_VERSION)]
    source = (manifest or {}).get('source_commit')
    if manifest is None:
        rows.append(Row(RECONCILIATION_ITEMS[1], 'unknown', NO_MANIFEST))
    elif not isinstance(source, str):
        rows.append(Row(RECONCILIATION_ITEMS[1], 'unknown', NO_SOURCE_COMMIT))
    else:
        rows.append(_pair(RECONCILIATION_ITEMS[1], source, index, reason or NO_INDEX))
    rows.append(_pair(RECONCILIATION_ITEMS[2], index, head, reason or NO_HEAD))
    rows.append(_pair(RECONCILIATION_ITEMS[3], index, checkout, reason or NO_CHECKOUT))
    return tuple(rows)


def identity_rows(context):
    """static 身分三項各一列。`static_identity_verified` 只回一個 bool，三項哪一項不過不可分辨；本函式把
    同樣三項拆開逐項印，⛔ 不新增第二套判定。"""
    if context is None:
        return tuple(Row(name, 'unknown', UNAVAILABLE) for name in STATIC_IDENTITY_ITEMS)
    rules, board, repository = context.rules, context.project_board, context.repository
    roots = bool(context.project.root.canonical and rules.identity and rules.iter_assets('core/*.md'))
    return (Row(STATIC_IDENTITY_ITEMS[0], 'ok' if roots else 'fail',
                f'project_root={context.project.root.canonical}；rules={rules.identity}'),
            Row(STATIC_IDENTITY_ITEMS[1], 'ok' if repository.stable_id else 'fail',
                f'{repository.name_with_owner}（{repository.stable_id}）'),
            Row(STATIC_IDENTITY_ITEMS[2], 'ok' if board is None or board.node_id else 'fail',
                '設定為 null（合法）' if board is None else f'{board.owner}/{board.number}（{board.node_id}）'))


def preflight_rows(root, rules, config, context=None, module_lines=(), *, runner=None):
    """項名清單＝`item_names(module_lines)`；零寫入（只讀本機檔與唯讀 git 子指令）。"""
    canonical = context.project.root.canonical if context is not None else str(Path(root).resolve())
    manifest, _ = read_manifest(root)
    version, _ = framework_version(rules)
    index, head, checkout, reason = gitlink_facts(canonical, rules, config, runner=runner)
    module = tuple(Row(line, 'fail', '模組宣告或設定不可用') for line in module_lines)
    return (*identity_rows(context), *module, *reconcile(manifest, version, index, head, checkout, reason))


def _stages(rules):
    """階段枚舉的唯一居所＝rules source 的 `core/enums.md`（⛔ 不重打）。讀不到＝空序列。"""
    try:
        enums, = load_blocks(rules_of(rules)).by_label('json wf-enums')
        values = enums.data['stages']['enum']
    except Exception:
        return ()
    return tuple(values) if isinstance(values, list) else ()


def _seed(rules):
    """`.wf/modules.json` 種子的唯一居所＝`ADOPTION.md` §2 的第一個 json 區塊（⛔ 不在本檔重打）。"""
    try:
        return json.loads(rules_of(rules).read_text(SEED_HOME).split('```json\n')[1].split('```')[0])
    except Exception:
        return None


def _stage_stub(stage):
    return (f'# {stage} · 專案層注意事項（P-）\n\n本檔＝本專案在「{stage}」階段的 P- 注意事項唯一居所'
            f'（`core/naming.md` §4）。條目形狀＝行首一個減號加一個半形空格、`P-{stage}-NN`、全形冒號、'
            f'條文；本檔⛔ 不帶 frontmatter。\n\n## 條目\n\n本檔目前⛔ 無條目。\n')


def step_install(root, rules, config, context=None, emit=print, *, runner=None):
    """framework-managed 資產落地＋寫 manifest；既有的 `consumer-owned` 登記項原樣保留。"""
    root, source = Path(root), rules_of(rules)
    canonical = context.project.root.canonical if context is not None else str(root.resolve())
    index, _, _, _ = gitlink_facts(canonical, rules, config, runner=runner)
    version, _ = framework_version(rules)
    assets = []
    for relative in MANAGED_ASSETS:
        try:
            data = source.read_text(relative).encode('utf-8')
        except Exception:  # 資產缺席：印一行並⛔ 不登記，⛔ 不外洩例外型別名
            emit(f'{STEP_PREFIX}・install・{relative}・資產缺席，未落地')
            continue
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_bytes(data)
        assets.append({'path': relative, 'ownership': OWNERSHIPS[0],
                       'digest': digest_of(data), 'pin': version})
        emit(f'{STEP_PREFIX}・install・{relative}・已落地')
    previous, _ = read_manifest(root)
    kept = [e for e in entries_of(previous, OWNERSHIPS[1]) if e.get('path') != MANIFEST_PATH]
    write_manifest(root, sorted([*assets, *kept], key=lambda e: e['path']), index, version)
    emit(f'{STEP_PREFIX}・install・{MANIFEST_PATH}・source_commit={index}')
    return 0


def step_bootstrap(root, rules, config=None, context=None, emit=print, *, runner=None):
    """冪等：已存在的檔一律沿用、⛔ 不覆寫；建立的骨架以 `consumer-owned` 登記進 manifest。"""
    root, created, owned = Path(root), [], []
    seed, config_path = _seed(rules), root / CONFIG_PATH
    if not config_path.exists() and seed is not None:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(seed, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        created.append(CONFIG_PATH)
    elif not config_path.exists():
        emit(f'{STEP_PREFIX}・bootstrap・{CONFIG_PATH}・種子來源不可讀，未建立')
    owned += [CONFIG_PATH] if config_path.exists() else []
    for stage in _stages(rules):
        relative = f'{STAGE_DIR}/{stage}.md'
        if not (root / relative).exists():
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text(_stage_stub(stage), encoding='utf-8')
            created.append(relative)
        owned.append(relative)
    version, _ = framework_version(rules)
    previous, _ = read_manifest(root)
    entries = [e for e in entries_of(previous, OWNERSHIPS[0]) if e.get('path') != MANIFEST_PATH]
    for relative in sorted(owned):
        emit(f'{STEP_PREFIX}・bootstrap・{relative}・{"建立" if relative in created else "沿用"}')
        entries.append({'path': relative, 'ownership': OWNERSHIPS[1],
                        'digest': digest_of((root / relative).read_bytes()), 'pin': version})
    source = (previous or {}).get('source_commit')
    write_manifest(root, sorted(entries, key=lambda e: e['path']),
                   source if isinstance(source, str) else None, version)
    return 0


def step_preflight(root, rules, config, context=None, emit=print, *, runner=None, module_lines=()):
    for line in render(preflight_rows(root, rules, config, context, module_lines, runner=runner)):
        emit(line)
    return 0


def smoke_rows(root, rules, config=None):
    """SMOKE_ITEMS 逐項；每項只讀自己的前提，⛔ 不共用中間結果（項與項須各自獨立翻面）。"""
    root = Path(root)
    manifest, absent = read_manifest(root)
    listed = [e for e in (manifest or {}).get('assets') or []
              if isinstance(e, dict) and e.get('path') == MANIFEST_PATH]
    if manifest is None:
        rows = [Row(SMOKE_ITEMS[0], 'unknown', absent)]
    elif manifest.get('schema') != MANIFEST_SCHEMA:
        rows = [Row(SMOKE_ITEMS[0], 'fail', f'schema 非 {MANIFEST_SCHEMA}')]
    elif len(listed) != 1:
        rows = [Row(SMOKE_ITEMS[0], 'fail', f'manifest 自身登記項 {len(listed)} 筆，期望 1 筆')]
    else:
        same = listed[0].get('digest') == self_digest(manifest)
        rows = [Row(SMOKE_ITEMS[0], 'ok' if same else 'fail',
                    f'自身登記項摘要{"相符" if same else "不符"}')]
    rows += [_smoke_assets(root, manifest), _smoke_version(rules, manifest), _smoke_config(root)]
    stages = _stages(rules)
    gone = [s for s in stages if not (root / f'{STAGE_DIR}/{s}.md').is_file()]
    rows.append(Row(SMOKE_ITEMS[4], 'unknown', '階段枚舉不可讀') if not stages else
                Row(SMOKE_ITEMS[4], 'fail' if gone else 'ok', f'缺 {len(gone)} 檔：{"、".join(gone)}'
                    if gone else f'{len(stages)} 個階段齊備'))
    return tuple(rows)


def _smoke_assets(root, manifest):
    if manifest is None:
        return Row(SMOKE_ITEMS[1], 'unknown', NO_MANIFEST)
    bad = []
    for entry in entries_of(manifest, OWNERSHIPS[0]):
        relative = str(entry.get('path'))
        if relative == MANIFEST_PATH:
            continue
        try:
            actual = digest_of((root / relative).read_bytes())
        except OSError:
            bad.append(f'{relative}（缺檔）')
            continue
        if actual != entry.get('digest'):
            bad.append(f'{relative}（摘要不符）')
    return Row(SMOKE_ITEMS[1], 'fail' if bad else 'ok',
               '、'.join(bad) if bad else 'framework-managed 資產全數存在且摘要相符')


def _smoke_version(rules, manifest):
    version, absent = framework_version(rules)
    pin, status, detail = pins_of(manifest)
    if version is None:
        return Row(SMOKE_ITEMS[2], 'unknown', absent)
    return Row(SMOKE_ITEMS[2], status, detail) if status != 'ok' else \
        Row(SMOKE_ITEMS[2], 'ok' if pin == version else 'fail', f'pin={pin}；現行={version}')


def _smoke_config(root):
    try:
        areas = load_project_config(root).get('areas') or []
    except Exception:  # ProjectConfigError 與讀檔失敗；⛔ 不外洩例外型別名
        return Row(SMOKE_ITEMS[3], 'fail', f'{CONFIG_PATH} 不可解析')
    return Row(SMOKE_ITEMS[3], 'ok' if areas else 'fail',
               f'areas={areas}' if areas else 'areas 為空，卡ID 無法配號')


def step_smoke(root, rules, config=None, context=None, emit=print, *, runner=None):
    for line in render(smoke_rows(root, rules, config)):
        emit(line)
    return 0


def step_deactivate(root, rules=None, config=None, context=None, emit=print, *, runner=None):
    """只看 manifest 的 `ownership` 欄，⛔ 不看路徑前綴、⛔ 不看副檔名。"""
    root = Path(root)
    manifest, absent = read_manifest(root)
    if manifest is None:
        emit(f'{STEP_PREFIX}・deactivate・{MANIFEST_PATH}・{absent}，本次零刪除')
        return 0
    for entry in sorted(entries_of(manifest, OWNERSHIPS[0]), key=lambda e: str(e.get('path'))):
        path = root / str(entry.get('path'))
        gone = path.is_file()
        if gone:
            path.unlink()
        emit(f'{STEP_PREFIX}・deactivate・{entry.get("path")}・{"已移除" if gone else "已不在樹上"}')
    for entry in sorted(entries_of(manifest, OWNERSHIPS[1]), key=lambda e: str(e.get('path'))):
        emit(f'{STEP_PREFIX}・deactivate・{entry.get("path")}・consumer-owned，保留')
    adopt_dir = (root / MANIFEST_PATH).parent
    if adopt_dir.is_dir() and not any(adopt_dir.iterdir()):
        adopt_dir.rmdir()
    return 0


STEP_FUNCTIONS = {'install': step_install, 'preflight': step_preflight, 'bootstrap': step_bootstrap,
                  'smoke': step_smoke, 'deactivate': step_deactivate}


def run_step(step, *, root, rules=None, config=None, context=None, emit=print, runner=None):
    """`snapshot --adopt <step>` 的唯一入口。rc 恆 0：`core/verbs.md` §1 `snapshot` 列硬擋欄逐字為「—」
    ——本動詞無拒收，結果逐項印、由人或 AI 判（第零條）。"""
    rules = rules_of(rules if rules is not None else (context.rules if context is not None else root))
    config = load_project_config(root) if config is None else config
    return STEP_FUNCTIONS[step](root, rules, config, context, emit, runner=runner)
