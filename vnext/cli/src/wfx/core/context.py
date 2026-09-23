"""核心上下文：專案層設定與不透明任務識別。

`wfx.core` ⛔ 不得 import `wfx.gh`、⛔ 不得 import subprocess（wfx/rules/core/boundaries.md「CLI 邊界」；
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
class RulesSource:
    """第 1 層規則樹的來源：套件內的 package data，或 `--rules-root` 指定的本機 checkout。

    ⛔ 不印 root 路徑：那會讓「同一輸入兩次執行逐字相同」隨機器而破。來源屬於哪一種與套件版本，
    由 `facts` 第 ⑦ 節報（`core/rules.rules_provenance`）。
    """
    root: Path


@dataclass(frozen=True)
class Context:
    """C6 四欄：`project_root`／`rules`／不透明 `task_id`／`config`。

    `rules` 由 `brief` 提供；`facts` 不讀規則樹，該欄為 None。
    GitHub 專屬事實⛔ 不進 Context，由 `wfx.gh` 另產並在動詞層並列傳遞。
    """
    project_root: Path
    task_id: str
    config: dict = field(default_factory=dict)
    rules: RulesSource | None = None


CONFIG_REL = '.wf/config.json'

# `.wf/config.json` 的三態；`load_config_result()` 用它，⛔ 不改變 `load_config()` 的 fail-loud。
CONFIG_OK, CONFIG_MISSING, CONFIG_MALFORMED = 'ok', 'missing', 'malformed'


@dataclass(frozen=True)
class ConfigResult:
    """不 raise 的設定讀取結果：三態＋逐字原因。

    採用清單要把「壞掉的 config」分類成一項可讀的「格式錯誤」，⛔ 不能在載入時就炸掉整份清單；
    普通三動詞仍走 `load_config()` 的 fail-loud，rc 與訊息逐字不變。
    `reason` 內的絕對路徑一律換成相對的 `.wf/config.json`——清單輸出⛔ 不得含絕對路徑。
    """
    state: str
    config: dict | None
    reason: str


def load_config_result(project_root) -> ConfigResult:
    path = Path(project_root) / CONFIG_REL
    if not path.exists():
        return ConfigResult(CONFIG_MISSING, None, f'{CONFIG_REL} 不存在')
    try:
        return ConfigResult(CONFIG_OK, load_config(project_root), '')
    except ConfigError as exc:
        return ConfigResult(CONFIG_MALFORMED, None, str(exc).replace(str(path), CONFIG_REL))


def load_config(project_root) -> dict:
    """只驗形狀、⛔ 不判內容、⛔ 不連網。缺檔＝空設定（各鍵為 None）。

    `rules`＝null 或 {"path": 非空字串}；`remote`＝null 或 remote 名稱（⛔ 不是 URL）；
    `project`＝null 或 {"owner": 字串, "number": 整數}；`modules`＝null 或非空的選用模組名稱清單
    （boundaries.md §5；`[]`＝形狀錯，⛔ 不是停用）。這裡只驗名稱的形狀；名稱在不在框架規則樹，要讀規則樹的 `brief` 才判。
    """
    path = Path(project_root) / CONFIG_REL
    try:
        raw = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raw = {}
    except (ValueError, OSError) as exc:
        raise ConfigError(f'{path}：{exc}') from exc
    if not isinstance(raw, dict):
        raise ConfigError(f'{path}：頂層須為物件')
    unknown = set(raw) - {'rules', 'remote', 'project', 'modules'}
    if unknown:
        raise ConfigError(f'{path}：未知鍵 {sorted(unknown)}（只認 rules／remote／project／modules）')
    cfg = {'rules': None, 'remote': None, 'project': None, 'modules': None, **raw}
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
    modules = cfg['modules']
    if modules is not None and (not isinstance(modules, list) or not modules
                                or not all(_module_name_ok(name) for name in modules)
                                or len(set(modules)) != len(modules)):
        raise ConfigError('modules 須為 null 或非空、不重複的模組名稱清單（名稱不得含路徑分隔、不得以 . 開頭）')
    return cfg


def _module_name_ok(name) -> bool:
    """模組名稱＝框架規則樹 `modules/` 下的一個目錄名；⛔ 不得藉名稱逃出該目錄。"""
    return (isinstance(name, str) and bool(name) and name == name.strip()
            and not name.startswith('.') and '/' not in name and '\\' not in name)
