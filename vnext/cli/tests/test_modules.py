"""#392 最小選用模組契約：`.wf/config.json` 的 `modules` 啟用、框架規則樹 `modules/<名稱>/<階段>.md` 提供。

樣本模組是**本檔的 fixture**（與任何特定方法、專案無關），只建在 tmp 規則樹副本裡；
套件本身⛔ 不出貨任何真實模組。全部走注入式快照，零網路、零 mutation。
"""

import json
import re

import pytest

from wfx.core.context import ConfigError, load_config
from wfx.core.layers import KINDS, NO_MODULE_DOC
from wfx.core.render import split_output
from wfx.verbs.main import main

SAMPLE = 'sample-checklist'
SAMPLE_TEXT = '樣本模組：交付前逐項核對一份自訂清單。'
MARKER = re.compile(r'^\[來源: (?P<kind>[a-z]+):')


@pytest.fixture
def sample_module(rules_root):
    """中立樣本：只在「規劃」「執行」兩個階段有文件。"""
    directory = rules_root / 'modules' / SAMPLE
    directory.mkdir(parents=True)
    (directory / '執行.md').write_text(
        f'---\nname: {SAMPLE}\n---\n\n# 樣本\n\n## 1 · 核對\n\n{SAMPLE_TEXT}\n', encoding='utf-8')
    (directory / '規劃.md').write_text('# 樣本\n\n## 1 · 預留\n\n規劃時預留核對項。\n', encoding='utf-8')
    return directory


def configure(project_root, **extra):
    config = {'rules': None, 'remote': None, 'project': {'owner': 'o', 'number': 9}, **extra}
    (project_root / '.wf' / 'config.json').write_text(json.dumps(config), encoding='utf-8')


# ── WP1：設定形狀 ───────────────────────────────────────────────────────

def test_modules_absent_null_or_empty_all_mean_disabled(project_root):
    configure(project_root)
    assert load_config(project_root)['modules'] is None
    configure(project_root, modules=None)
    assert load_config(project_root)['modules'] is None
    configure(project_root, modules=[])
    assert load_config(project_root)['modules'] == []
    configure(project_root, modules=[SAMPLE, '另一個'])
    assert load_config(project_root)['modules'] == [SAMPLE, '另一個']


@pytest.mark.parametrize('bad', [
    SAMPLE, {'name': SAMPLE}, [''], [1], [None], ['../core'], ['a/b'], ['a\\b'],
    ['.hidden'], [' 前後空白 '], [SAMPLE, SAMPLE],
])
def test_malformed_modules_is_a_config_error_for_every_verb(project_root, bad, capsys):
    configure(project_root, modules=bad)
    with pytest.raises(ConfigError, match='modules'):
        load_config(project_root)
    for argv in (['brief', '--task', '1', '--role', '執行者', '--stage', '執行'],
                 ['facts', '--task', '1'],
                 ['write', '--task', '1', '--field', '狀態=進行中', '--dry-run']):
        assert main(['--project-root', str(project_root), *argv], env={}) == 1
        captured = capsys.readouterr()
        assert captured.out == ''
        assert captured.err.startswith('ConfigError: modules 須為 null')


# ── WP2：階段載入 ───────────────────────────────────────────────────────

def test_enabled_module_injects_its_stage_document_as_framework(run_cli, project_root, sample_module):
    configure(project_root, modules=[SAMPLE])
    for role in ('執行者', '審核者'):     # 生效只看階段，不看角色
        rc, out, _ = run_cli(role=role, stage='執行')
        assert rc == 0
        first, appendix = split_output(out)
        assert f'[來源: framework:modules/{SAMPLE}/執行.md#1 · 核對]\n{SAMPLE_TEXT}' in appendix
        assert f'- modules/{SAMPLE}/執行.md（2 節）：前言／1 · 核對' in first
        assert '規劃時預留核對項' not in out      # 只注入當前階段那一份
        assert {MARKER.match(l).group('kind') for l in out.splitlines()
                if MARKER.match(l)} == set(KINDS)   # 仍恰四種 kind，⛔ 無第五層


def test_enabled_module_without_a_document_for_this_stage_injects_nothing(
        run_cli, project_root, sample_module):
    configure(project_root)
    _, disabled, _ = run_cli(stage='需求')
    configure(project_root, modules=[SAMPLE])
    rc, out, _ = run_cli(stage='需求')
    assert rc == 0
    assert 'framework:modules/' not in out
    first, appendix = split_output(out)
    assert f'- modules/{SAMPLE}/：{NO_MODULE_DOC}' in first
    assert appendix == split_output(disabled)[1]   # 附錄逐字等於停用時


def test_disabled_output_is_identical_to_a_rules_tree_without_modules(
        run_cli, project_root, rules_root):
    """停用（缺鍵／null／空清單）＝逐字等於規則樹根本沒有模組時的輸出。"""
    configure(project_root)
    _, baseline, _ = run_cli()
    (rules_root / 'modules' / SAMPLE).mkdir(parents=True)
    (rules_root / 'modules' / SAMPLE / '執行.md').write_text(f'## 1\n{SAMPLE_TEXT}\n', encoding='utf-8')
    for disabled in ({}, {'modules': None}, {'modules': []}):
        configure(project_root, **disabled)
        rc, out, _ = run_cli()
        assert rc == 0
        assert out == baseline


def test_modules_are_injected_in_declaration_order(run_cli, project_root, rules_root):
    for name in ('b-second', 'a-first'):
        (rules_root / 'modules' / name).mkdir(parents=True)
        (rules_root / 'modules' / name / '執行.md').write_text(f'## 1\n{name} 內容\n', encoding='utf-8')
    configure(project_root, modules=['b-second', 'a-first'])
    rc, out, _ = run_cli()
    assert rc == 0
    assert out.index('b-second 內容') < out.index('a-first 內容')


# ── 無效設定的可辨結果 ──────────────────────────────────────────────────

@pytest.mark.parametrize('stage', ['需求', '執行'])
def test_unknown_module_name_fails_loud_in_every_stage(run_cli, project_root, sample_module, stage):
    configure(project_root, modules=[SAMPLE, 'not-shipped'])
    rc, out, err = run_cli(stage=stage)
    assert (rc, out) == (1, '')
    assert err.startswith('LayerMissing: 缺少必要層 framework：modules/not-shipped（已在 .wf/config.json 啟用')


def test_module_directory_without_documents_fails_loud(run_cli, project_root, rules_root):
    (rules_root / 'modules' / 'empty').mkdir(parents=True)
    configure(project_root, modules=['empty'])
    rc, out, err = run_cli()
    assert (rc, out) == (1, '')
    assert 'LayerMissing: 缺少必要層 framework：modules/empty（目錄下沒有模組文件）' in err


def test_module_document_named_after_a_non_stage_fails_loud(run_cli, project_root, sample_module):
    (sample_module / '部署.md').write_text('## 1\n部署不是階段\n', encoding='utf-8')
    configure(project_root, modules=[SAMPLE])
    rc, out, err = run_cli()
    assert (rc, out) == (1, '')
    assert f'MalformedInput: framework:modules/{SAMPLE} 的檔名不是階段值：部署' in err



def test_adoption_listing_checks_only_the_shape_of_modules(tmp_path, rules_root, capsys):
    """`facts --adopt` 只驗形狀：合法清單＝已完成（名稱在不在規則樹由 `brief` 判），形狀錯＝格式錯誤。"""
    from wfx.core import adopt
    from .test_adopt import listing, runner, states
    (tmp_path / '.wf').mkdir()
    for modules, expected in ((['not-in-tree'], adopt.DONE), ('not-a-list', adopt.MALFORMED)):
        (tmp_path / '.wf/config.json').write_text(json.dumps({'modules': modules}), encoding='utf-8')
        rc, out = listing(tmp_path, rules_root, capsys, runner=runner())
        assert rc == 0
        assert states(out)['.wf/config.json'] == expected
