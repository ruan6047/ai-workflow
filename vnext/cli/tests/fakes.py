"""注入式替身：固定快照與序列快照。⛔ 不連網、⛔ 不 mutation 任何遠端資源。"""
from __future__ import annotations

import subprocess

from wfx.core.context import Provenance
from wfx.gh.task import TaskData

BODY = '\n'.join(f'## {name}\n\n內容 {name}\n' for name in
                 ('需求', '限制與非目標', '驗收', '風險與假設', '裁定紀錄'))

FIELD_NAMES = ('Title', 'Status', '階段', 'owner', '風險', '緊急性', '期限', 'Resource')

COMMENTS = ({'url': 'https://example.invalid/c1',
             'body': '## 規劃階段完成\n工作包：W1.1–W1.9。\n判斷留給讀者，CLI ⛔ 不解析。\n'},
            {'url': 'https://example.invalid/c2', 'body': '隨手一則，⛔ 不屬四類中的任何一類。\n'})

BASE_REF = 'codex/vnext-rebuild'


def snapshot(*, item_updated='2026-09-21T11:05:20Z', issue_updated='2026-09-21T10:49:13Z',
             status='進行中', body=BODY, field_names=FIELD_NAMES, item=True,
             viewer_permission='ADMIN', viewer_can_update=True, check_conclusion='success',
             comments=COMMENTS, pull_requests=({'number': 376, 'state': 'OPEN', 'baseRefName': BASE_REF},)):
    """一次遠端讀取的完整快照；各參數＝該次讀取到的遠端實況。"""
    values = {'Status': {'name': status}, '狀態': {'name': status}, '階段': {'name': '執行'},
              'owner': {'text': 'ruan6047'}, '風險': {'name': '重要'}, '緊急性': {'name': '一般'},
              '期限': {'date': '2026-09-30'}, 'Resource': None, 'Title': {'text': 'card'},
              '級別': {'name': 'T1'}}
    return {
        'repository': {'node_id': 'R_1', 'full_name': 'o/r', 'default_branch': 'main',
                       'viewer_permission': viewer_permission},
        'issue': {'id': 'I_1', 'number': 370, 'url': 'https://example.invalid/370',
                  'state': 'OPEN', 'body': body, 'updatedAt': issue_updated},
        'comments': list(comments),
        'pull_requests': list(pull_requests),
        'project': {'id': 'PVT_1', 'title': 'board', 'url': 'u', 'viewerCanUpdate': viewer_can_update},
        'field_names': [{'name': name, 'dataType': 'TEXT'} for name in field_names],
        'items': ([{'id': 'PVTI_1', 'updatedAt': item_updated, 'isArchived': False,
                    'content': {'__typename': 'Issue', 'number': 370, 'url': 'u',
                                'repository': {'nameWithOwner': 'o/r'}},
                    'fieldValues': {name: values.get(name) for name in field_names}}] if item else []),
        'ci': {'check_runs': [{'name': 'vnext-tests', 'status': 'completed',
                               'conclusion': check_conclusion}], 'statuses': []},
    }


class FakeClient:
    """序列快照：第 n 次讀取週期讀到第 n 份快照（最後一份之後維持最後一份）。

    一個讀取週期由入口 getter（`repository`＝facts／`issue`＝brief）起算；同一週期內的其他
    getter 都從**當次**綁定的那一份讀，證明沒有跨呼叫快取。
    """

    def __init__(self, *snapshots, pull_request_error=None):
        self.snapshots = list(snapshots) or [snapshot()]
        self.pull_request_error = pull_request_error
        self.reads = 0
        self._current = None
        self._seen = set()

    def _bind(self, entry):
        if self._current is None or entry in self._seen:
            index = min(self.reads, len(self.snapshots) - 1)
            self.reads += 1
            self._current = self.snapshots[index]
            self._seen = set()
        self._seen.add(entry)
        return self._current

    def repository(self, slug):
        return self._bind('repository')['repository']

    def issue(self, number):
        return self._bind('issue')['issue']

    def issue_comments(self, issue_id):
        return self._current['comments']

    def associated_pull_requests(self, oid):
        if self.pull_request_error is not None:
            raise self.pull_request_error
        return self._current['pull_requests']

    def project(self, owner, number):
        return self._current['project']

    def project_field_names(self, project_id):
        return self._current['field_names']

    def project_items(self, project_id, field_names):
        return self._current['items']

    def ci_checks(self, sha):
        return self._current['ci']


def fixed_base(branch, *, unknown=None):
    """測試用 base 解析：⛔ 不打 API，直接回一個已解析的預期合併目標。"""
    provenance = None if branch is None else Provenance(
        'api', f'associatedPullRequests[OPEN].baseRefName={branch}')
    return lambda head_sha: (branch, provenance, unknown)


class FixedTaskSource:
    """第 4 層的內部注入點：一份固定快照，⛔ 不連任何遠端（W1.6 零 provider 呼叫的取證路徑）。"""

    def __init__(self, task, *, issue_body=BODY, fields=None, comments=()):
        self.data = TaskData(task, issue_body,
                             {'狀態': '進行中', '階段': '執行', 'owner': 'ruan6047',
                              '風險': '重要', '緊急性': '一般', '期限': '', 'Resource': ''}
                             if fields is None else fields,
                             tuple(comments))

    def fetch(self, context):
        return self.data


class RecordedRunner:
    """subprocess.run 介面的替身：依 args 前綴回固定 (rc, stdout, stderr)。"""

    def __init__(self, responses, *, default=None):
        self.responses = responses
        self.default = default
        self.calls = []

    def __call__(self, args, **kwargs):
        args = tuple(args)
        self.calls.append(args)
        for prefix, response in self.responses:
            if args[:len(prefix)] == tuple(prefix):
                rc, stdout, stderr = response
                return subprocess.CompletedProcess(args, rc, stdout, stderr)
        if self.default is None:
            raise AssertionError(f'未預期的呼叫：{args}')
        rc, stdout, stderr = self.default
        return subprocess.CompletedProcess(args, rc, stdout, stderr)
