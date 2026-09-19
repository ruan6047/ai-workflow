"""消費 core/adopt.md §1（四列對帳、六個取源 ID、三個 gitlink 取源與 rules root 三分支）／
§2（`framework-version` 彙整規則、片段資產判定）／§3（preflight 七項、smoke 五項與其取源表）。

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
from wf.verbs._adopt_manifest import (CONFIG_PATH, INSTALL_SET, MANIFEST_PATH, NO_MANIFEST,
                                      OWNERSHIPS, STAGE_DIR, VERSION_HOME, digest_of, entries_of,
                                      fragment_of, job_text, read_manifest, self_digest)

STATUSES = ('ok', 'fail', 'unknown')
STATIC_IDENTITY_ITEMS = ('roots', 'repository', 'configured Project')
RECONCILIATION_ITEMS = ('framework-version', 'framework-commit', 'gitlink-committed', 'gitlink-checkout')
SMOKE_ITEMS = ('adopt-manifest', 'managed-assets', 'version-pin', 'project-config', 'stage-notes')
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
    """core/adopt.md §2 的彙整規則四條；回 (唯一版本值|None, 狀態, 理由)。母體**只含**
    `framework-managed` 項：consumer-owned 項的 `pin` 由 `bootstrap` 當次版本寫入，版本升級後
    只重跑 install 會讓兩者並存，把它們算進來等於用 consumer 自己的骨架推翻框架版本。"""
    if manifest is None:
        return None, 'unknown', NO_MANIFEST
    entries = entries_of(manifest, OWNERSHIPS[0])
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
    """§2 的兩類 `path` 各自的摘要：整檔對全部位元組，片段對該 job 的逐字文字。⛔ 無該物回 None。"""
    fragment = fragment_of(path)
    if fragment is None:
        try:
            return digest_of((Path(root) / path).read_bytes())
        except OSError:
            return None
    carrier, name = fragment
    try:
        text = job_text((Path(root) / carrier).read_text(encoding='utf-8'), name)
    except OSError:
        return None
    return None if text is None else digest_of(text.encode('utf-8'))


def _managed_assets_row(root, manifest):
    """雙向判準：應安裝集合的每一項都要①有登記②在樹上且摘要相符；manifest 內的 framework-managed
    項也都要在樹上且摘要相符。manifest 不存在或結構無效時只標 `unknown`（該情形由 §2 承接）。"""
    if manifest is None:
        return Row(SMOKE_ITEMS[1], 'unknown', NO_MANIFEST)
    registered = {e['path']: e for e in entries_of(manifest, OWNERSHIPS[0])}
    bad = [f'{path}（未登記）' for path in INSTALL_SET if path not in registered]
    for path in [*INSTALL_SET, *sorted(registered)]:
        entry = registered.get(path)
        if entry is None or path == MANIFEST_PATH:
            continue
        actual = asset_digest(root, path)
        note = '（缺席）' if actual is None else ('' if actual == entry['digest'] else '（摘要不符）')
        if note and f'{path}{note}' not in bad:
            bad.append(f'{path}{note}')
    return Row(SMOKE_ITEMS[1], 'fail' if bad else 'ok',
               '、'.join(bad) if bad else '應安裝集合與 manifest 雙向齊備且摘要相符')


def _adopt_manifest_row(root, manifest, absent):
    if manifest is None:
        return Row(SMOKE_ITEMS[0], 'unknown', absent)
    listed = [e for e in manifest['assets'] if e['path'] == MANIFEST_PATH]
    if len(listed) != 1:
        return Row(SMOKE_ITEMS[0], 'fail', f'manifest 自身登記項 {len(listed)} 筆，期望 1 筆')
    same = listed[0]['digest'] == self_digest(manifest)
    return Row(SMOKE_ITEMS[0], 'ok' if same else 'fail', f'自身登記項摘要{"相符" if same else "不符"}')


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
    return (_adopt_manifest_row(root, manifest, absent), _managed_assets_row(root, manifest),
            _version_pin_row(rules, manifest), _project_config_row(root),
            _stage_notes_row(root, rules))
