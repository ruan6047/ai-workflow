"""core/verbs.md §2；core/card-schema.md §1／§5／§6。"""
from copy import deepcopy
import json

import pytest

from wf.compose.blocks import LABELS, Block, Catalog, projection
from wf.verbs import _write as write
from wf.gh.writes import WriteMixin
from .fakes import FakeGhClient
from .test_compose_schema import ROOT, card, catalog


class ProjectionFake(FakeGhClient, WriteMixin):
    """沿用共用替身，欄／選項解析走正式實作；此切片不修改共用 fakes.py。"""
    def prepare_project_field(self, project, item_id, name, value):
        prepared = WriteMixin.prepare_project_field(self, project, item_id, name, value)
        self.calls.append(('prepare_project_field', dict(name=name, prepared=prepared)))
        return prepared, project, item_id, name, value

    def write_project_field(self, field):
        prepared, project, item_id, name, value = field
        self.calls.append(('write_project_field', dict(name=name, value=value, prepared=prepared)))
        return {'data': {prepared[0]: {'projectV2Item': {'id': item_id}}}}

    def _request(self, endpoint, **kwargs):
        assert endpoint == 'graphql' and 'query' in kwargs and 'payload' not in kwargs
        return self._read('options', field_id=kwargs['variables']['id'])


def body(value):
    return '散文\n```json wf-card\n' + json.dumps(value, ensure_ascii=False) + '\n```\n尾文'


def project_of(values):
    return {'id': 'PROJECT',
            'fields': [{'id': name, 'name': name, 'dataType': 'TEXT'} for name in values],
            'items': [{'id': 'ITEM', 'fieldValues': {
        name: None if value is None else {'text': value} for name, value in values.items()}}]}


def simulated(card, catalog, *, mismatch=(), bad_body=False):
    """回應模型獨立讀 calls；FakeGhClient 本身不假裝已寫遠端。"""
    initial = deepcopy(card)
    values = write.projected(card, catalog) if card.get('schema_version') == 2 else {
        name: {'stage': '執行', 'state': '進行中'}.get(spec['key'], card.get(spec['key']))
        for name, spec in projection(catalog).items()}
    fake = ProjectionFake()

    def issue(**kwargs):
        written = [kw['card_json'] for name, kw in fake.calls if name == 'update_card_body']
        return {'body': body(initial if bad_body or not written else written[-1])}

    def project(**kwargs):
        result = deepcopy(values)
        for name, kw in fake.calls:
            if name == 'write_project_field' and kw['name'] not in mismatch:
                result[kw['name']] = kw['value']
        return project_of(result)

    fake.responses = dict(issue=issue, project=project)
    return fake


def run(card, catalog, fake, **kwargs):
    options = dict(client=fake, number=295, catalog=catalog, project_owner='owner',
                   project_number=1, item_id='ITEM')
    return write.write_card(card, **(options | kwargs))


def mutations(fake, method=None):
    names = {'update_card_body', 'write_project_field', 'post_comment'} if method is None else {method}
    return [(name, kw) for name, kw in fake.calls if name in names]


def assert_reject(result, fake):
    assert result.rc != 0
    comments = mutations(fake, 'post_comment')
    assert len(comments) == 1
    assert comments[0][1]['first_line'] == 'wf:reject'
    assert comments[0][1]['body'].startswith('拒收・D3・')
    assert '\n' not in comments[0][1]['body']


def test_projection_original_order_and_runtime_reload(catalog):
    text = (ROOT / 'core/card-schema.md').read_text()
    raw = text.split('```json wf-projection\n')[1].split('```')[0]
    assert 'json wf-projection' in LABELS
    expected = json.loads(raw)
    assert list(projection(catalog).items()) == list(expected.items())
    assert len(expected) == 5
    original, = catalog.by_label('json wf-projection')
    changed = {'自訂欄': {'key': 'card_id', 'max_bytes': 7}}
    blocks = [Block(b.label, changed, json.dumps(changed), b.source) if b is original else b
              for b in catalog.blocks]
    assert projection(Catalog(blocks, catalog.schemas)) == changed
    print('PROJECTION', json.dumps(expected, ensure_ascii=False))


def test_write_order_and_equal_readback(card, catalog):
    fake = simulated(card, catalog)
    updated = card | {'stage': '執行', 'state': '進行中'}
    result = run(updated, catalog, fake)
    assert result.rc == 0 and result.card == updated
    print('WRITE_ORDER', [name for name, kw in fake.calls])
    assert [name for name, kw in mutations(fake)] == ['update_card_body'] + ['write_project_field'] * len(projection(catalog))
    assert [kw['name'] for name, kw in mutations(fake, 'write_project_field')] == list(projection(catalog))
    assert [name for name, kw in fake.calls][-2:] == ['issue', 'project']
    first_write = next(i for i, (name, kw) in enumerate(fake.calls) if name == 'update_card_body')
    assert [kw['name'] for name, kw in fake.calls[:first_write]
            if name == 'prepare_project_field'] == list(projection(catalog))


def test_readback_mismatch_rejects_once(card, catalog):
    name = next(iter(projection(catalog)))
    fake = simulated(card, catalog, mismatch=(name,))
    result = run(card | {'stage': '執行'}, catalog, fake)
    print('READBACK_RESULT', result.rc, 'REJECT_COMMENTS', len(mutations(fake, 'post_comment')))
    assert_reject(result, fake)
    assert result.reason == '回讀不等'
    assert len(mutations(fake, 'write_project_field')) == len(projection(catalog))


@pytest.mark.parametrize('change', [
    {'unknown': True}, {'tier': 'T9'}, {'card_id': 'WF-002'}, {'source_issue': 2},
    {'stage_plan': ['結案', '需求']}, {'iteration': True}, {'feature': float('nan')},
    {'schema_version': True},
])
def test_prevalidation_rejects_before_data_writes(card, catalog, change):
    fake = simulated(card, catalog)
    result = run(card | change, catalog, fake)
    print('DATA_WRITE_COUNTS', len(mutations(fake, 'update_card_body')), len(mutations(fake, 'write_project_field')))
    assert not mutations(fake, 'update_card_body')
    assert_reject(result, fake)
    assert not mutations(fake, 'update_card_body')
    assert not mutations(fake, 'write_project_field')


@pytest.mark.parametrize('key', ['owner', 'card_id'])
@pytest.mark.parametrize('extra', [0, 1])
def test_utf8_max_bytes_from_projection(card, catalog, key, extra):
    spec = next(s for s in projection(catalog).values() if s['key'] == key)
    if key == 'owner':
        prefix = 'executor:'
        size = spec['max_bytes'] - len(prefix)
        text = '中' * (size // 3) + 'a' * (size % 3 + extra)
        card[key] = {'role': 'executor', 'actor': text}
    else:
        card[key] = 'WF-' + '1' * (spec['max_bytes'] - 3 + extra)
    fake = simulated(card, catalog)
    result = run(card, catalog, fake, write_projection=False)
    assert result.rc == extra
    if extra:
        assert_reject(result, fake)
        assert not mutations(fake, 'update_card_body')
    assert not any(name in ('project', 'write_project_field') for name, kw in fake.calls)


@pytest.mark.parametrize('changes', [(), ('stage',), ('stage', 'state', 'tier')])
def test_reconcile_only_differing_fields(card, catalog, changes):
    expected = write.projected(card, catalog)
    names = [name for name, spec in projection(catalog).items() if spec['key'] in changes]
    actual = {name: '不同' if name in names else value for name, value in expected.items()}
    fake = ProjectionFake(project=project_of(actual))  # 對帳走 prepare→write
    assert write.reconcile(card, client=fake, catalog=catalog, project_owner='owner',
                           project_number=1, item_id='ITEM') == names
    assert [(kw['name'], kw['value']) for name, kw in mutations(fake)] == [(name, expected[name]) for name in names]
    assert not mutations(fake, 'post_comment')


@pytest.mark.parametrize('option', [dict(write_projection=False), dict(project_owner=None),
                                    dict(project_number=None), dict(item_id=None)])
@pytest.mark.parametrize('bad_body', [False, True])
def test_without_project_still_checks_card(card, catalog, option, bad_body):
    fake = simulated(card, catalog, bad_body=bad_body)
    result = run(card | {'feature': '更新'}, catalog, fake, **option)
    assert result.rc == int(bad_body)
    assert not any(name in ('project', 'write_project_field') for name, kw in fake.calls)
    assert result.printed == (() if 'write_projection' in option else ('無 Project 設定',))
    if bad_body:
        assert_reject(result, fake)
    else:
        assert not mutations(fake, 'post_comment')


def test_migration_only_version_stage_state(card, catalog):
    del card['stage'], card['state']
    card['schema_version'] = 1
    card['feature'] = '保留逐字'
    original = deepcopy(card)
    fake = simulated(card, catalog)
    result = run(card, catalog, fake)
    assert result.rc == 0
    assert result.card == original | {'schema_version': 2, 'stage': '執行', 'state': '進行中'}
    assert card == original
    assert result.card == json.loads(fake.issue(295)['body'].split('```json wf-card\n')[1].split('\n```')[0])


@pytest.mark.parametrize('option', [dict(write_projection=False), dict(project_owner=None)])
def test_migration_requires_projection(card, catalog, option):
    card['schema_version'] = 1
    fake = simulated(card, catalog)
    result = run(card, catalog, fake, **option)
    assert_reject(result, fake)
    assert result.reason == '無投影欄可回填 stage/state'
    assert not mutations(fake, 'update_card_body')


def test_create_without_current_skips_immutable_keys(card, catalog):
    fake = simulated(card, catalog)
    original_read = fake.responses['issue']
    fake.responses['issue'] = lambda **kw: original_read(**kw) if mutations(fake, 'update_card_body') else {'body': '原散文'}
    assert run(card, catalog, fake, create=True, write_projection=False).rc == 0
    assert mutations(fake, 'update_card_body')[0][1]['create'] is True


@pytest.mark.parametrize('bad', ['null', '{broken}', '{}\n```\n```json wf-card\n{}'])
def test_invalid_current_or_readback_reject(card, catalog, bad):
    fake = FakeGhClient(issue={'body': '```json wf-card\n' + bad + '\n```'})
    result = run(card, catalog, fake, write_projection=False)
    assert_reject(result, fake)
    assert not mutations(fake, 'update_card_body')


def test_reject_normalizes_reason_lines():
    fake = FakeGhClient()
    result = write.reject(fake, 295, 'D3', '一\n二\r\n三')
    assert_reject(result, fake)
    assert result.reason == '一 二 三'


def test_migration_uses_supplied_snapshot_without_project_io(card, catalog):
    snapshot = write.projected(card | {'stage': '執行', 'state': '進行中'}, catalog)
    card['schema_version'] = 1
    del card['stage'], card['state']
    fake = simulated(card, catalog)
    result = run(card, catalog, fake, write_projection=False, projection_values=snapshot)
    assert result.rc == 0 and result.card['stage'] == '執行' and result.card['state'] == '進行中'
    assert not any(name in ('project', 'write_project_field') for name, kw in fake.calls)


@pytest.mark.parametrize('missing', ['body', 'item'])
def test_missing_readback_data_is_d3(card, catalog, missing):
    fake = simulated(card, catalog)
    if missing == 'body':
        previous = fake.responses['issue']
        fake.responses['issue'] = lambda **kw: {'body': None} if mutations(fake, 'update_card_body') else previous(**kw)
    else:
        previous = fake.responses['project']
        fake.responses['project'] = lambda **kw: {'items': []} if mutations(fake, 'write_project_field') else previous(**kw)
    assert_reject(run(card, catalog, fake), fake)


def test_null_readback_card_block_is_d3(card, catalog):
    """null 區塊探針：寫入後回讀的 wf-card 值為 null ⇒ D3（不是物件），恰一則 wf:reject。"""
    fake = simulated(card, catalog)
    previous = fake.responses['issue']
    fake.responses['issue'] = lambda **kw: ({'body': '```json wf-card\nnull\n```'}
                                           if mutations(fake, 'update_card_body') else previous(**kw))
    result = run(card, catalog, fake)
    assert_reject(result, fake)
    assert '不是物件' in result.reason


def test_runtime_projection_max_bytes_drives_validation(card, catalog):
    original, = catalog.by_label('json wf-projection')
    changed = deepcopy(projection(catalog))
    name = next(n for n, spec in changed.items() if spec['key'] == 'owner')
    changed[name]['max_bytes'] = 1
    blocks = [Block(b.label, changed, json.dumps(changed), b.source) if b is original else b
              for b in catalog.blocks]
    modified = Catalog(blocks, catalog.schemas)
    card['owner'] = {'role': 'executor', 'actor': 'x'}
    fake = simulated(card, modified)
    result = run(card, modified, fake, write_projection=False)
    assert_reject(result, fake)
    assert result.reason == name + ' 超過 max_bytes'
    assert not mutations(fake, 'update_card_body')


@pytest.mark.parametrize('missing', ['option', 'field'])
def test_projection_resolution_precedes_data_writes(card, catalog, missing):
    fake = simulated(card, catalog)
    names = list(projection(catalog))
    previous = fake.responses['project']

    def project(**kwargs):
        result = previous(**kwargs)
        for field in result['fields'][:2]:
            field['dataType'] = 'SINGLE_SELECT'
        if missing == 'field':
            del result['fields'][1]
        return result

    values = write.projected(card, catalog)
    fake.responses['project'] = project
    fake.responses['options'] = lambda field_id: {'data': {'node': {'options':
        [] if field_id == names[1] else [{'id': 'OPTION', 'name': values[field_id]}]}}}
    result = run(card, catalog, fake)
    assert_reject(result, fake)
    assert [kw['name'] for method, kw in fake.calls if method == 'prepare_project_field'] == names[:1]
    assert not mutations(fake, 'update_card_body')
    assert not mutations(fake, 'write_project_field')
    print('PROJECTION_REJECT', missing, 'RC', result.rc, 'COMMENTS', len(mutations(fake, 'post_comment')),
          'BODY_WRITES', len(mutations(fake, 'update_card_body')),
          'FIELD_WRITES', len(mutations(fake, 'write_project_field')))
