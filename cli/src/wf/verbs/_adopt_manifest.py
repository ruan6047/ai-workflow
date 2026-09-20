"""消費 core/adopt.md §2（manifest 頂層鍵、項鍵集合、所有權二值、單一 `path` 文法、legacy 判定、
框架資產表、未完成項鍵集合、結構宣告八列缺陷代號、`framework-version` 彙整規則）。本檔是 manifest 的
讀寫與結構判定，外加框架資產的宣告。⛔ 不 import `wf.gh.*`、⛔ 不開子程序：對 GitHub 與 Project 的
mutation 原語呼叫序列長度恆為 0。

**本層⛔ 不解析採用者既有檔案的內部結構**：`install` 只有「整檔落地」與「零寫入＋未完成項」兩個分支，
CLI ⛔ 不推導插入或移除區間（`core/adopt.md` 開頭與 §2）。⛔ 不得推出「可以在別處重建片段定位」——
該機制連同它的行掃描、縮排判定與 `<承載檔>#<片段名>` 文法一併退休。
"""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

MANIFEST_PATH, MANIFEST_SCHEMA = '.wf/adopt/manifest.json', 'wf-adopt-manifest'
# `core/adopt.md` §2 的**控制檔集合**具名宣告在實作層的對應常數：基數恰 1、⛔ 無來源檔、⛔ 非整檔複製
# 產生，故它⛔ 不是 `ASSETS` 的一列。刻意與 `ASSETS` 分開宣告：控制檔的生成、更新與移除權限來自該具名
# 宣告本身，⛔ 非來自任何登記項（方案 A：控制檔⛔ 不自登記）。⛔ 不得推出「可以再加第二個控制檔」。
CONTROL_SET = (MANIFEST_PATH,)
TOP_KEYS = ('schema', 'source_commit', 'assets')
ASSET_KEYS = ('path', 'ownership', 'digest', 'pin')
OWNERSHIPS = ('framework-managed', 'consumer-owned')
# core/adopt.md §2「manifest 結構宣告」表的缺陷代號，逐字、同序。⛔ 不在別處重打：
# `cli/tests/test_adopt_manifest.py` 以解析該表得到的集合與本常數比對，任一側漏一個就轉紅。
DEFECTS = ('top-keys', 'schema-value', 'source-commit', 'assets-type', 'entry-type',
           'entry-keys', 'entry-value', 'path-unique', 'control-path')
NO_MANIFEST = 'manifest 不存在或不可解析'
VERSION_HOME = 'cli/pyproject.toml'
# 採用資料的機器可讀居所（`core/adopt.md` §3 `bootstrap`）：CLI ⛔ 不以「文件內第 N 個 json 圍欄」
# 或散文行首字串定位資料，故種子住自己的 JSON 資產、⛔ 不住 `ADOPTION.md` 的圍欄。
SEED_HOME, STAGES_HOME = '.github/adopt/modules.seed.json', 'core/enums.md'
STAGE_DIR, CONFIG_PATH = '.wf/stages', '.wf/modules.json'
# 未完成項的封閉鍵集合（`core/adopt.md` §2）；`install` 與 `bootstrap` 共用同一組鍵，值皆⛔ 非空。
PENDING_KEYS = ('source', 'target', 'content', 'section')
# 退場節的規範定位（`ADOPTION.md` §5 逐字三類）：legacy 項與 AI 整合內容一律指向這裡。
EXIT_SECTION = 'ADOPTION.md §5'


@dataclass(frozen=True)
class Asset:
    """`core/adopt.md` §2 框架資產表的一列，外加未完成項要用的兩個宣告值。
    表格恰四欄（`name`／`source`／`target`／`required`）；`content` 與 `section` ⛔ 不是表格欄，
    它們是同節另一條散文的宣告，⛔ 不得推出「資產表有六欄」。"""
    name: str
    source: str
    target: str
    required: bool
    content: tuple  # 必要內容識別（CI 資產＝job 名）
    section: str    # 規範定位：`ADOPTION.md` 的節次


ASSETS = (
    Asset('consumer-ci-jobs', '.github/adopt/consumer-jobs.yml', '.github/workflows/wf.yml',
          True, ('secret-scan', 'commit-trailer'), 'ADOPTION.md §1'),
    Asset('trailer-check', '.github/scripts/trailer_check.py', '.github/scripts/trailer_check.py',
          True, ('trailer_check.py',), 'ADOPTION.md §1'),
)
ASSET_NAMES = tuple(asset.name for asset in ASSETS)
# 應安裝集合＝資產表的目標路徑集合（`core/adopt.md` §3 `smoke` 的 `managed-assets` 母體）。整檔，⛔ 無片段項。
INSTALL_SET = tuple(asset.target for asset in ASSETS)


def digest_of(data):
    """內容摘要的唯一口徑：`sha256:<hex>`，對 bytes 算。⛔ 不比對 mtime、⛔ 不比對大小。"""
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def is_legacy(path):
    """§2 的 legacy 判定：`path` 含 `#` 的**既有**登記項是已退休片段機制的殘留。CLI 只列出、
    ⛔ 不處置、⛔ 不重寫；它⛔ 不使整份 manifest 無效（結構宣告⛔ 不以 `#` 判不合法）。"""
    return isinstance(path, str) and '#' in path


def pending(source, target, content, section):
    """未完成項：鍵集合封閉、四個值皆⛔ 非空。⛔ 不得推出「可以補第五個鍵」。"""
    return {'source': source, 'target': target,
            'content': content if isinstance(content, str) else '、'.join(content),
            'section': section}


def _entry_defect(entry):
    if not isinstance(entry, dict):
        return DEFECTS[4]
    if set(entry) != set(ASSET_KEYS):
        return DEFECTS[5]
    if not isinstance(entry['path'], str) or not entry['path'] \
            or entry['ownership'] not in OWNERSHIPS \
            or not isinstance(entry['digest'], str) or not isinstance(entry['pin'], str):
        return DEFECTS[6]
    return None


def defect_of(value):
    """回 §2 表的缺陷代號，⛔ 無缺陷回 None。可解析的 JSON ⛔ 不等於有效 manifest。"""
    if not isinstance(value, dict) or set(value) != set(TOP_KEYS):
        return DEFECTS[0]
    if value['schema'] != MANIFEST_SCHEMA:
        return DEFECTS[1]
    source = value['source_commit']
    if source is not None and not (isinstance(source, str) and len(source) == 40):
        return DEFECTS[2]
    if not isinstance(value['assets'], list):
        return DEFECTS[3]
    for entry in value['assets']:
        found = _entry_defect(entry)
        if found is not None:
            return found
    paths = [entry['path'] for entry in value['assets']]
    if len(set(paths)) != len(paths):
        return DEFECTS[7]
    # 方案 A：控制檔⛔ 不在 `assets` 內登記自己。命中即整份 manifest 不可用——否則「自登記」會成為
    # 一條把控制檔路徑當一般登記項刪除或改寫的旁路。⛔ 不得推出「只要忽略那一項就好」。
    return DEFECTS[8] if set(paths) & set(CONTROL_SET) else None


def read_manifest(root):
    """回 (manifest|None, 理由|None)。不存在、JSON 不合法、或⛔ 不合 §2 結構宣告一律回 None ＋
    **固定**理由（⛔ 不隨缺陷種類而異、⛔ 不 raise）。"""
    try:
        value = json.loads((Path(root) / MANIFEST_PATH).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None, NO_MANIFEST
    return (None, NO_MANIFEST) if defect_of(value) is not None else (value, None)


def control_unusable(root):
    """§2 的**前置條件**：控制檔路徑上有一個⛔ 不合結構宣告的既有物（⛔ 非 JSON、目錄、符號連結皆是）。
    符號連結單獨判是刻意的：它即使指向一份合法 manifest 也算既有物——跟隨它寫回去會寫到樹外。
    控制檔**⛔ 不存在**⛔ 不是本情形（那是乾淨起點，走正常分支）。"""
    path = Path(root) / MANIFEST_PATH
    if path.is_symlink():
        return True
    return path.exists() and read_manifest(root)[0] is None


def asset_entry(path, ownership, digest, pin):
    """四鍵、順序固定（`ASSET_KEYS`）。`pin` 缺席時寫空字串：⛔ 不寫 `None`，否則整份 manifest
    會被 §2 的 `entry-value` 判為無效而連坐其餘診斷列。"""
    return {'path': path, 'ownership': ownership, 'digest': digest,
            'pin': pin if isinstance(pin, str) else ''}


def write_manifest(root, assets, source_commit):
    """assets＝已排序的四鍵項。**控制檔⛔ 不在此登記自己**（方案 A，§2 控制檔具名宣告）：本函式
    只落檔，⛔ 不補任何自身項——補了會命中結構宣告的 `control-path` 列而使整份 manifest 不可用。"""
    manifest = {'schema': MANIFEST_SCHEMA, 'source_commit': source_commit, 'assets': list(assets)}
    (path := Path(root) / MANIFEST_PATH).parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def entries_of(manifest, ownership):
    return [entry for entry in (manifest or {}).get('assets') or []
            if isinstance(entry, dict) and entry.get('ownership') == ownership]


def managed_entries(manifest):
    """`framework-managed` 且⛔ 非 legacy 的項：§2 逐字「legacy ⛔ 不進 `framework-version` 的彙整
    母體與 `managed-assets` 的母體」。⛔ 不得推出「legacy 項可以被 CLI 刪除或改寫」。"""
    return [entry for entry in entries_of(manifest, OWNERSHIPS[0]) if not is_legacy(entry['path'])]


def legacy_entries(manifest):
    """manifest 內全部 legacy 項（⛔ 不分 ownership），依 `path` 排序；只供診斷列出。"""
    return sorted((entry for entry in (manifest or {}).get('assets') or []
                   if isinstance(entry, dict) and is_legacy(entry.get('path'))),
                  key=lambda entry: entry['path'])
