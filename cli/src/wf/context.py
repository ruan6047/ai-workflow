"""Context 值物件、RulesSource 與公開契約形狀；消費 core/verbs.md §2（檢查先於首次遠端寫入、留痕綁被拒的
遠端寫入、身分衝突走本機硬擋零寫入）與 ADOPTION.md §2（`rules`／`remote` 鍵、三個全域旗標）。
三個居所：規則資產只經 `RulesSource` 讀；專案資產（`.wf/`、snapshot 輸出、本機 git 工作樹）只用 `ProjectRoot`；
遠端動詞只消費 `Context.repository`／`project_board`。本層只做身分解析與存在性／相等性比對，⛔ 不判規則
內容、⛔ 不判卡面語意、⛔ 不產統計數字（第零條）。`RulesSource`＝operation-lifetime capability：只承諾列舉
資產、讀內容、穩定 identity、provenance 四件且只在單次 operation 期間可讀；⛔ 無永久 materialization／
copy／cache／install（WF-015）。`public_contract()`／`contract_digest()`＝本契約的單一權威形狀，只用標準庫。
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields
import hashlib
import inspect
import json
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, get_type_hints

if TYPE_CHECKING:  # 只供型別註記；執行期 ⛔ 不 import（避免 compose／gh 與本檔互相 import）
    from wf.compose.blocks import Catalog
    from wf.gh.localgit import LocalGitFacts
    from wf.gh.target import PermissionFact, ProjectIdentity, RepositoryIdentity

PROVENANCE_KINDS = ('cli', 'env', 'project_config', 'git', 'api', 'default')


class ContextError(RuntimeError):
    """bootstrap 期的 typed 失敗：呼叫端印一行並回 rc≠0；⛔ 不是 D 類拒收、⛔ 不寫遠端。"""


class RootError(ContextError):
    """路徑不可讀或無法嚴格 canonicalize（不存在、broken symlink、迴圈）。"""


class RulesSourceError(ContextError):
    """rules source 不可讀、缺 sentinel（`core/*.md`）或資產缺。"""


class IdentityError(ContextError):
    """身分衝突或卡面承載不一致：本機硬擋一行 `硬擋・<code>・<原因>`、零遠端寫入（§2 留痕條：沒有被拒的
    遠端寫入就⛔ 不貼 `wf:reject`）。code＝D 編號。"""
    code = 'D3'


class SourceIssueMismatch(IdentityError):
    """卡面 `source_issue` ≠ 承載該卡的 issue 號。"""


class DuplicateCardId(IdentityError):
    """同一 `card_id` 出現在多個 issue；訊息列出排序穩定的全部 issue 號。"""


class TargetIdentityError(IdentityError):
    """resolved target identity 分裂腦：remote 多義、stable ID 不同、`GH_REPO` 不符、item 不屬本 repo。"""
    code = 'D4'


@dataclass(frozen=True)
class Provenance:
    kind: str    # PROVENANCE_KINDS 之一
    detail: str  # 逐字來源：旗標名、環境變數名、設定鍵、git 取源、API 端點、預設規則


@dataclass(frozen=True)
class Resolved:
    raw: str
    base: str
    canonical: str
    provenance: Provenance


@dataclass(frozen=True)
class ProjectRoot:
    root: Resolved
    config_path: str
    config: dict
    config_provenance: Provenance


class RulesSource(Protocol):
    """恰四成員：identity／provenance 屬性、iter_assets／read_text 方法；⛔ 無 path／materialize／__fspath__。"""
    identity: str
    provenance: Provenance

    def iter_assets(self, pattern: str) -> Iterable[str]:
        """相對路徑（posix、排序穩定）；pattern 逐段比對，語意同 Path.glob。"""
        ...

    def read_text(self, relative: str) -> str:
        """逐字內容（保留原換行）；資產缺＝RulesSourceError。"""
        ...


@dataclass(frozen=True)
class Context:
    project: ProjectRoot
    rules: RulesSource
    catalog: Catalog
    git: LocalGitFacts | None
    repository: RepositoryIdentity
    project_board: ProjectIdentity | None
    permissions: tuple[PermissionFact, ...]
    invocation_cwd: Resolved
    static_identity_verified: bool


def _strict(path, error, what):
    try:
        return Path(path).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise error(f'{what} 不可讀：{path}（{exc}）') from exc


class FilesystemRulesSource:
    """檔案系統 adapter：identity＝`Path.resolve(strict=True)` 的 canonical 路徑（symlink 別名、含 `..`、
    相對寫法解析到同一 identity）；只在本次 operation 期間讀，⛔ 不複製、⛔ 不快取。"""

    def __init__(self, root, provenance=None):
        self._root = _strict(root, RulesSourceError, 'rules root')
        self.identity = str(self._root)
        self.provenance = Provenance('default', 'project_root') if provenance is None else provenance

    def iter_assets(self, pattern):
        return sorted(path.relative_to(self._root).as_posix()
                      for path in self._root.glob(pattern) if path.is_file())

    def read_text(self, relative):
        try:
            with (self._root / relative).open(encoding='utf-8', newline='') as handle:
                return handle.read()
        except OSError as exc:
            raise RulesSourceError(f'規則資產不可讀：{relative}（{self.identity}）') from exc


def open_rules_source(root, provenance):
    """bootstrap 用：嚴格 canonicalize 並驗 sentinel（至少一個 `core/*.md`），否則 typed 失敗。"""
    source = FilesystemRulesSource(root, provenance)
    if not source.iter_assets('core/*.md'):
        raise RulesSourceError(f'rules root 缺 core/*.md：{source.identity}')
    return source


def rules_of(source):
    """RulesSource 或路徑 → RulesSource；動詞層無 context 時（自舉直呼、測試）以 root 當規則來源。"""
    return source if hasattr(source, 'iter_assets') else FilesystemRulesSource(source)


def resolve_path(raw, base, provenance):
    """相對值以 base 解析；canonical＝嚴格 canonicalize；raw／base／provenance 逐字保存（A3）。"""
    canonical = _strict(Path(base) / raw, RootError, provenance.detail)
    return Resolved(str(raw), str(base), str(canonical), provenance)


def default_branch(client, context):
    """A7：預設分支＝resolved repository 的 API 值；無 context（直呼）時取 client 綁定後的值。"""
    return context.repository.default_branch if context is not None else client.default_branch


def static_identity_verified(project, rules, repository, board):
    """static Context gate 恰三項：roots（project_root canonical、rules source 可列舉且 canonical）、repository
    （stable ID 唯一）、configured Project（唯一 node_id 或合法為 null）。輸入已是解析成功的值物件（失敗早已
    raise）；⛔ 不讀 PermissionFact、⛔ 不含任何需 target issue／card／item 的檢查。"""
    roots = bool(project.root.canonical) and bool(rules.identity) and bool(rules.iter_assets('core/*.md'))
    return roots and bool(repository.stable_id) and (board is None or bool(board.node_id))


def public_contract():
    """frozen dataclass 以 dataclasses.fields 取 (name, str(type))；RulesSource Protocol 以 get_type_hints 取
    屬性註記、inspect.signature 取公開 method 簽章（fields 對 Protocol 回空集合，⛔ 不可混用）；只含 JSON primitive。"""
    from wf.gh.localgit import LocalGitFacts, RemoteFact
    from wf.gh.target import (PermissionFact, ProjectIdentity, ProjectItemRef, RepositoryIdentity,
                              TargetIssue)
    classes = (Context, ProjectRoot, Resolved, Provenance, LocalGitFacts, RemoteFact, RepositoryIdentity,
               ProjectIdentity, TargetIssue, ProjectItemRef, PermissionFact)
    contract = {cls.__name__: {f.name: str(f.type) for f in fields(cls)} for cls in classes}
    hints = get_type_hints(RulesSource)
    contract['RulesSource'] = {
        'attributes': {name: getattr(hint, '__name__', str(hint)) for name, hint in hints.items()},
        'methods': {name: str(inspect.signature(getattr(RulesSource, name)))
                    for name in ('iter_assets', 'read_text')}}
    return contract


def contract_digest():
    canonical = json.dumps(public_contract(), sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
