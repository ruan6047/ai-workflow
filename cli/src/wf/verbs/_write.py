"""消費 core/verbs.md §2、core/card-schema.md §1／§5／§6、core/naming.md §3。
呼叫端供給 catalog、模組與 Project 定位；不讀設定、不印、不產生動詞留言。
"""
from copy import deepcopy
from dataclasses import dataclass
import json

from wf.compose.blocks import projection
from wf.compose.schema import compose_schema
from wf.compose.transitions import is_legal_plan
from wf.compose.validate import validate, _equal
from wf.gh.writes import CardBodyError, block_span, read_card


@dataclass(frozen=True)
class WriteResult:
    rc: int
    card: dict | None = None
    reason: str = ''
    rejection: dict | None = None
    printed: tuple[str, ...] = ()


def reject(client, number, code, reason, printed=()):
    reason = ' '.join(reason.splitlines())
    comment = client.post_comment(number, 'wf:reject', f'拒收・{code}・{reason}')
    return WriteResult(1, reason=reason, rejection=comment, printed=printed)


def projected(card, catalog):
    values = {}
    for name, spec in projection(catalog).items():
        value = card[spec['key']]
        if spec['key'] == 'owner' and value is not None:
            value = f"{value['role']}:{value['actor']}"
        values[name] = value
    return values


def _values(project, item_id):
    item, = (item for item in project['items'] if item['id'] == item_id)
    return {name: (None if raw is None else raw.get('text', raw.get('name')))
            for name, raw in item['fieldValues'].items()}


def _prepare(card, current, projection_values, catalog, enabled_modules):
    card = deepcopy(card)
    if isinstance(card, dict) and _equal(card.get('schema_version'), 1):
        if projection_values is None:
            raise ValueError('無投影欄可回填 stage/state')
        card['schema_version'] = 2
        for name, spec in projection(catalog).items():
            if spec['key'] in ('stage', 'state'):
                if name not in projection_values:
                    raise ValueError('無投影欄可回填 stage/state')
                card[spec['key']] = projection_values[name]
    json.dumps(card, allow_nan=False)
    errors = validate(card, compose_schema(catalog, 'wf-card', enabled_modules))
    if errors:
        raise ValueError('; '.join(f'{e.path}: {e.message}' for e in errors))
    if current is not None and not isinstance(current, dict):
        raise CardBodyError('既有 wf-card 不是物件')
    for key in ('card_id', 'source_issue'):
        if current is not None and not _equal(card[key], current.get(key)):
            raise ValueError(f'{key} 建卡後不可改')
    if not is_legal_plan(card['stage_plan'], catalog=catalog):
        raise ValueError('stage_plan 不合階段序')
    values = projected(card, catalog)
    for name, spec in projection(catalog).items():
        value = values[name]
        if 'max_bytes' in spec and value is not None:
            if len(value.encode('utf-8')) > spec['max_bytes']:
                raise ValueError(f'{name} 超過 max_bytes')
    return card, values


def write_card(card_json, projection_values=None, *, client, number, catalog,
               project_owner=None, project_number=None, item_id=None, enabled_modules=(),
               write_projection=True, create=False):
    """projection_values 為讀卡時的投影快照；省略時由 Project 讀取。"""
    printed = ('無 Project 設定',) if None in (project_owner, project_number, item_id) else ()
    write_projection = write_projection and not printed
    project = client.project(project_owner, project_number, projection(catalog)) if write_projection else None
    try:
        body = client.issue(number)['body'] or ''
        current = None
        if block_span(body, 'wf-card', required=not create) is not None:
            current = read_card(body)
            if not isinstance(current, dict):
                raise CardBodyError('既有 wf-card 不是物件')
        source = projection_values
        if source is None and project is not None:
            source = _values(project, item_id)
        card, values = _prepare(card_json, current, source, catalog, enabled_modules)
        fields = [client.prepare_project_field(project, item_id, name, value)
                  for name, value in values.items()] if write_projection else []
    except (ValueError, TypeError, KeyError) as exc:
        return reject(client, number, 'D3', str(exc), printed)
    try:
        client.update_card_body(number, card, create=create)
    except CardBodyError as exc:
        return reject(client, number, 'D3', str(exc), printed)
    for field in fields:
        client.write_project_field(field)
    try:
        actual_card = read_card(client.issue(number)['body'] or '')
        actual = (_values(client.project(project_owner, project_number, projection(catalog)), item_id)
                  if write_projection else values)
    except (ValueError, TypeError, KeyError) as exc:
        return reject(client, number, 'D3', str(exc), printed)
    if not _equal(actual_card, card) or not _equal(actual, values):
        return reject(client, number, 'D3', '回讀不等', printed)
    return WriteResult(0, card=card, printed=printed)


def reconcile(card, *, client, catalog, project_owner, project_number, item_id):
    project = client.project(project_owner, project_number, projection(catalog))
    actual = _values(project, item_id)
    changed = []
    for name, value in projected(card, catalog).items():
        if not _equal(actual.get(name), value):
            client.set_project_field(project, item_id, name, value)
            changed.append(name)
    return changed
