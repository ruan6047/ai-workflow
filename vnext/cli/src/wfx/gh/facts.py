"""六類客觀事實的組裝（vnext/rules/core/github.md、boundaries.md「CLI 邊界」）。

六類：①Issue 五章節存在且非空 ②七個核心概念當下值 ③Project item 與 Issue 各自的 `updatedAt`
④本機 git rev-parse／log／diff --stat／merge-tree ⑤CI check 結論 ⑥權限三態。

⛔ 不判證據夠不夠、⛔ 不判內容品質、⛔ 不碰模型資料、⛔ 不推導退回次數、⛔ 不重建轉移歷史、
⛔ 不統計工作包完成度。取不到一律 typed unknown 或 raise，⛔ 不以空結果冒充「沒有改動」。
遠端每次即時讀取，⛔ 不快取：遠端改動後輸出隨之改變＝正確行為。
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from wfx.core.context import Provenance
from wfx.gh.client import GhError
from wfx.gh.localgit import LocalGitUnavailable, merge_tree
from wfx.gh.localrev import LocalRevUnavailable, diff_stat, log_commits, rev_parse
from wfx.gh.target import PermissionFact, TargetError, permission_fact, resolve_repository

SECTIONS = ('需求', '限制與非目標', '驗收', '風險與假設', '裁定紀錄')
CONCEPTS = ('狀態', '階段', 'owner', '風險', '緊急性', '期限', 'Resource')
STATUS_FIELD_ALIASES = ('狀態', 'Status')  # 內建欄位能否改名由平台決定；兩種都認、恰一個才合法
HEADING = re.compile(r'^(#{1,6})\s+(.*?)\s*$')
PRESENT, EMPTY, MISSING = '非空', '空', '缺章節'


@dataclass(frozen=True)
class SectionFact:
    name: str
    state: str


@dataclass(frozen=True)
class ConceptFact:
    concept: str
    field_name: str | None   # 該概念在此 Project 實際落地的欄名；None＝Project 無此欄
    value: str | None        # None＝欄位存在但未填（照實印，⛔ 不填預設）


@dataclass(frozen=True)
class Baseline:
    """`write --expect-updated-at` 的寫入基準；`object_kind` 標明它屬於哪個物件。"""
    object_kind: str         # project_item｜issue
    object_ref: str
    updated_at: str


@dataclass(frozen=True)
class GitFacts:
    base_ref: str | None
    base_provenance: Provenance | None
    base_sha: str | None
    head_ref: str
    head_sha: str | None
    log: tuple[str, ...] | None
    diff_stat: tuple[str, ...] | None
    merge_tree_rc: int | None
    unknown: tuple[str, ...]   # 每則＝一項取不到的事實與其逐字原因


@dataclass(frozen=True)
class CiFacts:
    sha: str | None
    check_runs: tuple[tuple[str, str, str | None], ...] | None   # (name, status, conclusion)
    statuses: tuple[tuple[str, str], ...] | None                 # (context, state)
    unknown: str | None


@dataclass(frozen=True)
class GhFacts:
    task: str
    repository: str
    repository_provenance: Provenance
    issue_url: str
    project_ref: str | None
    item_id: str | None
    sections: tuple[SectionFact, ...]
    concepts: tuple[ConceptFact, ...]
    baselines: tuple[Baseline, ...]
    unknown_baselines: tuple[str, ...]
    git: GitFacts
    ci: CiFacts
    permissions: tuple[PermissionFact, ...]


def section_facts(body):
    """只認「標題在且其下非空」。⛔ 不解析散文語意、⛔ 不判內容好壞。"""
    content, current = {}, None
    for line in (body or '').splitlines():
        match = HEADING.match(line)
        if match and len(match[1]) <= 2:
            current = match[2]
            content.setdefault(current, [])
            continue
        if current is not None:
            content[current].append(line)
    facts = []
    for name in SECTIONS:
        if name not in content:
            facts.append(SectionFact(name, MISSING))
        else:
            facts.append(SectionFact(name, PRESENT if any(l.strip() for l in content[name]) else EMPTY))
    return tuple(facts)


def _field_value(raw):
    """GraphQL fieldValueByName 的四種值型別取一；未填＝None（⛔ 不代填預設）。"""
    if not raw:
        return None
    for key in ('text', 'name', 'date', 'number'):
        if raw.get(key) is not None:
            return str(raw[key])
    return None


def status_field_name(field_names):
    """狀態欄的唯一落地欄名；⛔ 不得同時存在兩個（會變成第二個狀態居所）。"""
    found = [name for name in STATUS_FIELD_ALIASES if name in field_names]
    if len(found) != 1:
        raise TargetError(f'狀態欄不唯一：Project 內符合 {list(STATUS_FIELD_ALIASES)} 的欄位＝{found}')
    return found[0]


def concept_facts(field_names, values):
    facts = []
    for concept in CONCEPTS:
        name = status_field_name(field_names) if concept == '狀態' else concept
        if name not in field_names:
            facts.append(ConceptFact(concept, None, None))
        else:
            facts.append(ConceptFact(concept, name, _field_value(values.get(name))))
    return tuple(facts)


def base_resolver(client, default_branch):
    """本次受查 head SHA → **預期合併目標**（需求 §3.4）。⛔ 不以當前分支名查。

    ①該 SHA 的開啟中 PR `baseRefName` 唯一 ⇒ 用它；②對到多個開啟中 PR 且 base 不同 ⇒ unknown；
    ③查詢失敗 ⇒ unknown（⛔ 不得當成「沒有 PR」而靜默改用預設分支）；
    ④**確認**⛔ 無關聯的開啟中 PR ⇒ 才用 repository 預設分支，並在來源標記寫明。

    以 SHA 而非分支名查，是為了讓固定到同一 exact SHA 的 detached worktree 與分支 checkout
    印出同一個 base（E W1.7 (5)）。
    """
    def resolve(head_sha):
        if not head_sha:
            return None, None, 'base ref：未解析出受查 head SHA，⛔ 不以分支名代查'
        try:
            names = sorted({pr['baseRefName'] for pr in client.associated_pull_requests(head_sha)
                            if pr.get('state') == 'OPEN'})
        except GhError as exc:
            return None, None, ('base ref：associatedPullRequests 查詢未完成'
                                f'（{type(exc).__name__}: {exc}），⛔ 不當成沒有 PR')
        if len(names) > 1:
            return None, None, (f'base ref：{head_sha} 對到多個開啟中 PR 且 base 不同＝'
                                f'{"、".join(names)}，⛔ 不猜')
        if names:
            return names[0], Provenance('api', f'associatedPullRequests[OPEN].baseRefName={names[0]}'), None
        if default_branch:
            return default_branch, Provenance(
                'api', f'repository.defaultBranchRef={default_branch}（⛔ 無關聯的開啟中 PR）'), None
        return None, None, 'base ref：repository 無預設分支（API 回 null）'
    return resolve


def git_facts(root, *, base, remote_names, sha, runner=None):
    """`base`＝callable(head_sha) → (base 分支名｜None, Provenance｜None, unknown 原因｜None)。

    以 callable 傳入是因為它要先有本機解出的受查 head SHA（見 base_resolver）。
    本機解不到該 ref 時，依賴它的三項事實回 typed unknown，⛔ 不回空清單。
    """
    unknown, base_ref, base_provenance, base_sha = [], None, None, None
    head_ref = sha or 'HEAD'
    try:
        head_sha = rev_parse(head_ref, root=root, runner=runner)
    except LocalRevUnavailable as exc:
        return GitFacts(None, None, None, head_ref, None, None, None, None,
                        (f'rev-parse {head_ref}：{exc}',))
    if head_sha is None:
        unknown.append(f'rev-parse {head_ref}：本機沒有這個 revision')
    base_branch, resolved_provenance, reason = base(head_sha)
    if reason:
        unknown.append(reason)
    if base_branch:
        for candidate in [f'refs/remotes/{name}/{base_branch}' for name in remote_names] + \
                         [f'refs/heads/{base_branch}']:
            try:
                base_sha = rev_parse(candidate, root=root, runner=runner)
            except LocalRevUnavailable as exc:
                unknown.append(f'rev-parse {candidate}：{exc}')
                break
            if base_sha is not None:
                base_ref = candidate
                base_provenance = resolved_provenance
                break
        if base_sha is None and base_ref is None:
            unknown.append(f'base ref：本機解不到 {base_branch} 的任何 ref')
    log = stat = rc = None
    if base_sha and head_sha:
        for label, call in (('git log', lambda: log_commits(base_sha, head_sha, root=root, runner=runner)),
                            ('git diff --stat', lambda: diff_stat(base_sha, head_sha, root=root, runner=runner))):
            try:
                value = tuple(call())
            except LocalRevUnavailable as exc:
                unknown.append(f'{label}：{exc}')
                value = None
            if label == 'git log':
                log = value
            else:
                stat = value
        try:
            rc = merge_tree(base_sha, head_sha, root=root, runner=runner)
        except LocalGitUnavailable as exc:
            unknown.append(f'git merge-tree：{exc}')
    else:
        unknown.append('git log／diff --stat／merge-tree：base 或 head 未解析，⛔ 不以空結果冒充沒有改動')
    return GitFacts(base_ref, base_provenance, base_sha, head_ref, head_sha, log, stat, rc, tuple(unknown))


def locate_item(items, slug, number):
    """content 是本 repo 的該 Issue 者恰一個；⛔ 無＝事實缺席（回 None），多個＝fail-loud。"""
    matched = [item for item in items
               if (item.get('content') or {}).get('number') == number
               and ((item['content'].get('repository') or {}).get('nameWithOwner') in (None, slug))]
    if len(matched) > 1:
        raise GhError(f'{slug}#{number} 對應多個 Project item：{[i["id"] for i in matched]}')
    return matched[0] if matched else None


def resolve_slug(context, task, *, env=None, runner=None):
    """`--task` 已帶 slug 時逐字採用，否則走 remote precedence。回 (slug, Provenance, remote 名稱)。"""
    if task.slug:
        return task.slug, Provenance('cli', '--task'), ()
    target = resolve_repository(context.project_root, configured=context.config.get('remote'),
                                env_repo=(env or {}).get('GH_REPO'), runner=runner)
    return target.slug, target.provenance, target.remote_names


def ci_facts(client, sha):
    if not sha:
        return CiFacts(None, None, None, 'CI check：未解析出 SHA')
    try:
        payload = client.ci_checks(sha)
    except GhError as exc:
        return CiFacts(sha, None, None, f'CI check：{type(exc).__name__}: {exc}')
    runs = tuple((r.get('name') or '', r.get('status') or '', r.get('conclusion'))
                 for r in payload['check_runs'])
    statuses = tuple((s.get('context') or '', s.get('state') or '') for s in payload['statuses'])
    return CiFacts(sha, runs, statuses, None)
