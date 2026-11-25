"""四層注入。kind 恰四值：framework／user／project／task。

每段都是一個 Segment，輸出時逐段標示 `[來源: kind:path#節]`。
⛔ 不做 delta 合成、⛔ 不做模組層、⛔ 不解析散文語意。
已啟用的選用文件模組住在框架規則樹，因此仍是 `framework` 段，⛔ 不是第五種 kind。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata

from wfx.core.errors import LayerMissing, MalformedInput
from wfx.core import rules

KINDS = ("framework", "user", "project", "task")

# 七個核心概念的落地與值見 rules/core/github.md §2；此處只固定呈現順序。
CORE_CONCEPTS = ("狀態", "階段", "owner", "風險", "緊急性", "期限", "Resource")

# 使用者層的模型資料只有使用說明（rules/core/boundaries.md §2）；缺檔＝合法 unknown。
USER_MODEL_FILES = ("model-usage.md",)
USER_TOOL_FILE = "tool-usage.md"

UNKNOWN_MODEL_DATA = "使用者層模型資料：unknown"

# `brief --omit-user-layer`：使用者層未讀也未附時，首屏「模型資料狀態」的固定說明。
# ⛔ 不是 unknown（unknown 在 boundaries.md §2 另有語意）、⛔ 不印檔名行數。
USER_LAYER_OMITTED = "本輸出以 `--omit-user-layer` 產出：使用者層（`~/.wf/`）未讀，也未附原文。"


@dataclass(frozen=True)
class Segment:
    kind: str
    path: str
    section: str
    body: str

    def marker(self) -> str:
        return f"[來源: {self.kind}:{self.path}#{self.section}]"


# 會斷行或不可見的字元：控制字元（含 LF／CR）與 Unicode 行／段分隔符。
_LINE_BREAKING = ("Cc", "Zl", "Zp")


def one_line(text: str) -> str:
    """檔名裡會斷行或不可見的字元換成 escape 寫法（`\\n`、`\\x1b`、`\\u2028`…），其餘字元原樣保留。"""
    return "".join(
        ch.encode("unicode_escape").decode("ascii") if unicodedata.category(ch) in _LINE_BREAKING else ch
        for ch in text
    )


def _read_utf8(path: Path, display: str) -> str:
    """讀使用者層／專案層的一份檔案；不是 UTF-8＝`MalformedInput`（rc=1）。

    訊息單行、只帶顯示路徑（`~/.wf/<檔名>`、`.wf/<檔名>`），⛔ 不含絕對路徑；顯示路徑來自檔名，
    其中會斷行的字元一律 escape，訊息才保證是一行。
    ⛔ 不改用其他編碼、⛔ 不替換壞字元、⛔ 不捕捉 `UnicodeDecodeError` 以外的例外。
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise MalformedInput(f"{one_line(display)} 不是 UTF-8，編碼讀取失敗：{exc}") from exc


def _doc_segments(rel: str, text: str) -> list[Segment]:
    return [
        Segment("framework", rel, section, body)
        for section, body in rules.split_sections(text)
    ]


# 固定讀者／節名是本版套件的呈現契約，⛔ 不是採用者設定或情境推論。
IMMEDIATE = '立即契約'
_MODULE_READERS = {
    ('architecture', '需求'): ('PM', '需求方', '研究者'),
    ('architecture', '規劃'): ('規劃者',),
    ('architecture', '執行'): ('執行者',),
    ('architecture', '審核'): ('審核者',),
    ('codegraph', '規劃'): ('規劃者',),
    ('codegraph', '執行'): ('執行者',),
    ('codegraph', '審核'): ('審核者',),
    ('tdd', '執行'): ('執行者',),
    ('tdd', '審核'): ('審核者',),
}


@dataclass(frozen=True)
class FrameworkSelection:
    segments: list[Segment]
    modules: list[tuple[str, tuple[str, str] | None]]
    fallbacks: tuple[str, ...]
    stage_note: str = ''


def _select_doc(rel, text, wanted, fallbacks):
    """只有與同套件權威原檔逐字相同且版型已知才省略；未知原文不混入套件。"""
    expected = _RULE_HEADINGS.get(rel)
    headings = tuple(rules.headings(text))
    canonical = rules.default_rules_root() / rel
    sections = rules.split_sections(text)
    present = {name for name, _ in sections}
    trusted = (expected is not None and headings == expected and all(name in present for name in wanted)
               and len(headings) == len(set(headings))
               and canonical.is_file() and text == canonical.read_text(encoding='utf-8'))
    if not trusted:
        fallbacks.append(rel)
        return _doc_segments(rel, text)
    return [Segment('framework', rel, section, body)
            for section, body in sections if section in wanted]


def _stage_sections(role, stage):
    if role == 'PM':
        return (IMMEDIATE,) if stage == '需求' else ('PM 當值',)
    if role == '需求方' and stage == '需求':
        return (IMMEDIATE,)
    if (role, stage) in (('規劃者', '規劃'), ('執行者', '執行'), ('審核者', '審核')):
        return (IMMEDIATE,)
    if (role, stage) == ('執行者', '結案'):
        return ('機械收尾入口',)
    return ()


def select_framework(root, role, stage, modules=()):
    """本次唯一選取結果；必要清單、索引、指南定位與附錄共用，不判任務散文。"""
    fallbacks = []
    segments = []
    for rel, text in rules.core_docs(root):
        wanted = (IMMEDIATE,) if rel in ('core/boundaries.md', 'core/independence.md') else ()
        segments.extend(_select_doc(rel, text, wanted, fallbacks))
    rel, text = rules.role_doc(root, role)
    segments.extend(_select_doc(rel, text, (IMMEDIATE,), fallbacks))
    rel, text = rules.stage_doc(root, stage)
    wanted_stage = _stage_sections(role, stage)
    segments.extend(_select_doc(rel, text, wanted_stage, fallbacks))
    research_pair = role == '研究者' and stage in ('需求', '規劃')
    stage_note = ('' if wanted_stage or research_pair or role == '需求方' else
                  '此配對不新增其他角色職權，派工不明回本卡 PM。')
    selected_modules = []
    for name, doc in modules:
        if doc is None:
            selected_modules.append((name, None))
            continue
        rel, text = doc
        wanted = (IMMEDIATE,) if role in _MODULE_READERS.get((name, stage), ()) else ()
        selected = _select_doc(rel, text, wanted, fallbacks)
        # 單次選出的模組段轉成既有索引／指南定位函式的資料形狀，不重讀或另選。
        short_text = '\n\n'.join(f'## {s.section}\n\n{s.body}' for s in selected)
        selected_modules.append((name, (rel, short_text) if selected else None))
        segments.extend(selected)
    return FrameworkSelection(segments, selected_modules, tuple(fallbacks), stage_note)


def selected_checklist(segments):
    out = []
    for prefix in ('roles/', 'stages/'):
        paths = dict.fromkeys(s.path for s in segments if s.path.startswith(prefix))
        for path in paths:
            body = '\n'.join(f'- {s.section}' for s in segments if s.path == path)
            out.append(Segment('framework', path, '章節', body))
    return out


def selected_core_index(segments):
    paths = dict.fromkeys(s.path for s in segments if s.path.startswith('core/'))
    lines = []
    for path in paths:
        anchors = [s.section for s in segments if s.path == path]
        lines.append(f'- {path}（{len(anchors)} 節）：' + '／'.join(anchors))
    return Segment('framework', 'rules/core/', '節索引', '\n'.join(lines))


def _entry_rules(root, rel):
    """專屬入口直接取公共短契約＋該入口立即契約，⛔ 不偽裝成第七角色或本卡brief。"""
    fallbacks, segments = [], []
    for core_rel, text in rules.core_docs(root):
        wanted = (IMMEDIATE,) if core_rel in ('core/boundaries.md', 'core/independence.md') else ()
        segments.extend(_select_doc(core_rel, text, wanted, fallbacks))
    segments.extend(_select_doc(rel, rules.read_doc(root, rel), (IMMEDIATE,), fallbacks))
    if fallbacks:
        segments.append(Segment('framework', 'rules/', '按需取讀',
                                '未精簡：' + '、'.join(one_line(x) for x in fallbacks)))
    return segments


def coordination_rules(root):
    """共同協調入口：公共短契約＋共同協調立即契約。"""
    return _entry_rules(root, 'PM-coordination.md')


def project_rules(root):
    """專案 PM 入口：公共短契約＋專案 PM 立即契約；與共同協調同型，不是第七角色。"""
    return _entry_rules(root, 'PM-project.md')


_RULE_HEADINGS = {'PM-coordination.md': ('立即契約', '1 · 責任位置', '2 · 共享操作', '3 · 安全接手'),
 'PM-project.md': ('立即契約', '1 · 新案與拆分', '2 · 專案方向提案', '3 · 責任位置與接手'),
 'core/boundaries.md': ('立即契約',
                        '1 · 分層注入（四層）',
                        '2 · 使用者層的模型與工具資料',
                        '3 · 專案層',
                        '4 · CLI 邊界',
                        '5 · 模組四禁',
                        '6 · 偏移、根因與停止',
                        '7 · 經驗的確認、落地與退場'),
 'core/flow.md': ('1 · 為什麼有這個流程',
                  '2 · 五個階段',
                  '3 · 需求鎖定',
                  '4 · 階段確認',
                  '研究答案路徑',
                  '已定案改動路徑',
                  '具名討論對話',
                  '交付資料量',
                  '5 · 階段證據原則',
                  '6 · 審核結果與退回',
                  '7 · 工作包',
                  '8 · 結案的固定序',
                  '9 · 協作異常的停止'),
 'core/github.md': ('1 · Issue body 五章節',
                    '2 · 七個核心概念（唯一來源）',
                    '3 · 留言只有四類',
                    '4 · 裁定以留言為權威',
                    '5 · 開卡與關卡＝PM 的平台協調操作',
                    '6 · Resource 與資源租用',
                    '7 · 寫入基準'),
 'core/independence.md': ('立即契約',
                          '1 · 誰不能兼任誰',
                          '2 · 乾淨工作階段',
                          '3 · 分離程度',
                          '4 · 正式審核者的條件',
                          '5 · 審核家族的保留與送審確認'),
 'core/research.md': ('1 · 定位', '2 · 一次一問', '3 · 來源與分歧', '4 · 影響邊界', '5 · 網路使用與資料聲明', '6 · 高難度研究（例外）'),
 'core/values.md': ('⛔ 不存在的值域',),
 'modules/architecture/執行.md': ('立即契約', '操作細則'),
 'modules/architecture/審核.md': ('立即契約', '操作細則'),
 'modules/architecture/規劃.md': ('立即契約', '操作細則'),
 'modules/architecture/需求.md': ('立即契約', '操作細則'),
 'modules/codegraph/執行.md': ('立即契約', '操作細則'),
 'modules/codegraph/審核.md': ('立即契約', '操作細則'),
 'modules/codegraph/規劃.md': ('立即契約', '操作細則'),
 'modules/tdd/執行.md': ('立即契約',
                       '1 · 何時適用',
                       '2 · 在核定規劃內做',
                       '3 · 先失敗、後通過',
                       '4 · Green 之後才 Refactor',
                       '5 · 交付說明寫什麼'),
 'modules/tdd/審核.md': ('立即契約', '1 · 看什麼', '2 · 怎麼核對與必要重現', '3 · 缺少證據時怎麼判斷'),
 'roles/PM.md': ('立即契約',
                 '1 · 你⛔ 不做什麼',
                 '2 · 模型與流程協調',
                 '3 · 派工內容與需求質詢（原件優先、報告有用途；規劃先辨限制、純改期只交差異）',
                 '4 · 收交付時你檢查什麼',
                 '5 · 寫入流程狀態',
                 '6 · owner 不是第七個角色',
                 '7 · 結案（一次性處置依當輪終點退場；安全與復原證據保留）',
                 '8 · 注意事項',
                 '9 · 一卡一個 PM 對話'),
 'roles/執行者.md': ('立即契約',
                  '1 · 你可以自行調整什麼',
                  '2 · 假設失效時',
                  '3 · 交付前四項自檢',
                  '4 · 你的自檢不是審核',
                  '5 · 注意事項由你修改',
                  '6 · 獨立性'),
 'roles/審核者.md': ('立即契約',
                  '1 · 接案前確認四個前提',
                  '2 · 怎麼查',
                  '3 · 你⛔ 不得做什麼',
                  '4 · 四種結果',
                  '5 · 環境或權限不足',
                  '6 · 你回報什麼'),
 'roles/研究者.md': ('立即契約',
                  '1 · 一次一問',
                  '2 · 你在哪個階段，決定你能碰什麼',
                  '3 · 來源與分歧',
                  '4 · 影響邊界',
                  '5 · ⛔ 不替規劃者選方案',
                  '6 · 網路與資料聲明',
                  '7 · 獨立性'),
 'roles/規劃者.md': ('立即契約',
                  '1 · 你交什麼',
                  '2 · 你⛔ 不能做什麼',
                  '3 · 你的步驟是預估，不是逐檔契約',
                  '4 · 驗收怎麼定',
                  '5 · 規模只作警示',
                  '6 · 獨立性'),
 'roles/需求方.md': ('立即契約', '1 · 定義成果', '2 · 階段確認', '3 · 只有你能裁定的事', '4 · 階段確認不是審核', '5 · 你維護的模型資料'),
 'stages/執行.md': ('PM 當值',
                  '立即契約',
                  '1 · 只實作已核定方案',
                  '2 · 交付前自檢（四項，全部要做）',
                  '3 · 有疑慮就不要交付',
                  '4 · 正常修正與重跑',
                  '5 · 假設失效時',
                  '6 · 完成'),
 'stages/審核.md': ('PM 當值',
                  '立即契約',
                  '1 · 開始前先確認自己有資格',
                  '2 · 核對什麼',
                  '3 · 你⛔ 不得做的三件事',
                  '4 · 環境或權限不足',
                  '5 · 審核結果只有四種',
                  '6 · 再次審核',
                  '7 · 完成與授權'),
 'stages/結案.md': ('機械收尾入口',
                  'PM 當值',
                  '1 · 固定序（順序不可調換）',
                  '2 · 結案卡要放什麼',
                  '3 · 合併後驗證失敗',
                  '4 · 成果內容與機械發布收尾',
                  '5 · 收尾檢查'),
 'stages/規劃.md': ('PM 當值',
                  '立即契約',
                  '1 · 輸入',
                  '2 · 必要產出',
                  '3 · 驗收外檢查',
                  '4 · 執行步驟是預估',
                  '5 · 規劃／研究',
                  '6 · 邊界',
                  '7 · 完成'),
 'stages/需求.md': ('PM 當值',
                  '立即契約',
                  '1 · 這個階段要確認四件事',
                  '2 · Grilling（必做）',
                  '3 · 需求／研究',
                  '4 · 完成與鎖定',
                  '5 · 從後面退回進來時')}


def framework_rules(rules_root: Path, role: str, stage: str) -> list[Segment]:
    return select_framework(rules_root, role, stage).segments


def module_docs(rules_root: Path, names, stages, stage: str) -> list[tuple[str, tuple[str, str] | None]]:
    """已啟用模組（依 `.wf/config.json` 的宣告順序）在當前階段的文件；該階段沒有文件＝None。

    每個已啟用模組都完整驗過，不論當前階段——名稱打錯在任何階段都 typed 失敗，⛔ 不靜默略過。
    """
    return [(name, rules.module_stage_docs(rules_root, name, stages).get(stage)) for name in names]


def module_segments(docs) -> list[Segment]:
    return [segment for _, doc in docs if doc for segment in _doc_segments(*doc)]


def required_checklist(rules_root: Path, role: str, stage: str) -> list[Segment]:
    return selected_checklist(framework_rules(rules_root, role, stage))


def user_model_data(user_root: Path) -> list[Segment]:
    """模型使用說明原樣呈現；缺檔是合法的 unknown，⛔ 不是失敗。

    ⛔ 不判時效、⛔ 不逐則判欄位缺漏、⛔ 不解析內容。
    """
    out: list[Segment] = []
    for name in USER_MODEL_FILES:
        path = user_root / name
        display = f"~/.wf/{name}"
        if path.is_file():
            out.append(Segment("user", display, "全文", _read_utf8(path, display).strip("\n")))
        else:
            out.append(Segment("user", display, "缺", UNKNOWN_MODEL_DATA))
    return out


def _tool_text(user_root: Path) -> str | None:
    """只讀明列工具檔；缺席合法，壞檔不能冒充缺席。"""
    path = user_root / USER_TOOL_FILE
    display = f"~/.wf/{USER_TOOL_FILE}"
    try:
        try:
            path.lstat()
        except FileNotFoundError:
            return None
        if not path.resolve().is_relative_to(user_root.resolve()):
            raise MalformedInput(f"{display} 的符號連結越出使用者層")
        if not path.is_file():
            raise MalformedInput(f"{display} 存在但不是一般可讀檔案")
        return _read_utf8(path, display)
    except OSError as exc:
        raise MalformedInput(f"{display} 讀取失敗：{type(exc).__name__}") from exc


def user_data(user_root: Path) -> list[Segment]:
    out = user_model_data(user_root)
    text = _tool_text(user_root)
    if text is not None:
        out.append(Segment("user", f"~/.wf/{USER_TOOL_FILE}", "全文", text.strip("\n")))
    return out


def user_index(user_root: Path) -> Segment:
    models = user_model_index(user_root)
    text = _tool_text(user_root)
    status = ("未提供（選用）" if text is None else
              f"在（{sum(bool(line.strip()) for line in text.splitlines())} 非空行，全文見附錄）")
    return Segment("user", "~/.wf/", "狀態", models.body + f"\n- ~/.wf/{USER_TOOL_FILE}：{status}")


def project_layer(project_root: Path) -> list[Segment]:
    """專案層＝`<project-root>/.wf/` 下的 *.md（含 model-policy.md）。"""
    directory = project_root / ".wf"
    if not directory.is_dir():
        raise LayerMissing("project", ".wf", f"找不到 {directory}")
    paths = sorted(directory.glob("*.md"), key=lambda p: p.name)
    if not paths:
        raise LayerMissing("project", ".wf", "目錄下沒有專案層資料")
    return [
        Segment("project", f".wf/{p.name}", "全文", _read_utf8(p, f".wf/{p.name}").strip("\n"))
        for p in paths
    ]


def carried_comments(data, recent: int | None = None) -> list[int]:
    """附錄要附全文的留言序號（1-based、原序）：Issue body 引用到其 url 的每一則，加上最新 `recent` 則。

    `recent=None`＝全部。判準只有兩個機械事實——url 字面是否出現在 body、位置是否在最後 `recent` 則內；
    ⛔ 不判留言屬於哪一類（`github.md` §3 的四類是內容分類，CLI 判不得）、⛔ 不截斷、⛔ 不摘要：
    整則附或整則不附，未附的仍在首屏索引（`comment_index`）且序號不變。
    """
    total = len(data.comments)
    cutoff = 0 if recent is None else max(total - recent, 0)
    body = data.issue_body if isinstance(data.issue_body, str) else ""
    return [index for index, (url, _) in enumerate(data.comments, start=1)
            if index > cutoff or (url and url in body)]


def task_layer(data, *, recent: int | None = None) -> list[Segment]:
    """任務層＝Issue body 五章節＋七個核心概念＋留言全文（只附 `carried_comments` 選出的那些）。

    `data` 是動詞層交進來的純資料（`wfx.gh.task.TaskData`）——`wfx.core` ⛔ 不 import `wfx.gh`，
    也⛔ 不理解任務識別的格式。三者一律原樣納入，⛔ 不解析、⛔ 不驗章節、⛔ 不判留言屬於哪一類。
    """
    if not isinstance(data.fields, dict):
        raise MalformedInput("任務層的 fields 必須是 object")
    missing = [name for name in CORE_CONCEPTS if name not in data.fields]
    if missing:
        raise MalformedInput(f"任務層缺核心概念：{'、'.join(missing)}")
    body = data.issue_body
    if not isinstance(body, str) or not body.strip():
        raise LayerMissing("task", f"{data.task}#issue-body", "Issue body 缺或為空")

    out = [Segment("task", data.task, "issue-body", body.strip("\n"))]
    # 只投影七個核心概念；Project 的其餘內建欄位原樣忽略，⛔ 不是第八個核心概念、⛔ 不拒收
    rendered = "\n".join(f"{name}: {data.fields[name]}" for name in CORE_CONCEPTS)
    out.append(Segment("task", data.task, "核心概念", rendered))
    carried = set(carried_comments(data, recent))
    for index, (url, comment_body) in enumerate(data.comments, start=1):
        if index not in carried:
            continue
        lines = [f"url: {url}"] if url else []
        lines.append((comment_body or "").strip("\n"))
        out.append(Segment("task", data.task, f"comment-{index}", "\n".join(lines)))
    return out


# ── 派工首屏：只由機械資料組成的定位索引 ────────────────────────────
# 全部內容都是路徑、節錨、行數、既有欄位值與 url。
# ⛔ 不摘要、⛔ 不判讀留言屬於哪一類、⛔ 不截斷任何原文——被選入附錄的留言（`carried_comments`）全文逐字保留，其餘只在索引。
# 資料驅動的清單可帶 `limit`（#434 預設輸出）：超出時只依**位置**保留列、印一行省略數，
# ⛔ 不依內容挑選；`limit=None`＝全列（`--full`）。
# 預設輸出另帶 `single_line=True`：每列與每個任務來源標記都 escape 成恰一個實體行（`one_line`）——
# 單筆值、檔名或 url 內含換行時，「一列＝一個非空行」才成立，上限才由列數保證。⛔ 不丟字元、⛔ 不截斷，
# 原樣值在 `--full`；`--full`（`single_line=False`）逐字不變。

NO_COMMENTS = "（該卡⛔ 無留言）"
NO_HEADING = "⛔ 無 ## 標題"


def _bounded(lines: list[str], limit: int | None, *, keep_last: bool = False,
             single_line: bool = False) -> list[str]:
    """依位置保留至多 `limit` 列，其餘換成一行省略數；`None` 或未超出＝原樣。

    `single_line`：每列先 escape 成恰一個實體行（見上方說明）。
    """
    if single_line:
        lines = [one_line(line) for line in lines]
    if limit is None or len(lines) <= limit:
        return lines
    omitted = len(lines) - limit
    if keep_last:
        return [f"- （較早的 {omitted} 項未列；完整索引加 `--full`）", *lines[-limit:]]
    return [*lines[:limit], f"- （其後 {omitted} 項未列；完整索引加 `--full`）"]


def _task_path(task: str, single_line: bool) -> str:
    """任務來源標記與表頭裡的任務識別；`single_line` 時 escape 成一行。"""
    return one_line(task) if single_line else task


def _anchor_line(rel: str, text: str) -> str:
    anchors = [anchor for anchor, _ in rules.split_sections(text)]
    return f"- {rel}（{len(anchors)} 節）：" + "／".join(anchors)


def core_concept_values(data, *, single_line: bool = False) -> Segment:
    """七個核心概念的當下值；與附錄任務層同一份投影，⛔ 不另行加工（`single_line` 只 escape 斷行字元）。"""
    rows = [f"{name}: {data.fields[name]}" for name in CORE_CONCEPTS]
    return Segment("task", _task_path(data.task, single_line), "核心概念",
                   "\n".join(_bounded(rows, None, single_line=single_line)))


def rules_index(rules_root: Path) -> Segment:
    """core 六份的路徑與節錨。

    ⛔ 不印 rules-root 絕對路徑（那會讓逐字穩定隨機器而破；唯一例外是 `module_doc_index` 那一區塊）；
    stages／roles 兩份的節錨逐項列在「必要清單」，此處⛔ 不重複。
    """
    lines = [_anchor_line(rel, text) for rel, text in rules.core_docs(rules_root)]
    return Segment("framework", "rules/core/", "節索引", "\n".join(lines))


NO_MODULE_DOC = "本角色／階段無預載契約，⛔ 不注入"


def module_index(docs, *, single_line: bool = False) -> Segment:
    """已啟用模組逐個一行：當前階段的文件路徑與節錨，或「本階段無文件」。全文在附錄。"""
    lines = [
        _anchor_line(*doc) if doc else f"- {rules.MODULES_DIR}/{name}/：{NO_MODULE_DOC}"
        for name, doc in docs
    ]
    return Segment("framework", f"rules/{rules.MODULES_DIR}/", "啟用模組",
                   "\n".join(_bounded(lines, None, single_line=single_line)))


# 模組短文引用套件文件的字面寫法。`wfx/docs/` 與規則目錄同層（`pyproject.toml` 的 package data）。
MODULE_DOCS_DIR = "wfx/docs/"
MODULE_DOC_MISSING = "找不到"
_MODULE_DOC_REF = re.compile(re.escape(MODULE_DOCS_DIR) + r"[A-Za-z0-9._-]+\.md")


def module_doc_refs(docs) -> list[str]:
    """本階段已注入的模組短文裡 `wfx/docs/<檔名>.md` 的字面引用，依出現順序去重。

    只掃模組短文，core／stages／roles 提到的文件⛔ 不算；⛔ 不新增宣告或對照表、⛔ 不讀被引用的文件。
    """
    return list(dict.fromkeys(ref for _, doc in docs if doc for ref in _MODULE_DOC_REF.findall(doc[1])))


def module_doc_index(refs, rules_root: Path | None) -> Segment:
    """每份引用一行；`rules_root` 給了才解析實際路徑，`None`＝只列文件識別，本機路徑⛔ 不經過這裡。

    `wfx/docs/x.md`＝規則目錄同層的 `docs/x.md`，套件來源與 `--rules-root` 共用這一條。
    只做 `is_file()`，⛔ 不讀內容；旁邊沒有就列「找不到」，⛔ 不退回套件來源。
    這是 `brief` 輸出唯一會帶絕對路徑的地方，隨安裝位置變動（可重現性例外，見 `vnext/cli/README.md`）。
    """
    lines = [f"- {ref}" for ref in refs]
    if rules_root is not None:
        docs_dir = rules_root.resolve().parent / "docs"
        paths = [docs_dir / ref.removeprefix(MODULE_DOCS_DIR) for ref in refs]
        lines = [f"{line}：{path if path.is_file() else MODULE_DOC_MISSING}"
                 for line, path in zip(lines, paths)]
    return Segment("framework", MODULE_DOCS_DIR, "定位", "\n".join(lines))


def project_policy_index(project_segments: list[Segment], limit: int | None = None, *,
                         single_line: bool = False) -> Segment:
    """第 3 層每份政策檔的路徑與節錨；全文在附錄。傳入的就是附錄那份，⛔ 不重讀檔案。"""
    lines = [_anchor_line(segment.path, segment.body) for segment in project_segments]
    return Segment("project", ".wf/", "節索引",
                   "\n".join(_bounded(lines, limit, single_line=single_line)))


def user_model_index(user_root: Path) -> Segment:
    """模型使用說明的狀態與來源檔名；⛔ 不判時效、⛔ 不解析內容。"""
    lines = []
    for name in USER_MODEL_FILES:
        path = user_root / name
        if path.is_file():
            text = _read_utf8(path, f"~/.wf/{name}")
            filled = len([l for l in text.splitlines() if l.strip()])
            lines.append(f"- ~/.wf/{name}：在（{filled} 非空行，全文見附錄）")
        else:
            lines.append(f"- ~/.wf/{name}：{UNKNOWN_MODEL_DATA}")
    return Segment("user", "~/.wf/", "狀態", "\n".join(lines))


def user_layer_omitted_index() -> Segment:
    """`--omit-user-layer`：首屏保留標題與來源標記，內容換成固定說明一行；⛔ 不讀 `~/.wf/`。"""
    return Segment("user", "~/.wf/", "狀態", USER_LAYER_OMITTED)


def issue_section_index(rules_root: Path, data, limit: int | None = None, *,
                        single_line: bool = False) -> Segment:
    """Issue body 五章節的存在性與定位。

    `core/github.md` §1 明訂 CLI 只確認「標題在且其下非空」；本函式只做這件事，
    ⛔ 不解析散文語意。非五章節的 `## ` 標題一律照列，⛔ 不判它合不合法。
    五章節的列一律印出；`limit` 只作用在其後「五章節以外／同名重複」的列。
    """
    titles = rules.issue_section_titles(rules_root)
    # 五章節的存在／非空走 `rules.required_sections`＝與 `facts` 同一份解析來源
    required = rules.required_sections(titles, data.issue_body)
    lines = []
    for title, state, start, filled in required:
        if state == rules.MISSING:
            lines.append(f"- {title}：⛔ 標題不在 body")
        elif state == rules.EMPTY:
            lines.append(f"- {title}：標題在第 {start} 行、其下空")
        else:
            lines.append(f"- {title}：在（第 {start} 行，{filled} 非空行）")
    firsts = {title: start for title, _, start, _ in required}
    extras = []
    for anchor, start, _ in rules.section_spans(data.issue_body):
        if anchor not in titles:
            extras.append(f"- （五章節以外）{anchor}：第 {start} 行")
        elif start != firsts[anchor]:
            extras.append(f"- （同名重複）{anchor}：第 {start} 行")
    lines.extend(_bounded(extras, limit, single_line=single_line))
    return Segment("task", _task_path(data.task, single_line), "issue-body 章節", "\n".join(lines))


def comment_index(data, limit: int | None = None, *, single_line: bool = False) -> Segment:
    """全部留言逐則一行：編號、url、行數、該則首個 `## ` 標題（逐字）。

    ⛔ 不分類（`github.md` §3 的四類是內容分類，CLI 判不得）、⛔ 不挑「哪幾則是裁定」——
    裁定留言的定位靠 body §裁定紀錄 的連結索引與這份索引兩邊對照。`limit` 只依位置保留**最新**的 K 則，
    編號維持原序號；完整索引在 `--full`。
    """
    lines = []
    for index, (url, body) in enumerate(data.comments, start=1):
        text = (body or "").strip("\n")
        filled = len([l for l in text.splitlines() if l.strip()])
        heading = next(
            (l[3:].strip() for l in text.splitlines() if l.startswith("## ")), NO_HEADING
        )
        lines.append(f"- comment-{index}｜{url or '（⛔ 無 url）'}｜{filled} 非空行｜{heading}")
    return Segment("task", _task_path(data.task, single_line), "留言索引",
                   "\n".join(_bounded(lines, limit, keep_last=True, single_line=single_line))
                   or NO_COMMENTS)


# ── 相連任務（`core/github.md` §1 選用章節）：只對帶入角色呈現 ──────────────
# `linked` 是動詞層交進來的純資料（`wfx.gh.task.LinkedTask` 序列）；本層只讀屬性、⛔ 不理解 URL。
# 首屏只放機械事實（url／state／行號／行數／失敗類別），原文逐字在附錄。

LINKED_EMPTY = "（章節在，其下⛔ 無登記行）"
LINKED_COMMENT_SECTION = "已核定規劃"


def _linked_sections_line(entry, sections) -> str:
    parts = []
    for title, state, start, filled in rules.required_sections(sections, entry.body):
        if state == rules.MISSING:
            parts.append(f"{title}：⛔ 標題不在 body")
        elif state == rules.EMPTY:
            parts.append(f"{title}：標題在第 {start} 行、其下空")
        else:
            parts.append(f"{title}：在（第 {start} 行，{filled} 非空行）")
    return "｜".join(parts)


def _linked_comment_line(entry) -> str:
    if entry.comment_url is None:
        return f"{LINKED_COMMENT_SECTION}：未登記"
    if entry.comment_error is not None:
        return f"{LINKED_COMMENT_SECTION}：{entry.comment_url} 讀取失敗：{entry.comment_error}"
    if entry.comment_foreign is not None:
        return f"{LINKED_COMMENT_SECTION}：{entry.comment_url} 留言不屬於登記的相連卡：{entry.comment_foreign}"
    filled = len([l for l in entry.comment_body.splitlines() if l.strip()])
    return f"{LINKED_COMMENT_SECTION}：{entry.comment_url}（{filled} 非空行）"


def linked_index(task: str, linked, sections, limit: int | None = None, *,
                 single_line: bool = False) -> Segment:
    """每筆登記一行：序號、相連卡 url、讀取結果、state、帶入章節定位、規劃留言定位。

    ⛔ 不判是否真的相連、⛔ 不判規劃是否已核定；形狀不合的行照原文印出，⛔ 不猜、⛔ 不略過。
    `limit` 只依登記順序保留前 K 筆、印省略數；完整索引與相連卡原文在 `--full`。
    """
    lines = []
    for index, entry in enumerate(linked, start=1):
        if entry.issue_url is None:
            lines.append(f"- {index}｜無法解讀（逐字）：{entry.line}")
        elif entry.duplicate_of is not None:
            lines.append(f"- {index}｜{entry.issue_url}｜重複登記（同第 {entry.duplicate_of} 筆），⛔ 不重讀")
        elif entry.error is not None:
            lines.append(f"- {index}｜{entry.issue_url}｜讀取失敗：{entry.error}")
        else:
            lines.append(f"- {index}｜{entry.issue_url}｜{entry.state}｜"
                         f"{_linked_sections_line(entry, sections)}｜{_linked_comment_line(entry)}")
    return Segment("task", _task_path(task, single_line), "相連任務定位",
                   "\n".join(_bounded(lines, limit, single_line=single_line)) or LINKED_EMPTY)


def linked_segments(linked, sections) -> list[Segment]:
    """每張讀到的相連卡：帶入章節逐字（標題在且其下非空者）＋登記的規劃留言全文。

    來源標記 kind 仍是 `task`（⛔ 不是第五種 kind），path＝相連卡 issue url（⛔ 不含 `#`）。
    """
    out: list[Segment] = []
    for entry in linked:
        if entry.issue_url is None or entry.duplicate_of is not None or entry.error is not None:
            continue
        for title in sections:
            text = rules.section_text(entry.body, title)
            if text:
                out.append(Segment("task", entry.issue_url, title, text))
        if entry.comment_body is not None:
            out.append(Segment("task", entry.issue_url, LINKED_COMMENT_SECTION,
                               f"url: {entry.comment_url}\n{entry.comment_body.strip(chr(10))}"))
    return out
