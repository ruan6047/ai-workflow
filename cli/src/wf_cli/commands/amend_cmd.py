"""``wfcli amend``：開卡後修訂卡面欄位（唯一寫入通道補上缺的那一塊）。

痛點：`open` 之後卡面就凍住了。spec 基線隨上游卡 merge 而變、驗收條件被需求方追加、
tier 開卡時填錯——這些都是常態，但 CLI 沒有入口，於是每次更正都改用 `gh issue edit`
或 Project GraphQL mutation 直接寫，繞過唯一寫入通道。2026-08-10 一天之內就繞了四次
（ai-workflow#15 的 tier、#17 的 spec 基線與 Log 渲染修復），這不是紀律問題，是工具缺口。

範圍界定（#19 驗收第 4 條）：本指令**同時**涵蓋 body 欄位與 Project 的 `級別` 欄位，
`WF-CLI-TIER-MUTATION1`（ai-workflow#12）因此併入本卡，不另行實作。

四條紅線：

- **原值必留且不得截斷**：每個被改欄位 append 一行 Log，完整記下原值與理由。Log 是
  還原點之一，摘要不能取代它（R1-01）；主控台輸出才做可讀性截斷。
  ⚠️ WF-CARD-BODY-BUDGET1 之後，走指紋路徑時 Log 記 sha256、全文在平台前一版；
  ⛔ 「Log 是唯一還原點」已不再成立，見 `_fold` 與 `_prior_revision_recoverable`。
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

**第二個上限——author 比對對代貼者恆真（WF-AMEND-AUTHZ-BINDING1）**：本指令
從不讀取操作者身分（全 ``cli/src`` 只有 ``review_cmd`` 為了 ``marked_by`` 讀
``gh api user``，amend 這條路徑沒有）。因此 author 比對能分辨的只有「留言是不是
需求方這個平台身分發的」，**分辨不了「是需求方本人張貼」還是「他人以該身分代擬
代貼」**。而本 repo 只有一個人類帳號——PM 的 ``gh`` 與需求方同為 ``ruan6047``
——所以這道比對對 PM 恆真，一次也沒有區辨過任何東西。

**第三個上限——留言內文從未被讀取**：``_resolve_ruling_author`` 只取 payload 的
``user.login``。本指令因此不知道那則留言寫了什麼，也就無從判定它是否構成裁定、
是否揭露代貼、是否載明授權來源。把該 URL 稱作「裁定」是**操作者的宣告**，不是
本指令查得的事實——註記裡必須這樣講明，否則外層那個詞本身就是超出證據的宣稱。

處置**不是**補上身分驗證（``docs/ROADMAP.md`` §1 已裁定三張授權款卡都不再追求
驗證），也**不是**把恆真性導出成 ``structurally-vacuous`` 之類的值再當檢查用
（同節逐字禁止）。處置是讓寫進 Log 的那句話**只到證據為止**：窮舉比對過的事實、
逐項寫明分辨不了什麼，且**不替它們取任何總結名稱**。

⚠️ 取名字就是本卡第二輪被擋下的原因：把上述兩件事總結成「宣告完整性已檢查」，
名詞（完整性）的涵蓋範圍大於冒號後真正列出的內容，讀者拿到的是結論而非事實
（跨家族查核 R1-001 blocking）。**換一個比較弱的形容詞不算修好**——「基本檢查」
「初步核對」是同一個病換劑量。正解是沒有標籤。

⚠️ 守衛本身也被擋下過三次。R2 用結構斷言釘住「（」與第一個事實之間不得插字，
並宣稱「任何新標籤必然插在該位置，因此必然被抓」；查核者把同一個標籤插到第一個
事實**之後**，測試全綠（R2-001）。R3 改為逐字比對回傳值；查核者讓實作依 comment id
分支，fixture 那組維持原值，全套仍綠（R3-001）。R4 改為約束原始碼形狀；查核者在
return 之前改寫 ``author``，全套仍綠（R4-001，裁定不修）。現行守衛的實際內容、
歷代變異的實測紅綠、以及已知不涵蓋的清單，見 ``AUTHORITY_NOTE_TEMPLATE`` 與
``test_amend.py`` 守衛區塊。

此上限的正解與上一段同源——結構化事件承載授權，屬 checkpoint writer 的射程。

--------------------------------------------------------------------------
授權註記守衛的威脅模型：防誰，以及防不到誰
--------------------------------------------------------------------------

**本守衛防的是無意的後續編輯，不防蓄意繞過的提交者。**

前者是有人改措辭、有人補說明時順手加個總結標籤、有人把標籤換成比較弱的形容詞。
後者是有人刻意繞過守衛，例如在 ``return`` 之前依 comment id 改寫 ``author``
（查核者 M27／R4-001）。

⚠️ 本節刻意**不寫綜述**——不出現「因此…／所以…／故保證…」形式的句子。本卡四輪
查核抓到的四句過度宣稱全部出自綜述類，而執行者自己掃了四次、四次都漏。只寫跑過
什麼、不涵蓋什麼。

無意的那一類，下列四個實例已實測會紅：M20（依 comment id 分支）、M22（模板加
``{label}`` 插值）、M25（改模板措辭）、M26b（執行期以 ``globals()`` 換模板）。
這是一份實測清單，不是對「所有無意編輯」的涵蓋範圍描述。

M27 **記為已知不涵蓋，不修**。AST 釘的是 ``return`` 運算式的**語法形狀**，不約束
``author`` 這個**值**的來源；要關掉它就得約束資料流，而關掉資料流之後還有裝飾器、
``_resolve_ruling_author`` 內部、以及執行期 monkeypatch。**對擁有這份碼的人，任何
測試與任何執行期檢查都無效。**

⚠️ 這是比例判斷不是證明。需求方 2026-08-16 裁定原句，**逐字保留、不得軟化**，
刻意不折行以免日後 reflow 把它拆散（``#57`` R5 同型陷阱）：

    需求方不能證明 M27 不會發生，只能說它不是這個守衛被開出來要擋的東西

本卡的核心痛點是「留痕宣稱了它沒有的區辨力」——那是**無意的過度宣稱**，不是防
內鬼。

**已知不涵蓋的清單（不宣稱其中任何一條已被處理）**：

1. AST 只約束 ``_authorize_by_requester_ruling`` 這一個函式。模組別處以動態寫法
   （如 ``globals()["AUTHORITY_NOTE_TEMPLATE"] = ...``）改掉常數，AST 看不見。
2. **執行期 monkeypatch 無解**：原始碼層面攔不住，沒有辦法。
3. 呼叫端事後加工（``run()`` 的 ``_fold``）只由固定輸入的測試覆蓋，那一層仍是取樣。
4. 模板與測試黃金值兩邊同時改錯：測試會綠。

⚠️ 往後遇到守衛類 finding，**先問「防誰」，涵蓋到了就停**——不是每次再多擋一個，
是先定義「夠了」是什麼（需求方 2026-08-16 可重用判準；本卡是第一個案例）。

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
import hashlib
import sys
import uuid

from ..card import (
    adopt_resource_sentinels,
    restore_migration_header,
    drop_sentinel_less_resource_section,
    CAPABILITY_TIERS,
    ROUTING_FIELDS,
    TIERS,
    AmendError,
    MarkerWriteBoundaryError,
    RequesterUnparseable,
    amend_acceptance,
    amend_brief,
    amend_core_pain,
    amend_initiative,
    amend_resource_block,
    amend_routing,
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
    PROJECT_TITLE_FIELD,
    set_field_value,
    set_issue_title,
    set_item_body,
)
from ..resources import ResourceDeclaration, ResourceDeclarationError, parse_block, render_block

#: 授權註記的模板。寫進 Log 的授權欄由它代入 author／url 產生。
#:
#: 措辭本身為什麼長這樣（沒有總結標籤、外層「裁定」被降級為操作者宣告），見模組
#: docstring「第二／第三個上限」。這裡講的是**為什麼它是一個具名常數**。
#:
#: ⚠️ 以下刻意**不寫綜述**——不出現「因此…／所以…／故保證…」形式的句子。本卡四輪
#: 查核抓到的四句過度宣稱全部出自綜述類（R2-001／R5-001／R6-001 與一句自查補上的），
#: 而我自己掃了四次、四次都漏。只寫做了什麼、跑過什麼、不涵蓋什麼；結論讀者自己下。
#:
#: **做了什麼**
#:
#:   1. 本常數是模組層的單一常數。`test_authority_note_template_is_verbatim_golden`
#:      逐字元比對它，並檢查插值欄位名恰為 author 與 url。
#:   2. `test_authority_note_is_template_substitution_by_construction` 以 AST 斷言
#:      `_authorize_by_requester_ruling` 只有一個 return、無巢狀函式，且該 return
#:      的運算式逐節點等於 `AUTHORITY_NOTE_TEMPLATE.format(author=author,
#:      url=args.ruling_url)`。
#:   3. `test_authority_note_template_is_assigned_exactly_once_in_the_module` 以 AST
#:      數模組內對本常數的指派次數。
#:   4. `test_runtime_output_matches_the_template_for_varied_inputs` 以四組
#:      (author, comment id) 實際呼叫比對。
#:
#: **歷代變異與實測結果**：完整清單見 `test_amend.py` 守衛區塊第 2 節。與改動本檔
#: 最相關的四筆：改回 f-string（輸出完全相同）→ 1 failed；改模板措辭 → 7 failed；
#: 模板加 `{label}` 插值 → 12 failed；在 return 之前改寫 `author` → 976 passed。
#:
#: **已知不涵蓋**（威脅模型：防無意的後續編輯，不防蓄意繞過的提交者；需求方
#: 2026-08-16 裁定）：在 return 之前改寫 `author`／`url` 這兩個**值**，AST 看不見、
#: 測試不會紅（M27／R4-001，已知不涵蓋且不修）。執行期 monkeypatch、以及模組別處
#: 用 `globals()[...] = ...` 動態指派改掉本常數，同樣不在涵蓋範圍。完整清單與需求方
#: 那句「不能證明 M27 不會發生」的原文，見模組 docstring「授權註記守衛的威脅模型」。
#:
#: ⚠️ 要改措辭是合法的，但必須連同 `test_amend.py` 的黃金常數一起改——那一行 diff
#: 就是要給查核者看的東西。改回 f-string 或改動 return 那一行運算式的形狀會讓上述
#: 第 2 條紅。
AUTHORITY_NOTE_TEMPLATE = (
    "依需求方 {author} 於 {url} 的裁定"
    "（已核對：該 URL 指向本卡 issue 的既存留言，"
    "且其 GitHub author 欄逐字等於卡面「需求：」欄。"
    "本指令不讀取留言內文或操作者身分，故不判定留言內容是否構成裁定"
    "——上句「裁定」是操作者的宣告，不是本指令查得的事實——"
    "亦不區分「需求方本人張貼」與「他人代擬代貼」）"
)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "amend",
        help="開卡後修訂卡面：spec 基線／驗收／驗證／資源宣告／級別。"
        "⚠️ 舊值的還原位置**視路徑而定**：平台留有前一版且舊值取自 body 時，Log 只記 sha256 指紋、"
        "全文由 `userContentEdits` 前一版取回；其餘四種情形（DraftIssue／首寫／版本內容取不到／"
        "舊值非 body 來源）Log 記全文。⛔ 本 help 先前只寫「進 Log」，那對指紋路徑是錯的指引。",
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
    # ---- 功能／路由更新（`WF-REDESIGN-W1` 驗收 5b。⛔ 非新增動詞——本卡射程逐字
    # 「不新增 wfcli 動詞」，⇒ 擴充既有的 amend）。
    #
    # 寫入集四項：Issue title ＋ Project item title ＋ `功能` 欄 ＋ routing 行。
    # ⚠️ 前兩項在 issue-backed 卡上是**同一次寫入**——Project item 的標題是 Issue
    # 標題的平台導出（見 project.set_issue_title）。⇒ 本指令寫一次、**讀回驗證兩處**，
    # ⛔ 不假裝它是兩次寫入。
    p.add_argument(
        "--feature",
        default=None,
        help="更正功能（Issue 標題後半段＋Project `功能` 欄）。"
        "⚠️ 標題整行重寫為 `<卡ID> <功能>`，⛔ 不做部分替換——部分替換要先猜出舊功能"
        "在標題裡的邊界，而那個猜測本身就是會出錯的 parser。"
        "⛔ 只支援 issue-backed 卡：draft item 的標題走另一條 ID 命名空間。",
    )
    p.add_argument(
        "--executor",
        default=None,
        help="更正路由行的執行者名字。未給的路由欄逐字沿用卡面現值。",
    )
    p.add_argument(
        "--exec-capability",
        default=None,
        choices=list(CAPABILITY_TIERS),
        help="更正路由行的**建議執行能力層級**（⛔ 不是 --tier 的 T0–T4 風險級別）。",
    )
    p.add_argument(
        "--exec-capability-reason",
        default=None,
        help="更正路由行的建議執行能力層級理由。",
    )
    p.add_argument(
        "--reviewer",
        default=None,
        help="更正路由行的查核者名字。",
    )
    p.add_argument(
        "--review-capability",
        default=None,
        choices=list(CAPABILITY_TIERS),
        help="更正路由行的建議查核能力層級。",
    )
    p.add_argument(
        "--review-capability-reason",
        default=None,
        help="更正路由行的建議查核能力層級理由。",
    )
    p.add_argument(
        "--core-pain",
        default=None,
        help="更正核心痛點。**須併 --ruling-url**，且不得與其他欄位旗標同一次調用："
        "此欄餵給具否決權的 core_pain_resolved，一次調用＝一次治理裁定",
    )
    p.add_argument(
        "--brief",
        default=None,
        help=(
            "改（或首次寫入）卡片簡介（canonical §6.3）。⚠️ 既有卡沒有 `## 簡介` 區段——"
            "本旗標會**插入**一個到核心痛點之前，⛔ 不是報錯：188 張既有卡的補寫通道正是"
            "本旗標。形狀機械檢查必含「適用時機」與「⛔ 非射程：」；⛔ 不驗字數。"
            "雙居所：body 哨兵為權威、Project TEXT 欄位為恆等導出，寫入順序 body 先、"
            "欄位後並讀回驗證。"
        ),
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
        "--adopt-resource-sentinels",
        action="store_true",
        help="一次性結構修復：把既有的資源宣告 JSON 區塊包進 resource-claims 哨兵。"
        "⭐ **逐字保留原 payload**，⛔ 不發明也不清空——那 33 張遷移卡的宣告內容本來就在，缺的只有哨兵。"
        "⚠️ 包完後仍可能因 payload 本身不合 schema（如 db_scope: null）而解析失敗，"
        "那是失敗層級由「缺哨兵」位移到「內容」，⛔ 本旗標不代為修正內容",
    )
    p.add_argument(
        "--restore-migration-header",
        action="store_true",
        help="一次性結構修復：為 2026-08-04 遷移卡補回 `- 需求：…　規劃：…` 與 "
        "`- Initiative：…　spec 基線：…` 兩行標頭，以及 `## 核心痛點`／`## 驗收條件`／`## 驗證` "
        "三個**空**章節。理由是 canonical §6.4.1（無驗收／驗證章節 ⇒ 構造上離不開規劃），"
        "⛔ 不是「讓卡變成 wfcli 可達」（實測那批卡對 amend --brief／handoff／review 本來就打得到）。"
        "⛔ 只補結構不產生內容 ⇒ 補完後事後掃描仍報缺核心痛點／缺驗收，那是對的。"
        "⚠️ 須搭配 --header-requested-by／--header-planned-by",
    )
    p.add_argument(
        "--header-requested-by",
        help="--restore-migration-header 用：`需求` 欄的值。⚠️ 這是**一句斷言**⛔ 不是排版——"
        "它日後是 --ruling-url 精確比對的授權基準。⇒ 須自 cutover 前一版的原始卡面取值，"
        "並把舊值原文／來源 commit 與 path／正規化規則逐字寫進 --reason。⛔ CLI 不做正規化、不猜身分",
    )
    p.add_argument(
        "--header-planned-by",
        help="--restore-migration-header 用：`規劃` 欄的值（逐卡不同，須自來源取）",
    )
    p.add_argument(
        "--header-initiative",
        default="—",
        help="--restore-migration-header 用：`Initiative` 欄的值（預設 —）",
    )
    p.add_argument(
        "--header-spec-baseline",
        default="—",
        help="--restore-migration-header 用：`spec 基線` 欄的值（預設 —）",
    )
    p.add_argument(
        "--drop-stale-resource-section",
        action="store_true",
        help="一次性結構修復：刪掉**沒有哨兵**的那個資源宣告區段（前提是另有一個帶哨兵的）。"
        "⚠️ 只處理「恰好 2 個資源宣告標題、其中恰好 1 個含哨兵」的卡，其他形狀一律拒絕不猜。"
        "⛔ 這條路徑刻意**不走 parse_block**——會走到它的卡正是因為兩個標題而解析失敗的那些",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="只驗證與列印將寫入的變更，不連 GitHub 寫入任何狀態",
    )
    p.set_defaults(func=run)


def _fold(text: str) -> str:
    """Log 是單行條目，值摺成一行——但**不截斷**。

    ⚠️ **原 docstring 逐字寫「Log 是唯一還原點」，該前提已被本卡推翻**：
    GitHub `userContentEdits` 對每次 body 編輯保存**逐位元相同的完整前一版**
    （2026-08-25 實測：`#105` 截斷前後 sha256 相符；`#16` 50 版全數可取）。
    ⇒ 舊值改記指紋、由平台版本還原（見 `_prior_revision_recoverable` 的四條退路）。
    ⛔ **不截斷**這一點仍然成立：走全文退路時 Log 就是唯一還原點。
    """
    return " ".join(str(text).split())


#: GitHub issue body 的硬上限，單位是**字元**（Unicode code point），⛔ **不是位元組**。
#:
#: 2026-08-25 於 `ruan6047/ai-workflow#105` 實測：body **129,651 字元**時讀得到但寫不進去，
#: 截斷後恢復可寫 ⇒ 上限落在 (129,486, ~130,018) 字元之間。本常數取**下界**。
#: ⛔ 不是文件常引的 65,536。
#:
#: ⚠️ **單位是字元這件事是 V8 用真實卡抓到的，⛔ 不是推導出來的。**
#: 第一版把量到的 129,651 當成位元組，而碼裡用 `len(body.encode())` ⇒ 對中文卡面
#: （1 字 ≈ 3 位元組）守衛會**提早約 3 倍觸發**。反例是 `aiwf#130`：
#: 字元 74,894／位元組 156,942，🏁完成且真實存在於 GitHub 上——⇒ 上限若真是
#: 129,486 **位元組**，那張卡不可能存在。而截斷前的 `#105` 是字元 129,651／位元組 262,130。
#: ⛔ 所有 mock 測試都用 ASCII，構造上碰不到這個差異。
#:
#: ⚠️ 這是黑箱量測、⛔ 沒有官方文件保證；GitHub 若調整上限，此處要重新量。
BODY_LIMIT = 129_486

#: 軟門檻：餘裕低於此值時警告但**放行**。⛔ 不擋，因為擋了會讓人學會繞過。
BODY_SOFT_MARGIN = 20_000


def _fingerprint(text: str) -> str:
    """欄位值的指紋：sha256 全長 ＋ 位元組數。

    ⭐ 比存全文**更強**：全文自己不能證明自己沒被改，指紋可以。
    ⛔ 不截斷成短 hash——碰撞成本必須留在密碼學等級。
    """
    raw = (text or "").encode("utf-8")
    return f"sha256:{hashlib.sha256(raw).hexdigest()} ({len(raw)} bytes)"


def _prior_revision_recoverable(runner, item) -> tuple[bool, str]:
    """**實查**該卡的前一版是否真的取得回。回傳 (可取得, 理由)。

    ⛔ **必須實查，不得由 ``--repo`` 是否給定或卡片來源推定**（A3）。三條退路：

    1. ``content_type != "Issue"`` —— GraphQL schema 上 ``DraftIssue`` **沒有**
       ``userContentEdits`` 欄位（2026-08-25 實測），⇒ 平台零保存。
    2. ``totalCount == 0`` —— 首寫，平台沒有前一版（33 張抽樣中 9 張如此）。
    3. 最新一版的 ``diff`` 取回為 ``None`` —— 平台記了但內容拿不到。

    ⚠️ 第 3 條是本卡執行期新增的：A9 的實測只把已驗證區間由 39 版推到 50 版
    （`aiwf#16`，50/50 全數可取），⛔ **沒有證明無上限**，⛔ 也沒有官方保證，
    且 >39 版的樣本只有 1 個、最舊僅回溯 8 天。⇒ 設計必須對「取不到」fail-safe，
    ⛔ 不得因為那一輪結果而省掉實查。
    """
    if item.content_type != "Issue":
        return False, f"content_type={item.content_type}（平台無 userContentEdits）"
    if not item.issue_url:
        return False, "缺 issue_url，無法查詢版本"
    parts = item.issue_url.split("/")
    owner, name = parts[3], parts[4]
    query = (
        f'{{repository(owner:"{owner}",name:"{name}")'
        f"{{issue(number:{item.issue_number})"
        "{userContentEdits(last:1){totalCount nodes{diff}}}}}"
    )
    # ⚠️ **必須走 ``runner.graphql``**，⛔ 不是 ``run_json(["api","graphql",...])``。
    # 後者在 ``FakeGhRunner`` 上認不得 ⇒ 會拋錯 ⇒ 被下面的 except 吞掉 ⇒ 回傳 False
    # ⇒ **所有 mocked 測試都走全文退路、指紋路徑一次都不會被跑到**。
    # 那是「守衛在測試裡從不執行」的形態，⛔ 本卡不得留下它。
    try:
        data = runner.graphql(query)
        edits = data["data"]["repository"]["issue"]["userContentEdits"]
    except Exception as exc:  # noqa: BLE001 —— 任何查詢失敗一律退回全文，⛔ 不猜
        return False, f"版本查詢失敗（{exc}）"
    if not edits or edits.get("totalCount", 0) == 0:
        return False, "totalCount=0（首寫，平台無前一版）"
    nodes = edits.get("nodes") or []
    if not nodes or nodes[-1].get("diff") is None:
        return False, "最新一版的內容取回為 null"
    return True, f"totalCount={edits['totalCount']}，最新一版可取得"


def _render_budget(body: str, before_len: int) -> tuple[str, int, int]:
    """回傳 (預算行, 本次成本, 餘裕)。⭐ 零額外 API——完整新 body 此刻已在手上。"""
    after = len(body)  # ⚠️ 字元，⛔ 不是位元組——見 BODY_LIMIT 的註解
    cost = after - before_len
    margin = BODY_LIMIT - after
    if margin <= 0:
        # A4 逐字「⛔ 無資料時印「—」不印 0」。超過上限時「還能改幾次」沒有意義，
        # ⇒ 同樣印「—」，⛔ 不印 0——0 會被讀成「剛好用完」而不是「不適用」。
        remaining = f"—（已超過上限 {-margin:,}）"
    elif cost > 0:
        remaining = f"{margin // cost} 次"
    else:
        remaining = "—"
    delta = f"+{cost:,}" if cost >= 0 else f"{cost:,}"
    line = (
        f"[amend] 卡面預算：本次 {delta} 字元／寫入後 {after:,}／"
        f"上限 {BODY_LIMIT:,}／餘裕 {margin:,}／以本次成本估還能改 {remaining}"
    )
    return line, cost, margin


def _largest_field_hint(body: str) -> str:
    """硬線拒絕時指出**最大的可壓縮章節**，⛔ 不只說「太長了」。"""
    head, _, log = body.partition("\n## Log")
    parts: list[tuple[int, str]] = [(len(log), "## Log")]
    for name in ("## 驗收條件", "## 驗證", "## 核心痛點", "## 簡介"):
        if name in head:
            seg = head.split(name, 1)[1].split("\n## ", 1)[0]
            parts.append((len(seg), name))
    parts.sort(reverse=True)
    top = "、".join(f"{n}（{sz:,} 字元）" for sz, n in parts[:3])
    return top


def _where_for(entry: tuple, *, recoverable: bool) -> tuple[str, str]:
    """回傳該筆變更 (舊值, 新值) 各自的**還原位置**措辭（R1-001）。

    ⭐ 判準與 Log 寫入端**共用同一個表達式**（`recoverable and body_sourced`），
    ⛔ 不各寫一份——那正是本 repo 反覆踩到的「每個呼叫端自己重寫一份謂詞」。
    """
    body_sourced = entry[4] if len(entry) > 4 else False
    if recoverable and body_sourced:
        # 指紋路徑：Log 只有 sha256。舊值在平台前一版，新值就在正上方的欄位裡。
        return "見平台前一版", "見上方欄位"
    return "見 Log", "見 Log"


def _short(text: str, limit: int = 100, *, where: str = "見 Log") -> str:
    """只給主控台看的可讀摘要；永遠不進 Log。

    ⚠️ `where` **必須反映該次實際走的路徑**（R1-001，`GPT-5@Codex` 2026-08-26）。
    原版無條件寫「見 Log」，而指紋路徑的 Log **只有 sha256、沒有全文**
    ⇒ 同一次輸出會同時出現「Log 記法：指紋」與「全文 N 字，見 Log」，
    後者是**錯誤的還原指引**。⛔ 呼叫端不得沿用預設值而不判斷。
    """
    folded = _fold(text)
    return folded if len(folded) <= limit else folded[:limit] + f"…（全文 {len(folded)} 字，{where}）"


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
    """這個拒收是不是「**卡面上已經壞掉的 body**」，⛔ 不是「你送進來的值有問題」。

    ⭐ **型別先行的那一行是刻意的，⛔ 不是防禦性冗餘**（WF-MARKER-WRITE-BOUNDARY1）：
    (a) 現在的行為：``MarkerWriteBoundaryError`` 一律**不**算排版損壞。
    (b) 為什麼：寫入邊界守衛的訊息會轉述讀取端的原始錯誤，而那段原文就含
        ``個 `## Log` 標題`` 這串字面 ⇒ 純字面判斷會對一張**完好**的卡印出
        ``_LAYOUT_RUNBOOK``，教使用者去 ``gh issue edit`` 手改 body。那是把
        「請你改值」誤導成「請你動卡面」，⛔ 而動卡面正是本 repo 要消滅的繞道。
    (c) ⛔ **不得推出**「所以可以把守衛的訊息改成避開那兩串字面」——訊息裡引述讀取端
        的真實錯誤對使用者是必要資訊；分辨責任歸屬是**型別**的工作，⛔ 不是措辭的工作。
    """
    if isinstance(exc, MarkerWriteBoundaryError):
        return False
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
    """比對裁定留言的 author 欄與卡面「需求：」欄，回傳寫進 Log 的授權註記。

    三道檢查，缺一即拒（對齊 ``review-escalation.md`` §4 (a′) 與第 2、3 款）：

    1. 卡面「需求：」欄可解析（``parse_requested_by``，fail-closed）；
    2. 裁定留言的 GitHub comment author **逐字等於**該帳號；
    3. 該 author **不等於本卡當前 owner**——裁定者不得是被該裁定嘉惠的人。

    ``docs/ROADMAP.md`` §1 裁定本卡所屬的三張卡都**不再追求身分驗證**，改為確認
    宣告欄位存在且必填。但「不是身分驗證」不足以描述本函式的上限——三道檢查的
    區辨力並不相同，且有一整類事實它根本沒看：

    - 第 1、3 道與 ``_resolve_ruling_author`` 的形狀／卡號／留言存在各檢查**可以
      為假**，實測會拒（見 ``test_amend.py`` 對應各條；2026-08-16 一次把 ``#31``
      的 ``--ruling-url`` 誤指向 ``#88``，即由卡號檢查當場拒收）。
    - 第 2 道在**單一人類帳號**的 repo 裡對代貼者恆真：PM 的 ``gh`` 與需求方是
      同一個平台身分，故它從未區辨過任何東西。**恆真本身不導出成任何值**——
      ``ROADMAP.md`` §1 逐字禁止「把恆真性導出成 ``structurally-vacuous`` 再繼續
      假裝那是檢查」——只在回傳的註記裡據實寫明本比對不能分辨什麼。
    - **完全沒看的**：留言內文。本函式只取 payload 的 ``user.login``，故它不知道
      該留言寫了什麼，也無從判定它是否構成裁定、是否揭露代貼、是否載明授權來源。
      呼叫端把該 URL 稱為「裁定」是**操作者的宣告**，不是本函式查得的事實。

    因此回傳的註記**不替上述任何一組檢查命名**（不寫「完整性已檢查」之類的總結
    標籤——那會讓讀者拿到的強度高於證據，跨家族查核 R1-001 blocking），只窮舉
    比對過的兩件事，再逐項寫明它分辨不了什麼。
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
    # 這一行是本函式**唯一**的 return，且必須恰好是「模板 ＋ 兩個資料插值」。
    # 不得改成 f-string、不得依 author／url／環境分支、不得在此拼接任何其他字串——
    # 理由與守衛形狀見 `AUTHORITY_NOTE_TEMPLATE` 的說明。
    return AUTHORITY_NOTE_TEMPLATE.format(author=author, url=args.ruling_url)


#: ``--<旗標>`` → 路由行群組名。⛔ 值域由 ``card.ROUTING_FIELDS`` 持有，本表只做對映；
#: 模組載入時斷言兩者一致（多／少一個群組會當場炸，⛔ 不會靜默少改一欄）。
ROUTING_FLAG_TO_GROUP = {
    "executor": "executor",
    "exec_capability": "exec_tier",
    "exec_capability_reason": "exec_reason",
    "reviewer": "reviewer",
    "review_capability": "rev_tier",
    "review_capability_reason": "rev_reason",
}
assert set(ROUTING_FLAG_TO_GROUP.values()) == set(ROUTING_FIELDS), (
    "amend 的路由旗標對映與 card.ROUTING_FIELDS 不一致："
    f"{sorted(set(ROUTING_FLAG_TO_GROUP.values()) ^ set(ROUTING_FIELDS))}"
)


def _routing_updates(args: argparse.Namespace) -> dict[str, str]:
    """本次調用要改的路由群組（未給的旗標⛔ 不進 dict，由 ``amend_routing`` 沿用現值）。"""
    return {
        group: getattr(args, flag)
        for flag, group in ROUTING_FLAG_TO_GROUP.items()
        if getattr(args, flag) is not None
    }


def run(args: argparse.Namespace) -> int:  # noqa: C901 - 逐旗標的前置檢查本就是平鋪的
    if not args.reason.strip():
        print("[amend] 拒絕：--reason 不得為空（每次修訂都要能回答為什麼）", file=sys.stderr)
        return 2

    # ⭐ **空白 `--feature` 在任何遠端呼叫之前硬拒**（`WF-REDESIGN-W1` R1-1／R1-2）。
    #
    # (a) 現在的行為：`--feature '   '` 回 rc=2，⛔ 不解析 project、⛔ 不讀 item、
    #     ⛔ 不寫任何東西。
    # (b) 為什麼在這裡而不是下面的 try：那個 try 排在 `resolve_project` 與 `list_items`
    #     之後，⇒ 走到那裡時已經對 GitHub 發過查詢。本檢查是純字串判斷，沒有理由晚跑。
    #     判準與 `open` 的 `validate_open_fields`「功能 必填」**同一句話**——同一個欄位
    #     在兩個寫入端不得有兩套鬆緊。
    # (c) ⛔ 不得由此推出「amend 其餘旗標也各自有這種前置檢查」：它們沒有，
    #     值層面的拒收多數落在下面那個 try 內（讀了 item 之後）。
    if args.feature is not None and not args.feature.strip():
        print(
            "[amend] 拒絕（未寫入任何狀態，也未讀取任何遠端狀態）：--feature 不得為空或全空白"
            f"（收到 {args.feature!r}）。⇒ 功能是卡面標題的後半段，"
            "空值會寫出一個尾端帶空白、讀者認不出是哪張卡的標題。",
            file=sys.stderr,
        )
        return 2

    wants_resources = args.db_scope is not None or args.resources is not None
    routing_updates = _routing_updates(args)
    field_flags = [
        args.spec_baseline,
        args.acceptance,
        args.verification,
        args.tier,
        args.initiative,
        args.core_pain,
        args.brief,
        args.feature,
    ]
    wants_fields = (
        any(f is not None for f in field_flags)
        or bool(routing_updates)
        or wants_resources
        or args.drop_stale_resource_section
        or args.adopt_resource_sentinels
        or args.restore_migration_header
    )

    if not wants_fields:
        print("[amend] 拒絕：沒有指定任何要修訂的欄位", file=sys.stderr)
        return 2

    # 核心痛點獨占一次調用：op 識別碼與一次治理裁定必須 1:1。混在其他欄位裡改，
    # 會讓 Log 上同一個 op 同時承載「需求方裁定的問題重界定」與「順手改的筆誤」，
    # 稽核者無從分辨那份 --ruling-url 授權的究竟是哪一項。
    if args.core_pain is not None:
        others = [f for f in field_flags if f is not None and f is not args.core_pain]
        if (
            others
            or wants_resources
            or routing_updates
            or args.drop_stale_resource_section
            or args.adopt_resource_sentinels
            or args.restore_migration_header
        ):
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
    # ⭐ 這裡**刻意只解析 project、不取欄位定義**。
    #
    # (a) 刻意如此：原本這裡有一行 `fields = list_fields(...) if dry_run else
    #     ensure_fields(...)`——那個三元式是為了讓 `--dry-run` 不要建欄位而加的
    #     （查核 R3-001）。現在整行拿掉，改由下面**兩個受條件保護的呼叫點**各自取。
    # (b) 為什麼：`ensure_fields` 不是唯讀的（缺欄位就送 `gh project field-create`），
    #     而 `fields` 這個名字在本函式裡**只**被兩個分支讀到——`fields["級別"]`（級別
    #     欄先寫那條）與 `fields[field_name]`（body 之後補寫雙居所欄位那條）。
    #     擺在這裡，中間所有拒收（找不到卡 rc=3、缺授權 rc=2、body 超上限 rc=2、
    #     body 被他人改動 rc=6…）都會先改掉 Project 的欄位定義。
    # (c) ⛔ **兩個順帶的行為改變，不得靜默**：
    #     - `--dry-run` 從此**不再發任何欄位查詢**（原本走 `list_fields`）。它本來
    #       就沒用到回傳值，⇒ 唯讀路徑不少任何東西，但少了一次 API 呼叫。
    #     - `list_fields` 的 import 因此變成未使用，已一併移除。
    # (d) ⛔ 不得由此推出「amend 的拒收路徑零欄位寫入」：`tier_needs_field_write`
    #     為真時，級別欄的 `set_field_value` 讀回失敗仍會 rc=5，而 `ensure_fields`
    #     在它前一行——那是「閘門後、寫入前」的必要位置，⛔ 不是閘門前的寫入。
    #     逐字登記見 `cli/tests/test_gate_before_write.py` 的 `FROZEN`。

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
            changes.append(("spec 基線", old, args.spec_baseline, None, True))
        if args.initiative is not None:
            body, old = amend_initiative(body, args.initiative)
            changes.append(("Initiative", old, args.initiative, None, True))
            pending_field_writes["Initiative"] = args.initiative
        if args.core_pain is not None:
            body, old = amend_core_pain(body, args.core_pain)
            changes.append(("核心痛點", old, args.core_pain, ruling_note, True))
        if args.brief is not None:
            body, old = amend_brief(body, args.brief)
            changes.append(("簡介", old or "（原本沒有）", args.brief, None, True))
            # ⚠️ 欄位是 body 的恆等導出，故排進 pending_field_writes——指令層在 body
            # 寫成功後才寫欄位，並由 doctor 的漂移偵測抓「body 已更新、欄位過期」。
            pending_field_writes["簡介"] = args.brief
        if routing_updates:
            body, old = amend_routing(body, routing_updates)
            changed = "；".join(f"{g}={routing_updates[g]}" for g in sorted(routing_updates))
            changes.append(("routing 行", old, changed, None, True))
        if args.feature is not None:
            # ⚠️ **功能不在 body 裡**（``_render_issue_body`` 不渲染它；它只進 Issue 標題
            # 與 Project `功能` 欄）⇒ 這一格**沒有** body 差分，只有 Log 行與兩個導出面。
            # ⛔ 不得由「其他欄位都改 body」推出這一格也該改 body——把功能塞進 body 是
            # 新增一個居所，那是規格變更不是修訂。
            if item.content_type != "Issue" or item.issue_number is None or not target.repo:
                raise AmendError(
                    "--feature 需要 issue-backed 卡（本卡 content_type="
                    f"{item.content_type}、issue_number={item.issue_number}、"
                    f"repo={target.repo!r}）：draft item 的標題走 "
                    "`gh project item-edit --id <DI_…> --title`，是另一條 ID 命名空間"
                )
            current_feature = item.text("功能")
            if current_feature == args.feature:
                # 形狀與同檔資源宣告／級別的 no-op 拒收**逐字相同**：值沒變就沒有
                # 「修訂」可留痕，寫下去等於在 Log 上製造一筆不實的變更紀錄。
                # ⚠️ 判準取 `功能` 欄而**不是** Issue 標題：標題是 `<卡ID> <功能>` 的
                # 合成值，拿它比等於把卡ID 也算進「功能有沒有變」。
                raise AmendError(
                    f"功能與現值相同（{args.feature!r}）；拒絕寫入不實的修訂留痕。"
                    "⇒ 若你要修的是**標題其餘部分**，那不是本旗標的射程——"
                    "標題恆為 `<卡ID> <功能>`，卡ID 由 open 決定且 amend 不改它"
                )
            changes.append(("功能", current_feature or "（未設定）", args.feature, None, False))
            pending_field_writes["功能"] = args.feature
        if args.acceptance is not None:
            body, old = amend_acceptance(
                body, args.acceptance, preserve_checked=args.preserve_checked
            )
            changes.append(("驗收條件", old, "；".join(args.acceptance), None, True))
        if args.verification is not None:
            body, old = amend_verification(
                body, args.verification, preserve_checked=args.preserve_checked
            )
            changes.append(("驗證", old, "；".join(args.verification), None, True))
        if args.restore_migration_header:
            body, inserted = restore_migration_header(
                body,
                requested_by=args.header_requested_by or "",
                planned_by=args.header_planned_by or "",
                initiative=args.header_initiative,
                spec_baseline=args.header_spec_baseline,
            )
            changes.append(("卡面標頭（補回遷移缺行）", "（原卡面無標頭行與三章節）", inserted, None, True))
        if args.adopt_resource_sentinels:
            body, old_seg = adopt_resource_sentinels(body)
            changes.append(("資源宣告（補哨兵）", old_seg, "（已包入 resource-claims 哨兵）", None, True))
        if args.drop_stale_resource_section:
            body, removed = drop_sentinel_less_resource_section(body)
            changes.append(("資源宣告（刪除殘留區段）", removed, "（已刪除）", None, True))
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
                changes.append(("資源宣告", old, summary, None, True))
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

    # ⭐ **Log 的成本從 O(2×欄位大小) 降為 O(1)**（本卡 A1）。
    #
    # `_fold` 的 docstring 原本寫「Log 是唯一還原點」——2026-08-25 實測推翻：GitHub
    # `userContentEdits` 對每次 body 編輯保存**逐位元相同**的完整前一版（`#105` 截斷前後
    # sha256 相符；`#16` 50 版全數可取）。而**新值**更是冗餘的——它就在正上方的欄位裡。
    # ⇒ 兩者都改記指紋：指紋比全文**更強**（全文不能證明自己沒被改）。
    #
    # ⚠️ **代價明說**：Log 由自足變成依賴平台。任何離線讀 Log 的流程（匯出、封存、
    # repo 遷移）只會拿到指紋 ⇒ 遷離 GitHub 前須先全量匯出版本。⛔ 這不是零成本。
    #
    # ⛔ 三條退路一律寫全文，且**實查**而非推定（A2／A3）：見 `_prior_revision_recoverable`。
    recoverable, why = _prior_revision_recoverable(runner, item)
    timestamp = now_iso8601()
    for entry in changes:
        field_name, old, new, note = entry[:4]
        # ⭐ **預設 False（寫全文）**，`body` 來源者才 opt-in。
        #
        # ⚠️ 方向是刻意的：`userContentEdits` 保存的是**前一版 body**。若某筆變更的舊值
        # 取自別處（Project 欄位、或操作者宣告的字串），它**從來沒出現在任何一版 body 裡**
        # ⇒ 指紋不可還原、⛔ 那是靜默的資料損失。既有測試
        # `test_stale_project_field_converges_on_rerun` 正是這種：雙面不同步自癒時，
        # 舊值 `file:docs/only-one-file.md` 只存在於 Project 欄位。
        # ⇒ 預設若設 True，日後新增一個非 body 來源而忘了標記就會靜默丟資料。
        body_sourced = entry[4] if len(entry) > 4 else False
        authority = f"；授權 {_fold(note)}" if note else ""
        if recoverable and body_sourced:
            values = (
                f"原值指紋 {_fingerprint(old)} → 新值指紋 {_fingerprint(new)}"
                f"（現值見上方欄位；原值見平台 userContentEdits 前一版）"
            )
        else:
            reason_full = why if not recoverable else "舊值來源非 body，平台版本救不回"
            values = f"原值「{_fold(old)}」→ 新值「{_fold(new)}」（⚠️ 全文：{reason_full}）"
        body = append_log_line(
            body,
            f"{timestamp} amend by wf-cli（op {op_id}）→ {field_name}："
            f"{values}；理由 {_fold(args.reason)}{authority}。",
        )

    # ---- 卡面容量預算（A4–A6）。⭐ 零額外 API：完整新 body 此刻已在手上 ----
    budget_line, _cost, margin = _render_budget(body, len(item.body))
    print(budget_line)
    if margin <= 0:
        # ⭐ **縮小中的救援與撐大要分流。** 自審抓到：一張**已經**超過上限的卡
        # （`aiwf#105` 曾是 129,651）做壓縮修復時，若一次沒縮到上限以下，
        # 原本的訊息會叫它「請先封存再壓縮」——⛔ 而它正在做那件事。
        # ⇒ 兩種情境給的下一步完全不同，訊息必須分開。
        #
        # ⚠️ 兩者都仍 `return 2`：body 超過上限時 GitHub 本來就會拒收，
        # 放行只會換成一個更難懂的遠端錯誤。⛔ 這裡擋的是「白跑一趟」，不是修復本身。
        if _cost < 0:
            print(
                f"[amend] 拒絕：本次已縮小 {-_cost:,} 字元，但寫入後仍有 {-margin:,} "
                f"超過上限 {BODY_LIMIT:,}。⇒ **方向對了、幅度不夠**，請在同一次修訂裡再縮 "
                f"{-margin:,} 字元以上。目前最大的章節：{_largest_field_hint(body)}。"
                "⚠️ 若一次縮不到位，唯一的出路是走 `gh issue edit --body-file` 手動截斷"
                "（該路徑會抹掉 append-only 的 Log，須先把 Log 全文封存成留言）。",
                file=sys.stderr,
            )
        else:
            print(
                f"[amend] 拒絕：寫入後 body 會超過上限 {BODY_LIMIT:,} 字元（超出 {-margin:,}）。"
                f"最大的可壓縮章節：{_largest_field_hint(body)}。"
                "⇒ 請先把該章節的原文封存成留言、再以逐條壓縮改寫（⛔ 合併與丟棄不是壓縮）。"
                "⚠️ 若卡面**已經**在上限之上、壓縮改寫本身也寫不進去，唯一的出路是走 "
                "`gh issue edit --body-file` 手動截斷——該路徑會抹掉 append-only 的 Log，"
                "須先把 Log 全文封存成留言。（`aiwf#105` 2026-08-25 即循此救回："
                "三則留言封存 33 事件 Log，截斷後平台 userContentEdits 仍留有逐位元相同的截斷前 body。）",
                file=sys.stderr,
            )
        return 2
    if margin < BODY_SOFT_MARGIN:
        print(
            f"[amend] ⚠️ 警告：餘裕僅 {margin:,} 字元（軟門檻 {BODY_SOFT_MARGIN:,}）。"
            f"最大的可壓縮章節：{_largest_field_hint(body)}。**本次仍放行**。",
            file=sys.stderr,
        )

    if args.dry_run:
        # A4 逐字要求 `--dry-run` 也印預算行——它上面已經印過（在 Log 組裝之後），
        # 這裡不重印，只補上 Log 記法的說明，讓 dry-run 看得出這次會不會寫全文。
        print(f"[amend] Log 記法：{'指紋' if recoverable else '全文'}（{why}）")
        print(f"[amend] dry-run（未寫入任何狀態）：{args.card_id} 將修訂 {len(changes)} 個欄位")
        for entry in changes:
            field_name, old, new, note = entry[:4]
            w_old, w_new = _where_for(entry, recoverable=recoverable)
            print(f"  - {field_name}：「{_short(old, where=w_old)}」→「{_short(new, where=w_new)}」")
            if note:
                print(f"    授權：{_short(note)}")
        return 0

    # 級別先寫並讀回驗證，body 後寫。這個順序讓「欄位寫失敗」變成乾淨中止
    # （body 未動、無半寫入）；而「欄位成功、body 失敗」留下的不一致，由下一次
    # 同樣的 amend 依 _tier_change_logged 偵測並只補寫 Log 自癒。
    if tier_needs_field_write:
        # 第一個受條件保護的取值點：只有真的要寫級別欄時才準備欄位 schema。
        fields = ensure_fields(runner, target.owner, target.project)
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

    # ---- 標題（`WF-REDESIGN-W1` 驗收 5b 的寫入集前兩項）----
    #
    # ⭐ **一次寫入、三個 surface 分開讀回**（2026-08-31 依查核 R1-1 拆開；
    # 2026-09-01 依需求方裁定**甲**調整 ③ 的處置）。
    #
    # (a) 現在的行為：發一次 `gh issue edit --title`，然後**各自**讀回
    #     ① Issue 本體的 `title`、② Project item 的 `content.title`、
    #     ③ Project 內建 `Title` **欄**（`item.text("Title")`）。
    #     **①② 是判準**（不符 ⇒ rc=8）；**③ 不是判準**，只印一行事實註記。
    # (b) 為什麼 ③ 退出判準（需求方 2026-09-01 裁定甲，證據為下列四項實測）：
    #     1. **wfcli 現行路徑寫不動它；已窮舉的 GraphQL `ProjectV2*` mutation 面裡也
    #        找不到 writer**：對真 Project #4 實跑 `updateProjectV2ItemFieldValue`
    #        回 "The title field can only be updated on DraftIssues"；schema introspection
    #        窮舉 32 個 `ProjectV2*` mutation，吃 `title` 的 5 個之中，兩個限 DraftIssue、
    #        三個寫的是**專案自己**的標題。
    #        ⚠️ 射程逐字＝**GraphQL mutation 面**（查核 R2-1）；⛔ 未量 REST／匯出／webhook。
    #     2. **它是 add-time 快照**：把同一張 `aiwf#177` 加進一個新建的拋棄式 Project，
    #        該處的 `Title` 欄＝當下的 `content.title`（新值），而 Project #4 的同一張
    #        仍是舊值。同一 issue、同一時刻、兩個值。
    #     3. **母體兩個方向零反例**：213 個 item 中有改名紀錄的恰 5 筆、5 筆全部不一致；
    #        無改名的 208 筆全部一致。最舊的不一致已持續約 26 天。
    #     4. **人類讀者看不到它**：實看 Projects UI 的 Title 欄，五筆不一致的 item
    #        **全部**顯示 `content.title`（新值）。
    #     ⇒ 把它留在判準裡＝讓 `--feature` 在 issue-backed 卡上**永遠**回非零，
    #     而那個非零指向的是一個**在已量範圍內找不到 writer、沒有 wfcli 消費者、
    #     且實看 UI 讀者看不到**的值。
    # (c) ⚠️ **上一版在這裡寫過一句被自己量測推翻的話**：「它是看板檢視上讀者實際看到的
    #     那一格」——**錯的**，見 (b)4。就地留證，⛔ 不靜默刪掉。
    # (d) ⛔ **不得由「③ 退出判準」推出「③ 已同步」或「③ 不存在」**：它仍是一個對不上的
    #     機讀值；**目前已實測讀得到它的面，例子包括** GraphQL `fieldValueByName("Title")`
    #     與 `gh project item-list` 的頂層 `title`。⛔ 讀取面**未窮舉**，故⛔ 不寫「只有」。
    #     註記就是為了讓它保持被說出來。
    # (e) ⚠️ **本段與下方訊息的措辭收斂自查核 R2-1**（`title-field-note-exceeds-measured-
    #     api-surface`）：上一版寫「wfcli 與**任何 API** 呼叫都寫不動它」與「這個舊值
    #     **只有** …讀得到」，兩句都把**已窮舉的 GraphQL mutation 面**擴寫成全 API／
    #     全讀取面，而我自己在 issuecomment-5488724887 §七第 4 項就寫著 REST／匯出／
    #     webhook 未量。就地留證，⛔ 不靜默改掉。
    #     ⛔ 回歸斷言（`tests/test_amend.py`）禁止這兩個全稱重新出現。
    # (e) ⛔ 也不得由此推出「可以改用 delete+re-add 修它」：那會清掉該 item 全部自訂
    #     欄位值，且 `deleteProjectV2Item` 是 W2A 的「撤銷」語意。
    if args.feature is not None:
        expected_title = f"{args.card_id} {args.feature}"
        set_issue_title(runner, target.repo, item.issue_number, expected_title)
        issue_title = (
            runner.run_json(
                ["issue", "view", str(item.issue_number), "--repo", target.repo,
                 "--json", "title"]
            )
            or {}
        ).get("title")
        after_item = find_item_by_card_id(list_items(runner, project), args.card_id)
        content_title = after_item.title if after_item else None
        project_title_field = after_item.text(PROJECT_TITLE_FIELD) if after_item else None

        writable = [
            f"{label}（預期 {expected_title!r}，實際 {actual!r}）"
            for label, actual in (
                ("Issue title", issue_title),
                ("Project item content.title", content_title),
            )
            if actual != expected_title
        ]
        if writable:
            print(
                "[amend] body 已寫入，但標題寫入後讀回不符：" + "；".join(writable) + "。\n"
                "  ⚠️ 這兩個 surface 都是**寫得動**的（`gh issue edit --title` 直接寫 Issue，\n"
                "  content.title 就是它）⇒ 不符代表這一次寫入沒生效，⛔ 不是平台投影延遲。\n"
                "  本指令不猜，也不重試。重跑同一條 amend 即可再寫一次：\n"
                f"     wfcli amend {args.card_id} --feature '{args.feature}' "
                "--reason '<說明先前標題寫入為何中斷>'",
                file=sys.stderr,
            )
            return 8
        if project_title_field != expected_title:
            # ⚠️ 這是**註記不是警示**（需求方 2026-09-01 裁定甲）：它陳述一個已知且
            # 無出口的平台事實，⛔ 不暗示本次寫入有問題、⛔ 也不要求任何後續動作。
            print(
                f"[amend] 註記：Project 內建 `{PROJECT_TITLE_FIELD}` 欄仍是 "
                f"{project_title_field!r}（本次寫入值為 {expected_title!r}）。\n"
                "  這一格是 item **上板當下**的快照。wfcli 現行路徑寫不動它，"
                "已窮舉的 GraphQL ProjectV2 mutation 面裡也找不到 writer\n"
                "  （平台逐字：\"The title field can only be updated on DraftIssues\"）；"
                "⚠️ REST／匯出／webhook 面未量，⛔ 不宣稱全 API。\n"
                "  ⛔ 不是本次寫入失敗；⛔ 重跑本指令不會讓它收斂；⛔ Projects UI 上也沒有"
                "這一格的控制項。\n"
                "  ⚠️ 看板 UI 的 Title 欄顯示的是 content.title（＝新值）⇒ 目前已實測可讀到"
                "這個舊值的面，例子包括\n"
                "  GraphQL fieldValueByName(\"Title\") 與 gh project item-list 的頂層 title"
                "（⛔ 讀取面未窮舉）。⛔ 不得把它讀成「已同步」。",
                file=sys.stderr,
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
        # 第二個受條件保護的取值點。⚠️ 這裡已經在 `set_item_body` 之後 ⇒ 本輪早就
        # 寫過東西了，`ensure_fields` 排在它後面，⛔ 不落在「閘門前」那個區間。
        # ⛔ 不得為了「省一次呼叫」把這兩個取值點合併回函式頂端——那正是本卡拆開它的原因。
        fields = ensure_fields(runner, target.owner, target.project)
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

    provenance = "原值指紋已寫入 Log（原文見平台前一版）" if recoverable else "原值已完整寫入 Log"
    print(f"[amend] 已修訂 {args.card_id}（op {op_id}，{len(changes)} 個欄位，{provenance}）")
    for entry in changes:
        field_name, old, new, note = entry[:4]
        w_old, w_new = _where_for(entry, recoverable=recoverable)
        print(f"  - {field_name}：「{_short(old, 80, where=w_old)}」→「{_short(new, 80, where=w_new)}」")
        if note:
            print(f"    授權：{_short(note, 80)}")
    return 0
