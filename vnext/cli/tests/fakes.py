"""注入式替身：固定快照與序列快照。⛔ 不連網、⛔ 不 mutation 任何遠端資源。"""
from __future__ import annotations

import subprocess

BODY = '\n'.join(f'## {name}\n\n內容 {name}\n' for name in
                 ('需求', '限制與非目標', '驗收', '風險與假設', '裁定紀錄'))

FIELD_NAMES = ('Title', 'Status', '階段', 'owner', '風險', '緊急性', '期限', 'Resource')


def snapshot(*, item_updated='2026-09-21T11:05:20Z', issue_updated='2026-09-21T10:49:13Z',
             status='進行中', body=BODY, field_names=FIELD_NAMES, item=True,
             viewer_permission='ADMIN', viewer_can_update=True, check_conclusion='success'):
    """一次遠端讀取的完整快照；各參數＝該次讀取到的遠端實況。"""
    values = {'Status': {'name': status}, '階段': {'name': '執行'}, 'owner': {'text': 'ruan6047'},
              '風險': {'name': '重要'}, '緊急性': {'name': '一般'},
              '期限': {'date': '2026-09-30'}, 'Resource': None, 'Title': {'text': 'card'}}
    return {
        'repository': {'node_id': 'R_1', 'full_name': 'o/r', 'default_branch': 'main',
                       'viewer_permission': viewer_permission},
        'issue': {'id': 'I_1', 'number': 370, 'url': 'https://example.invalid/370',
                  'state': 'OPEN', 'body': body, 'updatedAt': issue_updated},
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
    """序列快照：第 n 次 collect 讀到第 n 份快照（最後一份之後維持最後一份）。

    每個 getter 都從**當次** collect 綁定的那一份讀，證明沒有跨呼叫快取。
    """

    def __init__(self, *snapshots):
        self.snapshots = list(snapshots) or [snapshot()]
        self.reads = 0
        self._current = None

    def _next(self):
        index = min(self.reads, len(self.snapshots) - 1)
        self.reads += 1
        return self.snapshots[index]

    def repository(self, slug):
        self._current = self._next()
        return self._current['repository']

    def issue(self, number):
        return self._current['issue']

    def project(self, owner, number):
        return self._current['project']

    def project_field_names(self, project_id):
        return self._current['field_names']

    def project_items(self, project_id, field_names):
        return self._current['items']

    def ci_checks(self, sha):
        return self._current['ci']


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


