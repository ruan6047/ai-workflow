"""交回單條號與卡面 `acceptance` 的機械對帳。消費 core/return.md（`wf-return` schema 的 `acceptance` 段）。

本檔釘的是**檢查器本身**，⛔ 不是某一份交回單：交回單住 GitHub 留言、⛔ 不在 repo 內，故以合成的
卡面／交回單配對證明 `numbering_defects` 有效（正控零缺陷、三種負控各自轉紅）。

**條數⛔ 不重打**：母體基數一律由傳進來的卡面 `acceptance` 清單自己決定，測試在多個不同基數上跑同
一個檢查器。規格改條數（本卡曾由 28 條換成 8 條）時本檔零改動——⛔ 不得推出「可以在此寫一個固定
條數當期望值」，那正是它取代的那個缺陷。
本檔的鍵名由 `core/return.md` 的 schema 解析取得（F-執行者-04：驗證器 `import` 或解析使用、⛔ 不重打）。
"""
import json
import re

import pytest

from .test_compose_schema import ROOT

RETURN_HOME = 'core/return.md'
SCHEMA_FENCE = '```json schema'
# 條號形狀：`A` 加十進位序數。前後界避免把 `SHA1`、`A1B2` 這類字串誤讀成條號。
CITED = re.compile(r'(?<![0-9A-Za-z])A([1-9][0-9]*)(?![0-9A-Za-z])')


def return_schema():
    """`core/return.md` 的 `wf-return` schema；⛔ 不重打鍵名。"""
    text = (ROOT / RETURN_HOME).read_text(encoding='utf-8')
    body = text.split(SCHEMA_FENCE, 1)[1].split('```', 1)[0]
    return json.loads(body)


def acceptance_item_keys():
    """交回單 `acceptance` 每項的必填鍵，逐字取自 schema。"""
    return tuple(return_schema()['properties']['acceptance']['items']['required'])


def acceptance_labels(card_acceptance):
    """卡面 `acceptance` → 條號序列 `A1`…`An`；基數由清單本身決定。"""
    return tuple(f'A{index}' for index in range(1, len(card_acceptance) + 1))


def cited_ids(value):
    """任意巢狀 JSON 值內出現的全部條號序數，去重後依數值排序。"""
    texts = []

    def walk(node):
        if isinstance(node, str):
            texts.append(node)
        elif isinstance(node, dict):
            for item in node.values():
                walk(item)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(value)
    return sorted({int(found) for text in texts for found in CITED.findall(text)})


def numbering_defects(card_acceptance, return_note):
    """回三類缺陷；三者皆空＝交回單的條號面與卡面相符。

    - `count`：交回單 `acceptance` 段條數 ≠ 卡面條數時回 (交回單條數, 卡面條數)。
    - `stale`：交回單任一處引用的條號超出卡面現行條數（⛔ 不限 `acceptance` 段，散文也算）。
    - `text_mismatch`：逐條 `text` 與卡面同序條文⛔ 不逐字相等的條號。
    """
    count = len(card_acceptance)
    listed = return_note.get('acceptance') or []
    labels = acceptance_labels(card_acceptance)
    return {
        'count': None if len(listed) == count else (len(listed), count),
        'stale': [f'A{found}' for found in cited_ids(return_note) if found > count],
        'text_mismatch': [labels[index] for index, item in enumerate(listed[:count])
                          if item.get(acceptance_item_keys()[0]) != card_acceptance[index]],
    }


def synthetic(count):
    """一份合成的 (卡面 `acceptance`, 交回單)，條數為 `count` 且三類缺陷皆空。"""
    card = [f'第 {index} 條的條文。' for index in range(1, count + 1)]
    keys = acceptance_item_keys()
    note = {'card_id': 'ZZZ-000', 'iteration': 1, 'role': 'executor', 'source_sha': '0' * 40,
            'acceptance': [dict(zip(keys, (text, '做法', '證據', '推翻'))) for text in card],
            'measurement': f'現行 {count} 條，最後一條是 A{count}。'}
    return card, note


@pytest.mark.parametrize('count', [1, 3, 8, 28, 40])
def test_the_numbering_check_passes_on_a_matching_pair(count):
    """正控：任一基數上，相符的配對三類缺陷皆空（⇒ 檢查器⛔ 不依賴任何固定條數）。"""
    card, note = synthetic(count)
    assert acceptance_labels(card) == tuple(f'A{i}' for i in range(1, count + 1))
    assert numbering_defects(card, note) == {'count': None, 'stale': [], 'text_mismatch': []}
    print('NUMBERING ok count', count, 'labels', acceptance_labels(card)[-1])


@pytest.mark.parametrize('count', [1, 3, 8, 28, 40])
def test_each_defect_class_has_a_negative_control(count):
    """負控（三種都必須會響）：條數不符、引用逾界條號、逐條條文不符。"""
    card, note = synthetic(count)
    short = {**note, 'acceptance': note['acceptance'][:-1]}
    assert numbering_defects(card, short)['count'] == (count - 1, count), count
    stale = {**note, 'measurement': f'沿用上一版：A{count + 1}／A{count + 3}。'}
    assert numbering_defects(card, stale)['stale'] == [f'A{count + 1}', f'A{count + 3}'], count
    drifted = {**note, 'acceptance': [{**note['acceptance'][0], acceptance_item_keys()[0]: '別的條文'},
                                      *note['acceptance'][1:]]}
    assert numbering_defects(card, drifted)['text_mismatch'] == ['A1'], count
    print('NEGATIVE_CONTROL numbering count', count, 'short/stale/drift all red')


def test_the_item_keys_come_from_the_rules_body():
    """鍵名的唯一居所＝`core/return.md` 的 schema；⛔ 不在本檔重打。"""
    keys = acceptance_item_keys()
    assert len(keys) == 4 and keys[0] == 'text', keys
    assert set(keys) <= set(return_schema()['properties']['acceptance']['items']['properties']), keys
    print('RETURN_ACCEPTANCE_KEYS', list(keys), 'home', f'{RETURN_HOME}#{SCHEMA_FENCE}')


def test_the_citation_scanner_ignores_non_ids():
    """`A` 開頭但⛔ 非條號的字串（SHA、識別碼）⛔ 不得被讀成條號，否則負控會假響。"""
    assert cited_ids({'a': '見 A7 與 A12'}) == [7, 12]
    assert cited_ids({'a': 'A1B2 與 SHA1 與 abcA9'}) == []
    assert cited_ids(['巢狀', {'b': ['A3']}]) == [3]
    print('CITED_IDS positive [7, 12] negative []')
