"""ADOPTION.md §2；WF-STEP6-S05 續派附錄 §4／§5e。"""
import json

import pytest

from wf.compose.project_config import ProjectConfigError, load_project_config, module_names, module_params
from .test_compose_schema import ROOT


def config(tmp_path, raw):
    path = tmp_path / '.wf/modules.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(raw, ensure_ascii=False))
    return load_project_config(tmp_path)


def test_missing_config_defaults(tmp_path):
    assert load_project_config(tmp_path) == {'modules': [], 'areas': [], 'merge_method': 'squash', 'project': None}


def test_adoption_seed_verbatim(tmp_path):
    text = (ROOT / 'ADOPTION.md').read_text()
    seed = text.split('```json\n')[1].split('```')[0]
    path = tmp_path / '.wf/modules.json'
    path.parent.mkdir()
    path.write_text(seed)
    cfg = load_project_config(tmp_path)
    assert cfg == json.loads(seed) | {'project': None}
    assert module_names(cfg) == ['snapshot']
    assert module_params(cfg, 'snapshot')['schedule'] == 'daily'
    assert module_params(cfg, 'missing') == {}


@pytest.mark.parametrize('bad,reason', [
    ([], '頂層'), ({'project': {'owner': 'a'}}, 'project'),
    ({'modules': [{}]}, 'name'), ({'modules': [{'name': 'snapshot', 'params': []}]}, 'params'),
    ({'modules': 'snapshot'}, 'modules'), ({'modules': ['snapshot']}, 'name'),
    ({'project': {'owner': 'a', 'number': True}}, 'project'), ({'project': None}, 'project'),
    ({'areas': [3]}, 'areas'), ({'areas': 'WF'}, 'areas'), ({'merge_method': 3}, 'merge_method'),
])
def test_bad_config_is_recognizable(tmp_path, bad, reason):
    with pytest.raises(ProjectConfigError, match=reason):
        config(tmp_path, bad)


def test_complete_config_and_module_defaults(tmp_path):
    raw = {'modules': [{'name': 'snapshot'}, {'name': 'db-contract', 'params': {'x': 1}}],
           'areas': ['WF'], 'merge_method': 'squash', 'project': {'owner': 'a', 'number': 7}}
    cfg = config(tmp_path, raw)
    assert cfg['modules'][0]['params'] == {}
    assert module_names(cfg) == ['snapshot', 'db-contract']
    assert module_params(cfg, 'db-contract') == {'x': 1}
    assert cfg['project'] == raw['project']


def test_malformed_json(tmp_path):
    path = tmp_path / '.wf/modules.json'
    path.parent.mkdir()
    path.write_text('{bad}')
    with pytest.raises(ProjectConfigError):
        load_project_config(tmp_path)
