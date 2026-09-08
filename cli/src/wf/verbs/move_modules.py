"""消費 core/verbs.md §1 move［3］［4］／§2 末、modules/escalation/module.md §0–1、
modules/resource-lock/module.md §0–1、modules/initiative/module.md §0–1、
core/card-schema.md §5、stages/closeout.md F-結案-02／03、ADOPTION.md §2；S09 派工單的 PM 預設。

註冊表的鍵＝模組 §0 `adds.counters`／`adds.move_prints` 宣告的 id，值＝該 id 的實作；
啟用判定與轉移合法性由呼叫端（S08）先做，本層只依宣告算計數與印，⛔ 不擋（第零條）。
"""
from copy import deepcopy

from wf.compose.blocks import projection
from wf.compose.project_config import module_params
from wf.verbs._common import block_object, board_items, field_values

# 狀態與階段字面＝各模組 §1 條文的語意，逐字對應該模組宣告的 id；值域住 core/enums.md。
RETURNED, IN_PROGRESS, ESCALATED, EXEC_STAGE = '退回', '進行中', '升級', '執行'
UNIMPLEMENTED = '未實作的模組印項／計數 {}'
NO_PROJECT = '無 Project 設定，未評估 {}'


def _state(node):
    """`階段/狀態`；阻塞節點形如 `階段/阻塞←來源狀態`（compose/transitions.blocked_node）。"""
    return node.partition('/')[2].partition('←')[0]


def _declarations(catalog, enabled_names=None):
    names = None if enabled_names is None else set(enabled_names)
    return [block.data for block in catalog.by_label('yaml wf-module')
            if names is None or block.data['name'] in names]


def _terminal_states(catalog):
    """終態值域住 core/enums.md `json wf-enums` 的 states_terminal；⛔ 不在程式碼寫死。"""
    enums, = catalog.by_label('json wf-enums')
    return set(enums.data['states_terminal']['enum'])


def escalation_count(card, from_node, to_node):
    """escalation §1 第 1 條：退回 +1；進執行（iteration +1 的同一轉移）與 升級→進行中 歸零。"""
    count = card.get('escalation_count', 0)
    if _state(to_node) == RETURNED:
        return count + 1
    if to_node == f'{EXEC_STAGE}/{IN_PROGRESS}':
        return 0
    if _state(from_node) == ESCALATED and _state(to_node) == IN_PROGRESS:
        return 0
    return count


def escalation_threshold(card, from_node, to_node, *, module, config, **_):
    """escalation §1 第 3 條「達」；現值取 .wf/modules.json 的 params，缺則模組宣告的種子。"""
    seed = module['params']['escalate_after']
    threshold = module_params(config, module['name']).get('escalate_after', seed)
    lines = []
    if type(threshold) is not int:
        lines.append(f'escalate_after 不合法，改用種子 {seed}')
        threshold = seed
    if card.get('escalation_count', 0) >= threshold:
        lines.append('達升級門檻')
    return lines


def resources_intersection(card, from_node, to_node, *, catalog, project, client, **_):
    """resource-lock §1 第 1–2 條：派工邊印交集；完全字串比對，⛔ 不自動擋。

    現役卡母體依 §1 第 3 條轉指 stages/closeout.md F-結案-03（進 main 未結案的卡仍算現役）
    與 F-結案-02（終態才釋放宣告的資源）：板上非 isArchived、同 repo、狀態不在
    core/enums.md states_terminal，且 owner 非 null 而 owner.actor 與本卡不同的卡；
    交集所需的 resources 不在投影欄，逐張回讀 issue 卡面（core/card-schema.md §5）。
    啟用條件（§0 enable_if 的「進行中」）是另一回事，由呼叫端 S03 判，本層⛔ 不重判。
    """
    if _state(to_node) != IN_PROGRESS:
        return []
    names = {spec['key']: name for name, spec in projection(catalog).items()}
    terminal = _terminal_states(catalog)
    actor = (card.get('owner') or {}).get('actor')
    mine = card.get('resources') or []
    lines, matched, unread = [], False, False
    for number, item in board_items(project, client.repo).items():
        values = field_values(item)
        if values.get(names['state']) in terminal:
            continue
        owner = values.get(names['owner'])
        if not owner or owner.partition(':')[2] == actor:
            continue
        card_id = values.get(names['card_id'])
        try:
            other = block_object(client.issue(number)['body'], 'wf-card')
            resources = other.get('resources') or []
        except (ValueError, TypeError, KeyError, RuntimeError):
            lines.append(f'無法讀取 {card_id} 的 resources')
            unread = True
            continue
        for resource in mine:
            if resource in resources:
                lines.append(f'{resource} ↔ {card_id}')
                matched = True
    if not matched and not unread:
        lines.append('無交集')
    return lines


def parent_spec_version_empty(card, from_node, to_node, **_):
    """initiative §1 第 3 條：空值由 move 印；⛔ 不擋（⛔ 不派工是 PM 規則）。"""
    if card.get('parent_spec_version') is not None:
        return []
    return ['parent_spec_version 空值']


COUNTERS = {'escalation_count': escalation_count}
MOVE_PRINTS = {'escalation_threshold': escalation_threshold,
               'resources_intersection': resources_intersection,
               'parent_spec_version_empty': parent_spec_version_empty}


def apply_counters(card, from_node, to_node, *, catalog, config, enabled_names):
    """verbs.md §1 move 寫欄列：已啟用模組 adds.counters 列的欄；寫入前先算。"""
    card = deepcopy(card)
    for module in _declarations(catalog, enabled_names):
        for identifier in module['adds'].get('counters', []):
            counter = COUNTERS.get(identifier)
            if counter is not None:
                card[identifier] = counter(card, from_node, to_node)
    return card


def module_prints(card, from_node, to_node, *, catalog, config, enabled_names,
                  project, client):
    """verbs.md §1 move 印列：已啟用模組 adds.move_prints 列的印項；門檻用更新後的計數值。"""
    enabled = set(enabled_names)
    lines = []
    for module in _declarations(catalog):
        if module['name'] not in enabled:
            if project is None and module['enable_if']['kind'] == 'other_actor_card_in_state':
                lines.append(NO_PROJECT.format(module['name']))
            continue
        adds = module['adds']
        for identifier in adds.get('counters', []):
            if identifier not in COUNTERS:
                lines.append(UNIMPLEMENTED.format(identifier))
        for identifier in adds.get('move_prints', []):
            emit = MOVE_PRINTS.get(identifier)
            if emit is None:
                lines.append(UNIMPLEMENTED.format(identifier))
                continue
            lines.extend(emit(card, from_node, to_node, module=module, config=config,
                              catalog=catalog, project=project, client=client))
    return lines
