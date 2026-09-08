"""共用手構替身；消費 core/verbs.md §2 與 WF-STEP6-S05 續派附錄 §9。"""
from copy import deepcopy


class FakeGhClient:
    """responses 可給固定回應或 callable(**kwargs)；寫入只記 calls，不修改遠端模型。"""

    repo = 'fake/repo'  # 與 post_comment 的 html_url 同一 repo；子類可覆寫

    def __init__(self, **responses):
        self.responses = responses
        self.calls = []

    def _read(self, method, **kwargs):
        self.calls.append((method, deepcopy(kwargs)))
        value = self.responses[method]
        return deepcopy(value(**kwargs) if callable(value) else value)

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

    def pulls_for_branch(self, branch):
        return self._read('pulls_for_branch', branch=branch)

    def update_card_body(self, number, card_json, create=False):
        self.calls.append(('update_card_body', dict(number=number, card_json=deepcopy(card_json), create=create)))
        return {'number': number, 'body': ''}

    def post_comment(self, number, first_line, body):
        self.calls.append(('post_comment', dict(number=number, first_line=first_line, body=body)))
        return {'id': 1, 'html_url': f'https://github.com/fake/repo/issues/{number}#issuecomment-1',
                'body': first_line + '\n' + body}

    def write_project_field(self, prepared):
        """投影欄的唯一寫入口（S20 刪 WriteMixin.set_project_field 後）；prepared 由 prepare_project_field 產。"""
        self.calls.append(('write_project_field', deepcopy(prepared)))
        operation, _, inputs = prepared
        return {'data': {operation: {'projectV2Item': {'id': inputs['itemId']}}}}

    def add_to_project(self, project_id, issue_id):
        self.calls.append(('add_to_project', dict(project_id=project_id, issue_id=issue_id)))
        return {'data': {'addProjectV2ItemById': {'item': {'id': 'ITEM'}}}}

    def remove_from_project(self, project_id, item_id):
        self.calls.append(('remove_from_project', dict(project_id=project_id, item_id=item_id)))
        return {'data': {'deleteProjectV2Item': {'deletedItemId': item_id}}}

    def close_issue(self, number):
        self.calls.append(('close_issue', dict(number=number)))
        return {'number': number, 'state': 'closed'}
