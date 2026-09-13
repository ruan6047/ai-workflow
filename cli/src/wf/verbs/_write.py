"""消費 core/verbs.md §2、core/card-schema.md §1／§5／§6、core/naming.md §3。
呼叫端供給 catalog、模組與 Project 定位；不讀設定、不印、不產生動詞留言。
"""
from copy import deepcopy
from dataclasses import dataclass
import json
import time

from wf.compose.blocks import projection
from wf.compose.schema import compose_schema
from wf.compose.transitions import is_legal_plan
from wf.compose.validate import validate, _equal
from wf.gh.writes import CardBodyError
from wf.verbs._common import block_object, board_items, field_values


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


def blocked(report, code, reason):
    """本機硬擋（§2 留痕綁被拒的那一次遠端寫入）：沒有遠端寫入可擋時只印一行
    `硬擋・<code>・<原因>`，⛔ 不碰 client、⛔ 不寫任何遠端，rejection 留 None。
    折行規則與 reject 相同（換行折成空白）；report＝呼叫端的 Printer。"""
    reason = ' '.join(reason.splitlines())
    report(f'硬擋・{code}・{reason}')
    return WriteResult(1, reason=reason, printed=tuple(report))


def projected(card, catalog, check=False):
    """check=True 另驗 §5 max_bytes（UTF-8 位元組，D3）；snapshot 唯讀對帳（§2 例外）要原值，故預設不驗。"""
    values = {}
    for name, spec in projection(catalog).items():
        value = card[spec['key']]
        if spec['key'] == 'owner' and value is not None:
            value = f"{value['role']}:{value['actor']}"
        if check and 'max_bytes' in spec and value is not None and len(value.encode('utf-8')) > spec['max_bytes']:
            raise ValueError(f'{name} 超過 max_bytes')
        values[name] = value
    return values


def _matched(project, item_id):
    """Project 查詢結果裡 id 相符的項；0 筆＝暫時不可見（可重試），>1 筆＝重複（⛔ 不可重試）。"""
    return [item for item in project['items'] if item['id'] == item_id]


def projection_values(project, item_id):
    item, = _matched(project, item_id)
    return field_values(item)


# GitHub Projects 的 items 查詢是最終一致的：addProjectV2ItemById 已經回了 item id，之後的
# projectV2 查詢仍可能看不到那一項（PM 2026-09-10 在 issue #306 實測 2/2 重現，非偶發）。
# 3＝首查加 2 次唯讀重試、間隔 0.5 秒：觀察到的延遲落在一次查詢往返之內，兩次重試（最多多等
# 1 秒）足以蓋過；再加次數只會讓「item 真的不在這塊板上」這種永遠查不到的情形拖著操作者等。
_ITEM_LOOKUP_ATTEMPTS = 3
_ITEM_LOOKUP_INTERVAL = 0.5


class ItemLookupTimeout(ValueError):
    """有界唯讀重試耗盡，Project 查詢仍看不到該 item；ValueError 子類，仍收斂到既有 D3。"""


def lookup_values(project, item_id, refetch):
    """有界唯讀重試取投影快照：只有「查詢結果裡沒有這一項」才重抓 Project（唯讀），
    ⛔ 不重跑任何寫入。其餘真因（同 id 多筆＝重複、Project 形狀壞掉的 TypeError／KeyError）
    原樣往上拋，交給呼叫端既有的泛用 except 用真訊息拒收——⛔ 不改寫成「查不到」：
    reject 只取 str(exc)、__cause__ 不進遠端留言，改寫等於在遠端留下錯的診斷。"""
    for attempt in range(1, _ITEM_LOOKUP_ATTEMPTS + 1):
        matched = _matched(project, item_id)
        if matched:
            item, = matched  # >1 ⇒ ValueError('too many values to unpack')，原樣往上拋
            return field_values(item)
        if attempt == _ITEM_LOOKUP_ATTEMPTS:
            raise ItemLookupTimeout(f'Project 查不到 item {item_id}'
                                    f'（唯讀重抓 {_ITEM_LOOKUP_ATTEMPTS} 次仍不可見）')
        time.sleep(_ITEM_LOOKUP_INTERVAL)
        project = refetch()


def needs_snapshot(card):
    """要不要舊投影快照＝卡面是不是 v1（唯一用途是 1→2 回填 stage/state）。
    ⛔ 不以 create 為判準：撤銷卡復板也傳 create=True，拿它當條件會讓 v1 卡從遷移成功
    變成『無投影欄可回填 stage/state』拒收（gpt-6-astra 2026-09-10 離線探針證偽）。
    ⚠️ 三個動詞入口都不會把 v1 卡送進 write_card：open 先過 prepare_card、move 自己先遷移過、
    edit 被 core/card-schema.md 的 schema_version const 2 擋在 validate 就拒收；⛔ 別以為
    edit 依賴這裡。此判準只服務直呼 write_card 的呼叫端（如 test_write_flow.py::
    test_migration_only_version_stage_state），留著比刪安全，故 ⛔ 未刪。"""
    return isinstance(card, dict) and _equal(card.get('schema_version'), 1)


def written_so_far(values):
    """update_card_body 之後才拒收時，讓操作者知道遠端已經被寫成什麼樣；三個 post-write
    出口都要帶，否則讀者會把「沒有這行」反推成「沒寫入」。values＝實際寫進投影欄的那批：
    無 Project 設定／write_projection=False 時傳空的，⛔ 不得列出沒發生的投影寫入。"""
    lines = ['已完成的寫入：卡面 JSON']
    if values:
        lines.append('已完成的寫入：投影欄 ' + '、'.join(values))
    return tuple(lines)


def prepare_card(card, current, snapshot, catalog, enabled_modules):
    """snapshot＝讀卡時的投影快照（1→2 遷移回填 stage/state 用）。"""
    card = deepcopy(card)
    if needs_snapshot(card):
        if snapshot is None:
            raise ValueError('無投影欄可回填 stage/state')
        card['schema_version'] = 2
        for name, spec in projection(catalog).items():
            if spec['key'] in ('stage', 'state'):
                if name not in snapshot:
                    raise ValueError('無投影欄可回填 stage/state')
                card[spec['key']] = snapshot[name]
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
    return card, projected(card, catalog, check=True)


_values, _prepare = projection_values, prepare_card  # 舊名別名（既有呼叫端）


def write_card(card_json, projection_values=None, *, client, number, catalog,
               project_owner=None, project_number=None, item_id=None, enabled_modules=(),
               write_projection=True, create=False):
    """projection_values 為讀卡時的投影快照；省略時只在卡面是 v1（needs_snapshot）時才由 Project
    讀取——新卡不去查剛加進板的 item（參數遮蔽同名函式，取快照一律經 lookup_values）。
    取快照那條分支在三個動詞入口皆走不到（見 needs_snapshot），只供直呼 write_card 的呼叫端。"""
    printed = ('無 Project 設定',) if None in (project_owner, project_number, item_id) else ()
    write_projection = write_projection and not printed

    def fetch_project():
        return client.project(project_owner, project_number, projection(catalog))

    project = fetch_project() if write_projection else None
    try:
        current = block_object(client.issue(number)['body'], 'wf-card', required=not create)
        source = projection_values
        if source is None and project is not None and needs_snapshot(card_json):
            source = lookup_values(project, item_id, fetch_project)
        card, values = prepare_card(card_json, current, source, catalog, enabled_modules)
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
    # 三個 post-write 出口一律帶已完成的寫入：此處卡面已寫，投影欄則以 fields 是否為空為準
    done = (*printed, *written_so_far(values if fields else {}))
    try:
        actual_card = block_object(client.issue(number)['body'], 'wf-card')
        actual = (lookup_values(fetch_project(), item_id, fetch_project)
                  if write_projection else values)
    except (ValueError, TypeError, KeyError) as exc:  # 含重試耗盡的 ItemLookupTimeout
        return reject(client, number, 'D3', str(exc), done)
    if not _equal(actual_card, card) or not _equal(actual, values):
        return reject(client, number, 'D3', '回讀不等', done)
    return WriteResult(0, card=card, printed=printed)


def reconcile(card, *, client, catalog, project_owner, project_number, item_id):
    project = client.project(project_owner, project_number, projection(catalog))
    values, actual, fields = projected(card, catalog, check=True), projection_values(project, item_id), {}
    for name in [key for key, value in values.items() if not _equal(actual.get(key), value)]:
        try:  # §2 檢查先於首次遠端寫入：不等的欄整批算完（含單選選項解析）才開始寫
            fields[name] = client.prepare_project_field(project, item_id, name, values[name])
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError(f'{name} 投影欄無法解析：{exc}') from exc
    for field in fields.values():
        client.write_project_field(field)
    return list(fields)


def check_card(card, *, client, number, catalog, enabled_modules=(), printed=(), fail=None):
    """§2 D3 鍵集合封閉、整卡拒：不合成後 schema 即該卡動詞⛔ 不再往下跑。
    fail＝呼叫端指定的失敗處置（取原因字串回 WriteResult）；缺省＝寫一則 wf:reject 的遠端拒收，
    讀側動詞改傳本機硬擋（blocked）。"""
    schema = compose_schema(catalog, 'wf-card', enabled_modules)
    failures = validate(card, schema)
    if not failures:
        return None
    reason = '; '.join(f'{e.path}: {e.message}' for e in failures)
    return reject(client, number, 'D3', reason, printed) if fail is None else fail(reason)


def reconcile_projection(card, *, client, catalog, location, project, number, report):
    """§2 對帳：不等即以卡面 JSON 重寫該欄後續跑並印，⛔ 不拒收；無 Project／不在板上略過；欄算不出＝零業務寫入的單一 D3 拒收（回非 None，呼叫端即停）。"""
    if location is None or project is None or any(
            spec['key'] not in card for spec in projection(catalog).values()):
        return None  # 缺投影鍵＝各動詞的驗卡面（check_card／prepare_card）處置，此處 ⛔ 不對帳
    item_id = board_items(project, client.repo, include_archived=True).get(number, {}).get('id')
    if item_id is None:
        return None
    try:
        changed = reconcile(card, client=client, catalog=catalog, item_id=item_id,
                            project_owner=location['owner'], project_number=location['number'])
    except (ValueError, TypeError, KeyError) as exc:
        return reject(client, number, 'D3', str(exc), tuple(report))
    if changed:
        report('重寫投影欄：' + '、'.join(changed))
    return None
