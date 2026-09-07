"""core/card-schema.md §1／§5；core/verbs.md §2；S05 gh 寫入協定與區塊定位。"""
import json
from types import SimpleNamespace

import pytest

from wf.gh.client import GhClient, PermissionDenied
from wf.gh.writes import CardBodyError, InvalidCommentURL, block_span, read_block, card_span, read_card


class ApiFake:
    """API 層手構回應；不冒充真實 fixture。"""
    def __init__(self, body=''):
        self.body = body
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        assert args[:2] == ['gh', 'api']
        assert kwargs['timeout'] == 60
        if args[2] == 'graphql':
            value = {'data': {'node': {'options': [{'name': '選值', 'id': 'OPTION'}]}}}
        elif args[args.index('--method') + 1] == 'GET':
            value = {'body': self.body}
        else:
            value = json.loads(kwargs['input'])
            if 'body' in value:
                self.body = value['body']
        return SimpleNamespace(returncode=0, stdout=json.dumps(value), stderr='')


@pytest.mark.parametrize('newline', ['\n', '\r\n'])
@pytest.mark.parametrize('create', [False, True])
def test_update_only_card_content_and_rereads_latest_body(newline, create):
    prefix, suffix = '前文 中\n```json wf-note\n{}\n```\n', '```\n尾文 `literal`\n'
    prefix = (prefix + '```json wf-card\n').replace('\n', newline)
    suffix = suffix.replace('\n', newline)
    runner = ApiFake(prefix + '{"old":1}' + newline + suffix)
    client = GhClient('a/b', runner=runner)
    runner.body = '剛加入的散文' + newline + runner.body
    before = runner.body
    result = client.update_card_body(295, {'新': ['值', 2]}, create=create)
    a, b = card_span(before)
    c, d = card_span(result['body'])
    assert before[:a].encode() == result['body'][:c].encode()
    assert before[b:].encode() == result['body'][d:].encode()
    assert read_card(result['body']) == {'新': ['值', 2]}
    assert [args[args.index('--method') + 1] for args, kw in runner.calls] == ['GET', 'PATCH']
    if newline == '\r\n':
        assert '\n' not in result['body'].replace('\r\n', '')


@pytest.mark.parametrize('original', ['', '原散文', '原散文\n', '原散文\r\n第二行', '原散文\r\n'])
def test_create_appends_preserving_prose(original):
    runner = ApiFake(original)
    result = GhClient('a/b', runner=runner).update_card_body(295, {'new': True}, create=True)
    assert result['body'].encode().startswith(original.encode())
    newline = '\r\n' if '\r\n' in original else '\n'
    separator = newline if original.endswith(newline) else newline * 2
    assert result['body'][len(original):].startswith(separator + '```json wf-card' + newline)
    assert read_card(result['body']) == {'new': True}


@pytest.mark.parametrize('text', ['', '```json wf-card\n{}', '```json wf-card\n{}\n```\n' * 2])
def test_bad_card_never_patches(text):
    runner = ApiFake(text)
    with pytest.raises(CardBodyError, match='wf-card 區塊缺少、重複或未閉合'):
        GhClient('a/b', runner=runner).update_card_body(295, {})
    assert len(runner.calls) == 1


def test_create_duplicate_never_patches():
    runner = ApiFake('```json wf-card\n{}\n```\n' * 2)
    with pytest.raises(CardBodyError):
        GhClient('a/b', runner=runner).update_card_body(295, {}, create=True)
    assert len(runner.calls) == 1


@pytest.mark.parametrize('label', ['wf-card', 'wf-return', 'wf-ruling', 'wf-note'])
def test_block_zero_one_two_and_invalid_json(label):
    text = f'```json {label}\n{{"a": 1}}\n```\n'
    assert block_span('純散文', label, required=False) is None
    assert read_block('純散文', label, required=False) is None
    assert read_block(text, label) == {'a': 1}
    assert read_block(text, label, required=False) == {'a': 1}
    for required in (True, False):
        with pytest.raises(CardBodyError):
            read_block(text * 2, label, required=required)
        with pytest.raises(CardBodyError):
            read_block(text.removesuffix('```\n'), label, required=required)
    with pytest.raises(CardBodyError, match=f'{label} JSON 解析失敗'):
        read_block(text.replace('{"a": 1}', '{bad}'), label)


@pytest.mark.parametrize('url', [
    'https://github.com/a/b/issues/1',
    'https://github.com/a/b/issues/1#issuecomment-no',
    'https://example.com/a/b/issues/1#issuecomment-123',
    'https://github.com/a/b/pull/1#issuecomment-123',
])
def test_bad_url_is_identifiable_without_network(url):
    runner = ApiFake()
    with pytest.raises(InvalidCommentURL):
        GhClient('a/b', runner=runner).comment_from_url(url)
    assert runner.calls == []


@pytest.mark.parametrize('value,data_type,operation', [
    ('選值', 'SINGLE_SELECT', 'updateProjectV2ItemFieldValue'),
    ('逐字', 'TEXT', 'updateProjectV2ItemFieldValue'),
    (None, 'SINGLE_SELECT', 'clearProjectV2ItemFieldValue'),
])
def test_field_name_id_option_resolution_and_clear(value, data_type, operation):
    runner = ApiFake()
    project = {'id': 'PROJECT', 'fields': [{'name': '呼叫端欄', 'id': 'FIELD', 'dataType': data_type}]}
    GhClient('a/b', runner=runner).set_project_field(project, 'ITEM', '呼叫端欄', value)
    payload = json.loads(runner.calls[-1][1]['input'])
    assert operation in payload['query']
    inputs = payload['variables']['input']
    assert {k: inputs[k] for k in ('projectId', 'itemId', 'fieldId')} == {
        'projectId': 'PROJECT', 'itemId': 'ITEM', 'fieldId': 'FIELD'}
    assert inputs.get('value') == (None if value is None else
                                  {'text': value} if data_type == 'TEXT' else {'singleSelectOptionId': 'OPTION'})


def test_add_remove_close_and_comment_interfaces():
    runner = ApiFake()
    client = GhClient('a/b', runner=runner)
    client.add_to_project('PROJECT', 'ISSUE')
    client.remove_from_project('PROJECT', 'ITEM')
    client.close_issue(295)
    client.post_comment(295, 'caller:first', '逐字\n第二行')
    payloads = [json.loads(kw['input']) for args, kw in runner.calls]
    assert 'addProjectV2ItemById' in payloads[0]['query']
    assert payloads[0]['variables']['input'] == {'projectId': 'PROJECT', 'contentId': 'ISSUE'}
    assert 'deleteProjectV2Item' in payloads[1]['query']
    assert payloads[1]['variables']['input'] == {'projectId': 'PROJECT', 'itemId': 'ITEM'}
    assert payloads[2] == {'state': 'closed'}
    assert payloads[3] == {'body': 'caller:first\n逐字\n第二行'}


def test_write_errors_keep_s02_classification():
    runner = lambda *a, **kw: SimpleNamespace(returncode=1, stdout='', stderr='gh: forbidden (HTTP 403)')
    with pytest.raises(PermissionDenied):
        GhClient('a/b', runner=runner).post_comment(295, 'wf:reject', 'reason')


def test_branch_queries_empty_nonempty_and_encoding():
    calls = []
    def runner(args, **kwargs):
        calls.append(args)
        rows = [] if len(calls) == 1 else [{'number': 293}]
        return SimpleNamespace(returncode=0, stdout=json.dumps(rows), stderr='')
    client = GhClient('owner/repo', runner=runner)
    assert client.pulls_for_branch('empty') == []
    assert client.pulls_for_branch('claude/wf-step6-cli') == [{'number': 293}]
    assert calls[-1][2] == 'repos/owner/repo/pulls?state=all&head=owner:claude%2Fwf-step6-cli&per_page=100&page=1'


def test_issues_filters_pr_and_keeps_paging():
    pages = [[{'number': 1}, {'number': 2, 'pull_request': {}}], [{'number': 3}]]
    calls = []
    def runner(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout=json.dumps(pages[len(calls) - 1]), stderr='')
    assert GhClient('a/b', runner=runner, page_size=2).issues() == [{'number': 1}, {'number': 3}]
    assert calls[-1][2] == 'repos/a/b/issues?state=all&per_page=2&page=2'


@pytest.mark.parametrize('method,args', [
    ('issue', [1]), ('comments', [1]), ('comment', [1]), ('project', ['a', 1, ['欄']]),
    ('commit_exists', ['abc']), ('branch_head', ['main']), ('pull_request', [1]),
    ('ci_checks', ['abc']), ('is_ancestor', ['abc']), ('issues', []), ('pulls_for_branch', ['branch']),
])
def test_shared_fake_programmable_reads(method, args):
    from .fakes import FakeGhClient
    fixed = FakeGhClient(**{method: {'sentinel': [True]}})
    assert getattr(fixed, method)(*args) == {'sentinel': [True]}
    dynamic = FakeGhClient(**{method: lambda **kw: kw})
    assert getattr(dynamic, method)(*args) == dynamic.calls[0][1]
    assert fixed.calls[0][0] == dynamic.calls[0][0] == method


def test_shared_fake_records_all_writes_in_order():
    from .fakes import FakeGhClient
    fake = FakeGhClient()
    fake.update_card_body(295, {'x': 1}, create=True)
    fake.post_comment(295, 'wf:reject', '拒收・D3・原因')
    fake.set_project_field({'id': 'P'}, 'I', '欄', None)
    fake.add_to_project('P', 'ISSUE')
    fake.remove_from_project('P', 'I')
    fake.close_issue(295)
    assert [name for name, kw in fake.calls] == ['update_card_body', 'post_comment', 'set_project_field',
                                                'add_to_project', 'remove_from_project', 'close_issue']
    assert fake.calls[0][1] == dict(number=295, card_json={'x': 1}, create=True)
    assert fake.calls[2][1]['value'] is None
    assert fake.responses == {}
