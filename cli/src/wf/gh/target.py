"""消費 core/verbs.md §2（檢查先於首次遠端寫入；身分衝突走本機硬擋零寫入）、ADOPTION.md §2（`remote`／
`project` 鍵）。resolved target identity：remote precedence ①顯式 `--remote` ②設定鍵 ③current branch upstream
④全部 remote（唯一者即選定，多者經 API canonical stable ID 合併，ID 相同才合併、仍多義即 fail-loud）；
`GH_REPO` 不在 precedence 內（本機身分缺席時成唯一候選，否則只作 stable ID 核對）；Project 與 repository 的
最低關聯＝被操作 item 的 content.repository stable ID 等於 resolved repository（可跨 repo、不要求 owner 相同、
project:null 合法）；permission 只產 `PermissionFact` 事實、⛔ 不做政策（逐 operation 放行或阻擋由 WF-016 決定）。
本機 Git 身分事實 `local_git_facts` 也住這裡（唯讀 plumbing；gh/localgit.py 依既有不變式只包 merge-tree）。
consumer superproject 內 rules source 的 gitlink 取源 `gitlink_sha` 同樣住這裡：它與 `local_git_facts` 共用
同一組失敗語意（事實缺席回 None、只有 git 不可執行才 raise），故落在本檔是沿用既有宣告、⛔ 不新增主張；
它只取源、⛔ 不比對（四列對帳住 verbs/_adopt.py，第零條）。
比對一律用 stable ID；⛔ 不建 dependency solver、⛔ 不耦合具名 consumer、⛔ 不支援 GHES（host 固定 github.com）。
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import subprocess

from wf.context import ContextError, Provenance, TargetIdentityError
from wf.gh.client import GhError, PermissionDenied
from wf.gh.localgit import LocalGitFacts, LocalGitUnavailable, RemoteFact

SLUG = re.compile(r'^(?:[a-z+]+://)?(?:[^@/]+@)?github\.com[/:]([^/:]+/[^/:]+?)(?:\.git)?/?$')
PERMISSION_STATES = ('allowed', 'denied', 'unknown')
GITLINK_MODE = '160000'  # git 對 submodule 條目的 mode（git 自身定義，⛔ 不是本框架的值）
WRITE_LEVELS = ('WRITE', 'MAINTAIN', 'ADMIN')  # GitHub viewerPermission 的可寫層級（API 自身定義）


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


def local_git_facts(root, *, runner=None):
    """六類事實各自取源（`--path-format=absolute` 讓 git-dir／common-dir 不含相對 cwd 前綴）；
    root 不在 git 工作樹內＝None（事實缺席，⛔ 不是錯誤）；git 不可執行＝LocalGitUnavailable。"""
    runner = subprocess.run if runner is None else runner

    def out(*args):
        try:
            result = runner(('git', '-C', str(root), *args), capture_output=True, text=True, check=False,
                            timeout=60)
        except (OSError, subprocess.SubprocessError) as exc:
            raise LocalGitUnavailable(str(exc)) from exc
        return result.stdout.strip() if result.returncode == 0 else None

    layout = out('rev-parse', '--path-format=absolute', '--show-toplevel', '--git-dir', '--git-common-dir')
    if layout is None:
        return None
    top_level, git_dir, common_dir = layout.splitlines()[:3]
    ref = out('symbolic-ref', '--quiet', 'HEAD')
    upstream = out('for-each-ref', '--format=%(upstream:remotename)', ref) if ref else None
    remotes = tuple(RemoteFact(name, out('remote', 'get-url', name) or '',
                               out('remote', 'get-url', '--push', name) or '', name == upstream)
                    for name in (out('remote') or '').split())
    return LocalGitFacts(top_level, git_dir, common_dir, out('rev-parse', '--verify', '--quiet', 'HEAD'),
                         ref, remotes)


def _gitlink_of(text, column):
    """`ls-files -s`／`ls-tree` 的逐筆輸出取 mode 160000 那一筆的 40 碼 SHA；⛔ 無該 mode＝None。
    `column` 是該指令輸出裡 SHA 的欄序（ls-files -s＝1、ls-tree＝2），刻意由呼叫端給：
    兩個指令的欄位形狀本來就不同，⛔ 不得推出「可以共用同一個欄序」。"""
    for record in (text or '').split('\0'):
        fields = record.split()
        if len(fields) > column and fields[0] == GITLINK_MODE and len(fields[column]) == 40:
            return fields[column]
    return None


def gitlink_sha(root, relative, *, runner=None):
    """consumer superproject（`root`）內 `relative` 這條路徑的 gitlink；回 (索引側, HEAD 側)，
    各自是 40 碼 commit SHA 或 None。索引側＝`git ls-files -s`（consumer 當下宣告要採用的版本，權威取源）；
    HEAD 側＝`git ls-tree HEAD`（診斷「已 stage 未 commit」）。兩側刻意⛔ 不折成單值、⛔ 不在本層比對。
    路徑不是 gitlink、路徑不存在、倉庫尚無 commit、root 非工作樹或 bare＝該側 None（事實缺席，⛔ 不是
    錯誤，同 `local_git_facts`）；git 不可執行＝LocalGitUnavailable。
    ⛔ 不得推出「None 代表兩側相同」或「None 代表未採用」——不可得只交給呼叫端標 unknown。"""
    runner = subprocess.run if runner is None else runner

    def out(*args):
        try:
            result = runner(('git', '-C', str(root), *args), capture_output=True, text=True, check=False,
                            timeout=60)
        except (OSError, subprocess.SubprocessError) as exc:
            raise LocalGitUnavailable(str(exc)) from exc
        return result.stdout if result.returncode == 0 else None

    path = str(relative)
    return (_gitlink_of(out('ls-files', '-s', '-z', '--', path), 1),
            _gitlink_of(out('ls-tree', '-z', 'HEAD', '--', path), 2))


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
    if not payload.get('default_branch'):
        raise ContextError(f"repository {payload['full_name']} 無預設分支（空 repo）：無法推導基線")
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
    """value＝API 欄位值（bool／viewerPermission／缺欄位＝None）或讀取時的例外；只翻譯成事實、⛔ 不判該不該。
    true／false、WRITE 以上／以下＝API 明確回報 ⇒ allowed／denied；403 ⇒ denied；401、404、傳輸未完成、
    缺欄位 ⇒ unknown（未知⛔ 不冒充允許或拒絕）。"""
    if isinstance(value, bool):
        return PermissionFact(subject, 'allowed' if value else 'denied', source, f'{source}={value!r}')
    if isinstance(value, str):
        return PermissionFact(subject, 'allowed' if value in WRITE_LEVELS else 'denied', source, f'{source}={value}')
    if value is None:
        return PermissionFact(subject, 'unknown', source, f'{source} 缺欄位')
    if isinstance(value, PermissionDenied):
        status = re.search(r'HTTP\s+(\d{3})', str(value))
        state = 'unknown' if status is not None and status[1] == '401' else 'denied'
        return PermissionFact(subject, state, source, f'{type(value).__name__}: {value}')
    return PermissionFact(subject, 'unknown', source, f'{type(value).__name__}: {value}')


def permission_facts(repository_payload, project_payload):
    """每個 subject 一筆事實，原樣掛進 Context；⛔ 不以 probe mutation 驗權限。"""
    facts = [permission_fact('repository', 'repository.viewerPermission',
                             (repository_payload or {}).get('viewer_permission'))]
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
