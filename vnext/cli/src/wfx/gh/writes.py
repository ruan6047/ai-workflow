"""唯一的 mutation surface：寫 Project 欄位、貼 Issue 留言，⛔ 無其他能力。

隔離：唯讀的 `GhClient` ⛔ 不長出寫入方法，`facts`／`brief` 全程⛔ 不 import 本模組
（機械錨＝tests/test_wfx_boundaries.py）。基準比對由 `verbs/write.py` 在**第一個 mutation 之前**
做一次；基準只縮小視窗、⛔ 不構成鎖，⛔ 不宣稱基準讀取與寫入之間具原子性（rules/core/github.md §7）。
⛔ 無開卡／關卡／改 body 能力、⛔ 無 envelope／fingerprint／續作／鎖定服務／寫入帳本、
⛔ 不重試、⛔ 不做部分失敗補償。
"""
from __future__ import annotations

import json
import subprocess

from wfx.core.errors import WfxError
# 四類錯誤分類與唯讀層共用同一份：未知錯誤⛔ 不得推論資源不存在（core/research.md）。
from wfx.gh.client import GhError, TransportError, _error as _classify


class UnwritableField(WfxError):
    """該欄位的型別或選項不在寫入能力內；⛔ 不猜、⛔ 不代填。"""


def field_value_input(field, value):
    """把字串值翻成該欄位型別的 GraphQL value input。⛔ 不判內容，只認 dataType。"""
    data_type = field.get('dataType')
    if data_type == 'SINGLE_SELECT':
        options = [o for o in (field.get('options') or []) if o.get('name') == value]
        if len(options) != 1:
            raise UnwritableField(
                f'{field["name"]}：選項 {value!r} 在該 Project 欄位上不存在或不唯一')
        return {'singleSelectOptionId': options[0]['id']}
    if data_type == 'DATE':
        return {'date': value}
    if data_type == 'TEXT':
        return {'text': value}
    raise UnwritableField(f'{field["name"]}：dataType={data_type} 不在寫入能力內')


class GhWriter:
    """兩個 mutation 原語。每次呼叫即時發請求，⛔ 不批次、⛔ 不快取。"""

    def __init__(self, *, runner=None):
        self.runner = subprocess.run if runner is None else runner

    def _graphql(self, query, variables):
        args = ['gh', 'api', 'graphql', '--method', 'POST', '--input', '-']
        body = json.dumps({'query': query, 'variables': variables},
                          ensure_ascii=False, allow_nan=False)
        try:
            result = self.runner(args, capture_output=True, text=True, check=False,
                                 timeout=60, input=body)
        except (subprocess.TimeoutExpired, ConnectionError) as exc:
            raise TransportError(str(exc)) from exc
        except OSError as exc:
            raise GhError(str(exc)) from exc
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            _classify(result.returncode, {}, result.stderr)
            raise GhError('gh 回傳非 JSON') from exc
        _classify(result.returncode, payload, result.stderr)
        return payload

    def set_field(self, project_id, item_id, field, value):
        """value＝None ⇒ 清空該欄位（clear），⛔ 不代填預設值、⛔ 不新增值域。"""
        inputs = {'projectId': project_id, 'itemId': item_id, 'fieldId': field['id']}
        if value is None:
            return self._graphql(
                'mutation($input:ClearProjectV2ItemFieldValueInput!){'
                'clearProjectV2ItemFieldValue(input:$input){projectV2Item{id}}}',
                {'input': inputs})
        inputs['value'] = field_value_input(field, value)
        return self._graphql(
            'mutation($input:UpdateProjectV2ItemFieldValueInput!){'
            'updateProjectV2ItemFieldValue(input:$input){projectV2Item{id}}}',
            {'input': inputs})

    def post_comment(self, issue_id, body):
        """回傳該留言的 URL；留言內容逐字送出，⛔ 不加標頭、⛔ 不分類。"""
        payload = self._graphql(
            'mutation($input:AddCommentInput!){addComment(input:$input){'
            'commentEdge{node{url}}}}',
            {'input': {'subjectId': issue_id, 'body': body}})
        return payload['data']['addComment']['commentEdge']['node']['url']
