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

import importlib
import inspect
import pkgutil
import re
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, fields
from datetime import datetime

from .brief import BRIEF_SECTION_HEADING_ALIAS as BRIEF_SECTION_HEADING
from .brief import Brief
from .brief import render_block as render_brief_block
from .brief import try_parse_block as try_parse_brief
from .brief import validate_shape as validate_brief_shape
from .card_face import SECTION_HEADING as CARD_FACE_SECTION_HEADING
from .card_face import render_block as render_card_face_block
from .card_face import try_parse_block as try_parse_card_face
from .card_face import validate as validate_card_face
from .resources import (
    CLAIMS_BEGIN_MARKER,
    CLAIMS_END_MARKER,
    SECTION_HEADING_VARIANTS,
    ResourceDeclaration,
    render_block,
)
from .resources import parse_block as parse_resource_block

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
    #: 卡面表單（`WF-REDESIGN-W1` 驗收 3）。⚠️ **可選**——本欄位上線前開的卡一律
    #: 沒有這個區塊，⛔ 不得讓它們因缺區塊而無法 amend 或 handoff（fail-open，
    #: 見 card_face.try_parse_block）。⭐ 但 ``open`` 這條路徑上它是**必填**：
    #: 旗標在 ``commands/open_cmd.py`` 是 required，⇒ 新卡不可能沒有。
    card_face: dict | None = None
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
            # ⚠️ 訊息與 body 讀取端（read_db_scope_agreement）共用同一份，⛔ 不重打。
            raise ValueError(
                db_scope_disagreement_message(self.db_scope, self.resources.db_scope)
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
        if self.card_face is not None:
            # 寫入端拒收的 model 層防線，形狀同上一行的 ``validate_routing_names``：
            # 繞過 CLI 直接建 Card 的路徑（測試／未來呼叫端）同樣不該產出一份
            # 讀得回卻不合 schema 的卡面表單。CLI 層的乾淨訊息由
            # ``commands/open_cmd.py`` 的前置檢查給（零遠端寫入）。
            validate_card_face(self.card_face)
        if self.chain_depth > CHAIN_DEPTH_HARD_CAP:
            # 與 validation.validate_chain_depth 相同的機械紅線，這裡是繞過 CLI
            # 直接建構 Card（測試／未來呼叫端）時的防線；CLI 路徑應該在到達這裡
            # 之前就已經被 validate_chain_depth 攔下並回報 ValidationError。
            raise ValueError(chain_depth_violation_message(self.chain_depth))
        # ⭐ **刻意行為：Card 建構就跑一次寫入邊界守衛，⛔ 不是等到 render 才跑。**
        #
        # (a) 現在的行為：建構一個「渲染出來會讓讀取端讀不回」的 Card 當場失敗。
        # (b) 為什麼在這裡：``templates/handoff-contract.md`` §3.2 規則二要求拒收發生在
        #     **任何遠端寫入之前**。``commands/open_cmd.py`` 的呼叫順序是
        #     ``Card(...)`` → ``resolve_project`` → ``ensure_fields``（會 field-create，
        #     是遠端寫入）→ ``render_issue_body`` → ``create_repo_issue``。⇒ 只掛在
        #     ``render_issue_body`` 上會讓拒收晚於 ``ensure_fields`` 的副作用；掛在這裡
        #     才是「零遠端寫入的拒絕」，與同檔 ``validate_routing_names`` 的防線同構。
        # (c) ⛔ **不得由此推出「render_issue_body 不必再驗」**：Card 是可變的
        #     dataclass，建構後改欄位再 render 完全合法 ⇒ 序列化端必須自己也驗一次。
        #     兩層共用同一份判準函式（§3.2 規則二的參考形狀），⛔ 不得只做一半。
        # (d) ⚠️ **拒收的乾淨化不在這裡**：本例外從這裡拋出後，由 ``commands/open_cmd.py``
        #     包住本建構的 ``except`` 印 ``[open] 拒絕：…`` 回 rc=2；``assign``／``handoff``／
        #     ``review``／``checkpoint`` 走 ``append_log_line`` 那條路徑則由
        #     ``cli.KNOWN_ERRORS`` 收成 ``[wfcli] 錯誤：…`` ＋ rc=2。
        #     ⚠️ **2026-08-27 依查核 R2-06 更正本段**：上一版逐字寫著「並由
        #     ``cli.KNOWN_ERRORS`` 收底」，⛔ 而當時 ``MarkerWriteBoundaryError`` 根本不在
        #     那個 tuple 裡（那四支仍會 traceback／rc=1）——**就地註解宣稱了一個尚未交付
        #     的能力**。今天那一行已補上，本段才成立；⛔ 不得再把「打算做」寫成「已經有」。
        #     ⛔ 也不得由此推出「所以這裡可以自己 print 或 sys.exit」——model 層拋型別、
        #     指令層決定訊息與退出碼，是 §3.2 逐字的參考形狀。
        enforce_card_render_boundary(self)

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
    return f"{ROUTING_MARKER}\n{format_routing_body_line(**routing_values(c))}"


#: 路由行的六個欄位名。⛔ 封閉集合，且**與 ``_ROUTING_PARSE_RE`` 的具名群組同名**——
#: 寫入端與讀取端共用同一組鍵，⛔ 不各寫一份對照表。
ROUTING_FIELDS = (
    "executor",
    "exec_tier",
    "exec_reason",
    "reviewer",
    "rev_tier",
    "rev_reason",
)


def routing_values(c: Card) -> dict[str, str]:
    """把一張卡的路由六欄取成 ``{群組名: 值}``（鍵＝:data:`ROUTING_FIELDS`）。"""
    return {
        "executor": c.executor,
        "exec_tier": c.executor_capability,
        "exec_reason": c.executor_capability_reason,
        "reviewer": c.reviewer,
        "rev_tier": c.reviewer_capability,
        "rev_reason": c.reviewer_capability_reason,
    }


def format_routing_body_line(
    *, executor: str, exec_tier: str, exec_reason: str,
    reviewer: str, rev_tier: str, rev_reason: str,
) -> str:
    """路由行本體（**不含** :data:`ROUTING_MARKER`）。

    ⭐ **從值渲染，⛔ 不從 Card**：``amend --executor`` 這一族旗標改的是既有卡面上的
    那一行，那裡沒有 ``Card`` 物件可拿（重建一個要湊齊十幾個與本次修訂無關的欄位，
    而湊錯任何一個都會靜默寫出不同的卡面）。⇒ 渲染字面只此一份，``open`` 與 ``amend``
    共用它，⛔ 兩處各寫一個 f-string 就會 drift，而範本一致性正是本欄位存在的理由。
    """
    return (
        f"- 執行：{executor}（建議 {exec_tier}；{exec_reason}）"
        f"　查核：{reviewer}（建議 {rev_tier}；{rev_reason}）"
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
    """GitHub Issue／draft item body（含資源宣告 fenced JSON 區塊與 Log 章節）。

    ⭐ **輸出在回傳前先過寫入邊界守衛**（WF-MARKER-WRITE-BOUNDARY1 A5：``open`` 才是
    主破口，14 個旗標裡 9 個寫得出一張永久不可 amend 的卡）。判準見
    :func:`enforce_write_boundary`。
    """
    now = now_iso8601()
    body = _render_issue_body(c, now)
    enforce_card_render_boundary(c, now=now, rendered=body)
    return body


def _render_issue_body(c: Card, now: str) -> str:
    """純範本渲染，⛔ 不含守衛。

    ⭐ **刻意把時戳提成參數，⛔ 不是為了可測性**：守衛要拿「同一張卡、同一個時戳、
    但自由文字只壓掉分行結構」的渲染當差分基線（見 :func:`_line_flattened_card`）。
    時戳若由本函式各自取，兩次渲染會在 Log 行差一個時間，差分就多一個與值無關的變因。
    """
    acceptance = "\n".join(f"- [ ] {line}" for line in c.acceptance)
    verification = "\n".join(f"- [ ] {line}" for line in c.verification)
    resource_block = render_block(c.resources)
    brief_block = f"{render_brief_block(Brief(text=c.brief))}\n\n" if c.brief else ""
    # 卡面表單緊接資源宣告：兩者都是機器可讀區塊，擺在一起讓「這張卡的機讀面」
    # 是一段連續的東西，⛔ 不散在 body 各處。缺表單的舊卡渲染成空字串 ⇒ 版面與
    # 本欄位上線前**逐位元相同**（legacy fallback 的基礎）。
    card_face_block = (
        f"\n{render_card_face_block(c.card_face)}\n" if c.card_face is not None else ""
    )
    return f"""- 需求：{c.requested_by}　規劃：{c.planned_by}
{format_routing_line(c)}
- Initiative：{c.initiative or '—'}　spec 基線：{c.spec_baseline}
- DB：db_scope={c.db_scope}
- 服務的原始目標：{c.service_goal}

{brief_block}## 核心痛點

- **痛點**：{c.core_pain}

{resource_block}
{card_face_block}
## 驗收條件

{acceptance}

## 驗證

{verification}

## Log

- {now} open by {c.planned_by}；owner {c.owner}；iteration {c.iteration}。
"""


_LOG_HEADING = "## Log"


def _append_log_line_raw(body: str, line: str) -> str:
    """純附加，⛔ 不含守衛。

    ⭐ **刻意與 :func:`append_log_line` 分開，⛔ 不是為了可測性**：
    (a) 現在的行為：本函式無條件附加，任何值都寫得出去。
    (b) 為什麼：守衛要拿「同一次附加、但值只被壓掉**自身**分行結構」的 body 當差分
        基線（與 :func:`_line_flattened_card` 對 ``open`` 做的事同構）。基線與候選只差
        在值的分行結構，差分才只歸因到那件事，⛔ 不會把「附加動作本身」算成破壞。
    (c) ⛔ **不得由此推出「這是可以直接用的附加函式」**：模組外的呼叫端一律走
        :func:`append_log_line`。本函式無守衛，直接用等於把 P0 的破口原樣搬回來。
    """
    entry = f"- {line}"
    if _LOG_HEADING in body:
        return body.rstrip("\n") + f"\n{entry}\n"
    return body.rstrip("\n") + f"\n\n{_LOG_HEADING}\n\n{entry}\n"


def _read_appended_log_entry(body: str, line_count: int) -> str:
    """讀回 ``## Log`` 區段末端 ``line_count`` 個**讀取端所見的行**，以 ``\\n`` 重組。

    ⭐ **這是性質 (2) 對 Log 行的讀回器，⛔ 不是另寫一份解析**：切段重用
    :func:`split_at_log`（body 已壞時它 fail closed 直接拋），切行重用 ``str.splitlines()``
    ——那正是**每一條**讀取路徑看「行」的方式。⇒ 「寫進去的那一段」與「讀取端看得到的
    那幾行」之間只要有任何不一致，就會在呼叫端的 ``!=`` 上現形。

    ⚠️ **刻意不採用事件層讀回器（``doctor.parse_log_events``），⛔ 不是沒想到**：
    (a) 現在的行為：本函式在**行**的層次比對，⛔ 不在事件層。
    (b) 為什麼：``doctor`` 的可達性探針逐字呼叫 ``append_log_line(body, f"- {TOKEN}")``
        ——那個值沒有時戳，事件層讀回器會判「寫了一筆、讀回零筆」而拒收，於是**每一張
        卡**都被報成 append-only 動詞不可達；同一個讀回器也會退回合法的多段落
        ``--evidence``，因為續行是 ``parse_log_events`` 明文支援的形狀。
    (c) ⛔ **不得由此推出「事件層的往返有保證」**——沒有。已登記的未涵蓋類別見
        :func:`append_log_line` 末段。
    """
    _, log_section = split_at_log(body)
    lines = log_section.splitlines()
    if line_count <= 0 or len(lines) < line_count:
        raise AmendError(
            f"`## Log` 區段只有 {len(lines)} 行，讀不回剛附加的 {line_count} 行"
        )
    return "\n".join(lines[len(lines) - line_count :])


def append_log_line(body: str, line: str) -> str:
    """在 body 的 ``## Log`` 區段末端附加一行；沒有該區段就新增一個到 body 尾端。

    這是 Issue／draft item body 版的 append-only 留痕，對齊
    ``templates/tasks-card.md`` 既有 Log 慣例（不可覆寫歷史，只能加行）。

    ⭐ **輸出在回傳前先過寫入邊界守衛的兩條性質**（WF-MARKER-WRITE-BOUNDARY1 A9，
    2026-08-27 依查核 R1-01／R1-02 補上）。⚠️ 為什麼它非在這裡不可：
    ``assign``／``handoff``／``review``／``checkpoint`` 四支動詞把使用者提供的自由文字
    **原樣**交給本函式（⛔ 四支都沒有 ``amend_cmd`` 的 ``_fold``），實測注入一個 U+2028
    即可讓卡面長出第二個 ``## Log``，``split_at_log`` 與 ``parse_requested_by`` 兩條讀取
    路徑當場失效 ⇒ 那張卡**永久失去 wfcli 可修改性**——那就是本卡的核心痛點本身。

    ⛔ **不得改成「把值摺平後寫入」**（``amend_cmd._fold`` 那種 ``" ".join(text.split())``）：
    ``templates/handoff-contract.md`` §3.2 規則二逐字禁止「以正規化代替拒收」。摺平會
    靜默改變值，其危害與寫得出讀不回同級。

    ⭐ **事件層偽造由性質 (3) 擋（2026-08-27 依查核 R2-01 補上）**，⛔ 不是靠禁 ``\\n``：
    (a) 現在的行為：普通 ``\\n`` **仍然寫得進去**（多段落續行是 ``doctor.parse_log_events``
        明文支援的形狀，``handoff --evidence`` 的多段落證據靠它）；被擋的是「同一次附加
        在事件層被讀成的那組事件，與它不帶分行結構時被讀成的那組不同」。
    (b) 為什麼判準是事件層的導出量而不是字元：禁 ``\\n`` 會擋掉合法的多段落證據，那是
        以拒收代替設計；而事件由**真正的讀取端**（``parse_log_events``）自己切 ⇒ 零列舉、
        ⛔ 不定義字元、⛔ 不定義 marker。實測：一次 ``handoff`` 被解析成 ``open``／
        ``handoff``／偽造 ``APPROVE`` 共 3 筆，而合法多段落仍只增加一筆。
    (c) ⛔ **不得由此推出「事件的語意可信」**——本條比對的是那組事件在「有／無分行結構」
        兩種寫法下是否相同，⛔ 不判斷任何一筆事件說的是不是真的。詳見
        :func:`_log_event_signature` 的三段說明（含「只比筆數會漏」的窮舉反例）。
    """
    entry = f"- {line}"
    candidate = _append_log_line_raw(body, line)
    # 基線：同一次附加，但值只被壓掉自身的分行結構（⇒ 差分只歸因到那件事）。
    baseline_entry = f"- {_flatten_line_structure(line)}"
    baseline = _append_log_line_raw(body, _flatten_line_structure(line))
    reader = lambda b: _read_appended_log_entry(b, len(entry.splitlines()))  # noqa: E731

    # ⭐ **往返比對先過一道「寫入前讀得回嗎」的閘門，⛔ 不是無條件套用**：
    # (a) 現在的行為：基線上讀不回（＝這張卡在本次寫入**之前**就已經壞了）時，跳過
    #     性質 (2)，只留性質 (1)。
    # (b) 為什麼：差分探測逐字是「寫入前讀得回、寫入後讀不回 ⇒ 拒收」——**只罰迴歸、
    #     ⛔ 不罰既有損壞**。往返比對若無條件套用，就會對每一張既有損壞的卡（例如
    #     `aiwf#15`）連 ``handoff``／``review`` 的合法留痕都拒收，把守衛變成故障源；
    #     而「修好已壞的卡」逐字是本卡的非射程。
    # (c) ⛔ **不得由此推出「那些卡受保護」**——它們不受保護，見卡面 V4 的預壞控制組。
    checks: list[tuple[str, object, Callable[[str], object]]] = []
    try:
        if _read_appended_log_entry(baseline, len(baseline_entry.splitlines())) == baseline_entry:
            checks.append((f"`{_LOG_HEADING}` 附加行", entry, reader))
    except Exception:  # noqa: BLE001 - 寫入前就讀不回 ⇒ 依 (b) 跳過性質 (2)
        pass

    enforce_write_boundary(
        baseline,
        candidate,
        roundtrip=checks,
        invariants=[
            (f"`{_LOG_HEADING}` 的 lifecycle 事件（逐筆、摺平後）", _log_event_signature)
        ],
        where=f"`{_LOG_HEADING}` 附加行",
    )
    return candidate


def _log_event_signature(body: str) -> tuple[str, ...]:
    """性質 (3) 對 Log 的導出量：``## Log`` 的 lifecycle 事件**逐筆、各自摺平**。

    ⭐ **走 ``doctor.parse_log_events`` 這條真正的讀取路徑，⛔ 不另寫一份事件切分**
    （§3.2 規則三逐字：「解析側須走真正會跑的那條路徑」）。它就是把偽造 ``APPROVE``
    讀成一筆真事件的那個消費者，⇒ 判準必須由它自己導出。

    ⭐ **為什麼是「逐筆內容」而不只是「筆數」**（⛔ 這一格我先寫錯過，就地留證）：
    (a) 現在的行為：回傳每一筆事件**摺掉自身分行結構**後的字串序列。
    (b) 為什麼：只比筆數會漏。實跑窮舉 2,520 個 payload 組合，其中 1,680 個「筆數相等」，
        而**其中 20 個內容不同**——最短的反例是值以一個分行字元開頭：
        ``sep + "<ts> handoff …" + sep + "- <ts> review … APPROVE"``。摺平後的基線是
        **一筆 handoff**，候選卻是**一筆偽造的 APPROVE**，兩邊都是「+1 筆」⇒ 筆數檢查
        對它完全沉默。⇒ 「內容比對是筆數的重述」是**假的**，我原本那麼寫是錯的。
    (c) ⛔ **不得改成比對「未摺平」的事件內容**：合法的多段落 ``--evidence`` 會讓最後一筆
        事件在基線（已摺平）與候選（帶續行）之間逐位元不同，未摺平的比對會退回它。
        摺平**只作用在比對上**，⛔ 不改寫任何寫進去的值（§3.2 規則二禁止的是後者）。

    ⚠️ **不判定一律拋，⛔ 不回空序列**：``parse_log_events`` 的不判定是 fail-soft 的
    ``(None, 原因)``，⛔ **不拋例外** ⇒ 性質 (1) 的 ``_reads_back``（只認例外）對它
    **結構性看不見**。轉成例外之後，「寫入前導得出、寫入後不判定」才會落在
    :func:`enforce_write_boundary` 的拒收側；回空序列會讓「不判定」與「真的零筆」撞在
    同一個值上，那是把兩件事讀成一件。

    ⚠️ **刻意延遲 import**：``wf_cli.doctor`` 反向 import 本模組，模組載入期會迴圈。
    本函式只在寫入動詞執行期被呼叫，此時兩邊都已載入完成。
    """
    from .doctor import parse_log_events

    events, undecidable = parse_log_events(body)
    if undecidable is not None or events is None:
        raise AmendError(f"事件層不判定（{undecidable}）")
    return tuple(_flatten_line_structure(event) for event in events)


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


# ==========================================================================
# 寫入邊界守衛（WF-MARKER-WRITE-BOUNDARY1）
# ==========================================================================
#
# 規範依據：``templates/handoff-contract.md`` §3.2，其機械形式逐字為
# 「**序列化成功 ⟹ 解析成功，且回傳逐字相同的值。**」本段是該句在卡面 body 上的
# 機械執行者（§3.2 末段要求每個格式「指名自己的執行者所在的檔與行」——就是這裡）。
#
# ⭐ **判準只有兩條性質，⛔ 零列舉**：
#
#   (1) **差分結構探測**：同一組讀取路徑在寫入前後各跑一次。寫入前讀得回、寫入後
#       讀不回 ⇒ 拒收。
#   (2) **值往返逐位元比對**：讀取端讀回的值必須 ``==`` 寫進去的值。
#
# ⭐ **兩條必須並用，⛔ 缺一不可**（各自抓不到對方那類）：
#
#   * 結構破壞（例：值裡的分行字元讓 ``## Log`` 多長出一個）——(1) 抓得到，
#     (2) 也常抓得到但不保證。
#   * **靜默截斷**（例：``--brief`` 的值行內提及 ``<!-- card-brief:end -->``，
#     寫 56 字讀回 23 字、⛔ 全程無錯誤）——(1) **抓 0**（每條讀取路徑都照樣讀得回，
#     只是讀回的東西變短了），只有 (2) 抓得到。
#
# ⛔ **本段刻意不定義「marker」、不定義「分界字元」、不定義「哪些案子算違規」。**
# 那三樣都是開放集合，本 repo 已在讀取端被同一個形狀打穿三次（R3-001／R4-001／
# R1-02，見 ``_routing_line_candidates`` 上方那段）。分行字元的涵蓋範圍由
# ``str.splitlines()`` **自身**導出——因為讀取路徑本來就是用它切行的，⛔ 不另存一份
# 字元清單，也就沒有「下一次再補一類」。
#
# ⚠️ **涵蓋宣稱的界線（⛔ 不得放大）**：
#
#   * 本守衛涵蓋的是 :func:`body_read_paths` **當次導出命中的那組讀取路徑**，
#     ⛔ **不宣稱涵蓋全部讀取端**。導出結果對偵測條件敏感（放寬條件會使命中數變動），
#     故清單由程式導出、⛔ 不手打。
#   * 兩條性質是**單欄位**性質。⛔ **不涵蓋跨欄位不變量**——即「每個欄位各自都讀得回，
#     但欄位之間的自洽檢查在讀取端退回它」那一類（§3.2 逐字舉的實例：``v2`` marker
#     的 ``card_id`` 字母集允許尾綴 ``-``，而 ``event=review`` 的三欄自洽檢查會退回）。
#     該類須另有承接者，見卡面 V7。


_READ_PATHS: tuple[tuple[str, Callable[[str], object]], ...] | None = None


class MarkerWriteBoundaryError(AmendError):
    """寫入邊界拒收：值寫得進去，但寫進去之後讀取端讀不回來。

    ⭐ **刻意獨立成一個型別，⛔ 不只是為了分類**：``commands/amend_cmd.py`` 的
    ``_is_layout_failure`` 以**訊息字面**判斷「body 排版已損壞」，而本例外的訊息
    必然轉述讀取端的原始錯誤（其中就含 ``個 `## Log` 標題`` 這串字面）⇒ 純字面判斷
    會把「卡面完好、是你送進來的值有問題」誤印成教人去 ``gh issue edit`` 手修 body 的
    runbook。⇒ 該處改以**型別**先行排除本例外（見 ``amend_cmd._is_layout_failure``）。
    ⛔ **不得改用「避開那兩串字面」的措辭來繞過**——那是把型別問題藏進文案，下一個
    改訊息的人會再踩一次。
    """


def body_read_paths() -> tuple[tuple[str, Callable[[str], object]], ...]:
    """導出本進程可見的**卡面讀取路徑**集合（(限定名, 函式) 依名排序）。

    ⭐ **這是偵測器的定義，⛔ 不是一份手打清單。** 命中條件逐字為：``wf_cli`` 套件內、
    模組層級定義（``fn.__module__`` 等於該模組本身，排除 re-export）、第一個參數名為
    ``body``、且其餘參數**全部有預設值或是 ``*args``／``**kwargs``**（＝可以只餵一個
    body 呼叫）的函式。

    ⚠️ **對偵測條件敏感是已知性質，⛔ 不是缺陷**：放寬或收緊條件會讓命中集變動。
    正因如此，任何涵蓋宣稱都必須寫成「本函式當次導出的那組」，⛔ 不得寫成「全部讀取端」。
    測試對本函式的輸出做的是**性質檢查**（幾個必須在裡面的成員），⛔ 不是逐字釘死整份
    清單——釘死等於把「清單」偷渡回來。

    ⚠️ **刻意延遲導出並快取**：``wf_cli.commands.*`` 反向 import 本模組，模組載入期
    走訪會迴圈。第一次呼叫必然發生在寫入動詞執行期，此時本模組已完成載入。
    """
    global _READ_PATHS
    if _READ_PATHS is not None:
        return _READ_PATHS
    # ⚠️ **``__package__`` 的靜態型別是 ``str | None``，本行刻意不加 None 分支**
    # （IDE 診斷 ``reportArgumentType``，⛔ 非 CI；本 repo 的 required check 只有 ``tests``）：
    # (a) 現在的行為：直接把 ``__package__`` 餵給 ``import_module``。
    # (b) 為什麼：本模組是 ``wf_cli`` **套件內**的模組，``__package__`` 在構造上恆為
    #     ``"wf_cli"``；``None`` 只出現在頂層腳本（``__name__ == "__main__"`` 且非 ``-m``），
    #     而本函式只在寫入動詞執行期被呼叫，那時本模組必然是被 import 進來的。
    # (c) ⛔ **不得為了讓 linter 閉嘴而加一個永不執行的 fallback 分支**——那會製造一段
    #     沒有任何測試走得到的碼，正是本 repo 已經登記過的「零資訊」形狀。真要動，
    #     正解是讓型別檢查器認得這個前提（``assert``／``cast``），⛔ 不是新增行為分支。
    package = importlib.import_module(__package__)
    found: list[tuple[str, Callable[[str], object]]] = []
    for info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        module = _import_or_none(info.name)
        if module is None:
            continue
        for name, fn in vars(module).items():
            if not inspect.isfunction(fn) or fn.__module__ != module.__name__:
                continue
            params = list(inspect.signature(fn).parameters.values())
            if not params or params[0].name != "body":
                continue
            if any(
                p.default is inspect.Parameter.empty
                and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
                for p in params[1:]
            ):
                continue
            found.append((f"{module.__name__}.{name}", fn))
    _READ_PATHS = tuple(sorted(found, key=lambda pair: pair[0]))
    return _READ_PATHS


def _import_or_none(name: str):
    """匯入失敗的模組**不該讓寫入動詞掛掉**——導出少一條讀取路徑只是涵蓋變窄，
    ⛔ 而讓 ``open``／``amend`` 因為某個無關模組壞掉就整個不能用，是把守衛變成故障源。
    """
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def _reads_back(fn: Callable[[str], object], body: str) -> Exception | None:
    """跑一次讀取路徑；回傳 ``None`` 代表讀得回，回傳例外代表讀不回。

    「讀得回」的定義刻意寬到只有一條：**沒有拋例外**。回傳 ``None``／空值都算讀得回
    ——那是讀取路徑自己的 fail-open 設計（例如 ``brief.try_parse_block``），⛔ 本守衛
    不代它判斷，否則就變成第二個猜測層。值層面的損失由性質 (2) 負責。
    """
    try:
        fn(body)
    except Exception as exc:  # 任何例外都算「讀不回」
        return exc
    return None


def _clip(value: object, limit: int = 160) -> str:
    text = repr(value)
    return text if len(text) <= limit else f"{text[:limit]}…（全長 {len(text)}）"


def enforce_write_boundary(
    baseline: str,
    candidate: str,
    *,
    roundtrip: Sequence[tuple[str, object, Callable[[str], object]]] = (),
    invariants: Sequence[tuple[str, Callable[[str], object]]] = (),
    where: str,
) -> None:
    """A1 的兩條性質＋性質 (3) 導出量差分。任一不成立即
    :class:`MarkerWriteBoundaryError`，⛔ 不做正規化。

    ``baseline`` 是「同一次寫入、但值不帶分行結構」的那個 body：``amend`` 用寫入前的原
    body，``open`` 用 :func:`_line_flattened_card` 的渲染。⭐ 兩者的共同性質是**與這次
    寫入的值無關**，差分因此只歸因到值。

    ``invariants`` 是**性質 (3)**（2026-08-27 依查核 R2-01 補上）：每一項是
    ``(標籤, 導出函式)``，要求 ``導出函式(baseline) == 導出函式(candidate)``。

    ⭐ **為什麼它不能由性質 (1)／(2) 涵蓋，⛔ 不是重複**：
    (a) 現在的行為：性質 (1) 只問「讀取路徑有沒有拋例外」、性質 (2) 只問「這個欄位的值
        逐位元讀得回嗎」。兩者都在**行**的層次。
    (b) 為什麼需要第三條：一個讀取端可以**不拋例外、也不改任何單一欄位的值**，卻把同
        一次寫入解讀成**更多筆語意單位**——``doctor.parse_log_events`` 對含普通 ``\\n``
        的 Log 值就是如此（實測：一次 ``handoff`` 被解析成 ``open``／``handoff``／偽造
        ``APPROVE`` 共 3 筆）。⇒ 那是**事件層**的偽造，行層兩條性質對它結構性沉默。
    (c) ⛔ **不得由此推出「導出量相等 ⇒ 那些事件說的是真的」**：本條只問「同一次寫入在
        帶／不帶分行結構兩種寫法下，導出量是否相同」，⛔ 不判斷任何一筆事件的語意。
        ⚠️ 導出量**必須對值自身的分行結構不敏感**（例如事件層那條先逐筆摺平再比），
        否則合法的多段落 ``--evidence`` 會被退回——那是本機制唯一的偽陽性來源。

    ⛔ **不得改成「把值正規化後寫入」**：§3.2 規則二逐字禁止以正規化代替拒收
    （把換行摺成空白、把連續空白壓成一個都是靜默改變值，其危害與寫得出讀不回同級）。
    """
    broken: list[tuple[str, Exception]] = []
    for name, fn in body_read_paths():
        if _reads_back(fn, baseline) is not None:
            continue
        exc = _reads_back(fn, candidate)
        if exc is not None:
            broken.append((name, exc))
    if broken:
        # ⭐ **列出全部失敗的讀取路徑，⛔ 不只第一個**：導出集合依名排序，只報第一個
        # 會挑到字母序最前的那條（實測是本檔自己的私有 helper），對被擋的人幾乎沒有
        # 資訊。⛔ 不得為了訊息短而改回只報一條。
        names = "、".join(f"`{n}`" for n, _ in broken)
        raise MarkerWriteBoundaryError(
            f"寫入邊界拒收（未寫入任何狀態）：{where}的值寫進去之後，下列 {len(broken)} "
            f"條讀取路徑就讀不回卡面了（寫入前都讀得回）：{names}。"
            f"首個失敗原因：{broken[0][1]}。"
            "⇒ 兩種可能：值裡含有會改變卡面結構的內容（任何 `str.splitlines()` 認得的"
            "分行字元、或會讓某個區段標題／哨兵獨立成行的片段都屬之），"
            "或值本身與卡面另一個欄位互相矛盾（跨欄位不變量）。⚠️ 上面那個原因就寫著是哪一種。"
            "⚠️ 卡面本身沒有損壞、本次也未改動它；請改寫該值後重試。"
        )
    for label, written, reader in roundtrip:
        try:
            got = reader(candidate)
        except Exception as exc:  # 讀不回同樣是往返失敗
            raise MarkerWriteBoundaryError(
                f"寫入邊界拒收（未寫入任何狀態）：{where}的「{label}」寫進去之後讀不回來"
                f"（讀取端錯誤：{exc}）。⚠️ 卡面本身沒有損壞、本次也未改動它。"
            ) from exc
        if got != written:
            raise MarkerWriteBoundaryError(
                f"寫入邊界拒收（未寫入任何狀態）：{where}的「{label}」寫入值與讀回值不同"
                f"——寫入 {_clip(written)}，讀回 {_clip(got)}。"
                "⇒ 值的一部分被卡面結構吃掉了（靜默截斷），寫入端不得接受一個自己讀不回的值。"
                "⚠️ 卡面本身沒有損壞、本次也未改動它；請改寫該值後重試。"
            )
    for label, derive in invariants:
        try:
            expected = derive(baseline)
        except Exception:  # noqa: BLE001 - 寫入前就導不出 ⇒ 只罰迴歸、⛔ 不罰既有損壞
            continue
        try:
            got = derive(candidate)
        except Exception as exc:  # 寫入前導得出、寫入後導不出 ⇒ 本次寫入弄壞了它
            raise MarkerWriteBoundaryError(
                f"寫入邊界拒收（未寫入任何狀態）：{where}的值寫進去之後，"
                f"「{label}」就導不出來了（讀取端錯誤：{exc}）。"
                "⚠️ 卡面本身沒有損壞、本次也未改動它；請改寫該值後重試。"
            ) from exc
        if got != expected:
            raise MarkerWriteBoundaryError(
                f"寫入邊界拒收（未寫入任何狀態）：{where}的值改變了「{label}」"
                f"——寫入前 {_clip(expected)}，寫入後 {_clip(got)}。"
                "⇒ 這一次寫入在讀取端被解讀成**不只一件事**（同一段值被切成多筆語意單位），"
                "而讀取端在結構上分不出哪一筆是產生器寫的、哪一筆是值裡帶進來的。"
                "⚠️ 卡面本身沒有損壞、本次也未改動它；請改寫該值後重試。"
            )


# --------------------------------------------------------------------------
# 往返比對用的讀取端（性質 (2)）
# --------------------------------------------------------------------------
#
# ⭐ 這些讀回器**重用本檔既有的定位謂詞**（``_REQUESTED_BY_RE``／``_SPEC_BASELINE_RE``／
# ``_CORE_PAIN_RE``／``_locate_section``／``_read_checklist``／``try_parse_brief``），
# ⛔ 不另寫一份解析。理由是 R1-01 的教訓逐字：「每個新呼叫端都自己重寫一份謂詞」是本檔
# 已經犯過的形狀；§3.2 規則三也逐字要求「解析側須走真正會跑的那條路徑」。


def _head_lines(body: str) -> list[str]:
    return split_at_log(body)[0].splitlines()


def _sole_match(body: str, pattern: re.Pattern[str]) -> re.Match[str] | None:
    hits = [m for m in (pattern.match(line) for line in _head_lines(body)) if m]
    return hits[0] if len(hits) == 1 else None


def _read_requested(body: str) -> str | None:
    m = _sole_match(body, _REQUESTED_BY_RE)
    return m.group("requested") if m else None


def _read_planned(body: str) -> str | None:
    m = _sole_match(body, _REQUESTED_BY_RE)
    return m.group("planned") if m else None


def _read_initiative(body: str) -> str | None:
    m = _sole_match(body, _SPEC_BASELINE_RE)
    return m.group("init") if m else None


def _read_spec_baseline(body: str) -> str | None:
    m = _sole_match(body, _SPEC_BASELINE_RE)
    return m.group("base") if m else None


def _read_prefixed_header(body: str, prefix: str) -> str | None:
    hits = [line[len(prefix):] for line in _head_lines(body) if line.startswith(prefix)]
    return hits[0] if len(hits) == 1 else None


_DB_HEADER_PREFIX = "- DB："
_DB_SCOPE_KEY = "db_scope="


def db_scope_disagreement_message(header_scope: str, declared_scope: str) -> str:
    """標頭行與資源宣告 JSON 對 ``db_scope`` 各說各話時的拒絕訊息。

    ``Card.__post_init__``（model 層）與 :func:`read_db_scope_agreement`（body 讀取端）
    共用同一段文字，⛔ 兩處措辭不得各自漂移——那正是本 repo 已經犯過的形狀。
    """
    return (
        "db_scope 與資源宣告內的 db_scope 不一致："
        f"{header_scope!r} vs {declared_scope!r}"
    )


def read_db_scope_agreement(body: str) -> str:
    """**跨欄位不變量的讀取端**：``- DB：db_scope=…`` 標頭行與資源宣告 JSON 必須同值。

    ⭐ **刻意做成一條 body 讀取路徑，⛔ 不是在某個 amend 函式裡加一段檢查**
    （2026-08-27 依需求方裁定甲案，R2-04／V7(c)）：
    (a) 現在的行為：本函式簽章是 ``(body) -> str`` ⇒ :func:`body_read_paths` 的導出
        條件當場命中它，於是**每一個**走 :func:`enforce_write_boundary` 的寫入點
        （``open`` 渲染、每一支 ``amend``、``## Log`` 附加）自動套上性質 (1) 的差分。
    (b) 為什麼是結構性而非逐點：逐點加檢查的缺陷形態是「某個呼叫端沒加」——那是本卡
        核心痛點的同一族（「三次都是逐個 marker、在讀取端修」）。做成讀取路徑，
        新增寫入點的人**忘不掉**。
    (c) ⛔ **不得由此推出「跨欄位不變量已全面涵蓋」**：本函式只涵蓋 ``db_scope`` 這一
        對載體——那是今日**本 repo 唯一能以碼重現**的同平面跨欄位反例。另兩個反例
        （``card_id`` 尾綴、Project「簡介」欄 vs body 簡介區塊）逐字登記於
        ``tests/test_marker_write_boundary.py`` 的「V7 跨欄位／跨平面」一節，含各自
        「今日無實例」或「本平面看不到」的量法。

    ⚠️ 讀不回（缺標頭行、資源宣告解析不了）一律拋：那讓「寫入前就讀不回」的卡落進
    差分探測的跳過側（只罰迴歸、⛔ 不罰既有損壞），⛔ 而不是被當成「一致」放行。
    """
    header = _read_prefixed_header(body, _DB_HEADER_PREFIX)
    if header is None or not header.startswith(_DB_SCOPE_KEY):
        # ⚠️ **訊息要說出實際命中幾次，⛔ 不要只寫「不是恰好 1 次」**（2026-08-27 依
        # 對抗式複驗 F8）：本 repo 上這條路徑**絕大多數是 0 次**（遷移期卡沒有這一行），
        # 而「不是恰好 1 次」讀起來像「有好幾行互相打架」⇒ 措辭把「這張卡只有一個載體」
        # 誤導成「這張卡壞了」。⛔ 不得改回不帶計數的措辭。
        hits = sum(
            1
            for line in _head_lines(body)
            if line.startswith(_DB_HEADER_PREFIX + _DB_SCOPE_KEY)
        )
        raise AmendError(
            f"`{_DB_HEADER_PREFIX}{_DB_SCOPE_KEY}…` 這一行在 Log 之前命中 {hits} 次，"
            "必須恰好 1 次才有「兩個載體」可比"
            + ("（這張卡只有資源宣告一個載體 ⇒ 跨欄位不變量對它不適用）" if hits == 0 else "")
        )
    header_scope = header[len(_DB_SCOPE_KEY):].strip()
    declared_scope = parse_resource_block(body).db_scope
    if header_scope != declared_scope:
        raise AmendError(db_scope_disagreement_message(header_scope, declared_scope))
    return header_scope


def _read_routing_group(body: str, group: str) -> str | None:
    m = _sole_match(body, _ROUTING_PARSE_RE)
    return m.group(group) if m else None


def _read_core_pain(body: str) -> str | None:
    lines = _head_lines(body)
    try:
        start, end = _locate_section(lines, _CORE_PAIN_HEADING)
    except AmendError:
        return None
    hits = [m for m in (_CORE_PAIN_RE.match(lines[i].strip()) for i in range(start + 1, end)) if m]
    return hits[0].group("pain") if len(hits) == 1 else None


def _read_checklist_texts(body: str, heading: str) -> list[str] | None:
    lines = _head_lines(body)
    try:
        start, end = _locate_section(lines, heading)
    except AmendError:
        return None
    return [text for _, text in _read_checklist(lines[start + 1 : end])]


def _read_brief_text(body: str) -> str | None:
    parsed = try_parse_brief(body)
    return parsed.text if parsed else None


def _flatten_line_structure(value: str) -> str:
    """把一個值**自身的分行結構**壓平，其餘逐字保留。

    ⭐ 涵蓋範圍由 ``str.splitlines()`` **自身**導出（A8）：⛔ 這裡沒有任何字元清單，
    也就沒有「下一次再補一類」。CRLF 這種雙字元序列同樣由 ``splitlines`` 處理。
    """
    return "".join(value.splitlines())


def _line_flattened_card(c: Card) -> Card:
    """同一張卡，但每個自由文字欄位**只**被壓掉自身的分行結構。

    ⭐ **為什麼基線是「壓平」而不是「換成惰性 token」**（這一格踩過一次，就地留證）：
    最初的寫法是把所有字串換成固定 token，結果 ``parse_requested_by`` 對 token
    ``'WFINERT'`` 讀得回、對真實預設值 ``'—'`` 卻**依設計** fail closed（它拒絕佔位身分）
    ⇒ 差分把一個**語意**拒絕誤判成結構破壞，每一張沒填需求方的新卡都會被擋。
    ⇒ 基線必須與候選**只差在分行結構**，語意逐字相同，差分才只歸因到結構。

    ⛔ 刻意用 ``object.__new__`` 繞過 ``__post_init__``：本複本只是渲染基線、⛔ 從不
    寫出去，而再跑一次驗證會遞迴回本守衛。
    ⛔ 也刻意**不列舉欄位名**——欄位由 ``dataclasses.fields`` 導出。新增欄位自動納入基線，
    ⛔ 不需要有人記得回來改這裡。
    ⚠️ ``None`` 保留 ``None``：``brief``／``initiative`` 為 ``None`` 時範本渲染的結構本來
    就不同，換成字串會讓基線與候選在**與值無關**的地方分岔。

    ⚠️ **已知界線，⛔ 不得放大宣稱**：本基線抓的是「值自身的分行結構」造成的破壞。
    一個**不含任何分行字元**卻仍獨立成行的值（例如 ``--brief`` 的整個值就是 ``## Log``，
    由哨兵區塊把它放到自己那一行）在基線與候選中形狀相同 ⇒ 性質 (1) 抓 0，
    改由性質 (2) 抓（實測 ``try_parse_brief`` 讀回 ``None`` ≠ 寫入值）。⇒ 兩條並用不是修辭。
    """
    clone = object.__new__(Card)
    clone.__dict__.update(vars(c))
    for f in fields(Card):
        value = getattr(clone, f.name)
        if isinstance(value, str):
            setattr(clone, f.name, _flatten_line_structure(value))
        elif isinstance(value, list):
            setattr(
                clone,
                f.name,
                [_flatten_line_structure(v) if isinstance(v, str) else v for v in value],
            )
    decl = object.__new__(ResourceDeclaration)
    decl.__dict__.update(vars(c.resources))
    decl.db_scope = _flatten_line_structure(c.resources.db_scope)
    decl.resources = [_flatten_line_structure(r) for r in c.resources.resources]
    clone.resources = decl
    return clone


def enforce_card_render_boundary(
    c: Card, *, now: str | None = None, rendered: str | None = None
) -> None:
    """對 ``render_issue_body`` 的輸出套用兩條性質（A5：``open`` 是主破口）。

    ``now``／``rendered`` 可注入，是為了讓 :func:`render_issue_body` 不必渲染兩次、
    且基線與候選共用同一個時戳（見 :func:`_render_issue_body`）。

    ⚠️ **名字用 ``enforce_`` 不用 ``validate_`` 是刻意的，且有一個必須揭露的副作用**：
    (a) 語意上它與 :func:`enforce_write_boundary` 同族——渲染、差分、往返比對，⛔ 不是
        同檔 ``validate_routing_field`` 那種純謂詞。
    (b) ⚠️ **副作用（⛔ 不得當成沒有）**：``scripts/contract_tool_reconcile.py`` 以
        ``^_?(validate|check|verify|find_conflicts|assert)`` 認「守衛」，⇒ 叫
        ``validate_*`` 會讓「守衛覆蓋缺口」表中 ``assign_cmd→card`` 那一列的
        **未跑的守衛**欄多出本函式，使 ``--check`` 判 rc=1，而該處置登記在
        ``docs/CONTRACT_TOOL_RECONCILE.md``——**本卡未宣告該檔**（A10）。
    (c) ⛔ **不得由此推出「本函式不是守衛」**：它是。上面那條只說明命名選擇同時避開了
        一個授權邊界，⛔ 不是主張對帳工具看不到它是對的。若日後宣告了該檔，改名並補
        登記那一列即可。
    """
    stamp = now if now is not None else now_iso8601()
    candidate = rendered if rendered is not None else _render_issue_body(c, stamp)
    baseline = _render_issue_body(_line_flattened_card(c), stamp)
    checks: list[tuple[str, object, Callable[[str], object]]] = [
        ("需求", c.requested_by, _read_requested),
        ("規劃", c.planned_by, _read_planned),
        ("Initiative", c.initiative or "—", _read_initiative),
        ("spec 基線", c.spec_baseline, _read_spec_baseline),
        ("DB", f"db_scope={c.db_scope}", lambda b: _read_prefixed_header(b, "- DB：")),
        ("服務的原始目標", c.service_goal, lambda b: _read_prefixed_header(b, "- 服務的原始目標：")),
        ("執行", c.executor, lambda b: _read_routing_group(b, "executor")),
        ("執行建議層級", c.executor_capability, lambda b: _read_routing_group(b, "exec_tier")),
        ("執行能力層級理由", c.executor_capability_reason, lambda b: _read_routing_group(b, "exec_reason")),
        ("查核", c.reviewer, lambda b: _read_routing_group(b, "reviewer")),
        ("查核建議層級", c.reviewer_capability, lambda b: _read_routing_group(b, "rev_tier")),
        ("查核能力層級理由", c.reviewer_capability_reason, lambda b: _read_routing_group(b, "rev_reason")),
        ("核心痛點", c.core_pain, _read_core_pain),
        ("驗收條件", list(c.acceptance), lambda b: _read_checklist_texts(b, _ACCEPTANCE_HEADING)),
        ("驗證", list(c.verification), lambda b: _read_checklist_texts(b, _VERIFICATION_HEADING)),
        ("資源宣告", c.resources, lambda b: parse_resource_block(b)),
    ]
    if c.brief:
        checks.append(("簡介", c.brief, _read_brief_text))
    if c.card_face is not None:
        checks.append(("卡面表單", c.card_face, try_parse_card_face))
    # ⚠️ **刻意登記的涵蓋落差**：``owner``／``iteration`` 只出現在 Log 行，而 Log 是
    # append-only 留痕、本檔沒有「讀回單一 Log 欄位」的路徑 ⇒ 它們**只由性質 (1)
    # 涵蓋**（例如 owner 裡塞進一個 ``## Log`` 會讓 ``split_at_log`` 讀不回，當場拒收）。
    # ⛔ 不得由此推出「Log 行的值有往返保證」。``feature`` 進的是 Issue 標題不是 body，
    # 不在本守衛管轄內。
    enforce_write_boundary(baseline, candidate, roundtrip=checks, where="open 渲染")


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


#: 各章節標題**全部**的合法寫法（封閉集合）。⛔ 只有資源宣告有第二種寫法，
#: 且它是 2026-08-04 遷移的歷史產物、⛔ 不是擴充點——來源是 ``resources`` 的
#: ``SECTION_HEADING_VARIANTS``，⛔ 本檔不另存一份字面值。
_HEADING_VARIANTS: dict[str, tuple[str, ...]] = {
    _RESOURCE_HEADING: SECTION_HEADING_VARIANTS,
}


def _heading_hit(line: str, heading: str, *, allow_known_variants: bool) -> bool:
    """該行是不是 ``heading`` 這個章節的標題。**唯一判準，⛔ 不得在別處另寫一份。**

    ⚠️ ``allow_known_variants`` 放寬的是**帶括號補述**（``<heading>（…）``），⛔ **不是任意前綴**。
    這個分界是 R1-01 的成因：``drop_sentinel_less_resource_section`` 原本自己寫了一份
    裸 ``startswith(_RESOURCE_HEADING)``，於是 ``## 資源宣告備註`` 也被當成資源宣告區段
    ——查核者實測它連同人寫的說明**一起被靜默刪除**。⇒ 判準抽成一份、兩處共用，
    ⛔ 不是在原處補一個 if：同族第三次的教訓是「每個新呼叫端都自己重寫一份謂詞」。
    """
    stripped = line.strip()
    if stripped == heading:
        return True
    if not allow_known_variants:
        return False
    return stripped in _HEADING_VARIANTS.get(heading, ())


def _locate_section(
    lines: list[str], heading: str, *, allow_known_variants: bool = False
) -> tuple[int, int]:
    """回傳該章節的 [起始標題列, 下一個 ``## `` 標題列或結尾)。標題須唯一。

    ``allow_known_variants`` 讓標題**額外**接受 ``<heading>（…）`` 這種帶括號補述的寫法
    （WF-RESOURCE-HEADING-SUFFIX1）。⛔ **預設關閉，且只有資源宣告那一個呼叫端打開它**——
    本函式是泛用的（``## 核心痛點``／``## 驗收條件``／``## 簡介`` 都走它），
    全域放寬等於為今天不存在的形態開門（實測全母體只有資源宣告有第二種寫法）。

    ⚠️ 「恰好 1 次」的檢查在新謂詞下**一字未動**——它才是擋住 #43 劫持的東西：
    真區段前插一個帶後綴的假區段、或兩種標題並存，都會讓命中數變 2 而被拒。
    """

    starts = [i for i, line in enumerate(lines) if _heading_hit(line, heading, allow_known_variants=allow_known_variants)]
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
    candidate = _join("\n".join(new_lines), tail)
    enforce_write_boundary(
        body,
        candidate,
        roundtrip=[(heading, list(new_items), lambda b: _read_checklist_texts(b, heading))],
        where=f"`{heading}`",
    )
    return candidate, old_repr


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
    candidate = _join("\n".join(lines), tail)
    enforce_write_boundary(
        body,
        candidate,
        roundtrip=[("spec 基線", new_value, _read_spec_baseline)],
        where="`spec 基線`",
    )
    return candidate, old


def adopt_resource_sentinels(body: str) -> tuple[str, str]:
    """把既有的資源宣告 三重反引號 json 區塊包進哨兵（WF-RESOURCE-HEADING-SUFFIX1 第二段）。

    ⭐ **不是「填空骨架」**：實測那 33 張遷移卡的區段**已經有合法的 JSON 宣告**
    （30 張 ``resources: []``、3 張帶真實清單），⛔ 缺的只有 begin/end 哨兵。
    ⇒ 本函式**逐字保留原 payload**，只在 fence 前後各插一行 ⇒ ⛔ 不發明、也不丟資訊。
    （若改成寫入一份新的空宣告，就會把 3 張已有清單的卡的內容抹掉，
    也會把「未正式宣告」偽造成「已確認無資源」——那正是 ``aiwf#31`` §3.2 禁止的轉譯。）

    ⛔ 刻意做得很窄，任一不成立即拋錯不猜：
    區段必須**恰好 1 個**、⛔ 尚未有哨兵、區段內**恰好 1 個** 三重反引號 json 圍籬。

    ⚠️ 包完之後仍可能解析失敗——payload 本身若含不合 grammar 的 token
    （實測有 1 張把卡 ID 寫進 resources），失敗會**從哨兵層位移到 grammar 層**。
    ⇒ 那是進展也是誠實的結果，⛔ 不該由本函式代為「修正」內容。

    回傳 ``(新 body, 原區段原文)``。
    """
    head, tail = split_at_log(body)
    lines = head.splitlines()
    start, end = _locate_section(lines, _RESOURCE_HEADING, allow_known_variants=True)
    seg = lines[start:end]
    if any(CLAIMS_BEGIN_MARKER in line for line in seg):
        raise AmendError("該區段已有 resource-claims 哨兵；本操作只處理缺哨兵的卡")
    fences = [k for k, line in enumerate(seg) if line.strip() == "```json"]
    if len(fences) != 1:
        raise AmendError(
            f"區段內有 {len(fences)} 個 ```json 圍籬，必須恰好 1 個；拒絕猜測要包哪一個"
        )
    open_at = fences[0]
    close_at = next(
        (k for k in range(open_at + 1, len(seg)) if seg[k].strip() == "```"), None
    )
    if close_at is None:
        raise AmendError("區段內的 ```json 圍籬沒有對應的收尾 ```；拒絕修訂")
    old_repr = "\n".join(seg).strip()
    wrapped = (
        seg[:open_at]
        + [CLAIMS_BEGIN_MARKER]
        + seg[open_at : close_at + 1]
        + [CLAIMS_END_MARKER]
        + seg[close_at + 1 :]
    )
    new_lines = lines[:start] + wrapped + lines[end:]
    return _join("\n".join(new_lines), tail), " ".join(old_repr.split())


def drop_sentinel_less_resource_section(body: str) -> tuple[str, str]:
    """刪掉**沒有哨兵**的那個資源宣告區段，前提是另有一個帶哨兵的（WF-RESOURCE-HEADING-SUFFIX1）。

    ⭐ **為什麼需要它**：2026-08-04 遷移當時的做法是「在 head 末端 **append** 一個正規區段」，
    ⛔ 不是取代殘留（由平台編輯歷史追出：``cpbl#55`` 建卡後四小時那次編輯的 diff）。
    於是有 6 張卡同時帶著「遷移殘留（無哨兵）」與「正規區段（有哨兵）」兩個標題。
    那在**逐字相等**比對下是安全的（只命中短標題那一個），⇒ 它們今天解析得動；
    ⚠️ 但本卡把比對放寬成前綴之後兩個都命中 ⇒ 「恰好 1 次」不變量拒收
    ⇒ **6 張今天正常的卡會變成解析失敗**。那是**回歸**，⛔ 不是邊界案例。

    ⛔ **刻意做得很窄**：只在「恰好 2 個資源宣告標題、其中恰好 1 個區段含哨兵」時動作，
    且只刪**無哨兵**的那個。任何其他形狀一律拋錯不猜——本函式是在修別人留下的殘留，
    ⛔ 不是通用的區段刪除器。

    ⚠️ 內容不會遺失的依據是**逐張比對過的**（6/6）：5 張的殘留 payload 是 ``resources: []``
    或與正規區段完全相同；1 張（``OPS-CODE-BRANCH-PROTECT1``）多兩個字串，
    ⛔ 但兩者皆不符 resource grammar（缺 ``file:`` 前綴／根本不是資源）⇒ 機器面本無效力。
    ⇒ 呼叫端須把被刪區段的原文寫進 Log（本函式第二個回傳值即為此）。

    回傳 ``(新 body, 被刪區段原文)``。
    """
    head, tail = split_at_log(body)
    lines = head.splitlines()
    starts = [
        i for i, line in enumerate(lines)
        if _heading_hit(line, _RESOURCE_HEADING, allow_known_variants=True)
    ]
    if len(starts) != 2:
        raise AmendError(
            f"本操作只處理「恰好 2 個資源宣告標題」的卡，實際 {len(starts)} 個；拒絕猜測"
        )

    def _seg(i: int) -> tuple[int, int]:
        end = next((j for j in range(i + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
        return i, end

    segs = [_seg(i) for i in starts]
    with_sentinel = [k for k, (a, b) in enumerate(segs) if any(CLAIMS_BEGIN_MARKER in l for l in lines[a:b])]
    if len(with_sentinel) != 1:
        raise AmendError(
            f"兩個資源宣告區段中含哨兵者為 {len(with_sentinel)} 個，必須恰好 1 個；拒絕猜測"
        )
    victim = segs[1 - with_sentinel[0]]
    removed = "\n".join(lines[victim[0]:victim[1]]).strip()
    kept = lines[:victim[0]] + lines[victim[1]:]
    # 收掉刪除後可能出現的連續空行，⛔ 不用正規化整份 body（那會動到無關的排版）。
    while kept and victim[0] < len(kept) and victim[0] > 0 and not kept[victim[0] - 1].strip() and not kept[victim[0]].strip():
        del kept[victim[0]]
    return _join("\n".join(kept), tail), " ".join(removed.split())


_MIGRATION_HEADER_SECTIONS = (_CORE_PAIN_HEADING, _ACCEPTANCE_HEADING, _VERIFICATION_HEADING)


def restore_migration_header(
    body: str,
    *,
    requested_by: str,
    planned_by: str,
    initiative: str,
    spec_baseline: str,
) -> tuple[str, str]:
    """補回 2026-08-04 遷移卡缺少的 canonical 標頭行與必要空章節（WF-RESOURCE-HEADING-SUFFIX1 第四段）。

    ⭐ **為什麼需要它，⛔ 以及理由不是「讓這些卡變成 wfcli 可達」**：實測那批卡對
    ``amend --brief``／``handoff``／``review``／``checkpoint``／``deploy-*`` 都打得到。
    真正的理由是 canonical §6.4.1——它們**沒有** ``## 驗收條件`` 也沒有 ``## 驗證``
    （``amend --acceptance`` 拒收原文：「章節 ``## 驗收條件`` 在 Log 之前出現 0 次」）
    ⇒ 「兩欄須於離開規劃前填實」對它們**構造上不可滿足** ⇒ 活卡即使被認領也永遠過不了規劃閘門。

    ⛔ **只補結構與可溯的值，不產生內容。** 章節一律留空 ⇒ 補完之後事後掃描仍會把
    它們報成「缺核心痛點／缺驗收」，**那是對的**，⛔ 不得視為本操作沒做完。

    ⚠️ ``requested_by`` 是**一句斷言**⛔ 不是排版修復：它日後會成為 ``--ruling-url``
    精確比對的授權基準。⇒ 呼叫端須自 cutover 前一版的原始卡面取值，並把**舊值原文、
    來源 commit/path、正規化規則**逐字寫進 Log。本函式**不做正規化**（⛔ 不剝括號、
    不猜身分）——傳進來什麼就寫什麼，轉換責任留在看得見來源的那一層。

    ⛔ 刻意做得很窄，任一不成立即拋錯不猜：標頭行**必須尚未存在**、三個目標章節
    **必須都不存在**、``requested_by``／``planned_by`` 不得為空或含分隔用全形空格。

    回傳 ``(新 body, 插入內容原文)``。
    """
    # ⚠️ **四個欄位全部要驗，⛔ 不只前兩個。** R1-02：原本只驗 requested_by／planned_by，
    # 而 initiative／spec_baseline 同樣會被寫進標頭行 ⇒ 注入換行即在 head 裡多出一個
    # ``## Log``，`split_at_log` 當場拋錯 ⇒ 該卡**永久無法以 wfcli 修改**（＝ ``aiwf#15``
    # 那個狀態，實測既無自動修法也無可用的人工程序）。⛔ 這不是想不到，是漏了一整類輸入。
    for label, value, required in (
        ("需求", requested_by, True),
        ("規劃", planned_by, True),
        ("Initiative", initiative, False),
        ("spec 基線", spec_baseline, False),
    ):
        text = value or ""
        if required and not text.strip():
            raise AmendError(f"`{label}` 值為空；⛔ 拒絕寫入佔位身分（它會成為授權基準）")
        if any(ch in text for ch in ("\u3000", "\n", "\r")):
            raise AmendError(
                f"`{label}` 值含分隔用全形空格或換行：{text!r}；⛔ 會破壞標頭行解析"
                "（換行更會在 head 裡多出一個 `## Log`，使該卡永久無法以 wfcli 修改）"
            )

    head, tail = split_at_log(body)
    lines = head.splitlines()

    existing = [i for i, line in enumerate(lines) if _REQUESTED_BY_RE.match(line.strip())]
    if existing:
        raise AmendError(
            f"卡面已有 `- 需求：…　規劃：…` 標頭行（{len(existing)} 行）；本操作只處理缺行的遷移卡"
        )
    if any(_SPEC_BASELINE_RE.match(line.strip()) for line in lines):
        raise AmendError("卡面已有 `- Initiative：…　spec 基線：…` 標頭行；拒絕重複插入")

    present = [h for h in _MIGRATION_HEADER_SECTIONS
               if any(line.strip() == h for line in lines)]
    if present:
        raise AmendError(
            f"卡面已有章節 {present}；本操作只補**全缺**的骨架，⛔ 不與既有章節合併"
        )

    header = [
        f"- 需求：{requested_by}　規劃：{planned_by}",
        f"- Initiative：{initiative or '—'}　spec 基線：{spec_baseline or '—'}",
        "",
    ]
    sections: list[str] = []
    for h in _MIGRATION_HEADER_SECTIONS:
        sections += ["", h, ""]

    new_lines = header + lines
    while new_lines and not new_lines[-1].strip():
        new_lines.pop()
    new_lines += sections
    inserted = "\n".join(header[:2] + [h for h in _MIGRATION_HEADER_SECTIONS])
    candidate = _join("\n".join(new_lines), tail)
    enforce_write_boundary(
        body,
        candidate,
        roundtrip=[
            ("需求", requested_by, _read_requested),
            ("規劃", planned_by, _read_planned),
            ("Initiative", initiative or "—", _read_initiative),
            ("spec 基線", spec_baseline or "—", _read_spec_baseline),
        ],
        where="`遷移標頭`",
    )
    return candidate, " ".join(inserted.split())


def _sync_db_scope_header(head_lines: list[str], body: str, rendered_block: str) -> list[str]:
    """把 ``- DB：db_scope=…`` 標頭行同步成 ``rendered_block`` 宣告的值。

    **只在改動前兩個載體一致時才動**；任一邊解析不出來、標頭行不是恰好一行、或改動前
    就已經不一致，一律原樣回傳（理由見呼叫點的 (d)）。
    """
    try:
        old_scope = parse_resource_block(body).db_scope
        new_scope = parse_resource_block(rendered_block).db_scope
    except Exception:  # noqa: BLE001 - 解析不出來就沒有「兩者一致」可言
        return head_lines
    if old_scope == new_scope:
        return head_lines
    prefix = _DB_HEADER_PREFIX + _DB_SCOPE_KEY
    hits = [i for i, line in enumerate(head_lines) if line.startswith(prefix)]
    if len(hits) != 1 or head_lines[hits[0]][len(prefix):].strip() != old_scope:
        return head_lines
    synced = list(head_lines)
    synced[hits[0]] = f"{prefix}{new_scope}"
    return synced


def amend_resource_block(body: str, rendered_block: str) -> tuple[str, str]:
    """整份替換「資源宣告」章節；``rendered_block`` 須含標題（``resources.render_block``
    的輸出即是）。回傳 (新 body, 原章節原文)。
    """
    head, tail = split_at_log(body)
    lines = head.splitlines()
    start, end = _locate_section(lines, _RESOURCE_HEADING, allow_known_variants=True)
    old_repr = "\n".join(lines[start:end]).strip()
    # ⭐ **標題逐字保留，⛔ 不由 ``rendered_block`` 決定**（WF-RESOURCE-HEADING-SUFFIX1）。
    #
    # ``resources.render_block`` 的第一行是短標題常數，⇒ 原本整段替換會把 2026-08-04
    # 遷移卡的後綴（``（機器可讀；`null`／`[]` 代表未正式宣告，不代表無資源）``）
    # **靜默吃掉**。而那句後綴不是排版，是「未正式宣告 vs 無資源」這條分界今天的
    # **唯一載體**——schema 的 ``resources`` 型別是 ``list[str]``，``null`` 被拒、
    # 缺鍵靜默變 ``[]``，⇒ 機器面表達不出第三個狀態。
    #
    # ⭐ 做成**結構性**而非參數：把找到的標題填回去，呼叫端**忘不掉**。
    # 若改成「由呼叫端傳 heading」，缺陷形態就變成「某個呼叫端沒傳」——
    # 那正是本卡研究期抓到的原始形態。
    replacement = rendered_block.splitlines()
    if replacement:
        replacement[0] = lines[start]
    new_lines = lines[:start] + replacement + [""] + lines[end:]
    # ⭐ **標頭行的 db_scope 跟著一起改，⛔ 不是「順手美化」**（2026-08-27，需求方裁定
    # 甲案把跨欄位不變量併入本卡後補上）。
    #
    # (a) 現在的行為：``db_scope`` 有兩個載體（``- DB：db_scope=…`` 標頭行、資源宣告
    #     JSON），本函式改後者時把前者一起改。
    # (b) 為什麼非改不可：改動前 ``wfcli amend --db-scope`` **只改 JSON 與 Project 欄位**，
    #     ⛔ 從不碰標頭行 ⇒ 官方寫入路徑自己就會產出一張 ``Card.__post_init__`` 讀不回的卡
    #     （逐字「db_scope 與資源宣告內的 db_scope 不一致」）。那正是 §3.2 指名的
    #     「寫得出、讀不回」跨欄位類別，且它**今天在本 repo 有實例**，⛔ 不是構造出來的。
    #     ⇒ 不修它，:func:`read_db_scope_agreement` 就會把這條合法路徑整條擋死。
    # (c) ⛔ **不得由此推出「這是以正規化代替拒收」**（§3.2 規則二禁止的那件事）：規則二
    #     禁的是**改寫使用者送進來的值**。這裡沒有任何值被改寫——``--db-scope read`` 這個
    #     值被逐字寫進兩個載體，因為兩者表達的是**同一個事實**。留痕也沒有缺口：標頭行
    #     的舊值在同步前**必然等於**舊 JSON 的 ``db_scope``（那是同步的前提條件），而舊
    #     JSON 整段已被呼叫端寫進 Log 的原值欄。
    # (d) ⛔ **也不得推出「它會修好既有不一致的卡」**——刻意不修：改動前兩個載體就已經
    #     各說各話時本函式**不動標頭行**（見 :func:`_sync_db_scope_header`），因為那時
    #     「哪一個才是真的」沒有證據，替它選一個等於無痕覆寫。那類卡落在差分探測的
    #     「寫入前就讀不回 ⇒ 跳過」側，治它是 ``aiwf#138`` 的射程。
    new_lines = _sync_db_scope_header(new_lines, body, rendered_block)
    candidate = _join("\n".join(new_lines), tail)
    if candidate == _join(head, tail):
        raise AmendError("資源宣告與現值相同；拒絕寫入不實的修訂留痕")
    # ⚠️ 資源宣告的值有 grammar（``_RESOURCE_PREFIX_RE``），但 grammar 的 ``.`` **不排除**
    # U+2028／U+2029，而 ``json.dumps(ensure_ascii=False)`` 也**不逃脫**它們
    # ⇒ ``file:x<U+2028>## Log`` 這種值過得了 grammar、寫進去卻讓卡面多出一個 ``## Log``。
    # ⛔ 不在 grammar 上補字元清單（那是列舉法）；由本守衛以結構差分擋。
    # ⚠️ **期望值本身可能解析不出來**（就地留註）：``rendered_block`` 是「即將寫進去的
    # 那一段」，值把它自己弄壞時 ``parse_block`` 會拋 ``ResourceDeclarationError``。
    # ⇒ 那不是呼叫端的 bug，正是「寫得出、讀不回」的最純粹形態，故轉成寫入邊界拒收。
    # ⛔ 不得改成「解析不出來就跳過往返比對」——那會把最嚴重的一格變成免驗的一格。
    try:
        expected = parse_resource_block(rendered_block)
    except Exception as exc:  # 期望值自己解析不回來 ⇒ 就是本守衛要擋的那件事
        raise MarkerWriteBoundaryError(
            f"寫入邊界拒收（未寫入任何狀態）：`資源宣告`即將寫入的區塊自己就解析不回來"
            f"（讀取端錯誤：{exc}）。⚠️ 卡面本身沒有損壞、本次也未改動它。"
        ) from exc
    enforce_write_boundary(
        body,
        candidate,
        roundtrip=[("資源宣告", expected, parse_resource_block)],
        where="`資源宣告`",
    )
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
    candidate = _join("\n".join(lines), tail)
    enforce_write_boundary(
        body,
        candidate,
        roundtrip=[("Initiative", new_value, _read_initiative)],
        where="`Initiative`",
    )
    return candidate, old


class RoutingUnamendable(AmendError):
    """卡面的路由行定位不成立（無版本標記、標記多於一個、候選行不唯一、不相鄰、
    或解析不出六欄）⇒ ⛔ 拒絕修訂。

    ⭐ **定位判準與 :func:`compare_capability_to_card` 逐字同一套，⛔ 不另寫一份**：
    那一套被同一個形狀打穿過兩次（R4-003／R5-001，見 ``_routing_line_candidates``
    上方那整段），寫第二份等於讓下一次打穿只修到其中一份。
    """


def _locate_routing_line(body: str) -> tuple[list[str], int, re.Match[str]]:
    """回傳 ``(Log 之前的全部行, 路由行在其中的索引, 解析結果)``；不成立即拋。"""
    head, _ = split_at_log(body)
    head_lines = head.splitlines()
    first_heading = next(
        (i for i, ln in enumerate(head_lines) if ln.startswith("## ")), len(head_lines)
    )
    header = head_lines[:first_heading]

    declarations = [i for i, ln in enumerate(header) if ln.strip() == ROUTING_MARKER]
    if len(declarations) != 1:
        raise RoutingUnamendable(
            f"卡面標頭區有 {len(declarations)} 個獨立成行的 {ROUTING_MARKER} 宣告（應恰為 1）"
            "；⛔ 拒絕猜哪一行是現行路由行"
            + ("。本卡開立於規劃期路由必填之前 ⇒ 沒有可修訂的路由行" if not declarations else "")
        )
    candidates = _routing_line_candidates(header)
    if len(candidates) != 1:
        raise RoutingUnamendable(
            f"卡面標頭區的候選路由行有 {len(candidates)} 行（應恰為 1）"
            "——候選＝標頭區裡無法被正面辨識為已知欄位行的每一行"
        )
    index = candidates[0]
    if index != declarations[0] + 1:
        raise RoutingUnamendable(
            f"{ROUTING_MARKER} 宣告在標頭區第 {declarations[0] + 1} 行，"
            f"但候選路由行在第 {index + 1} 行——標記必須緊鄰它所宣告的路由行"
        )
    match = _ROUTING_PARSE_RE.match(header[index].rstrip())
    if match is None:
        raise RoutingUnamendable(
            "候選路由行不符合 templates/tasks-card.md 第 4 行格式"
            "（全形／半形空白錯置、缺分號或括號、理由為空、查核段缺失、混入零寬字元）"
            "；⛔ 拒絕在讀不回的行上做替換"
        )
    return head_lines, index, match


def amend_routing(body: str, updates: dict[str, str]) -> tuple[str, str]:
    """整行重寫路由行；``updates`` 只帶要改的群組（鍵＝:data:`ROUTING_FIELDS`）。

    回傳 ``(新 body, 原路由行逐字)``。未給的群組**逐字沿用卡面現值**——⛔ 不從別處
    重建，也⛔ 不正規化（``templates/handoff-contract.md`` §3.2 規則二禁止以正規化
    代替拒收）。

    ⚠️ **改完仍須過 ``validate_routing_names``／``validate_capability_routing``**：
    本函式自己就跑，⇒ 寫不出一行讀不回的路由行（寫入端拒收，與 ``Card.__post_init__``
    同一組判準函式）。
    """
    unknown = sorted(set(updates) - set(ROUTING_FIELDS))
    if unknown:
        raise RoutingUnamendable(f"未知的路由欄位 {unknown}；合法鍵＝{list(ROUTING_FIELDS)}")
    head_lines, index, match = _locate_routing_line(body)
    old_line = head_lines[index]
    values = {name: match.group(name) for name in ROUTING_FIELDS}
    values.update({k: v for k, v in updates.items() if v is not None})
    validate_routing_names(executor=values["executor"], reviewer=values["reviewer"])
    validate_capability_routing(
        executor_capability=values["exec_tier"],
        executor_capability_reason=values["exec_reason"],
        reviewer_capability=values["rev_tier"],
        reviewer_capability_reason=values["rev_reason"],
    )
    new_line = format_routing_body_line(**values)
    if new_line == old_line:
        raise AmendError("路由行與現值相同；拒絕寫入不實的修訂留痕")
    head_lines[index] = new_line
    _, tail = split_at_log(body)
    return _join("\n".join(head_lines), tail), old_line


def amend_brief(body: str, new_value: str) -> tuple[str, str | None]:
    """改（或首次寫入）卡片簡介；回傳 (新 body, 原值或 None)。

    canonical §6.3：body 哨兵區塊為**權威**、Project TEXT 欄位為恆等導出。本函式只動
    body 那一半——欄位由指令層在 body 寫成功後才寫，並讀回驗證（失敗模式是
    「body 已更新、欄位過期」，偵測見 :func:`brief.drifted`）。

    ⚠️ **既有卡沒有 ``## 簡介`` 區段**時，本函式會自動補充一個。
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
    candidate = new_head + ("\n" + tail if tail else "\n")
    # ⭐ 這一格是「兩條性質必須並用」的**實證來源**：``--brief`` 的值行內提及
    # ``<!-- card-brief:end -->`` 時，每一條讀取路徑都照樣讀得回（性質 (1) 抓 0），
    # 但 ``try_parse_brief`` 讀回的是被哨兵截斷後的前半段 ⇒ 只有性質 (2) 抓得到。
    enforce_write_boundary(
        body,
        candidate,
        roundtrip=[("簡介", new_value, _read_brief_text)],
        where="`簡介`",
    )
    return (candidate, old)


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
    candidate = _join("\n".join(lines), tail)
    enforce_write_boundary(
        body,
        candidate,
        roundtrip=[("核心痛點", new_value, _read_core_pain)],
        where="`核心痛點`",
    )
    return candidate, old


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
    "CARD_FACE_SECTION_HEADING",
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
    "ROUTING_FIELDS",
    "RoutingUnamendable",
    "amend_acceptance",
    "amend_core_pain",
    "amend_initiative",
    "amend_resource_block",
    "amend_routing",
    "amend_spec_baseline",
    "amend_verification",
    "append_log_line",
    "capability_reason_missing_message",
    "capability_tier_violation_message",
    "chain_depth_violation_message",
    "compare_capability_to_card",
    "format_branch_worktree",
    "format_routing_body_line",
    "format_routing_line",
    "is_tier_downgrade",
    "now_iso8601",
    "parse_branch_worktree",
    "parse_requested_by",
    "render_issue_body",
    "render_spec_markdown",
    "routing_values",
    "routing_reserved_char_message",
    "split_at_log",
    "tier_downgrade_needs_ruling",
    "validate_capability_routing",
    "validate_routing_field",
    "validate_routing_names",
]
