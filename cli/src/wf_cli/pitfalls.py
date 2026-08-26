"""分階段踩坑族清冊與「離開階段」的報告閘門（WF-STAGE-PITFALL-LIST1）。

## 本模組做什麼、不做什麼

canonical ``AI_WORKFLOW.md`` §6.4 定義了一份分階段踩坑清單，條文有兩半：
「進入階段時 CLI 印出該階段的坑」與「離開階段時交付須逐項作說明」。
**本模組只實作後半**，理由是需求方 2026-08-26 的裁定：印出**連偵測器都不是**
（是通知），且 ``handoff`` 的 stdout 讀者是祕書、不是下一位執行者；送達通道
另屬 ``WF-DISPATCH-FROM-HANDOFF1``。後半掛在唯一寫入通道的前置段，缺報告即
``rc≠0`` 且零寫入 ⇒ 有機械執行者。

⛔ **本模組不宣稱它擋得住敷衍。** §6.4 逐字承認「CLI 分不出『認真讀過後寫的
說明』與『隨手打一行過關』」。這裡驗的只有三件機械性質：窮舉性、值域、冒號後
非空。**擋敷衍的是檢閱那一環，不是本模組。**

⛔ **本模組不重新定義 13 族的內容與歸屬**——那在 §6.4 已定。這裡是那份定義的
**權威副本**，canonical 保留族名與裁斷作為引用面，兩個方向由
``cli/tests/test_pitfalls.py`` 的互含測試逐字釘死。

## 為什麼 occurrence 數字不進碼

§6.4 的表對每一族標了 occurrence，但**歸併映射從未被寫下**（全 repo 搜 13 個
族名只命中 canonical 自己）⇒ 那些數字今天**不可複驗**。不可複驗的數就不得作為
任何機械判斷的輸入，否則等於把一個無人能檢查的常數放進閘門。⇒ 本模組只取
**族名與階段歸屬**，一個 occurrence 都不抄。

⚠️ 這不是「數字不重要」：§6.4 自己保留了「可依 occurrence 加門檻」的後路，
真要加門檻時得先把歸併映射寫下來、變成可複驗的產出，那是另一張卡的事。

## 「逐項」的粒度＝固定格數 × 受限值域（需求方 2026-08-26 採甲案）

該階段要印的每一族**恰好一列**，值域三選一：``已檢查``／``不適用：<原因>``／
``發現：<處置>``。CLI 驗的是 (i) 逐族有且只有一列，缺一即拒、多一即拒；
(ii) 值在三個值域內；(iii) 後兩者冒號後非空。⛔ 不判斷內容真假。

依據：**CLI 唯一拿得到的性質是窮舉性**，而窮舉性只在格數由清冊決定時存在。
乙案（自選族數 ＋ 強制錨點）讓掉窮舉性之後，剩下的檢查是零資訊。

⭐ **退化的否證條件在此預先登記**（:data:`DEGENERATION_SAMPLE_SIZE` 等三個
常數），門檻寫死在碼裡而不是事後訂。

## 有一個階段構造上永遠印不出來

Project 的 ``階段`` 欄有**七**個選項（末項為維護），而 ``handoff`` 的
``--next-stage`` 沒有維護、``STAGE_PHASE`` 只有六個鍵 ⇒ **維護階段的族清單
在本實作下構造上永遠印不出來**，見 :data:`UNREACHABLE_PHASES`。承接條件：新增
維護階段屬**語彙變更**，會觸發採用專案 cpbl 的 ``roadmap_lines.gate_of``
fail-closed，不是本模組補得起來的。
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: canonical §0.1 的七個階段，**順序與該節逐字相同**。⚠️ 這是 Project ``階段``
#: 欄的 SINGLE_SELECT 選項集合的鏡射（``project.FIELD_SPECS``），不是本模組的
#: 判斷；要變先改條文與欄位。
PHASES: tuple[str, ...] = ("需求", "研究", "規劃", "執行", "審核", "部署", "維護")

#: **全階段族**：每個階段都要回答的族。
#:
#: 前兩個是 §6.4 的「全階段族」本體——它們橫跨四階段，且正好是母體 occurrence
#: 最大的兩個。§6.4 逐字給了理由：**「大」與「跨階段」是同一件事的兩面**，
#: 它們大是因為每個階段都在寫東西，⛔ 不是某階段特別容易犯。
#:
#: 其後六個是 §6.4 的「無實測」族。§6.4 的處置逐字「無實測的 6 族暫列入全階段層
#: 一起印，待有實測再下放」——⛔ 它們在此**不是因為屬於所有階段**，而是因為
#: **階段歸屬今天沒有依據**，硬派一個階段會讓它們該印時不印。成本可承受的理由
#: 是需求方 2026-08-24 裁定**不設每階段族數上限**。
ALL_STAGE_FAMILIES: tuple[str, ...] = (
    "宣稱超過證據",
    "列舉或覆蓋不完整",
    "交付未落地或未接線",
    "文件與現實漂移",
    "狀態轉移或生命週期",
    "可重現性不足",
    "並發或時序不安全",
    "資源或寫入集宣告",
)

#: **階段族**：只在該階段印的族。今天只有執行階段有列，⚠️ 而那是**樣本的性質
#: 不是母體的**——§6.4 逐字寫明那兩日做的碼多、研究少，執行階段被過度取樣，
#: ⛔ 不得據此宣稱「其餘各屬一個階段」。
#:
#: ⚠️ 落入率的第一筆非循環觀測是 **0%（樣本數 1）**：``aiwf#129`` 推翻了當時的
#: 對應表——``守衛涵蓋不足或可被繞過`` 原只印在規劃，實際缺陷發生在執行。
STAGE_FAMILIES: dict[str, tuple[str, ...]] = {
    "執行": (
        "守衛涵蓋不足或可被繞過",
        "身分或歸屬對應錯誤",
        "程序或規格照字面不成立",
        "留痕失真或遺失",
        "解析或正規化錯誤",
    ),
}

#: 本實作到不了的階段，值是**為什麼到不了**。⛔ 不是「不重要」，是構造性缺口：
#: ``--next-stage`` 的 choices 與 ``STAGE_PHASE`` 都沒有它，於是沒有任何一條
#: ``handoff`` 路徑能讓 :func:`roster_for` 以它為輸入被呼叫到。
UNREACHABLE_PHASES: dict[str, str] = {
    "維護": (
        "handoff 的 --next-stage 沒有 maintenance、STAGE_PHASE 也沒有對應鍵，"
        "而維護專屬狀態「運行中」「失效」不在交付狀態的選項集合內 ⇒ 交付狀態的"
        "反函數也產不出它。補上屬語彙變更（會觸發採用專案 cpbl 的 "
        "roadmap_lines.gate_of fail-closed），不在本模組射程內。"
    ),
}

#: 三個合法值域。``已檢查`` 是**整格逐字相等**；另兩個是前綴，冒號後須非空。
VERDICT_CHECKED = "已檢查"
VERDICT_NA_PREFIX = "不適用："
VERDICT_FOUND_PREFIX = "發現："

#: 族名與值之間的分隔符。**全形冒號**，與兩個前綴同一個字元——報告因此可以
#: 直接貼進卡面而不必轉義。解析取**第一個**分隔符，故 ``發現：`` 自己帶的冒號
#: 不會把族名切壞。
FIELD_SEPARATOR = "："

#: 允許的行首裝飾（Markdown 條列）。⛔ 只剪這兩種，不做通用 strip——「隨便什麼
#: 前綴都吃」會讓「多一族」的偵測跟著變寬鬆。
_BULLET_PREFIXES = ("- ", "* ")

#: 閘門生效的分流界線（本次 handoff 自身的時戳）。**不是任選**，三條理由：
#:
#: 1. 既有 handoff 留痕**全部**沒有報告（本卡研究輪實測 717 筆，⚠️ 移動標靶，
#:    交付時須現場重數）。閘門若無條件生效，界線之前那些卡的下一次交接會在
#:    「補不出當時沒有的東西」上卡死——那是噪音不是缺陷。
#: 2. 界線寫**日期**而不是 SHA：執行者存在的時點＝本卡落 main 的時點，而那個
#:    SHA 在寫這行時還不存在（雞生蛋）。日期寫得出來、手算得出來。
#: 3. 本 repo 的 main 會被 ``pull --rebase`` 線性化，SHA 界線會被壓平成孤兒而
#:    失效；日期不會。
#:
#: ⚠️ 界線是**分流輔助**，不是安全邊界（逐字照抄 ``doctor.TRAILER_GUARD_EPOCH``
#: 的自陳）：系統時鐘可任意設定，想繞的人改一次系統時間就繞過去了。它的作用是
#: 讓「界線前的既有卡」與「界線後的新交接」分開處理，不是防禦。
PITFALL_GATE_EPOCH = "2026-08-26T00:00:00+08:00"

#: ⭐ **A3 預先登記的退化否證條件。** 上線後前 :data:`DEGENERATION_SAMPLE_SIZE`
#: 次帶報告的 handoff，若 ``已檢查`` 佔比 ≥ :data:`DEGENERATION_CHECKED_RATIO`
#: **且** ``發現：`` 的筆數 ≤ :data:`DEGENERATION_FOUND_CEILING`，即判定甲案已
#: 退化成打勾，承接卡改採乙案（自選族數 ＋ 強制錨點：檔與行／指令與 rc／40 碼
#: SHA／留言 URL）。
#:
#: ⛔ **門檻寫死在此，不得事後訂。** 事後訂門檻等於看著結果決定什麼叫失敗。
#: ⚠️ 本模組**不自己量測**這三個值——它沒有跨次呼叫的記憶體，量測要從卡面
#: 留痕的踩坑回應摘要事後統計。這裡只負責讓門檻可被引用、且改動看得見。
DEGENERATION_SAMPLE_SIZE = 30
DEGENERATION_CHECKED_RATIO = 0.80
DEGENERATION_FOUND_CEILING = 0


def roster_for(phase: str) -> tuple[str, ...]:
    """該階段要逐族回答的清冊。順序固定：全階段族在前、階段族在後。

    ⛔ 未知階段回空 tuple 而不是丟例外——呼叫端要能區分「這個階段沒有族」與
    「這個階段判不出來」，後者在 :func:`resolve_departing_phase` 就已經表達過了。
    """
    return ALL_STAGE_FAMILIES + STAGE_FAMILIES.get(phase, ())


def all_families() -> tuple[str, ...]:
    """13 族的全集，去重後依**首次出現順序**排列。互含測試的碼側輸入。"""
    seen: list[str] = list(ALL_STAGE_FAMILIES)
    for families in STAGE_FAMILIES.values():
        for name in families:
            if name not in seen:
                seen.append(name)
    return tuple(seen)


@dataclass(frozen=True)
class PhaseResolution:
    """「正在離開哪個階段」的判定結果。

    ``phase`` 為 ``None`` 代表**判不出來**，此時 ``basis`` 說明卡在哪一步。
    ⛔ 判不出來時不猜：不知道階段就不知道該要求哪幾族，硬要一份清冊等於要求
    一份連 CLI 自己都算不出正確格數的東西。
    """

    phase: str | None
    #: 判定依據的人話（會逐字進 stderr 與卡面留痕）。
    basis: str
    #: 判定走的是哪條路：``field``（Project 階段欄）／``status``（交付狀態反函數）
    #: ／``none``（兩條都不成立）。
    source: str


def status_to_phase(
    stage_status: dict[str, str], stage_phase: dict[str, str]
) -> dict[str, str]:
    """交付狀態 → 階段的反函數，由呼叫端的兩張表**組合**而成，⛔ 不另抄一份。

    兩張表都在 ``commands/handoff_cmd.py``：``STAGE_STATUS`` 是
    ``--next-stage`` → 交付狀態，``STAGE_PHASE`` 是 ``--next-stage`` → 階段。
    反函數＝先由狀態回推 next-stage 鍵，再查階段。

    **單射性由資料保證、不由本函式假設**：若兩個 next-stage 鍵映到同一個交付
    狀態，後者會覆蓋前者而靜默失真 ⇒ 這裡遇到重複的交付狀態即**整個丟掉那個
    狀態**（不猜），並由 ``test_pitfalls.py`` 斷言今天沒有重複。

    ⚠️ 本函式只涵蓋 ``stage_phase`` 有鍵的那些狀態。``📥Backlog`` 在
    ``STAGE_STATUS`` 裡而**不在** ``STAGE_PHASE`` 裡（它改的是狀態不是階段），
    因此不會出現在結果中——那正確：它的階段沿用現值，反推不出來。
    """
    counts: dict[str, int] = {}
    for status in stage_status.values():
        counts[status] = counts.get(status, 0) + 1
    out: dict[str, str] = {}
    for stage, status in stage_status.items():
        if counts[status] != 1:
            continue
        phase = stage_phase.get(stage)
        if phase is not None:
            out[status] = phase
    return out


def resolve_departing_phase(
    stage_field: str | None,
    delivery_status: str | None,
    stage_status: dict[str, str],
    stage_phase: dict[str, str],
) -> PhaseResolution:
    """判定「正在離開哪個階段」。Project ``階段`` 欄優先，其次交付狀態反函數。

    **為什麼欄位優先**：``階段`` 欄是 canonical §0.1 兩軸模型的第一軸本體，
    有值時它就是答案。⚠️ 但該欄今天覆蓋率極低（本卡交付附現場重數），所以必須
    有退路。

    **退路的單射性**：五個交付狀態（需求／研究中／規劃中／執行中／待查核）在
    ``STAGE_STATUS`` 裡各自唯一，反推得出階段。⛔ ``📥Backlog``／``📦已合併``／
    ``⏸阻塞`` 等其餘狀態**沒有反函數**，一律落 ``phase=None``。

    ⚠️ 欄位值不在 :data:`PHASES` 內時**不採信**（帶外改欄位或加選項都做得到），
    退回走反函數；兩條都不成立才 ``None``。
    """
    value = (stage_field or "").strip()
    if value in PHASES:
        return PhaseResolution(value, f"Project 階段欄逐字為「{value}」", "field")

    if value:
        field_note = f"Project 階段欄的值「{value}」不在七個合法階段內，不採信"
    else:
        field_note = "Project 階段欄無值"

    phase = _status_phase(delivery_status, stage_status, stage_phase)
    if phase is not None:
        return PhaseResolution(
            phase, f"{field_note}，由交付狀態「{delivery_status}」反推", "status"
        )
    # ⚠️ 這句話**刻意不列舉交付狀態的字面值**。`scripts/contract_tool_reconcile.py`
    # 以 AST 判定「哪些符號進得了狀態面」，而本函式的回傳值會被判成寫入路徑：
    # 在這裡寫下一個狀態字面，那個狀態就會從「無專責 writer」翻成「有 writer」，
    # 於是一個真實缺口被一句錯誤訊息靜默補平（實測翻紅一次）。⇒ 只講性質。
    return PhaseResolution(
        None,
        f"{field_note}，且交付狀態「{delivery_status}」沒有反函數"
        "（待辦、合併、阻塞這類狀態不對應唯一階段）",
        "none",
    )


def _status_phase(
    delivery_status: str | None,
    stage_status: dict[str, str],
    stage_phase: dict[str, str],
) -> str | None:
    if not delivery_status:
        return None
    return status_to_phase(stage_status, stage_phase).get(delivery_status.strip())


@dataclass(frozen=True)
class ReportRow:
    family: str
    verdict: str
    #: ``checked``／``not_applicable``／``found``；解析不出來時為 ``invalid``。
    kind: str
    #: 後兩者冒號之後的內容（``checked`` 恆為空字串）。
    detail: str = ""


@dataclass
class ReportParse:
    """一份報告的解析結果。``errors`` 非空即不合格——⛔ 呼叫端不得只看 rows。"""

    rows: list[ReportRow] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def counts(self) -> dict[str, int]:
        out = {"checked": 0, "not_applicable": 0, "found": 0}
        for row in self.rows:
            if row.kind in out:
                out[row.kind] += 1
        return out

    def digest(self) -> str:
        """進卡面留痕的一行摘要。⛔ 不含族名也不含自由文字——只有格數與分佈。

        理由：留痕要能事後統計 A3 的退化門檻（``已檢查`` 佔比與 ``發現：`` 筆數），
        而卡面 body 有實測上限、Log 又只增不減 ⇒ 摘要必須是**有界**的。
        報告全文屬檢閱那一環，不由 Log 承載。
        """
        c = self.counts()
        return (
            f"踩坑回應 {len(self.rows)} 族"
            f"（{VERDICT_CHECKED} {c['checked']}／不適用 {c['not_applicable']}"
            f"／發現 {c['found']}）"
        )


def _classify(verdict: str) -> tuple[str, str]:
    if verdict == VERDICT_CHECKED:
        return "checked", ""
    for prefix, kind in ((VERDICT_NA_PREFIX, "not_applicable"), (VERDICT_FOUND_PREFIX, "found")):
        if verdict.startswith(prefix):
            return kind, verdict[len(prefix):].strip()
    return "invalid", ""


def parse_report(text: str, roster: tuple[str, ...]) -> ReportParse:
    """把報告文字解析成逐族的列，並驗三件事：窮舉性、值域、冒號後非空。

    ⛔ **不判斷內容真假**——這是本模組能力的上界，見模組 docstring。

    窮舉性的兩個方向都驗，缺一不可：
    - **缺一即拒**：清冊有而報告沒有 ⇒ 少答一族就過關，窮舉性就沒了。
    - **多一即拒**：報告有而清冊沒有 ⇒ 湊行數也能過關，格數就不再由清冊決定。
      重複同一族亦拒（兩列相加不等於一列答完）。
    """
    result = ReportParse()
    seen: dict[str, int] = {}
    for raw in (text or "").splitlines():
        line = raw.strip()
        for prefix in _BULLET_PREFIXES:
            if line.startswith(prefix):
                line = line[len(prefix):].strip()
                break
        if not line:
            continue
        if FIELD_SEPARATOR not in line:
            result.errors.append(
                f"這一行沒有全形冒號分隔的「族名{FIELD_SEPARATOR}值」：{line}"
            )
            continue
        family, verdict = line.split(FIELD_SEPARATOR, 1)
        family = family.strip()
        verdict = verdict.strip()
        kind, detail = _classify(verdict)
        result.rows.append(ReportRow(family=family, verdict=verdict, kind=kind, detail=detail))
        seen[family] = seen.get(family, 0) + 1

        if family not in roster:
            result.errors.append(
                f"「{family}」不在本階段的族清冊內（多一即拒；清冊由階段決定，"
                "不由報告決定）"
            )
        elif seen[family] > 1:
            result.errors.append(f"「{family}」出現 {seen[family]} 次，每族恰好一列")
        if kind == "invalid":
            result.errors.append(
                f"「{family}」的值「{verdict}」不在三個合法值域內"
                f"（{VERDICT_CHECKED}／{VERDICT_NA_PREFIX}<原因>／{VERDICT_FOUND_PREFIX}<處置>）"
            )
        elif kind != "checked" and not detail:
            result.errors.append(f"「{family}」的「{verdict}」冒號之後是空的")

    missing = [name for name in roster if name not in seen]
    if missing:
        result.errors.append(
            f"缺 {len(missing)} 族未回答（缺一即拒）：{'、'.join(missing)}"
        )
    return result


def report_template(phase: str) -> str:
    """該階段的空白報告樣板。**由清冊產生**，⛔ 不是手抄的字面。"""
    return "\n".join(f"{name}{FIELD_SEPARATOR}{VERDICT_CHECKED}" for name in roster_for(phase))


def refusal_message(phase: str, resolution_basis: str, errors: list[str] | None = None) -> str:
    """拒收訊息。**要說得出怎麼修**，否則操作者只知道被擋、不知道要交什麼。"""
    lines = [
        (
            f"[handoff] 拒絕：離開「{phase}」階段須附踩坑族清冊回應，本次沒有合格的回應"
            "（狀態面一個字都沒寫）。"
        ),
        f"  - 階段判定依據：{resolution_basis}",
        (
            f"  - 本階段清冊共 {len(roster_for(phase))} 族，每族恰好一列，值三選一："
            f"{VERDICT_CHECKED}／{VERDICT_NA_PREFIX}<原因>／{VERDICT_FOUND_PREFIX}<處置>。"
        ),
    ]
    for err in errors or []:
        lines.append(f"  - {err}")
    lines.append("  - 可直接複製下列樣板改寫後以 --pitfall-report 傳入：")
    lines.extend(f"      {row}" for row in report_template(phase).splitlines())
    lines.append(
        "  - ⛔ 通過本閘門**不代表**內容被驗過：CLI 只驗窮舉性、值域與非空，"
        "分不出認真讀過與隨手打一行；擋敷衍的是檢閱那一環。"
    )
    return "\n".join(lines)
