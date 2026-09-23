"""GitHub 讀取層。只有唯讀能力：⛔ 無任何 mutation 方法（寫入契約由 W1.8 `write` 另立）。

四類錯誤分類沿用既有資產：**未知錯誤⛔ 不得推論資源不存在**（wfx/rules/core/research.md「未知不得冒充」）。
runner 採 subprocess.run 的參數與回傳介面，測試以注入式固定／序列快照替身驗遠端變更行為。
"""
import json
import re
import subprocess
from urllib.parse import quote


class GhError(RuntimeError):
    """API 未完成；未知錯誤⛔ 不得推論資源不存在。"""


class NotFound(GhError):
    """API 明確回報不存在。"""


class PermissionDenied(GhError):
    """API 回報權限不足或憑證遭拒。"""


class TransportError(GhError):
    """傳輸失敗、限流或服務端暫時失敗。"""


class NotLoggedIn(GhError):
    """gh 尚未登入。"""


def _error(rc, payload, stderr):
    errors = payload.get('errors', []) if isinstance(payload, dict) else []
    if not rc and not errors:
        return
    detail = stderr + '\n' + json.dumps(payload, ensure_ascii=False)
    lower = detail.lower()
    types = {e.get('type') for e in errors if isinstance(e, dict)}
    match = re.search(r'HTTP\s+(\d{3})', stderr)
    status = int(match[1]) if match else None
    if status is None and isinstance(payload, dict):
        candidate = str(payload.get('status', ''))
        status = int(candidate) if candidate.isdigit() else None
    if rc == 4 or (status is None and 'gh auth login' in lower):
        cls = NotLoggedIn
    elif (status == 429 or (status is not None and status >= 500)
          or 'RATE_LIMITED' in types or 'rate limit' in lower or 'secondary rate' in lower):
        cls = TransportError
    elif status in (401, 403) or types & {'FORBIDDEN', 'UNAUTHORIZED'}:
        cls = PermissionDenied
    elif status == 404 or types == {'NOT_FOUND'}:
        cls = NotFound
    elif status is None and not errors and any(s in lower for s in (
        'dial tcp', 'timeout', 'timed out', 'connection', 'network', 'tls', 'eof', 'no such host',
    )):
        cls = TransportError
    else:
        cls = GhError
    raise cls(detail.strip())


FIELD_VALUE_FRAGMENTS = (
    '... on ProjectV2ItemFieldTextValue{text}'
    '... on ProjectV2ItemFieldSingleSelectValue{name}'
    '... on ProjectV2ItemFieldDateValue{date}'
    '... on ProjectV2ItemFieldNumberValue{number}'
)


class GhClient:
    """唯讀 GitHub 介接；每次呼叫即時打 API，⛔ 不快取（wfx/rules/core/github.md §7）。"""

    def __init__(self, repo, *, runner=None, page_size=100):
        self.repo = '/'.join(quote(part, safe='') for part in repo.split('/'))
        self.runner = subprocess.run if runner is None else runner
        self.page_size = page_size

    def _request(self, endpoint, *, query=None, variables=None):
        args = ['gh', 'api', endpoint, '--method', 'POST' if query else 'GET']
        if query:
            args += ['-f', 'query=' + query]
            for key, value in (variables or {}).items():
                if value is not None:
                    args += ['-F' if isinstance(value, int) else '-f', f'{key}={value}']
        try:
            result = self.runner(args, capture_output=True, text=True, check=False, timeout=60)
        except (subprocess.TimeoutExpired, ConnectionError) as exc:
            raise TransportError(str(exc)) from exc
        except OSError as exc:
            raise GhError(str(exc)) from exc
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            _error(result.returncode, {}, result.stderr)
            raise GhError('gh 回傳非 JSON') from exc
        _error(result.returncode, payload, result.stderr)
        return payload

    def _rest(self, path):
        return self._request(f'repos/{self.repo}/{path}')

    def _pages(self, path, key=None):
        items, page = [], 1
        separator = '&' if '?' in path else '?'
        while True:
            data = self._rest(f'{path}{separator}per_page={self.page_size}&page={page}')
            batch = data[key] if key else data
            items.extend(batch)
            if len(batch) < self.page_size:
                return items
            page += 1

    def repository(self, slug):
        """stable ID（node_id）、full_name、default_branch（空 repo＝None）、viewer_permission。"""
        owner, _, name = slug.partition('/')
        query = ('query($owner:String!,$name:String!){repository(owner:$owner,name:$name){'
                 'id nameWithOwner defaultBranchRef{name} viewerPermission}}')
        repository = self._request('graphql', query=query,
                                   variables={'owner': owner, 'name': name})['data']['repository']
        if repository is None:
            raise GhError('GraphQL 未提供 repository；無法確定不存在')
        return {'node_id': repository['id'], 'full_name': repository['nameWithOwner'],
                'default_branch': (repository.get('defaultBranchRef') or {}).get('name'),
                'viewer_permission': repository.get('viewerPermission')}

    def issue(self, number):
        """Issue 的 body、state 與 `updatedAt`（＝貼留言的寫入基準；GraphQL 的 ISO-8601 逐字）。"""
        query = ('query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){'
                 'issue(number:$number){id number url state body updatedAt}}}')
        owner, _, name = self.repo.partition('/')
        repository = self._request('graphql', query=query,
                                   variables={'owner': owner, 'name': name,
                                              'number': number})['data']['repository']
        if repository is None:
            raise GhError('GraphQL 未提供 repository；無法確定不存在')
        issue = repository.get('issue')
        if issue is None:
            raise NotFound(f'issue #{number} 不存在於 {self.repo}')
        return issue

    def issue_comments(self, issue_id):
        """該 Issue 的**全部**留言，依遠端順序原樣回傳。

        ⛔ 不分類、⛔ 不篩「哪些算階段完成留言」——`github.md` §3 的四類是內容分類，CLI 判不得。
        """
        query = ('query($id:ID!,$size:Int!,$cursor:String){node(id:$id){... on Issue{'
                 'comments(first:$size,after:$cursor){nodes{url body}'
                 'pageInfo{hasNextPage endCursor}}}}}')
        return self._connection(query, {'id': issue_id, 'size': self.page_size}, 'comments')

    def associated_pull_requests(self, oid):
        """該 commit 的關聯 PR（`state`＋`baseRefName`）原樣回傳；篩 OPEN 由呼叫端做。

        以 SHA 查、⛔ 不以分支名查：detached checkout 與 `--sha` 都沒有分支名。
        查不到 commit＝NotFound，⛔ 不回空清單冒充「沒有 PR」。
        """
        query = ('query($owner:String!,$name:String!,$oid:GitObjectID!,$size:Int!,$cursor:String){'
                 'repository(owner:$owner,name:$name){object(oid:$oid){... on Commit{'
                 'associatedPullRequests(first:$size,after:$cursor)'
                 '{nodes{number state baseRefName}pageInfo{hasNextPage endCursor}}}}}}')
        owner, _, name = self.repo.partition('/')
        nodes, cursor, seen = [], None, set()
        while True:
            repository = self._request('graphql', query=query, variables={
                'owner': owner, 'name': name, 'oid': oid,
                'size': self.page_size, 'cursor': cursor})['data']['repository']
            if repository is None:
                raise GhError('GraphQL 未提供 repository；無法確定不存在')
            commit = repository.get('object')
            if commit is None:
                raise NotFound(f'{self.repo} 內⛔ 無 commit {oid}')
            connection = commit['associatedPullRequests']
            nodes.extend(connection['nodes'])
            info = connection['pageInfo']
            if not info['hasNextPage']:
                return nodes
            cursor = info['endCursor']
            if cursor is None or cursor in seen:
                raise GhError('GraphQL 分頁未前進；讀取未完成')
            seen.add(cursor)

    def ci_checks(self, sha):
        """checks 與舊式 status 原樣回傳；⛔ 不篩 required checks、⛔ 不判通過。"""
        ref = quote(sha, safe='')
        return {'check_runs': self._pages(f'commits/{ref}/check-runs', 'check_runs'),
                'statuses': self._pages(f'commits/{ref}/statuses')}

    def _connection(self, query, variables, field):
        nodes, cursor, seen = [], None, set()
        while True:
            parent = self._request('graphql', query=query,
                                   variables={**variables, 'cursor': cursor})['data']['node']
            if parent is None:
                raise GhError('GraphQL 未提供資源；無法確定不存在')
            connection = parent[field]
            nodes.extend(connection['nodes'])
            info = connection['pageInfo']
            if not info['hasNextPage']:
                return nodes
            cursor = info['endCursor']
            if cursor is None or cursor in seen:
                raise GhError('GraphQL 分頁未前進；讀取未完成')
            seen.add(cursor)

    def project(self, owner, number):
        """Project 本體＋`viewerCanUpdate`；未提供＝GhError（無法確定不存在）。"""
        query = ('query($owner:String!,$number:Int!){repositoryOwner(login:$owner){'
                 '... on ProjectV2Owner{projectV2(number:$number){id title url viewerCanUpdate}}}}')
        data = self._request('graphql', query=query, variables={'owner': owner, 'number': number})
        project = (data['data']['repositoryOwner'] or {}).get('projectV2')
        if project is None:
            raise GhError('GraphQL 未提供 Project；無法確定不存在')
        return project

    def project_field_names(self, project_id):
        """欄位名稱逐字（含內建），供呼叫端判定狀態欄實際落在 `Status` 還是 `狀態`。

        另帶 `id` 與 SingleSelect 的 `options`：那是**寫入時指名該欄與該選項**所需的識別，
        本方法仍是唯讀查詢（mutation 只住 wfx/gh/writes.py）。
        """
        query = ('query($id:ID!,$size:Int!,$cursor:String){node(id:$id){... on ProjectV2{'
                 'fields(first:$size,after:$cursor){nodes{... on ProjectV2FieldCommon{id name dataType}'
                 '... on ProjectV2SingleSelectField{options{id name}}}'
                 'pageInfo{hasNextPage endCursor}}}}}')
        return self._connection(query, {'id': project_id, 'size': self.page_size}, 'fields')

    def project_items(self, project_id, field_names):
        """每個 item 帶自己的 `updatedAt`（＝寫欄位的寫入基準）與逐名 fieldValue（缺值＝None）。"""
        selections = '\n'.join(
            f'f{i}:fieldValueByName(name:{json.dumps(name, ensure_ascii=False)})'
            f'{{{FIELD_VALUE_FRAGMENTS}}}' for i, name in enumerate(field_names))
        query = ('query($id:ID!,$size:Int!,$cursor:String){node(id:$id){... on ProjectV2{'
                 'items(first:$size,after:$cursor){nodes{id updatedAt isArchived content{__typename'
                 ' ... on Issue{number url repository{nameWithOwner}}'
                 ' ... on PullRequest{number url repository{nameWithOwner}}}'
                 ' SELECTIONS}pageInfo{hasNextPage endCursor}}}}}').replace('SELECTIONS', selections)
        items = self._connection(query, {'id': project_id, 'size': self.page_size}, 'items')
        for item in items:
            item['fieldValues'] = {name: item.pop(f'f{i}') for i, name in enumerate(field_names)}
        return items
