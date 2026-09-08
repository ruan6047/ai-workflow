"""消費 ADOPTION.md §2；project 定位形狀依 WF-STEP6-S05 續派附錄 §4。
只讀專案設定與正規化缺省值；不判模組是否應啟用，不連網。
"""
import json
from pathlib import Path


class ProjectConfigError(ValueError):
    """設定形狀不合法；呼叫端印出，非 D 類拒收。"""


def load_project_config(root) -> dict:
    path = Path(root) / '.wf/modules.json'
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raw = {}
    except (ValueError, OSError) as exc:
        raise ProjectConfigError(str(exc)) from exc
    if not isinstance(raw, dict):
        raise ProjectConfigError('頂層須為物件')
    cfg = {'modules': [], 'areas': [], 'merge_method': 'squash', 'project': None, **raw}
    if not isinstance(cfg['modules'], list):
        raise ProjectConfigError('modules 須為物件陣列')
    for module in cfg['modules']:
        if not isinstance(module, dict) or not isinstance(module.get('name'), str):
            raise ProjectConfigError('modules 每項須有字串 name')
        module.setdefault('params', {})
        if not isinstance(module['params'], dict):
            raise ProjectConfigError('modules[].params 須為物件')
    if not isinstance(cfg['areas'], list) or any(not isinstance(a, str) for a in cfg['areas']):
        raise ProjectConfigError('areas 須為字串陣列')
    if not isinstance(cfg['merge_method'], str):
        raise ProjectConfigError('merge_method 須為字串')
    if cfg['project'] is not None:
        project = cfg['project']
        if (not isinstance(project, dict) or not isinstance(project.get('owner'), str)
                or type(project.get('number')) is not int):
            raise ProjectConfigError('project 須有字串 owner 與整數 number')
    return cfg


def module_names(cfg) -> list[str]:
    return [module['name'] for module in cfg['modules']]


def module_params(cfg, name) -> dict:
    return next((module.get('params', {}) for module in cfg['modules'] if module['name'] == name), {})
