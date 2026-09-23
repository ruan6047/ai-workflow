"""#393 出貨的 `tdd` 選用文件模組：只在「執行」「審核」兩個階段有文件。

載入機制本身由 test_modules.py（#392）證明；本檔只證明**真實出貨的規則樹**接上那個機制：
有文件的階段注入、無文件的階段不多注入、停用時與沒有 `modules/` 的規則樹逐字相同。
⛔ 不驗模組散文內容。
"""

import shutil

import pytest

from wfx.core.layers import NO_MODULE_DOC
from wfx.core.render import split_output

from .test_modules import configure

TDD = 'tdd'


def test_shipped_tdd_module_has_exactly_the_execution_and_review_documents(rules_root):
    assert {p.name for p in (rules_root / 'modules' / TDD).iterdir()} == {'執行.md', '審核.md'}


@pytest.mark.parametrize('stage, role', [('執行', '執行者'), ('審核', '審核者')])
def test_enabled_tdd_injects_its_document_for_the_stage(run_cli, project_root, stage, role):
    configure(project_root, modules=[TDD])
    rc, out, _ = run_cli(role=role, stage=stage)
    assert rc == 0
    first, appendix = split_output(out)
    assert f'[來源: framework:modules/{TDD}/{stage}.md#' in appendix
    assert f'- modules/{TDD}/{stage}.md（' in first
    other = ({'執行', '審核'} - {stage}).pop()
    assert f'modules/{TDD}/{other}.md' not in out


def test_enabled_tdd_in_a_stage_without_a_document_adds_nothing_to_the_appendix(
        run_cli, project_root):
    configure(project_root)
    _, disabled, _ = run_cli(role='規劃者', stage='規劃')
    configure(project_root, modules=[TDD])
    rc, out, _ = run_cli(role='規劃者', stage='規劃')
    assert rc == 0
    first, appendix = split_output(out)
    assert f'- modules/{TDD}/：{NO_MODULE_DOC}' in first
    assert appendix == split_output(disabled)[1]


def test_disabled_output_is_identical_to_the_rules_tree_without_modules(
        run_cli, project_root, rules_root):
    configure(project_root)
    _, shipped, _ = run_cli()
    shutil.rmtree(rules_root / 'modules')
    rc, without, _ = run_cli()
    assert rc == 0
    assert shipped == without
