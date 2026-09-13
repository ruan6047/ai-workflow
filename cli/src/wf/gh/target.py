"""消費 core/verbs.md §2（檢查先於首次遠端寫入；身分衝突走本機硬擋零寫入）、ADOPTION.md §2
（`remote`／`project` 鍵）。resolved target identity 的解析：remote precedence ①顯式 `--remote`
②設定鍵 ③current branch upstream ④全部 remote（唯一者即選定，多者經 API canonical stable ID 合併，
ID 相同才合併、仍多義即 fail-loud）；`GH_REPO` 不在 precedence 內（本機身分缺席時成唯一候選，否則
只作 stable ID 核對）；Project 與 repository 的最低關聯＝被操作 item 的 content.repository stable ID
等於 resolved repository（Project 可跨 repo、不要求 owner 相同、project:null 合法）；permission 只產
`PermissionFact` 事實、⛔ 不做政策（逐 operation 放行或阻擋由 WF-016 決定）。

比對一律用 stable ID（node_id）；本層只做身分解析與相等性比對；⛔ 不建 dependency solver、
⛔ 不耦合具名 consumer、⛔ 不支援 GHES（host 固定 github.com）。
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from wf.context import ContextError, Provenance, TargetIdentityError
from wf.gh.client import GhError, PermissionDenied

SLUG = re.compile(r'^(?:[a-z+]+://)?(?:[^@/]+@)?github\.com[/:]([^/:]+/[^/:]+?)(?:\.git)?/?$')
PERMISSION_STATES = ('allowed', 'denied', 'unknown')


@dataclass(frozen=True)
class RepositoryIdentity:
    stable_id: str
    name_with_owner: str
    default_branch: str
    provenance: Provenance


@dataclass(frozen=True)
class RepositoryCandidate:
    slug: str
    provenance: Provenance


@dataclass(frozen=True)
class ProjectIdentity:
    node_id: str
    owner: str
    number: int
    provenance: Provenance


@dataclass(frozen=True)
class TargetIssue:
    number: int
    node_id: str | None
    repository_name_with_owner: str | None
    provenance: Provenance


@dataclass(frozen=True)
class ProjectItemRef:
    item_id: str
    repository_stable_id: str | None
    repository_name_with_owner: str | None
    provenance: Provenance


@dataclass(frozen=True)
class PermissionFact:
    subject: str
    state: str
    source: str
    reason: str


def slug_of(url):
    """github.com 的 `owner/name`；別的主機或形狀＝None（⛔ 不猜）。"""
    match = SLUG.match(url or '')
    return match[1] if match else None


def select_remotes(facts, *, explicit=None, configured=None):
    """A4 precedence；回 (候選 remote 們, provenance)。名稱不存在＝fail-loud；facts None＝空候選。"""
    remotes = () if facts is None else facts.remotes
    by_name = {remote.name: remote for remote in remotes}
    for value, provenance in ((explicit, Provenance('cli', '--remote')),
                              (configured, Provenance('project_config', 'remote'))):
        if value is not None:
            if value not in by_name:
                raise TargetIdentityError(f'remote 不存在：{value}（{provenance.detail}）')
            return (by_name[value],), provenance
    upstream = tuple(remote for remote in remotes if remote.is_upstream_of_current)
    if upstream:
        return upstream, Provenance('git', 'current branch upstream')
    return remotes, Provenance('git', 'sole remote' if len(remotes) == 1 else 'all remotes')


def _lookup(lookup, candidate):
    try:
        return lookup(candidate.slug)
    except GhError as exc:
        raise ContextError(f'未能解析 repository {candidate.slug}：{exc}') from exc


def resolve_repository(candidates, *, lookup, assertion=None):
    """候選逐一經 API 取 stable ID；ID 相同才合併、不同即 fail-loud（列出兩邊 ID 與 provenance）；
    assertion（`GH_REPO`）只核對、⛔ 不改變被選 remote。回 (identity, 該 repo 的 API payload)。"""
    if not candidates:
        raise ContextError('未能取得 repo：設 GH_REPO 或在有 remote 的 git repo 內執行')
    found = {}
    for candidate in candidates:
        payload = _lookup(lookup, candidate)
        found.setdefault(payload['node_id'], []).append((candidate, payload))
    if len(found) > 1:
        raise TargetIdentityError('repository 候選的 stable ID 不同：' + '；'.join(
            f'{stable_id}←{c.slug}（{c.provenance.kind}:{c.provenance.detail}）'
            for stable_id, rows in found.items() for c, _ in rows))
    (stable_id, rows), = found.items()
    candidate, payload = rows[0]
    detail = candidate.provenance.detail + ('' if len(rows) == 1 else
                                            '（合併 ' + '、'.join(c.slug for c, _ in rows) + '）')
    identity = RepositoryIdentity(stable_id, payload['full_name'], payload['default_branch'],
                                  Provenance(candidate.provenance.kind, detail))
    if assertion is not None:
        asserted = _lookup(lookup, assertion)['node_id']
        if asserted != stable_id:
            raise TargetIdentityError(f'{assertion.provenance.detail} {assertion.slug} 的 stable ID {asserted}'
                                      f' ≠ resolved {stable_id}（{identity.name_with_owner}）')
    return identity, payload


def resolve_project(location, lookup):
    """`project` 鍵解析到唯一 ProjectV2 node_id；null 合法（回 (None, None)）。"""
    if location is None:
        return None, None
    try:
        payload = lookup(location['owner'], location['number'])
    except GhError as exc:
        raise ContextError(f"未能解析 Project {location['owner']}/{location['number']}：{exc}") from exc
    node_id = payload.get('id') if isinstance(payload, dict) else None
    if not node_id:
        raise TargetIdentityError(f"Project {location['owner']}/{location['number']} 解析不到唯一 node_id")
    return ProjectIdentity(node_id, location['owner'], location['number'], Provenance('api', 'projectV2.id')), payload


def permission_fact(subject, source, value):
    """value＝API 欄位值（bool／缺欄位＝None）或讀取時的例外；只翻譯成事實、⛔ 不判該不該。
    true／false＝API 明確回報 ⇒ allowed／denied；403＝明確拒絕 ⇒ denied；401（憑證遭拒）、404
    （資源不可見）、傳輸未完成、缺欄位 ⇒ unknown（未知⛔ 不冒充允許或拒絕）。"""
    if isinstance(value, bool):
        return PermissionFact(subject, 'allowed' if value else 'denied', source, f'{source}={value!r}')
    if value is None:
        return PermissionFact(subject, 'unknown', source, f'{source} 缺欄位')
    if isinstance(value, PermissionDenied):
        status = re.search(r'HTTP\s+(\d{3})', str(value))
        state = 'unknown' if status is not None and status[1] == '401' else 'denied'
        return PermissionFact(subject, state, source, f'{type(value).__name__}: {value}')
    return PermissionFact(subject, 'unknown', source, f'{type(value).__name__}: {value}')


def permission_facts(repository_payload, project_payload):
    """每個 subject 一筆事實，原樣掛進 Context；⛔ 不以 probe mutation 驗權限。"""
    hint = (repository_payload or {}).get('permissions') or {}
    facts = [permission_fact('repository', 'repository.permissions.push', hint.get('push'))]
    if project_payload is not None:
        facts.append(permission_fact('project', 'projectV2.viewerCanUpdate', project_payload.get('viewerCanUpdate')))
    return tuple(facts)


def target_issue(payload, number):
    """REST issue 的身分事實；repository_url 缺（替身）＝None。"""
    url = (payload or {}).get('repository_url') or ''
    name = url.rsplit('/repos/', 1)[1] if '/repos/' in url else None
    return TargetIssue(number, (payload or {}).get('node_id'), name, Provenance('api', f'issues/{number}'))


def item_ref(item, detail='projectV2.items'):
    """Project item 的身分事實；content.repository 缺 id（舊形狀）＝None。"""
    repository = ((item or {}).get('content') or {}).get('repository') or {}
    return ProjectItemRef(item['id'], repository.get('id'), repository.get('nameWithOwner'), Provenance('api', detail))


def check_item_repository(ref, identity):
    """A8：item 的 content.repository stable ID 必須等於 resolved repository；stable ID 缺（舊形狀）時退回
    nameWithOwner 比對；不等＝TargetIdentityError（本機硬擋 D4、零遠端寫入）。"""
    if ref.repository_stable_id is not None:
        if ref.repository_stable_id != identity.stable_id:
            raise TargetIdentityError(f'Project item {ref.item_id} 所屬 repository {ref.repository_stable_id}'
                                      f' ≠ resolved {identity.stable_id}（{identity.name_with_owner}）')
    elif ref.repository_name_with_owner not in (None, identity.name_with_owner):
        raise TargetIdentityError(f'Project item {ref.item_id} 所屬 repository {ref.repository_name_with_owner}'
                                  f' ≠ resolved {identity.name_with_owner}')


def check_target_issue(issue, identity):
    """A8 的 issue 側：REST issue 的 repository（取自 repository_url）必須是 resolved repository；未知不比。"""
    if issue.repository_name_with_owner not in (None, identity.name_with_owner):
        raise TargetIdentityError(f'issue #{issue.number} 屬 {issue.repository_name_with_owner}'
                                  f' ≠ resolved {identity.name_with_owner}')
