"""共用手構替身；消費 core/verbs.md §2。

`--dry-run`：六個 mutation 原語各自先問 `wf.gh.writes.dry_run`（生產碼的同一個判定，
import 使用、⛔ 不在替身重打），帶旗標時⛔ 不記 calls、⛔ 不動替身的狀態——否則測到的是替身
自己的行為，而不是 gate。"""
from copy import deepcopy
from types import SimpleNamespace

from wf.gh import writes  # 兩版共有的**模組**；⛔ 不 from-import 只存在於被審版的名字

# `--dry-run` gate 在替身側的**委派**介面：判定與 item id 都在呼叫時向 `wf.gh.writes` 取，
# ⛔ 不在替身重打生產常數 `DRY_RUN_ITEM`、⛔ 不重打判定式（F-執行者-04 逐字「驗證器 `import`
# 使用，⛔ 不重打常數」）。
#
# 為什麼是「import 模組 ＋ 呼叫時 getattr」而不是 `from wf.gh.writes import dry_run,
# DRY_RUN_ITEM`：A8（`cli/tests/test_baseline_parity.py`）的兩個隔離子行程共用本目錄下的同一份
# 場景建構碼，而基線樹 f69f6216e575ec881222fc20549685795e2fc1c8 的 `cli/src` 還沒有這兩個
# **名字**，模組級 from-import 會讓共用碼在基線子行程載入失敗（A8 逐字「該份碼⛔ 不得 import
# 任一只存在於被審版的名字（`wf.verbs._ops`、`wf.gh.writes.dry_run`、`wf.gh.writes.DRY_RUN_ITEM`
# 等），版本差異只能經一個在兩版都存在的狀態讀取介面取得」）。模組 `wf.gh.writes` 本身兩版都在
# （實測：基線樹載入 OK 而 `hasattr(writes, 'dry_run')` 為 False），故 import 的是模組、屬性到
# 呼叫時才取——版本差異就是那個「在兩版都存在的狀態讀取介面」。
#
# ⚠️ 邊界：下面「屬性缺席 ⇒ 回 False」的默認值**只針對 `--dry-run` 這一個功能**。理由逐字＝基線
# ⛔ 無 dry-run 這個功能、A8 的場景一律不帶該旗標，故回 False 逐字等於基線的實際行為（⛔ 不是
# 猜的默認值）。⛔ 不得把它推廣成「所有跨版本功能缺席時都取默認值」的通則；別的功能要跨版本
# 共用時各自另行裁定其缺席語意。
# 委派的有效性（換掉生產側的判定／常數，替身必須跟著換）由
# `test_dry_run_write_plan.py::test_the_fake_dry_run_gate_delegates_to_the_production_gate`
# 釘住。⛔ 不得推出「替身自己另定了一套 gate」。


def dry_run(client):
    gate = getattr(writes, 'dry_run', None)
    if gate is None:
        return False  # 基線無此功能；A8 場景不啟用 dry-run
    return gate(client)


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
            return self.added(writes.DRY_RUN_ITEM)  # 生產常數，⛔ 不在替身重打
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
