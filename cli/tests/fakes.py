"""共用手構替身；消費 core/verbs.md §2。

`--dry-run`：六個 mutation 原語各自先問 `wf.gh.writes.dry_run`（生產碼的同一個判定，
import 使用、⛔ 不在替身重打），帶旗標時⛔ 不記 calls、⛔ 不動替身的狀態——否則測到的是替身
自己的行為，而不是 gate。"""
from copy import deepcopy
from types import SimpleNamespace

from wf.gh.writes import DRY_RUN_ITEM, dry_run

REPOSITORY_ID = 'R_FAKE'  # 替身的 repository stable ID：任何 slug 都回同一顆（同一 repo 的不同拼寫）
PROJECT_ID = 'PVT_FAKE'
DEFAULTS = {  # bootstrap 期的兩個身分讀取：未程式化時給可解析的預設，讓直呼 main() 的既有測試照常
    'repository': lambda slug: {'node_id': REPOSITORY_ID, 'full_name': slug, 'default_branch': 'main',
                                'viewer_permission': 'ADMIN'},
    'capability': lambda owner, number: {'id': PROJECT_ID, 'title': 'fake', 'viewerCanUpdate': True},
}


class FakeGhClient:
    """responses 可給固定回應或 callable(**kwargs)；寫入只記 calls，不修改遠端模型。
    context：直呼動詞的測試沒有 bootstrap，替身自帶「已通過 static gate」的樁；經 main() 時由
    bind_context 換成真 Context（呼叫序記入 calls，供 preflight 時序測試）。"""

    repo = 'fake/repo'  # 與 post_comment 的 html_url 同一 repo；子類可覆寫
    default_branch = 'main'  # 直呼動詞時的預設分支；bind_context 後改取 resolved 值
    context = SimpleNamespace(static_identity_verified=True)

    def __init__(self, **responses):
        self.responses = responses
        self.calls = []

    def _read(self, method, **kwargs):
        self.calls.append((method, deepcopy(kwargs)))
        value = self.responses[method] if method in self.responses else DEFAULTS[method]
        return deepcopy(value(**kwargs) if callable(value) else value)

    def bind_context(self, context):
        self.calls.append(('bind_context', {'static_identity_verified': context.static_identity_verified}))
        self.context = context
        self.default_branch = context.repository.default_branch

    def repository(self, slug):
        return self._read('repository', slug=slug)

    def capability(self, owner, number):
        return self._read('capability', owner=owner, number=number)

    def issue(self, number):
        return self._read('issue', number=number)

    def comments(self, number):
        return self._read('comments', number=number)

    def comment(self, comment_id):
        return self._read('comment', comment_id=comment_id)

    def project(self, owner, number, field_names):
        return self._read('project', owner=owner, number=number, field_names=list(field_names))

    def commit_exists(self, sha):
        return self._read('commit_exists', sha=sha)

    def branch_head(self, branch):
        return self._read('branch_head', branch=branch)

    def merge_base(self, base, head):
        return self._read('merge_base', base=base, head=head)

    def pull_request(self, number):
        return self._read('pull_request', number=number)

    def ci_checks(self, sha):
        return self._read('ci_checks', sha=sha)

    def is_ancestor(self, sha, branch='main'):
        return self._read('is_ancestor', sha=sha, branch=branch)

    def issues(self, state='all'):
        return self._read('issues', state=state)

    def issue_is_open(self, number):
        """唯讀：承載 issue 的 open／closed（core/verbs.md §2 終態 move 的第三個回讀證據）。
        刻意取同一顆 issue 狀態、⛔ 不另存一份：`close_issue` 之後同一替身的回答必須翻面，
        否則測到的是替身自己的常數，而不是 CLI 有沒有把 issue state 讀進完成判定。"""
        return self.issue(number).get('state') == 'open'

    def pulls_for_branch(self, branch):
        return self._read('pulls_for_branch', branch=branch)

    def update_card_body(self, number, card_json, create=False):
        if dry_run(self):
            return None
        self.calls.append(('update_card_body', dict(number=number, card_json=deepcopy(card_json), create=create)))
        return {'number': number, 'body': ''}

    def post_comment(self, number, first_line, body):
        if dry_run(self):
            return None
        self.calls.append(('post_comment', dict(number=number, first_line=first_line, body=body)))
        return {'id': 1, 'html_url': f'https://github.com/fake/repo/issues/{number}#issuecomment-1',
                'body': first_line + '\n' + body}

    def write_project_field(self, prepared):
        """投影欄的唯一寫入口；prepared 由 prepare_project_field 產。"""
        if dry_run(self):
            return None
        self.calls.append(('write_project_field', deepcopy(prepared)))
        operation, _, inputs = prepared
        return {'data': {operation: {'projectV2Item': {'id': inputs['itemId']}}}}

    def added(self, item_id):
        """add_to_project 的回傳形狀；`--dry-run` 也回等形（只是 item id 是 `(dry-run)`），
        讓 open 的 stable ID 比對照常跑（同 wf.gh.writes.dry_run_item）。"""
        return {'data': {'addProjectV2ItemById': {'item': {'id': item_id, 'content': {
            '__typename': 'Issue', 'repository': {'id': REPOSITORY_ID, 'nameWithOwner': self.repo}}}}}}

    def add_to_project(self, project_id, issue_id):
        if dry_run(self):
            return self.added(DRY_RUN_ITEM)
        self.calls.append(('add_to_project', dict(project_id=project_id, issue_id=issue_id)))
        return self.added('ITEM')

    def remove_from_project(self, project_id, item_id):
        if dry_run(self):
            return None
        self.calls.append(('remove_from_project', dict(project_id=project_id, item_id=item_id)))
        return {'data': {'deleteProjectV2Item': {'deletedItemId': item_id}}}

    def close_issue(self, number):
        if dry_run(self):
            return None
        self.calls.append(('close_issue', dict(number=number)))
        return {'number': number, 'state': 'closed'}
