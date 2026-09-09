"""消費 core/verbs.md §1–2、core/dispatch.md「基線」、core/naming.md §3、
core/platform.md P1–P5、core/card-schema.md §5。
投影名稱由呼叫端依規則提供；此層只保留 API 事實，不內建規則或解析本文。
"""
import json
import re
import subprocess
from urllib.parse import quote

from .writes import WriteMixin


class GhError(RuntimeError):
    """API 未完成；未知錯誤不得推論資源不存在。"""


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
    elif status == 404 or (types == {'NOT_FOUND'}):
        cls = NotFound
    elif status is None and not errors and any(s in lower for s in (
        'dial tcp', 'timeout', 'timed out', 'connection', 'network', 'tls', 'eof', 'no such host',
    )):
        cls = TransportError
    else:
        cls = GhError
    raise cls(detail.strip())


class GhClient(WriteMixin):
    """GitHub 介接層；runner 採 subprocess.run 的參數與回傳介面。"""

    def __init__(self, repo, *, runner=None, page_size=100):
        self.repo = '/'.join(quote(part, safe='') for part in repo.split('/'))
        self.runner = subprocess.run if runner is None else runner
        self.page_size = page_size

    def _request(self, endpoint, *, query=None, variables=None, method=None, payload=None):
        args = ['gh', 'api', endpoint, '--method', method or ('POST' if query else 'GET')]
        if query:
            args += ['-f', 'query=' + query]
            for key, value in (variables or {}).items():
                if value is not None:
                    args += ['-F' if isinstance(value, int) else '-f', f'{key}={value}']
        options = {}
        if payload is not None:
            args += ['--input', '-']
            options['input'] = json.dumps(payload, ensure_ascii=False, allow_nan=False)
        try:
            result = self.runner(args, capture_output=True, text=True, check=False, timeout=60, **options)
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

    def issue(self, number):
        """保留 body、state 與其餘 API 欄位。"""
        return self._rest(f'issues/{number}')

    def issues(self, state='all'):
        return [item for item in self._pages(f'issues?state={quote(state, safe="")}')
                if 'pull_request' not in item]

    def pulls_for_branch(self, branch):
        head = self.repo.split('/')[0] + ':' + quote(branch, safe='')
        return self._pages(f'pulls?state=all&head={head}')

    def issue_exists(self, number):
        try:
            self.issue(number)
            return True
        except NotFound:
            return False

    def issue_is_open(self, number):
        return self.issue(number)['state'] == 'open'

    @staticmethod
    def _comment(data):
        return {'id': data['id'], 'url': data['html_url'],
                'author': (data.get('user') or {}).get('login'),
                'created_at': data['created_at'], 'body': data['body']}

    def comments(self, number):
        return [self._comment(c) for c in self._pages(f'issues/{number}/comments')]

    def comment(self, comment_id):
        """保留 issue_url，讓呼叫端可比對裁定所屬卡；不解析留言。"""
        data = self._rest(f'issues/comments/{comment_id}')
        return {**self._comment(data), 'issue_url': data['issue_url']}

    def commit(self, sha):
        return self._rest(f'git/commits/{quote(sha, safe="")}')

    def commit_exists(self, sha):
        try:
            self.commit(sha)
            return True
        except NotFound:
            return False

    def branch_head(self, branch):
        data = self._rest(f'git/ref/heads/{quote(branch, safe="")}')
        return data['object']['sha']

    def pull_request(self, number):
        return self._rest(f'pulls/{number}')

    def ci_checks(self, sha):
        """回傳 checks 與舊式 status；不篩 required checks、不判通過。"""
        ref = quote(sha, safe='')
        return {'check_runs': self._pages(f'commits/{ref}/check-runs', 'check_runs'),
                'statuses': self._pages(f'commits/{ref}/statuses')}

    def _compare(self, base, head):
        return self._rest(f'compare/{quote(base, safe="")}...{quote(head, safe="")}?per_page=1')

    def is_ancestor(self, sha, branch='main'):
        return self._compare(sha, branch)['status'] in ('ahead', 'identical')

    def merge_base(self, base, head):
        return self._compare(base, head)['merge_base_commit']['sha']

    def _connection(self, query, variables, root, field):
        nodes, cursor, seen = [], None, set()
        while True:
            data = self._request('graphql', query=query, variables={**variables, 'cursor': cursor})
            parent = data['data'][root]
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

    def project(self, owner, number, field_names):
        """欄名逐字由 caller 提供；缺值保留 null，名稱與 dataType 原樣回傳。"""
        query = '''query($owner:String!,$number:Int!){
          repositoryOwner(login:$owner){... on ProjectV2Owner{
            projectV2(number:$number){id title url}}}}'''
        data = self._request('graphql', query=query, variables={'owner': owner, 'number': number})
        project = (data['data']['repositoryOwner'] or {}).get('projectV2')
        if project is None:
            raise GhError('GraphQL 未提供 Project；無法確定不存在')
        variables = {'id': project['id'], 'size': self.page_size}
        fields_query = '''query($id:ID!,$size:Int!,$cursor:String){node(id:$id){... on ProjectV2{
          fields(first:$size,after:$cursor){nodes{... on ProjectV2FieldCommon{id name dataType}}
          pageInfo{hasNextPage endCursor}}}}}'''
        fields = self._connection(fields_query, variables, 'node', 'fields')
        selections = '\n'.join(
            f'f{i}:fieldValueByName(name:{json.dumps(name, ensure_ascii=False)}){{'
            '... on ProjectV2ItemFieldTextValue{text field{... on ProjectV2FieldCommon{id name dataType}}}'
            '... on ProjectV2ItemFieldSingleSelectValue{name optionId field{... on ProjectV2FieldCommon{id name dataType}}}}'
            for i, name in enumerate(field_names)
        )
        items_query = '''query($id:ID!,$size:Int!,$cursor:String){node(id:$id){... on ProjectV2{
          items(first:$size,after:$cursor){nodes{id isArchived content{__typename
            ... on Issue{number url repository{nameWithOwner}}
            ... on PullRequest{number url repository{nameWithOwner}}
            ... on DraftIssue{id}} SELECTIONS}pageInfo{hasNextPage endCursor}}}}}'''.replace('SELECTIONS', selections)
        items = self._connection(items_query, variables, 'node', 'items')
        for item in items:
            item['fieldValues'] = {name: item.pop(f'f{i}') for i, name in enumerate(field_names)}
        return {**project, 'fields': fields, 'items': items}
