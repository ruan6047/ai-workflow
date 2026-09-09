"""消費 modules/escalation/module.md §0–1、core/verbs.md §1 move［4］／§2 末、ADOPTION.md §2。
計數、兩個歸零邊、params 三案、未啟用不計不印。
"""
import json
from pathlib import Path

import pytest

from wf.compose.blocks import load_blocks
from wf.compose.project_config import load_project_config
from wf.verbs.move_modules import apply_counters, module_prints

RULES = Path(__file__).resolve().parents[2]
THRESHOLD = '達升級門檻'


@pytest.fixture(scope='module')
def catalog():
    return load_blocks(RULES)


def config(tmp_path, params=None, listed=True):
    """.wf/modules.json 形狀逐字依 ADOPTION.md §2 modules[].params。"""
    module = {'name': 'escalation'}
    if params is not None:
        module['params'] = params
    payload = {'modules': [module] if listed else [], 'merge_method': 'squash', 'areas': ['WF']}
    (tmp_path / '.wf').mkdir(exist_ok=True)
    (tmp_path / '.wf/modules.json').write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    return load_project_config(tmp_path)


def card(**changes):
    return {'card_id': 'WF-001', 'owner': {'role': 'executor', 'actor': 'me'},
            'resources': [], 'parent': None, 'parent_spec_version': None} | changes


def run_edges(catalog, cfg, names=('escalation',), start=None,
              edges=(('審核/待確認', '審核/退回'),) * 4):
    """逐邊套用計數再取印項；印項用更新後的卡。"""
    current, counts, prints = card() if start is None else start, [], []
    for source, target in edges:
        current = apply_counters(current, source, target, catalog=catalog, config=cfg,
                                 enabled_names=names)
        counts.append(current.get('escalation_count'))
        prints.append(module_prints(current, source, target, catalog=catalog, config=cfg,
                                    enabled_names=names, project=None, client=None))
    return current, counts, prints


def test_four_returns_count_and_threshold_at_third(catalog, tmp_path):
    _, counts, prints = run_edges(catalog, config(tmp_path))
    assert counts == [1, 2, 3, 4]
    assert [THRESHOLD in lines for lines in prints] == [False, False, True, True]


def test_reset_on_entering_exec_in_progress(catalog, tmp_path):
    cfg = config(tmp_path)
    counted, _, _ = run_edges(catalog, cfg)
    assert counted['escalation_count'] == 4
    reset = apply_counters(counted, '執行/退回', '執行/進行中', catalog=catalog, config=cfg,
                           enabled_names=['escalation'])
    assert reset['escalation_count'] == 0
    assert THRESHOLD not in module_prints(reset, '執行/退回', '執行/進行中', catalog=catalog,
                                          config=cfg, enabled_names=['escalation'],
                                          project=None, client=None)


def test_reset_on_escalated_to_in_progress(catalog, tmp_path):
    cfg = config(tmp_path)
    counted, _, _ = run_edges(catalog, cfg)
    reset = apply_counters(counted, '審核/升級', '審核/進行中', catalog=catalog, config=cfg,
                           enabled_names=['escalation'])
    assert reset['escalation_count'] == 0


def test_reset_on_leaving_blocked_back_into_exec(catalog, tmp_path):
    """core/verbs.md §1 move：不論來源，進入執行／進行中即 iteration +1 ⇒ 同一轉移歸零。"""
    cfg = config(tmp_path)
    counted, _, _ = run_edges(catalog, cfg)
    reset = apply_counters(counted, '執行/阻塞←進行中', '執行/進行中', catalog=catalog, config=cfg,
                           enabled_names=['escalation'])
    assert reset['escalation_count'] == 0


@pytest.mark.parametrize('edge', [('需求/退回', '需求/進行中'), ('執行/進行中', '執行/待確認'),
                                  ('審核/待確認', '結案/待確認'), ('執行/進行中', '執行/阻塞←進行中'),
                                  ('規劃/退回', '規劃/進行中')])
def test_other_edges_leave_counter_untouched(catalog, tmp_path, edge):
    cfg = config(tmp_path)
    counted, _, _ = run_edges(catalog, cfg)
    moved = apply_counters(counted, *edge, catalog=catalog, config=cfg, enabled_names=['escalation'])
    assert moved['escalation_count'] == 4


def test_params_escalate_after_two_prints_on_second(catalog, tmp_path):
    _, counts, prints = run_edges(catalog, config(tmp_path, {'escalate_after': 2}))
    assert counts == [1, 2, 3, 4]
    assert [THRESHOLD in lines for lines in prints] == [False, True, True, True]


def test_params_missing_falls_back_to_module_seed(catalog, tmp_path):
    seed, = {block.data['params']['escalate_after'] for block in catalog.by_label('yaml wf-module')
             if block.data['name'] == 'escalation'}
    assert seed == 3
    _, _, prints = run_edges(catalog, config(tmp_path, params=None))
    assert [THRESHOLD in lines for lines in prints] == [False, False, True, True]


@pytest.mark.parametrize('bad', ['3', 3.0, True, None, [3]])
def test_params_non_integer_prints_and_uses_seed(catalog, tmp_path, bad):
    _, _, prints = run_edges(catalog, config(tmp_path, {'escalate_after': bad}))
    assert all('escalate_after 不合法，改用種子 3' in lines for lines in prints)
    assert [THRESHOLD in lines for lines in prints] == [False, False, True, True]


def test_valid_integer_param_prints_no_complaint(catalog, tmp_path):
    """負控：合法值時不得出現不合法印句，證明上一測的命中不是常駐字串。"""
    _, _, prints = run_edges(catalog, config(tmp_path, {'escalate_after': 3}))
    assert not any('不合法' in line for lines in prints for line in lines)


def test_disabled_escalation_neither_counts_nor_prints(catalog, tmp_path):
    cfg = config(tmp_path, listed=False)
    current, counts, prints = run_edges(catalog, cfg, names=())
    assert counts == [None] * 4
    assert 'escalation_count' not in current
    assert not any(THRESHOLD in lines for lines in prints)
