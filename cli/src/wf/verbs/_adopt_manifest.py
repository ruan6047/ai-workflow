"""消費 core/adopt.md §2（manifest 頂層鍵、項鍵集合、所有權二值、`path` 兩類文法、片段資產判定、
結構宣告九列缺陷代號、`framework-version` 彙整規則）。本檔是 manifest 的讀寫與結構判定，外加**片段**
（承載檔內的一個 job）的純文字切分、插入與移除。⛔ 不 import `wf.gh.*`、⛔ 不開子程序：對 GitHub 與
Project 的 mutation 原語呼叫序列長度恆為 0。片段邊界以**縮排層級的行掃描**判定，⛔ 不依賴 PyYAML
（`cli/src/wf` 只准 stdlib 與 `wf`，`cli/tests/test_gh_scope.py`）；⛔ 不得推出「只能行掃描」。
"""
import hashlib
import json
import re
from pathlib import Path

MANIFEST_PATH, MANIFEST_SCHEMA = '.wf/adopt/manifest.json', 'wf-adopt-manifest'
TOP_KEYS = ('schema', 'source_commit', 'assets')
ASSET_KEYS = ('path', 'ownership', 'digest', 'pin')
OWNERSHIPS = ('framework-managed', 'consumer-owned')
# core/adopt.md §2「manifest 結構宣告」表的缺陷代號，逐字、同序。⛔ 不在別處重打：
# `cli/tests/test_adopt_manifest.py` 以解析該表得到的集合與本常數比對，任一側漏一個就轉紅。
DEFECTS = ('top-keys', 'schema-value', 'source-commit', 'assets-type', 'entry-type',
           'entry-keys', 'entry-value', 'path-unique', 'path-grammar')
NO_MANIFEST = 'manifest 不存在或不可解析'
JOBS_KEY, JOB_INDENT = 'jobs:', 2
# 合法 job 鍵行：縮排恰 `JOB_INDENT`、鍵名後恰一個半形冒號，其後只准空白與一段 `#` 行尾註解
# （`  secret-scan: # consumer job` 仍是一個 job 鍵）。⛔ 不得推出「⛔ 不符本形狀的行⛔ 不是 job」
# ——那種行由 `unsafe_job_lines` 收成「無法安全辨識」，呼叫端據以零寫入，⛔ 不猜片段邊界。
JOB_KEY = re.compile(r'^([A-Za-z0-9][A-Za-z0-9_.\-]*):[ \t]*(#.*)?$')
VERSION_HOME, SEED_HOME = 'cli/pyproject.toml', 'ADOPTION.md'
STAGE_DIR, CONFIG_PATH = '.wf/stages', '.wf/modules.json'
# `core/adopt.md` §2「consumer 面 job 片段表」的「承載檔」欄與「片段來源檔」欄各一個值：本檔是
# `_adopt` 層對這兩個值的**唯一**字面居所，且⛔ 不由 `.wf/modules.json` 或任何設定鍵宣告。
CARRIER = '.github/workflows/wf.yml'
FRAGMENT_SOURCE = '.github/adopt/consumer-jobs.yml'
FRAGMENTS = ('secret-scan', 'commit-trailer')
MANAGED_ASSETS = ('.github/scripts/trailer_check.py',)
# 應安裝集合的單一常數居所（`core/adopt.md` §3 `smoke` 的 `managed-assets` 母體）：整檔項＋片段項。
INSTALL_SET = (*MANAGED_ASSETS, *(f'{CARRIER}#{name}' for name in FRAGMENTS))


def digest_of(data):
    """內容摘要的唯一口徑：`sha256:<hex>`，對 bytes 算。⛔ 不比對 mtime、⛔ 不比對大小。"""
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def fragment_of(path):
    """§2 的 `path` 文法：回 (承載檔, 片段名) 或 None（整檔）。`#` 的出現次數決定歸類，故單一值
    ⛔ 不得同時屬於兩類；`#` 數 ≠ 0 且 ≠ 1、或任一段為空 ⇒ 兩類皆⛔ 不屬於（`path-grammar`）。"""
    if not isinstance(path, str) or '#' not in path:
        return None
    carrier, _, name = path.partition('#')
    return (carrier, name) if carrier and name and '#' not in name else None


def _entry_defect(entry):
    if not isinstance(entry, dict):
        return DEFECTS[4]
    if set(entry) != set(ASSET_KEYS):
        return DEFECTS[5]
    if not isinstance(entry['path'], str) or not entry['path'] \
            or entry['ownership'] not in OWNERSHIPS \
            or not isinstance(entry['digest'], str) or not isinstance(entry['pin'], str):
        return DEFECTS[6]
    return DEFECTS[8] if '#' in entry['path'] and fragment_of(entry['path']) is None else None


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
    return DEFECTS[7] if len(set(paths)) != len(paths) else None


def read_manifest(root):
    """回 (manifest|None, 理由|None)。不存在、JSON 不合法、或⛔ 不合 §2 結構宣告一律回 None ＋
    **固定**理由（⛔ 不隨缺陷種類而異、⛔ 不 raise）。"""
    try:
        value = json.loads((Path(root) / MANIFEST_PATH).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None, NO_MANIFEST
    return (None, NO_MANIFEST) if defect_of(value) is not None else (value, None)


def self_digest(manifest):
    """manifest 自身那項的摘要前像＝把自己那項的 `digest` 換成空字串後的 canonical JSON。刻意如此：摘要
    自指算不出定值，而 manifest 又必須被登記。⛔ 不得推出「這個摘要涵蓋檔案位元組」——它釘的是內部一致性。"""
    blanked = {**manifest, 'assets': [dict(e, digest='') if e.get('path') == MANIFEST_PATH else e
                                      for e in manifest.get('assets') or []]}
    return digest_of(json.dumps(blanked, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


def asset_entry(path, ownership, digest, pin):
    """四鍵、順序固定（`ASSET_KEYS`）。`pin` 缺席時寫空字串：⛔ 不寫 `None`，否則整份 manifest
    會被 §2 的 `entry-value` 判為無效而連坐其餘診斷列。"""
    return {'path': path, 'ownership': ownership, 'digest': digest,
            'pin': pin if isinstance(pin, str) else ''}


def write_manifest(root, assets, source_commit, pin):
    """assets＝已排序的四鍵項（⛔ 不含 manifest 自身）；本函式補上 manifest 自身那一項後落檔。"""
    entries = [*assets, asset_entry(MANIFEST_PATH, OWNERSHIPS[0], '', pin)]
    manifest = {'schema': MANIFEST_SCHEMA, 'source_commit': source_commit, 'assets': entries}
    entries[-1]['digest'] = self_digest(manifest)
    (path := Path(root) / MANIFEST_PATH).parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def entries_of(manifest, ownership):
    return [entry for entry in (manifest or {}).get('assets') or []
            if isinstance(entry, dict) and entry.get('ownership') == ownership]


# ── 片段（承載檔內的一個 job）的純文字層 ────────────────────────────────────────────
def split_lines(text):
    """只以 `\\n` 切行並保留行尾。⛔ 不用 `str.splitlines`（它另外把 `\\r`、`\\x0b`、`\\x0c`、`\\u2028` 當行尾，CRLF 承載檔會丟位元組）。"""
    parts = text.split('\n')
    return [part + '\n' for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def _indent(line):
    stripped = line.lstrip(' ')
    return None if not stripped.strip() else len(line) - len(stripped)


def jobs_index(lines):
    """頂層 `jobs:` 鍵行的索引；⛔ 無則 None。"""
    for index, line in enumerate(lines):
        if line.strip() == JOBS_KEY and _indent(line) == 0:
            return index
    return None


def job_key_of(line):
    """該行是合法 job 鍵行時回鍵名，否則 None（含縮排⛔ 不等於 `JOB_INDENT` 的行）。"""
    if _indent(line) != JOB_INDENT:
        return None
    found = JOB_KEY.match(line.strip())
    return found.group(1) if found else None


def _jobs_end(lines, start):
    for index in range(start + 1, len(lines)):
        if _indent(lines[index]) == 0:
            return index
    return len(lines)


def _jobs_body(text):
    """`jobs:` 標頭行之後、下一個頂層鍵之前的那些行；⛔ 無 `jobs:` 標頭時為空。"""
    lines = split_lines(text)
    start = jobs_index(lines)
    return [] if start is None else lines[start + 1:_jobs_end(lines, start)]


def job_names(text):
    """承載檔內 `jobs:` 之下的 job 名，依出現序。帶行尾註解的鍵行同樣算一個 job：
    漏判它會讓 `install` 在同一個 `jobs:` 區塊內追加同名鍵而改變 workflow 語意。"""
    body = _jobs_body(text)
    return tuple(name for name in map(job_key_of, body) if name is not None)


def unsafe_job_lines(text):
    """`jobs:` 之下每一個⛔ 非空白、⛔ 非整行註解的行都必須是合法 job 鍵行，或是已辨識 job 鍵行之後深於
    `JOB_INDENT` 的內容行；首行就⛔ 不是 job 鍵行時（例：整個 `jobs:` 區塊用四格縮排）整段都算無法安全辨識。
    ⛔ 非空即「片段邊界無法安全辨識」，呼叫端據以零寫入；⛔ 不得推出「這些行⛔ 不是 job」。"""
    body = [line for line in _jobs_body(text) if line.strip() and not line.strip().startswith('#')]
    if body and job_key_of(body[0]) is None:
        return tuple(body)
    return tuple(line for line in body if job_key_of(line) is None and (_indent(line) or 0) <= JOB_INDENT)


def job_span(lines, name):
    """§2 的「片段區間」：自該 job 的鍵行起、到下一個縮排 ≤ 該鍵行的非空行之前，去掉尾端空白行。"""
    start = jobs_index(lines)
    if start is None:
        return None
    end_of_jobs = _jobs_end(lines, start)
    head = next((i for i in range(start + 1, end_of_jobs) if job_key_of(lines[i]) == name), None)
    if head is None:
        return None
    tail = next((i for i in range(head + 1, end_of_jobs)
                 if (_indent(lines[i]) or 99) <= JOB_INDENT), end_of_jobs)
    while tail > head + 1 and not lines[tail - 1].strip():
        tail -= 1
    return head, tail


def job_text(text, name):
    """該 job 的逐字文字（§2 的 `digest` 前像）；⛔ 無該 job 回 None。⛔ 不補檔尾換行：補過的字串既
    ⛔ 不是落地的位元組，也會讓 `digest` 與實際片段分離而掩蓋逐字差異。"""
    span = job_span(lines := split_lines(text), name)
    return None if span is None else ''.join(lines[span[0]:span[1]])


def skeleton_of(text):
    """片段來源檔的頂層骨架＝`jobs:` 鍵行（含）之前的全部位元組。新建承載檔時 CLI 逐字取用它，
    ⛔ 不在 CLI 內另建第二個居所（`core/adopt.md` §2 末條）。"""
    lines = split_lines(text)
    start = jobs_index(lines)
    return None if start is None else ''.join(lines[:start + 1])


def upsert_job(text, name, block):
    """把 `block`（逐字片段文字）寫進 `jobs:` 區塊：同名 job 已在就原位取代，否則插在區塊末端；末端前一行
    ⛔ 無換行時改插在 `jobs:` 標頭之後。刻意⛔ 不補接行用的換行——§2 逐字「為了把新行接上去而補的那個換行
    ⛔ 不屬於任何片段區間」，補它就改到片段區間之外的位元組。`jobs:` 標頭缺席、或兩個插點的前一行都⛔ 無
    換行時回 `None`，呼叫端據以零寫入；⛔ 不得推出「⛔ 無 `jobs:` 就⛔ 不能採用」（新建時由骨架帶入）。"""
    lines = split_lines(text)
    if (start := jobs_index(lines)) is None:
        return None
    if (span := job_span(lines, name)) is None:
        at = end if lines[(end := _jobs_end(lines, start)) - 1].endswith('\n') else start + 1
        if not lines[at - 1].endswith('\n'):
            return None
        span = (at, at)
    lines[span[0]:span[1]] = split_lines(block)
    return ''.join(lines)


def remove_jobs(text, names):
    """自承載檔移除指定的片段區間。`jobs:` 標頭行⛔ 不移除：它屬頂層骨架、可能是 consumer 原有的
    （§2／§5；install 也⛔ 不新增它，兩側對稱）。⛔ 不得推出「可以移除 consumer 自有的 job」。純刪行
    ⛔ 不需要接行用的換行（只有 `split_lines` 的最後一段可能⛔ 無換行，而它⛔ 不會是被刪區間的前一行）。"""
    lines = split_lines(text)
    for name in names:
        span = job_span(lines, name)
        if span is not None:
            del lines[span[0]:span[1]]
    return ''.join(lines)
