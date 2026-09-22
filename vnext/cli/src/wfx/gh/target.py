"""resolved target identity：任務識別、repository 與 Project 的解析，以及權限三態事實。

remote precedence 四段：①設定鍵 `remote` ②current branch upstream ③唯一 remote ④全部 remote
（同一 repository 才合併、仍多義即 fail-loud）。`GH_REPO` ⛔ 不在 precedence 內：本機身分缺席時成唯一候選。
permission 只產事實（allowed／denied／unknown）、⛔ 不做政策、⛔ 不以 probe mutation 驗權限。
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from wfx.core.context import Provenance
from wfx.gh.client import PermissionDenied
from wfx.gh.localgit import remote_facts

SLUG_URL = re.compile(r'^(?:[a-z+]+://)?(?:[^@/]+@)?github\.com[/:]([^/:]+/[^/:]+?)(?:\.git)?/?$')
SLUG_PLAIN = re.compile(r'^[^/\s]+/[^/\s]+$')
TASK_ID = re.compile(r'^(?:(?P<slug>[^/\s#]+/[^/\s#]+)?#?)(?P<number>\d+)$')
PERMISSION_STATES = ('allowed', 'denied', 'unknown')
WRITE_LEVELS = ('WRITE', 'MAINTAIN', 'ADMIN')  # GitHub viewerPermission 自身定義的可寫層級


class TargetError(RuntimeError):
    """目標身分無法解析或多義；本機硬擋，⛔ 不猜。"""


@dataclass(frozen=True)
class TaskRef:
    """`--task` 的 GitHub 解讀：`370`／`#370`／`owner/name#370`。核心層只把它當不透明字串。"""
    slug: str | None
    number: int
    raw: str


@dataclass(frozen=True)
class RepositoryTarget:
    slug: str
    remote_names: tuple[str, ...]
    provenance: Provenance


@dataclass(frozen=True)
class PermissionFact:
    subject: str
    state: str
    source: str
    reason: str


def parse_task(task_id) -> TaskRef:
    match = TASK_ID.match((task_id or '').strip())
    if match is None:
        raise TargetError(f'--task 形狀無法解讀為 GitHub 任務：{task_id!r}（收 370／#370／owner/name#370）')
    return TaskRef(match['slug'], int(match['number']), task_id)


def slug_of(url):
    """github.com 的 `owner/name`；別的主機或形狀＝None（⛔ 不猜）。"""
    match = SLUG_URL.match(url or '')
    return match[1] if match else None


def same_repository(left, right):
    """GitHub 的 owner／name 大小寫不敏感：`o/r` 與 `O/R` 是同一個 repository（同一 node id）。

    只做 GitHub slug 的身分比對，⛔ 不改寫任何人給的字面、⛔ 不做通用 URL 正規化。
    """
    return left is not None and right is not None and left.lower() == right.lower()


def _candidates(remotes, configured):
    by_name = {remote.name: remote for remote in remotes}
    if configured is not None:
        if configured not in by_name:
            raise TargetError(f'remote 不存在：{configured}（來源 project_config:remote）')
        return (by_name[configured],), Provenance('project_config', 'remote')
    upstream = tuple(remote for remote in remotes if remote.is_upstream_of_current)
    if upstream:
        return upstream, Provenance('git', 'current branch upstream')
    return tuple(remotes), Provenance('git', 'sole remote' if len(remotes) == 1 else 'all remotes')


def _group_by_repository(candidates):
    """把候選依 GitHub 的 repository 身分分組，回 [(顯示 slug, [remote 名稱…])…]。

    等價定義**只有** `same_repository()`：⛔ 不另立第二套正規化或大小寫敏感的 dict key——
    多一套等價定義就是把同一個缺陷搬到下一個角落（`remote_names_for`／`locate_item` 已走它）。
    顯示 slug 取每組第一個候選的字面，順序沿用 precedence，因此 deterministic 且⛔ 不改寫任何人的寫法。
    """
    groups = []
    for remote in candidates:
        slug = slug_of(remote.fetch_url)
        if slug is None:
            continue
        for group_slug, names in groups:
            if same_repository(group_slug, slug):
                names.append(remote.name)
                break
        else:
            groups.append((slug, [remote.name]))
    return groups


def resolve_repository(root, *, configured=None, env_repo=None, runner=None) -> RepositoryTarget:
    """候選指向**多個 repository** 時＝fail-loud（列出每個候選與其 remote）；同一個 repository
    的多個 remote（含只差 owner／name 大小寫的寫法）合併成一個身分，⛔ 不誤報多義。
    `remote_names` 供本機 remote-tracking ref 取源，⛔ 不寫死 `origin`。"""
    remotes = remote_facts(root, runner=runner)
    candidates, provenance = _candidates(remotes or (), configured)
    found = _group_by_repository(candidates)
    if not found:
        if env_repo and SLUG_PLAIN.match(env_repo):
            return RepositoryTarget(env_repo, (), Provenance('env', 'GH_REPO'))
        raise TargetError('未能取得 repository：設 GH_REPO，或在有 github.com remote 的 git 工作樹內執行')
    if len(found) > 1:
        raise TargetError('repository 候選不唯一：' + '；'.join(
            f'{slug}←{"、".join(names)}' for slug, names in sorted(found)))
    (slug, names), = found
    detail = provenance.detail + ('' if len(names) == 1 else '（合併 ' + '、'.join(names) + '）')
    if env_repo and SLUG_PLAIN.match(env_repo) and env_repo != slug:
        raise TargetError(f'GH_REPO {env_repo} ≠ resolved {slug}')
    return RepositoryTarget(slug, tuple(names), Provenance(provenance.kind, detail))


def remote_names_for(root, slug, *, configured=None, runner=None) -> tuple[str, ...]:
    """repository 身分**已由呼叫端給定**時的本機 remote-tracking ref 候選。

    走與 `resolve_repository` 同一組 precedence 候選、再逐個比對 fetch URL 的 slug
    （大小寫不敏感＝GitHub 自己的 repository 身分語意），因此 `370`、`o/name#370` 與
    `O/Name#370` 對同一 repository 拿到同一組候選（否則完整寫法會退回較舊的
    `refs/heads/<base>`）。本機不是 git 工作樹、或⛔ 無指向該 repository 的
    remote 時回 ()＝事實缺席。precedence 本身不成立（設定鍵指向不存在的 remote）
    照樣 fail-loud，⛔ 不因為身分已知就靜默改用別的候選——那就是同一個缺陷換個角落。
    """
    candidates, _ = _candidates(remote_facts(root, runner=runner) or (), configured)
    return tuple(remote.name for remote in candidates
                 if same_repository(slug_of(remote.fetch_url), slug))


def permission_fact(subject, source, value):
    """value＝API 欄位值（bool／viewerPermission／缺欄位＝None）或讀取時的例外；只翻譯成事實。
    true／false、WRITE 以上／以下＝allowed／denied；403 ⇒ denied；
    401、404、傳輸未完成、缺欄位 ⇒ unknown（未知⛔ 不冒充允許或拒絕）。"""
    if isinstance(value, bool):
        return PermissionFact(subject, 'allowed' if value else 'denied', source, f'{source}={value!r}')
    if isinstance(value, str):
        return PermissionFact(subject, 'allowed' if value in WRITE_LEVELS else 'denied', source,
                              f'{source}={value}')
    if value is None:
        return PermissionFact(subject, 'unknown', source, f'{source} 缺欄位')
    if isinstance(value, PermissionDenied):
        status = re.search(r'HTTP\s+(\d{3})', str(value))
        state = 'unknown' if status is not None and status[1] == '401' else 'denied'
        return PermissionFact(subject, state, source, f'{type(value).__name__}: {value}')
    return PermissionFact(subject, 'unknown', source, f'{type(value).__name__}: {value}')
