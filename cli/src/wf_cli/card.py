"""卡片模型：Card dataclass + 範本渲染（git spec 檔骨架／Issue body／Log 行）。

架構切分（呼應 canonical AI_WORKFLOW.md §6「git 是程式碼／文件事實來源；adapter
event log 是作業狀態事實來源」，遷移後把「adapter event log」實作換成 GitHub
Issue/Project）：

- **git spec 檔**（``tasks/<CARD_ID>.md``，寫回目標 repo 並由使用者自行 commit）：
  穩定的範圍／驗收／驗證內容，不重複會變動的 Ledger 欄位。
- **GitHub Issue／Project item**：owner／worktree／iteration／交付狀態／部署狀態／
  最後交接等會變動的 current-state，以及供機器解析的資源宣告區塊、可累積的 Log。
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime

from .brief import BRIEF_SECTION_HEADING_ALIAS as BRIEF_SECTION_HEADING
from .brief import Brief
from .brief import render_block as render_brief_block
from .brief import try_parse_block as try_parse_brief
from .brief import validate_shape as validate_brief_shape
from .resources import ResourceDeclaration, render_block

TIERS = ("T0", "T1", "T2", "T3", "T4")

# 能力層級語彙**不在這裡新創**：唯一權威是 repo 根目錄 ``MODEL_ROUTING.md`` 的
# 「預設能力等級」欄（第 7–10 列）。原文四列去掉修飾後恰好三級：
#
#   第 7 列「經濟型／deterministic automation」——「／deterministic automation」是
#       同一級的英文同義註解，不是第四級。
#   第 8 列「主力型」、第 10 列「主力型」——同一級。
#   第 9 列「高階型 + 跨家族 review」——「+ 跨家族 review」是**查核側的附加要求**
#       （templates/tasks-card.md 第 4 行同樣寫「紅線須跨家族或人工」），是能力層級
#       之上疊加的獨立性條件，不是第四級。
#
# 因此本枚舉照抄權威的三級，且刻意**封閉**：沒有「其他」「未定」逃生格。每個輸入
# 落在且僅落在一格——落不進去就是硬拒，不是歸進 fallback 桶。
CAPABILITY_TIERS = ("經濟型", "主力型", "高階型")

# 決議 5（鏈式停損協定，見 docs/research/WORKFLOW-REVIEW-2026-08-04.md）：
# 鏈深硬上限＝原始目標之下 2 層；超過強制整鏈重審，不得逕行加深。
CHAIN_DEPTH_HARD_CAP = 2

_BRANCH_WORKTREE_RE = re.compile(r"^\s*(?P<branch>\S+)\s*@\s*(?P<path>.+?)\s*$")


def chain_depth_violation_message(chain_depth: int) -> str:
    """決議 5 鏈式停損協定的拒絕訊息；CLI 層（ValidationError）與 model 層
    （Card.__post_init__ 的 ValueError）共用同一段文字，避免兩處措辭各自漂移。
    """
    return (
        f"鏈深 {chain_depth} 超過硬上限：原始目標之下最深 {CHAIN_DEPTH_HARD_CAP} 層；"
        "超過須整鏈重審，不得逕行加深——見決議 5（鏈式停損協定）"
    )


def capability_tier_violation_message(axis: str, value: str) -> str:
    """能力層級不在權威語彙內時的拒絕訊息；CLI 層與 model 層共用同一段文字。

    刻意在訊息裡點名「這不是 T0–T4」：``--tier``／``級別`` 是**風險級別**（另一條
    軸），兩者都叫「tier／層級」，是本卡要消除的命名碰撞的主要誤用來源。
    """
    return (
        f"{axis}能力層級必須是 {CAPABILITY_TIERS} 之一，收到 {value!r}"
        "——語彙出自 MODEL_ROUTING.md「預設能力等級」欄，不得自創；"
        f"注意這**不是** T0–T4 風險級別（那是另一條軸，欄位名「級別」／旗標 --tier）"
    )


def capability_reason_missing_message(axis: str) -> str:
    """缺理由時的拒絕訊息。

    **硬拒而非預設＋警示**，理由寫在這裡以便被擋的人直接看到取捨：能力層級可以有
    「常見值」，但 canonical AI_WORKFLOW.md §3 Plan 要的是「建議**反映任務風險**」。
    任何預設值都是在沒有讀過這張卡的風險的情況下先填一個答案，等於把「規劃者判斷」
    降級成「CLI 猜測」——而本卡的核心痛點正是「規則寫在範本裡、產生端靜默不符」。
    預設值只會把靜默不符換成靜默填錯，痛點沒消失。
    """
    return (
        f"{axis}能力層級的理由必填，且不得為空白"
        "——canonical AI_WORKFLOW.md §3 Plan：「Plan 產出必含建議執行／查核能力層級"
        "與理由」「建議反映任務風險，不得因當下額度預先降級」。"
        "此處硬拒不設預設值：預設值等於在未讀本卡風險的前提下代替規劃者作答"
    )


# --------------------------------------------------------------------------
# 路由行的保留字元（WF-CARD-FIELD-CORRECTION1；需求方 2026-08-12 裁定）
# --------------------------------------------------------------------------
#
# **這一段是「保留字元清單」的機器可讀居所。** ``templates/tasks-card.md`` 第 4 行
# 早就逐字寫出了這些分隔符，缺的從來不是文件詳盡度，而是**沒有任何一處宣告它們是
# 保留字**、且寫入端對名字**完全不做格式檢查**。後果是 #21 的往返缺陷：
#
#     open 寫得出 ``- 執行：Claude Opus 5@Claude Code（子 agent）（建議 主力型；…）``
#     assign 讀不回（``_ROUTING_PARSE_RE`` 的名字段在第一個全形左括號就停）
#     → 同一張卡的同一行被兩支給出不一致的解讀（#21 已 🏁完成後才被發現）
#
# 修法方向是**保留字元**而非跳脫：結構字元不得同時當資料。寫入端拒收，讀取端也不把
# 它們當資料收（見 ``_ROUTING_PARSE_RE`` 的字元類與本清單同源）。
#
# **清單逐欄位不同，而且是實測出來的、不是照第 4 行的外觀推的。**
# 2026-08-12 對六個值欄位 × 四個候選結構字元做過往返實測（24 格；探針形狀見
# ``cli/tests/test_amend.py`` 的「保留字元完整性」測試，該測試就是探針的常駐版本）。
# 結論按欄位分三類：
#
#   * **名字段**（``executor``／``reviewer``）：四個字元全禁。實測四格全部使解析失配，
#     故這裡的禁止與需求方 2026-08-12 的裁定重合，不是為了對齊裁定而多禁。
#   * **理由段**（``exec_reason``／``rev_reason``）：**只禁全形空格**。
#     ``（``／``）``／``；`` 實測全部往返成立，且是**現行真實用法**——中文散文本來就
#     大量使用全形括號（#38 的規劃理由「…真實歸因（PM 的 checkpoint 記錄與可稽核
#     留痕不符），再判斷…」正是被舊 ``[^）]+`` 攔掉的真實個案：其 assign 事件落
#     ``ambiguous``、被要求填偏離理由後才放行，**不是被拒絕派工**——路由行讀不回的
#     代價是留下一筆不實的「卡面建議無法解析」，不是停機）。
#     禁全形空格則有硬理由：名字與層級都不含它之後，**整行唯一的全形空格就是軸分隔
#     符**，這條唯一性把「哪裡切開執行段與查核段」變成確定性的，不再靠正則貪婪回溯。
#
#     ⚠️ **「名字段禁四個、理由段只禁一個」不是漏寫，是實測結論。** 需求方 2026-08-12
#     的裁定原文是「全形左右括號、全形分號、全形空格…不得出現在執行者／查核者名的
#     值裡」——只涵蓋名字段。把同一份清單照抄到理由段會當場擋掉 #38 那條合法理由，
#     等於用一個新缺陷換掉舊缺陷。要改動這一格，請先重跑 24 格逐欄位往返實測。
#   * **層級段**（``exec_tier``／``rev_tier``）：不設保留字元清單，因為它是**封閉語彙**
#     （``CAPABILITY_TIERS``），值不可能由使用者自由輸入。這條保護以測試釘住
#     （語彙成員不得含任何結構字元）。實測中唯一會**靜默錯讀**的格子在這裡：層級值
#     若含全形分號，解析會讀成截斷後的前半段而不是失配——正因如此，封閉語彙那條
#     保證不能只留在註解裡。
#
# 換行字元對名字與理由皆禁：路由行是單行結構，塞進換行會在標頭區多長出一行，使候選
# 路由行不唯一 → ``ambiguous``。這同樣是「寫得出、讀不回」，與全形空格同一類。
ROUTING_NAME_RESERVED = ("（", "）", "；", "　")
ROUTING_REASON_RESERVED = ("　",)
ROUTING_TIER_SEPARATORS = ("；", "　")
# 路由行用到的**全部**結構字元（＝逐欄位清單的聯集，也是實測矩陣的行）。與
# ``ROUTING_NAME_RESERVED`` 目前值相同純屬巧合——名字段恰好把四個全禁；兩者語意不同，
# 不可互相取代。
ROUTING_STRUCTURAL_CHARS = ("（", "）", "；", "　")
_ROUTING_LINE_BREAKS = ("\n", "\r")

_ROUTING_RESERVED_ROLE = {
    "（": "界定「（建議 <層級>；<理由>）」段的左界",
    "）": "界定該段的右界",
    "；": "分隔建議層級與理由",
    "　": "分隔執行軸與查核軸，且是整行唯一的軸分隔訊號",
    "\n": "路由行是單行結構，換行會在標頭區多長出一行",
    "\r": "路由行是單行結構，換行會在標頭區多長出一行",
}


def routing_reserved_char_message(field_label: str, value: str, offending: tuple[str, ...]) -> str:
    """路由行欄位含保留字元時的拒絕訊息；寫入端與 model 層共用同一段文字。

    訊息裡逐字說明每個字元承擔什麼結構，並給出可用的替代寫法——被擋的人要的是
    「那我該怎麼寫」，不是「你錯了」。半形括號／分號／空白不承擔結構，可直接用。
    """
    roles = "、".join(f"{ch!r}（{_ROUTING_RESERVED_ROLE[ch]}）" for ch in offending)
    return (
        f"{field_label}不得含路由行保留字元：{roles}"
        "——這些字元在 templates/tasks-card.md 第 4 行承擔結構，寫進值裡會讓 open "
        "寫得出、assign 讀不回（WF-CLI-ROUTING-TIER1 的往返缺陷）。"
        "改用半形括號 ()／半形分號 ;／半形空白，它們不承擔結構。"
        "（理由欄只禁全形空格；全形括號與全形分號在理由裡合法，不必改寫。）"
        f"收到 {value!r}"
    )


def validate_routing_field(field_label: str, value: str, reserved: tuple[str, ...]) -> None:
    """單一路由行欄位的保留字元檢查；不合格一律 ``ValueError``。

    ``reserved`` 由呼叫端指定（名字段與理由段的清單不同，見上方說明），這裡不內建
    預設值——「哪些字元對這個欄位是結構」是欄位的性質，不該由本函式代為猜測。
    """
    offending = tuple(
        ch for ch in (*reserved, *_ROUTING_LINE_BREAKS) if ch in (value or "")
    )
    if offending:
        raise ValueError(routing_reserved_char_message(field_label, value, offending))


def validate_routing_names(*, executor: str, reviewer: str) -> None:
    """執行者／查核者**名字**的保留字元檢查；不合格一律 ``ValueError``。

    刻意獨立成具名函式而不是塞進 ``validate_capability_routing`` 的可選參數：後者
    的兩個呼叫端（``commands/open_cmd.py``、``Card.__post_init__``）不會同時改，
    加一個有預設值的參數等於留一個「沒傳就不檢查」的靜默洞——正是本卡要消滅的形態。

    **兩個呼叫端各自負責一半，缺一不可**：

    - ``commands/open_cmd.py`` 的前置檢查給的是**乾淨的拒絕**——``[open] 拒絕：…``
      ＋ 退出碼 2，與理由側同一種形狀。``cli.py`` 的 ``KNOWN_ERRORS`` 不收
      ``ValueError``，少了這一道就會以 traceback 收場，而**以 stack trace 收場的
      fail-closed 不算乾淨拒絕**。
    - ``Card.__post_init__`` 給的是**防線**：繞過 CLI 直接建 Card 的路徑同樣擋得住，
      且 Card 建構早於任何 GitHub 寫入，故拒收不留半寫狀態。
    """
    for axis, name in (("執行者", executor), ("查核者", reviewer)):
        validate_routing_field(f"{axis}名", name, ROUTING_NAME_RESERVED)


def validate_capability_routing(
    *,
    executor_capability: str,
    executor_capability_reason: str,
    reviewer_capability: str,
    reviewer_capability_reason: str,
) -> None:
    """規劃期路由的機械檢查（執行／查核各一層級＋一理由）；不合格一律 ``ValueError``。

    純函式、不碰網路，故 CLI 層（``commands/open_cmd.py``）與 model 層
    （``Card.__post_init__``）呼叫同一份，兩層不會 drift 出不一致的判準。

    理由段的保留字元一併在此檢查——這兩個呼叫端都已存在，故理由側的拒收在
    ``open`` 是完整的（``[open] 拒絕：…`` ＋ 退出碼 2）。名字側見
    ``validate_routing_names`` 的說明。
    """
    for axis, tier, reason in (
        ("執行", executor_capability, executor_capability_reason),
        ("查核", reviewer_capability, reviewer_capability_reason),
    ):
        if tier not in CAPABILITY_TIERS:
            raise ValueError(capability_tier_violation_message(axis, tier))
        if not reason or not reason.strip():
            raise ValueError(capability_reason_missing_message(axis))
        validate_routing_field(f"{axis}能力層級理由", reason, ROUTING_REASON_RESERVED)


def now_iso8601() -> str:
    """寫入當下的系統時鐘，本機時區，完整 ISO-8601（含時分秒與時區）。

    對齊需求方裁決：「最後交接＝TEXT 完整 ISO-8601 單欄（字典序即時序）」——
    字典序等於時序的前提是格式固定寬度、時區固定。刻意用 ``isoformat(timespec=
    "seconds")`` 而非 ``strftime("%z")``：後者的時區產出 ``+0800``（無冒號），
    與既有事件慣例（``occurred_at": "2026-08-04T21:48:37+08:00"``）及 OPS-STATE-
    PLANE-MIG1 實測值不一致，字典序比較時每字元對齊才可靠。
    """
    dt = datetime.now().astimezone()
    return dt.isoformat(timespec="seconds")


_OWNER_PLACEHOLDER_PREFIXES = ("待指派", "待建立", "待認領", "—")


def is_owner_assigned(owner: str | None) -> bool:
    """owner 欄是否已指向真正的執行者，而非「待指派／待建立／待認領／—」佔位字串。

    assign 的資源交集檢查與 doctor 的殘留 lease 檢查共用同一套「什麼算已認領」
    判準，避免兩處各自定義漂移出不一致的行為。
    """
    if not owner:
        return False
    return not owner.strip().startswith(_OWNER_PLACEHOLDER_PREFIXES)


def format_branch_worktree(branch: str | None, worktree: str | None) -> str:
    if not branch and not worktree:
        return "—"
    return f"{branch or '—'} @ {worktree or '—'}"


def parse_branch_worktree(value: str) -> tuple[str | None, str | None]:
    """解析 Ledger 慣例的複合字串 ``branch @ path``；``—`` 或空字串回傳 (None, None)。"""
    if not value or value.strip() in {"—", ""}:
        return None, None
    match = _BRANCH_WORKTREE_RE.match(value)
    if not match:
        return None, None
    return match.group("branch"), match.group("path")


@dataclass
class Card:
    card_id: str
    feature: str
    tier: str
    db_scope: str
    core_pain: str
    service_goal: str
    resources: ResourceDeclaration
    # 規劃期路由（無預設值＝建構 Card 就必須給）。刻意不設 default：範本第 4 行把
    # 這四項列為卡面欄位，而本卡的痛點就是「產生端可以不給也不報錯」。放在
    # dataclass 的必填區，等於連繞過 CLI 直接建 Card 都無法產出不符範本的卡。
    executor_capability: str
    executor_capability_reason: str
    reviewer_capability: str
    reviewer_capability_reason: str
    #: 卡片簡介（canonical §6.3）。⚠️ **可選**——既有卡在本欄位上線前一律沒有簡介，
    #: ⛔ 不得讓它們因缺欄位而無法 amend 或 handoff（fail-open，見 brief.try_parse_block）。
    brief: str | None = None
    initiative: str | None = None
    requested_by: str = "—"
    planned_by: str = "—"
    executor: str = "待指派"
    reviewer: str = "待指派"
    spec_baseline: str = "—"
    acceptance: list[str] = field(default_factory=lambda: ["TODO：填入可獨立驗證的條件"])
    verification: list[str] = field(default_factory=lambda: ["TODO：填入驗證指令與證據要求"])
    owner: str = "待指派"
    branch: str | None = None
    worktree: str | None = None
    iteration: int = 0
    delivery_status: str = "💡需求"
    deployment_status: str = "—不適用"
    last_handoff: str = field(default_factory=now_iso8601)
    chain_depth: int = 0

    def __post_init__(self) -> None:
        if self.tier not in TIERS:
            raise ValueError(f"tier 必須是 {TIERS} 之一，收到 {self.tier!r}")
        if self.resources.db_scope != self.db_scope:
            # db_scope 是資源宣告的一部分，這裡保留獨立欄位方便 CLI 參數化，
            # 但兩者必須一致，不允許卡面文字與機器可讀宣告各說各話。
            raise ValueError(
                "db_scope 與資源宣告內的 db_scope 不一致："
                f"{self.db_scope!r} vs {self.resources.db_scope!r}"
            )
        validate_capability_routing(
            executor_capability=self.executor_capability,
            executor_capability_reason=self.executor_capability_reason,
            reviewer_capability=self.reviewer_capability,
            reviewer_capability_reason=self.reviewer_capability_reason,
        )
        # 寫入端拒收（WF-CARD-FIELD-CORRECTION1 驗收 (b)）：不得靜默接受一個自己
        # 讀不回的名字。放在 Card 建構而非只放 CLI，是因為繞過 CLI 直接建 Card 的
        # 路徑（測試／未來呼叫端）同樣不該產出無法解析的路由行。
        validate_routing_names(executor=self.executor, reviewer=self.reviewer)
        if self.chain_depth > CHAIN_DEPTH_HARD_CAP:
            # 與 validation.validate_chain_depth 相同的機械紅線，這裡是繞過 CLI
            # 直接建構 Card（測試／未來呼叫端）時的防線；CLI 路徑應該在到達這裡
            # 之前就已經被 validate_chain_depth 攔下並回報 ValidationError。
            raise ValueError(chain_depth_violation_message(self.chain_depth))

    @property
    def branch_worktree(self) -> str:
        return format_branch_worktree(self.branch, self.worktree)


# 規劃期路由的**格式版本標記**（WF-CLI-ROUTING-TIER1 R3-001）。
#
# 為什麼需要它：舊制卡面第 4 行的執行／查核兩欄都是**不受限的自由文字**，因此舊卡可以
# 產生與新制**逐位元組相同**的一行——2026-08-11 以 format_routing_line 對照實證：
#
#   新制 Card(executor='待指派', executor_capability='主力型', …) 渲染
#   舊制 executor 自由文字填 '待指派（建議 主力型；跨模組）'
#   → 兩者字串相等
#
# 所以「從 body 內容判斷這張卡是不是新制」在資訊上不可能為真。R2-001／R3-001 兩輪都
# 是在這個不可能的問題上調整啟發式：先用「正規表示式有沒有匹配」（→ 排版壞掉的新卡
# 被寫成「無建議」），再用「行內有沒有『建議』字樣或能力層級值」（→ 舊卡自由文字寫
# 「依建議降級」「主力型模型當班」就被誤判為新制）。自然語言 token 不是格式版本訊號。
#
# 誠實解是**遷移標記**：新制卡由 open 寫入一個機器可辨識的版本標記，判準只看標記，
# 完全不看自由文字。沿用本 repo 既有的 HTML 註解標記慣例（resources.py 的
# `<!-- resource-claims:begin -->`、doctor.py 的 `<!-- wf-review-event:v1 ... -->`），
# 不另創一套。與 doctor 的事件 marker 不碰撞：後者只掃 Issue **留言**且鎖
# `wf-review-event:` 前綴。
#
# 殘留假設（明說，不宣稱絕對）：舊卡的自由文字不會剛好含這串 HTML 註解。這與「不會
# 剛好含『建議』二字」是不同量級的假設——前者不是人會打進姓名欄的東西。
ROUTING_MARKER = "<!-- wf-routing:v1 -->"


def format_routing_line(c: Card) -> str:
    """``templates/tasks-card.md`` 第 4 行（執行／查核＋建議能力層級＋理由）。

    抽成單一函式是因為 git spec 檔與 Issue body 兩個渲染路徑都要輸出它——兩處各自
    f-string 就會 drift，而範本一致性正是本欄位存在的理由。範本原文：

        - 執行：<模型@工具／待指派>（建議 <MODEL_ROUTING 能力層級>；<能力軸理由>）
          查核：<模型@工具／待指派>（<層級；紅線須跨家族或人工>；須 ≠ 執行）

    括號內第一段填層級、第二段填理由；「紅線須跨家族或人工」「須 ≠ 執行」是範本給
    規劃者的填寫指示（規則文字），不是要逐字複製進卡面的內容，故不渲染。
    """
    return (
        f"{ROUTING_MARKER}\n"
        f"- 執行：{c.executor}"
        f"（建議 {c.executor_capability}；{c.executor_capability_reason}）"
        f"　查核：{c.reviewer}"
        f"（建議 {c.reviewer_capability}；{c.reviewer_capability_reason}）"
    )


def render_spec_markdown(c: Card) -> str:
    """git spec 檔骨架（寫入目標 repo ``tasks/<CARD_ID>.md``）。"""
    acceptance = "\n".join(f"- [ ] {line}" for line in c.acceptance)
    verification = "\n".join(f"- [ ] {line}" for line in c.verification)
    return f"""# {c.card_id} {c.feature}　〔{c.tier}〕

- 需求：{c.requested_by}　規劃：{c.planned_by}
{format_routing_line(c)}
- Initiative：{c.initiative or '—'}　spec 基線：{c.spec_baseline}
- DB：db_scope={c.db_scope}
- 服務的原始目標：{c.service_goal}
- owner、worktree、iteration、交付／部署狀態、最後交接、資源宣告與 Log
  current-state 見對應 GitHub Issue／Project item（卡ID：{c.card_id}），不重複於此檔。

## 核心痛點

- **痛點**：{c.core_pain}

## 驗收條件

{acceptance}

## 驗證

{verification}
"""


def render_issue_body(c: Card) -> str:
    """GitHub Issue／draft item body（含資源宣告 fenced JSON 區塊與 Log 章節）。"""
    acceptance = "\n".join(f"- [ ] {line}" for line in c.acceptance)
    verification = "\n".join(f"- [ ] {line}" for line in c.verification)
    resource_block = render_block(c.resources)
    brief_block = f"{render_brief_block(Brief(text=c.brief))}\n\n" if c.brief else ""
    return f"""- 需求：{c.requested_by}　規劃：{c.planned_by}
{format_routing_line(c)}
- Initiative：{c.initiative or '—'}　spec 基線：{c.spec_baseline}
- DB：db_scope={c.db_scope}
- 服務的原始目標：{c.service_goal}

{brief_block}## 核心痛點

- **痛點**：{c.core_pain}

{resource_block}

## 驗收條件

{acceptance}

## 驗證

{verification}

## Log

- {now_iso8601()} open by {c.planned_by}；owner {c.owner}；iteration {c.iteration}。
"""


_LOG_HEADING = "## Log"


def append_log_line(body: str, line: str) -> str:
    """在 body 的 ``## Log`` 區段末端附加一行；沒有該區段就新增一個到 body 尾端。

    這是 Issue／draft item body 版的 append-only 留痕，對齊
    ``templates/tasks-card.md`` 既有 Log 慣例（不可覆寫歷史，只能加行）。
    """
    entry = f"- {line}"
    if _LOG_HEADING in body:
        return body.rstrip("\n") + f"\n{entry}\n"
    return body.rstrip("\n") + f"\n\n{_LOG_HEADING}\n\n{entry}\n"


# --------------------------------------------------------------------------
# 開卡後的卡面修訂（WF-CLI-CARD-AMEND1）
# --------------------------------------------------------------------------
#
# 這些是純函式：吃 body 字串、回傳 (新 body, 被改欄位的原值)，不碰網路。原值一律
# 回傳而非丟棄，呼叫端才有東西寫進 Log——「不得無痕覆寫」是本能力的硬要求。
#
# 所有修訂**只作用於 ``## Log`` 之前的區段**。Log 是 append-only 留痕，修訂能力
# 不為自己破例；真要動 Log 的唯一合法方式是再 append 一行。


class AmendError(ValueError):
    """卡面修訂失敗：錨點缺失／不唯一／值未變更／目標落在 Log 區段。"""


_ACCEPTANCE_HEADING = "## 驗收條件"
_VERIFICATION_HEADING = "## 驗證"
_RESOURCE_HEADING = "## 資源宣告"
_CORE_PAIN_HEADING = "## 核心痛點"
_SPEC_BASELINE_RE = re.compile(r"^- Initiative：(?P<init>.*)　spec 基線：(?P<base>.*)$")
_CHECKBOX_RE = re.compile(r"^- \[(?P<state>[ xX])\] (?P<text>.*)$")
_CORE_PAIN_RE = re.compile(r"^- \*\*痛點\*\*：(?P<pain>.*)$")
_REQUESTED_BY_RE = re.compile(r"^- 需求：(?P<requested>.*?)　規劃：(?P<planned>.*)$")


def split_at_log(body: str) -> tuple[str, str]:
    """切成「Log 之前」與「``## Log`` 起的全部」。修訂只准動前者。

    刻意 fail closed：body 出現 ``## Log`` 字樣卻不是獨立標題行時直接拒絕。實務上
    這代表排版已被破壞（例如有人把換行寫成字面 ``\\n``），此時任何依標題定位的
    區段替換都可能誤動 Log。
    """
    lines = body.splitlines()
    idx = [i for i, line in enumerate(lines) if line.strip() == _LOG_HEADING]
    if len(idx) > 1:
        raise AmendError(f"body 內有 {len(idx)} 個 `## Log` 標題，無法安全定位修訂範圍")
    if not idx:
        if _LOG_HEADING in body:
            raise AmendError(
                "body 含 `## Log` 字樣但它不是獨立標題行（排版可能已被字面 \\n 破壞）；"
                "拒絕修訂，以免區段替換誤動 Log"
            )
        return body, ""
    return "\n".join(lines[: idx[0]]), "\n".join(lines[idx[0] :])


def _join(head: str, tail: str) -> str:
    return f"{head.rstrip()}\n\n{tail.strip()}\n" if tail else f"{head.rstrip()}\n"


def _locate_section(lines: list[str], heading: str) -> tuple[int, int]:
    """回傳該章節的 [起始標題列, 下一個 ``## `` 標題列或結尾)。標題須唯一。"""
    starts = [i for i, line in enumerate(lines) if line.strip() == heading]
    if len(starts) != 1:
        raise AmendError(
            f"章節 `{heading}` 在 Log 之前出現 {len(starts)} 次，必須恰好 1 次才能安全替換"
        )
    start = starts[0]
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            return start, j
    return start, len(lines)


def _read_checklist(lines: list[str]) -> list[tuple[str, str]]:
    """讀出 ``- [ ] text`` 形式的項目，保留勾選狀態。"""
    out: list[tuple[str, str]] = []
    for line in lines:
        m = _CHECKBOX_RE.match(line.strip())
        if m:
            out.append((m.group("state"), m.group("text")))
    return out


def _amend_checklist(
    body: str, heading: str, new_items: list[str], *, preserve_checked: bool = False
) -> tuple[str, str]:
    if not new_items or any(not item.strip() for item in new_items):
        raise AmendError(f"`{heading}` 的新內容不得為空，也不得含空白項目")
    head, tail = split_at_log(body)
    lines = head.splitlines()
    start, end = _locate_section(lines, heading)
    old = _read_checklist(lines[start + 1 : end])
    old_repr = "；".join(f"[{s}] {t}" for s, t in old) or "（原本無項目）"
    # 預設一律重設為未勾選：整份替換代表驗收語意已變動，此時「文字相同」不保證
    # 「仍然成立」——相鄰條件全改時，沿用勾選會把過期的完成證據當成現況。
    # 需要沿用時由呼叫端顯式指定，責任因此可歸屬。
    prior = {t: s for s, t in old} if preserve_checked else {}
    rendered = [f"- [{prior.get(item, ' ')}] {item}" for item in new_items]
    if rendered == [line.strip() for line in lines[start + 1 : end] if line.strip()]:
        raise AmendError(f"`{heading}` 的新內容與現值相同；拒絕寫入不實的修訂留痕")
    new_lines = lines[: start + 1] + ["", *rendered, ""] + lines[end:]
    return _join("\n".join(new_lines), tail), old_repr


def amend_acceptance(
    body: str, new_items: list[str], *, preserve_checked: bool = False
) -> tuple[str, str]:
    """整份替換「驗收條件」；回傳 (新 body, 原內容含勾選狀態)。"""
    return _amend_checklist(
        body, _ACCEPTANCE_HEADING, new_items, preserve_checked=preserve_checked
    )


def amend_verification(
    body: str, new_items: list[str], *, preserve_checked: bool = False
) -> tuple[str, str]:
    """整份替換「驗證」；回傳 (新 body, 原內容含勾選狀態)。"""
    return _amend_checklist(
        body, _VERIFICATION_HEADING, new_items, preserve_checked=preserve_checked
    )


def amend_spec_baseline(body: str, new_value: str) -> tuple[str, str]:
    """改 spec 基線（它內嵌在 Initiative 那一行）；回傳 (新 body, 原值)。"""
    if not new_value.strip():
        raise AmendError("spec 基線不得為空；無基線請明確填 `—`")
    if "\n" in new_value or "\r" in new_value:
        # spec 基線是單行欄位，內嵌換行會在**標頭區**多長出一行——而標頭區正是路由
        # 版本宣告的判定範圍（見 compare_capability_to_card）。單行欄位就該保持單行，
        # 這裡把它擋在寫入前，而不是讓下游去分辨那行是不是宣告。
        raise AmendError("spec 基線是單行欄位，不得含換行（會在卡面標頭區插入額外行）")
    head, tail = split_at_log(body)
    lines = head.splitlines()
    hits = [i for i, line in enumerate(lines) if _SPEC_BASELINE_RE.match(line)]
    if len(hits) != 1:
        raise AmendError(
            f"`- Initiative：…　spec 基線：…` 這一行在 Log 之前命中 {len(hits)} 次，必須恰好 1 次"
        )
    match = _SPEC_BASELINE_RE.match(lines[hits[0]])
    assert match is not None
    old = match.group("base")
    if old.strip() == new_value.strip():
        raise AmendError("spec 基線與現值相同；拒絕寫入不實的修訂留痕")
    lines[hits[0]] = f"- Initiative：{match.group('init')}　spec 基線：{new_value}"
    return _join("\n".join(lines), tail), old


def amend_resource_block(body: str, rendered_block: str) -> tuple[str, str]:
    """整份替換「資源宣告」章節；``rendered_block`` 須含標題（``resources.render_block``
    的輸出即是）。回傳 (新 body, 原章節原文)。
    """
    head, tail = split_at_log(body)
    lines = head.splitlines()
    start, end = _locate_section(lines, _RESOURCE_HEADING)
    old_repr = "\n".join(lines[start:end]).strip()
    new_lines = lines[:start] + rendered_block.splitlines() + [""] + lines[end:]
    candidate = _join("\n".join(new_lines), tail)
    if candidate == _join(head, tail):
        raise AmendError("資源宣告與現值相同；拒絕寫入不實的修訂留痕")
    return candidate, " ".join(old_repr.split())


def amend_initiative(body: str, new_value: str) -> tuple[str, str]:
    """改 Initiative（與 spec 基線同一行）；回傳 (新 body, 原值)。

    刻意與 ``amend_spec_baseline`` 分成兩個函式而非一個帶兩參數的：兩者的授權
    層級相同（都只需 ``--reason``），但**語意不同**——spec 基線是版本釘選，
    Initiative 是父卡身分。同一次修訂改動其中一個時，另一個必須逐字保留，
    分開實作才能讓「只改一半」成為型別上的預設而不是要記得做的事。
    """
    if not new_value.strip():
        raise AmendError("Initiative 不得為空；無父卡請明確填 `—`")
    if "\n" in new_value or "\r" in new_value:
        # 與 spec 基線同理：這是標頭區的單行欄位，內嵌換行會多長出一行，
        # 而標頭區正是路由版本宣告的判定範圍（見 compare_capability_to_card）。
        raise AmendError("Initiative 是單行欄位，不得含換行（會在卡面標頭區插入額外行）")
    head, tail = split_at_log(body)
    lines = head.splitlines()
    hits = [i for i, line in enumerate(lines) if _SPEC_BASELINE_RE.match(line)]
    if len(hits) != 1:
        raise AmendError(
            f"`- Initiative：…　spec 基線：…` 這一行在 Log 之前命中 {len(hits)} 次，必須恰好 1 次"
        )
    match = _SPEC_BASELINE_RE.match(lines[hits[0]])
    assert match is not None
    old = match.group("init")
    if old.strip() == new_value.strip():
        raise AmendError("Initiative 與現值相同；拒絕寫入不實的修訂留痕")
    lines[hits[0]] = f"- Initiative：{new_value}　spec 基線：{match.group('base')}"
    return _join("\n".join(lines), tail), old


def amend_brief(body: str, new_value: str) -> tuple[str, str | None]:
    """改（或首次寫入）卡片簡介；回傳 (新 body, 原值或 None)。

    canonical §6.3：body 哨兵區塊為**權威**、Project TEXT 欄位為恆等導出。本函式只動
    body 那一半——欄位由指令層在 body 寫成功後才寫，並讀回驗證（失敗模式是
    「body 已更新、欄位過期」，偵測見 :func:`brief.drifted`）。

    ⚠️ **既有卡沒有 ``## 簡介`` 區段**（canonical §6.3 逐字：今天沒有任何卡符合這一條）。
    ⇒ 找不到區段時**插入**一個到 ``## 核心痛點`` 之前，⛔ 不是報錯——那會讓 188 張既有卡
    永遠補不了簡介，而本卡的存在理由正是給它們一條通道。

    ⛔ 形狀由 :func:`brief.validate_shape` 驗（必含兩個標記、不驗字數），⛔ 不在此重寫。
    """
    validate_brief_shape(new_value)
    head, tail = split_at_log(body)
    lines = head.splitlines()
    old: str | None = None
    try:
        start, end = _locate_section(lines, BRIEF_SECTION_HEADING)
    except AmendError:
        if any(line.strip() == BRIEF_SECTION_HEADING for line in lines):
            raise
        start = end = None
    if start is not None and end is not None:
        parsed = try_parse_brief(body)
        if parsed is None:
            # ⛔ **fail-closed**（查核 R1-004）：區段在、但解析不出來，代表哨兵已被
            # 破壞或內容被手改過。此時覆蓋會讓舊內容永久消失，而 Log 會錯記成
            # 「原本沒有」——⚠️ **資料遺失加上留痕說謊**，兩者疊加。
            # ⇒ 插入通道只給「確實沒有簡介區段」的卡；壞掉的區段須人工先修。
            raise AmendError(
                f"`{BRIEF_SECTION_HEADING}` 區段存在但解析不出簡介"
                "（哨兵可能被破壞或內容被手改）。⛔ 拒絕覆蓋——覆蓋會讓舊內容永久消失，"
                "且 Log 會把它記成「原本沒有」。請先人工修復該區段的哨兵，或整段刪除後再重寫。"
            )
        old = parsed.text
        block = render_brief_block(Brief(text=new_value)).splitlines()
        lines[start:end] = block + [""]
    else:
        # 插入位置：第一個 ``## `` 章節之前。⛔ **不能只認 ``## 核心痛點``**——
        # 實測 61 張活卡中有 24 張（39%）沒有該章節（MIG1 一次性遷移卡用
        # ``## Spec``／``## 現況摘要``），只認它會讓那 24 張永遠補不了簡介，
        # 而本函式的存在理由正是給既有卡一條通道（查核 V5 以 cpbl#53 抓到）。
        # ⚠️ 找不到任何 ``## `` 章節時附在 head 末端——那種 body 已經不是卡片
        # 範本的形狀，但補簡介仍不該因此失敗。
        first_section = next(
            (i for i, line in enumerate(lines) if line.startswith("## ")),
            len(lines),
        )
        block = render_brief_block(Brief(text=new_value)).splitlines()
        lines[first_section:first_section] = block + [""]
    new_head = "\n".join(lines)
    return (new_head + ("\n" + tail if tail else "\n"), old)


def amend_core_pain(body: str, new_value: str) -> tuple[str, str]:
    """改核心痛點；回傳 (新 body, 原值)。

    **這個欄位與其他被 amend 的欄位不同類。** 它餵給查核第一判準
    ``core_pain_resolved``（canonical §5.1、``templates/review-prompt.md`` §2），
    該判準具否決權：痛點未消即 ``REQUEST_CHANGES``，即使驗收清單全過。

    因此本函式**刻意只做字串替換、不含任何授權判斷**——授權屬指令層
    （見 ``commands/amend_cmd.py`` 的「核心痛點的授權模型」）。純函式層保持
    無副作用可測，但呼叫端不得繞過指令層的授權檢查直接用它改卡。
    """
    if not new_value.strip():
        raise AmendError("核心痛點不得為空——它是查核第一判準的來源，空值等於移除否決權")
    if "\n" in new_value or "\r" in new_value:
        # 痛點在範本裡是 `- **痛點**：…` 單行條目。允許換行會讓下一次修訂
        # 定位不到唯一錨點（_CORE_PAIN_RE 逐行比對），把可改欄位變成不可改。
        raise AmendError("核心痛點是單行欄位，不得含換行（會破壞 `- **痛點**：` 錨點的唯一性）")
    head, tail = split_at_log(body)
    lines = head.splitlines()
    start, end = _locate_section(lines, _CORE_PAIN_HEADING)
    hits = [i for i in range(start + 1, end) if _CORE_PAIN_RE.match(lines[i].strip())]
    if len(hits) != 1:
        raise AmendError(
            f"`- **痛點**：…` 這一行在 `{_CORE_PAIN_HEADING}` 章節內命中 {len(hits)} 次，必須恰好 1 次"
        )
    match = _CORE_PAIN_RE.match(lines[hits[0]].strip())
    assert match is not None
    old = match.group("pain")
    if old.strip() == new_value.strip():
        raise AmendError("核心痛點與現值相同；拒絕寫入不實的修訂留痕")
    lines[hits[0]] = f"- **痛點**：{new_value}"
    return _join("\n".join(lines), tail), old


class RequesterUnparseable(AmendError):
    """卡面「需求：」欄缺漏或無法解析。

    獨立成一個類別而非沿用 ``AmendError``，是因為它的**處置方式不同**：一般
    ``AmendError`` 是「這次修訂不合法」，本例外是「**授權無法機械核對**」。
    ``review-escalation.md`` §4 第 2 款對此已有明文：「該欄未宣告或無法解析時
    本出口不可用，adapter 一律 fail-closed——無法機械核對的授權不得以自述成立」。
    呼叫端必須據此拒絕，不得退回「找不到就當作放行」。
    """


def parse_requested_by(body: str) -> str:
    """讀出卡面「需求：」欄宣告的帳號（``wfcli open`` 寫入的 ``requested_by``）。

    **本函式刻意具名並公開匯出，供跨卡共用。** 目前有兩個已知消費者：

    1. 本檔的卡面修訂授權（核心痛點更正、紅線級別降級）——比對裁定留言的
       GitHub comment author 是否為需求方；
    2. ``review-escalation.md`` §4 的 ``deferred_findings`` 出口——第 2 款要求
       ``deferred_by`` 逐字等於本欄、第 3 款要求它不等於 owner／reviewer。
       該 checkpoint writer 尚未實作（屬另一張卡）。

    兩處若各寫一份解析器就會 drift，而 drift 的後果是**兩個授權閘門對「誰是
    需求方」給出不同答案**。因此這裡先落一份，後續消費者匯入而非重寫。

    只讀 ``## Log`` 之前的區段：Log 會逐字引用被 amend 掉的舊值原文，其中可能
    含字面的「- 需求：」，不切掉就會把歷史當成現況讀（與
    ``compare_capability_to_card`` 同一個理由）。

    fail closed：命中次數不等於 1、或值為空／佔位符時拋 ``RequesterUnparseable``。
    """
    head, _ = split_at_log(body)
    hits = [m for m in (_REQUESTED_BY_RE.match(line) for line in head.splitlines()) if m]
    if len(hits) != 1:
        raise RequesterUnparseable(
            f"`- 需求：…　規劃：…` 這一行在 Log 之前命中 {len(hits)} 次，必須恰好 1 次；"
            "無法機械核對需求方身分，拒絕以自述成立"
        )
    value = hits[0].group("requested").strip()
    # 佔位字串判準與 is_owner_assigned 共用同一組前綴，避免兩處對「這欄填了沒」
    # 漂移出不一致的答案。
    if not value or value.startswith(_OWNER_PLACEHOLDER_PREFIXES):
        raise RequesterUnparseable(
            f"卡面「需求：」欄為 {value or '（空）'!r}，未宣告實際帳號；"
            "無法機械核對需求方身分，拒絕以自述成立"
        )
    return value


def is_tier_downgrade(old_tier: str | None, new_tier: str) -> bool:
    """新級別是否低於原級別。原級別未知（未設定／不在語彙內）時一律回 False。

    未知即 False 是刻意的：把「讀不出原值」當成降級會讓正常的補值操作被擋，
    而降級的額外要求本就該由**可確認的**原值觸發。讀不出原值時真正的問題是
    卡面壞了，那由其他檢查處理。
    """
    if old_tier not in TIERS or new_tier not in TIERS:
        return False
    return TIERS.index(new_tier) < TIERS.index(old_tier)


# 需求方**親自操作**規劃閘門的級別（canonical §3.1 三級制）：
#
#   - Initiative／T4／不可逆 → 同步對抗式質詢真對話（「不得以 brief 代替對話」）
#   - T3                     → 核心痛點三問，**需求方批註放行**後才進 📥Backlog
#   - 所有 T2 以上           → 前提清單附實查證據（規劃者的義務，非需求方閘門）
#
# 從 T3／T4 降下來，移除的是需求方**本人**操作過的閘門；T2 以下沒有這種閘門。
# 這就是降級授權要求只綁在這兩級的理由，見 amend_cmd「級別降級的不對稱」。
REQUESTER_GATED_TIERS = ("T3", "T4")


def tier_downgrade_needs_ruling(old_tier: str | None, new_tier: str) -> bool:
    """降級是否需要需求方裁定留痕（而非只要 ``--reason``）。"""
    return is_tier_downgrade(old_tier, new_tier) and old_tier in REQUESTER_GATED_TIERS


# --------------------------------------------------------------------------
# 派工端：實際能力層級 vs 卡面建議（WF-CLI-ROUTING-TIER1 R1-001）
# --------------------------------------------------------------------------
#
# ``MODEL_ROUTING.md`` 第 14 行後半：「派工時可依可用性偏離建議，但實際模型與偏離
# 理由記入 claim 事件。」開卡端負責寫下建議，這一段負責在 assign 時把「實際」與
# 「建議」對起來。
#
# **卡面建議只存在於 Issue body**：``project.FIELD_SPECS`` 的 13 個凍結欄位沒有任何
# 一個放能力層級（2026-08-11 以 ``FIELD_SPECS``／``CARD_FIELD_MAP``／``open_cmd`` 的
# values dict 三處查證），所以解析 body 第 2 行是唯一路徑。這條路徑的脆弱性必須明講，
# 不能當成隱含前提：
#
#   1. 它依賴 ``format_routing_line`` 的輸出形狀。兩者同檔且有 round-trip 測試
#      （render → parse 讀回同一層級），改渲染而忘了改解析會當場紅。
#   2. 它依賴 body 沒有被人手改壞。因此**不猜**：定位不到、不唯一、或讀出來的層級
#      不在 MODEL_ROUTING 語彙內，一律歸 ``ambiguous`` 而不是「當作沒有建議」放行。
#   3. 只看 ``## Log`` 之前的區段（``split_at_log``）。Log 會引用被 amend 掉的舊值原文，
#      其中可能含字面的「- 執行：」——不切掉就會把歷史當成現況讀。
#
# 分類是**全函數**：任一 body ＋ 任一合法實際層級，恰好落在下列四格之一，沒有「其餘」。

CAPABILITY_MATCHED = "matched"
CAPABILITY_DEVIATED = "deviated"
CAPABILITY_BASELINE_ABSENT = "absent"
CAPABILITY_BASELINE_AMBIGUOUS = "ambiguous"

CAPABILITY_COMPARISON_OUTCOMES = (
    CAPABILITY_MATCHED,
    CAPABILITY_DEVIATED,
    CAPABILITY_BASELINE_ABSENT,
    CAPABILITY_BASELINE_AMBIGUOUS,
)

# 每一格的理由政策顯式列出，不留 ``else`` 預設值：新增結果態卻忘了決定政策時，
# ``requires_reason`` 會 KeyError 當場炸，而不是靜默沿用「不需要理由」。
#
# 為什麼 absent／ambiguous 也要理由（而不是比照 matched 放行）：這兩格代表**沒有可
# 比對的基線**，不是「比對過且相符」。當作相符放行等於用沉默宣稱一致性，正是本卡要
# 消滅的失敗形態。本檔既有慣例也支持這個方向——assign 對「目標卡自己」的資源宣告
# 解析失敗是 fail closed（見 commands/assign_cmd.py docstring），路由基線同樣長在
# 目標卡自己身上。代價只是操作者多打一個 --capability-deviation-reason。
_REASON_REQUIRED_BY_OUTCOME: dict[str, bool] = {
    CAPABILITY_MATCHED: False,
    CAPABILITY_DEVIATED: True,
    CAPABILITY_BASELINE_ABSENT: True,
    CAPABILITY_BASELINE_AMBIGUOUS: True,
}

# 解析用；與測試裡那支「範本合規 oracle」刻意分開兩份，round-trip 測試才不是套套邏輯。
#
# 理由欄用 ``+`` 而非 ``*``（現行字元類是 ``[^　]+``）：空理由必須讓整行**不匹配**，
# 不能匹配成功後才靠後續檢查補救（R2-001 就是後者漏掉的）。全空白理由 ``+`` 擋不掉，
# 由下方 ``_field_problems`` 的 strip 檢查接手。
#
# 三個字元類與寫入端的保留字元清單**同源**（``ROUTING_NAME_RESERVED``／
# ``ROUTING_REASON_RESERVED``／``ROUTING_TIER_SEPARATORS``），由 ``_char_class``
# 生成而非兩處各手打一份：寫入端禁什麼，讀取端就不把什麼當資料收。這條對稱性正是
# #21 往返缺陷缺的那一半——當時名字段寫成 ``[^（]*``（只擋左括號），寫入端則什麼都不擋。
#
# 兩個方向的改動各自的射程，明列以便查核：
#
#   * 名字段 ``[^（]*`` → ``[^（）；　]*``：**加嚴**。原先名字含 ``）``／``；``／``　``
#     能靠貪婪回溯讀回；現在一律失配。只會 matched → ambiguous，不會反向放行。
#   * 理由段 ``[^）]+`` → ``[^　]+``：**放寬全形括號與全形分號、收緊全形空格**。
#     放寬是為了修 #38 那一類真實個案（理由是中文散文，本來就含全形括號）；
#     它不會造成歧義，因為名字與層級都不含全形空格之後，整行唯一的全形空格就是軸
#     分隔符，``[^　]+`` 的貪婪邊界因此是確定性的、不依賴回溯順序。
#   * 層級段 ``[^；）]+`` → ``[^；　]+``：跟著上一條走（``）`` 不再是理由的邊界）。
#     層級的真正保護是封閉語彙 ``CAPABILITY_TIERS``，由 ``_field_problems`` 查表。
#
# 兩個方向都碰不到永久 absent 的舊卡：解析只在卡面已宣告 ``ROUTING_MARKER`` 時才跑，
# 而那 18 張卡的標頭區沒有標記，在到達本正則之前就已判 absent。


def _char_class(reserved: tuple[str, ...]) -> str:
    """把保留字元清單轉成正規表示式的否定字元類內容（含跳脫）。"""
    return "".join(re.escape(ch) for ch in reserved)


_NAME_CLASS = _char_class(ROUTING_NAME_RESERVED)
_REASON_CLASS = _char_class(ROUTING_REASON_RESERVED)
_TIER_CLASS = _char_class(ROUTING_TIER_SEPARATORS)

_ROUTING_PARSE_RE = re.compile(
    rf"^- 執行：(?P<executor>[^{_NAME_CLASS}]*)（建議 (?P<exec_tier>[^{_TIER_CLASS}]+)；"
    rf"(?P<exec_reason>[^{_REASON_CLASS}]+)）"
    rf"　查核：(?P<reviewer>[^{_NAME_CLASS}]*)（建議 (?P<rev_tier>[^{_TIER_CLASS}]+)；"
    rf"(?P<rev_reason>[^{_REASON_CLASS}]+)）$"
)

def _field_problems(match: re.Match[str]) -> list[str]:
    """匹配成功後的逐欄檢查；回傳所有問題（空清單＝四欄皆合格）。

    層級值先 ``strip`` 再查表——前後空白不帶語意，值本身仍必須落在 MODEL_ROUTING
    語彙內。理由則只要求 strip 後非空：內容是規劃者的判斷，CLI 不評價其品質。
    """
    problems: list[str] = []
    for axis, tier_key, reason_key in (
        ("執行", "exec_tier", "exec_reason"),
        ("查核", "rev_tier", "rev_reason"),
    ):
        tier = match.group(tier_key).strip()
        if tier not in CAPABILITY_TIERS:
            problems.append(
                f"{axis}建議層級 {tier!r} 不在 MODEL_ROUTING.md 語彙 {CAPABILITY_TIERS} 內"
            )
        if not match.group(reason_key).strip():
            problems.append(f"{axis}能力層級理由為空白")
    return problems


# --------------------------------------------------------------------------
# 候選路由行的成員資格（R4-003 → R5-001 重新設計）
# --------------------------------------------------------------------------
#
# **這一段被打穿兩次，兩次是同一個形狀：判準去列舉「什麼算雜訊」。**
#
#   R4-003：候選用 ``startswith("- 執行：")`` 收 → 第二條路由行前置一個 U+200B 就掉出
#           候選集，兩條降成一條，``ambiguous`` 變 ``matched``。
#   R5-001：改成「NFKC 折疊 ＋ 剝除 Cc／Cf／Mn／Me 與空白後比前綴」 → 前置 U+02B0
#           （Lm）或 U+0378（Cn）這種**不在剝除清單裡**的碼位，照樣掉出候選集。
#
# 兩次的修法都是「再多列舉一類字元」。Unicode 的碼位與類別是開放集合，列舉必然還有
# 第六次。問題不在清單不夠長，在**未知輸入被推到危險的那一側**：沒被列舉到的字元讓
# 一行從候選集**消失**，剩下的唯一候選剛好緊鄰標記，於是判 ``matched`` 並免除偏離理由。
#
# 現行設計把承擔未知的那一側翻過來：
#
#   **候選資格 ＝ 「已知非路由行」的補集。**
#
# 標頭區的每一行，只有被**正面辨識**為 ``render_issue_body`` 會產出的某一種已知非路由
# 行（需求／Initiative／DB／服務的原始目標／版本標記／純空白行）時才不算候選；其餘一律
# 是候選，**包括任何我們看不懂的行**。由此得到一條可機械檢查的單調性：
#
#   **往標頭區的任何一行插入任何字元，只能讓它從「已知」掉進「候選」，不能反向。**
#
# 因為「已知」的判準是**原始行**對固定字面前綴的 ``startswith``：插入字元只會破壞前綴
# 比對（→ 變成候選 → 更嚴），不可能憑空造出前綴。同理，往標頭區插入一整行——無論內容
# 是什麼碼位——都是多一個候選 → ``ambiguous``。未知碼位因此天然落在保守側，本檔不再
# 需要任何「哪些字元算雜訊」的清單，也就沒有下一次「再補一類」。
#
# 受理側（候選能否當基線）維持嚴格：一律用**原始行**比對，不套任何正規化。偵測的寬鬆
# 只決定「這行要不要被檢查」，絕不用來幫破損的卡面補正。
#
# **不宣稱窮盡**：本設計保證的是「加字元／加行不會使候選集縮小」（見
# ``tests/test_card.py`` 的單調性與逐位置性質測試）。它**不**保證有人把路由行的內容
# 藏在某個已知前綴後面時一定被算成候選——那一面由下方 ``_carries_routing_shape``
# 這條**非承載性**的額外收緊處理，其漏網只會退回本設計的保證，不會低於它。

# ``render_issue_body`` 標頭區的已知非路由行前綴。這份清單與渲染端同檔並有一致性測試
# （``test_every_generated_header_line_is_positively_classified``）：渲染端新增或改名
# 標頭欄位卻忘了同步這裡，該測試會當場紅；即使沒紅，漏掉的那一行也只會被當成候選路由行
# 而使新卡落 ``ambiguous``——保守側的失敗，不是放行。
_KNOWN_HEADER_PREFIXES = (
    "- 需求：",
    "- Initiative：",
    "- DB：",
    "- 服務的原始目標：",
)


def _carries_routing_shape(line: str) -> bool:
    """（**非承載性**收緊）這行是否把路由行的形狀藏在某個已知前綴後面。

    唯一用途是把「``- DB：…　- 執行：…（建議 …）``」這種借殼行**降級**回候選，
    多產生 ``ambiguous``。它是純粹的加嚴：
    - 漏判（有人把 ``執行：`` 寫成別的形狀）→ 退回 ``_KNOWN_HEADER_PREFIXES`` 補集
      這條承載性保證，不會比它更寬。
    - 誤判（某張卡的 spec 基線真的引用了「執行：」字樣）→ 該卡落 ``ambiguous``，
      派工時多帶一個理由。保守側的雜訊，不是放行。

    因為它只加嚴不放寬，這裡用 NFKC 折疊＋去空白是安全的——即使折不到某種變體，
    後果也只是回到補集判準。
    """
    folded = unicodedata.normalize("NFKC", line)
    return "執行:" in "".join(ch for ch in folded if not ch.isspace())


def _duplicated_known_prefixes(header: list[str]) -> frozenset[str]:
    """標頭區裡出現超過一次的已知前綴。

    渲染端每個標頭欄位恰出現一次，重複即代表結構異常（例如有人刪掉真的 DB 行、另寫
    一行借殼的 DB 行）。重複者一律不再享有「已知非路由行」豁免，全數回到候選集。
    """
    counts: dict[str, int] = {}
    for line in header:
        for prefix in _KNOWN_HEADER_PREFIXES:
            if line.startswith(prefix):
                counts[prefix] = counts.get(prefix, 0) + 1
                break
    return frozenset(prefix for prefix, n in counts.items() if n > 1)


def _is_known_non_routing_header_line(line: str, duplicated: frozenset[str]) -> bool:
    """這行是否被**正面辨識**為已知的非路由標頭行。回 ``False`` 即進候選集。"""
    stripped = line.strip()
    if not stripped:
        return True  # 純空白行不可能承載路由行
    if stripped == ROUTING_MARKER:
        return True
    for prefix in _KNOWN_HEADER_PREFIXES:
        if line.startswith(prefix):
            if prefix in duplicated:
                return False
            return not _carries_routing_shape(line)
    return False


def _routing_line_candidates(header: list[str]) -> list[int]:
    """標頭區裡所有**不能被正面辨識為已知非路由行**的行號（＝候選路由行）。"""
    duplicated = _duplicated_known_prefixes(header)
    return [
        i
        for i, line in enumerate(header)
        if not _is_known_non_routing_header_line(line, duplicated)
    ]


@dataclass(frozen=True)
class CapabilityComparison:
    """實際能力層級與卡面建議的比對結果（四格全函數之一）。"""

    outcome: str
    actual: str
    suggested: str | None  # 只有 matched／deviated 讀得到建議值
    detail: str  # absent／ambiguous 的具體原因；其餘為空字串

    @property
    def requires_reason(self) -> bool:
        return _REASON_REQUIRED_BY_OUTCOME[self.outcome]

    def refusal_message(self) -> str:
        """缺理由時的拒絕訊息；固定引用 MODEL_ROUTING.md 第 14 行後半。"""
        citation = (
            "MODEL_ROUTING.md「路由決定於規劃期」：「派工時可依可用性偏離建議，"
            "但實際模型與偏離理由記入 claim 事件」"
        )
        if self.outcome == CAPABILITY_DEVIATED:
            why = f"實際能力層級 {self.actual} 偏離卡面建議 {self.suggested}"
        elif self.outcome == CAPABILITY_BASELINE_ABSENT:
            why = f"卡面沒有可比對的建議層級（{self.detail}）"
        elif self.outcome == CAPABILITY_BASELINE_AMBIGUOUS:
            why = f"卡面建議層級無法可靠解析（{self.detail}）"
        else:  # pragma: no cover - matched 不會走到這裡（requires_reason 為 False）
            raise ValueError(f"outcome {self.outcome!r} 不需要理由，不該產生拒絕訊息")
        return (
            f"{why}，必須以 --capability-deviation-reason 說明後才可派工——{citation}。"
            "無基線時同樣要求理由：沒有比對過的一致性不得以沉默宣稱"
        )

    def log_fragment(self, reason: str) -> str:
        """寫進 assign／claim 事件 Log 的片段；四格各自措辭，不共用模糊字串。

        關鍵是**不得把「無建議」寫成「偏離建議」**——那會產生不實留痕。
        """
        reason = (reason or "").strip()
        if self.outcome == CAPABILITY_MATCHED:
            base = f"實際能力層級 {self.actual}（與卡面建議 {self.suggested} 相符"
            # 相符時理由非必填；操作者若仍寫了就照錄，不靜默丟棄其輸入。
            return base + (f"；備註：{reason}）" if reason else "）")
        if self.outcome == CAPABILITY_DEVIATED:
            return (
                f"實際能力層級 {self.actual}"
                f"（偏離卡面建議 {self.suggested}；偏離理由：{reason}）"
            )
        if self.outcome == CAPABILITY_BASELINE_ABSENT:
            return (
                f"實際能力層級 {self.actual}"
                f"（卡面無建議層級：{self.detail}；理由：{reason}）"
            )
        if self.outcome == CAPABILITY_BASELINE_AMBIGUOUS:
            return (
                f"實際能力層級 {self.actual}"
                f"（卡面建議無法解析：{self.detail}；理由：{reason}）"
            )
        raise ValueError(f"未知的比對結果 {self.outcome!r}")  # pragma: no cover


def compare_capability_to_card(body: str, actual_capability: str) -> CapabilityComparison:
    """把「實際派到的能力層級」對上「卡面第 4 行的建議執行層級」。

    只比**執行**軸：assign 寫的是 owner（執行者）。查核者的建議層級留在卡面供派查核
    時使用，本函式不碰，以免用一個旗標同時宣稱兩件事。
    """
    if actual_capability not in CAPABILITY_TIERS:
        raise ValueError(capability_tier_violation_message("實際", actual_capability))

    try:
        head, _ = split_at_log(body)
    except AmendError as exc:
        return CapabilityComparison(
            CAPABILITY_BASELINE_AMBIGUOUS,
            actual_capability,
            None,
            f"卡面排版已損壞，無法安全定位 Log 之前的區段（{exc}）",
        )

    # 版本判準是**結構位置**，不是子字串存在性（R4-001）。
    #
    # 前一版寫 ``ROUTING_MARKER in head``，把「出現」當成「宣告」。但 amend 可以把任意
    # 文字寫進 Log 之前——舊卡的驗收條件只要提到這串標記，分類就從 absent 誤升
    # ambiguous。**入口不在使用者手打，在本 CLI 自己的 amend。** 這與 R3-001 是同一個
    # 病的不同層：R3 用內容猜版本，R4 用存在性猜版本；兩次都把「出現」當「宣告」。
    #
    # 宣告的定義收緊為三個結構條件同時成立：
    #   (1) 獨立成行——整行 strip 後恰等於標記，不接受行內出現；
    #   (2) 位於**標頭區**——第一個 ``## `` 標題之前。amend 的驗收／驗證／資源宣告都
    #       寫在 ``## `` 章節內，結構上碰不到標頭區；
    #   (3) **緊鄰**唯一一行合格路由行——標記與它宣告的那一行必須相鄰。
    #
    # 刻意**不做**零寬／格式字元正規化：標記是否成立由位置決定，不受路由行內字元破壞
    # 影響（前綴被 U+200B 打斷的新卡，其標記仍在標頭區且仍相鄰，落 ambiguous 而非
    # absent）。加一層「哪些碼位可剝除」等於再造一個猜測層。
    head_lines = head.splitlines()
    first_heading = next(
        (i for i, ln in enumerate(head_lines) if ln.startswith("## ")), len(head_lines)
    )
    header = head_lines[:first_heading]

    declarations = [i for i, ln in enumerate(header) if ln.strip() == ROUTING_MARKER]
    if not declarations:
        return CapabilityComparison(
            CAPABILITY_BASELINE_ABSENT,
            actual_capability,
            None,
            f"卡面標頭區沒有獨立成行的 {ROUTING_MARKER} 宣告："
            "本卡開立於規劃期路由必填之前",
        )
    if len(declarations) > 1:
        return CapabilityComparison(
            CAPABILITY_BASELINE_AMBIGUOUS,
            actual_capability,
            None,
            f"卡面標頭區有 {len(declarations)} 個 {ROUTING_MARKER} 宣告（應恰為 1）",
        )

    # 以下：卡面**自我宣告**為新制，因此任何讀不出合格建議的情形都是 ambiguous，
    # 不再有「退回當舊卡」這條路——宣告了就要拿得出來。
    # 候選集是「已知非路由行」的**補集**（見 _routing_line_candidates 上方的說明）：
    # 看不懂的行一律算候選，所以加字元／加行只會讓候選變多、判定更嚴。收完先要求
    # 「恰好一條候選」，再要求它緊鄰宣告，最後才用**原始行**嚴格解析。
    candidates = _routing_line_candidates(header)
    if len(candidates) != 1:
        return CapabilityComparison(
            CAPABILITY_BASELINE_AMBIGUOUS,
            actual_capability,
            None,
            f"卡面宣告 {ROUTING_MARKER}，但標頭區的候選路由行有 {len(candidates)} 行"
            "（應恰為 1）——候選＝標頭區裡無法被正面辨識為已知欄位行"
            f"（{'／'.join(_KNOWN_HEADER_PREFIXES)}／版本標記／純空白行）的每一行，"
            "多於一行即無法確定哪一行是規劃期建議",
        )

    routing_index = candidates[0]
    if routing_index != declarations[0] + 1:
        return CapabilityComparison(
            CAPABILITY_BASELINE_AMBIGUOUS,
            actual_capability,
            None,
            f"{ROUTING_MARKER} 宣告在標頭區第 {declarations[0] + 1} 行，但候選路由行在"
            f"第 {routing_index + 1} 行——標記必須緊鄰它所宣告的路由行",
        )

    # 受理側：**原始行**、嚴格比對，不套用任何偵測正規化。偵測的寬鬆只用來決定
    # 「這行要不要被檢查」，絕不用來幫破損的卡面補正。
    match = _ROUTING_PARSE_RE.match(header[routing_index].rstrip())
    if match is None:
        return CapabilityComparison(
            CAPABILITY_BASELINE_AMBIGUOUS,
            actual_capability,
            None,
            "候選路由行不符合 templates/tasks-card.md 第 4 行格式"
            "（如全形／半形空白錯置、缺分號或括號、理由為空、查核段缺失、混入零寬字元）",
        )

    # 匹配成功不等於四欄都合格：層級要在語彙內、理由不得全空白。任一不合格都歸
    # ambiguous——「部分正確的建議」不可當成可信基線，更不可當成相符而免除理由。
    problems = _field_problems(match)
    if problems:
        return CapabilityComparison(
            CAPABILITY_BASELINE_AMBIGUOUS,
            actual_capability,
            None,
            "；".join(problems),
        )

    suggested = match.group("exec_tier").strip()
    outcome = (
        CAPABILITY_MATCHED if suggested == actual_capability else CAPABILITY_DEVIATED
    )
    return CapabilityComparison(outcome, actual_capability, suggested, "")


__all__ = [
    "CAPABILITY_BASELINE_ABSENT",
    "CAPABILITY_BASELINE_AMBIGUOUS",
    "CAPABILITY_COMPARISON_OUTCOMES",
    "CAPABILITY_DEVIATED",
    "CAPABILITY_MATCHED",
    "CAPABILITY_TIERS",
    "CHAIN_DEPTH_HARD_CAP",
    "REQUESTER_GATED_TIERS",
    "ROUTING_MARKER",
    "ROUTING_NAME_RESERVED",
    "ROUTING_REASON_RESERVED",
    "ROUTING_STRUCTURAL_CHARS",
    "ROUTING_TIER_SEPARATORS",
    "TIERS",
    "AmendError",
    "CapabilityComparison",
    "Card",
    "RequesterUnparseable",
    "amend_acceptance",
    "amend_core_pain",
    "amend_initiative",
    "amend_resource_block",
    "amend_spec_baseline",
    "amend_verification",
    "append_log_line",
    "capability_reason_missing_message",
    "capability_tier_violation_message",
    "chain_depth_violation_message",
    "compare_capability_to_card",
    "format_branch_worktree",
    "format_routing_line",
    "is_tier_downgrade",
    "now_iso8601",
    "parse_branch_worktree",
    "parse_requested_by",
    "render_issue_body",
    "render_spec_markdown",
    "routing_reserved_char_message",
    "split_at_log",
    "tier_downgrade_needs_ruling",
    "validate_capability_routing",
    "validate_routing_field",
    "validate_routing_names",
]
