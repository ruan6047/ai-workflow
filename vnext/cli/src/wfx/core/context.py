"""核心上下文：專案層設定與不透明任務識別。

`wfx.core` ⛔ 不得 import `wfx.gh`、⛔ 不得 import subprocess（vnext/rules/core/boundaries.md「CLI 邊界」；
機械錨＝tests/test_wfx_scope.py）。`task_id` 對核心是不透明字串，格式的理解只住 `wfx.gh`。
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path


class ConfigError(ValueError):
    """`.wf/config.json` 形狀不合法；呼叫端印出。"""


@dataclass(frozen=True)
class Provenance:
    """一項事實的來源標記：kind＋逐字細節。⛔ 不作內容判讀。"""
    kind: str
    detail: str

    def __str__(self):
        return f'{self.kind}:{self.detail}'


@dataclass(frozen=True)
class Context:
    """`rules` 由 W1.6 brief 補上（本工作包⛔ 不預建規則載入）。"""
    project_root: Path
    task_id: str
    config: dict = field(default_factory=dict)


def load_config(project_root) -> dict:
    """只驗形狀、⛔ 不判內容、⛔ 不連網。缺檔＝空設定（各鍵為 None）。

    `rules`＝null 或 {"path": 非空字串}；`remote`＝null 或 remote 名稱（⛔ 不是 URL）；
    `project`＝null 或 {"owner": 字串, "number": 整數}。⛔ 無 modules 鍵（§13 模組四禁）。
    """
    path = Path(project_root) / '.wf/config.json'
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raw = {}
    except (ValueError, OSError) as exc:
        raise ConfigError(f'{path}：{exc}') from exc
    if not isinstance(raw, dict):
        raise ConfigError(f'{path}：頂層須為物件')
    unknown = set(raw) - {'rules', 'remote', 'project'}
    if unknown:
        raise ConfigError(f'{path}：未知鍵 {sorted(unknown)}（只認 rules／remote／project）')
    cfg = {'rules': None, 'remote': None, 'project': None, **raw}
    rules = cfg['rules']
    if rules is not None and (not isinstance(rules, dict) or set(rules) != {'path'}
                              or not isinstance(rules['path'], str) or not rules['path']):
        raise ConfigError('rules 須為 null 或 {"path": 非空字串}')
    remote = cfg['remote']
    if remote is not None and (not isinstance(remote, str) or not remote or ':' in remote):
        raise ConfigError('remote 須為 null 或 remote 名稱（非 URL）')
    project = cfg['project']
    if project is not None and (not isinstance(project, dict) or set(project) != {'owner', 'number'}
                                or not isinstance(project['owner'], str) or not project['owner']
                                or type(project['number']) is not int):
        raise ConfigError('project 須為 null 或 {"owner": 非空字串, "number": 整數}')
    return cfg
