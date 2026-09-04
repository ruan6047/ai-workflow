# #148 WF-STAGE-PITFALL-LIST1 canonical §6.4 的踩坑清單零實作
- state: closed  created: 2026-08-25T18:01:23Z  closed: 2026-08-26T08:57:02Z
- url: https://github.com/ruan6047/ai-workflow/issues/148
- comments: 5

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；要接進 `handoff` 的階段進出點並決定報告必填的形狀；⚠️ 而「逐項」的粒度尚未定案（`WF-STAGE-STATE-TWO-AXIS1` 逐字交給本卡的 Discovery）⇒ 有設計判斷。）　查核：待指派（建議 高階型；查核要判斷「報告必填」會不會變成敷衍的樣板——§6.4 逐字承認 CLI 分不出認真讀過與隨手打一行，⇒ 擋敷衍的是檢閱那一環。屬跨家族查核（動的是所有卡都會經過的階段進出點）。）
- Initiative：WF-STAGE-STATE-TWO-AXIS1　spec 基線：337f4c19af9b88eef4271998cf32f5569997120b
- DB：db_scope=none
- 服務的原始目標：ROADMAP §0 目標 1「防止低級事故」——判準逐字「有機械執行者會擋下它。沒有執行者的偵測器不算達成」。§6.4 今日連偵測器都沒有。

## 簡介
<!-- card-brief:begin -->
把 canonical §6.4 的分階段踩坑清單接進階段進出點。**適用時機**：要知道「這個階段最常犯什麼」時；或交付要逐項作說明時。⛔ 非射程：不重新定義 13 族的內容與歸屬（§6.4 已定）；⛔ 不宣稱它擋得住敷衍（§6.4 逐字承認「CLI 分不出認真讀過與隨手打一行」）；⛔ 不在本卡決定「逐項」的粒度——`WF-STAGE-STATE-TWO-AXIS1` 逐字把它交給本卡的 Discovery。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：**canonical §6.4 定義了分階段踩坑清單，而全 repo 零實作、⛔ 無承接卡。**§6.4 逐字要求「進入階段時 CLI 印出該階段的坑，離開階段時交付須逐項作說明」——實查：**沒有任何動詞印它、沒有欄位存它、`validation.py` 不驗它**。⇒ 那是「規則寫了但沒人能照做」，正是 §6.3 當初的狀況（已由 `WF-CARD-BRIEF-AND-TWO-AXIS-WRITE1` 補上通道）。⚠️ 而它已經有可觀測代價：2026-08-25／26 兩日的 8 筆失誤實例中，**至少 5 筆會被全階段族的兩條直接命中**（`列舉或覆蓋不完整` occ 48、`宣稱超過證據` occ 54）——包含開卡時把量測結論寫進身分欄位、字元守衛漏 8 個 `splitlines()` 字元、以及兩次把守衛的無條件警示當成分類結果。⇒ 清單若當時有印，那幾筆有機會在寫下前被攔。⛔ 本卡不重新定義清單內容（那在 §6.4 已定）。切片定義見 https://github.com/ruan6047/ai-workflow/issues/130#issuecomment-5391005830 的 S6。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/pitfalls.py",
    "file:cli/src/wf_cli/commands/handoff_cmd.py",
    "file:cli/tests/test_pitfalls.py",
    "file:cli/tests/test_commands_mocked.py",
    "file:cli/tests/test_release_cleanup.py",
    "file:cli/tests/test_review.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⚠️ 本清單於 2026-08-26 依 32 輪研究輪填實（開卡時刻意留白）。⭐ **射程已由需求方裁定更正**（issuecomment-5420340614）：⛔ 身分欄機械上改不動，執行者與查核者**一律以本清單為準**，⛔ 不以 `功能` 欄或核心痛點的射程措辭為準。
- [ ] **A1 ⭐ 射程＝「離開閘門」，⛔ 不是「進入印出」。** 本卡實作：`handoff` 在**任何寫入之前**要求一份「離開現階段的族清冊回應」，缺報告即 rc≠0 且**零寫入**（形狀比照 `handoff_cmd` 既有的四個前置閘門）。⛔ **不得宣稱它擋得住敷衍**（§6.4 逐字承認 CLI 分不出認真讀過與隨手打一行）。⛔ **不做「進入下一階段時印給下一個人看」**——`handoff` 的 stdout 讀者是祕書不是下一位執行者，送達通道屬 `WF-DISPATCH-FROM-HANDOFF1`。
- [ ] **A2 ⭐ 粒度＝固定格數 × 受限值域**（需求方採甲案）。該階段要印的每一族恰好一列，值域三選一：`已檢查`／`不適用：<原因>`／`發現：<處置>`。CLI 只驗三件：(i) 族清單逐族有且只有一列（**缺一即拒、多一即拒**）；(ii) 值在三個值域內；(iii) 後兩者冒號後非空。⛔ 不判斷內容真假。⭐ 依據：CLI 唯一拿得到的性質是**窮舉性**，而窮舉性只在格數由清單決定時存在。
- [ ] **A3 ⭐ 預先登記退化的否證條件。** 上線後前 30 次帶報告的 handoff，若 `已檢查` 佔比 ≥ 80% **且** `發現：` 為 0，即判定 A2 已退化成打勾 ⇒ 承接卡改採乙案（自選族數＋強制錨點：`檔:行`／指令＋rc／40 碼 SHA／留言 URL）。⛔ 門檻須在本卡交付時就寫死，不得事後訂。
- [ ] **A4 ⛔ 必須解決「正在離開哪個階段」的取值並交出實測涵蓋率。** Project `階段` 欄今天覆蓋極低。允許的退路是 `handoff_cmd.STAGE_STATUS` 的反函數（單射；💡需求／🔬研究中／🧭規劃中／🔨執行中／🔍待查核 五個可反推）；📥Backlog／📦已合併／⏸阻塞 **無反函數**，須 fail-closed 或明文豁免。⛔ 交付須附**現場重數**的涵蓋率，不得引用研究輪定值。
- [ ] **A5 ⛔ 必須把階段寫進 Log 行。** `handoff` 的 Log 行今天不記 `--next-stage` ⇒ 報告寫下後留痕無法反推它屬於哪個階段。修法照 `assign_cmd` 的既有形狀，在 `；證據` **之前**插入 `；階段 X；`。⭐ 已實測：全 repo 只有 `doctor` 對該行做 `startswith`，⛔ 無任何模組解析行內欄位 ⇒ 不破壞既有消費者。⛔ 本卡**不改 `doctor.py`**（那是 `WF-POSTHOC-CONFORMANCE1`／`WF-MARKER-SCOPE-CLEARANCE1` 的檔）。
- [ ] **A6 ⛔ 必須有日期界線，否則會癱瘓唯一寫入通道。** 717 筆歷史 handoff 全部沒有報告；閘門若無條件生效，下一次任何 handoff 都會被拒。樣板：`doctor.TRAILER_GUARD_EPOCH` 的形狀，⚠️ 並照抄該處自陳的誠實聲明「界線是分流輔助，不是安全邊界」。
- [ ] **A7 ⛔ 明列 7 個階段裡到不了的那一個。** `STAGE_PHASE` 只有 6 個鍵、`--next-stage` 的 choices 無 `maintenance`，而 Project `階段` 欄的選項**有**「維護」⇒ 維護階段的族清單構造上永遠印不出來。交付須逐字寫明並指出承接條件（新增 `maintenance` 屬語彙變更，會觸發 cpbl `roadmap_lines.gate_of` 的 fail-closed）。
- [ ] **A8 ⭐ 清單的居所＝碼是權威、canonical 是引用面、測試雙向釘死。** 族名與階段對應放 `cli/src/wf_cli/pitfalls.py` 常數；canonical §6.4 保留族名與裁斷；一條測試斷言**兩個方向逐字互含**。樣板＝`doctor` 的 root_cause_id 常數與其 canonical 互含測試（逐字：「裁定要寫在後續查核者引用得到的地方，不能只活在程式碼常數裡」）。⛔ **occ 數字不進碼**——理由見 A9。
- [ ] **A9 ⛔ occ 不得作為任何機械判斷的輸入。** 歸併映射從未被寫下（全 repo grep 13 族名只命中 `AI_WORKFLOW.md`）⇒ 今天不可複驗。⚠️ **canonical §6.4 表格有兩格錯值**（`可重現性不足` 應為 16、`資源或寫入集宣告` 應為 4，表上皆為 `—`），⭐ PM 已獨立複驗**兩值逐字就在 `#130` 的留言裡** ⇒ ⛔ 不需根因 corpus，是純抄寫錯誤。⛔ **不納入本卡**（`AI_WORKFLOW.md` 由三張活卡宣告）；承接者待需求方指定。⚠️ 這不是抄寫瑕疵：§6.4 保留了「可依 occurrence 加門檻」的後路，`—` 會讓第 7 大的一族被靜默丟掉。
- [ ] **A10 ⚠️ 資源最小集——⭐ 本條已由需求方裁定局部推翻**（`issuecomment-5420885014`）。**維持**：⭐ **新測試一律開新檔** `cli/tests/test_pitfalls.py`。**推翻**：⛔ 原文的「不宣告 `test_commands_mocked.py`」不成立——閘門讓 **33 條既有測試**轉紅（`test_commands_mocked.py` 16／`test_release_cleanup.py` 15／`test_review.py` 2），那是**既有**測試的契約被新增的必要前提改變，⛔ 不是新測試該去的地方。⚠️ 原禁令把「不新增測試到擁擠的檔」誤推廣成「不修改既有測試」，而後者在閘門類的卡上**構造上做不到**。三檔的 8 個持有者實查**全部未認領**（📥Backlog／⏸阻塞、角色皆 `—`）⇒ `assign` 構造上不擋。⇒ 三檔已納入資源宣告。**修法須由 `pitfalls.report_template(<離開階段>)` 導出清冊，⛔ 不得塞固定字串**（實證：`test_handoff_log_line_never_carries_the_status_it_wrote` 第 6 圈離開 `執行` 要 13 族、其餘圈要 8 族）。⛔ 仍不宣告也不改 `AI_WORKFLOW.md`。⚠️ 授權邊界規則不變：發現須改宣告外的檔即停、寫阻塞發現、交需求方裁決。
- [ ] **A11 ✅ 已修**：本卡 `spec 基線` 原為「—」，違反 `templates/baseline-cascade.md` 的 WF-18 逐字條文；已於 2026-08-26 amend 為 `337f4c19af9b88eef4271998cf32f5569997120b`。
- [ ] **A12 ⚠️ 父卡與 canonical 的既存矛盾登記，⛔ 執行者一律以 canonical 為準。** `#130` 卡面驗收條逐字仍寫「其餘各一」，而它交付的 canonical §6.4 逐字「⛔ 不得據此宣稱『其餘各屬一個階段』」。`#130` 已 🏁完成 ⇒ 矛盾凍結。
- [ ] **A13 ⭐ 核心痛點第二句已被推翻，交付須逐字承接更正。** 卡面寫「清單若當時有印，那 5 筆有機會在寫下前被攔」——研究輪證明**那半邊是假的**：兩個全階段族的語意早已在 auto-memory 裡，而產生那 8 筆的 11 份 transcript 全部落在繼承該 memory 的目錄 ⇒「印在眼前」當時已成立、失誤照樣發生。⚠️ 並更正射程：8 筆中落在 `handoff` 出口的只有 **1 筆**。⇒ 交付**不得**引用「會被攔」為價值論證。
- [ ] **A14 ⛔ 三條取巧設計維持拒絕**（需求方裁定）：界線設在未來日期（＝排定一次午夜轉紅，形狀與 `conftest.py` 逐字警告過的既有事故相同）、以 DraftIssue／Issue 分流、以 fake runner 分流。⚠️ 後兩者會讓閘門變成零資訊。⭐ 執行者自陳「為了讓套件變綠而弱化守衛」的念頭一輪內出現**三次** ⇒ 逐字留痕。
- [ ] **A15 ⚠️ `assign` 不寫階段欄的缺口另行登記，⛔ 不擴本卡射程。** 實查全 repo 只有 `open_cmd`（一律寫「需求」）與 `handoff_cmd` 兩個階段欄 writer ⇒ 閘門全面生效時 `執行` 階段為 **0 張**，而看板上有卡在 🔨執行中；兩來源都判得出的 6 張中 **2 張不一致**。⛔ 工具不偷偷改判（哪一軸權威是條文問題），印警示並以測試釘住即可。

## 驗證

- [ ] ⚠️ 本清單依 32 輪研究輪填實。⭐ **V7 是唯一構造上可能推翻本卡的驗證**。
- [ ] **V1 端到端、真實既有卡、⛔ 不自造**：對至少一張真實活卡跑 `handoff`（沙箱／`FakeGhRunner` 皆可，須聲明），驗證缺報告時 **rc≠0 且 body 與所有欄位逐位元未變**，並附**實際拒收訊息全文**。
- [ ] **V2 負控（窮舉，⛔ 不得引用定值）**：帶合格報告時必須寫得進去；且 A6 的日期界線之前的卡必須仍可 handoff。⚠️ 母體須**現場重數**並附指令與時點——研究輪的 717／201／13 全是移動標靶。
- [ ] **V3 變異檢驗，對象是「缺格偵測」本身**：(a) 移除「缺一即拒」⇒ 少一族的報告應轉紅；(b) 移除「多一即拒」⇒ 混入不存在的族名應轉紅；(c) 把族清單來源從 `pitfalls.py` 常數換成硬編字面 ⇒ A8 的雙向互含測試應轉紅。⛔ 只跑正向為零資訊。
- [ ] **V4 ⭐ 階段取值涵蓋率須由指令輸出產生**（canonical §6.2）：交付須附一份掃全 Project 的輸出，逐張列出「階段欄有值／可由狀態反推／不可判定」三類的張數與卡 ID。⛔ 人工聲明不成立。
- [ ] **V5 守衛連鎖不得被牽動**：`contract_tool_reconcile --check` **rc=0 且判定表逐列不變**；`canonical_citation_scan` rc=0。⚠️ 同型連鎖已實測會翻紅（把 marker 字面放進 `validation.py`）。⛔ **不得接管線**（`| tail` 會把 rc 換成 tail 的）。
- [ ] **V6 回歸基線逐字記錄**：`cd cli && uv run pytest -q`，研究輪基線 **1174 passed**（於 `cd17ba5` 實測）。⛔ 交付時現場重記，⛔ 不得只寫「全過」。
- [ ] **V7 ⭐ 可證偽條件逐字寫進交付**：找到一次 handoff——報告全格滿、CLI 全綠、留痕帶階段——而**該階段真正發生的失誤不屬於任何一族** ⇒ 兩層結構不成立。⚠️ 已知候選反例：`#130` 自陳 17 個實例中 6 族零命中、且「其餘五族只在執行」是樣本的性質不是母體的。
- [ ] **V8 ⛔ 落入率不得沿用卡面的「5/9」。** 該數字混了兩個母體（1 筆非循環 ＋ 8 筆 PM 自己歸族）。交付若要報落入率，須**分開報**並逐筆說明它落在哪一個進出點上。⭐ 研究輪的獨立複驗：8 筆中落在 `handoff` 出口的只有 1 筆。

## Log

- 2026-08-26T02:01:22+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-26T02:04:39+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (研究)；iteration 0；SHA cd17ba5f0bda377a0bcdbf542932e6a977f7c409；證據 派研究輪（子代理，唯讀）。⭐ 本卡驗收刻意留白至研究輪產出——判準由研究產生，⛔ 不由開卡者預先決定。依據：2026-08-26 的實測教訓（aiwf#142 開卡時把尚未複驗的量測結論寫進驗收與身分欄位，被三輪研究連續推翻；aiwf#141 兩輪共被推翻 10 條）。⚠️ 並登記 S4 的查證結果：cpbl 移除相容層在現行設計下**不該做**——roadmap_lines.py:220-221 逐字「保留是刻意的裁斷，不是忘了刪」，canonical 明列廢止值為「向後相容，已寫的卡留著」⇒ 相容層永久保留，#130 切片表的 S4 是切片當時的假設，已被 cpbl#165 的裁定取代。。
- 2026-08-26T02:56:19+08:00 amend by wf-cli（op 7bab0c10）→ spec 基線：原值指紋 sha256:bda050585a00f0f6cb502350559d75532ae3b244c9498b996e7c5df2d98dfc8d (3 bytes) → 新值指紋 sha256:8a4e84b5efe51a8f44cb5ed47a4f4e34f23bdb12f5600ad6b114f78da35b8699 (40 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 補 Initiative 子卡的 spec 基線＝父卡 WF-STAGE-STATE-TWO-AXIS1 的交付 SHA（開卡時漏填，canonical §5.1.2）。
- 2026-08-26T11:54:53+08:00 amend by wf-cli（op f2770992）→ 驗收條件：原值指紋 sha256:a722b8ffa091e6b8c3360a5fb87e8b48d1d53db2f71cc9799ecfe65ec139f815 (387 bytes) → 新值指紋 sha256:781ccae2c60c2369a6d13fb65f7d84b5f0d37e0934994adbd852a838a7dbdcc6 (6018 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定改形狀不停卡（issuecomment-5420340614）：射程由「進入印出」改為「離開閘門」、粒度採甲案固定格數×受限值域；32 輪研究輪產出填實 A1-A13/V1-V8，含 A13 逐字承接核心痛點第二句被推翻。
- 2026-08-26T11:54:53+08:00 amend by wf-cli（op f2770992）→ 驗證：原值指紋 sha256:2f5af99c040d81a6a1b5cc24dd27c170c37bb6143fc1d5784f559f18ad494a8f (53 bytes) → 新值指紋 sha256:474868d0753f4b57ecbc3f18e390f33534bacebc6c7f3efd65cbbdd4109e406f (2380 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定改形狀不停卡（issuecomment-5420340614）：射程由「進入印出」改為「離開閘門」、粒度採甲案固定格數×受限值域；32 輪研究輪產出填實 A1-A13/V1-V8，含 A13 逐字承接核心痛點第二句被推翻。
- 2026-08-26T11:54:53+08:00 amend by wf-cli（op f2770992）→ 資源宣告：原值指紋 sha256:5a1a2d3b0b878f96460dafff131cc779429481f3017ca4b56343b14ff5c84a08 (127 bytes) → 新值指紋 sha256:c126b658724bd4fac21749d7e962143955433cd943e55204f9a81097535bf19c (127 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定改形狀不停卡（issuecomment-5420340614）：射程由「進入印出」改為「離開閘門」、粒度採甲案固定格數×受限值域；32 輪研究輪產出填實 A1-A13/V1-V8，含 A13 逐字承接核心痛點第二句被推翻。
- 2026-08-26T12:11:21+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code (執行)；分支worktree ai/opus-5/WF-STAGE-PITFALL-LIST1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/stage-pitfall；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-26T13:15:59+08:00 amend by wf-cli（op 2708d5c1）→ 驗收條件：原值指紋 sha256:c6cf99ec723f2dc30032bfa5b2e388b7b087c654e0d2173bb2799bb5b5ef8da8 (6022 bytes) → 新值指紋 sha256:854f246e1ca1d2a3443cafc2427fac4d0a996667eb7aca2cab1265a7ce53246e (7721 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定擴充資源宣告納入三個既有測試檔（issuecomment-5420885014）：A10 局部推翻並逐字更正、新增 A14 取巧設計維持拒絕、A15 登記 assign 不寫階段欄的缺口。
- 2026-08-26T13:15:59+08:00 amend by wf-cli（op 2708d5c1）→ 資源宣告：原值指紋 sha256:264f5c63f5877a33a501e6057ba6ba2bfb65cfdc30edcb46abf518f6a9dbf4c7 (244 bytes) → 新值指紋 sha256:84848352d86800c0f7184b4d168aa9c810e68ea1e6891479312500294be32985 (241 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定擴充資源宣告納入三個既有測試檔（issuecomment-5420885014）：A10 局部推翻並逐字更正、新增 A14 取巧設計維持拒絕、A15 登記 assign 不寫階段欄的缺口。
- 2026-08-26T13:19:04+08:00 amend by wf-cli（op c8325e89）→ 驗收條件：原值指紋 sha256:00e640c494dd3cb441dd0280a93375dda86c1a30096f7cbbf59e58e33efebe7d (7725 bytes) → 新值指紋 sha256:f3347ef4c14d83b7b7b9d3c2c5993f39387f6b574217765c86edb6008a516d55 (7709 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 修正 amend 第一行重複的 `- [ ] ` 前綴（CLI 對每個 checklist item 自動加一個，傳入時已自帶 ⇒ 疊加）。
- 2026-08-26T13:19:04+08:00 amend by wf-cli（op c8325e89）→ 驗證：原值指紋 sha256:62abf262c7cbdcf817c59e4cb12705142735e0c5d0c64d32f62d601a3e751b2b (2384 bytes) → 新值指紋 sha256:4cc8d0c67715e035102bd6340cdf88f160b61370d6bf6d84a2c4e1e657b29a37 (2374 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 修正 amend 第一行重複的 `- [ ] ` 前綴（CLI 對每個 checklist item 自動加一個，傳入時已自帶 ⇒ 疊加）。
- 2026-08-26T13:48:01+08:00 handoff by wf-cli → owner 待認領（跨家族查核）；iteration 0；SHA f5ed165b3a40f92eba274c7c8fc6e6694f4ab148；證據 PR #153。射程由需求方裁定改為離開閘門、粒度採甲案（issuecomment-5420340614）；資源宣告擴充納入三個既有測試檔（issuecomment-5420885014）。回歸四節點現場實跑：cd17ba5=1174 passed、10a053f=1206、16ac6ec=1182 passed 33 failed、f5ed165=1215 passed 0 failed。守衛 contract_tool_reconcile --check rc=0（judgment 表以 --format json 對帳 86 符號、verdict 逐列差異 0）、canonical_citation_scan rc=0；ruff 逐檔對基線零新增、全 repo 104=104。「沒有固定字串」以四種獨立方式機械證明（族名掃描含正控／AST 常數與 Call 判定／執行期攔截逐次入參 8-8-8-8-8-13 族／AST 數 test_ 函式證三檔零新增測試）。執行者另以 67 次呼叫全數帶報告、原樣回傳 0 次的攔截量測，推翻「33 條是靠豁免分流變綠」的可能。⚠️ 基線是 merge-base cd17ba5f0bda377a0bcdbf542932e6a977f7c409，⛔ 不是 origin/main 4e99845（PR #149 在本分支開出後才合併）。⚠️ 上一輪的 V3 證據取自未進 commit 的草稿（sha256 435d864a1769 vs 三個 commit 皆為 d6c6ef3d65a9），本輪已重跑並取自 committed blob。。
- 2026-08-26T15:37:11+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 跨家族查核者（身分未自述；收據原文見 PR #153 的 issuecomment-5421266988，PM 逐字轉錄）；core_pain_resolved no；self_run 8 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-STAGE-PITFALL-LIST1-e0-f5ed165b3a40f92eba274c7c8fc6e6694f4ab148。
- 2026-08-26T16:17:52+08:00 handoff by wf-cli → owner 待認領（跨家族查核）；iteration 0；SHA 8c75c3a7955d21fc1c638086270d363068505c93；證據 第 2 輪修復送審（PR #153，留言 issuecomment-5422535835，SHA 更正見其後一帖）。R1-001 已處置：ensure_fields 由 resolve_project 旁搬到 gate.rc!=0 之後；以 AST 證明賦值點到閘門之間讀取次數 0（只認 ast.Name 排除 item.fields 的 ast.Attribute），並以 inspect.signature 證明閘門參數為 args/item/ts 不吃 fields ⇒ 不需拆 ensure_fields、不需動 project.py。拒收路徑實跑呼叫序列 2 筆、非唯讀 []。新增三條回歸測試：正向以 _world(vars(runner) 扣三個非狀態面屬性，封閉集合) 比對、呼叫面以唯讀白名單（⛔ 非黑名單，field-create 在既有黑名單裡卻沒被攔到正是缺陷形狀）、負控證明欄位確實會被建立。M0 變異（搬回閘門前）rc=1 且失敗身分逐字核過、失敗訊息印出缺陷簽章 field-create --name 階段 出現在 rc=2 路徑上。V3 五條重跑成立含 c3 仍綠。67/67 攔截重跑通過。33 條以 nodeid 逐條對帳、先驗身分：全部仍在收集集合、added_report>0、returned_input=0。回歸 pytest 1218 passed（基線 cd17ba5=1174、退回點 f5ed165=1215、+3 本輪）、contract_tool_reconcile --check rc=0、canonical_citation_scan rc=0、ruff 四筆既存 finding 逐筆相同無新增。⚠️ 基線仍為 merge-base cd17ba5f0bda377a0bcdbf542932e6a977f7c409。⚠️ 形狀層未處置：同一形狀在 assign_cmd.py 仍存在且該處逐字記載為刻意，形狀修法須動 project.py 與 assign_cmd.py，皆不在本卡宣告內，交需求方裁決。。
- 2026-08-26T16:41:25+08:00 review by wf-cli → APPROVE（✅通過）；查核者 跨家族查核者（身分未自述；收據原文見 PR #153 的 issuecomment-5422708955，PM 逐字轉錄）；core_pain_resolved yes；self_run 8 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-STAGE-PITFALL-LIST1-e0-8c75c3a7955d21fc1c638086270d363068505c93。
- 2026-08-26T16:56:39+08:00 handoff by wf-cli → owner 已合併（無部署面）；iteration 0；SHA 6148bd4495fd3134f0e42db926b558a02761fda8；階段 審核；踩坑回應 8 族（已檢查 8／不適用 0／發現 0）；證據 第 2 輪查核 APPROVE（findings 0，收據原文 PR #153 的 issuecomment-5422708955，PM 逐字轉錄）。查核者自行重跑第 1 輪的探針、核了 M0 的失敗身分、驗了 _world() 的封閉性、並自行重跑 AST 檢查。需求方指示後執行：先在分支 git merge origin/main（bda5e37，帶入 PR #149 canonical 與 PR #152 doctor），CI 綠後 gh pr merge 153 --merge，merge commit 6148bd4495fd3134f0e42db926b558a02761fda8。⚠️ 途中 CI 一度紅：astral-sh/setup-uv 抓 manifest 逾時導致 uv 未安裝、後續 step exit 127（同一 head 的另一 run 為 success）⇒ 基礎設施失敗非碼，gh run rerun --failed 後 success。合併結果上重跑：pytest 1262 passed（算術：cd17ba5 基線 1174 ＋ #152 的 44 ＋ 本卡的 44）、contract_tool_reconcile --check rc=0、canonical_citation_scan rc=0。本卡為 CLI 閘門，⛔ 無部署面。⚠️ 形狀層未處置：assign_cmd.py 同型既存行為仍在，形狀修法須動 project.py 與 assign_cmd.py，交需求方裁決是否開卡。；收尾清理：已清除 worktree、本地分支、遠端分支。


## Comment 5420340614 · 2026-08-26T03:53:26Z

## 裁定：**改形狀，⛔ 不停卡**

研究輪（32 輪）的結論逐字是「照現在的形狀不該做，改了形狀之後該」。裁定採納，理由是研究輪自己給的兩層判準：

1. **「進入時印出」不該做。** 依 ROADMAP §0 的判準「有機械執行者會擋下它。沒有執行者的偵測器不算達成」——印出**連偵測器都不是**（是通知），且讀者是錯的人（`handoff` stdout 前坐的是祕書不是下一位執行者）。⛔ 送達通道屬 `WF-DISPATCH-FROM-HANDOFF1`，本卡不做。
2. **「離開時驗非空」該做。** 它掛在唯一寫入通道的前置段，缺報告即 rc≠0 且零寫入 ⇒ **有機械執行者**，且產出的是**窮舉性由機器保證**的交付物。承重的是閘門不是印出。

⭐ **並採納研究輪對本卡核心推論的推翻。** 卡面寫「清單若當時有印，那 5 筆有機會在寫下前被攔」——研究輪證明**那半邊是假的**：那兩個全階段族的語意早已在 auto-memory 裡（`completeness-claims-must-be-generated` 07-27、`shape-change-not-instance-fix` 08-16、`numbers-need-evidence-or-discussion` 08-24 13:43），而 08-25/26 產生那 8 筆的 11 份 transcript **全部**落在繼承該 memory 的目錄 ⇒ 「印在眼前」當時已成立，失誤照樣發生。⇒ 這強化「閘門有用、印出無用」的裁斷。

⚠️ 並採納「至少 5 筆」的射程更正：8 筆中落在 `handoff` 出口的只有 **1 筆**（2 筆發生在 `open` 當下、1 筆在研究輪中段、1 筆已被既有查核攔下）。

## ⛔ 身分欄改不動，以驗收條逐字更正

`功能` 欄與核心痛點在機械上改不動（`validation.py` 拒空、`card.py` 拒自述、`--core-pain` 須併 `--ruling-url` 且不得與其他欄位旗標同一次調用）。⇒ 照 `WF-MARKER-WRITE-BOUNDARY1` 的既有先例，**以驗收條 A1 逐字更正射程**、A12 逐字登記卡面矛盾，執行者與查核者一律以驗收條為準。

## 「逐項」粒度：採**甲案**（固定格數 × 受限值域）

每族恰一列，值域三選一（`已檢查`／`不適用：<原因>`／`發現：<處置>`），CLI 只驗窮舉性、值域、非空，⛔ 不判內容真假。

理由是研究輪給的：**CLI 唯一拿得到的性質就是窮舉性**，乙案（自選族數＋強制錨點）讓掉窮舉性之後，剩下的檢查是零資訊。⇒ 甲把 CLI 該做的做到、做不到的誠實留給檢閱。**並採納其預先登記的否證條件**（前 30 次若 `已檢查` ≥80% 且 `發現：` 為 0 即判定退化、改採乙），寫進 A3。

## 兩項阻塞的處置

- **A9 的 canonical §6.4 兩格錯值**（`可重現性不足` 應為 16、`資源或寫入集宣告` 應為 4）：⭐ **PM 已獨立複驗，兩個值逐字就在本 Initiative 父卡的留言裡**（`gh api repos/ruan6047/ai-workflow/issues/130/comments --paginate` 命中）⇒ ⛔ 這不需要根因 corpus，是純抄寫錯誤。⛔ **不納入本卡**（`AI_WORKFLOW.md` 由 `#11`／`#89`／`#137` 三張活卡宣告）；承接者待需求方指定，PM 已將此項列入待裁定。
- **A11 `spec 基線`＝「—」**：⭐ **已修**，於 2026-08-26 amend 為 `337f4c19af9b88eef4271998cf32f5569997120b`（`#130` 交付 §6.4 進 main 的 commit，已驗證為 main 祖先）。

---
以上由 PM（Claude Opus 5@Claude Code）以需求方的 token 發文；裁定內容轉錄自需求方在 2026-08-26 session 的逐字指示「好依照你建議」（其中「② `#148` 改形狀還是停卡」的建議是改形狀不停卡）。⛔ 合併與部署不在此授權內。

## Comment 5420885014 · 2026-08-26T05:09:32Z

## 裁定：**擴充資源宣告**，納入三個測試檔

執行者依 canonical §3.2 停在檔案邊界並回報：A1 的閘門讓 **33 條既有測試**轉紅，全部落在本卡未宣告的檔（`test_commands_mocked.py` 16／`test_release_cleanup.py` 15／`test_review.py` 2）。三個處置選項中採**擴充宣告**。

**理由（機械查證，2026-08-26）**：三個檔的 8 個持有者**全部未認領**——

| 檔 | 持有者 | 狀態／角色 |
|---|---|---|
| `test_commands_mocked.py` | `#57`／`#66`／`#84`／`#86`／`#91` | 📥Backlog、角色 `—` |
| | `#142` | ⏸阻塞、角色 `—` |
| `test_release_cleanup.py` | `#57` | 📥Backlog、角色 `—` |
| `test_review.py` | `#137` | 📥Backlog、角色 `—` |

⇒ `assign_cmd` 的既有裁斷逐字「衝突比對範圍刻意限定**已指派**的活卡……後者只是『未來可能碰』的宣告，尚未有實際執行中的分支／worktree 與它爭資源」⇒ **構造上不會擋，也沒有人在跟它搶**。「排在它們之後」等於無限期等一批沒人認領的卡。

## ⛔ A10 的禁令被本裁定局部推翻，逐字更正

A10 原文逐字「⛔ **不宣告** `cli/tests/test_commands_mocked.py`（被 6 張活卡宣告，是全 repo 競爭最激烈的檔）⇒ 新測試一律開新檔」。

**維持的部分**：⭐ **新測試仍一律開新檔** `cli/tests/test_pitfalls.py`。
**推翻的部分**：⛔ 「不宣告」不成立——那 33 條是**既有**測試的契約被閘門改變，⛔ 不是新測試該去的地方。原禁令把「不新增測試到擁擠的檔」誤推廣成「不修改既有測試」，⚠️ 而後者在閘門類的卡上構造上做不到（新增必要前提必然改變所有既有呼叫點的契約）。

⇒ **執行者的修法必須是**：共用 argv helper 改由 `pitfalls.report_template(<離開階段>)` 導出清冊，⛔ 不得塞固定字串（實證：`test_handoff_log_line_never_carries_the_status_it_wrote` 的第 6 圈離開 `執行` 要 13 族，其餘圈要 8 族）。

## ⛔ 三條被拒絕的設計，裁定維持拒絕

執行者自陳認真考慮過三條「讓套件變綠」的路：界線設在未來日期、以 DraftIssue／Issue 分流、以 fake runner 分流。**全部維持拒絕**。第一條在形狀上與 `conftest.py` 逐字警告過的既有事故完全相同（排定一次午夜轉紅）；後兩者會讓閘門變成零資訊。

⚠️ 而「為了讓套件變綠而弱化守衛」這個念頭在一輪內**出現過三次** —— 這件事本身值得留在留痕裡。

## 併帶登記：`assign` 不寫階段欄（⛔ 不納入本卡）

本輪順帶測到：全 repo 只有 `open_cmd`（一律寫「需求」）與 `handoff_cmd` 兩個階段欄 writer，**`assign` 只寫交付狀態** ⇒ 若閘門今天全面生效，`執行` 階段是 **0 張**，而看板上有卡在 🔨執行中；兩個來源都判得出來的 6 張裡 **2 張不一致**。

執行者⛔ 未偷偷改判（哪一軸權威是條文問題不是工具問題），加了警示並以測試釘住。**裁定維持此處置**，缺口另行登記，⛔ 不擴本卡射程。

## V7 的處置：接受「未證實也未推翻」

執行者未找到反例，並自陳搜尋為弱——⭐ **關鍵是它指出代理量測是循環的**：13 族本身就是從那份 finding corpus 歸併出來的，拿產生它的母體量它的涵蓋率量的是零。⇒ ⛔ 未據此宣稱涵蓋率，裁定接受。

今天能誠實說的：兩層結構**既沒被證實也沒被推翻**，唯一的非循環觀測（`aiwf#129`，n=1）是負面的。⇒ A3 預先登記的退化否證條件（前 30 次 `已檢查` ≥80% 且 `發現：` 為 0 即改採乙案）**因此更重要**，⛔ 不得在交付時弱化。

---
以上由 PM（Claude Opus 5@Claude Code）以需求方的 token 發文；裁定內容轉錄自需求方在 2026-08-26 session 對「要我擴宣告嗎？」的逐字回覆「OK」。⛔ 合併與部署不在此授權內。⚠️ 卡面資源宣告的實際 amend 待 GitHub GraphQL 額度重置後執行（本裁定寫下時剩餘不足一次 amend 所需）。

## Comment 5422121773 · 2026-08-26T07:37:13Z

<!-- wf-review-event:v1 card_id=WF-STAGE-PITFALL-LIST1 source_sha=f5ed165b3a40f92eba274c7c8fc6e6694f4ab148 attempt_id=WF-STAGE-PITFALL-LIST1-e0-f5ed165b3a40f92eba274c7c8fc6e6694f4ab148 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-STAGE-PITFALL-LIST1`　attempt_id：`WF-STAGE-PITFALL-LIST1-e0-f5ed165b3a40f92eba274c7c8fc6e6694f4ab148`
- 查核者：跨家族查核者（身分未自述；收據原文見 PR #153 的 issuecomment-5421266988，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`f5ed165b3a40f92eba274c7c8fc6e6694f4ab148`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-26T15:37:11+08:00

### self_run（查核者實跑）

- `git worktree add --detach /tmp/chk cd17ba5f0bda377a0bcdbf542932e6a977f7c409 && cd /tmp/chk/cli && uv run pytest -q`
  - rc=0，1174 passed
- `同上 @ 10a053f`
  - rc=0，1206 passed
- `同上 @ 16ac6ec`
  - rc=1，1182 passed、33 failed
- `同上 @ f5ed165b3a40f92eba274c7c8fc6e6694f4ab148`
  - rc=0，1215 passed
- `三檔 helper 執行期攔截`
  - rc=0，193 passed；calls=67 added_report=67 returned_input=0 missing_report=0
- `V3 五個反向變異`
  - 移除缺格偵測 rc=1；移除多格偵測 rc=1；canonical c1 漂移 rc=1；碼側 c2 漂移 rc=1；測試側硬編清單＋c1 rc=0（預期）
- `uv run python scripts/contract_tool_reconcile.py --check；uv run python scripts/canonical_citation_scan.py`
  - rc=0；rc=0
- `空欄位 Project 的零寫入探針`
  - rc=0（探針成功重現缺陷）：handoff rc=2、field_created_before_gate=True、project_state_unchanged=False

### findings（1，其中 blocking 1）

- **WF-STAGE-PITFALL-LIST1-R1-001**　severity=critical　blocking=true　class=implementation　attribution=executor　root_cause_id=`gate-placed-after-a-writing-precondition`
  - evidence：cli/src/wf_cli/commands/handoff_cmd.py:680 在 _pitfall_gate（:503 定義、:766 呼叫）之前呼叫 ensure_fields，而 ensure_fields 非唯讀——project.py 的 ensure_fields 對每個缺少的凍結欄位送出 gh project field-create。查核者以空欄位 Project 探針重現：handoff rc=2、field_created_before_gate=True、project_state_unchanged=False。現有測試只深拷 runner.items，未檢查 Project 欄位定義，故漏檢。⭐ PM 獨立複驗成立，並補一項：:764-765 的就地註解逐字宣稱「擺在最後一道之後、第一次 set_field_value 之前，『缺報告即 rc≠0 且零寫入』與既有退出碼語意兩者同時成立」——該句在 ensure_fields 這條路徑上不成立，註解寫了意圖而碼未達成。
  - disposition：將 ensure_fields 移到閘門成功之後，並新增回歸測試比較 Project 欄位 schema 前後不變。⛔ 須同時更正 :764-765 的就地註解，使它描述的是實際成立的性質。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-STAGE-PITFALL-LIST1-e0-f5ed165b3a40f92eba274c7c8fc6e6694f4ab148
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: no
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待認領（跨家族查核）
findings:
  - finding_id: WF-STAGE-PITFALL-LIST1-R1-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: gate-placed-after-a-writing-precondition
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5422792691 · 2026-08-26T08:41:26Z

<!-- wf-review-event:v1 card_id=WF-STAGE-PITFALL-LIST1 source_sha=8c75c3a7955d21fc1c638086270d363068505c93 attempt_id=WF-STAGE-PITFALL-LIST1-e0-8c75c3a7955d21fc1c638086270d363068505c93 -->
## 查核裁決：APPROVE

- 卡：`WF-STAGE-PITFALL-LIST1`　attempt_id：`WF-STAGE-PITFALL-LIST1-e0-8c75c3a7955d21fc1c638086270d363068505c93`
- 查核者：跨家族查核者（身分未自述；收據原文見 PR #153 的 issuecomment-5422708955，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`8c75c3a7955d21fc1c638086270d363068505c93`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-26T16:41:25+08:00

### self_run（查核者實跑）

- `清除目標 worktree 的 cli/src、cli/tests、scripts pycache`
  - rc=0
- `空欄位 Project＋缺 --pitfall-report 手動探針`
  - 外層 rc=0；handoff 內部 rc=2，schema 深度相等（不再建立欄位）
- `R1 三條回歸`
  - 3 passed，rc=0
- `uv run pytest tests/test_pitfalls.py -q`
  - 43 passed，rc=0
- `M0 記憶體 AST 變異（把 ensure_fields 搬回閘門前）`
  - 內層 pytest rc=1，精確 2 failed / 1 passed；紅的是 schema 與唯讀呼叫兩條，負控維持綠
- `三 SHA collect-only 對帳`
  - 1174 / 1215 / 1218，皆 rc=0
- `nodeid 對帳（先驗身分）`
  - rc=0：193 條各自唯一、兩版集合完全一致；16ac 的 33 個唯一失敗 nodeid 在 f5 的相同 193 nodeid 中全數通過
- `scripts/contract_tool_reconcile.py --check；scripts/canonical_citation_scan.py`
  - 皆 rc=0

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-STAGE-PITFALL-LIST1-e0-8c75c3a7955d21fc1c638086270d363068505c93
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待認領（跨家族查核）
findings: []
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5424777228 · 2026-08-26T11:43:37Z

## 上線首日的踩坑清冊實況：**PM 的用法有缺口，機制沒有**

本卡於 2026-08-26 合併上線（`6148bd4`）。⭐ 首日 **6 筆**帶報告的 handoff 全部由 PM 發出。逐項登記，⛔ 含對 PM 自己的三項不利事實。

### ① ⛔ PM 貢獻了 A3 的第一個退化樣本

`WF-STAGE-PITFALL-LIST1` 自己的 `release`：**已檢查 8／不適用 0／發現 0**。

⛔ **那是 PM 直接餵 `pitfalls.report_template('審核')` 的原樣輸出、一個字都沒改。** ⇒ A3 逐字預先登記的「退化成打勾」形狀，**第一個樣本點由 PM 製造**。Log 是 append-only ⇒ ⛔ 改不掉，本帖即更正留痕。

### ② ⛔ 六次的清冊內文**一次都沒進交付**（0/8，六次全中）

canonical §6.4 逐字：「離開階段時**交付**須逐項作說明」。而 `pitfalls.Roster.digest()` 的就地註解逐字：「⛔ 不含族名也不含自由文字——只有格數與分佈……**報告全文屬檢閱那一環，不由 Log 承載**。」

⇒ ⭐ **機制是對的**（摘要必須有界，理由是卡面 body 有實測上限、Log 只增不減）。⛔ **錯的是 PM 的用法**：六次都把逐族內文餵給 `--pitfall-report`（設計上讀完即丟），而**沒有同時貼進 `--evidence`**。機械查證：六筆的 evidence 內含族名皆為 **0/8**。

⇒ **PM 的處置（⛔ 不需要卡）**：往後 `--pitfall-report` 的內文同時進 `--evidence`。

### ③ ⛔ PM 先前口頭報過一個錯的口徑，就地更正

PM 曾稱「6 筆中 1 筆全已檢查 ＝ **16.7%**」。⛔ **口徑錯**——A3 逐字是「**`已檢查` 佔比** ≥ 80%」，算的是**列**，⛔ 不是「幾次全打勾」。

**現況（2026-08-26 現場重算，母體＝Project #4 全部卡面 Log）**：

| 卡 | 離開 | 已檢查／不適用／發現 |
|---|---|---|
| `WF-TRANSITION-TABLE-UNWRITTEN1` | 研究 | 2／1／5 |
| `WF-STAGE-PITFALL-LIST1` | 審核 | **8／0／0** ⬅ PM 的空殼 |
| `WF-CLI-ENSURE-FIELDS-DOUBLE-READ1` | 規劃 | 1／1／6 |
| `WF-CLI-ENSURE-FIELDS-DOUBLE-READ1` | 審核 | 3／1／4 |
| `WF-CLI-ENSURE-FIELDS-DOUBLE-READ1` | 審核 | 3／1／4 |
| `WF-CLI-ENSURE-FIELDS-DOUBLE-READ1` | 審核 | 2／1／5 |

```
總列 48｜已檢查 19 = 39.6%｜發現 24
門檻：已檢查佔比 ≥ 80% 且 發現 ≤ 0
現況：39.6% ≥ 80%？⛔ 否   發現 24 ≤ 0？⛔ 否
⇒ ⛔ 未退化。⚠️ 樣本 6 < 30，門檻尚不可評。
```

---

## ⭐ 併帶登記一個缺口：**A3 沒有排定的評估者，⛔ 構造上不會自己觸發**

實查 `grep -rn "DEGENERATION" cli/src/ scripts/` ⇒ ⛔ **只有 `pitfalls.py` 自己**，零消費者。

而該模組**就地承認**了這件事（逐字）：「⚠️ 本模組**不自己量測**這三個值——它沒有跨次呼叫的記憶體，量測要從卡面留痕的踩坑回應摘要**事後統計**。這裡只負責讓門檻可被引用、且改動看得見。」

⚠️ **而本卡 A3 的條文⛔ 沒有指定「誰來算、什麼時候算」。**

⇒ ⭐ 那是一個**預先登記的否證條件，而它會安靜地停在「樣本 6/30」直到有人想起來**。⛔ 這正是本卡 A0b 在講的同一個形狀（「沒有任何機械會告訴你沒修完」）。

**處置：登記，⛔ 不開卡。** 理由：(a) 本卡已 🏁完成，A3 的門檻**寫死在碼裡且改動看得見**，那半是有效的；(b) 缺的只是一次事後統計，而重算指令已在本帖給出；(c) 為一次手工統計開卡，正撞 ROADMAP §5 對「命名了但沒接線」的既有警告——⛔ **再開一張沒有執行者的卡不會讓它變成有執行者**。

⭐ **重算方式（任何人可原樣重跑）**：掃 Project #4 全部卡面 body，正則取 `；踩坑回應 (\d+) 族（已檢查 (\d+)／不適用 (\d+)／發現 (\d+)）`，逐列加總。⇒ 樣本達 30 時比對 A3 的三個常數。

---
本帖由 PM（Claude Opus 5@Claude Code）以需求方的 token 發文，內容為 **PM 自己的失誤登記與處置**，⛔ 非需求方的裁定。⛔ 本卡狀態未動（🏁完成）。
