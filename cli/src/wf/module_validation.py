"""`ModuleValidation`：模組可用性結果的唯一定義與輸出處所（core/modules.md §1／§4／§5）。

其他動詞只消費本檔的結果、⛔ 不重定義。三項檢查（§1 宣告、§4 `.wf/modules.json` 的 `modules[]`、
§5 `maturity=ready` 的宣告↔hook 雙向核對）在同一次執行中全部跑完並收齊錯誤，⛔ 不在第一條就停。
任一項不過＝呼叫端 rc≠0、stdout 列出完整修正資訊、且對 GitHub 與 Project 零寫入呼叫。
本檔是純計算：⛔ 不讀遠端、⛔ 不寫檔；registry 以延遲 import 取得，`ImportError` 是明確失敗
（刻意用 importlib 而非頂層 import：頂層會與 verbs 層構成環，且 ImportError 會在 import 時就炸掉
整個 CLI，⛔ 不得推出「registry 缺席可以續跑」）。
"""
from dataclasses import dataclass
import importlib

from wf.compose.enable import KINDS, READY

DECLARATION_KEYS = ("name", "enable_when", "enable_if", "fact_source", "scope",
                    "maturity", "adds", "project_inputs", "params")
ADDS_KEYS = ("fields", "stages", "enums", "transitions", "flags", "notes",
             "counters", "move_prints", "handoff_sections")
REGISTRY = "wf.verbs.move_modules"
HOOKS = (("counters", "COUNTERS"), ("move_prints", "MOVE_PRINTS"))
SCALARS = (bool, int, float, str)  # params 種子可用的 JSON 純量；容器與 null ⛔ 不是種子


class ModuleValidationError(ValueError):
    """本邊界的結果為不可用；`lines` 是逐條完整修正資訊，呼叫端逐行印到 stdout。"""

    def __init__(self, lines):
        self.lines = list(lines)
        super().__init__("；".join(self.lines))


def _type_name(value):
    """把 JSON 值映成人可讀的型別名；bool 先於 int（bool 是 int 的子類）。"""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    return type(value).__name__


def _domains(catalog):
    """`scope`／`maturity` 的值域只從 core/enums.md 取（唯一居所），⛔ 不在本檔重打字面。"""
    enums, = catalog.by_label("json wf-enums")
    return {"scope": enums.data["module_scope"]["enum"],
            "maturity": enums.data["module_maturity"]["enum"]}


def _declaration_errors(module, domains, where):
    out = []
    keys = set(module)
    for key in sorted(keys - set(DECLARATION_KEYS)):
        out.append(f"{where}: 未知頂層鍵 {key}；頂層鍵集合恰為 {list(DECLARATION_KEYS)}")
    for key in DECLARATION_KEYS:
        if key not in keys:
            out.append(f"{where}: 缺必填鍵 {key}；頂層鍵集合恰為 {list(DECLARATION_KEYS)}")
    for key, values in domains.items():
        if key in keys and module[key] not in values:
            out.append(f"{where}: {key} 值 {module[key]!r} 不在值域；期望 {values}（core/enums.md）")
    adds = module.get("adds")
    if not isinstance(adds, dict):
        out.append(f"{where}: adds 型別 {_type_name(adds)}；期望 object")
    else:
        for key in sorted(set(adds) - set(ADDS_KEYS)):
            out.append(f"{where}: adds 未知子鍵 {key}；子鍵集合封閉為 {list(ADDS_KEYS)}")
        for key, _ in HOOKS:  # §5 雙向核對只讀這兩個子鍵，型別不對就在這裡具名收，⛔ 不靜默略過
            if key in adds and not isinstance(adds[key], list):
                out.append(f"{where}: adds.{key} 型別 {_type_name(adds[key])}；期望 array（§5 雙向核對的 id 列）")
    condition = module.get("enable_if")
    if not isinstance(condition, dict):
        out.append(f"{where}: enable_if 型別 {_type_name(condition)}；期望 object")
    elif condition.get("kind") not in KINDS:
        out.append(f"{where}: enable_if.kind {condition.get('kind')!r} 不在已實作 kind 封閉集；"
                   f"期望 {sorted(KINDS)}")
    params = module.get("params")
    if not isinstance(params, dict):
        out.append(f"{where}: params 型別 {_type_name(params)}；期望 object")
    else:
        for key in sorted(params):
            if not isinstance(params[key], SCALARS):
                out.append(f"{where}: params.{key} 種子型別 {_type_name(params[key])}；"
                           f"期望 string／integer／number／boolean 之一")
    return out


def _config_errors(entries, declarations):
    """§4 四類：未知模組名、重複模組名、未知 `params` 鍵、`params` 型別不符宣告種子。"""
    out, seen = [], set()
    for index, entry in enumerate(entries):
        name = entry.get("name")
        where = f".wf/modules.json modules[{index}] {name!r}"
        if name not in declarations:
            out.append(f"{where}: 未知模組名；期望 {sorted(declarations)} 之一")
            continue
        if name in seen:
            # 重複判定與參數診斷分開累加：記下重複後⛔ 不 continue，否則該筆的未知 params 鍵與
            # 錯型值會被靜默漏掉，違反「兩側錯誤同一次執行全部收齊」。
            out.append(f"{where}: 重複模組名；modules[].name 須唯一")
        seen.add(name)
        seeds = declarations[name].get("params")
        seeds = seeds if isinstance(seeds, dict) else {}
        for key, value in (entry.get("params") or {}).items():
            if key not in seeds:
                out.append(f"{where}: 未知 params 鍵 {key}；期望 {sorted(seeds)} 之一")
            elif _type_name(value) != _type_name(seeds[key]):
                out.append(f"{where}: params.{key} 型別 {_type_name(value)} 不符宣告種子；"
                           f"期望 {_type_name(seeds[key])}")
    return out


def _hook_ids(module, key):
    """`adds.<key>` 的 id 列；`adds` 非 object 或該子鍵非 array ⇒ 空列。

    刻意只取形狀可用的部分：這些結構錯型已由 `_declaration_errors` 具名收進同一份 `lines`，
    在這裡再拋 `AttributeError`／`TypeError` 只會讓整批已收集的診斷連同兩側錯誤一起遺失。
    ⛔ 不得推出「錯型的 adds 通過驗證」——該次 `ModuleValidation.ok` 仍為假。
    """
    adds = module.get("adds")
    ids = adds.get(key) if isinstance(adds, dict) else None
    return ids if isinstance(ids, list) else []


def _hook_errors(declarations):
    """§5 雙向核對；只對 `maturity=ready` 的模組。非 ready 的缺實作⛔ 不構成失敗。"""
    try:
        registry = importlib.import_module(REGISTRY)
    except ImportError as exc:
        return [f"{REGISTRY}: 載入 production registry 失敗（ImportError: {exc}）；"
                f"期望可 import 且提供 {[attr for _, attr in HOOKS]}"]
    out = []
    for key, attribute in HOOKS:
        implemented = set(getattr(registry, attribute, {}))
        declared_ready, declared_any = set(), set()
        for module in declarations.values():
            ids = _hook_ids(module, key)
            declared_any.update(ids)
            if module.get("maturity") == READY:
                declared_ready.update(ids)
                for identifier in ids:
                    if identifier not in implemented:
                        out.append(f"{module['name']}: adds.{key} 的 {identifier} 在 {REGISTRY}."
                                   f"{attribute} 缺實作；期望 registry 有同名鍵")
        for identifier in sorted(implemented - declared_any):
            out.append(f"{REGISTRY}.{attribute}: {identifier} 有實作而無任何宣告；"
                       f"期望某模組 adds.{key} 列出它，或移除該實作")
    return out


@dataclass(frozen=True)
class ModuleValidation:
    """模組可用性結果。`ok` 為真才可進行任何遠端寫入；`lines` 逐條給人改。"""
    lines: tuple
    declarations: dict

    @property
    def ok(self) -> bool:
        return not self.lines

    def raise_for_status(self):
        if self.lines:
            raise ModuleValidationError(self.lines)


def validate_modules(catalog, config) -> ModuleValidation:
    """三項檢查一次收齊（core/modules.md §5）：宣告 → `.wf/modules.json` → 宣告↔hook 雙向核對。

    catalog＝compose/blocks.py 的 Catalog；config＝compose/project_config.py 的設定 dict。
    ⛔ 不在此決定啟用（那是 compose/enable.activate），只決定「宣告與設定可不可用」。
    """
    domains = _domains(catalog)
    lines, declarations = [], {}
    for block in catalog.by_label("yaml wf-module"):
        module = block.data
        where = f"{block.source.path}#{block.source.section}" if not isinstance(module.get("name"), str) \
            else module["name"]
        lines += _declaration_errors(module, domains, where)
        if isinstance(module.get("name"), str):
            declarations[module["name"]] = module
    lines += _config_errors(config.get("modules") or (), declarations)
    lines += _hook_errors(declarations)
    return ModuleValidation(tuple(lines), declarations)
