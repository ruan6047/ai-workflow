"""消費 core/card-schema.md §1／§5、core/verbs.md §2、core/naming.md §3。
GitHub API 協定與 body 區塊定位；欄名、值與留言首行由呼叫端供給。
"""
import json
import re
from urllib.parse import urlsplit


class CardBodyError(ValueError):
    """卡面區塊不能唯一定位或不是 JSON。"""


class InvalidCommentURL(ValueError):
    """留言 URL 不能解析；呼叫端當 D4。"""


LABELS = ('wf-card', 'wf-intake', 'wf-return', 'wf-ruling', 'wf-note')
MULTI_LABELS = ('wf-note',)  # 複數區塊的白名單；其餘標籤機械擋在 block_spans 內，⛔ 不靠呼叫端自律


def _scan(body, label):
    """掃出該標籤的全部區塊範圍，與「結尾還開著的圍欄正好是該標籤」與否。"""
    spans, fence, start, offset = [], None, None, 0
    for line in body.splitlines(keepends=True):
        marker = line.rstrip('\r\n')
        if fence is None and marker.startswith('```'):
            fence = marker
            start = offset + len(line)
        elif fence is not None and marker == '```':
            if fence == '```json ' + label:
                spans.append((start, offset))
            fence = None
        offset += len(line)
    return spans, fence == '```json ' + label


def block_span(body, label, required=True):
    if label not in LABELS:
        raise CardBodyError(f'不支援的區塊：{label}')
    spans, dangling = _scan(body, label)
    if not spans and not dangling and not required:
        return None
    if len(spans) != 1 or dangling:
        raise CardBodyError(f'{label} 區塊缺少、重複或未閉合')
    return spans[0]


def block_spans(body, label):
    """一則留言內該標籤的 N 個區塊範圍（N≥0，依出現序）；只對 MULTI_LABELS 開放。
    未閉合的圍欄正好是該標籤時區塊邊界無法辨認 ⇒ CardBodyError（留言級）；別的標籤
    未閉合⛔ 不吞掉已閉合的本標籤區塊。"""
    if label not in MULTI_LABELS:
        raise CardBodyError(f'不支援的複數區塊：{label}')
    spans, dangling = _scan(body, label)
    if dangling:
        raise CardBodyError(f'{label} 區塊未閉合')
    return spans


def read_block(body, label, required=True):
    span = block_span(body, label, required)
    if span is None:
        return None
    start, end = span
    try:
        return json.loads(body[start:end])
    except ValueError as exc:
        raise CardBodyError(f'{label} JSON 解析失敗') from exc


def block_value(body, label):
    """回傳（區塊在不在, 區塊值）；值可為 null／任何 JSON，型別由呼叫端判（⛔ 此層不判讀）。
    0／≥2／未閉合／壞 JSON 的行為與 block_span(required=False)／read_block 相同。
    """
    span = block_span(body, label, required=False)
    if span is None:
        return False, None
    start, end = span
    try:
        return True, json.loads(body[start:end])
    except ValueError as exc:
        raise CardBodyError(f'{label} JSON 解析失敗') from exc


def card_span(body):
    return block_span(body, 'wf-card')


def read_card(body):
    return read_block(body, 'wf-card')


class WriteMixin:
    def update_card_body(self, number, card_json, create=False):
        body = self.issue(number)['body'] or ''
        span = block_span(body, 'wf-card', required=not create)
        newline = '\r\n' if '\r\n' in body else '\n'
        content = json.dumps(card_json, ensure_ascii=False, indent=2, allow_nan=False)
        content = content.replace('\n', newline) + newline
        if span is None:
            separator = newline if body.endswith(newline) else newline * 2
            body += separator + '```json wf-card' + newline + '```' + newline
            span = card_span(body)
        start, end = span
        return self._request(f'repos/{self.repo}/issues/{number}', method='PATCH',
                             payload={'body': body[:start] + content + body[end:]})

    def post_comment(self, number, first_line, body):
        return self._request(f'repos/{self.repo}/issues/{number}/comments', method='POST',
                             payload={'body': first_line + '\n' + body})

    def comment_from_url(self, url):
        if not isinstance(url, str):
            raise InvalidCommentURL(str(url))
        try:
            parsed = urlsplit(url)
        except (ValueError, TypeError) as exc:
            raise InvalidCommentURL(str(url)) from exc
        match = re.fullmatch(r'/([^/]+/[^/]+)/issues/([1-9][0-9]*)', parsed.path)
        fragment = re.fullmatch(r'issuecomment-([1-9][0-9]*)', parsed.fragment)
        if (parsed.scheme != 'https' or parsed.netloc != 'github.com' or parsed.query
                or not match or not fragment or match[1] != self.repo):
            raise InvalidCommentURL(url)
        result = self.comment(int(fragment[1]))
        if result['issue_url'] != f'https://api.github.com/repos/{self.repo}/issues/{match[2]}':
            raise InvalidCommentURL('留言不屬於 URL 指定的 issue')
        return result

    def prepare_project_field(self, project, item_id, name, value):
        """只解析欄與選項 ID；讓呼叫端在首次寫入前準備整批。"""
        field, = (f for f in project['fields'] if f['name'] == name)
        inputs = {'projectId': project['id'], 'itemId': item_id, 'fieldId': field['id']}
        if value is None:
            operation, input_type = 'clearProjectV2ItemFieldValue', 'ClearProjectV2ItemFieldValueInput'
        else:
            operation, input_type = 'updateProjectV2ItemFieldValue', 'UpdateProjectV2ItemFieldValueInput'
            if field['dataType'] == 'SINGLE_SELECT':
                query = '''query($id:ID!){node(id:$id){... on ProjectV2SingleSelectField{
                  options{id name}}}}'''
                data = self._request('graphql', query=query, variables={'id': field['id']})
                option, = (o for o in data['data']['node']['options'] if o['name'] == value)
                inputs['value'] = {'singleSelectOptionId': option['id']}
            else:
                inputs['value'] = {'text': value}
        return operation, input_type, inputs

    def write_project_field(self, prepared):
        return self._mutation(*prepared, 'projectV2Item{id}')

    def _mutation(self, operation, input_type, inputs, selection):
        return self._request('graphql', method='POST', payload={
            'query': f'mutation($input:{input_type}!){{{operation}(input:$input){{{selection}}}}}',
            'variables': {'input': inputs}})

    def add_to_project(self, project_id, issue_id):
        return self._mutation('addProjectV2ItemById', 'AddProjectV2ItemByIdInput',
                              {'projectId': project_id, 'contentId': issue_id}, 'item{id}')

    def remove_from_project(self, project_id, item_id):
        return self._mutation('deleteProjectV2Item', 'DeleteProjectV2ItemInput',
                              {'projectId': project_id, 'itemId': item_id}, 'deletedItemId')

    def close_issue(self, number):
        return self._request(f'repos/{self.repo}/issues/{number}', method='PATCH',
                             payload={'state': 'closed'})
