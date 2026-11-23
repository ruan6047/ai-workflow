"""#554：真正 CLI 的立即契約、同源按需取讀及角色分流。"""
import json
import re

import pytest

from wfx.core import layers, rules
from wfx.core.render import split_output
from .test_brief import section


def test_executor_full_preloads_only_immediate_framework_contracts(run_cli):
    rc, out, err = run_cli()
    assert (rc, err) == (0, "")
    first, appendix = split_output(out)
    framework = section(appendix, "適用規則")
    assert "core/boundaries.md#立即契約]" in framework
    assert "stages/執行.md#立即契約]" in framework
    assert "#1 · 分層注入（四層）]" not in framework
    assert "core/research.md#" not in framework
    assert "按需" in out
    assert "1 · 分層注入（四層）" not in first


def test_pm_same_stage_gets_handoff_not_executor_method(run_cli):
    _, out, _ = run_cli(role="PM")
    framework = section(out, "適用規則")
    assert "stages/執行.md#PM 當值]" in framework
    assert "stages/執行.md#立即契約]" not in framework


def test_modules_follow_reader_and_keep_trigger_entry(run_cli, project_root):
    config = project_root / ".wf/config.json"
    data = json.loads(config.read_text())
    data["modules"] = ["architecture", "codegraph", "tdd"]
    config.write_text(json.dumps(data))
    rc, executor, _ = run_cli()
    assert rc == 0
    assert "modules/codegraph/執行.md#立即契約]" in executor
    assert "modules/tdd/執行.md#3 · 先失敗、後通過]" not in executor
    rc, pm, _ = run_cli(role="PM")
    assert rc == 0
    assert "modules/codegraph/執行.md#" not in section(pm, "適用規則")


def test_changed_override_keeps_its_own_full_document(run_cli, rules_root):
    doc = rules_root / "roles/執行者.md"
    doc.write_text(doc.read_text() + "\n## 自訂安全契約\n自訂原文不可省略\n")
    _, out, _ = run_cli()
    assert "自訂原文不可省略" in out
    assert "未精簡" in out


@pytest.mark.parametrize('role,stage,expected', [
    ('PM', '需求', '立即契約'), ('需求方', '需求', '立即契約'),
    ('研究者', '規劃', None), ('規劃者', '規劃', '立即契約'),
    ('審核者', '審核', '立即契約'), ('執行者', '結案', '機械收尾入口'),
    ('執行者', '規劃', None),
])
def test_role_contract_and_actual_stage_responsibility(run_cli, role, stage, expected):
    rc, out, _ = run_cli(role=role, stage=stage)
    assert rc == 0
    body = section(out, '適用規則')
    assert f'roles/{role}.md#立即契約]' in body
    if expected:
        assert f'stages/{stage}.md#{expected}]' in body
    else:
        assert f'framework:stages/{stage}.md#' not in body


@pytest.mark.parametrize('change', ['same_heading', 'duplicate_heading', 'missing_entry'])
def test_override_never_guesses_a_changed_contract(run_cli, rules_root, change):
    doc = rules_root / 'core/boundaries.md'
    text = doc.read_text()
    if change == 'same_heading':
        text = text.replace('不得外送憑證', '額外安全前提：不得外送憑證')
    elif change == 'duplicate_heading':
        text += '\n## 立即契約\n額外安全前提\n'
    else:
        text = text.replace('## 立即契約', '## 額外安全前提')
    doc.write_text(text)
    _, out, _ = run_cli()
    assert '未精簡' in out
    assert '額外安全前提' in out
    assert 'core/boundaries.md#1 · 分層注入（四層）]' in out


def test_selected_contract_links_resolve_to_the_same_tree():
    root = rules.default_rules_root()
    chosen = layers.framework_rules(root, '執行者', '執行')
    assert [(s.path, s.section) for s in chosen] == [
        ('core/boundaries.md', '立即契約'), ('core/independence.md', '立即契約'),
        ('roles/執行者.md', '立即契約'), ('stages/執行.md', '立即契約')]
    for rel in ('roles/PM.md', 'roles/研究者.md', 'roles/規劃者.md', 'roles/審核者.md',
                'roles/需求方.md', 'modules/codegraph/執行.md'):
        chosen += [s for s in layers._doc_segments(rel, rules.read_doc(root, rel))
                   if s.section == '立即契約']
    for segment in chosen:
        for href in re.findall(r'\]\(([^)]+)\)', segment.body):
            target, _, anchor = href.partition('#')
            path = (root / segment.path).parent / target
            assert path.is_file(), (segment.path, href)
            if anchor:
                anchors = [re.sub(r'[^\w\- ]', '', h.lower()).replace(' ', '-')
                           for h in rules.headings(path.read_text())]
                assert anchor in anchors, (segment.path, href)


def test_coordination_reads_short_shared_authority_without_becoming_a_role(rules_root):
    chosen = layers.coordination_rules(rules_root)
    assert [(s.path, s.section) for s in chosen] == [
        ('core/boundaries.md', '立即契約'), ('core/independence.md', '立即契約'),
        ('PM-coordination.md', '立即契約')]
    assert '不因本入口取得任一卡' in chosen[-1].body
    assert all(not s.path.startswith(('roles/', 'stages/')) for s in chosen)
