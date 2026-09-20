"""消費 core/adopt.md §1（四列對帳、六個取源 ID、三個 gitlink 取源與 rules root 三分支）／
§2（`framework-version` 彙整規則、legacy 判定）／§3（preflight 七項、smoke 七項與其類別／取源表）。

本檔是採用診斷的**純計算**層：只讀本機檔與唯讀 git 子指令，對 GitHub 與 Project 的 mutation 原語
呼叫序列長度恆為 0（⛔ 不 import `wf.gh.client`／`wf.gh.writes`）。本機 git 的唯一取源是
`wf.gh.target`——`gh/` 是唯一可 import subprocess 的層（`cli/tests/test_gh_scope.py`），故本檔
⛔ 不自開子程序。

身分兩項（`repository`、`configured Project`）由呼叫端把**已解析到的物件**傳進來，本檔⛔ 不自
`Context` 取屬性：WF-015 對 `context.repository` 的消費面零改動（本卡 A24 的連帶條款）。
"""
from dataclasses import dataclass
from pathlib import Path
import tomllib

from wf.compose.blocks import load_blocks
from wf.compose.project_config import load_project_config
from wf.context import FilesystemRulesSource, rules_of
from wf.gh.localgit import LocalGitUnavailable
from wf.gh.target import gitlink_sha, local_git_facts
from wf.verbs._adopt_manifest import (ASSETS, CONFIG_PATH, EXIT_SECTION, INSTALL_SET, MANIFEST_PATH,
                                      NO_MANIFEST, OWNERSHIPS, STAGE_DIR, VERSION_HOME, digest_of,
                                      entries_of, legacy_entries, managed_entries, read_manifest)

STATUSES = ('ok', 'fail', 'unknown')
STATIC_IDENTITY_ITEMS = ('roots', 'repository', 'configured Project')
RECONCILIATION_ITEMS = ('framework-version', 'framework-commit', 'gitlink-committed', 'gitlink-checkout')
SMOKE_ITEMS = ('adopt-manifest', 'managed-assets', 'version-pin', 'project-config', 'stage-notes',
               'pending-integration', 'legacy-entries')
# `core/adopt.md` §3 的（乙）類：須由 AI 判定的整合結果。這些項**一律**標 `unknown`、⛔ 不得標 `ok`，
# 並印出判定所需的證據種類——CLI ⛔ 不得對採用者既有檔案內由 AI 整合的內容宣稱已驗證其正確性。
# ⛔ 不得推出「湊齊證據後 CLI 就可以改標 `ok`」：判定者是查核者，⛔ 不是本層。
SMOKE_AI_ITEMS = ('pending-integration', 'legacy-entries')
AI_EVIDENCE = '證據種類：目標檔逐字內容、來源資產逐字內容、兩者的必要內容識別對照'
# `core/adopt.md` §3（甲-c）的逐字措辭。本列⛔ 不自行重印 job 名：必要內容識別只有一個居所，
# 即（乙）類 `pending-integration`；兩列各留一份會漂。
UNREGISTERED_OCCUPANT = '既有物・未登記・見 pending-integration'
PREFIX = '採用診斷'
# 固定措辭：理由字串⛔ 不得含例外類別名（⛔ 不得出現 `Error`、`Traceback` 子字串）——把例外物件轉成
# 字串印出等於把實作細節當成診斷結果。⛔ 不得推出「例外可以照原樣落到輸出」。
UNRESOLVED = '本次執行尚未解析到此項的取源'
NO_SOURCE_COMMIT = 'manifest ⛔ 無 source_commit'
NO_VERSION, GIT_UNAVAILABLE = '現行版本值不可讀', 'git 不可執行'
NO_INDEX, NO_HEAD = 'gitlink 索引側不可得', 'gitlink HEAD 側不可得'
NO_CHECKOUT = '子模組簽出 HEAD 不可得或未初始化'
OUTSIDE_PROJECT, RULES_IS_PROJECT = '規則來源在專案根目錄之外', '規則來源就在專案根目錄，⛔ 無 gitlink'
NOT_FILESYSTEM = '規則來源⛔ 不是檔案系統轉接器'
NO_STAGES = '階段枚舉不可讀'


@dataclass(frozen=True)
class Row:  # 一列診斷；`reason` ⛔ 不帶例外物件、⛔ 不帶堆疊
    name: str
    status: str
    reason: str


def item_names():
    """preflight 與三個 bootstrap 失敗分支共用的項名清單（單一居所、恰七項、順序固定）。
    ⛔ 不含資料相依的 `ModuleValidation.lines` 列——那一份由 `verbs/main.py` 自己逐條印。"""
    return (*STATIC_IDENTITY_ITEMS, *RECONCILIATION_ITEMS)


def render(rows, prefix=PREFIX):
    return [f'{prefix}・{row.name}・{row.status}・{row.reason}' for row in rows]


def pins_of(manifest):
    """core/adopt.md §2 的彙整規則四條；回 (唯一版本值|None, 狀態, 理由)。母體**只含 `framework-managed`
    且⛔ 非 legacy** 的項：consumer-owned 項的 `pin` 由 `bootstrap` 當次版本寫入，版本升級後只重跑
    install 會讓兩者並存，把它們算進來等於用 consumer 自己的骨架推翻框架版本；legacy 項是已退休機制的
    殘留，CLI ⛔ 不處置它，也⛔ 不讓它的舊 `pin` 翻掉現行資產的版本對帳。"""
    if manifest is None:
        return None, 'unknown', NO_MANIFEST
    entries = managed_entries(manifest)
    absent = sorted(str(e.get('path')) for e in entries if not e.get('pin'))
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
    if rules is None:
        return None, NO_VERSION
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
    if project_canonical is None:
        return None, None, None, UNRESOLVED
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
    """core/adopt.md §1 的四列，逐列只比同一種識別粒度、逐列獨立取源。
    ⛔ 不把 `pin`（版本字串）與 gitlink SHA 直接比相等；⛔ 不做 SHA→版本值 映射。"""
    pin, status, detail = pins_of(manifest)
    rows = [Row(RECONCILIATION_ITEMS[0], status, detail) if status != 'ok'
            else _pair(RECONCILIATION_ITEMS[0], pin, version, NO_VERSION)]
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


def identity_rows(root, rules, config, repository, board):
    """static 身分三項各一列，逐項獨立降級（⛔ 不連坐）：某項的取源在本次執行已解析到就⛔ 不得標
    `unknown`，任一取源不可得才標 `unknown`。"""
    if root is None or rules is None:
        roots = Row(STATIC_IDENTITY_ITEMS[0], 'unknown', UNRESOLVED)
    else:
        ok = bool(rules.identity and rules.iter_assets('core/*.md'))
        roots = Row(STATIC_IDENTITY_ITEMS[0], 'ok' if ok else 'fail',
                    f'project_root={root}；rules={rules.identity}')
    if repository is None:
        repo_row = Row(STATIC_IDENTITY_ITEMS[1], 'unknown', UNRESOLVED)
    else:
        repo_row = Row(STATIC_IDENTITY_ITEMS[1], 'ok' if repository.stable_id else 'fail',
                       f'{repository.name_with_owner}（{repository.stable_id}）')
    if board is not None:
        project = Row(STATIC_IDENTITY_ITEMS[2], 'ok' if board.node_id else 'fail',
                      f'{board.owner}/{board.number}（{board.node_id}）')
    elif config is not None and config.get('project') is None:
        project = Row(STATIC_IDENTITY_ITEMS[2], 'ok', '設定為 null（合法）')
    else:
        project = Row(STATIC_IDENTITY_ITEMS[2], 'unknown', UNRESOLVED)
    return roots, repo_row, project


def preflight_rows(root, rules, config, repository=None, board=None, *, runner=None):
    """項名清單＝`item_names()`（恰七項）；零寫入（只讀本機檔與唯讀 git 子指令）。"""
    canonical = None if root is None else str(Path(root).resolve())
    manifest, _ = (None, None) if root is None else read_manifest(root)
    version, _ = framework_version(rules)
    index, head, checkout, reason = gitlink_facts(canonical, rules, config, runner=runner)
    return (*identity_rows(canonical, rules, config, repository, board),
            *reconcile(manifest, version, index, head, checkout, reason))


def stages_of(rules):
    """階段枚舉的唯一居所＝rules source 的 `core/enums.md`（⛔ 不重打）。讀不到＝空序列。"""
    try:
        enums, = load_blocks(rules_of(rules)).by_label('json wf-enums')
        values = enums.data['stages']['enum']
    except Exception:
        return ()
    return tuple(values) if isinstance(values, list) else ()


def asset_digest(root, path):
    """§2 的單一 `path` 文法：整檔，前像是該檔的全部位元組。⛔ 無該物回 None。
    ⛔ 不接受第二種文法——片段粒度的前像契約已隨片段機制退休。"""
    try:
        return digest_of((Path(root) / path).read_bytes())
    except OSError:
        return None


def _member(root, registered, path):
    """§3 的全函數：對母體每一個成員回 (狀態, 理由)，恰三種情形、⛔ 無第四種。
    **母體是 `INSTALL_SET`、⛔ 不因樹或 manifest 的狀態收窄**——以「已登記者」定義母體會使本列恆真。"""
    entry = registered.get(path)
    if entry is None:                                   # ⛔ 無 framework-managed 登記
        if asset_digest(root, path) is None:
            return 'fail', '未登記・樹上⛔ 不存在'       # （甲-b）既未落地也未整合
        # （甲-c）走過 §2 分支 ② 的零寫入。必要內容識別（job 名）只有一個居所＝`pending-integration`，
        # 本列⛔ 不自行重印：兩列對同一路徑各留一份 job 名會漂。
        return 'unknown', UNREGISTERED_OCCUPANT
    actual = asset_digest(root, path)                   # （甲-a）登記在案 ⇒ 雙向都要成立
    if actual is None:
        return 'fail', '已登記・樹上缺席'
    return ('ok', '已登記・整檔摘要相符') if actual == entry['digest'] \
        else ('fail', '已登記・整檔摘要⛔ 不符')


def _managed_assets_rows(root, manifest):
    """成員行在前、該項的狀態行在後（§3）：狀態行取成員狀態的最劣者。同一個項名重複印是刻意的——
    逐成員印出它落在哪一種情形是 §3 的逐字要求，而該項在取源矩陣裡仍是**一個**項。"""
    registered = {entry['path']: entry for entry in managed_entries(manifest)}
    members = [(path, *_member(root, registered, path)) for path in INSTALL_SET]
    rows = [Row(SMOKE_ITEMS[1], status, f'{path}・{note}') for path, status, note in members]
    seen = {status for _, status, _ in members}
    worst = 'fail' if 'fail' in seen else ('unknown' if 'unknown' in seen else 'ok')
    return (*rows, Row(SMOKE_ITEMS[1], worst,
                       f'母體 {len(members)} 項・{"、".join(sorted(seen))}'))


def _pending_integration_row(manifest):
    """（乙）類：`install` 走了零寫入分支的資產，其內容整合在採用者既有檔案內，機械上無法確認。
    **一律 `unknown`**；只印待整合清單與證據種類。取源只有 `manifest.file`：⛔ 不讀樹，否則
    「刪掉已落地資產」也會翻動本項，那條翻面屬 `tree.assets` 的消費項 `managed-assets`。"""
    if manifest is None:
        return Row(SMOKE_ITEMS[5], 'unknown', f'{NO_MANIFEST}；{AI_EVIDENCE}')
    registered = {entry['path'] for entry in managed_entries(manifest)}
    # **必要內容識別（CI 資產＝job 名）只有這一個居所**（§3）：`managed-assets` ⛔ 不自行重印它，
    # 否則兩列對同一路徑各留一份會漂。⛔ 不得推出「印出 job 名＝已驗證它在位」——本項恆 `unknown`。
    outstanding = [f'{asset.target}（{"、".join(asset.content)}）'
                   for asset in ASSETS if asset.target not in registered]
    body = '、'.join(outstanding) if outstanding else '⛔ 無待整合資產'
    return Row(SMOKE_ITEMS[5], 'unknown', f'待整合 {len(outstanding)} 項：{body}；{AI_EVIDENCE}')


def _legacy_entries_row(manifest):
    """（乙）類：`path` 含 `#` 的 legacy 登記項。CLI 只列出並指向退場節，⛔ 不處置、⛔ 不重寫。"""
    if manifest is None:
        return Row(SMOKE_ITEMS[6], 'unknown', f'{NO_MANIFEST}；{AI_EVIDENCE}')
    found = [entry['path'] for entry in legacy_entries(manifest)]
    body = '、'.join(found) if found else '⛔ 無 legacy 登記項'
    return Row(SMOKE_ITEMS[6], 'unknown',
               f'legacy {len(found)} 項：{body}；依 {EXIT_SECTION} 由 AI 依證據處理；{AI_EVIDENCE}')


def _adopt_manifest_row(manifest, absent):
    """語意恰為：控制檔存在且合 §2 結構宣告 ⇒ `ok`，否則⛔ 非 `ok`。**⛔ 不比對控制檔自身的內容摘要**
    ——方案 A 下控制檔⛔ 不自登記，⛔ 無自指摘要、⛔ 不得再有第二種 `digest` 前像文法。"""
    return Row(SMOKE_ITEMS[0], 'unknown', absent) if manifest is None \
        else Row(SMOKE_ITEMS[0], 'ok', f'{MANIFEST_PATH} 存在且合 §2 結構宣告')


def _version_pin_row(rules, manifest):
    version, absent = framework_version(rules)
    pin, status, detail = pins_of(manifest)
    if version is None:
        return Row(SMOKE_ITEMS[2], 'unknown', absent)
    return Row(SMOKE_ITEMS[2], status, detail) if status != 'ok' else \
        Row(SMOKE_ITEMS[2], 'ok' if pin == version else 'fail', f'pin={pin}；現行={version}')


def _project_config_row(root):
    try:
        areas = load_project_config(root).get('areas') or []
    except Exception:  # ProjectConfigError 與讀檔失敗；⛔ 不外洩例外型別名
        return Row(SMOKE_ITEMS[3], 'fail', f'{CONFIG_PATH} 不可解析')
    return Row(SMOKE_ITEMS[3], 'ok' if areas else 'fail',
               f'areas={areas}' if areas else 'areas 為空，卡ID 無法配號')


def _stage_notes_row(root, rules):
    stages = stages_of(rules)
    if not stages:
        return Row(SMOKE_ITEMS[4], 'unknown', NO_STAGES)
    gone = [s for s in stages if not (Path(root) / f'{STAGE_DIR}/{s}.md').is_file()]
    return Row(SMOKE_ITEMS[4], 'fail' if gone else 'ok',
               f'缺 {len(gone)} 檔：{"、".join(gone)}' if gone else f'{len(stages)} 個階段齊備')


def smoke_rows(root, rules, config=None):
    """SMOKE_ITEMS 逐項；每項只讀 `core/adopt.md` §3 取源表宣告的那些取源（項與項須各自獨立翻面）。"""
    manifest, absent = read_manifest(root)
    return (_adopt_manifest_row(manifest, absent), *_managed_assets_rows(root, manifest),
            _version_pin_row(rules, manifest), _project_config_row(root),
            _stage_notes_row(root, rules), _pending_integration_row(manifest),
            _legacy_entries_row(manifest))
