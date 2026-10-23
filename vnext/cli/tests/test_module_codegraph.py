"""真實出貨文件接上既有 loader；不鏡像散文，也不啟動 CodeGraph。"""
import shutil
from types import SimpleNamespace

import pytest

from wfx.core.layers import NO_MODULE_DOC
from wfx.core.render import split_output

from .test_modules import configure


def test_shipped_documents_match_the_three_content_stages(rules_root):
    assert {p.name for p in (rules_root / 'modules/codegraph').iterdir()} == {
        '規劃.md', '執行.md', '審核.md'}


@pytest.mark.parametrize('stage,role', [('規劃', '規劃者'), ('執行', '執行者'),
                                       ('審核', '審核者'), ('規劃', 'PM')])
def test_enabled_document_injection_does_not_start_helper(
        run_cli, project_root, monkeypatch, stage, role):
    from wfx import codegraph

    def forbidden(*args, **kwargs):
        raise AssertionError('brief 不得執行外部工具')

    monkeypatch.setattr(codegraph, 'subprocess', SimpleNamespace(run=forbidden))
    configure(project_root, modules=['codegraph'])
    rc, out, _ = run_cli(role=role, stage=stage)
    assert rc == 0
    first, appendix = split_output(out)
    assert f'[來源: framework:modules/codegraph/{stage}.md#' in appendix
    assert f'- modules/codegraph/{stage}.md（' in first
    for other in {'規劃', '執行', '審核'} - {stage}:
        assert f'modules/codegraph/{other}.md' not in out


def test_uncovered_stage_keeps_appendix(run_cli, project_root):
    configure(project_root)
    _, disabled, _ = run_cli(role='規劃者', stage='需求')
    configure(project_root, modules=['codegraph'])
    rc, out, _ = run_cli(role='規劃者', stage='需求')
    assert rc == 0
    first, appendix = split_output(out)
    assert f'- modules/codegraph/：{NO_MODULE_DOC}' in first
    assert appendix == split_output(disabled)[1]


def test_disabled_module_changes_no_output(run_cli, project_root, rules_root):
    configure(project_root)
    _, shipped, _ = run_cli()
    shutil.rmtree(rules_root / 'modules/codegraph')
    rc, without, _ = run_cli()
    assert rc == 0 and shipped == without
