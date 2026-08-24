"""``wfcli handoff``：交接（狀態轉換＋source SHA＋證據欄必填）。

source_sha 必須是完整 40 字元 hex；``--repo-path`` 有給時另外唯讀驗證該 commit
真的存在於本機 repo（對齊 handoff-contract.md §1「sender 必須先 push source_sha
指向的 commit」的精神——CLI 能做的部份先擋，pushed／branch tip 一致性仍需
receiver 自行複查，CLI 不代替人類判斷）。release 若卡片需要部署且尚未 ✅已驗證，
機械拒絕（canonical §0「需部署卡在部署 ✅已驗證 前不得 release」）。

iteration 遞增（需求方 2026-08-05 拍板；WF-22-CLI2）：``--next-stage
implementation`` 承載「查核退回」語意（review → 退回 implementation 修正），讀回
現值＋1 寫回；``review``／``release`` 這兩個方向不遞增。``--iteration N`` 是顯式
覆寫逃生門（供 iteration counter 需要異常修正時使用），會印出警示，覆寫理由請
說明於既有必填的 ``--evidence``，不另建新旗標。

## ``--cleanup``：release 接上 WF-CLEANUP-GUARD1 的守衛（R1-002）

``--next-stage release`` 原本只寫狀態面。帶 ``--cleanup`` 時改走
`cleanup.execute_closeout_transition`——與 `reconcile --apply` 白名單第 2 條**同一份**
守衛與同一個 executor（`cleanup.py` 模組說明）。差別只在誰發動，前提一條都不放寬。

**兩分支契約（WF-RELEASE-NO-CLEANUP-REFUSE1，2026-08-24 需求方裁定）**：

1. **給了 ``--repo-path`` 卻沒給 ``--cleanup`` ⇒ 拒絕**（``rc=2``，狀態面一個字都不寫）。
   此時守衛拿得到真實 repo，能證明繼續下去會落成
   ``cleanup.classify_state`` 的 ``illegal_terminal_before_cleanup``——而守衛明文拒絕
   修復該狀態（實測 ``illegal_state``：須人工判斷，守衛不代為修復），只能人工刪
   worktree／本地分支／遠端分支再手動關 Issue。
2. **沒給 ``--repo-path`` ⇒ 不拒絕**，但把「收尾清理未執行」寫進卡上 Log 行。該分支的
   ``--cleanup`` 構造上做不到（見下方 ``--cleanup and not args.repo_path`` 的既有拒絕），
   且本專案無該情境實例 ⇒ 不為它設計拒絕；但它先前**只印 stderr、卡上零紀錄**，
   使「不帶 ``--cleanup`` 的 release 發生過幾次」事後不可觀測。

⛔ **本節先前寫的「預設不清理較安全」已被推翻，理由留在這裡以免後人重提**：原論證是
「兩種預設的錯誤代價不對稱：漏清理可以再跑一次補；刪錯了沒有補救」。但**刪錯**那一半
早就被 ``cleanup.AUTHORITY_BY_PROOF`` 以證明分級中和——只有分支已證明是 main 祖先
（commit 都在 main、刪了可用 ``git branch <name> <sha>`` 復原）時才授權刪分支；
``content_absorbed``（squash）只授權 ``remove_worktree``；``diverged`` 與
``unobservable`` 皆為空集合；``NO_AUTHORITY`` 亦空且註解逐字「空集合＝fail-closed：
證不出來就不動手」。⇒ 預設選的那一邊產生的才是**比較不可回復**的狀態，與該論證相反。

兩例實害：``cpbl#138``（2026-08-15）與 ``cpbl#166``（2026-08-22）。⚠️ 因該路徑先前
不寫卡上留痕，兩例是**下限**而非總數。

``--cleanup`` 仍需搭配 ``--repo-path``，因此它無法被設定檔或環境變數「不小心變成預設」。

**刻意不提供 ``--main-ref``／``--remote``**：它們是能讓祖先檢查名存實亡的旋鈕
（把 main_ref 指向待刪分支自己，``merge-base --is-ancestor`` 必然通過）。doctor 的
同名旗標無妨，因為 doctor 唯讀；破壞性路徑上不開這個口。

**``--cleanup`` 做哪幾件事不是固定的**（WF-CLEANUP-SQUASH-AWARE1）：授權範圍由合併
方式決定——merge 合併走 ``ancestor``，三個動作全做；squash 合併走 ``content_absorbed``，
**只移除 worktree、分支保留**（`cleanup.AUTHORITY_BY_PROOF`）。因此本指令的輸出與
寫回卡片的終態留痕**都由實際執行的動作集合產生**（`cleanup.describe_cleanup`），
不是固定字串——上一版就是寫死字串，於是授權分流上線後留痕開始宣稱一件沒發生的事。

**收尾沒走完時仍會留一筆非終態紀錄**（R3-01）：清理被中止、或清理回報成功而效果被扣住
時，worktree 可能已經不在了，狀態面卻依規則不寫。此時只印 stderr 等於卡片上一個字都沒
有，事後重建不出做過什麼。因此那些路徑會往 ``## Log`` 附加一行**明確非終態**的紀錄
（`_record_actions_without_terminal`）：owner／交付狀態／最後交接／iteration 一格不動、
Issue 不關，**只記錄本次實際動作與阻擋原因**。守衛擋下、一個動作都沒走的 ``detect_only``
不寫——世界沒被動過，重跑就能重新得到同一份判定。

## ``--next-stage backlog``：閘門過了、進待辦池（WF-BACKLOG-STAGE1）

``📥Backlog`` 在 canonical ``AI_WORKFLOW.md`` §0 的序列裡（``🧭規劃中 → 📥Backlog``），
但 **從來沒有專責 writer**：唯一寫得出它的是 ``wfcli open`` 的 dataclass 預設（意外充當）
與 ``--status`` 這個無 ``choices`` 的自由文字旗標。後果是**合規的轉換與違規的轉換在機械
上完全同形**。本階段補上那個動詞。

**「受檢查的」逐項回答**（ai-workflow#118 的 R1-002 用詞；三個候選逐一裁定，不挑好做的做）：

1. **要帶前提檢查。** 只加一個 enum 值＝只有「專責」沒有「受檢查」，那不閉合 R1-002
   ——它抱怨的正是自由文字逃生口「不能取代具名、**受前提檢查**的狀態轉換」。

2. **檢查的是：卡片現在的交付狀態必須是 ``🧭規劃中``**（`BACKLOG_REQUIRED_PRIOR_STATUS`），
   **但只對 T2 以上的卡課這個前提**（`BACKLOG_GATE_EXEMPT_TIERS`）。資料來源是 Project 的
   交付狀態欄與級別欄，與 ``release`` 讀 ``部署狀態`` 同一形狀、同一退出碼。
   **它會擋人**：T2 以上、剛開的卡、執行中的卡、已退回的卡一律拒絕；要進 Backlog 得先真的
   到過規劃階段。

   ⚠️ **級別分流的規則本體寫在 canonical** ``AI_WORKFLOW.md`` §3.1（「進 ``📥Backlog`` 的
   狀態前提依級別分流」），本模組只是那條規則的執行者。**先有條文才有這段碼**——讓工具執行
   canonical 沒說的規則，正是 WF-BACKLOG-STAGE1 要治的病，重演一次即是回歸。分流依據
   （需求方 2026-08-21 就 R1-001 的裁定）：§3.1 表格第三列的「所有 T2 以上」是**疊加下限**
   不是替代選項，故 T2 在 §3.1 射程內、有規劃義務；**只有 T0／T1 沒有對應列**。

   ⛔ **``⏸阻塞`` 不是合法前身**，即使它在別的流程裡是個「回得來」的狀態：實查全部阻塞卡
   皆由執行態或查核退回態進入、解阻後回 ``🔨執行中``，``⏸阻塞`` → ``📥Backlog`` 的實例
   為 0。加進來只會得到一條零資訊的檢查。

2b. **T0／T1 直通分支：這個分支一個檢查都不做，而且是刻意的。** 理由不是「T0／T1 風險低」
   這種感覺，是 §3.1 的表**沒有 T0／T1 的列**——沒有條文就沒有可執行的前提，硬編一個出來
   等於工具自己立法。這與下面第 4 點對「需求方批註放行」的處置是**同一個形狀**：說清楚它
   不做什麼，而不是留一個看起來有檢查的空殼。該分支會往 stderr 印一行明說「未做前提檢查」，
   讓「這裡沒有閘門」在操作當下就看得見，而不是要讀碼才知道。

2c. **級別讀不到、為空、或不在 ``card.TIERS`` 語彙內 → 照 T2 以上處理**（fail closed）。
   讀法與 `snapshot.py` 對級別欄的讀法同源（``item.text("級別")``，非字串一律回 ``None``）。
   取 fail closed 的理由是錯誤代價不對稱：誤擋一張 T0 卡，操作者補一次級別欄就過；誤放一張
   級別壞掉的 T4 卡，狀態面上再也看不出它沒走過規劃。

   ⚠️ **這條分支的可達性要說實話：只走 ``wfcli`` 幾乎踩不到。** ``open`` 必填 ``--tier``
   且 ``validation.py`` 驗過語彙，``project.py`` 又把 ``級別`` 宣告成只有 T0–T4 五個選項的
   SINGLE_SELECT，所以本工具自己寫不出空值或語彙外的值。它變得可達要靠**帶外**途徑：
   GitHub UI 直接改欄位或替該欄加選項（``ensure_fields`` 對已存在欄位「原樣保留」，不驗
   選項集合），或 ``open`` 半寫入使 ``卡ID`` 已寫、``級別`` 未寫。⇒ 這是一個**防禦性預設**，
   不是天天會擋人的檢查；⛔ 不得把它講成後者。它的價值在於「真的發生時往哪邊倒」是被
   決定過、且測得出來的，而不是留給 ``None`` 去比較。

   ⚠️ 這也意味著**本檢查信任級別欄**——級別是 ``amend --tier`` 可改的欄位，改級別就能改變
   自己受不受這道閘門管。那不是本卡能關的口（降級另有需求方裁定留痕的要求，見
   ``commands/amend_cmd.py``「級別降級的不對稱」），但必須寫在這裡，不得讓人讀成閘門管得住
   級別本身。

3. **被否決的候選 A——「Log 內須有 planning 階段的事件」**（卡面舉的例）：**機械上做不到。**
   ``handoff`` 的 Log 行只記 owner／iteration／SHA／證據，**不記 ``--next-stage`` 也不記
   ``--status``**（`doctor.HANDOFF_STAGE_EXPECTED_STATUS` 上方的長註解逐條寫明，並把後果
   釘成 `doctor.UNDECIDABLE_HANDOFF`）。因此 ``handoff --next-stage planning`` 留下的行與
   ``--next-stage review`` 留下的行**逐位元組相同**。照這條做，檢查會退化成「Log 裡有任何一
   筆 handoff」——那才是恆真的裝飾。要讓它成立必須改 handoff 的留痕格式與 doctor 的推導語意，
   兩者都在本卡射程外。

4. **被否決的候選 B——「需求方批註放行」**（canonical §3.1 T3 列的字面）：**在本 repo 恆真，
   故明文不實作。** ``docs/ROADMAP.md`` §1：人類、PM、執行者、查核者共用同一個 GitHub 帳號
   ``ruan6047``，且該節逐字禁止「寫看起來在驗證身分、實際恆真的條文」。把它做成欄位＝正是
   被禁的那個東西。

**這個檢查不驗什麼**（誠實邊界，不得被讀成比實際更強）：

- **它不證明規劃閘門真的跑過。** ``🧭規劃中`` 本身既可由 ``handoff --next-stage planning``
  寫入，也可由 ``assign --status 🧭規劃中`` 這個自由文字旗標寫入。本檢查證明的是「狀態面
  說它來自規劃」，不是「有人真的做了規劃」。門檻由「沒有」升到「至少得先移動到規劃」，
  **不是升到不可偽造**。
- **它不驗需求方批註**（見第 4 點）。canonical §3.1 T3 列的「需求方批註放行後才進
  ``📥Backlog``」這半句**仍然無執行者**，本卡不宣稱它已落地。
- **``--status`` 仍然繞得過。** 給了 ``--status`` 時整條 ``elif`` 鏈不進來，前提一條都不跑
  ——這與 ``release`` 的部署閘門是**同一個既有形狀**，不是本卡新開的口。收斂 ``--status``
  成 ``choices`` 是獨立一問（``docs/CONTRACT_TOOL_RECONCILE.md`` §4.1 已登記），不在本卡射程內。
  ⚠️ 這不是假想：2026-08-21 的看板快照裡，``WF-24-EVIDENCE-STRENGTH1`` 的 Log 就有一筆
  ``assign … 交付狀態 📥Backlog``——那條路真的被走過。
- **T0／T1 這條路上沒有任何閘門。** 不是「檢查通過了」，是**沒有檢查**（第 2b 點）。任何
  「``handoff --next-stage backlog`` 成功＝這張卡走過規劃」的推論，對 T0／T1 一律不成立。
- **它管不住級別本身。** 級別由 ``amend --tier`` 可改，改成 T1 就繞開了本閘門（第 2c 點）。
- **它不驗任何既有卡。** 本閘門只管 ``handoff --next-stage backlog`` 這一個動詞；既有卡進
  ``📥Backlog`` 走的是 ``open`` 的 dataclass 預設或 ``--status``，兩條都不經過這裡。因此
  「回放既有卡，零張被本閘門擋下」是**構造上必然**，⛔ 不得拿來當閘門設計良好的證據。

**不遞增 iteration**：只有 ``--next-stage implementation`` 承載退回語意，backlog 與
``review``／``release`` 同樣走 else 分支（現值原樣寫回）。

**不帶 ``--cleanup`` 的代價也必須講明**：那條路徑會在清理完成前寫入終態，依
`cleanup.classify_state` 的分類即 ``illegal_terminal_before_cleanup``；守衛不自動
修復非法態，所以事後再補 ``--cleanup`` 會被擋。因此該路徑會印出警示，而不是靜靜
維持原狀。
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from .. import git_ops
from ..card import TIERS, append_log_line, now_iso8601, parse_branch_worktree
from ..cleanup import (
    SUBSEQUENT_OBLIGATION_STEPS,
    CleanupTarget,
    CleanupOutcome,
    CloseoutResult,
    RemoteCardFacts,
    describe_cleanup,
    execute_closeout_transition,
)
from ..config import add_target_args, resolve_target
from ..gh import GhError, GhRunner, default_runner
from ..project import (
    ItemSnapshot,
    ensure_fields,
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_field_value,
    set_item_body,
)
from ..registry import RegisteredCard, TasksMdRegistry
from ..validation import ValidationError, validate_evidence, validate_source_sha
from .assign_cmd import TERMINAL_STATUSES

STAGE_STATUS = {
    "requirement": "💡需求",
    "research": "🔬研究中",
    "planning": "🧭規劃中",
    "backlog": "📥Backlog",
    "implementation": "🔨執行中",
    "review": "🔍待查核",
}

#: ``--next-stage backlog`` 的**唯一**合法前身狀態（canonical ``AI_WORKFLOW.md`` §3.1
#: 「進 ``📥Backlog`` 的狀態前提依級別分流」）。讀 Project 的交付狀態欄，不符即拒絕
#: ——形狀與 ``release`` 讀 ``部署狀態`` 完全相同。**這個檢查會擋人，不是恆真的裝飾**：
#: 任何不在規劃中的 T2 以上卡（含剛開的卡）都過不了。它**不驗**的東西見本模組 docstring。
#: ⛔ 這裡刻意只有一個值：``⏸阻塞`` 不加進來（理由見 docstring 第 2 點）。
BACKLOG_REQUIRED_PRIOR_STATUS = STAGE_STATUS["planning"]

#: **不課前身狀態前提的級別**（canonical ``AI_WORKFLOW.md`` §3.1；需求方 2026-08-21 就
#: WF-BACKLOG-STAGE1 的 R1-001 裁定）。⚠️ 這個集合是**條文的鏡射，不是本模組的判斷**
#: ——§3.1 的表對 T0／T1 沒有列，所以這條路徑上沒有可執行的前提；集合要變，先改條文。
#: 反過來說：不在本集合裡的一切（T2／T3／T4，以及讀不出來的級別）都課前提，因此擴充
#: 本集合＝實質放寬閘門，屬 canonical 變更而非實作細節。
BACKLOG_GATE_EXEMPT_TIERS = ("T0", "T1")

#: 不帶 ``--cleanup`` 的 release 會造出「終態已寫、清理未做」的組合。這不是猜測，
#: 是 `cleanup.classify_state` 對該組合的分類名稱。
NO_CLEANUP_WARNING = (
    "[handoff] 警示：未帶 --cleanup 的 release 只寫狀態面。worktree 與分支"
    "（權威清單 templates/worktree-lifecycle.md 第 2 步）不會被清理，而終態已經寫下去了"
    "——依 WF_CLEANUP_GUARD1 的分類，這是 illegal_terminal_before_cleanup。"
    "守衛不自動修復非法態，事後再補 --cleanup 會被擋，屆時只能人工收尾。"
)

#: ``--repo-path`` 給了卻沒給 ``--cleanup`` 時的拒絕。**能看見資源就不准製造非法態**：
#: 有 ``--repo-path`` 時守衛拿得到真實 repo，可以證明繼續下去會落成
#: ``illegal_terminal_before_cleanup``——而那正是守衛自己拒絕修復的那一格
#: （``cleanup.classify_state`` 對該組合的分類名稱，實測拒絕訊息為 ``illegal_state``）。
#:
#: **為什麼是拒絕而不是警示**：原設計選警示，理由寫在 ``--cleanup`` 的 help 逐字
#: 「預設不清理——刪除不可逆，預設值取代價可回復的那一邊」。但不可逆那一半早就被
#: ``cleanup.AUTHORITY_BY_PROOF`` 以證明分級中和了——只有分支已證明是 main 祖先
#: （commit 都在 main、刪了可用 ``git branch <name> <sha>`` 復原）時才會刪分支；
#: squash 只授權 ``remove_worktree``；``diverged``／``unobservable`` 皆為空集合。
#: ⇒ 預設選的那一邊產生的才是比較不可回復的狀態，與它自己寫下的理由相反。
#:
#: 兩例實害：``cpbl#138``（2026-08-15）與 ``cpbl#166``（2026-08-22），皆須人工刪
#: worktree／本地分支／遠端分支再手動關 Issue。⚠️ 因該路徑先前不寫卡上留痕，
#: 兩例是**下限**而非總數。
REPO_PATH_WITHOUT_CLEANUP_REFUSAL = (
    "[handoff] 拒絕：--next-stage release 帶了 --repo-path 卻沒帶 --cleanup。"
    "有 --repo-path 時守衛看得見 worktree 與分支，能證明這樣寫下去會落成 "
    "illegal_terminal_before_cleanup——而守衛拒絕修復非法態，事後補 --cleanup 會被擋、"
    "只能人工收尾。請補 --cleanup；若確實要跳過清理，請移除 --repo-path 並在 "
    "--evidence 說明理由（該路徑會把跳過清理寫進卡上留痕）。"
)

#: 無 ``--repo-path`` 的 release 之留痕後綴。⛔ 該分支**不拒絕**——沒有本機 repo 時
#: ``--cleanup`` 在構造上做不到（見上方 ``--cleanup and not args.repo_path`` 的既有拒絕），
#: 且本專案無該情境的實例，⇒ 不為它設計拒絕。但它先前**只印 stderr、卡上零紀錄**，
#: 使「不帶 --cleanup 的 release 發生過幾次」在事後不可觀測（實測：搜三個收尾留痕
#: 字串，「已清除」有命中而「未走到」「無任何對象」皆 0——那個 0 是不可觀測不是未發生）。
#: ⇒ 本後綴讓它可事後稽核。
NO_REPO_PATH_TRACE_SUFFIX = (
    "；⚠️ 未帶 --cleanup 且未帶 --repo-path，收尾清理未執行"
    "（worktree、本地分支、遠端分支皆未處理），狀態面已寫終態"
)


class _CallbackEffectWriter:
    """把第 4 步的兩次狀態面寫入包成 `cleanup.CloseoutEffectWriter`。

    本類別只負責「怎麼寫」；**「何時寫」完全由 executor 決定**——它只在第 1–3 步
    確實完成後才呼叫。因此「終態先於清理」這個組合在這條路徑上寫不出來，不是靠
    呼叫端自律。
    """

    def __init__(
        self,
        close_issue: Callable[[], None],
        write_terminal: Callable[[CleanupOutcome], None],
    ) -> None:
        self._close_issue = close_issue
        self._write_terminal = write_terminal
        self.calls: list[str] = []

    def close_issue(self, target: CleanupTarget) -> None:
        self.calls.append("close_issue")
        self._close_issue()

    def write_release_terminal(
        self, target: CleanupTarget, outcome: CleanupOutcome
    ) -> None:
        # `outcome` 原樣轉交，本類別**不加工也不加註**：留痕的措辭只有
        # `cleanup.describe_cleanup()` 一個產生點。
        self.calls.append("write_release_terminal")
        self._write_terminal(outcome)


def registry_from_items(items: list[ItemSnapshot]) -> TasksMdRegistry:
    """用 Project items 組出守衛要的卡註冊。

    `no_foreign_active_lease` 要問的是「別張活卡是不是還握著同一條分支／worktree」。
    已 cutover 到 GitHub Issues 的專案，那個事實在 Project 欄位裡，不在 docs/TASKS.md，
    所以這裡就地轉成守衛認得的 `RegisteredCard` 形狀（`registry.py` 未改動）。
    """
    active: list[RegisteredCard] = []
    for it in items:
        if not it.card_id:
            continue
        branch, worktree = parse_branch_worktree(it.branch_worktree or "")
        active.append(
            RegisteredCard(
                card_id=it.card_id,
                branch=branch,
                worktree_path=worktree,
                delivery_status=it.delivery_status,
                owner=it.owner_field,
                last_handoff=it.text("最後交接"),
            )
        )
    return TasksMdRegistry(active=active, archived_card_ids=set(), source_paths=[])


def _issue_open(runner: GhRunner, repo: str, issue_number: int) -> bool | None:
    """Issue 現在是不是開著。讀不到回 ``None``——由呼叫端 fail closed。

    這個值決定第 4 步要不要關 Issue。猜錯的後果是「Issue 還開著卻回報 completed」，
    也就是一個看起來成功的半完成收尾，因此不猜。
    """
    try:
        data = runner.run_json(
            ["issue", "view", str(issue_number), "--repo", repo, "--json", "state"]
        )
    except GhError:
        return None
    state = str((data or {}).get("state") or "").upper()
    if state not in {"OPEN", "CLOSED"}:
        return None
    return state == "OPEN"


def _print_closeout(result: CloseoutResult, card_id: str) -> None:
    """stderr／stdout 的逐項回報。**與終態留痕同源**：兩者都由動作集合產生。

    `mode=applied` 不代表三個動作都做了——squash 路徑只做 worktree。因此這裡逐格
    印出，並在最後印一行與終態留痕**逐字相同**的摘要，讓「畫面上看到的」與「寫進
    卡片的」不可能各說各話。
    """
    outcome = result.cleanup_outcome
    print(f"[handoff] 收尾轉換（{card_id}）：mode={result.mode}／"
          f"狀態={result.state_after}（合法={result.legal_state}）")
    if result.authorized_actions:
        print(f"  - 本次授權：{', '.join(sorted(result.authorized_actions))}")
    if outcome.performed:
        print(f"  - 已執行：{', '.join(outcome.performed)}")
    if outcome.skipped_absent:
        print(f"  - 跳過（本來就不存在）：{', '.join(outcome.skipped_absent)}")
    if outcome.withheld_unauthorized:
        print(f"  - 保留（授權不足，刻意不刪）：{', '.join(outcome.withheld_unauthorized)}")
    if outcome.aborted:
        print(f"  - 中止（刪除前複驗不通過）：{', '.join(outcome.aborted)}")
    if outcome.unaccounted:
        print(f"  - 未走到：{', '.join(outcome.unaccounted)}")
    print(f"  - 留痕敘述：{describe_cleanup(outcome)}")
    for reason in result.blocking_reasons:
        print(f"  - 阻擋：{reason}", file=sys.stderr)
    print(f"  - 其後義務（不寫狀態面、不阻擋 release）：第 "
          f"{'、'.join(str(s) for s in SUBSEQUENT_OBLIGATION_STEPS)} 步仍待完成")


#: 第 4 步兩次寫入的人話標籤。**與 `cleanup.ACTION_LABELS` 同型**：留痕裡凡是「做了
#: 什麼」的字詞都從一張表出來，不在句子裡各寫一份。
_EFFECT_LABELS: dict[str, str] = {
    "close_issue": "已關 Issue",
    "write_release_terminal": "已寫終態",
}


def _record_actions_without_terminal(
    result: CloseoutResult,
    args: argparse.Namespace,
    effect_calls: Sequence[str],
    append_log: Callable[[str], None],
) -> bool:
    """本次真的動了東西、終態卻沒寫時，補一筆**非終態**的 Log 留痕。回傳有沒有寫。

    R3-01：`aborted` 已經移除了 worktree、甚至刪掉了本地分支，然後把效果扣住、只印
    一行 stderr 就 return。**stdout／stderr 不是 Issue Log**——換人接手或事後追查時，
    卡片上一個字都沒有，「做了什麼」重建不出來。這是 `ROADMAP §0` 目標 2 與 §4「會不
    會讓留痕重建不出來——會 → 不是細節」的字面情況。

    ⚠️ **「效果扣住」那條規則沒有被動到。** 被扣住的是第 4 步的兩次寫入（關 Issue、
    寫終態），本函式一件都不做：不呼叫 `set_field_value`，因此 owner／交付狀態／
    最後交接／iteration 一格不動；不呼叫 `issue close`；也不改 `RemoteCardFacts`。
    它只往 append-only 的 Log 加一行「本次做了什麼、被什麼擋住」。**留一筆做過什麼的
    紀錄，不等於宣告轉換完成**——這兩件事之前綁在同一個函式裡，所以扣住效果順帶扣住
    了留痕；現在分開了。

    **觸發條件讀的是動作集合，不是 `mode`**，這正是 R2 的教訓（`applied` 不代表三個
    動作都做了）。三種情況因此各自落到正確的一邊：

    - `detect_only` 恆為 `performed=() and aborted=()`（守衛擋下時 executor 直接
      return，一個動作都沒走）。世界沒被動過，重跑就能重新得到同一份判定，**沒有東西
      需要被保存**——所以不寫，也不會讓每次被擋的重跑都在卡上疊一行噪音。
    - `aborted` 必然帶著非空的 `aborted`，且通常已有 `performed`。→ 寫。
    - **`applied` 但效果被扣住**（清理回報成功、遠端分支卻還在，`observation_after.
      effect_done` 為 False）：動作發生了、終態沒寫，病灶完全相同。**照 `mode` 分流會
      漏掉這一格**，照動作集合分流不會。→ 寫。

    句子裡每一段都由實際資料產生：動作集合走 `cleanup.describe_cleanup()`（與終態留痕
    **同一個**產生點），第 4 步做了什麼走 `effect_calls`，阻擋原因走
    `result.blocking_reasons`。沒有一段是寫死的事實宣稱。

    `effect_calls` 刻意收**已發生的呼叫名稱序列**（`_CallbackEffectWriter.calls` 的
    快照）而不是 writer 本身：本函式只需要「第 4 步做了什麼」這個事實，拿到 writer
    就同時拿到了發動第 4 步的能力。收窄型別，這條路徑因此連寫都寫不出那個動作。
    """
    outcome = result.cleanup_outcome
    if not (outcome.performed or outcome.aborted):
        return False
    if "write_release_terminal" in effect_calls:
        # 終態已由第 4 步落地，而那句話裡帶的就是同一個 describe_cleanup()。再記一次
        # 只會讓同一件事在 Log 裡出現兩行，且第二行還自稱非終態。
        return False

    effects = "、".join(_EFFECT_LABELS.get(c, c) for c in effect_calls) or "無"
    reasons = "；".join(result.blocking_reasons) or "無具名阻擋原因"
    append_log(
        "cleanup by wf-cli（非終態紀錄：僅記錄本次實際動作，不代表交接或結案；"
        "owner／交付狀態／最後交接／iteration 皆未變更）；"
        f"SHA {args.source_sha}；mode={result.mode}；狀態={result.state_after}；"
        f"效果落地={'是' if result.observation_after.effect_done else '否'}；"
        f"本次第 4 步寫入：{effects}；{describe_cleanup(outcome)}；阻擋：{reasons}。"
    )
    return True


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("handoff", help="交接：狀態轉換＋source SHA＋證據欄必填")
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument("--to", required=True, help="下一位 owner（角色／帳號／模型@工具）")
    p.add_argument(
        "--next-stage",
        required=True,
        choices=[
            "requirement", "research", "planning", "backlog",
            "implementation", "review", "release",
        ],
    )
    p.add_argument("--source-sha", required=True, help="完整 40 字元 hex SHA")
    p.add_argument("--evidence", required=True, help="測試／CI／審核／決策連結或摘要")
    p.add_argument(
        "--repo-path",
        default=None,
        help="有給則唯讀驗證 source_sha 在該本機 repo 存在（不驗證是否已 push）",
    )
    p.add_argument("--status", default=None, help="覆寫依 next-stage 推導出的交付狀態")
    p.add_argument(
        "--cleanup",
        action="store_true",
        help="僅 --next-stage release：連同執行守衛化的收尾清理，全部前提成立才動手。"
        "**實際做哪幾個動作視合併方式而定**：merge 合併（分支是 main 的祖先）會移除 "
        "worktree 並刪本地與遠端分支；squash 合併只移除 worktree，分支刻意保留"
        "（cleanup.AUTHORITY_BY_PROOF）。做了什麼以本次輸出與寫回卡片的留痕為準。"
        "**兩分支契約**：給了 --repo-path 卻沒給本旗標一律拒絕（守衛看得見資源就不准"
        "製造 illegal_terminal_before_cleanup）；沒給 --repo-path 才放行，且會把"
        "「收尾清理未執行」寫進卡上留痕。⛔ 舊說法「預設不清理較安全」已被推翻——"
        "不可逆的那一半早被 AUTHORITY_BY_PROOF 以證明分級中和。需搭配 --repo-path",
    )
    p.add_argument(
        "--iteration",
        type=int,
        default=None,
        help="顯式覆寫 iteration（僅供異常修正逃生門；會印出警示，"
        "覆寫理由請說明於 --evidence；不覆寫時依 --next-stage 自動推導）",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    try:
        validate_source_sha(args.source_sha)
        validate_evidence(args.evidence)
    except ValidationError as exc:
        for e in exc.errors:
            print(f"[handoff] {e}", file=sys.stderr)
        return 2

    if args.cleanup and args.next_stage != "release":
        print("[handoff] 拒絕：--cleanup 只適用於 --next-stage release", file=sys.stderr)
        return 2
    if args.cleanup and not args.repo_path:
        print("[handoff] 拒絕：--cleanup 需要 --repo-path（守衛要在真實 repo 上驗前提）",
              file=sys.stderr)
        return 2
    if args.next_stage == "release" and not args.cleanup and args.repo_path:
        print(REPO_PATH_WITHOUT_CLEANUP_REFUSAL, file=sys.stderr)
        return 2

    if args.repo_path:
        repo_root = Path(args.repo_path)
        if not git_ops.commit_exists(repo_root, args.source_sha):
            print(
                f"[handoff] 拒絕：source_sha {args.source_sha} 在 {repo_root} 找不到對應 commit",
                file=sys.stderr,
            )
            return 2

    target = resolve_target(
        owner=args.owner, project=args.project, repo=args.repo, config=args.config
    )
    runner = default_runner
    project = resolve_project(runner, target.owner, target.project)
    fields = ensure_fields(runner, target.owner, target.project)

    items = list_items(runner, project)
    item = find_item_by_card_id(items, args.card_id)
    if not item:
        print(f"[handoff] 找不到卡 {args.card_id}", file=sys.stderr)
        return 3

    if args.status:
        new_status = args.status
    elif args.next_stage == "release":
        deployment_status = item.fields.get("部署狀態")
        if deployment_status not in (None, "—不適用", "✅已驗證"):
            print(
                "[handoff] 拒絕：需部署卡在部署 ✅已驗證 前不得 release"
                f"（目前部署狀態={deployment_status}；canonical §0）",
                file=sys.stderr,
            )
            return 4
        new_status = "🏁完成"
    elif args.next_stage == "backlog":
        tier = item.text("級別")
        if tier in BACKLOG_GATE_EXEMPT_TIERS:
            # ⚠️ 直通分支：**這裡沒有任何前提檢查，而且是刻意的**——canonical
            # AI_WORKFLOW.md §3.1 的表沒有 T0／T1 的列，沒有條文就沒有可執行的前提，
            # 硬編一個出來等於工具自己立法。與 docstring 第 4 點對「需求方批註放行」
            # 的處置同形：明說它不做什麼，不留一個看起來有檢查的空殼。
            # 印出來而不是靜靜放行，是為了讓「這裡沒有閘門」在操作當下就看得見。
            print(
                f"[handoff] 注意：級別 {tier} 直通 {STAGE_STATUS['backlog']}，"
                "**本次未做任何前身狀態檢查**"
                "（canonical §3.1 的表沒有 T0／T1 的列，故此分支無可執行的前提；"
                f"T2 以上才要求前身為 {BACKLOG_REQUIRED_PRIOR_STATUS}）",
                file=sys.stderr,
            )
        else:
            # T2／T3／T4，以及級別讀不到／為空／不在語彙內——後者一律照 T2 以上處理
            # （fail closed，理由與可達性見 docstring 第 2c 點）。
            tier_known = tier in TIERS
            current_status = item.fields.get("交付狀態")
            if current_status != BACKLOG_REQUIRED_PRIOR_STATUS:
                basis = (
                    f"級別 {tier}"
                    if tier_known
                    else f"級別讀到 {tier!r}，不在 T0–T4 語彙內，依 canonical §3.1 照 T2 以上處理"
                )
                print(
                    f"[handoff] 拒絕：{basis}；進 {STAGE_STATUS['backlog']} 時"
                    f"當下交付狀態必須是 {BACKLOG_REQUIRED_PRIOR_STATUS}"
                    f"（目前交付狀態={current_status}；canonical §3.1"
                    "「進 📥Backlog 的狀態前提依級別分流」）",
                    file=sys.stderr,
                )
                return 4
        new_status = STAGE_STATUS[args.next_stage]
    else:
        new_status = STAGE_STATUS[args.next_stage]

    current_iteration = item.fields.get("iteration")
    current_iteration = int(current_iteration) if current_iteration is not None else 0

    if args.iteration is not None:
        # 顯式覆寫逃生門：直接採用給定值，不套用自動遞增規則（供 iteration
        # counter 因例外狀況需要人工修正時使用；理由寫在既有必填的 --evidence，
        # 不另立新旗標）。
        new_iteration = args.iteration
        print(
            f"[handoff] 警示：顯式覆寫 iteration（{current_iteration} → {new_iteration}），"
            "非自動遞增路徑；此為異常修正逃生門，覆寫理由須說明於 --evidence",
            file=sys.stderr,
        )
    elif args.next_stage == "implementation":
        # 查核退回語意：handoff → implementation 代表送回修正，讀回現值＋1
        # 寫回（需求方 2026-08-05 拍板；review／release 兩個方向不遞增）。
        new_iteration = current_iteration + 1
    else:
        new_iteration = current_iteration

    ts = now_iso8601()

    def append_card_log(entry: str) -> None:
        """往卡片的 ``## Log`` 附加一行（append-only）。**只碰 body，不碰任何欄位。**

        從 `write_status_face` 抽出來的，理由不是去重：Log 留痕與狀態面寫入原本綁在
        同一個函式裡，於是「不寫終態」只能連同「不留紀錄」一起做到——那正是 R3-01
        的成因。抽開之後，兩件事可以各自決定要不要發生。
        """
        new_body = append_log_line(item.body, f"{ts} {entry}")
        set_item_body(
            runner, item.content_type, item.content_id, project, target.repo,
            item.issue_number, new_body,
        )

    def write_status_face(cleanup_note: str = "") -> None:
        set_field_value(runner, project, item.item_id, fields["owner"], args.to)
        set_field_value(runner, project, item.item_id, fields["交付狀態"], new_status)
        set_field_value(runner, project, item.item_id, fields["最後交接"], ts)
        set_field_value(runner, project, item.item_id, fields["iteration"], new_iteration)

        append_card_log(
            f"handoff by wf-cli → owner {args.to}；iteration {new_iteration}；"
            f"SHA {args.source_sha}；證據 {args.evidence}{cleanup_note}。"
        )

    if args.cleanup:
        rc = _release_with_cleanup(
            args, runner, target.repo, item, items, write_status_face, append_card_log
        )
        if rc != 0:
            return rc
    else:
        if args.next_stage == "release":
            # 此處已可斷言 not args.repo_path——帶 --repo-path 的組合在前置檢查即被拒。
            print(NO_CLEANUP_WARNING, file=sys.stderr)
            write_status_face(NO_REPO_PATH_TRACE_SUFFIX)
        else:
            write_status_face()

    print(f"[handoff] 已交接 {args.card_id} → {args.to}（狀態={new_status}，SHA={args.source_sha}）")
    return 0


def _release_with_cleanup(
    args: argparse.Namespace,
    runner: GhRunner,
    repo: str | None,
    item: ItemSnapshot,
    items: list[ItemSnapshot],
    write_status_face: Callable[[str], None],
    append_card_log: Callable[[str], None],
) -> int:
    """release 的守衛化路徑：清理先於狀態面，兩者由同一個 executor 串起來。

    這裡**不自己判斷任何前提**，也不自己決定寫入順序——那些全在
    `cleanup.execute_closeout_transition` 裡，與 reconcile 共用。本函式只負責把
    Project 上的事實翻譯成守衛要的輸入，並把第 4 步的寫入包成 effect writer。
    """
    branch, worktree = parse_branch_worktree(item.branch_worktree or "")
    if not branch:
        print(f"[handoff] 拒絕：{args.card_id} 的「分支worktree」欄沒有可解析的分支，"
              "無法界定要清理什麼（請先修欄位，不要讓守衛猜）", file=sys.stderr)
        return 2

    repo_root = Path(args.repo_path).resolve()
    worktree_path: Path | None = None
    if worktree:
        candidate = Path(worktree)
        worktree_path = candidate if candidate.is_absolute() else repo_root / candidate

    issue_open = False
    if item.issue_number is not None:
        if not repo:
            print("[handoff] 拒絕：卡由 Issue 承載但沒有 --repo，讀不到 Issue 開關狀態",
                  file=sys.stderr)
            return 2
        state = _issue_open(runner, repo, item.issue_number)
        if state is None:
            # fail closed：讀不到就不動手。猜「已關」會讓收尾自稱 completed 卻留著
            # 開著的 Issue；猜「開著」則會對已關的 Issue 再關一次。兩個都不做。
            print(f"[handoff] 拒絕：讀不到 Issue #{item.issue_number} 的開關狀態，"
                  "無法判斷第 4 步該做什麼；不猜、不動手", file=sys.stderr)
            return 5
        issue_open = state

    def close_issue() -> None:
        if item.issue_number is not None and repo:
            runner.execute(["issue", "close", str(item.issue_number), "--repo", repo])

    def write_terminal(outcome: CleanupOutcome) -> None:
        # ⚠️ 這句話**必須由 executor 實際做過的動作產生**，不得是固定字串。
        #
        # R2 之前它寫死成「worktree 與本地／遠端分支皆已不存在」，理由是「executor
        # 只在清理確實完成後才呼叫本函式」——那個理由在 squash 授權分流上線的當下就
        # 失效了：squash 路徑刻意保留分支，而這句話仍宣稱分支不存在。
        # **行為改了、敘述沒改，因為兩者不同源。** 現在同源：唯一的產生點是
        # `cleanup.describe_cleanup()`，輸入是這一輪的 `CleanupOutcome`。
        write_status_face("；" + describe_cleanup(outcome))

    writer = _CallbackEffectWriter(close_issue, write_terminal)
    target_spec = CleanupTarget(
        repo_root=repo_root,
        card_id=args.card_id,
        branch=branch,
        worktree_path=worktree_path,
    )
    result = execute_closeout_transition(
        target_spec,
        trigger="release",
        registry=registry_from_items(items),
        card_body=item.body,
        remote_facts=RemoteCardFacts(
            terminal_status_written=(item.delivery_status or "") in TERMINAL_STATUSES,
            issue_open=issue_open,
        ),
        effect_writer=writer,
    )
    _print_closeout(result, args.card_id)

    # 留痕先於 return：下面每一條 `return 5` 都是「動作已經發生、狀態面不寫」的路徑，
    # 在它們之前把實際動作記進 Log，卡片才不會對已發生的不可逆動作一個字都沒有。
    if _record_actions_without_terminal(result, args, tuple(writer.calls), append_card_log):
        print("  - 已在卡片 Log 留下非終態紀錄（本次實際動作與阻擋原因）；"
              "狀態面與 Issue 開關維持原狀")

    if result.mode != "applied":
        # 守衛擋下或中途中止：狀態面**一個字都沒寫**（第 4 步由 executor 在清理
        # 完成後才呼叫）。卡停在原本的交付狀態，Issue 維持原狀，可重跑續作。
        print(f"[handoff] 拒絕 release：收尾未完成（mode={result.mode}），"
              "狀態面未寫入；請處理上列阻擋原因後重跑", file=sys.stderr)
        return 5
    if not result.observation_after.effect_done:
        # applied 但效果沒落地：清理回報成功而實際沒完成（受保護分支、鏡像同步…）。
        # 此時 executor 刻意扣住第 4 步，這裡跟著回非 0，不讓它看起來像成功。
        print("[handoff] 拒絕 release：清理未真正完成，第 4 步已被守衛扣住，"
              "終態未落地", file=sys.stderr)
        return 5
    if writer.calls and writer.calls[-1] != "write_release_terminal":
        print("[handoff] 拒絕：第 4 步的寫入順序異常（終態不是最後一步）", file=sys.stderr)
        return 5
    if not writer.calls:
        # 卡早已在終態且清理也已完成：本次是冪等空跑，不重複寫入。
        print(f"[handoff] {args.card_id} 已在終態且清理完成，本次為冪等空跑，未重複寫入狀態面")
    return 0
