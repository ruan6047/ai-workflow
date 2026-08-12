"""``wfcli amend``：開卡後修訂卡面欄位（唯一寫入通道補上缺的那一塊）。

痛點：`open` 之後卡面就凍住了。spec 基線隨上游卡 merge 而變、驗收條件被需求方追加、
tier 開卡時填錯——這些都是常態，但 CLI 沒有入口，於是每次更正都改用 `gh issue edit`
或 Project GraphQL mutation 直接寫，繞過唯一寫入通道。2026-08-10 一天之內就繞了四次
（ai-workflow#15 的 tier、#17 的 spec 基線與 Log 渲染修復），這不是紀律問題，是工具缺口。

範圍界定（#19 驗收第 4 條）：本指令**同時**涵蓋 body 欄位與 Project 的 `級別` 欄位，
`WF-CLI-TIER-MUTATION1`（ai-workflow#12）因此併入本卡，不另行實作。

四條紅線：

- **原值必留且不得截斷**：每個被改欄位 append 一行 Log，完整記下原值與理由。Log 是
  唯一還原點，摘要不能取代全文（R1-01）；主控台輸出才做可讀性截斷。
- **不動 Log**：修訂只作用於 `## Log` 之前。排版壞到無法安全定位 Log 時一律拒絕，
  不提供修復模式——見下方「為什麼沒有排版修復」。
- **半寫入可偵測且可自癒**：`級別` 先寫並讀回驗證，再寫 body。若 body 寫入失敗導致
  欄位已改卻沒有 Log，下一次同樣的 amend 會偵測到「欄位已是目標值但 Log 沒記」，
  並只補寫 Log（R1-03）。每次執行帶 `op` 識別碼，便於跨 Log 條目對齊同一次操作。
- **完成證據不隱式沿用**：清單整份替換預設重設為未勾選；要沿用須顯式 `--preserve-checked`（R1-04）。

退出碼：0 成功／2 參數或內容檢查失敗（未寫入）／3 找不到卡／5 級別寫入後讀回驗證不符
（body 未寫，stderr 印出補記留痕的恢復指令）／6 body 在本次操作期間被其他 writer 改動／
7 body 已寫入但雙居所欄位的 Project 側補寫失敗（見下方「雙居所欄位」）。

--------------------------------------------------------------------------
核心痛點的授權模型：為什麼它不能只要 --reason
--------------------------------------------------------------------------

核心痛點餵給查核第一判準 ``core_pain_resolved``，而該判準**具否決權**
（canonical §5.1、``templates/review-prompt.md`` §2：痛點未消即 REQUEST_CHANGES，
即使驗收清單全過）。查核詞是**以卡面痛點原文組裝**的，所以「誰能改這行字」
等價於「誰能改自己的及格線」。

危害不在文字會變，而在**變更路徑弱於產生路徑**。canonical §3.1 規劃閘門三級制：
T3 的痛點須過「核心痛點三問」且**需求方批註放行**才進 📥Backlog；Initiative／T4／
不可逆須**同步對抗式質詢真對話**，且明文「不得以 brief 代替對話」。一個只要求
自由文字 ``--reason`` 的旗標，嚴格弱於建立該值的閘門——那不是補上缺口，是把
閘門拆掉。

但**不給路徑已被證明更糟**：缺口不會阻止重界定，只會把它趕到看不見的地方。
實例是本輪撞到的那張 T4 卡——需求方裁定縮小其射程時，痛點段落改不了，只能改由
新驗收條文的判準去吸收，PM 當場自記「那是繞過而非修好」；跨家族查核者隨即判為
critical blocking，逐字指出「amend 僅改驗收條件，不能更改 canonical §5.1 的第一
判準」。**該次繞道確實改變了查核者被要求判斷的東西，而痛點欄毫無痕跡。**

所以本指令採第三條路：**可改，但綁定需求方的平台身分**。

- ``--core-pain`` 必須併 ``--ruling-url``，指向**本卡 issue 的單一留言**；
- 取該留言的 **GitHub comment author**，逐字比對卡面「需求：」欄（``parse_requested_by``）；
- 追加 ``author ≠ 當前 owner`` 的排除；
- 取不到 author、URL 指向他卡、或「需求：」欄無法解析，一律 fail-closed。

這**不是新發明的標準**：``review-escalation.md`` §4 對 ``spec-narrowed`` 的
(a′) 款已要求同一件事，並明寫「這是平台可驗證身分，不是留言內文的自述」；
第 3 款要求裁定者不得是被該裁定嘉惠的人。本指令沿用該標準，不另立一套。

**已知上限（明說，不假裝相反）**：author 不可變、body 可變。具 repo 寫入權者能
編輯他人留言，故本檢查的保證止於「沒有人事後改寫需求方的裁定」。消除它需要
結構化事件承載授權（``review-escalation.md`` §4 (b′-1)），那屬 checkpoint writer
的射程，不在本指令。

**本指令關不掉的洞（指名記下，因為它是唯一出路）**：``review.py`` 的裁決留言
只寫 ``core_pain_resolved：yes|no``，**不寫它所判斷的痛點原文**。裁決事件是
append-only 且不可改，它所依據的前提卻可變——痛點一經更正，**歷史上每一筆
``core_pain_resolved`` 都失去可回溯解讀性**：沒有人能分辨那個 yes/no 是在判哪
一個問題。授權綁定擋得住「未經需求方改寫」，擋不住這件事。唯一的修法是讓
裁決事件快照痛點原文或其 hash，那屬 ``review.py``（另一張卡持有），本卡不得動。

--------------------------------------------------------------------------
級別降級的不對稱：為什麼與核心痛點同機制、但理由不同、觸發更窄
--------------------------------------------------------------------------

``--tier`` 先前對升降級完全對稱。升級是安全方向（加保護），降級不是：
**T4→T2 會移除紅線卡的跨家族／人工 sign-off 要求**，而這正是本卡開卡時就自己
寫下的風險，交付時未被兌現。

但降級的授權理由**不同於核心痛點**，不可直接套用：

- 核心痛點的授權來源是「**需求方是問題的擁有者**」——那行字描述的是他要解的問題。
- 級別的授權來源是「**需求方是被移除閘門的操作者**」——canonical §3.1 把 T3 的
  三問放行與 T4／Initiative 的同步質詢都交給需求方**親自**執行。降級移除的是
  他本人操作過的閘門。

兩者恰好指向同一個人，所以用同一個機制；但**觸發範圍更窄**：只有原級別為
T3／T4 時才要裁定留痕（見 ``card.tier_downgrade_needs_ruling``）。T2 以下沒有
需求方閘門可移除，只需 ``--reason``，Log 仍逐字標記為降級以利稽核。

刻意**不**要求「降級須無既有查核紀錄」：那需要解析 timeline 的裁決事件，屬
doctor／review 的射程，且會讓本指令與 marker 契約耦合。授權綁定已足以讓降級
可歸屬，剩下的由人判斷。

--------------------------------------------------------------------------
雙居所欄位：body 與 Project 欄位各存一份時的寫入順序取捨
--------------------------------------------------------------------------

卡面欄位有三種居所，而它決定了實作風險，與「筆誤 vs 重界定」的治理軸正交：

===================  ======  ==============  ==============
欄位                 body    Project 欄位    進 Ledger 快照
===================  ======  ==============  ==============
核心痛點             唯一    無              否
spec 基線／驗收／驗證 唯一    無              否
級別                 無      唯一            是
資源宣告             有      有              **兩者都讀**
Initiative           有      有              是
===================  ======  ==============  ==============

**已知缺陷（本次修復）**：``snapshot.build_rows`` 的 ``resource_summary`` 讀
**Project 欄位**，``resource_db_scope``／``resources`` 讀 **body 區塊**；而本指令
先前只改 body，從不寫 ``資源宣告`` 欄位。後果不是潔癖問題而是**安全問題**：
本輪四次 ``--resources`` 全部只落 body，其中三張卡的欄位比實際**寬**（保守方向），
但有一張 T4 卡的欄位比實際**窄**——看板顯示它只佔一份文件，實際持有八個檔，
含 ``cleanup.py``／``doctor.py``／``handoff_cmd.py``。那是 fail-open 方向：任何靠
看板／Ledger 判斷佔用的人都會低估它。（``assign`` 的交集檢查讀 body，所以擋派工
是對的；壞的是看板那一面。）該案例已釘進 ``test_amend.py`` 的迴歸測試。

**取捨（是取捨，不是解法）**：雙居所欄位**沒有**任何寫入順序能同時做到
(a) 首寫自描述、(b) 中途崩潰不留下不一致。必須擇一並為另一種失敗提供偵測：

- **級別**（單居所）現行為「欄位先寫、讀回驗證、body 後寫」。欄位失敗＝乾淨中止，
  代價是**首寫不自描述**（該判定見既有的動詞稽核卡）。
- **雙居所欄位**本次採**相反**順序：**body 先寫**（body 攜帶 Log 行，故首寫自描述、
  不新增第三個不自描述的首寫），Project 欄位後寫並讀回驗證。失敗模式因此變成
  「body 已更新、欄位過期」——**與現存的四張卡完全同型**，而那正是已經有偵測
  慣用法的那一種：``_tier_change_logged`` 對級別做的事（比對 Log 有沒有記過這筆
  變更），這裡由「欄位值 ≠ body 導出值」直接偵測，更強——不需要靠 Log 推測，
  兩個居所的實際值可以直接比。

因此**重跑即修復**：``--resources`` 帶與 body 相同的值時，先前一律拒為 no-op；
現在會先比對 Project 欄位，只有**兩個居所都已一致**才拒絕，否則走欄位補寫路徑
並留 Log。這讓已經不同步的卡有一條合規的收斂路徑，不必手改 Project UI。

--------------------------------------------------------------------------
未納入的欄位與理由（讓下一個人拿得到判準，而不是只拿到「沒做」）
--------------------------------------------------------------------------

- **服務的原始目標**：不補。它是**鏈級**欄位（canonical §3.3「這根鏈最終要解的
  問題」），是鏈式停損兩問的錨。單卡改會與同鏈其他卡去同步，而 CLI 沒有鏈的
  視野。它的變更本質是 ``baseline-cascade.md`` 的 ``invalidated``（退回 Gate 或
  由需求方裁定停止），不是欄位編輯。
- **鏈深**：不補。降鏈深等於規避 canonical §3.3 的硬上限（>2 強制整鏈重審，
  「預設答案是擱置或降級，不是繼續鑽」）。真的需要改，代表該重審，不是該改欄位。
- **feature（卡片標題）**：不補。``card_id`` 取自 Project 的 ``卡ID`` TEXT 欄位而
  非標題（``find_item_by_card_id``），全 CLI 對 ``.title`` 零消費者，故標題錯誤
  **零機械後果**，只誤導人讀。而補它必須新增 ``project.py`` 的標題寫入函式
  （真實 Issue 與 draft 走兩條不同的 ID 命名空間），超出本卡宣告的寫入集。

  **這個裁定的代價已經實現，記在這裡以免下一個人以為它是免費的**：本卡自己的
  標題描述的是一個**已由他卡交付**的能力，而正因為 ``feature`` 沒有更正路徑，
  該標題永遠修不掉。最後的處置不是修好它，而是**繞過**——結案本卡、以正確標題
  另開一張承接殘餘射程。也就是說，「不補 feature」的實際代價是：標題一旦錯，
  修法只剩開新卡。若日後這種情形變得頻繁，本裁定就該重審。

**併發保證的界線（誠實聲明）**：本指令在寫入前會重讀並比對 body，但那**不是**原子的
compare-and-swap——GitHub 對 issue body 沒有條件寫入。重讀只把競態窗口從「整條指令
執行期間」縮到「重讀與寫入之間」。真正的解法是可序列化的唯一 writer 或底層條件寫入，
不在本指令能提供的保證內。
"""

from __future__ import annotations

import argparse
import re
import sys
import uuid

from ..card import (
    TIERS,
    AmendError,
    RequesterUnparseable,
    amend_acceptance,
    amend_core_pain,
    amend_initiative,
    amend_resource_block,
    amend_spec_baseline,
    amend_verification,
    append_log_line,
    is_tier_downgrade,
    now_iso8601,
    parse_requested_by,
    tier_downgrade_needs_ruling,
)
from ..config import add_target_args, resolve_target
from ..gh import default_runner
from ..project import (
    add_issue_comment,
    ensure_fields,
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_field_value,
    set_item_body,
)
from ..resources import ResourceDeclaration, ResourceDeclarationError, parse_block, render_block


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "amend", help="開卡後修訂卡面：spec 基線／驗收／驗證／資源宣告／級別（原值寫入 Log）"
    )
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument("--reason", required=True, help="修訂理由；會寫進 Log，不得為空")
    p.add_argument("--spec-baseline", default=None)
    p.add_argument(
        "--acceptance",
        action="append",
        default=None,
        help="可重複；給定時整份取代驗收條件（預設全部重設為未勾選）",
    )
    p.add_argument(
        "--verification",
        action="append",
        default=None,
        help="可重複；給定時整份取代驗證項目（預設全部重設為未勾選）",
    )
    p.add_argument(
        "--preserve-checked",
        action="store_true",
        help="清單替換時，文字未變的項目沿用原勾選狀態。預設不沿用："
        "整份替換代表驗收語意已變動，文字相同不保證仍然成立",
    )
    p.add_argument(
        "--db-scope",
        default=None,
        help="改資源宣告的 db_scope；與 --resources 至少給一個才會動資源宣告區塊",
    )
    p.add_argument(
        "--resources",
        default=None,
        help="逗號分隔資源清單，整份取代；空字串代表清空",
    )
    p.add_argument("--tier", choices=TIERS, default=None, help="更正級別（Project 欄位）")
    p.add_argument(
        "--initiative",
        default=None,
        help="更正 Initiative 父卡（body 標頭行＋Project 欄位雙面同寫）；無父卡填 `—`",
    )
    p.add_argument(
        "--core-pain",
        default=None,
        help="更正核心痛點。**須併 --ruling-url**，且不得與其他欄位旗標同一次調用："
        "此欄餵給具否決權的 core_pain_resolved，一次調用＝一次治理裁定",
    )
    p.add_argument(
        "--ruling-url",
        default=None,
        help="需求方裁定留言的 URL（本卡 issue 的單一留言，形如 "
        "https://github.com/<owner>/<repo>/issues/<n>#issuecomment-<id>）。"
        "其 GitHub comment author 須逐字等於卡面「需求：」欄；"
        "核心痛點更正與 T3／T4 降級必填",
    )
    p.add_argument(
        "--record-unlogged-change",
        action="store_true",
        help="半寫入補救：Project 級別欄已是 --tier 指定值但 Log 無對應紀錄時，"
        "只補寫 Log、不改欄位。CLI 分不出「開卡時就是這個值」與「先前半寫入」，"
        "故此判斷由操作者顯式承擔",
    )
    p.add_argument(
        "--escalate",
        action="store_true",
        help="偵測到 body 排版損壞而拒絕時，在該 Issue 留言記錄求助（不碰 body、"
        "不改交付狀態），讓人或 AI 接手。stderr 是瞬時的，卡面留言才是持久紀錄",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="只驗證與列印將寫入的變更，不連 GitHub 寫入任何狀態",
    )
    p.set_defaults(func=run)


def _fold(text: str) -> str:
    """Log 是單行條目，原值摺成一行——但**不截斷**：Log 是唯一還原點。"""
    return " ".join(str(text).split())


def _short(text: str, limit: int = 100) -> str:
    """只給主控台看的可讀摘要；永遠不進 Log。"""
    folded = _fold(text)
    return folded if len(folded) <= limit else folded[:limit] + f"…（全文 {len(folded)} 字，見 Log）"


# 排版損壞沒有自動修復（見 README「為什麼沒有排版修復」）。但「沒有自動修復」不等於
# 「沒有出路」——工具不改 body，卻必須讓人知道**怎麼修**、以及**機械驗證的必要條件
# 是否通過**。工具能證明的是「只改了那一處」，不是「那一處是對的」；語意判斷留給人。
_LAYOUT_MARKERS = ("不是獨立標題行", "個 `## Log` 標題")

# 第 3 步的驗證指令抽成常數，讓**測試執行的就是印給使用者的那一份**。先前 runbook
# 只存在於字串裡、從沒被實跑過，結果同時出兩個錯：引用了一個從未建立的 orig.md，
# 以及用「刪掉全文所有字面 \n 再比」當判準——那會把 Log 內文合法的字面 \n 一併刪掉，
# 使 #17 的正確修復被誤判為內容遭竄改。
#
# 現在的判準精確得多：修好的 body 必須**恰好等於**原文做一次目標替換後的結果。
# 任何其他改動（多刪一個字、順手改錯字）都會被抓到。這與被移除的自動修復同樣的
# 邏輯，差別在它只**驗證**、不寫入——檢查失敗是安全的，寫錯才不是。
_LAYOUT_VERIFY_SNIPPET = r"""python3 - /tmp/orig.md /tmp/body.md <<'PY'
import sys
o = open(sys.argv[1]).read(); n = open(sys.argv[2]).read()
t = "\\n## Log\\n\\n"; f = "\n\n## Log\n\n"
c = o.count(t)
if c != 1:
    print(f"NG：原文有 {c} 處候選標記，本程序只處理恰好 1 處。請人工判斷後個別處理")
elif o.replace(t, f, 1) != n:
    print("NG：除了那一處之外還動到別的地方，請重做")
else:
    print("必要條件通過：只還原了那一處候選標記。")
    print("⚠️ 這不是安全證明——本檢查無法判斷它是否真的是 Log 標題。")
    print("   請自行確認它不在 code fence／inline code／內文引用中，並審閱完整 diff。")
PY"""

_LAYOUT_RUNBOOK = """
[amend] 這是 body 排版損壞，本指令刻意不自動修（理由見 cli/README.md）。人工程序：

  ⚠️ 下列所有機械檢查都是**必要條件，不是安全證明**。是否真的修對了，最終由你判斷。

  1. 取出現行 body，並另存一份原文副本供比對：
     gh issue view <N> --repo <owner/repo> --json body --jq .body > /tmp/body.md
     cp /tmp/body.md /tmp/orig.md
  2. **人工判斷（無法機械化）**：確認 body 中的 `\\n## Log\\n\\n` 候選標記確實是被寫壞的
     Log 標題，而不是 code fence 內的範例、inline code 引用、或內文提到的字樣。
     若有多處候選，逐一判斷；本程序的檢查只處理恰好一處。
  3. 編輯 /tmp/body.md：把該處的字面 \\n 改回真換行。
     **只改那一處，不動任何其他字元**（Log 內文提到的字面 \\n 是內容，不要碰）。
  4. 檢查「只改了那一處」（必要條件）：
     {verify}
  5. **審閱完整 diff**——這一步不可省略，它是唯一能看見全部改動的地方：
     diff /tmp/orig.md /tmp/body.md
  6. 寫回：gh issue edit <N> --repo <owner/repo> --body-file /tmp/body.md
  7. 確認 amend 不再回報排版錯誤（必要條件，非充分；不寫入任何狀態）：
     wfcli amend {card_id} --repo <owner/repo> --reason 驗證排版 --dry-run --spec-baseline '<現值>'
     注意：它只證明「找得到唯一一個 Log 標題」，不證明那個標題在對的位置，
     也不保證 body 其他地方沒有殘留的字面 \\n。
  8. 在該 Issue 留言記錄這次人工寫入與原因——它同時是「某處仍在繞過 wfcli」的訊號。
""".rstrip()


def _is_layout_failure(exc: Exception) -> bool:
    return any(marker in str(exc) for marker in _LAYOUT_MARKERS)


def _escalate_layout_failure(runner, target, item, args, exc: Exception) -> None:
    """把排版損壞留成 Issue 留言，讓人或 AI 接手。

    stderr 是瞬時的：腳本裡跑 amend 失敗，runbook 捲過去就沒了，卡面不留痕跡，
    沒人知道有卡卡住。留言是**唯一不必碰 body 就能留下持久紀錄**的通道——正好
    避開「body 已經壞了、再寫更危險」這個處境。

    刻意**不**改交付狀態：轉 ⏸阻塞 是 lifecycle 決定，屬 PM 的判斷，不由一個
    修訂指令代勞。本函式只負責讓問題可被看見與被指派。
    """
    if args.dry_run:
        # --dry-run 承諾零遠端寫入，這條承諾不因為「只是留言」而破例：留言同樣是
        # 對 GitHub 的寫入，而 dry-run 的用途正是「先看看會發生什麼」。
        print(
            "[amend] --dry-run：略過 --escalate 的留言（dry-run 不做任何遠端寫入）。"
            "要留下求助紀錄請去掉 --dry-run 重跑",
            file=sys.stderr,
        )
        return
    if item.content_type != "Issue" or item.issue_number is None or not target.repo:
        print(
            "[amend] --escalate 需要真實 repo Issue（draft item 沒有可留言的 timeline）；"
            "本次僅印出 runbook，未留下持久紀錄",
            file=sys.stderr,
        )
        return
    comment = (
        f"<!-- wf-amend-blocked:v1 card_id={args.card_id} check=log-layout -->\n"
        f"## ⏸ `wfcli amend` 因 body 排版損壞而拒絕\n\n"
        f"- 卡：`{args.card_id}`\n"
        f"- 偵測到的問題：{exc}\n"
        f"- 嘗試的修訂理由：{_fold(args.reason)}\n"
        f"- 時間：{now_iso8601()}\n\n"
        "**本指令刻意不自動修復 body**（理由見 `cli/README.md`「為什麼沒有排版修復」）。"
        "在修好之前，這張卡的任何 `wfcli amend` 都會被拒絕。\n\n"
        "### 需要人或 AI 接手\n"
        f"```text{_LAYOUT_RUNBOOK.format(card_id=args.card_id, verify=_LAYOUT_VERIFY_SNIPPET)}\n```\n\n"
        "修復後請在本串回覆，並一併說明 body 為何會被繞過 `wfcli` 直接寫入——"
        "排版損壞本身就是那條繞道仍然存在的證據。"
    )
    try:
        add_issue_comment(runner, target.repo, item.issue_number, comment)
    except Exception as post_exc:  # noqa: BLE001 - 留言失敗不得蓋掉原本的拒收語意
        # 升級是**盡力而為**的附加動作。它失敗時最糟的處理就是讓例外逸出：呼叫端會
        # 收到非預期的退出碼，而 stack trace 會把上面那份 runbook 沖掉——使用者因此
        # 同時失去自動紀錄與人工出路。這裡改為警告並保留退出碼 2。
        print(
            f"[amend] --escalate 留言失敗（{type(post_exc).__name__}: {post_exc}）；"
            "拒收結論不變，請依上方 runbook 人工處理並自行留痕",
            file=sys.stderr,
        )
        return
    print(
        f"[amend] --escalate：已在 #{item.issue_number} 留下求助紀錄（body 與交付狀態均未變動）",
        file=sys.stderr,
    )


def _tier_change_logged(body: str, tier: str) -> bool:
    """body 的 Log 是否已記過「級別 → tier」這筆變更。

    逐行比對且不綁定完整格式：Log 行含 op 識別碼，欄位名又有「級別」與
    「級別（補記先前未留痕的變更）」兩種寫法。綁死字面格式會讓偵測器認不出
    自己寫的紀錄，把真正的 no-op 誤判成半寫入而重複「自癒」。
    """
    needle = f"→ 新值「{tier}」"
    return any(
        "amend by wf-cli" in line and "→ 級別" in line and needle in line
        for line in body.splitlines()
    )


# 只認完整、單一留言的 URL 形狀。與 review-escalation.md §4 第 5 款同一個判準：
# 「必須解析為本卡 issue 的單一留言 URL；無法解析、指向他卡、指向非留言資源
# （含任意站外 URL）者，該筆無效。」
_ISSUECOMMENT_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/issues/"
    r"(?P<issue>\d+)#issuecomment-(?P<comment_id>\d+)$"
)


class RulingError(ValueError):
    """裁定留痕無法機械核對。一律 fail-closed，不得以自述成立。"""


def _resolve_ruling_author(runner, target, item, ruling_url: str) -> tuple[str, str]:
    """核對裁定留言屬於本卡，並回傳 (comment_id, GitHub comment author)。

    只走**唯讀** API。取 author 而非讀內文，是因為 author 是平台可驗證身分，
    內文是自述——``review-escalation.md`` §4 (a′) 對此已有明文，本函式沿用。
    """
    match = _ISSUECOMMENT_URL_RE.match(ruling_url.strip())
    if not match:
        raise RulingError(
            f"--ruling-url 不是單一留言 URL：{ruling_url!r}；"
            "須形如 https://github.com/<owner>/<repo>/issues/<n>#issuecomment-<id>"
        )
    if item.content_type != "Issue" or item.issue_number is None:
        raise RulingError(
            "本卡是 draft item，沒有可指向的 issue 留言 timeline；"
            "授權綁定不可用，拒絕更正（draft 卡請先轉為真實 Issue）"
        )
    url_repo = f"{match.group('owner')}/{match.group('repo')}"
    if not target.repo or url_repo != target.repo:
        raise RulingError(
            f"--ruling-url 指向 {url_repo}，與本次目標 repo {target.repo!r} 不符；"
            "裁定必須落在本卡自己的 issue"
        )
    if int(match.group("issue")) != item.issue_number:
        raise RulingError(
            f"--ruling-url 指向 issue #{match.group('issue')}，本卡是 "
            f"#{item.issue_number}；指向他卡的裁定不成立"
        )
    comment_id = match.group("comment_id")
    try:
        payload = runner.run_json(["api", f"/repos/{url_repo}/issues/comments/{comment_id}"])
    except Exception as exc:
        # 任何讀取失敗都轉成 RulingError：取不到 author 一律 fail-closed，
        # 不得以「讀不到就當作成立」放行（review-escalation.md §4 (c′) 同向）。
        raise RulingError(
            f"讀取裁定留言 {comment_id} 失敗（{type(exc).__name__}: {exc}）；"
            "無法核對 author，拒絕更正"
        ) from exc
    user = (payload or {}).get("user") or {}
    author = user.get("login") if isinstance(user, dict) else None
    if not author:
        raise RulingError(
            f"裁定留言 {comment_id} 取不到 GitHub comment author；"
            "無法機械核對授權，拒絕更正"
        )
    return comment_id, str(author)


def _authorize_by_requester_ruling(runner, target, item, args, what: str) -> str:
    """核對「這次更正確經需求方以其平台身分裁定」，回傳寫進 Log 的授權註記。

    三道檢查，缺一即拒（對齊 ``review-escalation.md`` §4 (a′) 與第 2、3 款）：

    1. 卡面「需求：」欄可解析（``parse_requested_by``，fail-closed）；
    2. 裁定留言的 GitHub comment author **逐字等於**該帳號；
    3. 該 author **不等於本卡當前 owner**——裁定者不得是被該裁定嘉惠的人。
    """
    if not args.ruling_url:
        raise RulingError(
            f"{what}須併 --ruling-url 指向需求方的裁定留言；"
            "此欄的變更是治理事件，不接受只有 --reason 的自述"
        )
    requester = parse_requested_by(item.body)
    comment_id, author = _resolve_ruling_author(runner, target, item, args.ruling_url)
    if author != requester:
        raise RulingError(
            f"裁定留言 {comment_id} 的 GitHub author 是 {author!r}，"
            f"卡面「需求：」欄是 {requester!r}，兩者不符；"
            f"{what}的授權只能來自需求方本人"
        )
    owner = (item.text("owner") or "").strip()
    if owner and author == owner:
        raise RulingError(
            f"裁定留言 author {author!r} 逐字等於本卡當前 owner；"
            "裁定者不得是被該裁定嘉惠的人（review-escalation.md §4 第 3 款同向）"
        )
    return (
        f"依需求方 {author} 於 {args.ruling_url} 的裁定"
        f"（GitHub comment author 已逐字核對，非留言內文自述）"
    )


def run(args: argparse.Namespace) -> int:  # noqa: C901 - 逐旗標的前置檢查本就是平鋪的
    if not args.reason.strip():
        print("[amend] 拒絕：--reason 不得為空（每次修訂都要能回答為什麼）", file=sys.stderr)
        return 2

    wants_resources = args.db_scope is not None or args.resources is not None
    field_flags = [
        args.spec_baseline,
        args.acceptance,
        args.verification,
        args.tier,
        args.initiative,
        args.core_pain,
    ]
    wants_fields = any(f is not None for f in field_flags) or wants_resources

    if not wants_fields:
        print("[amend] 拒絕：沒有指定任何要修訂的欄位", file=sys.stderr)
        return 2

    # 核心痛點獨占一次調用：op 識別碼與一次治理裁定必須 1:1。混在其他欄位裡改，
    # 會讓 Log 上同一個 op 同時承載「需求方裁定的問題重界定」與「順手改的筆誤」，
    # 稽核者無從分辨那份 --ruling-url 授權的究竟是哪一項。
    if args.core_pain is not None:
        others = [f for f in field_flags if f is not None and f is not args.core_pain]
        if others or wants_resources:
            print(
                "[amend] 拒絕：--core-pain 不得與其他欄位旗標同一次調用；"
                "此欄餵給具否決權的 core_pain_resolved，一次調用＝一次治理裁定，"
                "請單獨執行",
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
        print(f"[amend] 找不到卡 {args.card_id}", file=sys.stderr)
        return 3

    op_id = uuid.uuid4().hex[:8]
    body = item.body
    # (欄位, 原值, 新值, 授權註記或 None)
    changes: list[tuple[str, str, str, str | None]] = []
    tier_needs_field_write = False
    old_tier = item.text("級別")
    # 雙居所欄位在 body 寫入**之後**要補寫的 Project 欄位：{欄位名: 目標值}
    pending_field_writes: dict[str, str] = {}

    # ---- 授權綁定：必須在任何寫入之前完成，且只走唯讀 API ----
    #
    # 放在這裡而不是各欄位的分支裡，是為了讓「哪些欄位需要裁定」成為一份可讀的
    # 清單，而不是散在條件式中——漏掉一個就等於少一道閘門。
    ruling_note: str | None = None
    needs_ruling_for: list[str] = []
    if args.core_pain is not None:
        needs_ruling_for.append("核心痛點更正")
    if args.tier is not None and tier_downgrade_needs_ruling(old_tier, args.tier):
        needs_ruling_for.append(f"級別由 {old_tier} 降為 {args.tier}（移除需求方操作過的規劃閘門）")
    if needs_ruling_for:
        try:
            ruling_note = _authorize_by_requester_ruling(
                runner, target, item, args, "、".join(needs_ruling_for)
            )
        except (RulingError, RequesterUnparseable) as exc:
            print(f"[amend] 拒收（未寫入任何狀態）：{exc}", file=sys.stderr)
            return 2
    elif args.ruling_url:
        # 刻意**不**把未經核對的 URL 寫進 Log：一個指標不證明它指向什麼，
        # 而 Log 裡出現裁定連結會讓稽核者誤以為它已被核對過
        # （review-escalation.md §4 第 5 款「此欄只是形狀檢查」的同型陷阱）。
        print(
            "[amend] 提示：本次修訂不需要需求方裁定授權，--ruling-url 未被核對，"
            "亦不寫入 Log（避免留下看似已授權的痕跡）",
            file=sys.stderr,
        )

    try:
        if args.spec_baseline is not None:
            body, old = amend_spec_baseline(body, args.spec_baseline)
            changes.append(("spec 基線", old, args.spec_baseline, None))
        if args.initiative is not None:
            body, old = amend_initiative(body, args.initiative)
            changes.append(("Initiative", old, args.initiative, None))
            pending_field_writes["Initiative"] = args.initiative
        if args.core_pain is not None:
            body, old = amend_core_pain(body, args.core_pain)
            changes.append(("核心痛點", old, args.core_pain, ruling_note))
        if args.acceptance is not None:
            body, old = amend_acceptance(
                body, args.acceptance, preserve_checked=args.preserve_checked
            )
            changes.append(("驗收條件", old, "；".join(args.acceptance), None))
        if args.verification is not None:
            body, old = amend_verification(
                body, args.verification, preserve_checked=args.preserve_checked
            )
            changes.append(("驗證", old, "；".join(args.verification), None))
        if wants_resources:
            current = parse_block(item.body)
            db_scope = args.db_scope if args.db_scope is not None else current.db_scope
            resources = (
                [r.strip() for r in args.resources.split(",") if r.strip()]
                if args.resources is not None
                else current.resources
            )
            decl = ResourceDeclaration(db_scope=db_scope, resources=resources)
            summary = decl.summary()
            current_field = item.text("資源宣告")
            if decl != current:
                # 一般路徑：body 與 Project 欄位都要更新。
                body, old = amend_resource_block(body, render_block(decl))
                changes.append(("資源宣告", old, summary, None))
                pending_field_writes["資源宣告"] = summary
            elif current_field != summary:
                # body 已是目標值但 Project 欄位過期——這正是先前「只寫 body」
                # 留下的不同步。不再一律拒為 no-op，改走欄位補寫路徑讓它收斂。
                changes.append(
                    (
                        "資源宣告（Project 欄位補寫；body 已是目標值）",
                        current_field or "（未設定）",
                        summary,
                        None,
                    )
                )
                pending_field_writes["資源宣告"] = summary
            else:
                raise AmendError(
                    "資源宣告與現值相同（body 與 Project 欄位皆已一致）；"
                    "拒絕寫入不實的修訂留痕"
                )
    except (AmendError, ResourceDeclarationError) as exc:
        print(f"[amend] 拒收（未寫入任何狀態）：{exc}", file=sys.stderr)
        if _is_layout_failure(exc):
            print(_LAYOUT_RUNBOOK.format(card_id=args.card_id, verify=_LAYOUT_VERIFY_SNIPPET), file=sys.stderr)
            if args.escalate:
                _escalate_layout_failure(runner, target, item, args, exc)
        elif args.escalate:
            print(
                "[amend] --escalate 只對排版損壞生效；本次是一般拒收，不留升級紀錄",
                file=sys.stderr,
            )
        return 2

    if args.tier is not None:
        already_logged = _tier_change_logged(item.body, args.tier)
        if old_tier == args.tier and not args.record_unlogged_change:
            # 「欄位已是目標值且 Log 沒記」有兩種可能：開卡時就是這個值（正常
            # no-op），或先前 amend 寫完欄位後 body 寫入失敗（半寫入）。CLI 分不
            # 出來，也不該猜——猜錯就會把正常的 no-op 記成一筆不存在的變更。
            # 因此預設拒絕，並在確實可能是半寫入時提示補記旗標，由操作者承擔判斷。
            hint = (
                ""
                if already_logged
                else "；若這是先前 amend 寫完欄位卻 body 寫入失敗所致，"
                "請加 --record-unlogged-change 補記留痕"
            )
            print(
                f"[amend] 拒收（未寫入任何狀態）：級別已是 {args.tier}"
                f"，拒絕寫入不實的修訂留痕{hint}",
                file=sys.stderr,
            )
            return 2
        if args.record_unlogged_change:
            if old_tier != args.tier:
                print(
                    f"[amend] 拒絕：--record-unlogged-change 只補留痕、不改欄位，"
                    f"但級別現為 {old_tier!r} 而非 {args.tier}；請改用一般 --tier",
                    file=sys.stderr,
                )
                return 2
            if already_logged:
                print(
                    f"[amend] 拒絕：級別 {args.tier} 的變更 Log 已存在，無需補記",
                    file=sys.stderr,
                )
                return 2
            changes.append(
                (
                    "級別（補記先前未留痕的變更）",
                    "（Project 欄位已是目標值但 Log 無紀錄；操作者判定為先前半寫入）",
                    args.tier,
                    None,
                )
            )
        else:
            tier_needs_field_write = True
            # 降級逐字標記在欄位名裡：稽核者掃 Log 時不必自己比對 T 值大小，
            # 也讓「這是降級」成為留痕的一部分而非讀者的推論。
            label = "級別（降級）" if is_tier_downgrade(old_tier, args.tier) else "級別"
            changes.append((label, old_tier or "（未設定）", args.tier, ruling_note))

    timestamp = now_iso8601()
    for field_name, old, new, note in changes:
        authority = f"；授權 {_fold(note)}" if note else ""
        body = append_log_line(
            body,
            f"{timestamp} amend by wf-cli（op {op_id}）→ {field_name}："
            f"原值「{_fold(old)}」→ 新值「{_fold(new)}」；理由 {_fold(args.reason)}{authority}。",
        )

    if args.dry_run:
        print(f"[amend] dry-run（未寫入任何狀態）：{args.card_id} 將修訂 {len(changes)} 個欄位")
        for field_name, old, new, note in changes:
            print(f"  - {field_name}：「{_short(old)}」→「{_short(new)}」")
            if note:
                print(f"    授權：{_short(note)}")
        return 0

    # 級別先寫並讀回驗證，body 後寫。這個順序讓「欄位寫失敗」變成乾淨中止
    # （body 未動、無半寫入）；而「欄位成功、body 失敗」留下的不一致，由下一次
    # 同樣的 amend 依 _tier_change_logged 偵測並只補寫 Log 自癒。
    if tier_needs_field_write:
        set_field_value(runner, project, item.item_id, fields["級別"], args.tier)
        after = find_item_by_card_id(list_items(runner, project), args.card_id)
        actual_tier = after.text("級別") if after else None
        if actual_tier != args.tier:
            print(
                f"[amend] 寫入後讀回驗證失敗：級別預期 {args.tier}，實際 {actual_tier!r}。\n"
                "  body 未寫入，卡片現在可能處於「欄位已改、Log 沒記」。恢復步驟：\n"
                f"  1. 確認 Project 的級別實際值。\n"
                f"  2. 若已是 {args.tier}，以下列指令補記留痕（只補 Log、不再改欄位）：\n"
                f"     wfcli amend {args.card_id} --tier {args.tier} "
                f"--record-unlogged-change --reason '<說明先前寫入為何中斷>'\n"
                f"  3. 若仍是舊值，直接重跑原本的 amend 即可。\n"
                "  注意：--record-unlogged-change 是操作者的宣告，不是系統的自動證明。",
                file=sys.stderr,
            )
            return 5

    # 寫入前再讀一次，擋掉「讀取後、寫入前被他人改動」而整份覆寫的情形。
    # 這**不是**原子的 compare-and-swap：GitHub 對 issue body 沒有條件寫入，本檢查
    # 與 set_item_body 之間仍有殘餘競態視窗。它只把競態窗口從「整條指令執行期間」
    # 縮到「這兩次呼叫之間」，不宣稱完全防護——真正的解法是可序列化的唯一 writer
    # 或底層條件寫入，不在本指令能提供的保證內。
    fresh = find_item_by_card_id(list_items(runner, project), args.card_id)
    if fresh is None or fresh.body != item.body:
        print(
            "[amend] 中止：body 在本次操作期間已被其他 writer 改動，"
            "繼續寫入會整份覆寫對方的內容。請重新讀取後再跑一次。",
            file=sys.stderr,
        )
        return 6

    set_item_body(
        runner, item.content_type, item.content_id, project, target.repo, item.issue_number, body
    )

    # ---- 雙居所欄位：body 之後補寫 Project 側，並讀回驗證 ----
    #
    # 順序與級別相反（級別是欄位先寫），理由見模組 docstring「雙居所欄位」：
    # body 攜帶 Log 行，body 先寫使**首寫自描述**，不新增第三個不自描述的首寫。
    # 代價是失敗模式變成「body 已更新、欄位過期」——但那一種是**可直接偵測**的
    # （兩個居所的實際值可以互比），且重跑本指令即收斂，不需要 --record-unlogged-change
    # 那種由操作者宣告的補救。這是取捨不是解法：雙居所欄位沒有任何順序能同時
    # 做到首寫自描述與崩潰不留不一致。
    if pending_field_writes:
        stale: list[str] = []
        for field_name, value in pending_field_writes.items():
            set_field_value(runner, project, item.item_id, fields[field_name], value)
        after = find_item_by_card_id(list_items(runner, project), args.card_id)
        for field_name, value in pending_field_writes.items():
            actual = after.text(field_name) if after else None
            if actual != value:
                stale.append(f"{field_name}（預期 {value!r}，實際 {actual!r}）")
        if stale:
            print(
                "[amend] body 已寫入，但下列 Project 欄位補寫後讀回不符："
                + "；".join(stale)
                + "。\n"
                "  卡片現在處於「body 已更新、Project 欄位過期」——這是可直接偵測的\n"
                "  不一致（兩個居所的值可互比），且**重跑同一條 amend 即會收斂**：\n"
                f"     wfcli amend {args.card_id} --reason '<說明先前補寫為何中斷>' <原本的旗標>\n"
                "  重跑時 body 已是目標值，本指令會走欄位補寫路徑而非拒為 no-op。",
                file=sys.stderr,
            )
            return 7

    print(f"[amend] 已修訂 {args.card_id}（op {op_id}，{len(changes)} 個欄位，原值已完整寫入 Log）")
    for field_name, old, new, note in changes:
        print(f"  - {field_name}：「{_short(old, 80)}」→「{_short(new, 80)}」")
        if note:
            print(f"    授權：{_short(note, 80)}")
    return 0
