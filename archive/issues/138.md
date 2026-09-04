# #138 WF-POSTHOC-CONFORMANCE1 doctor 增通用的事後重驗：既有卡是否仍合乎現行 canonical（aiwf#130 子卡 S7b）
- state: closed  created: 2026-08-25T02:24:08Z  closed: 2026-08-26T07:56:23Z
- url: https://github.com/ruan6047/ai-workflow/issues/138
- comments: 24

## Body

- 需求：ruan6047　規劃：—
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；動 doctor 的掃描面並對全部既有卡重跑欄位檢查；⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。）　查核：待指派（建議 高階型；本卡改的是守衛自身，⛔ 執行者無法自證非阻擋性；須以真實既有卡實測並與基線清冊逐張對帳。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：目標 2 可稽核的內容：卡是否仍服務其原始目標、是否仍合乎現行規範，必須是查核留痕上讀得出來的答案，而不是靠查核者當下想不想得到。

## 簡介
<!-- card-brief:begin -->
做什麼：把 canonical §5.1.2 的事後符合性從條文變成 doctor 的通用掃描——對既有卡重跑現行欄位與格式檢查，列出不合規者。適用時機：canonical 改版後要知道哪些既有卡已經不合規、或要盤點遷移卡殘留時。⛔ 非射程：不新增 review schema 欄位（屬 S7a）；⛔ 不自動修復（沿用 cleanup 立場：守衛不代為修復非法態）；⛔ 不阻擋既有卡的 amend 或 handoff。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：canonical §5.1.2 在 main 生效（d4ba7ce5）而 doctor **沒有事後重驗既有卡的通用路徑**：卡在開卡當下通過欄位檢查，之後 canonical 改版，⛔ 沒有任何動詞會回頭問「它現在還合規嗎」。⇒ 不合規只在下一次剛好有人動那張卡時偶然被撞見。⭐ 而這有量化支持（開卡前實測）：validate_open_fields（cli/src/wf_cli/validation.py:88）本來就能對既有卡重跑，實測 161 張中 7 張不合規、全為 2026-08-04 遷移卡 —— 那 7 張沒有任何機制會通知任何人，量測見 aiwf#136 issuecomment-5400106397。⚠️ 而 §5.1.2 逐字指出既有的 legacy_authority_notes「證明該需求已出現過一次，但當時針對單一形態單獨做，不是通用機制」⇒ 再做一個單一形態的掃描等於重犯。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/doctor.py",
    "file:cli/src/wf_cli/commands/doctor_cmd.py",
    "file:cli/tests/test_doctor.py",
    "file:cli/src/wf_cli/project.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⚠️ A1–A25 逐條壓縮（一對一，⛔ 無合併無丟棄）；原文封存於 https://github.com/ruan6047/ai-workflow/issues/138#issuecomment-5407338420
- [ ] A1 doctor 新增**通用**事後重驗；⛔ 不自動修復。判定放 doctor.py（純函式）、取卡放 doctor_cmd.py
- [ ] A2 ⭐ 報告須**逐張歸因**，值域恰五類：tool_cannot_read／undecidable／rule_changed／writer_nonconformant／channel_bypassed。⛔ 只計數＝錯誤指控（實測 41 中 34 屬 (c)）
- [ ] A3 ⭐ 判準順序不可換：tool_cannot_read→undecidable→rule_changed→writer_nonconformant→channel_bypassed（前兩者是我們的侷限，⛔ 不得變成指控）
- [ ] A4 ⭐ 每個 rule_epoch 須帶 disposition（migrate／accept_as_legacy）；⛔ 否則 rule_changed 會變成下一個 190
- [ ] A5 ⭐ rule_epoch 釘**構件落地的完整 ISO-8601 時刻**，⛔ 非日期（實測日期粒度會把 16 誤判成 21）
- [ ] A6 ⭐ 卡的存在時刻取值序：Log 的 open 事件 → Issue createdAt → undecidable。⚠️ createdAt 只能比 2026-08-04 之後的 epoch；須擴既有 list_items 查詢，⛔ 不加第二次抓取
- [ ] A7 ⭐ 抽取三個既有掃描的共用形狀為第一批實作：legacy_authority_notes／brief_drift／**state_face_drift（生產碼 0 呼叫端）**；⛔ 不蓋第四個單一形態
- [ ] A8 ⭐ 共用信封、⛔ 不共用 finding 型別（三者資訊不同，併型別＝損失）；三者皆有 card_id ⇒ Protocol 即可
- [ ] A9 ⭐ 改寫 render_state_face_drift 使處置文案**依 cause 分流**（現行無條件輸出「補跑動詞…勿手動搬看板」＝對 rule_changed 是錯誤指控）；保留統計行與「偵測不等於強制」段。回歸基線 `-k drift` 31 passed
- [ ] A10 ⛔ 不得把 run_doctor 的 card_bodies 與掃描用卡面合成一個參數（doctor.py 逐字：會沉默改變 --cleanup-preview）
- [ ] A11 ⭐ 基線清冊用本卡自量數字（193 母體／41 不合規／34 tool_cannot_read／7 card_deficient，其中僅 2 張非終態）；⛔ 不引用 aiwf#136 的 161/7
- [ ] A12 ⚠️ 接線 state_face_drift 的兩個已知常態須寫進交付：76% 不判定（無承接卡）、14 筆 open_initial 屬 rule_changed 非 drift
- [ ] A13 ⭐ **可達性是逐動詞的**，⛔ 非卡的二值屬性：assign ⛔／amend 五旗標 ⛔／`amend --brief` ✅ 40/41／handoff·review·checkpoint·deploy-* ✅。⭐ 真正的阻塞是 assign。⛔ 更正：先前寫「會擋住 S5」是錯的
- [ ] A14 ⭐ 可證偽預測：上線時 unreachable=41；aiwf#105 落地後應為 0
- [ ] A15 ⭐ **欄位層掃描**（與 per-card 正交，獨立區段）：看板實際欄位 vs FIELD_SPECS。實測孤兒欄位 1 個＝`分支／worktree`（41 張有值、無人讀；真正讀不到的登記 3 張、活卡 0）。成因：ensure_fields 冪等但只增不減
- [ ] A16 ⚠️ 稽核取值一律走 `wf_cli.project.list_items`，⛔ 不用 `gh project item-list`（project.py 逐字：中文欄位 key 編碼錯誤）；判定直接呼叫 wf_cli 純函式使盤點與守衛同源
- [ ] A17 ⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend／handoff
- [ ] A18 ⚠️ legacy_authority_notes 由「合流或劃界」改為**抽取**；且其 findings ⛔ **不進待辦**（既有立場：報的是留痕強度不足，不是授權無效）
- [ ] A19 ⚠️ 旗標改名 `--conformance`（實查 CI／腳本／文件 0 命中），保留舊名為 alias；交付須明說連帶修正是否刻意
- [ ] A20 ⛔ 授權邊界：發現須改本卡未宣告的檔 ⇒ 停、寫阻塞發現、由需求方裁決（§3.2）
- [ ] A21 ⚠️ 與 aiwf#137 的介面：S7a 已合併則納入 service_goal_still_served，否則明列為已知缺口。⭐ 兩卡寫入集不相交、可真平行
- [ ] A22 回歸：cli 既有測試全過（基線數逐字記錄，⛔ 不得只寫「全過」）
- [ ] A23 ⚠️ 交付須附 PM 單方面決定清冊
- [ ] A24 ⭐ writer_nonconformant 的 finding 須自帶 rule_epoch 與卡的建立時刻（狀態面無工具版本可查：pyproject 凍在 0.1.0、無 --version）

## 驗證

- [ ] 對至少 3 張真實既有卡（含一張 2026-08-04 遷移卡）實跑，附原始輸出。⛔ 不接受自造樣本。
- [ ] ⛔ 非阻擋的**負控**：對一張被判不合規的既有卡實跑 amend --dry-run 證明不受阻；handoff 無 dry 路徑，須明列原因與密封探針設計。
- [ ] ⭐ **五類歸因各取真實樣本證明**：rule_changed 取 14 筆 open_initial 中至少 3 張；tool_cannot_read 取 33 張帶後綴標題中至少 3 張；writer_nonconformant 取 16 張缺 wf-routing 中至少 3 張；undecidable 取 41 張無 open 行中至少 3 張；channel_bypassed 母體中實測 **0 筆** ⇒ 須**明說是零筆**並以構造樣本證明該分支可達，⛔ 不得靜默略過。
- [ ] ⭐ **判準順序的變異檢驗**：把 tool_cannot_read 從第一順位移到最後，證明那 34 張會改被報成其他類（即順序真的承重）。⛔ 只跑正確順序是零資訊。
- [ ] ⭐ disposition 兩種取值各驗一次：migrate 的 epoch 其殘餘**逐張列出**；accept_as_legacy 的 epoch **只出現摘要行、⛔ 不逐張**。附兩份輸出對照。
- [ ] ⭐ createdAt 退路的邊界：取一張 2026-08-04 遷移卡，證明它對 08-04 之前的 epoch **落 undecidable 而非 writer_nonconformant**。⛔ 只驗 happy path 是零資訊。
- [ ] ⭐ state_face_drift 接線的**前後對照**：附接線前（直接 import 呼叫）與接線後（wfcli doctor 實跑）的輸出，證明那 14 筆不再被報成 drift。⛔ 只附接線後是零資訊。
- [ ] ⭐ 掃描結果與基線清冊**逐張**對帳，差異逐筆附原因；⛔「掃到 N 張」不算。同時記錄母體數與取樣時刻。
- [ ] ⭐ 證明對本卡未宣告的檔零寫入：附本卡分支對 validation.py 與 card.py 的 git diff 為空（附指令與輸出）。⛔ 自述不算。
- [ ] ⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因；⛔ 標不出原因者代表驗得了、不得列入。
- [ ] ⭐ **可達性判準的變異檢驗**：取 41 張中至少 3 張（三種成因各一）以 `amend --dry-run` 實跑，附拒收原文；再取一張 reachable 的真實卡證明**不誤報**。⛔ 只驗 unreachable 那側是零資訊。
- [ ] ⭐ **欄位層掃描的負控**：構造一個「宣告了但零卡有值」的情形證明 (ii) 分支可達（實測母體為 0，⇒ 不構造就永遠測不到）；並證明孤兒欄位 `分支／worktree` 被列在**獨立區段**而非逐卡 findings。
- [ ] ⚠️ 證明本卡的盤點與守衛同源：附至少一項量測，其結果由**直接呼叫 wf_cli 純函式**與**經 wfcli doctor 輸出**兩條路徑取得且逐字相同。⛔ 只跑一條無法排除自寫判定與工具判定不一致。

## Log

- 2026-08-25T10:24:07+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-25T11:14:34+08:00 amend by wf-cli（op 847701be）→ 驗收條件：原值「[ ] doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復（沿用 cleanup 的既有立場：守衛不代為修復非法態）。；[ ] ⚠️ 須**與既有的 legacy_authority_notes 合流或明確劃界**——canonical §5.1.2 逐字指出後者「證明該需求已出現過一次，但當時針對單一形態單獨做，不是通用機制」。⛔ 再做一個單一形態的掃描等於重犯。；[ ] ⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。；[ ] ⭐ 基線須先登記：開工當下的不合規清冊**逐張列出卡號**（開卡前實測 161 張中 7 張不合規、全為 2026-08-04 遷移卡，見 aiwf#136 issuecomment-5400106397）。⇒ 交付後的掃描結果須與該清冊逐張對帳，⛔ 不得只報「掃到 N 張」。⚠️ 母體會隨時間變動，對帳須同時記錄母體數與取樣時刻。；[ ] ⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時，事後重驗須把 service_goal_still_served 納入檢查面；尚未合併時須明列該欄位為**已知缺口**而非遺漏。⛔ 兩張卡都宣告 cli/src/wf_cli/validation.py，資源互斥上必然序列化——S7a 先。；[ ] 回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。；[ ] ⚠️ 交付時須附「PM 單方面決定清冊」，逐一標明哪些形狀或判準由執行者提出而非 canonical 明文或需求方裁定。」→ 新值「doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復（沿用 cleanup 的既有立場：守衛不代為修復非法態）。⚠️ 實作分層依既有形狀：判定放 doctor.py（純函式、不碰 gh），取卡放 doctor_cmd.py（已具 list_items／resolve_project／find_item_by_card_id，實測 :20／:169-170／:221-222）。；⚠️ 須**與既有的 legacy_authority_notes 合流或明確劃界**——canonical §5.1.2 逐字指出後者「證明該需求已出現過一次，但當時針對單一形態單獨做，不是通用機制」。⛔ 再做一個單一形態的掃描等於重犯。；⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。；⭐ 基線須先登記：開工當下的不合規清冊**逐張列出卡號**（開卡前實測 161 張中 7 張不合規、全為 2026-08-04 遷移卡，見 aiwf#136 issuecomment-5400106397）。⇒ 交付後的掃描結果須與該清冊逐張對帳，⛔ 不得只報「掃到 N 張」。⚠️ 母體會隨時間變動，對帳須同時記錄母體數與取樣時刻。；⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時，事後重驗須把 service_goal_still_served 納入檢查面；尚未合併時須明列該欄位為**已知缺口**而非遺漏。⭐ 兩張卡**寫入集不相交、可真平行**（需求方 2026-08-25 裁定甲）——本卡對 validate_open_fields（cli/src/wf_cli/validation.py:88）是**呼叫**不是修改，該檔已自本卡資源宣告移除。⛔ 先前卡上「資源互斥上必然序列化——S7a 先」那句**作廢**。；⛔ 授權邊界：執行中若發現**必須修改** cli/src/wf_cli/validation.py（或任何本卡未宣告的檔），依 canonical §3.2「執行中發現授權缺口：**停** → 寫阻塞發現 → 由需求方裁決」，⛔ 執行者不得自行擴權。⚠️ 該風險來自「呼叫得動」是讀碼推論（validate_open_fields 為 keyword-only 純函式、無 I/O），⛔ 未在 doctor 側寫過原型驗證。；回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。；⚠️ 交付時須附「PM 單方面決定清冊」，逐一標明哪些形狀或判準由執行者提出而非 canonical 明文或需求方裁定。」；理由 需求方 2026-08-25 裁定甲。研究第八輪（aiwf#137 issuecomment-5404548830）實測：validate_open_fields 是 keyword-only 純函式、無 I/O，doctor_cmd.py 既有的 list_items 取回的 ItemSnapshot（帶 fields dict）可直接餵它 ⇒ 本卡對 validation.py 是呼叫不是修改，該檔自資源宣告移除。第九輪（issuecomment-5404558339）以三組既有切片兄弟卡實測 canonical §3.2(3)：唯一寫入集相交的 cpbl#100／#147 其 spec 基線逐字指向前卡交付、屬承接非切片，⇒ 無反例。移除後兩張卡寫入集不相交，§3.2(3)「可真平行」成立，故作廢原驗收第 5 條末句「S7a 先」，並依 §3.2 補授權邊界條與零寫入的驗證。。
- 2026-08-25T11:14:34+08:00 amend by wf-cli（op 847701be）→ 驗證：原值「[ ] 對至少 3 張真實既有卡（含一張 2026-08-04 遷移卡——實測 61 張活卡中 24 張的 body 結構與範本不同）實跑，附原始輸出。⛔ 不接受自造樣本。；[ ] ⛔ 非阻擋的**負控**：對一張被判不合規的既有卡實跑 amend --dry-run，證明不受阻；handoff 無 dry 路徑，須明列原因與密封探針設計（⚠️ 實測 amend **有** --dry-run、handoff 沒有）。；[ ] ⚠️ 與 legacy_authority_notes 的關係須以碼證明（指出合流點或劃界處的檔與行），⛔ 不接受「我劃了界」的自述。；[ ] ⭐ 掃描結果與驗收第 4 條的基線清冊**逐張**對帳，差異逐筆附原因；⛔ 「掃到 N 張」不算。；[ ] ⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因（缺什麼、要等什麼、需要誰）；⛔ 標不出原因者代表驗得了、不得列入。」→ 新值「對至少 3 張真實既有卡（含一張 2026-08-04 遷移卡——實測 61 張活卡中 24 張的 body 結構與範本不同）實跑，附原始輸出。⛔ 不接受自造樣本。；⛔ 非阻擋的**負控**：對一張被判不合規的既有卡實跑 amend --dry-run，證明不受阻；handoff 無 dry 路徑，須明列原因與密封探針設計（⚠️ 實測 amend **有** --dry-run、handoff 沒有）。；⚠️ 與 legacy_authority_notes 的關係須以碼證明（指出合流點或劃界處的檔與行），⛔ 不接受「我劃了界」的自述。；⭐ 掃描結果與驗收第 4 條的基線清冊**逐張**對帳，差異逐筆附原因；⛔ 「掃到 N 張」不算。；⭐ 證明對 validation.py 為零寫入：附本卡分支對該檔的 git diff 為空（附指令與輸出）。⛔ 「我沒改」的自述不算。；⚠️ ItemSnapshot.fields 是否對全部母體都備齊 validate_open_fields 所需七值，須實測並附缺值卡的清冊；⛔ 缺值不得靜默當成不合規。；⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因（缺什麼、要等什麼、需要誰）；⛔ 標不出原因者代表驗得了、不得列入。」；理由 需求方 2026-08-25 裁定甲。研究第八輪（aiwf#137 issuecomment-5404548830）實測：validate_open_fields 是 keyword-only 純函式、無 I/O，doctor_cmd.py 既有的 list_items 取回的 ItemSnapshot（帶 fields dict）可直接餵它 ⇒ 本卡對 validation.py 是呼叫不是修改，該檔自資源宣告移除。第九輪（issuecomment-5404558339）以三組既有切片兄弟卡實測 canonical §3.2(3)：唯一寫入集相交的 cpbl#100／#147 其 spec 基線逐字指向前卡交付、屬承接非切片，⇒ 無反例。移除後兩張卡寫入集不相交，§3.2(3)「可真平行」成立，故作廢原驗收第 5 條末句「S7a 先」，並依 §3.2 補授權邊界條與零寫入的驗證。。
- 2026-08-25T11:14:34+08:00 amend by wf-cli（op 847701be）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/doctor.py", "file:cli/src/wf_cli/commands/doctor_cmd.py", "file:cli/src/wf_cli/validation.py", "file:cli/tests/test_doctor.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/doctor.py、file:cli/src/wf_cli/commands/doctor_cmd.py、file:cli/tests/test_doctor.py」；理由 需求方 2026-08-25 裁定甲。研究第八輪（aiwf#137 issuecomment-5404548830）實測：validate_open_fields 是 keyword-only 純函式、無 I/O，doctor_cmd.py 既有的 list_items 取回的 ItemSnapshot（帶 fields dict）可直接餵它 ⇒ 本卡對 validation.py 是呼叫不是修改，該檔自資源宣告移除。第九輪（issuecomment-5404558339）以三組既有切片兄弟卡實測 canonical §3.2(3)：唯一寫入集相交的 cpbl#100／#147 其 spec 基線逐字指向前卡交付、屬承接非切片，⇒ 無反例。移除後兩張卡寫入集不相交，§3.2(3)「可真平行」成立，故作廢原驗收第 5 條末句「S7a 先」，並依 §3.2 補授權邊界條與零寫入的驗證。。
- 2026-08-25T11:22:20+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/WF-POSTHOC-CONFORMANCE1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/posthoc-conformance1；交付狀態 🔬研究中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-25T11:23:00+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 0；SHA d4ba7ce5f3fa526fc3a7aa0ebbeee3c926e5eb28；證據 需求方 2026-08-25 指示本卡與 aiwf#137 同時開始（裁定甲之後：兩張寫入集交集為空，canonical §3.2(3) 可真平行成立，實測見 aiwf#137 issuecomment-5404558339 與 5404609166）。承接留痕：aiwf#136 issuecomment-5400106397（validate_open_fields 可對既有卡重跑，實測 161 張中 7 張不合規、全為 2026-08-04 遷移卡——本卡驗收第 4 條的基線清冊出處）；本卡 issuecomment-5404614655（⚠️ 稽核取值一律讀 body 的 resource-claims JSON，⛔ 不得讀 Project 的攤平欄位——PM 已於同日親自踩過該坑）。研究階段要收斂：合流或劃界 legacy_authority_notes、掃描面的取值路徑、基線清冊的重算與母體時刻。基準 origin/main = d4ba7ce5（已 fetch 核對）。。
- 2026-08-25T11:40:14+08:00 amend by wf-cli（op f879ae07）→ 驗收條件：原值「[ ] doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復（沿用 cleanup 的既有立場：守衛不代為修復非法態）。⚠️ 實作分層依既有形狀：判定放 doctor.py（純函式、不碰 gh），取卡放 doctor_cmd.py（已具 list_items／resolve_project／find_item_by_card_id，實測 :20／:169-170／:221-222）。；[ ] ⚠️ 須**與既有的 legacy_authority_notes 合流或明確劃界**——canonical §5.1.2 逐字指出後者「證明該需求已出現過一次，但當時針對單一形態單獨做，不是通用機制」。⛔ 再做一個單一形態的掃描等於重犯。；[ ] ⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。；[ ] ⭐ 基線須先登記：開工當下的不合規清冊**逐張列出卡號**（開卡前實測 161 張中 7 張不合規、全為 2026-08-04 遷移卡，見 aiwf#136 issuecomment-5400106397）。⇒ 交付後的掃描結果須與該清冊逐張對帳，⛔ 不得只報「掃到 N 張」。⚠️ 母體會隨時間變動，對帳須同時記錄母體數與取樣時刻。；[ ] ⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時，事後重驗須把 service_goal_still_served 納入檢查面；尚未合併時須明列該欄位為**已知缺口**而非遺漏。⭐ 兩張卡**寫入集不相交、可真平行**（需求方 2026-08-25 裁定甲）——本卡對 validate_open_fields（cli/src/wf_cli/validation.py:88）是**呼叫**不是修改，該檔已自本卡資源宣告移除。⛔ 先前卡上「資源互斥上必然序列化——S7a 先」那句**作廢**。；[ ] ⛔ 授權邊界：執行中若發現**必須修改** cli/src/wf_cli/validation.py（或任何本卡未宣告的檔），依 canonical §3.2「執行中發現授權缺口：**停** → 寫阻塞發現 → 由需求方裁決」，⛔ 執行者不得自行擴權。⚠️ 該風險來自「呼叫得動」是讀碼推論（validate_open_fields 為 keyword-only 純函式、無 I/O），⛔ 未在 doctor 側寫過原型驗證。；[ ] 回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。；[ ] ⚠️ 交付時須附「PM 單方面決定清冊」，逐一標明哪些形狀或判準由執行者提出而非 canonical 明文或需求方裁定。」→ 新值「doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復（沿用 cleanup 立場：守衛不代為修復非法態）。⚠️ 分層依既有形狀：判定放 doctor.py（純函式、不碰 gh），取卡放 doctor_cmd.py（既有 list_items／resolve_project／find_item_by_card_id，實測 :20／:169-170／:221-222）。；⭐ **報告須逐張歸因，⛔ 不得只計數**。三類：(a) **規則變了、卡沒動**（常數或 canonical 改版，既有卡自然落後；處置＝遷移或明示接受，⛔ 不歸咎任何人）；(b) **卡被動了、事件沒寫**（有人繞過 wfcli；處置＝補跑動詞）；(c) **工具讀不到**（解析器缺陷；處置＝**修工具**，⛔ 不是修卡）。⇒ 實測支持（2026-08-25，見本卡 issuecomment-5404753163）：41 張不合規中 **34 張屬 (c)**，只報總數等於 34 個錯誤的指控。；⭐ 每個掃描須宣告自己的**規則生效時刻**（形狀比照既有 TRAILER_GUARD_EPOCH，doctor.py:828），⇒ (a) 的機械判準是「卡的最後相關事件早於該時刻」。⛔ 沒有這個欄位，任何事後掃描在下一次改版後都會開始把 (a) 報成 (b)。；⭐ 通用機制的做法是**把三個既有掃描已共用的形狀抽出來，並讓它們成為第一批實作**，⛔ 不是在旁邊再蓋第四個單一形態（那正是 canonical §5.1.2 批評的形態）。三個是：legacy_authority_notes（doctor.py:1255）、brief_drift（:1298）、**state_face_drift（:1574——今天生產碼 0 個呼叫端，只有測試約 30 處，接線屬 aiwf#65 明列的「後續卡」而該卡從未開過）**。共用形狀含：純函式 audit_X(card_bodies)→XReport、status scanned／not_scanned（⛔ 未掃描不得讀成乾淨，doctor.py:1210-1213 逐字）、scanned_cards 記母體數、findings 與「常態缺漏」分開（BriefDriftReport.missing 的既有理由）。；⛔ **不得把 run_doctor 的 card_bodies 參數與掃描用的卡面合成一個**——doctor.py:1822-1827 逐字裁定：那個參數餵給 evaluate_cleanup_guard，順手填上會**沉默地改變 --cleanup-preview 的判定**。⭐ 正解是「同一次 list_items、多個獨立消費者各帶自己的參數」，⇒ 保住 doctor_cmd.py:167-183 單次抓取（避免 body 與欄位跨時間），但**不**把 cleanup guard 拉進來。；⭐ 基線清冊改用本卡自量的數字並附方法：母體 193 張（Project #4 中有卡ID且有 body 者，取樣時刻 2026-08-25）、不合規 41 張（21%），型態為 核心痛點必填 40／資源宣告必填 34／db_scope 不在值域 34。⛔ **不得引用 aiwf#136 的「161 張中 7 張」**——本卡重算差一個數量級，該數字來源不可考。⚠️ 清冊須逐張帶歸因欄。；⚠️ 接上 state_face_drift 時的兩個已知常態，須逐字寫進交付：(1) **76% 不判定**（實測 62 張未結案卡中 47 張，主因 handoff_status_not_in_log 45）——其修法「讓 handoff Log 行自帶 stage/status」**今天沒有承接卡**（aiwf#54 的驗收是「第一個遠端寫入帶載荷」，⛔ 不涵蓋 Log 行內容），⇒ 本卡須把 76% 當常態設計報告，⛔ 不得假設它會被消掉；(2) **14 筆 open_initial 屬 (a) 而非 drift**——成因是 1531666（2026-08-21）把 open 初始狀態由 📥Backlog 改為 💡需求，實測 14/14 開卡日皆早於該日。⛔ 不得把它們報成 drift（drift 的既有語意是「欄位被手搬」）。；⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。；⚠️ 與既有 legacy_authority_notes 的關係由「合流或劃界」改為**抽取**（見第 4 條）。⛔ 交付須以碼指出抽取後三者共用的落點，不接受「我劃了界」的自述。；⚠️ 旗標命名：簡介漂移目前掛在 --legacy-authority-notes 底下（doctor_cmd.py:121／:167 同一個 if），而該旗標 help（:54-55）⛔ 一個字沒提簡介漂移。抽取後命名勢必要動 ⇒ 交付須明說該連帶修正是不是刻意的。；⛔ 授權邊界：執行中若發現**必須修改**本卡未宣告的檔（例如 cli/src/wf_cli/validation.py 或 cli/src/wf_cli/card.py），依 canonical §3.2「執行中發現授權缺口：**停** → 寫阻塞發現 → 由需求方裁決」，⛔ 執行者不得自行擴權。；⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時把 service_goal_still_served 納入檢查面；未合併時明列為**已知缺口**而非遺漏。⭐ 兩張寫入集不相交、**可真平行**（需求方 2026-08-25 裁定甲）；⛔ 先前「S7a 先」那句已作廢。；回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。；⚠️ 交付時須附「PM 單方面決定清冊」。」；理由 需求方 2026-08-25 裁定甲：本卡把「工具讀不到」當獨立歸因類輸出並指名 aiwf#105，⛔ 不等它修完。依研究第一至四輪重寫驗收與驗證（issuecomment-5404646517／5404661843／5404721662／5404753163）。四項實測改變了卡的形狀：(1) 事後掃描已有三個而非 canonical §5.1.2 說的一個，其中 state_face_drift（doctor.py:1574）完整寫好測過但生產碼 0 呼叫端、接線的後續卡從未開過；(2) 直接 import 對今日看板實跑得 76% 不判定／14 筆 drift，而 14/14 的開卡日皆早於 1531666（2026-08-21）改動 open 初始狀態之日 ⇒ 那 14 筆是規則變更殘餘不是有人繞過通道；(3) 重算基線得 41/193（21%），與 aiwf#136 的 7/161 差一個數量級，且其中 34 張的成因是解析器讀不到（33 張標題帶後綴＝aiwf#105 的缺陷、1 張另有未命名失敗）而非卡缺宣告 ⇒ 只計數會產生 34 個錯誤指控；(4) aiwf#54 的驗收是「第一個遠端寫入帶載荷」，⛔ 不涵蓋 handoff Log 行內容 ⇒ 76% 不判定今天沒有承接卡。故新增三類歸因、規則生效時刻欄位、抽取三個既有掃描、card_bodies 不得合流的禁令，並把基線改用本卡自量的數字。。
- 2026-08-25T11:40:14+08:00 amend by wf-cli（op f879ae07）→ 驗證：原值「[ ] 對至少 3 張真實既有卡（含一張 2026-08-04 遷移卡——實測 61 張活卡中 24 張的 body 結構與範本不同）實跑，附原始輸出。⛔ 不接受自造樣本。；[ ] ⛔ 非阻擋的**負控**：對一張被判不合規的既有卡實跑 amend --dry-run，證明不受阻；handoff 無 dry 路徑，須明列原因與密封探針設計（⚠️ 實測 amend **有** --dry-run、handoff 沒有）。；[ ] ⚠️ 與 legacy_authority_notes 的關係須以碼證明（指出合流點或劃界處的檔與行），⛔ 不接受「我劃了界」的自述。；[ ] ⭐ 掃描結果與驗收第 4 條的基線清冊**逐張**對帳，差異逐筆附原因；⛔ 「掃到 N 張」不算。；[ ] ⭐ 證明對 validation.py 為零寫入：附本卡分支對該檔的 git diff 為空（附指令與輸出）。⛔ 「我沒改」的自述不算。；[ ] ⚠️ ItemSnapshot.fields 是否對全部母體都備齊 validate_open_fields 所需七值，須實測並附缺值卡的清冊；⛔ 缺值不得靜默當成不合規。；[ ] ⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因（缺什麼、要等什麼、需要誰）；⛔ 標不出原因者代表驗得了、不得列入。」→ 新值「對至少 3 張真實既有卡（含一張 2026-08-04 遷移卡）實跑，附原始輸出。⛔ 不接受自造樣本。；⛔ 非阻擋的**負控**：對一張被判不合規的既有卡實跑 amend --dry-run 證明不受阻；handoff 無 dry 路徑，須明列原因與密封探針設計。；⭐ **歸因正確性的三組真實樣本**：(a) 取那 14 筆 open_initial 中至少 3 張，證明標為 (a) 而非 (b)；(c) 取那 33 張標題帶後綴的卡中至少 3 張，證明標為 (c)（工具讀不到）而非「卡缺宣告」；(b) 若母體中無真實 (b) 樣本（本輪實測 0 筆），須**明說是零筆**並以構造樣本證明該分支可達，⛔ 不得靜默略過。；⭐ 掃描結果與基線清冊**逐張**對帳，差異逐筆附原因；⛔ 「掃到 N 張」不算。並同時記錄母體數與取樣時刻。；⭐ state_face_drift 接線的**前後對照**：附接線前（今日直接 import 呼叫）與接線後（wfcli doctor 實跑）的輸出，證明那 14 筆不再被報成 drift。⛔ 只附接線後是零資訊。；⭐ 證明對本卡未宣告的檔為零寫入：附本卡分支對 cli/src/wf_cli/validation.py 與 cli/src/wf_cli/card.py 的 git diff 為空（附指令與輸出）。⛔ 自述不算。；⚠️ ItemSnapshot.fields 是否對全部母體備齊 validate_open_fields 所需七值，須實測並附缺值卡清冊；⛔ 缺值不得靜默當成不合規（那會落回 (c) 卻被報成卡的缺陷）。；⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因；⛔ 標不出原因者代表驗得了、不得列入。」；理由 需求方 2026-08-25 裁定甲：本卡把「工具讀不到」當獨立歸因類輸出並指名 aiwf#105，⛔ 不等它修完。依研究第一至四輪重寫驗收與驗證（issuecomment-5404646517／5404661843／5404721662／5404753163）。四項實測改變了卡的形狀：(1) 事後掃描已有三個而非 canonical §5.1.2 說的一個，其中 state_face_drift（doctor.py:1574）完整寫好測過但生產碼 0 呼叫端、接線的後續卡從未開過；(2) 直接 import 對今日看板實跑得 76% 不判定／14 筆 drift，而 14/14 的開卡日皆早於 1531666（2026-08-21）改動 open 初始狀態之日 ⇒ 那 14 筆是規則變更殘餘不是有人繞過通道；(3) 重算基線得 41/193（21%），與 aiwf#136 的 7/161 差一個數量級，且其中 34 張的成因是解析器讀不到（33 張標題帶後綴＝aiwf#105 的缺陷、1 張另有未命名失敗）而非卡缺宣告 ⇒ 只計數會產生 34 個錯誤指控；(4) aiwf#54 的驗收是「第一個遠端寫入帶載荷」，⛔ 不涵蓋 handoff Log 行內容 ⇒ 76% 不判定今天沒有承接卡。故新增三類歸因、規則生效時刻欄位、抽取三個既有掃描、card_bodies 不得合流的禁令，並把基線改用本卡自量的數字。。
- 2026-08-25T11:41:17+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (PM)；iteration 0；SHA d4ba7ce5f3fa526fc3a7aa0ebbeee3c926e5eb28；證據 研究四輪完成，需求方 2026-08-25 裁定甲（本卡 timeline 之「裁定（需求方，2026-08-25）：採甲」留言），卡面已 amend（op 847701be 移除 validation.py 並作廢「S7a 先」；op f879ae07 寫入三類歸因、規則生效時刻、抽取三個既有掃描、card_bodies 不得合流、基線改用本卡自量數字）。四輪留痕：issuecomment-5404646517（事後掃描已有兩個且共用同一形狀）、5404661843（⛔ 更正為三個：state_face_drift 完整寫好測過但生產碼 0 呼叫端；且 doctor.py:1822-1827 有「刻意不共用 card_bodies」的既有裁定）、5404721662（aiwf#65 未接線是資源射程邊界非裁定、後續卡從未開過；直接 import 對今日看板實跑得76% 不判定／14 筆 drift，而 14/14 開卡日皆早於 1531666 的 2026-08-21 ⇒ 規則變更殘餘非有人繞過）、5404753163（⛔ 基線 161/7 不可用，重算 41/193，其中 34 張成因是解析器讀不到；aiwf#54 不涵蓋 76% 的修法）。⚠️ 進規劃要定的三題：抽取後的共用型別與命名（含 --legacy-authority-notes 旗標連帶更名）、規則生效時刻欄位的落點、state_face_drift 接線的最小改動面。基準 origin/main = d4ba7ce5（已 fetch 核對）。。
- 2026-08-25T12:03:51+08:00 amend by wf-cli（op 090d1d7b）→ 驗收條件：原值「[ ] doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復（沿用 cleanup 立場：守衛不代為修復非法態）。⚠️ 分層依既有形狀：判定放 doctor.py（純函式、不碰 gh），取卡放 doctor_cmd.py（既有 list_items／resolve_project／find_item_by_card_id，實測 :20／:169-170／:221-222）。；[ ] ⭐ **報告須逐張歸因，⛔ 不得只計數**。三類：(a) **規則變了、卡沒動**（常數或 canonical 改版，既有卡自然落後；處置＝遷移或明示接受，⛔ 不歸咎任何人）；(b) **卡被動了、事件沒寫**（有人繞過 wfcli；處置＝補跑動詞）；(c) **工具讀不到**（解析器缺陷；處置＝**修工具**，⛔ 不是修卡）。⇒ 實測支持（2026-08-25，見本卡 issuecomment-5404753163）：41 張不合規中 **34 張屬 (c)**，只報總數等於 34 個錯誤的指控。；[ ] ⭐ 每個掃描須宣告自己的**規則生效時刻**（形狀比照既有 TRAILER_GUARD_EPOCH，doctor.py:828），⇒ (a) 的機械判準是「卡的最後相關事件早於該時刻」。⛔ 沒有這個欄位，任何事後掃描在下一次改版後都會開始把 (a) 報成 (b)。；[ ] ⭐ 通用機制的做法是**把三個既有掃描已共用的形狀抽出來，並讓它們成為第一批實作**，⛔ 不是在旁邊再蓋第四個單一形態（那正是 canonical §5.1.2 批評的形態）。三個是：legacy_authority_notes（doctor.py:1255）、brief_drift（:1298）、**state_face_drift（:1574——今天生產碼 0 個呼叫端，只有測試約 30 處，接線屬 aiwf#65 明列的「後續卡」而該卡從未開過）**。共用形狀含：純函式 audit_X(card_bodies)→XReport、status scanned／not_scanned（⛔ 未掃描不得讀成乾淨，doctor.py:1210-1213 逐字）、scanned_cards 記母體數、findings 與「常態缺漏」分開（BriefDriftReport.missing 的既有理由）。；[ ] ⛔ **不得把 run_doctor 的 card_bodies 參數與掃描用的卡面合成一個**——doctor.py:1822-1827 逐字裁定：那個參數餵給 evaluate_cleanup_guard，順手填上會**沉默地改變 --cleanup-preview 的判定**。⭐ 正解是「同一次 list_items、多個獨立消費者各帶自己的參數」，⇒ 保住 doctor_cmd.py:167-183 單次抓取（避免 body 與欄位跨時間），但**不**把 cleanup guard 拉進來。；[ ] ⭐ 基線清冊改用本卡自量的數字並附方法：母體 193 張（Project #4 中有卡ID且有 body 者，取樣時刻 2026-08-25）、不合規 41 張（21%），型態為 核心痛點必填 40／資源宣告必填 34／db_scope 不在值域 34。⛔ **不得引用 aiwf#136 的「161 張中 7 張」**——本卡重算差一個數量級，該數字來源不可考。⚠️ 清冊須逐張帶歸因欄。；[ ] ⚠️ 接上 state_face_drift 時的兩個已知常態，須逐字寫進交付：(1) **76% 不判定**（實測 62 張未結案卡中 47 張，主因 handoff_status_not_in_log 45）——其修法「讓 handoff Log 行自帶 stage/status」**今天沒有承接卡**（aiwf#54 的驗收是「第一個遠端寫入帶載荷」，⛔ 不涵蓋 Log 行內容），⇒ 本卡須把 76% 當常態設計報告，⛔ 不得假設它會被消掉；(2) **14 筆 open_initial 屬 (a) 而非 drift**——成因是 1531666（2026-08-21）把 open 初始狀態由 📥Backlog 改為 💡需求，實測 14/14 開卡日皆早於該日。⛔ 不得把它們報成 drift（drift 的既有語意是「欄位被手搬」）。；[ ] ⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。；[ ] ⚠️ 與既有 legacy_authority_notes 的關係由「合流或劃界」改為**抽取**（見第 4 條）。⛔ 交付須以碼指出抽取後三者共用的落點，不接受「我劃了界」的自述。；[ ] ⚠️ 旗標命名：簡介漂移目前掛在 --legacy-authority-notes 底下（doctor_cmd.py:121／:167 同一個 if），而該旗標 help（:54-55）⛔ 一個字沒提簡介漂移。抽取後命名勢必要動 ⇒ 交付須明說該連帶修正是不是刻意的。；[ ] ⛔ 授權邊界：執行中若發現**必須修改**本卡未宣告的檔（例如 cli/src/wf_cli/validation.py 或 cli/src/wf_cli/card.py），依 canonical §3.2「執行中發現授權缺口：**停** → 寫阻塞發現 → 由需求方裁決」，⛔ 執行者不得自行擴權。；[ ] ⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時把 service_goal_still_served 納入檢查面；未合併時明列為**已知缺口**而非遺漏。⭐ 兩張寫入集不相交、**可真平行**（需求方 2026-08-25 裁定甲）；⛔ 先前「S7a 先」那句已作廢。；[ ] 回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。；[ ] ⚠️ 交付時須附「PM 單方面決定清冊」。」→ 新值「doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復。⚠️ 分層依既有形狀：判定放 doctor.py（純函式、不碰 gh），取卡放 doctor_cmd.py（既有 list_items／resolve_project／find_item_by_card_id，實測 :20／:169-170／:221-222）。；⭐ **報告須逐張歸因，值域恰為五類**（⛔ 三類不夠，實測逼出後兩類）：`tool_cannot_read`（解析失敗 ⇒ 修工具）／`undecidable`（建立時刻不可得 ⇒ ⛔ 不猜）／`rule_changed`（卡早於規則 ⇒ 依 disposition 處置）／`writer_nonconformant`（⭐ 卡**晚於**規則卻仍不合規、且經正規通道建立 ⇒ **查寫入端**）／`channel_bypassed`（欄位被手搬、無對應事件 ⇒ 補跑動詞）。；⭐ **判準順序不可換**：tool_cannot_read → undecidable → rule_changed → writer_nonconformant → channel_bypassed。⇒ 理由：前兩者是**我們自己的侷限**，⛔ 不得讓它們變成對卡或對人的指控。實測支持：41 張不合規中 34 張屬 tool_cannot_read（issuecomment-5404753163）。；⭐ **每個 rule_epoch 必須帶宣告過的 disposition，⛔ 不能只有時刻**：`migrate`（殘餘應清掉 ⇒ 報告逐張列出）或 `accept_as_legacy`（需求方已裁定不追溯 ⇒ 報告**只給一行摘要數字**，⛔ 不逐張列）。⚠️ 依據：實測規則變更約**每 3–4 天一次**（最近 20 天 6 次），且殘餘**只累積不清除**——26a0149／6325ae2（2026-08-11）的殘餘至今 14 天原封不動（107 張缺標記、活卡 38 張）。⇒ 沒有 disposition，rule_changed 桶會變成下一個 190，與本卡要解的問題同形。；⭐ **rule_epoch 的值須釘「檢查所依據的那個構件」落地的完整 ISO-8601 時刻**，⛔ 不是日期、也⛔ 不是「大家覺得規則何時開始」的那個 commit。實測教訓：wf-routing 的規則卡是 26a0149（13:01:38），但標記字面由 6325ae2 引入（18:29:56），晚 5.5 小時；用日期粒度會把 21 張誤判，用正確時刻是 16 張。；⭐ 卡的「存在時刻」取值優先序：(1) 卡面 Log 的 `open by` 事件時戳；(2) Issue 的 createdAt；(3) 都沒有 → undecidable。⚠️ 條文須釘死 (2) **只能用於比較 2026-08-04 之後的 epoch**——遷移卡的 Issue 建立於 08-04 而工作早於它，用它比更早的規則會誤判成 writer_nonconformant。⚠️ 取 createdAt 須**擴既有 list_items 查詢**，⛔ 不得加第二次抓取（會違反 doctor_cmd.py:167-183 的「同一次抓取」紀律）。實測母體：41 張無 open by 行（21 首筆 handoff／12 完全無時戳事件／8 assign；活卡 25 張）。；⭐ 通用機制的做法是**把三個既有掃描已共用的形狀抽出來，並讓它們成為第一批實作**，⛔ 不是再蓋第四個單一形態。三個是：legacy_authority_notes（doctor.py:1255）、brief_drift（:1298）、**state_face_drift（:1574——生產碼 0 呼叫端，接線屬 aiwf#65 明列而從未開過的「後續卡」）**。共用形狀含：純函式 audit_X(card_bodies)→XReport、status scanned／not_scanned（⛔ 未掃描不得讀成乾淨）、scanned_cards 記母體數、findings 與 routine_gaps 分開。；⭐ 抽取時**共用信封、⛔ 不共用 finding 型別**：三者攜帶資訊不同（timestamp／op_id／field_name vs reason vs verdict／expected／actual／rule），併型別會損失資訊。三者**都已有 card_id** ⇒ Protocol 約束即可。⚠️ 實測 dataclasses.asdict 對 list[Protocol] 正常遞迴、json.dumps 成功 ⇒ --json 輸出面無風險。；⭐ **改寫既有 render_state_face_drift（doctor.py:1625）使其依 cause 分流處置文案**：現行每筆 drift 無條件輸出「補跑對應的 wfcli 動詞…勿手動搬看板」，⇒ 對 rule_changed 的卡那是**錯誤的指控**。保留既有的「一致／漂移／不判定＋佔比」統計行與「偵測不等於強制」段（後者指名強制面承接者是 aiwf#48）。⚠️ 交付須附變更前後逐字對照，⛔ 不得混在新功能裡帶過。回歸基線：`uv run pytest tests/test_doctor.py -k drift -q` ⇒ **31 passed**（d4ba7ce5；⛔ `-k state_face` 選到 0 支，別用）。；⛔ **不得把 run_doctor 的 card_bodies 參數與掃描用的卡面合成一個**——doctor.py:1822-1827 逐字裁定：那個參數餵給 evaluate_cleanup_guard，順手填上會**沉默地改變 --cleanup-preview 的判定**。⭐ 正解是「同一次 list_items、多個獨立消費者各帶自己的參數」。；⭐ 基線清冊改用本卡自量的數字並附方法與取樣時刻：母體 193 張、不合規 41 張（21%），歸因為 tool_cannot_read 34／card_deficient 7，而 7 張中僅 **2 張非終態**。⛔ **不得引用 aiwf#136 的「161 張中 7 張」**。⚠️ 清冊須逐張帶歸因欄。；⚠️ 接線 state_face_drift 的兩個已知常態須逐字寫進交付：(1) **76% 不判定**（62 張未結案中 47 張，主因 handoff_status_not_in_log 45），其修法「handoff Log 行自帶 stage/status」**今天沒有承接卡**（aiwf#54 的驗收是「第一個遠端寫入帶載荷」，⛔ 不涵蓋 Log 行內容）；(2) **14 筆 open_initial 屬 rule_changed 而非 drift**（成因 1531666，2026-08-21；實測 14/14 開卡日早於該日）。；⚠️ 條文須指名一個本卡**解不掉**的限制：writer_nonconformant 指得出來但**追不下去**——狀態面不記錄「這筆是哪個版本的工具寫的」。實測 16 張卡在規則生效後仍缺 wf-routing 標記（開卡時刻橫跨 2026-08-12T00:11→08-15T10:07，抽驗 5 張全為「有路由行、無標記、Log 完整」），⛔ 根因未查出且本卡不查。；⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。；⚠️ 與既有 legacy_authority_notes 的關係由「合流或劃界」改為**抽取**。⚠️ 且該掃描的既有立場逐字是「報的是**留痕強度不足，不是授權無效**」⇒ 其 findings ⛔ **不進待辦集合**，報告須明示這一點（實測 11 張，本卡曾一度把它們誤算進待辦）。；⚠️ 旗標命名：簡介漂移目前掛在 --legacy-authority-notes 底下（doctor_cmd.py:121／:167 同一個 if），而該旗標 help（:54-55）⛔ 一個字沒提簡介漂移。改名為 --conformance（實查 CI／腳本／文件 0 命中，⛔ 不弄壞自動化），保留舊名為 deprecated alias。交付須明說連帶修正是不是刻意的。；⛔ 授權邊界：執行中若發現**必須修改**本卡未宣告的檔（如 validation.py／card.py），依 canonical §3.2「停 → 寫阻塞發現 → 由需求方裁決」，⛔ 執行者不得自行擴權。；⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時把 service_goal_still_served 納入檢查面；未合併時明列為**已知缺口**。⭐ 兩張寫入集不相交、可真平行；⛔ 先前「S7a 先」已作廢。；回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。；⚠️ 交付時須附「PM 單方面決定清冊」。」；理由 把規劃期第五至九輪的實測落卡（issuecomment-5404840089／5404849912／5404875156／5404887674／5404894912）。四項改變卡的形狀：(1) 歸因由三類改為**五類**——實測 16 張卡在規則生效後仍缺 wf-routing 標記且抽驗 5 張全為「有路由行、無標記、Log 完整」⇒ 既非殘餘也非有人繞過，逼出 writer_nonconformant；另 41 張讀不出建立時刻 ⇒ 逼出 undecidable。(2) 每個 rule_epoch 須帶 disposition——實測規則變更約每 3–4 天一次、且 2026-08-11 的殘餘至今 14 天原封不動 ⇒ 無 disposition 時 rule_changed 桶會變成下一個 190。(3) rule_epoch 須釘構件落地的完整時刻：wf-routing 的規則卡是 26a0149(13:01:38) 而標記由 6325ae2(18:29:56) 引入，用日期粒度會把 21 張誤判、用時刻是 16 張。(4) 存在時刻取值加 Issue createdAt 退路，但釘死只能比 2026-08-04 之後的 epoch。另更正：legacy_authority_notes 的 11 張 findings 依其既有立場「留痕強度不足，不是授權無效」⛔ 不進待辦，本卡曾一度誤算進去。。
- 2026-08-25T12:03:51+08:00 amend by wf-cli（op 090d1d7b）→ 驗證：原值「[ ] 對至少 3 張真實既有卡（含一張 2026-08-04 遷移卡）實跑，附原始輸出。⛔ 不接受自造樣本。；[ ] ⛔ 非阻擋的**負控**：對一張被判不合規的既有卡實跑 amend --dry-run 證明不受阻；handoff 無 dry 路徑，須明列原因與密封探針設計。；[ ] ⭐ **歸因正確性的三組真實樣本**：(a) 取那 14 筆 open_initial 中至少 3 張，證明標為 (a) 而非 (b)；(c) 取那 33 張標題帶後綴的卡中至少 3 張，證明標為 (c)（工具讀不到）而非「卡缺宣告」；(b) 若母體中無真實 (b) 樣本（本輪實測 0 筆），須**明說是零筆**並以構造樣本證明該分支可達，⛔ 不得靜默略過。；[ ] ⭐ 掃描結果與基線清冊**逐張**對帳，差異逐筆附原因；⛔ 「掃到 N 張」不算。並同時記錄母體數與取樣時刻。；[ ] ⭐ state_face_drift 接線的**前後對照**：附接線前（今日直接 import 呼叫）與接線後（wfcli doctor 實跑）的輸出，證明那 14 筆不再被報成 drift。⛔ 只附接線後是零資訊。；[ ] ⭐ 證明對本卡未宣告的檔為零寫入：附本卡分支對 cli/src/wf_cli/validation.py 與 cli/src/wf_cli/card.py 的 git diff 為空（附指令與輸出）。⛔ 自述不算。；[ ] ⚠️ ItemSnapshot.fields 是否對全部母體備齊 validate_open_fields 所需七值，須實測並附缺值卡清冊；⛔ 缺值不得靜默當成不合規（那會落回 (c) 卻被報成卡的缺陷）。；[ ] ⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因；⛔ 標不出原因者代表驗得了、不得列入。」→ 新值「對至少 3 張真實既有卡（含一張 2026-08-04 遷移卡）實跑，附原始輸出。⛔ 不接受自造樣本。；⛔ 非阻擋的**負控**：對一張被判不合規的既有卡實跑 amend --dry-run 證明不受阻；handoff 無 dry 路徑，須明列原因與密封探針設計。；⭐ **五類歸因各取真實樣本證明**：rule_changed 取 14 筆 open_initial 中至少 3 張；tool_cannot_read 取 33 張帶後綴標題中至少 3 張；writer_nonconformant 取 16 張缺 wf-routing 中至少 3 張；undecidable 取 41 張無 open 行中至少 3 張；channel_bypassed 母體中實測 **0 筆** ⇒ 須**明說是零筆**並以構造樣本證明該分支可達，⛔ 不得靜默略過。；⭐ **判準順序的變異檢驗**：把 tool_cannot_read 從第一順位移到最後，證明那 34 張會改被報成其他類（即順序真的承重）。⛔ 只跑正確順序是零資訊。；⭐ disposition 兩種取值各驗一次：migrate 的 epoch 其殘餘**逐張列出**；accept_as_legacy 的 epoch **只出現摘要行、⛔ 不逐張**。附兩份輸出對照。；⭐ createdAt 退路的邊界：取一張 2026-08-04 遷移卡，證明它對 08-04 之前的 epoch **落 undecidable 而非 writer_nonconformant**。⛔ 只驗 happy path 是零資訊。；⭐ state_face_drift 接線的**前後對照**：附接線前（直接 import 呼叫）與接線後（wfcli doctor 實跑）的輸出，證明那 14 筆不再被報成 drift。⛔ 只附接線後是零資訊。；⭐ 掃描結果與基線清冊**逐張**對帳，差異逐筆附原因；⛔「掃到 N 張」不算。同時記錄母體數與取樣時刻。；⭐ 證明對本卡未宣告的檔零寫入：附本卡分支對 validation.py 與 card.py 的 git diff 為空（附指令與輸出）。⛔ 自述不算。；⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因；⛔ 標不出原因者代表驗得了、不得列入。」；理由 把規劃期第五至九輪的實測落卡（issuecomment-5404840089／5404849912／5404875156／5404887674／5404894912）。四項改變卡的形狀：(1) 歸因由三類改為**五類**——實測 16 張卡在規則生效後仍缺 wf-routing 標記且抽驗 5 張全為「有路由行、無標記、Log 完整」⇒ 既非殘餘也非有人繞過，逼出 writer_nonconformant；另 41 張讀不出建立時刻 ⇒ 逼出 undecidable。(2) 每個 rule_epoch 須帶 disposition——實測規則變更約每 3–4 天一次、且 2026-08-11 的殘餘至今 14 天原封不動 ⇒ 無 disposition 時 rule_changed 桶會變成下一個 190。(3) rule_epoch 須釘構件落地的完整時刻：wf-routing 的規則卡是 26a0149(13:01:38) 而標記由 6325ae2(18:29:56) 引入，用日期粒度會把 21 張誤判、用時刻是 16 張。(4) 存在時刻取值加 Issue createdAt 退路，但釘死只能比 2026-08-04 之後的 epoch。另更正：legacy_authority_notes 的 11 張 findings 依其既有立場「留痕強度不足，不是授權無效」⛔ 不進待辦，本卡曾一度誤算進去。。
- 2026-08-25T12:28:39+08:00 amend by wf-cli（op a2c31042）→ 驗收條件：原值「[ ] doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復。⚠️ 分層依既有形狀：判定放 doctor.py（純函式、不碰 gh），取卡放 doctor_cmd.py（既有 list_items／resolve_project／find_item_by_card_id，實測 :20／:169-170／:221-222）。；[ ] ⭐ **報告須逐張歸因，值域恰為五類**（⛔ 三類不夠，實測逼出後兩類）：`tool_cannot_read`（解析失敗 ⇒ 修工具）／`undecidable`（建立時刻不可得 ⇒ ⛔ 不猜）／`rule_changed`（卡早於規則 ⇒ 依 disposition 處置）／`writer_nonconformant`（⭐ 卡**晚於**規則卻仍不合規、且經正規通道建立 ⇒ **查寫入端**）／`channel_bypassed`（欄位被手搬、無對應事件 ⇒ 補跑動詞）。；[ ] ⭐ **判準順序不可換**：tool_cannot_read → undecidable → rule_changed → writer_nonconformant → channel_bypassed。⇒ 理由：前兩者是**我們自己的侷限**，⛔ 不得讓它們變成對卡或對人的指控。實測支持：41 張不合規中 34 張屬 tool_cannot_read（issuecomment-5404753163）。；[ ] ⭐ **每個 rule_epoch 必須帶宣告過的 disposition，⛔ 不能只有時刻**：`migrate`（殘餘應清掉 ⇒ 報告逐張列出）或 `accept_as_legacy`（需求方已裁定不追溯 ⇒ 報告**只給一行摘要數字**，⛔ 不逐張列）。⚠️ 依據：實測規則變更約**每 3–4 天一次**（最近 20 天 6 次），且殘餘**只累積不清除**——26a0149／6325ae2（2026-08-11）的殘餘至今 14 天原封不動（107 張缺標記、活卡 38 張）。⇒ 沒有 disposition，rule_changed 桶會變成下一個 190，與本卡要解的問題同形。；[ ] ⭐ **rule_epoch 的值須釘「檢查所依據的那個構件」落地的完整 ISO-8601 時刻**，⛔ 不是日期、也⛔ 不是「大家覺得規則何時開始」的那個 commit。實測教訓：wf-routing 的規則卡是 26a0149（13:01:38），但標記字面由 6325ae2 引入（18:29:56），晚 5.5 小時；用日期粒度會把 21 張誤判，用正確時刻是 16 張。；[ ] ⭐ 卡的「存在時刻」取值優先序：(1) 卡面 Log 的 `open by` 事件時戳；(2) Issue 的 createdAt；(3) 都沒有 → undecidable。⚠️ 條文須釘死 (2) **只能用於比較 2026-08-04 之後的 epoch**——遷移卡的 Issue 建立於 08-04 而工作早於它，用它比更早的規則會誤判成 writer_nonconformant。⚠️ 取 createdAt 須**擴既有 list_items 查詢**，⛔ 不得加第二次抓取（會違反 doctor_cmd.py:167-183 的「同一次抓取」紀律）。實測母體：41 張無 open by 行（21 首筆 handoff／12 完全無時戳事件／8 assign；活卡 25 張）。；[ ] ⭐ 通用機制的做法是**把三個既有掃描已共用的形狀抽出來，並讓它們成為第一批實作**，⛔ 不是再蓋第四個單一形態。三個是：legacy_authority_notes（doctor.py:1255）、brief_drift（:1298）、**state_face_drift（:1574——生產碼 0 呼叫端，接線屬 aiwf#65 明列而從未開過的「後續卡」）**。共用形狀含：純函式 audit_X(card_bodies)→XReport、status scanned／not_scanned（⛔ 未掃描不得讀成乾淨）、scanned_cards 記母體數、findings 與 routine_gaps 分開。；[ ] ⭐ 抽取時**共用信封、⛔ 不共用 finding 型別**：三者攜帶資訊不同（timestamp／op_id／field_name vs reason vs verdict／expected／actual／rule），併型別會損失資訊。三者**都已有 card_id** ⇒ Protocol 約束即可。⚠️ 實測 dataclasses.asdict 對 list[Protocol] 正常遞迴、json.dumps 成功 ⇒ --json 輸出面無風險。；[ ] ⭐ **改寫既有 render_state_face_drift（doctor.py:1625）使其依 cause 分流處置文案**：現行每筆 drift 無條件輸出「補跑對應的 wfcli 動詞…勿手動搬看板」，⇒ 對 rule_changed 的卡那是**錯誤的指控**。保留既有的「一致／漂移／不判定＋佔比」統計行與「偵測不等於強制」段（後者指名強制面承接者是 aiwf#48）。⚠️ 交付須附變更前後逐字對照，⛔ 不得混在新功能裡帶過。回歸基線：`uv run pytest tests/test_doctor.py -k drift -q` ⇒ **31 passed**（d4ba7ce5；⛔ `-k state_face` 選到 0 支，別用）。；[ ] ⛔ **不得把 run_doctor 的 card_bodies 參數與掃描用的卡面合成一個**——doctor.py:1822-1827 逐字裁定：那個參數餵給 evaluate_cleanup_guard，順手填上會**沉默地改變 --cleanup-preview 的判定**。⭐ 正解是「同一次 list_items、多個獨立消費者各帶自己的參數」。；[ ] ⭐ 基線清冊改用本卡自量的數字並附方法與取樣時刻：母體 193 張、不合規 41 張（21%），歸因為 tool_cannot_read 34／card_deficient 7，而 7 張中僅 **2 張非終態**。⛔ **不得引用 aiwf#136 的「161 張中 7 張」**。⚠️ 清冊須逐張帶歸因欄。；[ ] ⚠️ 接線 state_face_drift 的兩個已知常態須逐字寫進交付：(1) **76% 不判定**（62 張未結案中 47 張，主因 handoff_status_not_in_log 45），其修法「handoff Log 行自帶 stage/status」**今天沒有承接卡**（aiwf#54 的驗收是「第一個遠端寫入帶載荷」，⛔ 不涵蓋 Log 行內容）；(2) **14 筆 open_initial 屬 rule_changed 而非 drift**（成因 1531666，2026-08-21；實測 14/14 開卡日早於該日）。；[ ] ⚠️ 條文須指名一個本卡**解不掉**的限制：writer_nonconformant 指得出來但**追不下去**——狀態面不記錄「這筆是哪個版本的工具寫的」。實測 16 張卡在規則生效後仍缺 wf-routing 標記（開卡時刻橫跨 2026-08-12T00:11→08-15T10:07，抽驗 5 張全為「有路由行、無標記、Log 完整」），⛔ 根因未查出且本卡不查。；[ ] ⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。；[ ] ⚠️ 與既有 legacy_authority_notes 的關係由「合流或劃界」改為**抽取**。⚠️ 且該掃描的既有立場逐字是「報的是**留痕強度不足，不是授權無效**」⇒ 其 findings ⛔ **不進待辦集合**，報告須明示這一點（實測 11 張，本卡曾一度把它們誤算進待辦）。；[ ] ⚠️ 旗標命名：簡介漂移目前掛在 --legacy-authority-notes 底下（doctor_cmd.py:121／:167 同一個 if），而該旗標 help（:54-55）⛔ 一個字沒提簡介漂移。改名為 --conformance（實查 CI／腳本／文件 0 命中，⛔ 不弄壞自動化），保留舊名為 deprecated alias。交付須明說連帶修正是不是刻意的。；[ ] ⛔ 授權邊界：執行中若發現**必須修改**本卡未宣告的檔（如 validation.py／card.py），依 canonical §3.2「停 → 寫阻塞發現 → 由需求方裁決」，⛔ 執行者不得自行擴權。；[ ] ⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時把 service_goal_still_served 納入檢查面；未合併時明列為**已知缺口**。⭐ 兩張寫入集不相交、可真平行；⛔ 先前「S7a 先」已作廢。；[ ] 回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。；[ ] ⚠️ 交付時須附「PM 單方面決定清冊」。」→ 新值「doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復。⚠️ 分層依既有形狀：判定放 doctor.py（純函式、不碰 gh），取卡放 doctor_cmd.py（既有 list_items／resolve_project／find_item_by_card_id，實測 :20／:169-170／:221-222）。；⭐ **報告須逐張歸因，值域恰為五類**（⛔ 三類不夠，實測逼出後兩類）：`tool_cannot_read`（解析失敗 ⇒ 修工具）／`undecidable`（建立時刻不可得 ⇒ ⛔ 不猜）／`rule_changed`（卡早於規則 ⇒ 依 disposition 處置）／`writer_nonconformant`（⭐ 卡**晚於**規則卻仍不合規、且經正規通道建立 ⇒ **查寫入端**）／`channel_bypassed`（欄位被手搬、無對應事件 ⇒ 補跑動詞）。；⭐ **判準順序不可換**：tool_cannot_read → undecidable → rule_changed → writer_nonconformant → channel_bypassed。⇒ 理由：前兩者是**我們自己的侷限**，⛔ 不得讓它們變成對卡或對人的指控。實測支持：41 張不合規中 34 張屬 tool_cannot_read（issuecomment-5404753163）。；⭐ **報告須先分可達性、再談合規性**：新增 `reachability = reachable | unreachable` 這一軸，且它**排在五類歸因之前**。`unreachable` ＝ 唯一的寫入通道（wfcli）在構造上碰不到這張卡 ⇒ 它的任何其他不合規項**都修不了**，⛔ 把它們和「缺核心痛點」列在同一份待辦裡會讓人以為那是能動手的。⚠️ 判準以碼為準（`card.split_at_log` 拋錯／卡面標頭兩行命中數 ≠ 1／無 `## Log` 段落），⛔ 不是啟發式。實測基線：193 張中 **41 張 unreachable（活卡 24，其中 21 張在 💡需求）**，實測拒收原文見 aiwf#138 issuecomment-5404979025。；⭐ **可證偽預測須寫進交付**：本卡上線時 `unreachable = 41`（活卡 24）；`aiwf#105`（其射程已於 2026-08-25 擴充涵蓋這 41 張）落地後**應為 0**，否則兩者之一有缺陷。⛔ 不得只報一個數字而不說它應該往哪走。⚠️ 交付須同時記錄取樣時刻與當時 aiwf#105 的狀態。；⭐ **每個 rule_epoch 必須帶宣告過的 disposition，⛔ 不能只有時刻**：`migrate`（殘餘應清掉 ⇒ 報告逐張列出）或 `accept_as_legacy`（需求方已裁定不追溯 ⇒ 報告**只給一行摘要數字**，⛔ 不逐張列）。⚠️ 依據：實測規則變更約**每 3–4 天一次**（最近 20 天 6 次），且殘餘**只累積不清除**——26a0149／6325ae2（2026-08-11）的殘餘至今 14 天原封不動（107 張缺標記、活卡 38 張）。⇒ 沒有 disposition，rule_changed 桶會變成下一個 190，與本卡要解的問題同形。；⭐ **rule_epoch 的值須釘「檢查所依據的那個構件」落地的完整 ISO-8601 時刻**，⛔ 不是日期、也⛔ 不是「大家覺得規則何時開始」的那個 commit。實測教訓：wf-routing 的規則卡是 26a0149（13:01:38），但標記字面由 6325ae2 引入（18:29:56），晚 5.5 小時；用日期粒度會把 21 張誤判，用正確時刻是 16 張。；⭐ 卡的「存在時刻」取值優先序：(1) 卡面 Log 的 `open by` 事件時戳；(2) Issue 的 createdAt；(3) 都沒有 → undecidable。⚠️ 條文須釘死 (2) **只能用於比較 2026-08-04 之後的 epoch**——遷移卡的 Issue 建立於 08-04 而工作早於它，用它比更早的規則會誤判成 writer_nonconformant。⚠️ 取 createdAt 須**擴既有 list_items 查詢**，⛔ 不得加第二次抓取（會違反 doctor_cmd.py:167-183 的「同一次抓取」紀律）。實測母體：41 張無 open by 行（21 首筆 handoff／12 完全無時戳事件／8 assign；活卡 25 張）。；⭐ 通用機制的做法是**把三個既有掃描已共用的形狀抽出來，並讓它們成為第一批實作**，⛔ 不是再蓋第四個單一形態。三個是：legacy_authority_notes（doctor.py:1255）、brief_drift（:1298）、**state_face_drift（:1574——生產碼 0 呼叫端，接線屬 aiwf#65 明列而從未開過的「後續卡」）**。共用形狀含：純函式 audit_X(card_bodies)→XReport、status scanned／not_scanned（⛔ 未掃描不得讀成乾淨）、scanned_cards 記母體數、findings 與 routine_gaps 分開。；⭐ 抽取時**共用信封、⛔ 不共用 finding 型別**：三者攜帶資訊不同（timestamp／op_id／field_name vs reason vs verdict／expected／actual／rule），併型別會損失資訊。三者**都已有 card_id** ⇒ Protocol 約束即可。⚠️ 實測 dataclasses.asdict 對 list[Protocol] 正常遞迴、json.dumps 成功 ⇒ --json 輸出面無風險。；⭐ **改寫既有 render_state_face_drift（doctor.py:1625）使其依 cause 分流處置文案**：現行每筆 drift 無條件輸出「補跑對應的 wfcli 動詞…勿手動搬看板」，⇒ 對 rule_changed 的卡那是**錯誤的指控**。保留既有的「一致／漂移／不判定＋佔比」統計行與「偵測不等於強制」段（後者指名強制面承接者是 aiwf#48）。⚠️ 交付須附變更前後逐字對照，⛔ 不得混在新功能裡帶過。回歸基線：`uv run pytest tests/test_doctor.py -k drift -q` ⇒ **31 passed**（d4ba7ce5；⛔ `-k state_face` 選到 0 支，別用）。；⛔ **不得把 run_doctor 的 card_bodies 參數與掃描用的卡面合成一個**——doctor.py:1822-1827 逐字裁定：那個參數餵給 evaluate_cleanup_guard，順手填上會**沉默地改變 --cleanup-preview 的判定**。⭐ 正解是「同一次 list_items、多個獨立消費者各帶自己的參數」。；⭐ 基線清冊改用本卡自量的數字並附方法與取樣時刻：母體 193 張、不合規 41 張（21%），歸因為 tool_cannot_read 34／card_deficient 7，而 7 張中僅 **2 張非終態**。⛔ **不得引用 aiwf#136 的「161 張中 7 張」**。⚠️ 清冊須逐張帶歸因欄。；⚠️ 接線 state_face_drift 的兩個已知常態須逐字寫進交付：(1) **76% 不判定**（62 張未結案中 47 張，主因 handoff_status_not_in_log 45），其修法「handoff Log 行自帶 stage/status」**今天沒有承接卡**（aiwf#54 的驗收是「第一個遠端寫入帶載荷」，⛔ 不涵蓋 Log 行內容）；(2) **14 筆 open_initial 屬 rule_changed 而非 drift**（成因 1531666，2026-08-21；實測 14/14 開卡日早於該日）。；⚠️ 條文須指名一個本卡**解不掉**的限制：writer_nonconformant 指得出來但**追不下去**——狀態面不記錄「這筆是哪個版本的工具寫的」。實測 16 張卡在規則生效後仍缺 wf-routing 標記（開卡時刻橫跨 2026-08-12T00:11→08-15T10:07，抽驗 5 張全為「有路由行、無標記、Log 完整」），⛔ 根因未查出且本卡不查。；⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。；⚠️ 與既有 legacy_authority_notes 的關係由「合流或劃界」改為**抽取**。⚠️ 且該掃描的既有立場逐字是「報的是**留痕強度不足，不是授權無效**」⇒ 其 findings ⛔ **不進待辦集合**，報告須明示這一點（實測 11 張，本卡曾一度把它們誤算進待辦）。；⚠️ 旗標命名：簡介漂移目前掛在 --legacy-authority-notes 底下（doctor_cmd.py:121／:167 同一個 if），而該旗標 help（:54-55）⛔ 一個字沒提簡介漂移。改名為 --conformance（實查 CI／腳本／文件 0 命中，⛔ 不弄壞自動化），保留舊名為 deprecated alias。交付須明說連帶修正是不是刻意的。；⛔ 授權邊界：執行中若發現**必須修改**本卡未宣告的檔（如 validation.py／card.py），依 canonical §3.2「停 → 寫阻塞發現 → 由需求方裁決」，⛔ 執行者不得自行擴權。；⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時把 service_goal_still_served 納入檢查面；未合併時明列為**已知缺口**。⭐ 兩張寫入集不相交、可真平行；⛔ 先前「S7a 先」已作廢。；回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。；⚠️ 交付時須附「PM 單方面決定清冊」。；⭐ **欄位層掃描（與 per-card findings 正交）**：比對看板實際帶過值的欄位集合 vs `project.FIELD_SPECS`，列出 (i) **有值但未宣告的孤兒欄位**、(ii) 宣告了但零張卡有值的欄位。⚠️ 這不是某一張卡的問題，是**狀態面本身的形狀問題** ⇒ 報告須有獨立區段，⛔ 不得把 N 張卡各報一筆。實測基線（2026-08-25）：孤兒欄位 **1 個**＝`分支／worktree`（全形斜線；`FIELD_SPECS` 宣告的是 `分支worktree`），41 張卡有值、8 張兩欄都有值、33 張只有舊欄（其中 30 張是佔位 `—`）⇒ **真正讀不到的登記 3 張、非終態 0 張**；(ii) 實測 **0 個**。⚠️ 成因是遷移用 Ledger 欄名建欄、CLI 同日用自己的常數建了第二個（`registry.py:261` 逐字有 `分支／worktree` 欄名；`9ef3154` 的 FIELD_SPECS 從一開始就是 `分支worktree`），而 `ensure_fields` **冪等但只增不減** ⇒ ⭐ 每次欄位命名分歧都會留一個孤兒，而沒有任何東西會說。；⚠️ 稽核取值一律走 `wf_cli.project.list_items` 正規路徑，⛔ **不得用 `gh project item-list`**——`project.py:377-378` 逐字記載後者「對中文欄位名稱的 JSON key 有編碼錯誤」。⚠️ 本卡研究期 PM 十餘支探針全踩此坑（結論重驗後不變，但方法錯）。⭐ 且判定一律直接呼叫 `wf_cli` 的純函式（`audit_state_face_drift`／`validate_open_fields`／`resources.try_parse_block`／`card.split_at_log`），⇒ 盤點結果與守衛判定**同源**。」；理由 把規劃期第十、十一輪的實測落卡（issuecomment-5404946150／5404979025）並補上方法紀律。新增四條驗收：(1) reachability 軸且排在五類歸因之前——實測 41 張 amend 構造上打不到（活卡 24、21 張在 💡需求），其他不合規項對它們修不了，混列會誤導；(2) 可證偽預測——上線時 unreachable=41，aiwf#105（射程已於本日擴充涵蓋這 41 張）落地後應為 0；(3) 欄位層掃描——實測孤兒欄位 1 個（分支／worktree，41 張有值但 FIELD_SPECS 未宣告故無人讀），成因是 ensure_fields 冪等但只增不減；(4) 取值一律走 list_items 正規路徑，⛔ 不用 gh project item-list（project.py:377-378 逐字記載其中文欄位 key 編碼錯誤，PM 研究期十餘支探針全踩）。驗證同步新增三條：可達性判準的變異檢驗（含不誤報側）、欄位層掃描的負控、盤點與守衛同源的雙路徑對照。。
- 2026-08-25T12:28:39+08:00 amend by wf-cli（op a2c31042）→ 驗證：原值「[ ] 對至少 3 張真實既有卡（含一張 2026-08-04 遷移卡）實跑，附原始輸出。⛔ 不接受自造樣本。；[ ] ⛔ 非阻擋的**負控**：對一張被判不合規的既有卡實跑 amend --dry-run 證明不受阻；handoff 無 dry 路徑，須明列原因與密封探針設計。；[ ] ⭐ **五類歸因各取真實樣本證明**：rule_changed 取 14 筆 open_initial 中至少 3 張；tool_cannot_read 取 33 張帶後綴標題中至少 3 張；writer_nonconformant 取 16 張缺 wf-routing 中至少 3 張；undecidable 取 41 張無 open 行中至少 3 張；channel_bypassed 母體中實測 **0 筆** ⇒ 須**明說是零筆**並以構造樣本證明該分支可達，⛔ 不得靜默略過。；[ ] ⭐ **判準順序的變異檢驗**：把 tool_cannot_read 從第一順位移到最後，證明那 34 張會改被報成其他類（即順序真的承重）。⛔ 只跑正確順序是零資訊。；[ ] ⭐ disposition 兩種取值各驗一次：migrate 的 epoch 其殘餘**逐張列出**；accept_as_legacy 的 epoch **只出現摘要行、⛔ 不逐張**。附兩份輸出對照。；[ ] ⭐ createdAt 退路的邊界：取一張 2026-08-04 遷移卡，證明它對 08-04 之前的 epoch **落 undecidable 而非 writer_nonconformant**。⛔ 只驗 happy path 是零資訊。；[ ] ⭐ state_face_drift 接線的**前後對照**：附接線前（直接 import 呼叫）與接線後（wfcli doctor 實跑）的輸出，證明那 14 筆不再被報成 drift。⛔ 只附接線後是零資訊。；[ ] ⭐ 掃描結果與基線清冊**逐張**對帳，差異逐筆附原因；⛔「掃到 N 張」不算。同時記錄母體數與取樣時刻。；[ ] ⭐ 證明對本卡未宣告的檔零寫入：附本卡分支對 validation.py 與 card.py 的 git diff 為空（附指令與輸出）。⛔ 自述不算。；[ ] ⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因；⛔ 標不出原因者代表驗得了、不得列入。」→ 新值「對至少 3 張真實既有卡（含一張 2026-08-04 遷移卡）實跑，附原始輸出。⛔ 不接受自造樣本。；⛔ 非阻擋的**負控**：對一張被判不合規的既有卡實跑 amend --dry-run 證明不受阻；handoff 無 dry 路徑，須明列原因與密封探針設計。；⭐ **五類歸因各取真實樣本證明**：rule_changed 取 14 筆 open_initial 中至少 3 張；tool_cannot_read 取 33 張帶後綴標題中至少 3 張；writer_nonconformant 取 16 張缺 wf-routing 中至少 3 張；undecidable 取 41 張無 open 行中至少 3 張；channel_bypassed 母體中實測 **0 筆** ⇒ 須**明說是零筆**並以構造樣本證明該分支可達，⛔ 不得靜默略過。；⭐ **判準順序的變異檢驗**：把 tool_cannot_read 從第一順位移到最後，證明那 34 張會改被報成其他類（即順序真的承重）。⛔ 只跑正確順序是零資訊。；⭐ disposition 兩種取值各驗一次：migrate 的 epoch 其殘餘**逐張列出**；accept_as_legacy 的 epoch **只出現摘要行、⛔ 不逐張**。附兩份輸出對照。；⭐ createdAt 退路的邊界：取一張 2026-08-04 遷移卡，證明它對 08-04 之前的 epoch **落 undecidable 而非 writer_nonconformant**。⛔ 只驗 happy path 是零資訊。；⭐ state_face_drift 接線的**前後對照**：附接線前（直接 import 呼叫）與接線後（wfcli doctor 實跑）的輸出，證明那 14 筆不再被報成 drift。⛔ 只附接線後是零資訊。；⭐ 掃描結果與基線清冊**逐張**對帳，差異逐筆附原因；⛔「掃到 N 張」不算。同時記錄母體數與取樣時刻。；⭐ 證明對本卡未宣告的檔零寫入：附本卡分支對 validation.py 與 card.py 的 git diff 為空（附指令與輸出）。⛔ 自述不算。；⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因；⛔ 標不出原因者代表驗得了、不得列入。；⭐ **可達性判準的變異檢驗**：取 41 張中至少 3 張（三種成因各一）以 `amend --dry-run` 實跑，附拒收原文；再取一張 reachable 的真實卡證明**不誤報**。⛔ 只驗 unreachable 那側是零資訊。；⭐ **欄位層掃描的負控**：構造一個「宣告了但零卡有值」的情形證明 (ii) 分支可達（實測母體為 0，⇒ 不構造就永遠測不到）；並證明孤兒欄位 `分支／worktree` 被列在**獨立區段**而非逐卡 findings。；⚠️ 證明本卡的盤點與守衛同源：附至少一項量測，其結果由**直接呼叫 wf_cli 純函式**與**經 wfcli doctor 輸出**兩條路徑取得且逐字相同。⛔ 只跑一條無法排除自寫判定與工具判定不一致。」；理由 把規劃期第十、十一輪的實測落卡（issuecomment-5404946150／5404979025）並補上方法紀律。新增四條驗收：(1) reachability 軸且排在五類歸因之前——實測 41 張 amend 構造上打不到（活卡 24、21 張在 💡需求），其他不合規項對它們修不了，混列會誤導；(2) 可證偽預測——上線時 unreachable=41，aiwf#105（射程已於本日擴充涵蓋這 41 張）落地後應為 0；(3) 欄位層掃描——實測孤兒欄位 1 個（分支／worktree，41 張有值但 FIELD_SPECS 未宣告故無人讀），成因是 ensure_fields 冪等但只增不減；(4) 取值一律走 list_items 正規路徑，⛔ 不用 gh project item-list（project.py:377-378 逐字記載其中文欄位 key 編碼錯誤，PM 研究期十餘支探針全踩）。驗證同步新增三條：可達性判準的變異檢驗（含不誤報側）、欄位層掃描的負控、盤點與守衛同源的雙路徑對照。。
- 2026-08-25T12:32:39+08:00 amend by wf-cli（op f754033d）→ 驗收條件：原值「[ ] doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復。⚠️ 分層依既有形狀：判定放 doctor.py（純函式、不碰 gh），取卡放 doctor_cmd.py（既有 list_items／resolve_project／find_item_by_card_id，實測 :20／:169-170／:221-222）。；[ ] ⭐ **報告須逐張歸因，值域恰為五類**（⛔ 三類不夠，實測逼出後兩類）：`tool_cannot_read`（解析失敗 ⇒ 修工具）／`undecidable`（建立時刻不可得 ⇒ ⛔ 不猜）／`rule_changed`（卡早於規則 ⇒ 依 disposition 處置）／`writer_nonconformant`（⭐ 卡**晚於**規則卻仍不合規、且經正規通道建立 ⇒ **查寫入端**）／`channel_bypassed`（欄位被手搬、無對應事件 ⇒ 補跑動詞）。；[ ] ⭐ **判準順序不可換**：tool_cannot_read → undecidable → rule_changed → writer_nonconformant → channel_bypassed。⇒ 理由：前兩者是**我們自己的侷限**，⛔ 不得讓它們變成對卡或對人的指控。實測支持：41 張不合規中 34 張屬 tool_cannot_read（issuecomment-5404753163）。；[ ] ⭐ **報告須先分可達性、再談合規性**：新增 `reachability = reachable | unreachable` 這一軸，且它**排在五類歸因之前**。`unreachable` ＝ 唯一的寫入通道（wfcli）在構造上碰不到這張卡 ⇒ 它的任何其他不合規項**都修不了**，⛔ 把它們和「缺核心痛點」列在同一份待辦裡會讓人以為那是能動手的。⚠️ 判準以碼為準（`card.split_at_log` 拋錯／卡面標頭兩行命中數 ≠ 1／無 `## Log` 段落），⛔ 不是啟發式。實測基線：193 張中 **41 張 unreachable（活卡 24，其中 21 張在 💡需求）**，實測拒收原文見 aiwf#138 issuecomment-5404979025。；[ ] ⭐ **可證偽預測須寫進交付**：本卡上線時 `unreachable = 41`（活卡 24）；`aiwf#105`（其射程已於 2026-08-25 擴充涵蓋這 41 張）落地後**應為 0**，否則兩者之一有缺陷。⛔ 不得只報一個數字而不說它應該往哪走。⚠️ 交付須同時記錄取樣時刻與當時 aiwf#105 的狀態。；[ ] ⭐ **每個 rule_epoch 必須帶宣告過的 disposition，⛔ 不能只有時刻**：`migrate`（殘餘應清掉 ⇒ 報告逐張列出）或 `accept_as_legacy`（需求方已裁定不追溯 ⇒ 報告**只給一行摘要數字**，⛔ 不逐張列）。⚠️ 依據：實測規則變更約**每 3–4 天一次**（最近 20 天 6 次），且殘餘**只累積不清除**——26a0149／6325ae2（2026-08-11）的殘餘至今 14 天原封不動（107 張缺標記、活卡 38 張）。⇒ 沒有 disposition，rule_changed 桶會變成下一個 190，與本卡要解的問題同形。；[ ] ⭐ **rule_epoch 的值須釘「檢查所依據的那個構件」落地的完整 ISO-8601 時刻**，⛔ 不是日期、也⛔ 不是「大家覺得規則何時開始」的那個 commit。實測教訓：wf-routing 的規則卡是 26a0149（13:01:38），但標記字面由 6325ae2 引入（18:29:56），晚 5.5 小時；用日期粒度會把 21 張誤判，用正確時刻是 16 張。；[ ] ⭐ 卡的「存在時刻」取值優先序：(1) 卡面 Log 的 `open by` 事件時戳；(2) Issue 的 createdAt；(3) 都沒有 → undecidable。⚠️ 條文須釘死 (2) **只能用於比較 2026-08-04 之後的 epoch**——遷移卡的 Issue 建立於 08-04 而工作早於它，用它比更早的規則會誤判成 writer_nonconformant。⚠️ 取 createdAt 須**擴既有 list_items 查詢**，⛔ 不得加第二次抓取（會違反 doctor_cmd.py:167-183 的「同一次抓取」紀律）。實測母體：41 張無 open by 行（21 首筆 handoff／12 完全無時戳事件／8 assign；活卡 25 張）。；[ ] ⭐ 通用機制的做法是**把三個既有掃描已共用的形狀抽出來，並讓它們成為第一批實作**，⛔ 不是再蓋第四個單一形態。三個是：legacy_authority_notes（doctor.py:1255）、brief_drift（:1298）、**state_face_drift（:1574——生產碼 0 呼叫端，接線屬 aiwf#65 明列而從未開過的「後續卡」）**。共用形狀含：純函式 audit_X(card_bodies)→XReport、status scanned／not_scanned（⛔ 未掃描不得讀成乾淨）、scanned_cards 記母體數、findings 與 routine_gaps 分開。；[ ] ⭐ 抽取時**共用信封、⛔ 不共用 finding 型別**：三者攜帶資訊不同（timestamp／op_id／field_name vs reason vs verdict／expected／actual／rule），併型別會損失資訊。三者**都已有 card_id** ⇒ Protocol 約束即可。⚠️ 實測 dataclasses.asdict 對 list[Protocol] 正常遞迴、json.dumps 成功 ⇒ --json 輸出面無風險。；[ ] ⭐ **改寫既有 render_state_face_drift（doctor.py:1625）使其依 cause 分流處置文案**：現行每筆 drift 無條件輸出「補跑對應的 wfcli 動詞…勿手動搬看板」，⇒ 對 rule_changed 的卡那是**錯誤的指控**。保留既有的「一致／漂移／不判定＋佔比」統計行與「偵測不等於強制」段（後者指名強制面承接者是 aiwf#48）。⚠️ 交付須附變更前後逐字對照，⛔ 不得混在新功能裡帶過。回歸基線：`uv run pytest tests/test_doctor.py -k drift -q` ⇒ **31 passed**（d4ba7ce5；⛔ `-k state_face` 選到 0 支，別用）。；[ ] ⛔ **不得把 run_doctor 的 card_bodies 參數與掃描用的卡面合成一個**——doctor.py:1822-1827 逐字裁定：那個參數餵給 evaluate_cleanup_guard，順手填上會**沉默地改變 --cleanup-preview 的判定**。⭐ 正解是「同一次 list_items、多個獨立消費者各帶自己的參數」。；[ ] ⭐ 基線清冊改用本卡自量的數字並附方法與取樣時刻：母體 193 張、不合規 41 張（21%），歸因為 tool_cannot_read 34／card_deficient 7，而 7 張中僅 **2 張非終態**。⛔ **不得引用 aiwf#136 的「161 張中 7 張」**。⚠️ 清冊須逐張帶歸因欄。；[ ] ⚠️ 接線 state_face_drift 的兩個已知常態須逐字寫進交付：(1) **76% 不判定**（62 張未結案中 47 張，主因 handoff_status_not_in_log 45），其修法「handoff Log 行自帶 stage/status」**今天沒有承接卡**（aiwf#54 的驗收是「第一個遠端寫入帶載荷」，⛔ 不涵蓋 Log 行內容）；(2) **14 筆 open_initial 屬 rule_changed 而非 drift**（成因 1531666，2026-08-21；實測 14/14 開卡日早於該日）。；[ ] ⚠️ 條文須指名一個本卡**解不掉**的限制：writer_nonconformant 指得出來但**追不下去**——狀態面不記錄「這筆是哪個版本的工具寫的」。實測 16 張卡在規則生效後仍缺 wf-routing 標記（開卡時刻橫跨 2026-08-12T00:11→08-15T10:07，抽驗 5 張全為「有路由行、無標記、Log 完整」），⛔ 根因未查出且本卡不查。；[ ] ⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。；[ ] ⚠️ 與既有 legacy_authority_notes 的關係由「合流或劃界」改為**抽取**。⚠️ 且該掃描的既有立場逐字是「報的是**留痕強度不足，不是授權無效**」⇒ 其 findings ⛔ **不進待辦集合**，報告須明示這一點（實測 11 張，本卡曾一度把它們誤算進待辦）。；[ ] ⚠️ 旗標命名：簡介漂移目前掛在 --legacy-authority-notes 底下（doctor_cmd.py:121／:167 同一個 if），而該旗標 help（:54-55）⛔ 一個字沒提簡介漂移。改名為 --conformance（實查 CI／腳本／文件 0 命中，⛔ 不弄壞自動化），保留舊名為 deprecated alias。交付須明說連帶修正是不是刻意的。；[ ] ⛔ 授權邊界：執行中若發現**必須修改**本卡未宣告的檔（如 validation.py／card.py），依 canonical §3.2「停 → 寫阻塞發現 → 由需求方裁決」，⛔ 執行者不得自行擴權。；[ ] ⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時把 service_goal_still_served 納入檢查面；未合併時明列為**已知缺口**。⭐ 兩張寫入集不相交、可真平行；⛔ 先前「S7a 先」已作廢。；[ ] 回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。；[ ] ⚠️ 交付時須附「PM 單方面決定清冊」。；[ ] ⭐ **欄位層掃描（與 per-card findings 正交）**：比對看板實際帶過值的欄位集合 vs `project.FIELD_SPECS`，列出 (i) **有值但未宣告的孤兒欄位**、(ii) 宣告了但零張卡有值的欄位。⚠️ 這不是某一張卡的問題，是**狀態面本身的形狀問題** ⇒ 報告須有獨立區段，⛔ 不得把 N 張卡各報一筆。實測基線（2026-08-25）：孤兒欄位 **1 個**＝`分支／worktree`（全形斜線；`FIELD_SPECS` 宣告的是 `分支worktree`），41 張卡有值、8 張兩欄都有值、33 張只有舊欄（其中 30 張是佔位 `—`）⇒ **真正讀不到的登記 3 張、非終態 0 張**；(ii) 實測 **0 個**。⚠️ 成因是遷移用 Ledger 欄名建欄、CLI 同日用自己的常數建了第二個（`registry.py:261` 逐字有 `分支／worktree` 欄名；`9ef3154` 的 FIELD_SPECS 從一開始就是 `分支worktree`），而 `ensure_fields` **冪等但只增不減** ⇒ ⭐ 每次欄位命名分歧都會留一個孤兒，而沒有任何東西會說。；[ ] ⚠️ 稽核取值一律走 `wf_cli.project.list_items` 正規路徑，⛔ **不得用 `gh project item-list`**——`project.py:377-378` 逐字記載後者「對中文欄位名稱的 JSON key 有編碼錯誤」。⚠️ 本卡研究期 PM 十餘支探針全踩此坑（結論重驗後不變，但方法錯）。⭐ 且判定一律直接呼叫 `wf_cli` 的純函式（`audit_state_face_drift`／`validate_open_fields`／`resources.try_parse_block`／`card.split_at_log`），⇒ 盤點結果與守衛判定**同源**。」→ 新值「doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復。⚠️ 分層依既有形狀：判定放 doctor.py（純函式、不碰 gh），取卡放 doctor_cmd.py（既有 list_items／resolve_project／find_item_by_card_id，實測 :20／:169-170／:221-222）。；⭐ **報告須逐張歸因，值域恰為五類**（⛔ 三類不夠，實測逼出後兩類）：`tool_cannot_read`（解析失敗 ⇒ 修工具）／`undecidable`（建立時刻不可得 ⇒ ⛔ 不猜）／`rule_changed`（卡早於規則 ⇒ 依 disposition 處置）／`writer_nonconformant`（⭐ 卡**晚於**規則卻仍不合規、且經正規通道建立 ⇒ **查寫入端**）／`channel_bypassed`（欄位被手搬、無對應事件 ⇒ 補跑動詞）。；⭐ **判準順序不可換**：tool_cannot_read → undecidable → rule_changed → writer_nonconformant → channel_bypassed。⇒ 理由：前兩者是**我們自己的侷限**，⛔ 不得讓它們變成對卡或對人的指控。實測支持：41 張不合規中 34 張屬 tool_cannot_read（issuecomment-5404753163）。；⭐ **報告須先分可達性、再談合規性**：新增 `reachability = reachable | unreachable` 這一軸，且它**排在五類歸因之前**。`unreachable` ＝ 唯一的寫入通道（wfcli）在構造上碰不到這張卡 ⇒ 它的任何其他不合規項**都修不了**，⛔ 把它們和「缺核心痛點」列在同一份待辦裡會讓人以為那是能動手的。⚠️ 判準以碼為準（`card.split_at_log` 拋錯／卡面標頭兩行命中數 ≠ 1／無 `## Log` 段落），⛔ 不是啟發式。實測基線：193 張中 **41 張 unreachable（活卡 24，其中 21 張在 💡需求）**，實測拒收原文見 aiwf#138 issuecomment-5404979025。；⭐ **可證偽預測須寫進交付**：本卡上線時 `unreachable = 41`（活卡 24）；`aiwf#105`（其射程已於 2026-08-25 擴充涵蓋這 41 張）落地後**應為 0**，否則兩者之一有缺陷。⛔ 不得只報一個數字而不說它應該往哪走。⚠️ 交付須同時記錄取樣時刻與當時 aiwf#105 的狀態。；⭐ **每個 rule_epoch 必須帶宣告過的 disposition，⛔ 不能只有時刻**：`migrate`（殘餘應清掉 ⇒ 報告逐張列出）或 `accept_as_legacy`（需求方已裁定不追溯 ⇒ 報告**只給一行摘要數字**，⛔ 不逐張列）。⚠️ 依據：實測規則變更約**每 3–4 天一次**（最近 20 天 6 次），且殘餘**只累積不清除**——26a0149／6325ae2（2026-08-11）的殘餘至今 14 天原封不動（107 張缺標記、活卡 38 張）。⇒ 沒有 disposition，rule_changed 桶會變成下一個 190，與本卡要解的問題同形。；⭐ **rule_epoch 的值須釘「檢查所依據的那個構件」落地的完整 ISO-8601 時刻**，⛔ 不是日期、也⛔ 不是「大家覺得規則何時開始」的那個 commit。實測教訓：wf-routing 的規則卡是 26a0149（13:01:38），但標記字面由 6325ae2 引入（18:29:56），晚 5.5 小時；用日期粒度會把 21 張誤判，用正確時刻是 16 張。；⭐ 卡的「存在時刻」取值優先序：(1) 卡面 Log 的 `open by` 事件時戳；(2) Issue 的 createdAt；(3) 都沒有 → undecidable。⚠️ 條文須釘死 (2) **只能用於比較 2026-08-04 之後的 epoch**——遷移卡的 Issue 建立於 08-04 而工作早於它，用它比更早的規則會誤判成 writer_nonconformant。⚠️ 取 createdAt 須**擴既有 list_items 查詢**，⛔ 不得加第二次抓取（會違反 doctor_cmd.py:167-183 的「同一次抓取」紀律）。實測母體：41 張無 open by 行（21 首筆 handoff／12 完全無時戳事件／8 assign；活卡 25 張）。；⭐ 通用機制的做法是**把三個既有掃描已共用的形狀抽出來，並讓它們成為第一批實作**，⛔ 不是再蓋第四個單一形態。三個是：legacy_authority_notes（doctor.py:1255）、brief_drift（:1298）、**state_face_drift（:1574——生產碼 0 呼叫端，接線屬 aiwf#65 明列而從未開過的「後續卡」）**。共用形狀含：純函式 audit_X(card_bodies)→XReport、status scanned／not_scanned（⛔ 未掃描不得讀成乾淨）、scanned_cards 記母體數、findings 與 routine_gaps 分開。；⭐ 抽取時**共用信封、⛔ 不共用 finding 型別**：三者攜帶資訊不同（timestamp／op_id／field_name vs reason vs verdict／expected／actual／rule），併型別會損失資訊。三者**都已有 card_id** ⇒ Protocol 約束即可。⚠️ 實測 dataclasses.asdict 對 list[Protocol] 正常遞迴、json.dumps 成功 ⇒ --json 輸出面無風險。；⭐ **改寫既有 render_state_face_drift（doctor.py:1625）使其依 cause 分流處置文案**：現行每筆 drift 無條件輸出「補跑對應的 wfcli 動詞…勿手動搬看板」，⇒ 對 rule_changed 的卡那是**錯誤的指控**。保留既有的「一致／漂移／不判定＋佔比」統計行與「偵測不等於強制」段（後者指名強制面承接者是 aiwf#48）。⚠️ 交付須附變更前後逐字對照，⛔ 不得混在新功能裡帶過。回歸基線：`uv run pytest tests/test_doctor.py -k drift -q` ⇒ **31 passed**（d4ba7ce5；⛔ `-k state_face` 選到 0 支，別用）。；⛔ **不得把 run_doctor 的 card_bodies 參數與掃描用的卡面合成一個**——doctor.py:1822-1827 逐字裁定：那個參數餵給 evaluate_cleanup_guard，順手填上會**沉默地改變 --cleanup-preview 的判定**。⭐ 正解是「同一次 list_items、多個獨立消費者各帶自己的參數」。；⭐ 基線清冊改用本卡自量的數字並附方法與取樣時刻：母體 193 張、不合規 41 張（21%），歸因為 tool_cannot_read 34／card_deficient 7，而 7 張中僅 **2 張非終態**。⛔ **不得引用 aiwf#136 的「161 張中 7 張」**。⚠️ 清冊須逐張帶歸因欄。；⚠️ 接線 state_face_drift 的兩個已知常態須逐字寫進交付：(1) **76% 不判定**（62 張未結案中 47 張，主因 handoff_status_not_in_log 45），其修法「handoff Log 行自帶 stage/status」**今天沒有承接卡**（aiwf#54 的驗收是「第一個遠端寫入帶載荷」，⛔ 不涵蓋 Log 行內容）；(2) **14 筆 open_initial 屬 rule_changed 而非 drift**（成因 1531666，2026-08-21；實測 14/14 開卡日早於該日）。；⚠️ 條文須指名一個本卡**解不掉**的限制：writer_nonconformant 指得出來但**追不下去**——狀態面不記錄「這筆是哪個版本的工具寫的」。實測 16 張卡在規則生效後仍缺 wf-routing 標記（開卡時刻橫跨 2026-08-12T00:11→08-15T10:07，抽驗 5 張全為「有路由行、無標記、Log 完整」），⛔ 根因未查出且本卡不查。；⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。；⚠️ 與既有 legacy_authority_notes 的關係由「合流或劃界」改為**抽取**。⚠️ 且該掃描的既有立場逐字是「報的是**留痕強度不足，不是授權無效**」⇒ 其 findings ⛔ **不進待辦集合**，報告須明示這一點（實測 11 張，本卡曾一度把它們誤算進待辦）。；⚠️ 旗標命名：簡介漂移目前掛在 --legacy-authority-notes 底下（doctor_cmd.py:121／:167 同一個 if），而該旗標 help（:54-55）⛔ 一個字沒提簡介漂移。改名為 --conformance（實查 CI／腳本／文件 0 命中，⛔ 不弄壞自動化），保留舊名為 deprecated alias。交付須明說連帶修正是不是刻意的。；⛔ 授權邊界：執行中若發現**必須修改**本卡未宣告的檔（如 validation.py／card.py），依 canonical §3.2「停 → 寫阻塞發現 → 由需求方裁決」，⛔ 執行者不得自行擴權。；⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時把 service_goal_still_served 納入檢查面；未合併時明列為**已知缺口**。⭐ 兩張寫入集不相交、可真平行；⛔ 先前「S7a 先」已作廢。；回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。；⚠️ 交付時須附「PM 單方面決定清冊」。；⭐ **欄位層掃描（與 per-card findings 正交）**：比對看板實際帶過值的欄位集合 vs `project.FIELD_SPECS`，列出 (i) **有值但未宣告的孤兒欄位**、(ii) 宣告了但零張卡有值的欄位。⚠️ 這不是某一張卡的問題，是**狀態面本身的形狀問題** ⇒ 報告須有獨立區段，⛔ 不得把 N 張卡各報一筆。實測基線（2026-08-25）：孤兒欄位 **1 個**＝`分支／worktree`（全形斜線；`FIELD_SPECS` 宣告的是 `分支worktree`），41 張卡有值、8 張兩欄都有值、33 張只有舊欄（其中 30 張是佔位 `—`）⇒ **真正讀不到的登記 3 張、非終態 0 張**；(ii) 實測 **0 個**。⚠️ 成因是遷移用 Ledger 欄名建欄、CLI 同日用自己的常數建了第二個（`registry.py:261` 逐字有 `分支／worktree` 欄名；`9ef3154` 的 FIELD_SPECS 從一開始就是 `分支worktree`），而 `ensure_fields` **冪等但只增不減** ⇒ ⭐ 每次欄位命名分歧都會留一個孤兒，而沒有任何東西會說。；⚠️ 稽核取值一律走 `wf_cli.project.list_items` 正規路徑，⛔ **不得用 `gh project item-list`**——`project.py:377-378` 逐字記載後者「對中文欄位名稱的 JSON key 有編碼錯誤」。⚠️ 本卡研究期 PM 十餘支探針全踩此坑（結論重驗後不變，但方法錯）。⭐ 且判定一律直接呼叫 `wf_cli` 的純函式（`audit_state_face_drift`／`validate_open_fields`／`resources.try_parse_block`／`card.split_at_log`），⇒ 盤點結果與守衛判定**同源**。；⭐ **`writer_nonconformant` 的 finding 必須自帶可追溯的兩個時刻**（需求方 2026-08-25 裁定：本類保留為完整一類）：(1) 該規則的 `rule_epoch`、(2) 該卡的建立時刻。⇒ 接手的人可直接做 git 考古比對寫入端的 commit 時序，⛔ 不用重新推導一次。⚠️ 依據：狀態面**沒有任何工具版本可查**——`cli/pyproject.toml` 的 `version` 自 2026-08-04 起凍在 `0.1.0` 未曾 bump，`wfcli` 也**沒有 `--version`**，Log 行只寫 `by wf-cli` ⇒ 「這筆是哪個版本寫的」構造上無解。⭐ 但**追得下去**：本卡研究期即以 commit 時序追出那 16 張的形狀（開卡於 2026-08-12→08-15、有路由行、無標記、Log 完整，見 issuecomment-5404887674）。⚠️ 該類的真正風險是 **epoch 精確度**（實測挑錯 commit 會讓 16 變成 21）⇒ 由既有的「epoch 須釘構件落地的完整 ISO-8601 時刻」那條驗收承接。⚠️ 本卡**不解決**版本缺口本身（無 version／無 --version），僅在條文中指名。」；理由 需求方 2026-08-25 裁定：writer_nonconformant 保留為完整一類，並補一條讓它可追溯。查證後 PM 先前「報出來之後沒有下一步」的說法過重——狀態面確實沒有工具版本可查（pyproject version 自 08-04 凍在 0.1.0、wfcli 無 --version、Log 只寫 by wf-cli），但研究期已用 commit 時序成功追出那 16 張的形狀 ⇒ 追得下去，只是走 git 考古而非查版本號。保留該類的理由：它是五類中唯一分得出「還在持續產出新壞卡的洞」與「既有存量損害」的一類。新增條款要求每筆 finding 自帶 rule_epoch 與卡的建立時刻，讓接手者免於重新推導。。
- 2026-08-25T12:33:39+08:00 handoff by wf-cli → owner 待認領；iteration 0；SHA d4ba7ce5f3fa526fc3a7aa0ebbeee3c926e5eb28；證據 T3 規劃閘門通過：需求方 2026-08-25 批註放行（本卡 timeline 之「T3 規劃閘門：需求方批註放行」留言），並一併裁定 writer_nonconformant 保留為完整一類。核心痛點三問（更新版）見 issuecomment-5405240624。規劃期共十一輪，卡面 amend 五次（847701be／f879ae07／090d1d7b／a2c31042／f754033d），驗收 25 條、驗證 13 條。研究期實測（全部走 wf_cli.project.list_items 正規路徑，母體 193 張、取樣時刻 2026-08-25）：事後掃描已有三個而非 canonical §5.1.2 說的一個，其中 state_face_drift 生產碼 0 呼叫端；歸因需五類（rule_changed 14／writer_nonconformant 16／tool_cannot_read 34／undecidable 41／channel_bypassed 0）；規則變更約每 3–4 天一次且殘餘只累積不清除（2026-08-11 的殘餘沉默 14 天）；⭐ 最大發現是 41 張卡 amend 構造上打不到（活卡 24、21 張在 💡需求），已交由射程擴充後的 aiwf#105 承接；另查出孤兒欄位 分支／worktree（41 張有值但 FIELD_SPECS 未宣告故無人讀）。⚠️ 已知未解：76% 不判定的修法無承接卡（aiwf#54 不涵蓋 Log 行內容）；版本缺口（無 version／無 --version）僅記錄未開卡。⚠️ 開工前須確認與 aiwf#137 在資源上不相交（實測交集為空，可真平行）。基準 origin/main = d4ba7ce5。。
- 2026-08-25T12:52:53+08:00 amend by wf-cli（op fcb8ea9a）→ 驗收條件：原值「[ ] doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復。⚠️ 分層依既有形狀：判定放 doctor.py（純函式、不碰 gh），取卡放 doctor_cmd.py（既有 list_items／resolve_project／find_item_by_card_id，實測 :20／:169-170／:221-222）。；[ ] ⭐ **報告須逐張歸因，值域恰為五類**（⛔ 三類不夠，實測逼出後兩類）：`tool_cannot_read`（解析失敗 ⇒ 修工具）／`undecidable`（建立時刻不可得 ⇒ ⛔ 不猜）／`rule_changed`（卡早於規則 ⇒ 依 disposition 處置）／`writer_nonconformant`（⭐ 卡**晚於**規則卻仍不合規、且經正規通道建立 ⇒ **查寫入端**）／`channel_bypassed`（欄位被手搬、無對應事件 ⇒ 補跑動詞）。；[ ] ⭐ **判準順序不可換**：tool_cannot_read → undecidable → rule_changed → writer_nonconformant → channel_bypassed。⇒ 理由：前兩者是**我們自己的侷限**，⛔ 不得讓它們變成對卡或對人的指控。實測支持：41 張不合規中 34 張屬 tool_cannot_read（issuecomment-5404753163）。；[ ] ⭐ **報告須先分可達性、再談合規性**：新增 `reachability = reachable | unreachable` 這一軸，且它**排在五類歸因之前**。`unreachable` ＝ 唯一的寫入通道（wfcli）在構造上碰不到這張卡 ⇒ 它的任何其他不合規項**都修不了**，⛔ 把它們和「缺核心痛點」列在同一份待辦裡會讓人以為那是能動手的。⚠️ 判準以碼為準（`card.split_at_log` 拋錯／卡面標頭兩行命中數 ≠ 1／無 `## Log` 段落），⛔ 不是啟發式。實測基線：193 張中 **41 張 unreachable（活卡 24，其中 21 張在 💡需求）**，實測拒收原文見 aiwf#138 issuecomment-5404979025。；[ ] ⭐ **可證偽預測須寫進交付**：本卡上線時 `unreachable = 41`（活卡 24）；`aiwf#105`（其射程已於 2026-08-25 擴充涵蓋這 41 張）落地後**應為 0**，否則兩者之一有缺陷。⛔ 不得只報一個數字而不說它應該往哪走。⚠️ 交付須同時記錄取樣時刻與當時 aiwf#105 的狀態。；[ ] ⭐ **每個 rule_epoch 必須帶宣告過的 disposition，⛔ 不能只有時刻**：`migrate`（殘餘應清掉 ⇒ 報告逐張列出）或 `accept_as_legacy`（需求方已裁定不追溯 ⇒ 報告**只給一行摘要數字**，⛔ 不逐張列）。⚠️ 依據：實測規則變更約**每 3–4 天一次**（最近 20 天 6 次），且殘餘**只累積不清除**——26a0149／6325ae2（2026-08-11）的殘餘至今 14 天原封不動（107 張缺標記、活卡 38 張）。⇒ 沒有 disposition，rule_changed 桶會變成下一個 190，與本卡要解的問題同形。；[ ] ⭐ **rule_epoch 的值須釘「檢查所依據的那個構件」落地的完整 ISO-8601 時刻**，⛔ 不是日期、也⛔ 不是「大家覺得規則何時開始」的那個 commit。實測教訓：wf-routing 的規則卡是 26a0149（13:01:38），但標記字面由 6325ae2 引入（18:29:56），晚 5.5 小時；用日期粒度會把 21 張誤判，用正確時刻是 16 張。；[ ] ⭐ 卡的「存在時刻」取值優先序：(1) 卡面 Log 的 `open by` 事件時戳；(2) Issue 的 createdAt；(3) 都沒有 → undecidable。⚠️ 條文須釘死 (2) **只能用於比較 2026-08-04 之後的 epoch**——遷移卡的 Issue 建立於 08-04 而工作早於它，用它比更早的規則會誤判成 writer_nonconformant。⚠️ 取 createdAt 須**擴既有 list_items 查詢**，⛔ 不得加第二次抓取（會違反 doctor_cmd.py:167-183 的「同一次抓取」紀律）。實測母體：41 張無 open by 行（21 首筆 handoff／12 完全無時戳事件／8 assign；活卡 25 張）。；[ ] ⭐ 通用機制的做法是**把三個既有掃描已共用的形狀抽出來，並讓它們成為第一批實作**，⛔ 不是再蓋第四個單一形態。三個是：legacy_authority_notes（doctor.py:1255）、brief_drift（:1298）、**state_face_drift（:1574——生產碼 0 呼叫端，接線屬 aiwf#65 明列而從未開過的「後續卡」）**。共用形狀含：純函式 audit_X(card_bodies)→XReport、status scanned／not_scanned（⛔ 未掃描不得讀成乾淨）、scanned_cards 記母體數、findings 與 routine_gaps 分開。；[ ] ⭐ 抽取時**共用信封、⛔ 不共用 finding 型別**：三者攜帶資訊不同（timestamp／op_id／field_name vs reason vs verdict／expected／actual／rule），併型別會損失資訊。三者**都已有 card_id** ⇒ Protocol 約束即可。⚠️ 實測 dataclasses.asdict 對 list[Protocol] 正常遞迴、json.dumps 成功 ⇒ --json 輸出面無風險。；[ ] ⭐ **改寫既有 render_state_face_drift（doctor.py:1625）使其依 cause 分流處置文案**：現行每筆 drift 無條件輸出「補跑對應的 wfcli 動詞…勿手動搬看板」，⇒ 對 rule_changed 的卡那是**錯誤的指控**。保留既有的「一致／漂移／不判定＋佔比」統計行與「偵測不等於強制」段（後者指名強制面承接者是 aiwf#48）。⚠️ 交付須附變更前後逐字對照，⛔ 不得混在新功能裡帶過。回歸基線：`uv run pytest tests/test_doctor.py -k drift -q` ⇒ **31 passed**（d4ba7ce5；⛔ `-k state_face` 選到 0 支，別用）。；[ ] ⛔ **不得把 run_doctor 的 card_bodies 參數與掃描用的卡面合成一個**——doctor.py:1822-1827 逐字裁定：那個參數餵給 evaluate_cleanup_guard，順手填上會**沉默地改變 --cleanup-preview 的判定**。⭐ 正解是「同一次 list_items、多個獨立消費者各帶自己的參數」。；[ ] ⭐ 基線清冊改用本卡自量的數字並附方法與取樣時刻：母體 193 張、不合規 41 張（21%），歸因為 tool_cannot_read 34／card_deficient 7，而 7 張中僅 **2 張非終態**。⛔ **不得引用 aiwf#136 的「161 張中 7 張」**。⚠️ 清冊須逐張帶歸因欄。；[ ] ⚠️ 接線 state_face_drift 的兩個已知常態須逐字寫進交付：(1) **76% 不判定**（62 張未結案中 47 張，主因 handoff_status_not_in_log 45），其修法「handoff Log 行自帶 stage/status」**今天沒有承接卡**（aiwf#54 的驗收是「第一個遠端寫入帶載荷」，⛔ 不涵蓋 Log 行內容）；(2) **14 筆 open_initial 屬 rule_changed 而非 drift**（成因 1531666，2026-08-21；實測 14/14 開卡日早於該日）。；[ ] ⚠️ 條文須指名一個本卡**解不掉**的限制：writer_nonconformant 指得出來但**追不下去**——狀態面不記錄「這筆是哪個版本的工具寫的」。實測 16 張卡在規則生效後仍缺 wf-routing 標記（開卡時刻橫跨 2026-08-12T00:11→08-15T10:07，抽驗 5 張全為「有路由行、無標記、Log 完整」），⛔ 根因未查出且本卡不查。；[ ] ⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。；[ ] ⚠️ 與既有 legacy_authority_notes 的關係由「合流或劃界」改為**抽取**。⚠️ 且該掃描的既有立場逐字是「報的是**留痕強度不足，不是授權無效**」⇒ 其 findings ⛔ **不進待辦集合**，報告須明示這一點（實測 11 張，本卡曾一度把它們誤算進待辦）。；[ ] ⚠️ 旗標命名：簡介漂移目前掛在 --legacy-authority-notes 底下（doctor_cmd.py:121／:167 同一個 if），而該旗標 help（:54-55）⛔ 一個字沒提簡介漂移。改名為 --conformance（實查 CI／腳本／文件 0 命中，⛔ 不弄壞自動化），保留舊名為 deprecated alias。交付須明說連帶修正是不是刻意的。；[ ] ⛔ 授權邊界：執行中若發現**必須修改**本卡未宣告的檔（如 validation.py／card.py），依 canonical §3.2「停 → 寫阻塞發現 → 由需求方裁決」，⛔ 執行者不得自行擴權。；[ ] ⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時把 service_goal_still_served 納入檢查面；未合併時明列為**已知缺口**。⭐ 兩張寫入集不相交、可真平行；⛔ 先前「S7a 先」已作廢。；[ ] 回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。；[ ] ⚠️ 交付時須附「PM 單方面決定清冊」。；[ ] ⭐ **欄位層掃描（與 per-card findings 正交）**：比對看板實際帶過值的欄位集合 vs `project.FIELD_SPECS`，列出 (i) **有值但未宣告的孤兒欄位**、(ii) 宣告了但零張卡有值的欄位。⚠️ 這不是某一張卡的問題，是**狀態面本身的形狀問題** ⇒ 報告須有獨立區段，⛔ 不得把 N 張卡各報一筆。實測基線（2026-08-25）：孤兒欄位 **1 個**＝`分支／worktree`（全形斜線；`FIELD_SPECS` 宣告的是 `分支worktree`），41 張卡有值、8 張兩欄都有值、33 張只有舊欄（其中 30 張是佔位 `—`）⇒ **真正讀不到的登記 3 張、非終態 0 張**；(ii) 實測 **0 個**。⚠️ 成因是遷移用 Ledger 欄名建欄、CLI 同日用自己的常數建了第二個（`registry.py:261` 逐字有 `分支／worktree` 欄名；`9ef3154` 的 FIELD_SPECS 從一開始就是 `分支worktree`），而 `ensure_fields` **冪等但只增不減** ⇒ ⭐ 每次欄位命名分歧都會留一個孤兒，而沒有任何東西會說。；[ ] ⚠️ 稽核取值一律走 `wf_cli.project.list_items` 正規路徑，⛔ **不得用 `gh project item-list`**——`project.py:377-378` 逐字記載後者「對中文欄位名稱的 JSON key 有編碼錯誤」。⚠️ 本卡研究期 PM 十餘支探針全踩此坑（結論重驗後不變，但方法錯）。⭐ 且判定一律直接呼叫 `wf_cli` 的純函式（`audit_state_face_drift`／`validate_open_fields`／`resources.try_parse_block`／`card.split_at_log`），⇒ 盤點結果與守衛判定**同源**。；[ ] ⭐ **`writer_nonconformant` 的 finding 必須自帶可追溯的兩個時刻**（需求方 2026-08-25 裁定：本類保留為完整一類）：(1) 該規則的 `rule_epoch`、(2) 該卡的建立時刻。⇒ 接手的人可直接做 git 考古比對寫入端的 commit 時序，⛔ 不用重新推導一次。⚠️ 依據：狀態面**沒有任何工具版本可查**——`cli/pyproject.toml` 的 `version` 自 2026-08-04 起凍在 `0.1.0` 未曾 bump，`wfcli` 也**沒有 `--version`**，Log 行只寫 `by wf-cli` ⇒ 「這筆是哪個版本寫的」構造上無解。⭐ 但**追得下去**：本卡研究期即以 commit 時序追出那 16 張的形狀（開卡於 2026-08-12→08-15、有路由行、無標記、Log 完整，見 issuecomment-5404887674）。⚠️ 該類的真正風險是 **epoch 精確度**（實測挑錯 commit 會讓 16 變成 21）⇒ 由既有的「epoch 須釘構件落地的完整 ISO-8601 時刻」那條驗收承接。⚠️ 本卡**不解決**版本缺口本身（無 version／無 --version），僅在條文中指名。」→ 新值「doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復。⚠️ 分層依既有形狀：判定放 doctor.py（純函式、不碰 gh），取卡放 doctor_cmd.py（既有 list_items／resolve_project／find_item_by_card_id，實測 :20／:169-170／:221-222）。；⭐ **報告須逐張歸因，值域恰為五類**（⛔ 三類不夠，實測逼出後兩類）：`tool_cannot_read`（解析失敗 ⇒ 修工具）／`undecidable`（建立時刻不可得 ⇒ ⛔ 不猜）／`rule_changed`（卡早於規則 ⇒ 依 disposition 處置）／`writer_nonconformant`（⭐ 卡**晚於**規則卻仍不合規、且經正規通道建立 ⇒ **查寫入端**）／`channel_bypassed`（欄位被手搬、無對應事件 ⇒ 補跑動詞）。；⭐ **判準順序不可換**：tool_cannot_read → undecidable → rule_changed → writer_nonconformant → channel_bypassed。⇒ 理由：前兩者是**我們自己的侷限**，⛔ 不得讓它們變成對卡或對人的指控。實測支持：41 張不合規中 34 張屬 tool_cannot_read（issuecomment-5404753163）。；⭐ **報告須先分可達性、再談合規性；而可達性是「逐動詞」的，⛔ 不是卡的二值屬性**（⛔ 更正本卡 issuecomment-5404979025 的二值設計，依 aiwf#105 issuecomment-5405392222 的實跑）。⇒ 欄位形狀為 `reachable_for: list[verb_or_flag]` 或等價映射，報告須說**哪個動詞打不到**。⚠️ 理由是可操作性：「assign 打不到」的處置（先修卡才能派工）與「--resources 打不到」的處置（該欄位暫時改不了）完全不同。實測分佈（2026-08-25，母體 193 張中 41 張至少一項不可達）：`assign` ⛔（assign_cmd.py:179 對目標卡走嚴格 parse_block）；`amend` 的 --spec-baseline／--initiative／--resources／--core-pain／--acceptance／--verification ⛔；**`amend --brief` ✅ 40/41**（28 張缺標頭 rc=0、12 張連 ## Log 都沒有也 rc=0，僅排版損壞 1 張被拒）；`handoff`／`review`／`checkpoint`／`deploy-declare`／`deploy-state` ✅（只做 append_log_line，而它逐字「沒有該區段就新增一個到 body 尾端」）。⭐ **真正的阻塞是 `assign`**：那 41 張裡 21 張活卡（💡需求）今天無法被認領。⚠️ 該項為讀碼結論，⛔ 未實跑（assign 無 --dry-run）⇒ 驗證須以拋棄式卡進行，⛔ 不對真實卡試寫。⛔ **並更正**：先前寫「這會擋住 aiwf#130 的 S5」為**錯誤**——S5 走 `amend --brief`，實測 40/41 通過，未被擋。；⭐ **可證偽預測須寫進交付**：本卡上線時 `unreachable = 41`（活卡 24）；`aiwf#105`（其射程已於 2026-08-25 擴充涵蓋這 41 張）落地後**應為 0**，否則兩者之一有缺陷。⛔ 不得只報一個數字而不說它應該往哪走。⚠️ 交付須同時記錄取樣時刻與當時 aiwf#105 的狀態。；⭐ **每個 rule_epoch 必須帶宣告過的 disposition，⛔ 不能只有時刻**：`migrate`（殘餘應清掉 ⇒ 報告逐張列出）或 `accept_as_legacy`（需求方已裁定不追溯 ⇒ 報告**只給一行摘要數字**，⛔ 不逐張列）。⚠️ 依據：實測規則變更約**每 3–4 天一次**（最近 20 天 6 次），且殘餘**只累積不清除**——26a0149／6325ae2（2026-08-11）的殘餘至今 14 天原封不動（107 張缺標記、活卡 38 張）。⇒ 沒有 disposition，rule_changed 桶會變成下一個 190，與本卡要解的問題同形。；⭐ **rule_epoch 的值須釘「檢查所依據的那個構件」落地的完整 ISO-8601 時刻**，⛔ 不是日期、也⛔ 不是「大家覺得規則何時開始」的那個 commit。實測教訓：wf-routing 的規則卡是 26a0149（13:01:38），但標記字面由 6325ae2 引入（18:29:56），晚 5.5 小時；用日期粒度會把 21 張誤判，用正確時刻是 16 張。；⭐ 卡的「存在時刻」取值優先序：(1) 卡面 Log 的 `open by` 事件時戳；(2) Issue 的 createdAt；(3) 都沒有 → undecidable。⚠️ 條文須釘死 (2) **只能用於比較 2026-08-04 之後的 epoch**——遷移卡的 Issue 建立於 08-04 而工作早於它，用它比更早的規則會誤判成 writer_nonconformant。⚠️ 取 createdAt 須**擴既有 list_items 查詢**，⛔ 不得加第二次抓取（會違反 doctor_cmd.py:167-183 的「同一次抓取」紀律）。實測母體：41 張無 open by 行（21 首筆 handoff／12 完全無時戳事件／8 assign；活卡 25 張）。；⭐ 通用機制的做法是**把三個既有掃描已共用的形狀抽出來，並讓它們成為第一批實作**，⛔ 不是再蓋第四個單一形態。三個是：legacy_authority_notes（doctor.py:1255）、brief_drift（:1298）、**state_face_drift（:1574——生產碼 0 呼叫端，接線屬 aiwf#65 明列而從未開過的「後續卡」）**。共用形狀含：純函式 audit_X(card_bodies)→XReport、status scanned／not_scanned（⛔ 未掃描不得讀成乾淨）、scanned_cards 記母體數、findings 與 routine_gaps 分開。；⭐ 抽取時**共用信封、⛔ 不共用 finding 型別**：三者攜帶資訊不同（timestamp／op_id／field_name vs reason vs verdict／expected／actual／rule），併型別會損失資訊。三者**都已有 card_id** ⇒ Protocol 約束即可。⚠️ 實測 dataclasses.asdict 對 list[Protocol] 正常遞迴、json.dumps 成功 ⇒ --json 輸出面無風險。；⭐ **改寫既有 render_state_face_drift（doctor.py:1625）使其依 cause 分流處置文案**：現行每筆 drift 無條件輸出「補跑對應的 wfcli 動詞…勿手動搬看板」，⇒ 對 rule_changed 的卡那是**錯誤的指控**。保留既有的「一致／漂移／不判定＋佔比」統計行與「偵測不等於強制」段（後者指名強制面承接者是 aiwf#48）。⚠️ 交付須附變更前後逐字對照，⛔ 不得混在新功能裡帶過。回歸基線：`uv run pytest tests/test_doctor.py -k drift -q` ⇒ **31 passed**（d4ba7ce5；⛔ `-k state_face` 選到 0 支，別用）。；⛔ **不得把 run_doctor 的 card_bodies 參數與掃描用的卡面合成一個**——doctor.py:1822-1827 逐字裁定：那個參數餵給 evaluate_cleanup_guard，順手填上會**沉默地改變 --cleanup-preview 的判定**。⭐ 正解是「同一次 list_items、多個獨立消費者各帶自己的參數」。；⭐ 基線清冊改用本卡自量的數字並附方法與取樣時刻：母體 193 張、不合規 41 張（21%），歸因為 tool_cannot_read 34／card_deficient 7，而 7 張中僅 **2 張非終態**。⛔ **不得引用 aiwf#136 的「161 張中 7 張」**。⚠️ 清冊須逐張帶歸因欄。；⚠️ 接線 state_face_drift 的兩個已知常態須逐字寫進交付：(1) **76% 不判定**（62 張未結案中 47 張，主因 handoff_status_not_in_log 45），其修法「handoff Log 行自帶 stage/status」**今天沒有承接卡**（aiwf#54 的驗收是「第一個遠端寫入帶載荷」，⛔ 不涵蓋 Log 行內容）；(2) **14 筆 open_initial 屬 rule_changed 而非 drift**（成因 1531666，2026-08-21；實測 14/14 開卡日早於該日）。；⚠️ 條文須指名一個本卡**解不掉**的限制：writer_nonconformant 指得出來但**追不下去**——狀態面不記錄「這筆是哪個版本的工具寫的」。實測 16 張卡在規則生效後仍缺 wf-routing 標記（開卡時刻橫跨 2026-08-12T00:11→08-15T10:07，抽驗 5 張全為「有路由行、無標記、Log 完整」），⛔ 根因未查出且本卡不查。；⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。；⚠️ 與既有 legacy_authority_notes 的關係由「合流或劃界」改為**抽取**。⚠️ 且該掃描的既有立場逐字是「報的是**留痕強度不足，不是授權無效**」⇒ 其 findings ⛔ **不進待辦集合**，報告須明示這一點（實測 11 張，本卡曾一度把它們誤算進待辦）。；⚠️ 旗標命名：簡介漂移目前掛在 --legacy-authority-notes 底下（doctor_cmd.py:121／:167 同一個 if），而該旗標 help（:54-55）⛔ 一個字沒提簡介漂移。改名為 --conformance（實查 CI／腳本／文件 0 命中，⛔ 不弄壞自動化），保留舊名為 deprecated alias。交付須明說連帶修正是不是刻意的。；⛔ 授權邊界：執行中若發現**必須修改**本卡未宣告的檔（如 validation.py／card.py），依 canonical §3.2「停 → 寫阻塞發現 → 由需求方裁決」，⛔ 執行者不得自行擴權。；⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時把 service_goal_still_served 納入檢查面；未合併時明列為**已知缺口**。⭐ 兩張寫入集不相交、可真平行；⛔ 先前「S7a 先」已作廢。；回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。；⚠️ 交付時須附「PM 單方面決定清冊」。；⭐ **欄位層掃描（與 per-card findings 正交）**：比對看板實際帶過值的欄位集合 vs `project.FIELD_SPECS`，列出 (i) **有值但未宣告的孤兒欄位**、(ii) 宣告了但零張卡有值的欄位。⚠️ 這不是某一張卡的問題，是**狀態面本身的形狀問題** ⇒ 報告須有獨立區段，⛔ 不得把 N 張卡各報一筆。實測基線（2026-08-25）：孤兒欄位 **1 個**＝`分支／worktree`（全形斜線；`FIELD_SPECS` 宣告的是 `分支worktree`），41 張卡有值、8 張兩欄都有值、33 張只有舊欄（其中 30 張是佔位 `—`）⇒ **真正讀不到的登記 3 張、非終態 0 張**；(ii) 實測 **0 個**。⚠️ 成因是遷移用 Ledger 欄名建欄、CLI 同日用自己的常數建了第二個（`registry.py:261` 逐字有 `分支／worktree` 欄名；`9ef3154` 的 FIELD_SPECS 從一開始就是 `分支worktree`），而 `ensure_fields` **冪等但只增不減** ⇒ ⭐ 每次欄位命名分歧都會留一個孤兒，而沒有任何東西會說。；⚠️ 稽核取值一律走 `wf_cli.project.list_items` 正規路徑，⛔ **不得用 `gh project item-list`**——`project.py:377-378` 逐字記載後者「對中文欄位名稱的 JSON key 有編碼錯誤」。⚠️ 本卡研究期 PM 十餘支探針全踩此坑（結論重驗後不變，但方法錯）。⭐ 且判定一律直接呼叫 `wf_cli` 的純函式（`audit_state_face_drift`／`validate_open_fields`／`resources.try_parse_block`／`card.split_at_log`），⇒ 盤點結果與守衛判定**同源**。；⭐ **`writer_nonconformant` 的 finding 必須自帶可追溯的兩個時刻**（需求方 2026-08-25 裁定：本類保留為完整一類）：(1) 該規則的 `rule_epoch`、(2) 該卡的建立時刻。⇒ 接手的人可直接做 git 考古比對寫入端的 commit 時序，⛔ 不用重新推導一次。⚠️ 依據：狀態面**沒有任何工具版本可查**——`cli/pyproject.toml` 的 `version` 自 2026-08-04 起凍在 `0.1.0` 未曾 bump，`wfcli` 也**沒有 `--version`**，Log 行只寫 `by wf-cli` ⇒ 「這筆是哪個版本寫的」構造上無解。⭐ 但**追得下去**：本卡研究期即以 commit 時序追出那 16 張的形狀（開卡於 2026-08-12→08-15、有路由行、無標記、Log 完整，見 issuecomment-5404887674）。⚠️ 該類的真正風險是 **epoch 精確度**（實測挑錯 commit 會讓 16 變成 21）⇒ 由既有的「epoch 須釘構件落地的完整 ISO-8601 時刻」那條驗收承接。⚠️ 本卡**不解決**版本缺口本身（無 version／無 --version），僅在條文中指名。」；理由 ⛔ 更正本卡 issuecomment-5404979025 的兩個錯誤陳述，依 aiwf#105 研究第二輪（issuecomment-5405392222）的逐動詞讀碼與三組 amend --dry-run 實跑：(1)「24 張活卡的寫入通道打不到」過重——擋人的是各個 amend_* 純函式各自的前提而非全域閘門，amend --brief 實測打得到 40/41（含 12 張連 ## Log 都沒有的），handoff/review/checkpoint/deploy-* 亦皆可達；(2)「會擋住 aiwf#130 的 S5」完全錯——S5 正是走 amend --brief。⇒ reachability 由二值改為逐動詞映射，理由是處置不同（assign 打不到＝開不了工，--resources 打不到＝該欄位改不了）。並載明真正的阻塞是 assign（21 張活卡無法被認領），且該項為讀碼結論、驗證須以拋棄式卡進行。。
- 2026-08-25T16:13:43+08:00 amend by wf-cli（op 761c812e）→ 驗收條件：原值「[ ] doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復。⚠️ 分層依既有形狀：判定放 doctor.py（純函式、不碰 gh），取卡放 doctor_cmd.py（既有 list_items／resolve_project／find_item_by_card_id，實測 :20／:169-170／:221-222）。；[ ] ⭐ **報告須逐張歸因，值域恰為五類**（⛔ 三類不夠，實測逼出後兩類）：`tool_cannot_read`（解析失敗 ⇒ 修工具）／`undecidable`（建立時刻不可得 ⇒ ⛔ 不猜）／`rule_changed`（卡早於規則 ⇒ 依 disposition 處置）／`writer_nonconformant`（⭐ 卡**晚於**規則卻仍不合規、且經正規通道建立 ⇒ **查寫入端**）／`channel_bypassed`（欄位被手搬、無對應事件 ⇒ 補跑動詞）。；[ ] ⭐ **判準順序不可換**：tool_cannot_read → undecidable → rule_changed → writer_nonconformant → channel_bypassed。⇒ 理由：前兩者是**我們自己的侷限**，⛔ 不得讓它們變成對卡或對人的指控。實測支持：41 張不合規中 34 張屬 tool_cannot_read（issuecomment-5404753163）。；[ ] ⭐ **報告須先分可達性、再談合規性；而可達性是「逐動詞」的，⛔ 不是卡的二值屬性**（⛔ 更正本卡 issuecomment-5404979025 的二值設計，依 aiwf#105 issuecomment-5405392222 的實跑）。⇒ 欄位形狀為 `reachable_for: list[verb_or_flag]` 或等價映射，報告須說**哪個動詞打不到**。⚠️ 理由是可操作性：「assign 打不到」的處置（先修卡才能派工）與「--resources 打不到」的處置（該欄位暫時改不了）完全不同。實測分佈（2026-08-25，母體 193 張中 41 張至少一項不可達）：`assign` ⛔（assign_cmd.py:179 對目標卡走嚴格 parse_block）；`amend` 的 --spec-baseline／--initiative／--resources／--core-pain／--acceptance／--verification ⛔；**`amend --brief` ✅ 40/41**（28 張缺標頭 rc=0、12 張連 ## Log 都沒有也 rc=0，僅排版損壞 1 張被拒）；`handoff`／`review`／`checkpoint`／`deploy-declare`／`deploy-state` ✅（只做 append_log_line，而它逐字「沒有該區段就新增一個到 body 尾端」）。⭐ **真正的阻塞是 `assign`**：那 41 張裡 21 張活卡（💡需求）今天無法被認領。⚠️ 該項為讀碼結論，⛔ 未實跑（assign 無 --dry-run）⇒ 驗證須以拋棄式卡進行，⛔ 不對真實卡試寫。⛔ **並更正**：先前寫「這會擋住 aiwf#130 的 S5」為**錯誤**——S5 走 `amend --brief`，實測 40/41 通過，未被擋。；[ ] ⭐ **可證偽預測須寫進交付**：本卡上線時 `unreachable = 41`（活卡 24）；`aiwf#105`（其射程已於 2026-08-25 擴充涵蓋這 41 張）落地後**應為 0**，否則兩者之一有缺陷。⛔ 不得只報一個數字而不說它應該往哪走。⚠️ 交付須同時記錄取樣時刻與當時 aiwf#105 的狀態。；[ ] ⭐ **每個 rule_epoch 必須帶宣告過的 disposition，⛔ 不能只有時刻**：`migrate`（殘餘應清掉 ⇒ 報告逐張列出）或 `accept_as_legacy`（需求方已裁定不追溯 ⇒ 報告**只給一行摘要數字**，⛔ 不逐張列）。⚠️ 依據：實測規則變更約**每 3–4 天一次**（最近 20 天 6 次），且殘餘**只累積不清除**——26a0149／6325ae2（2026-08-11）的殘餘至今 14 天原封不動（107 張缺標記、活卡 38 張）。⇒ 沒有 disposition，rule_changed 桶會變成下一個 190，與本卡要解的問題同形。；[ ] ⭐ **rule_epoch 的值須釘「檢查所依據的那個構件」落地的完整 ISO-8601 時刻**，⛔ 不是日期、也⛔ 不是「大家覺得規則何時開始」的那個 commit。實測教訓：wf-routing 的規則卡是 26a0149（13:01:38），但標記字面由 6325ae2 引入（18:29:56），晚 5.5 小時；用日期粒度會把 21 張誤判，用正確時刻是 16 張。；[ ] ⭐ 卡的「存在時刻」取值優先序：(1) 卡面 Log 的 `open by` 事件時戳；(2) Issue 的 createdAt；(3) 都沒有 → undecidable。⚠️ 條文須釘死 (2) **只能用於比較 2026-08-04 之後的 epoch**——遷移卡的 Issue 建立於 08-04 而工作早於它，用它比更早的規則會誤判成 writer_nonconformant。⚠️ 取 createdAt 須**擴既有 list_items 查詢**，⛔ 不得加第二次抓取（會違反 doctor_cmd.py:167-183 的「同一次抓取」紀律）。實測母體：41 張無 open by 行（21 首筆 handoff／12 完全無時戳事件／8 assign；活卡 25 張）。；[ ] ⭐ 通用機制的做法是**把三個既有掃描已共用的形狀抽出來，並讓它們成為第一批實作**，⛔ 不是再蓋第四個單一形態。三個是：legacy_authority_notes（doctor.py:1255）、brief_drift（:1298）、**state_face_drift（:1574——生產碼 0 呼叫端，接線屬 aiwf#65 明列而從未開過的「後續卡」）**。共用形狀含：純函式 audit_X(card_bodies)→XReport、status scanned／not_scanned（⛔ 未掃描不得讀成乾淨）、scanned_cards 記母體數、findings 與 routine_gaps 分開。；[ ] ⭐ 抽取時**共用信封、⛔ 不共用 finding 型別**：三者攜帶資訊不同（timestamp／op_id／field_name vs reason vs verdict／expected／actual／rule），併型別會損失資訊。三者**都已有 card_id** ⇒ Protocol 約束即可。⚠️ 實測 dataclasses.asdict 對 list[Protocol] 正常遞迴、json.dumps 成功 ⇒ --json 輸出面無風險。；[ ] ⭐ **改寫既有 render_state_face_drift（doctor.py:1625）使其依 cause 分流處置文案**：現行每筆 drift 無條件輸出「補跑對應的 wfcli 動詞…勿手動搬看板」，⇒ 對 rule_changed 的卡那是**錯誤的指控**。保留既有的「一致／漂移／不判定＋佔比」統計行與「偵測不等於強制」段（後者指名強制面承接者是 aiwf#48）。⚠️ 交付須附變更前後逐字對照，⛔ 不得混在新功能裡帶過。回歸基線：`uv run pytest tests/test_doctor.py -k drift -q` ⇒ **31 passed**（d4ba7ce5；⛔ `-k state_face` 選到 0 支，別用）。；[ ] ⛔ **不得把 run_doctor 的 card_bodies 參數與掃描用的卡面合成一個**——doctor.py:1822-1827 逐字裁定：那個參數餵給 evaluate_cleanup_guard，順手填上會**沉默地改變 --cleanup-preview 的判定**。⭐ 正解是「同一次 list_items、多個獨立消費者各帶自己的參數」。；[ ] ⭐ 基線清冊改用本卡自量的數字並附方法與取樣時刻：母體 193 張、不合規 41 張（21%），歸因為 tool_cannot_read 34／card_deficient 7，而 7 張中僅 **2 張非終態**。⛔ **不得引用 aiwf#136 的「161 張中 7 張」**。⚠️ 清冊須逐張帶歸因欄。；[ ] ⚠️ 接線 state_face_drift 的兩個已知常態須逐字寫進交付：(1) **76% 不判定**（62 張未結案中 47 張，主因 handoff_status_not_in_log 45），其修法「handoff Log 行自帶 stage/status」**今天沒有承接卡**（aiwf#54 的驗收是「第一個遠端寫入帶載荷」，⛔ 不涵蓋 Log 行內容）；(2) **14 筆 open_initial 屬 rule_changed 而非 drift**（成因 1531666，2026-08-21；實測 14/14 開卡日早於該日）。；[ ] ⚠️ 條文須指名一個本卡**解不掉**的限制：writer_nonconformant 指得出來但**追不下去**——狀態面不記錄「這筆是哪個版本的工具寫的」。實測 16 張卡在規則生效後仍缺 wf-routing 標記（開卡時刻橫跨 2026-08-12T00:11→08-15T10:07，抽驗 5 張全為「有路由行、無標記、Log 完整」），⛔ 根因未查出且本卡不查。；[ ] ⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。；[ ] ⚠️ 與既有 legacy_authority_notes 的關係由「合流或劃界」改為**抽取**。⚠️ 且該掃描的既有立場逐字是「報的是**留痕強度不足，不是授權無效**」⇒ 其 findings ⛔ **不進待辦集合**，報告須明示這一點（實測 11 張，本卡曾一度把它們誤算進待辦）。；[ ] ⚠️ 旗標命名：簡介漂移目前掛在 --legacy-authority-notes 底下（doctor_cmd.py:121／:167 同一個 if），而該旗標 help（:54-55）⛔ 一個字沒提簡介漂移。改名為 --conformance（實查 CI／腳本／文件 0 命中，⛔ 不弄壞自動化），保留舊名為 deprecated alias。交付須明說連帶修正是不是刻意的。；[ ] ⛔ 授權邊界：執行中若發現**必須修改**本卡未宣告的檔（如 validation.py／card.py），依 canonical §3.2「停 → 寫阻塞發現 → 由需求方裁決」，⛔ 執行者不得自行擴權。；[ ] ⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時把 service_goal_still_served 納入檢查面；未合併時明列為**已知缺口**。⭐ 兩張寫入集不相交、可真平行；⛔ 先前「S7a 先」已作廢。；[ ] 回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。；[ ] ⚠️ 交付時須附「PM 單方面決定清冊」。；[ ] ⭐ **欄位層掃描（與 per-card findings 正交）**：比對看板實際帶過值的欄位集合 vs `project.FIELD_SPECS`，列出 (i) **有值但未宣告的孤兒欄位**、(ii) 宣告了但零張卡有值的欄位。⚠️ 這不是某一張卡的問題，是**狀態面本身的形狀問題** ⇒ 報告須有獨立區段，⛔ 不得把 N 張卡各報一筆。實測基線（2026-08-25）：孤兒欄位 **1 個**＝`分支／worktree`（全形斜線；`FIELD_SPECS` 宣告的是 `分支worktree`），41 張卡有值、8 張兩欄都有值、33 張只有舊欄（其中 30 張是佔位 `—`）⇒ **真正讀不到的登記 3 張、非終態 0 張**；(ii) 實測 **0 個**。⚠️ 成因是遷移用 Ledger 欄名建欄、CLI 同日用自己的常數建了第二個（`registry.py:261` 逐字有 `分支／worktree` 欄名；`9ef3154` 的 FIELD_SPECS 從一開始就是 `分支worktree`），而 `ensure_fields` **冪等但只增不減** ⇒ ⭐ 每次欄位命名分歧都會留一個孤兒，而沒有任何東西會說。；[ ] ⚠️ 稽核取值一律走 `wf_cli.project.list_items` 正規路徑，⛔ **不得用 `gh project item-list`**——`project.py:377-378` 逐字記載後者「對中文欄位名稱的 JSON key 有編碼錯誤」。⚠️ 本卡研究期 PM 十餘支探針全踩此坑（結論重驗後不變，但方法錯）。⭐ 且判定一律直接呼叫 `wf_cli` 的純函式（`audit_state_face_drift`／`validate_open_fields`／`resources.try_parse_block`／`card.split_at_log`），⇒ 盤點結果與守衛判定**同源**。；[ ] ⭐ **`writer_nonconformant` 的 finding 必須自帶可追溯的兩個時刻**（需求方 2026-08-25 裁定：本類保留為完整一類）：(1) 該規則的 `rule_epoch`、(2) 該卡的建立時刻。⇒ 接手的人可直接做 git 考古比對寫入端的 commit 時序，⛔ 不用重新推導一次。⚠️ 依據：狀態面**沒有任何工具版本可查**——`cli/pyproject.toml` 的 `version` 自 2026-08-04 起凍在 `0.1.0` 未曾 bump，`wfcli` 也**沒有 `--version`**，Log 行只寫 `by wf-cli` ⇒ 「這筆是哪個版本寫的」構造上無解。⭐ 但**追得下去**：本卡研究期即以 commit 時序追出那 16 張的形狀（開卡於 2026-08-12→08-15、有路由行、無標記、Log 完整，見 issuecomment-5404887674）。⚠️ 該類的真正風險是 **epoch 精確度**（實測挑錯 commit 會讓 16 變成 21）⇒ 由既有的「epoch 須釘構件落地的完整 ISO-8601 時刻」那條驗收承接。⚠️ 本卡**不解決**版本缺口本身（無 version／無 --version），僅在條文中指名。」→ 新值「⚠️ A1–A25 逐條壓縮（一對一，⛔ 無合併無丟棄）；原文封存於 https://github.com/ruan6047/ai-workflow/issues/138#issuecomment-5407338420；A1 doctor 新增**通用**事後重驗；⛔ 不自動修復。判定放 doctor.py（純函式）、取卡放 doctor_cmd.py；A2 ⭐ 報告須**逐張歸因**，值域恰五類：tool_cannot_read／undecidable／rule_changed／writer_nonconformant／channel_bypassed。⛔ 只計數＝錯誤指控（實測 41 中 34 屬 (c)）；A3 ⭐ 判準順序不可換：tool_cannot_read→undecidable→rule_changed→writer_nonconformant→channel_bypassed（前兩者是我們的侷限，⛔ 不得變成指控）；A4 ⭐ 每個 rule_epoch 須帶 disposition（migrate／accept_as_legacy）；⛔ 否則 rule_changed 會變成下一個 190；A5 ⭐ rule_epoch 釘**構件落地的完整 ISO-8601 時刻**，⛔ 非日期（實測日期粒度會把 16 誤判成 21）；A6 ⭐ 卡的存在時刻取值序：Log 的 open 事件 → Issue createdAt → undecidable。⚠️ createdAt 只能比 2026-08-04 之後的 epoch；須擴既有 list_items 查詢，⛔ 不加第二次抓取；A7 ⭐ 抽取三個既有掃描的共用形狀為第一批實作：legacy_authority_notes／brief_drift／**state_face_drift（生產碼 0 呼叫端）**；⛔ 不蓋第四個單一形態；A8 ⭐ 共用信封、⛔ 不共用 finding 型別（三者資訊不同，併型別＝損失）；三者皆有 card_id ⇒ Protocol 即可；A9 ⭐ 改寫 render_state_face_drift 使處置文案**依 cause 分流**（現行無條件輸出「補跑動詞…勿手動搬看板」＝對 rule_changed 是錯誤指控）；保留統計行與「偵測不等於強制」段。回歸基線 `-k drift` 31 passed；A10 ⛔ 不得把 run_doctor 的 card_bodies 與掃描用卡面合成一個參數（doctor.py 逐字：會沉默改變 --cleanup-preview）；A11 ⭐ 基線清冊用本卡自量數字（193 母體／41 不合規／34 tool_cannot_read／7 card_deficient，其中僅 2 張非終態）；⛔ 不引用 aiwf#136 的 161/7；A12 ⚠️ 接線 state_face_drift 的兩個已知常態須寫進交付：76% 不判定（無承接卡）、14 筆 open_initial 屬 rule_changed 非 drift；A13 ⭐ **可達性是逐動詞的**，⛔ 非卡的二值屬性：assign ⛔／amend 五旗標 ⛔／`amend --brief` ✅ 40/41／handoff·review·checkpoint·deploy-* ✅。⭐ 真正的阻塞是 assign。⛔ 更正：先前寫「會擋住 S5」是錯的；A14 ⭐ 可證偽預測：上線時 unreachable=41；aiwf#105 落地後應為 0；A15 ⭐ **欄位層掃描**（與 per-card 正交，獨立區段）：看板實際欄位 vs FIELD_SPECS。實測孤兒欄位 1 個＝`分支／worktree`（41 張有值、無人讀；真正讀不到的登記 3 張、活卡 0）。成因：ensure_fields 冪等但只增不減；A16 ⚠️ 稽核取值一律走 `wf_cli.project.list_items`，⛔ 不用 `gh project item-list`（project.py 逐字：中文欄位 key 編碼錯誤）；判定直接呼叫 wf_cli 純函式使盤點與守衛同源；A17 ⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend／handoff；A18 ⚠️ legacy_authority_notes 由「合流或劃界」改為**抽取**；且其 findings ⛔ **不進待辦**（既有立場：報的是留痕強度不足，不是授權無效）；A19 ⚠️ 旗標改名 `--conformance`（實查 CI／腳本／文件 0 命中），保留舊名為 alias；交付須明說連帶修正是否刻意；A20 ⛔ 授權邊界：發現須改本卡未宣告的檔 ⇒ 停、寫阻塞發現、由需求方裁決（§3.2）；A21 ⚠️ 與 aiwf#137 的介面：S7a 已合併則納入 service_goal_still_served，否則明列為已知缺口。⭐ 兩卡寫入集不相交、可真平行；A22 回歸：cli 既有測試全過（基線數逐字記錄，⛔ 不得只寫「全過」）；A23 ⚠️ 交付須附 PM 單方面決定清冊；A24 ⭐ writer_nonconformant 的 finding 須自帶 rule_epoch 與卡的建立時刻（狀態面無工具版本可查：pyproject 凍在 0.1.0、無 --version）」；理由 ⛔ 立即止血：本卡 body 68,521、amend 11 次、驗收 6,348 ⇒ 每改一次付 12,696，**只剩 4 次餘裕**就會撞上 GitHub body 上限（aiwf#105 今天已撞上並一度不可寫）。驗收改為逐條壓縮（A1–A25 一對一、⛔ 無合併無丟棄），原文封存於 https://github.com/ruan6047/ai-workflow/issues/138#issuecomment-5407338420。⇒ 本次付一次 ~7,700，之後每次僅 ~2,400 ⇒ 可再改 22 次。⭐ 並確立紀律：研究結論一律進 comment，卡面欄位只寫判準。。
- 2026-08-26T01:16:43+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/WF-POSTHOC-CONFORMANCE1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/posthoc-conformance1；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-26T02:52:28+08:00 amend by wf-cli（op 50fcd58a）→ 資源宣告：原值指紋 sha256:3dc442e1499e2d63380e4a74a8ba3f24e936f47f25d209676f2575896c312c7c (239 bytes) → 新值指紋 sha256:13a37b08b0b7bc12f051fea5deaea429c4a02a97531f75a3cb8a3231e2c1b513 (155 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方授權擴 project.py 取 createdAt（A6 阻塞，裁定見 issuecomment-5415168406）；射程限 _LIST_ITEMS_QUERY 與 ItemSnapshot，實跑 find_conflicts 非終態持有者 0 張。
- 2026-08-26T12:30:53+08:00 handoff by wf-cli → owner 待認領（跨家族查核）；iteration 0；SHA 2470738def020c0dd4304545ec237dea95759fe6；證據 A6 阻塞已解除（需求方授權擴 project.py，裁定 issuecomment-5415168406）。PR #152。undecidable 85→44（-48%），createdAt 覆蓋 203/203；剩 44 筆逐筆檢查為 44/44 全由 CREATED_AT_TRUSTED_FROM 樓地板造成。channel_bypassed 程式路徑已可達（構造樣本命中並有測試釘住），真實母體候選 0 張且四類歸因逐條。變異檢驗 9 條全部反注轉紅還原逐位元相同；M20/M21 接上後原本失去鑑別力已改寫成釘住兩段文案互斥。pytest 1214→1218、contract_tool_reconcile --check rc=0、canonical_citation_scan rc=0、replay_escalation_rules rc=0、uv lock --check rc=0，皆以 $? 讀未接管線。ruff 逐檔對基線零新增、pyright delta 0（12→12 逐筆相同）。執行者自陳兩次相反方向的假結果，根因為 pyc 快取的 (mtime,size) 驗證在對調式變異下靜默失效。⚠️ 基線是 merge-base 4dd63dadc16a1626e81e2d6c50922f4137bf220a，⛔ 不是 origin/main 4e99845（PR #149 已於本卡分支開出後合併，兩者今日真的不同）。。
- 2026-08-26T15:36:21+08:00 review by wf-cli → APPROVE（✅通過）；查核者 跨家族查核者（身分未自述；需求方於對話中轉貼、PM 逐字轉錄）；core_pain_resolved yes；self_run 7 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-POSTHOC-CONFORMANCE1-e0-2470738def020c0dd4304545ec237dea95759fe6。
- 2026-08-26T15:56:08+08:00 handoff by wf-cli → owner 已合併（無部署面）；iteration 0；SHA 5170c27ef61df240ab6452f7172ff5830d1464c4；證據 查核 APPROVE（findings 0，收據由需求方於 2026-08-26 session 對話中轉貼、PM 逐字轉錄，⚠️ 收據原文未發佈於 PR）。需求方逐字指示「138 併 main 合併」後執行：先在分支上 git merge origin/main（993dc74，僅帶入 PR #149 的 AI_WORKFLOW.md，⭐ cli/ 相對查核 SHA 2470738 一行未變），CI 綠後 gh pr merge 152 --merge，merge commit 5170c27ef61df240ab6452f7172ff5830d1464c4。⭐ 併 main 排在查核之後而非之前，理由：提前併會使已發出的審核詞基線多出 canonical 改動、且 handoff 釘的 source_sha 過期。合併結果上重跑：pytest 1218 passed、contract_tool_reconcile --check rc=0、canonical_citation_scan rc=0、wfcli doctor --conformance rc=0。本卡為 CLI 唯讀檢查，⛔ 無部署面。；收尾清理：已清除 worktree、本地分支、遠端分支。


## Comment 5404265749 · 2026-08-25T02:26:32Z

## 承接自 aiwf#136（已停止）：既有研究留痕

本卡是 aiwf#136 依需求方 2026-08-25 拆卡裁定分出的 **S7b**。相關研究：

- [⭐ 合流點與基線清冊](https://github.com/ruan6047/ai-workflow/issues/136#issuecomment-5400106397)　⇒ validate_open_fields（validation.py:88）本來就能對既有卡重跑，實測 161 張中 7 張不合規、全為 2026-08-04 遷移卡。**驗收第 4 條的基線清冊即出自此。**

⚠️ 排程與資源：本卡與 aiwf#137（S7a）**都宣告 cli/src/wf_cli/validation.py** ⇒ assign 的資源互斥會硬拒後派的那張（assign_cmd.py 回 rc=4、零寫入）。⭐ 順序是 **S7a 先**——本卡的檢查面要不要含 service_goal_still_served，取決於 S7a 是否已合併（驗收第 5 條）。

⚠️ 卡面「需求：」欄已填 ruan6047（#136 是「—」，導致該卡痛點在機械上永遠改不了，card.py:775）。


## Comment 5404614655 · 2026-08-25T03:19:35Z

## ⚠️ 給本卡執行者：資源／欄位稽核**只能讀 body**，⛔ 不能讀 Project 欄位

本卡的事後掃描母體是**全部既有卡**，⇒ 它比任何一次臨時盤點都更容易踩到下面這個坑。

**實例（PM 於 2026-08-25 親自踩到，見 aiwf#137 [issuecomment-5404609166](https://github.com/ruan6047/ai-workflow/issues/137#issuecomment-5404609166)）**：
Project 的「資源宣告」欄是**有損攤平**，實際值形如

```
db_scope=none；file:a.py、file:b.py
```

`db_scope` 與清單塞在同一字串、`；` 與 `、` 混用。⇒ 用 `split("、")` 再 filter
`startswith("file:")` 會**丟掉每張卡的第一個資源**。PM 據此報過三次數字，全錯。

⭐ **權威在 body**：`assign_cmd.py:179` `parse_block(item.body)`、`:231` `try_parse_block(other.body)`
讀的是 `resources.py:51–52` 的 `resource-claims` JSON 哨兵區塊。

⇒ **本卡的事後重驗取值一律走 body**：
- 資源宣告 → `resources.parse_block(body)`
- 服務的原始目標 → `card.parse_service_goal(body)`（由 aiwf#137 落點 E 新增；本卡**呼叫**它，⛔ 不修改 `card.py`）
- 需求方 → 既有的 `card.parse_requested_by(body)`

⚠️ `ItemSnapshot.fields` 仍可用於**取卡清單與狀態**（`doctor_cmd.py:169–170` 既有路徑），
⛔ 但不可用於取上述宣告值。

⇒ 這一條應於本卡進規劃時**寫進驗收條件**，⛔ 不要只留在本則留言。

---

另記：`aiwf#137` 已於同日 amend 移除本卡與它的資源交集（本卡的 `validation.py` 已移除，
`#137` 已補上 `card.py`），實測兩張寫入集**交集為空** ⇒ canonical §3.2(3)「可真平行」成立，
**兩張可同時派工**。⛔ 先前卡上「S7a 先」那句已作廢。


## Comment 5404646517 · 2026-08-25T03:24:38Z

## 研究交付（第一輪，2026-08-25）：⭐ 事後掃描**已經有兩個**單一形態實例，而它們早就共用同一個形狀

canonical §5.1.2 逐字說 `legacy_authority_notes`「證明該需求**已經出現過一次**」。
**⛔ 那句已經過時：現在是兩次，而第二次是 `aiwf#130` 自己加的。**

### 兩個既有實例

| | `legacy_authority_notes` | **簡介雙居所漂移** |
|---|---|---|
| 純判定 | `find_legacy_authority_notes`（`doctor.py:1225`） | `find_brief_drift`（`doctor.py:1285`） |
| 批次入口 | `audit_legacy_authority_notes`（`:1255`） | `audit_brief_drift`（`:1297`） |
| 報告 | `LegacyAuthorityNoteReport` | `BriefDriftReport`（`:1275`） |
| canonical 提及 | ✅ §5.1.2 | ⛔ **沒有**——§5.1.2 寫在 `337f4c19`，該掃描來自 `d4ba7ce5` |

### ⭐ ⇒ 「合流或劃界」的正解是**第三個**：把它們已經共用的形狀抽出來

兩者**已經**逐點同形，⇒ 通用機制不是新發明，是**把既有共通點抽出來**：

1. **`audit_X(card_bodies: dict[str, str] | None, …) -> XReport`**——純函式、⛔ 不碰網路。
2. **`status: "scanned" | "not_scanned"`**，且 `card_bodies` 為 None／空時回 `not_scanned`。
   ⭐ `doctor.py:1210–1213` 逐字說明為什麼：「呼叫端不提供卡面時，findings 一樣是空的，
   **若兩者都印「無」，就成了一個永遠不會響的偵測器**」。
   ⇒ **這條是通用機制的必要條件，⛔ 不是選配。**
3. **`scanned_cards` 記母體數**——⇒ 對帳時「掃了幾張」與「幾張不合規」分開，
   ⭐ 正是本卡驗收第 4 條要的「母體數與取樣時刻」。
4. **`findings` 與「常態缺漏」分開**：`BriefDriftReport.missing`（`:1281`）逐字理由——
   「缺簡介是既有卡的常態、⛔ 非阻擋，混在一起會讓真正的漂移**淹沒在 188 張卡的雜訊裡**」。
   ⇒ 本卡的 7 張不合規遷移卡是同一個形狀：**不合規 ≠ 應阻擋**，兩類要分開列。
5. **I/O 在 `doctor_cmd.py`、判定在 `doctor.py`**——與本卡驗收第 1 條已寫的分層一致。
6. ⭐ **兩個掃描共用同一次 `list_items`**（`doctor_cmd.py:167–183`），逐字理由：
   「分兩次讀會讓 body 與欄位**跨了時間**，漂移偵測就分不出『真的漂移』與『兩次讀之間有人改過』」
   ⇒ **通用機制必須保住這個單次抓取的性質**，⛔ 不得讓每個掃描各抓一次。

⇒ **建議：本卡做「抽取＋讓兩個既有掃描成為它的第一批實作」，⛔ 不是在旁邊再蓋第三個。**
⭐ 那樣才對得上 §5.1.2「不是通用機制」那句批評——否則本卡就是第三個單一形態。

### ⚠️ 順帶查出一個既有缺陷（⛔ 本卡不一定要修，但要指名）

簡介漂移掃描**掛在 `--legacy-authority-notes` 旗標底下**（`doctor_cmd.py:121`／`:167` 同一個 `if`）。
而該旗標的 help（`:54–55`）逐字只說「列出使用 #62 之前措辭的 amend 授權留痕」，
⛔ **一個字都沒提簡介漂移**。

⇒ 使用者要跑簡介漂移，得先知道去打一個**名字是別的東西**的旗標。
⚠️ 若本卡做了抽取，旗標命名勢必要動；那時這個缺陷會一起被解掉——
**但那是副作用，須在交付中明說是不是刻意的**。

### ⚠️ 本輪未驗

- **`#136` 第一輪報的「161 張中 7 張不合規」**：⛔ 本輪未重驗。
  ⚠️ 依 `aiwf#137` 第十一輪的教訓（我的資源 parser 漏掉每張卡第一個資源），
  **凡是我自己腳本算出來的數字都要重算一次**。⇒ 下一輪重驗，
  ⛔ 在重驗完成前**不得**把 161／7 寫進交付當基線。
- **`run_doctor` 是否還有第三個事後掃描**：本輪只從 `legacy_authority_notes` 與
  `brief` 兩條線索找。⛔ 未對 `doctor.py` 全表窮舉 `audit_*`／`find_*`。
  ⚠️ 這**有進推理鏈**（「已經有兩個」與「抽取兩者共通點」都依賴它）⇒ 下一輪關掉。


## Comment 5404661843 · 2026-08-25T03:27:01Z

## 研究交付（第二輪，2026-08-25）：⛔ 更正第一輪的「兩個」——是**三個**，而第三個已經寫好卻打不到

第一輪我自標「⛔ 未對 `doctor.py` 全表窮舉 `audit_*`／`find_*`，⚠️ 這**有進推理鏈**」。窮舉了。

### 一、`doctor.py` 的 `audit_*`／`find_*` 全表（7 支）

| 行 | 函式 | 是不是「對既有卡面的事後掃描」 |
|---|---|---|
| `:472` | `audit_review_channel` | ⛔ 否（查核通道，非卡面欄位符合性） |
| `:1126` | `audit_commit_trailers` | ⛔ 否（掃 commit 不掃卡） |
| `:1225`／`:1255` | `find_legacy_authority_notes`／`audit_legacy_authority_notes` | ✅ 是 |
| `:1285`／`:1298` | `find_brief_drift`／`audit_brief_drift` | ✅ 是 |
| `:1574` | **`audit_state_face_drift`** | ✅ **是——而第一輪我漏了它** |

### 二、⭐⭐ 第三個**完整寫好、完整測過，但 CLI 打不到**

`audit_state_face_drift(card_id, body, delivery_status)`（`:1574`）：
比對「Log 最後一筆 lifecycle 事件推導的應有交付狀態」vs「Project 欄位實際值」。
它有 renderer（`render_state_face_drift`，`:1625`）、有 `__all__` 導出（`:1866`／`:1872`）、
用的是三值 `DriftVerdict = consistent／drift／undecidable`（`:1423`）。

**呼叫端全 repo 窮舉（含 tests、scripts）**：

- `cli/tests/test_doctor.py` **約 30 處**、`cli/tests/test_commands_mocked.py:1009` 一處
- `cli/src/` 生產碼 **0 處**——`run_doctor` 不呼叫它，`doctor_cmd.py` 沒有對應旗標

⇒ **它是一個測得很紮實但沒有入口的檢查。**

⭐ ⇒ **本卡的通用機制有一個現成、免費、且高價值的第一份工作：把它接上。**
那正好回答 §5.1.2 的批評——三個實例足以歸納出通用形狀，
⛔ 而不是在旁邊再蓋第四個單一形態。

### 三、⚠️ 但「統一取卡」有一條既有裁定擋著，⛔ 不能天真地合流

`doctor.py:1822–1827` 逐字：

> ⚠️ 刻意**不共用** `card_bodies`：那個參數餵給 `evaluate_cleanup_guard` 的第 3 步
> （資源宣告釋放），今天 `doctor_cmd` 從不提供它，故該步一律走 `card_body is None`
> 的分支。若本檢查為了取得卡面而順手把 `card_bodies` 一起填上，就會**沉默地改變
> `--cleanup-preview` 的判定**（原本跳過的資源釋放檢查開始生效，proceed 可能變
> blocked）——**那是另一張卡的射程**。兩個用途各自帶參數，誰都不會因為對方被接線而改變行為。

⇒ ⛔ **本卡不得把 `card_bodies` 與掃描用的卡面合成一個參數。**
⭐ 通用機制的正確形狀是「**同一次抓取、多個獨立消費者，各自帶自己的參數**」——
⇒ 保住 `doctor_cmd.py:167–183` 的單次 `list_items`（避免 body 與欄位跨時間），
但**不**把 `evaluate_cleanup_guard` 拉進來。⚠️ 這一條須逐字寫進交付，
⛔ 否則接線的人會「順手」把它填上而靜默改變 `--cleanup-preview`。

### 四、⛔ 更正我自己對 doctor 輸出的誤讀

我實跑 `wfcli doctor <root> --registry none`，看到 `#137`／`#138` 的 worktree 都被報成
「孤兒／未註冊」，一度以為是缺陷。**不是。**

- `--registry none` 的定義就是「只做純 git 檢查」，⇒ 沒有卡註冊可比 ⇒ 全部算孤兒。**設計如此。**
- 而預設 `--registry tasks-md` 在本 repo 同樣打不到：**`docs/TASKS.md` 根本不存在**（只有 `templates/TASKS.md`）。
- ⚠️ 且這**早就記在碼裡**，⛔ 不是我的發現：`doctor_cmd.py:34` 的 help 逐字
  「本 repo 與 cpbl 都已 cutover，讀到的是**封存於 2026-08-05 的凍結快照**」；
  `registry.py:159–163` 逐字記載「2026-08-12 實測 `doctor` 把六個 WF 卡的 worktree 全報為孤兒，
  正是因為它讀已封存的 `TASKS.md`」。

⇒ 與本卡的關係：**`doctor_cmd.py` 已經有一條從 Project 讀卡的路**（給 §5.5／§6 用），
而第 1 節的 worktree 對帳仍綁在死掉的 registry 上。
⚠️ 本卡把取卡變成一等公民之後，第 1 節的缺口會變得可順手補——
⛔ **但那是射程外，本卡只能指名，不得順手做**（同第三節的教訓）。

### 五、順帶佐證第一輪的旗標命名問題

實跑輸出第 5.5 節逐字：「（未掃描：本次未取得卡面。**這不等於沒有**——要掃描請加
`--legacy-authority-notes --owner <o> --project <n>`，**本節與該旗標共用卡面**。）」
⇒ 簡介漂移確實掛在名字是別的東西的旗標底下，**產品輸出自己承認了**。

### ⚠️ 本輪未驗

- **`audit_state_face_drift` 為何當初沒接線**：⛔ 未查其來源卡與裁定。
  ⚠️ **有進推理鏈**——若當初是**刻意不接**（像第三節那樣有裁定），本卡就不能逕自接上。
  ⇒ 下一輪必須關掉。
- **`#136` 第一輪的「161 張中 7 張」**：⛔ 仍未重驗（第一輪已標）。


## Comment 5404721662 · 2026-08-25T03:33:38Z

## 研究交付（第三輪，2026-08-25）：關掉「為何沒接線」，⛔ 並推翻我第二輪說的「免費」

### 一、⇒ 沒接線是**資源宣告邊界**，⛔ 不是刻意不接

`aiwf#65 DEV-STATE-FACE-DRIFT-GUARD1`（CLOSED，commit `4dd9d32`，2026-08-19）的 release 留痕逐字：

> ⚠️ **已知未接線：doctor_cmd.py 不在本卡資源宣告內，wfcli doctor 尚無旗標觸發此檢查，接線屬後續卡。**

執行者交付時也逐字寫過「未接線 CLI（doctor_cmd 不在宣告內），**接線屬後續**」。

⇒ ⛔ 與第二輪查到的 `card_bodies` 那條「刻意不共用」**不同性質**——那有裁定，這只是射程劃界。
⇒ **本卡宣告了 `doctor_cmd.py`，是天然的承接者。**

⛔ **而那張「後續卡」從來沒開過。** 搜遍兩 repo 全部 Issue（`STATE-FACE|DRIFT|state.face`），
只有 `#65` 自己與一張無關的 `#52`。⇒ **孤兒承接，已 6 天。**

### 二、⛔ 但我第二輪說的「現成、免費」是錯的——我實跑了

⛔ 不引用 `#65` 的舊數字。**直接 import `audit_state_face_drift` 對今天的看板跑一次**
（母體：Project #4 中有卡ID且有 body 的 193 張，取未結案 **62 張**，取樣時刻 2026-08-25）：

| | `#65` 實跑（2026-08-19） | **本輪實跑（2026-08-25）** |
|---|---|---|
| 未結案卡 | 82 | **62** |
| consistent | 21 | **1** |
| drift | **0** | **14** |
| undecidable | 61（74%） | 47（**76%**） |

不判定的 rule：`handoff_status_not_in_log` **45**、`open_initial` 14、`no_log_section` 2、`assign_logged_status` 1。

### 三、⭐⭐ 那 14 筆「漂移」全部是**規則變了**，⛔ 不是有人手搬看板

14 筆的 rule 全是 `open_initial`，形態一致：期望 `💡需求`、實際 `📥Backlog`。

⇒ 追成因：`1531666 fix(cli): open a card into the status the planning gate has not yet passed`
（**2026-08-21**）把 `card.py` 的 `delivery_status` 預設由 `📥Backlog` 改成 `💡需求`。

⇒ 實測驗證：**14 筆的開卡日 100% 落在 2026-08-21 之前**（12 之前 + 08-20 一筆；
⛔ 0 筆在當日或之後；⛔ 0 筆抓不到 open 行）。最早 2026-08-12，最晚 2026-08-20。

⭐ 而稽核**沒有過期**：`1531666` 同時改了 `doctor.py`（12 行），`OPEN_INITIAL_STATUS = "💡需求"`
（`doctor.py:1397`）是現值。

⇒ **這 14 筆是規則變更的殘餘，⛔ 不是任何人繞過通道。**

### 四、⇒ 本卡最重要的設計需求（本輪最大產出）

現行 `StateFaceDriftFinding.verdict ∈ {consistent, drift, undecidable}`
——⛔ **沒有「規則變了」這一格**。⇒ 今天接上去，它會把 14 張卡報成 `drift`，
而 `drift` 的既有語意是「**欄位被手搬而無事件**」。⇒ **那是 14 個錯誤的指控。**

⭐ **⇒ 事後符合性報告必須把兩件事分開：**

| 類型 | 成因 | 正確處置 |
|---|---|---|
| **(a) 規則變了、卡沒動** | canonical／常數改版，既有卡自然落後 | 遷移，或明示接受；⛔ 不歸咎任何人 |
| **(b) 卡被動了、事件沒寫** | 有人繞過 wfcli 手搬看板 | 補跑對應動詞讓事件與欄位同源 |

⚠️ 而區分它們**需要時間軸**：(a) 的判準是「卡的最後相關事件早於規則變更時刻」。
⇒ **通用機制必須讓每個掃描宣告自己的「規則生效時刻」**（形狀比照既有的
`TRAILER_GUARD_EPOCH = "2026-08-13T00:00:00+08:00"`，`doctor.py:828`）。
⛔ 沒有這個，任何事後掃描在下一次改版後都會開始亂指控。

### 五、⭐ 這一輪本身就是 §5.1.2 的活體實證

§5.1.2 說「卡開完之後 canonical 改版…**既有卡不會被重驗**」。
⇒ 本輪的實測是：**規則於 08-21 改變，14 張既有卡當場不合規，而到 08-25 沒有任何東西發現**
——因為唯一看得到它的那支檢查**沒有入口**。⇒ 本卡的存在理由，本輪自己量到了。

### ⚠️ 本輪未驗

- **76% 不判定的正解**：`#65` 逐字指名「寫入端讓 handoff Log 行自帶 stage/status（**首寫自描述**），
  屬另一張卡」⇒ 對應 `aiwf#54 WF-CLI-RESUME1`（**OPEN**）。
  ⛔ 本輪未讀 `#54` 卡面確認它真的涵蓋 handoff Log 行。⚠️ **有進推理鏈**
  （「本卡不必處理 76%」依賴它有承接者）⇒ 下一輪關掉。
- **`#136` 第一輪的「161 張中 7 張」**：⛔ 仍未重驗（第一、二輪皆已標）。
  ⚠️ 它是本卡驗收第 4 條的基線，**進交付前必須重算**。


## Comment 5404753163 · 2026-08-25T03:36:46Z

## 研究交付（第四輪，2026-08-25）：關掉兩個未驗項——⛔ 舊基線數字不能用，而「不合規」有第三種成因

### 一、⛔ `aiwf#54` **沒有**涵蓋 76% 不判定的修法

`#65` 逐字說正解「在寫入端讓 handoff Log 行自帶 stage/status（**首寫自描述**），屬另一張卡」。
⇒ 我第三輪據此指向 `aiwf#54 WF-CLI-RESUME1`（OPEN）。**本輪讀了它的驗收，⛔ 不成立。**

`#54` 驗收第 1 條逐字：「改造 handoff 與 assign 使**首寫自描述**——**第一個遠端寫入**
必須帶足以辨識『這是誰、為了什麼、寫到哪』的載荷。」

⇒ 那說的是**第一個遠端寫入**（`#23` 已判定＝owner 欄），⛔ **不是 Log 行的內容**。
而 Log 行是 handoff 的**最後**一個寫入。⇒ 兩件事相鄰但不重疊。

⇒ ⛔ **76% 不判定的修法今天沒有明確承接卡。**
⭐ ⇒ **本卡必須把「76% 判不出來」當成可預見的常態來設計報告**，
⛔ 不得假設它會被別張卡消掉。

### 二、⛔ `#136` 的「161 張中 7 張」不能用——本輪重算是 41／193

依 `aiwf#137` 第十一輪的教訓（我的 parser 會出錯），本輪**自己重跑**
`validate_open_fields`，取值一律讀 body（資源走 `resources.try_parse_block`）：

- 母體：Project #4 中有卡ID且有 body 的 **193 張**（取樣時刻 2026-08-25）
- 不合規：**41 張（21%）**
- 錯誤型態：`核心痛點 必填` **40**、`資源宣告必填` **34**、`db_scope 不在值域` **34**

⇒ ⛔ 與 `#136` 記的「161 張中 7 張」差一個數量級。**驗收第 4 條的基線須改用本輪的數字並附方法。**

### 三、⭐⭐ 但 41 之中只有一部分是「卡有缺陷」——**第三種成因浮出來了**

**(1) 核心痛點 40 筆 ⇒ 確認為真。** 抽驗 `INIT-PRODUCT-UX`（cpbl#62）、`ML-PT3`（cpbl#69）、
`OPS-REMOTE-PROBE1`（cpbl#75）：章節是
`## Spec`／`## 現況摘要（遷移當下…）`／`## 新制欄位`／`## 資源宣告（機器可讀；…）`，
⛔ **全文連「痛點」二字都沒有**。⇒ 不是我的 regex 讀不到，是真的沒有。

**(2) 資源／db_scope 的 34 筆 ⇒ ⛔ 不是卡的錯，是解析器讀不到。**
逐筆拆解 `try_parse_block` 回 `None` 的 34 張：

- **33 張**的標題是 `## 資源宣告（機器可讀；…）`——**帶後綴** ⇒ 正是
  `aiwf#105 WF-RESOURCE-HEADING-SUFFIX1`（**OPEN、待指派**）的缺陷，
  ⭐ 而 33 這個數字與該卡記載的「amend 可達 0/33」**逐字吻合**。
- **1 張**（`WF-REVIEW-EVENT-MARKER-CONTRACT1`）body 裡**確實有**合格外觀的
  `resource-claims` 哨兵與 JSON，`try_parse_block` 仍回 `None`
  ⇒ ⚠️ **另一種、尚未命名的解析失敗**。

### 四、⇒ 事後符合性報告必須**歸因**，⛔ 不能只計數

第三輪定出兩類，本輪補上第三類：

| | 成因 | 正確處置 | 本輪實測 |
|---|---|---|---|
| **(a) 規則變了、卡沒動** | 常數／canonical 改版 | 遷移或明示接受 | 14 筆（`open_initial`，全部開卡於 2026-08-21 之前） |
| **(b) 卡被動了、事件沒寫** | 有人繞過 wfcli | 補跑動詞 | 本輪 **0 筆** |
| **(c) ⭐ 工具讀不到** | 解析器缺陷（`aiwf#105` 等） | **修工具**，⛔ 不是修卡 | 34 筆（33＋1） |

⇒ ⛔ **若本卡交付時直接報「41 張不合規」，其中 34 張是錯誤的指控**——
它們的宣告存在，是讀取端有缺陷。⚠️ 那正是既有紀律裡「宣稱超出證據」的形態。

⭐ **⇒ 驗收第 4 條的基線清冊必須逐張帶歸因（a／b／c），⛔ 不得只有卡號與總數。**

### ⚠️ 本輪未驗

- **`WF-REVIEW-EVENT-MARKER-CONTRACT1` 那一筆的實際失敗原因**：⛔ 未追。
  ⚠️ 不進推理鏈——(c) 這一類的成立只需要 33 張那一群。
  ⇒ 但**實作前要追**，否則它會被錯歸成 (a) 或當成真不合規。
- **40 筆缺核心痛點是否全部是 2026-08-04 遷移卡**：抽驗 3 張全中，⛔ 未逐張確認。
  ⚠️ 影響的是歸因細節（是否全歸 (a)），⛔ 不影響「(c) 存在且有 34 筆」。


## Comment 5404779329 · 2026-08-25T03:40:59Z

## 裁定（需求方，2026-08-25）：採甲

本則由 PM 依需求方於本次 session 的口頭裁定「甲」逐字轉錄寫入，⚠️ 帳號為需求方本人的 token。

**本卡把「(c) 工具讀不到」當獨立歸因類輸出並指名 `aiwf#105`，⛔ 不等它修完。**

理由（需求方採納研究第四輪的論證）：(c) 這一類不是 `aiwf#105` 專屬——
只要有解析器就會有讀不到的卡，事後符合性報告本來就必須分得出
「**卡缺欄位**」與「**我讀不到**」。⇒ 歸因欄是通用機制的必要組成，
⛔ 不是為了繞過某一張未修的卡而加的權宜。

卡面已依此 amend（op `f879ae07`）。


## Comment 5404799028 · 2026-08-25T03:44:12Z

## 規劃交付（2026-08-25）

### Q1：抽取後的共用型別 ⇒ **共用信封，⛔ 不共用 finding 型別**

三個既有 finding 型別攜帶的資訊**不同**（`LegacyAuthorityNoteFinding` 有 timestamp／op_id／field_name；
`BriefDriftFinding` 有 reason；`StateFaceDriftFinding` 有 verdict／expected／actual／rule／deciding_event）。
⇒ ⛔ 強行併成一個 finding 型別會**損失資訊**，那是把抽取做成降級。

⭐ 正解：抽**信封**，finding 型別原樣保留。三者**都已經有 `card_id`** ⇒ 用 Protocol 約束即可。

```python
ConformanceCause = Literal["rule_changed", "channel_bypassed", "tool_cannot_read"]

class HasCardId(Protocol):
    card_id: str

@dataclass
class ConformanceScanReport:
    scan_id: str                               # legacy-authority-notes / brief-drift / state-face-drift
    status: Literal["scanned", "not_scanned"] = "not_scanned"
    scanned_cards: int = 0
    rule_epochs: dict[str, str] = field(default_factory=dict)   # ⭐ 見 Q2
    findings: list[HasCardId] = field(default_factory=list)
    #: ⚠️ 與 findings 分開，沿用 BriefDriftReport.missing 的既有理由
    #: （常態缺漏會把真訊號淹沒在 188 張卡的雜訊裡）
    routine_gaps: list[str] = field(default_factory=list)
    attribution: dict[str, ConformanceCause] = field(default_factory=dict)  # card_id → cause
```

**命名**：`--legacy-authority-notes` 改成 `--conformance`。
⭐ 實查：該旗標字面在 CI／腳本／文件（`*.yml`／`*.sh`／`*.md`）**0 命中** ⇒ 改名不會弄壞任何自動化。
⚠️ 但人會打它 ⇒ 保留為 deprecated alias（一行 `dest=` 即可），⛔ 不刪。

### Q2：規則生效時刻的落點 ⇒ ⭐ **它屬於「規則」，⛔ 不屬於「掃描」**

`state_face_drift` 一個掃描裡有多條規則（`open_initial`／`handoff_status_not_in_log`／…），
而 **2026-08-21 只變了 `open_initial` 一條**。⇒ 掛在掃描層會把整個掃描的結果一起誤判。

⇒ `rule_epochs: dict[rule_id, iso8601]`，形狀比照既有 `TRAILER_GUARD_EPOCH`（`doctor.py:828`）。
⭐ 而 `StateFaceDriftFinding.rule` **已經是機械可枚舉的常數**（該 dataclass docstring 逐字：
「值域是本模組的 `RULE_*`／`UNDECIDABLE_*` 常數——機械可枚舉，讓『不判定佔比』可以由 findings
直接統計而非人工宣稱」）⇒ **接得上，⛔ 不需要新增欄位。**

**歸因判準（機械）**：

```
cause(finding) =
  tool_cannot_read   若該卡的宣告區塊解析失敗（parse 回 None 而 body 有對應區段）
  rule_changed       否則，若 卡的最後相關事件時刻 < rule_epochs[finding.rule]
  channel_bypassed   否則
```

⚠️ 順序不可換：`tool_cannot_read` 必須先判，⛔ 否則解析失敗的卡會落到後兩類而變成錯誤指控。

### Q3：`state_face_drift` 接線的最小改動面 ⇒ **一個新參數、一個報告欄、一次 render**

| # | 落點 | 動作 |
|---|---|---|
| A | `doctor.py` `run_doctor` 簽章 | 新增 `card_delivery_statuses: dict[str, str \| None] \| None = None`。⛔ **獨立參數**——`doctor.py:1822-1827` 逐字禁止與 `card_bodies` 合流 |
| B | `doctor.py` `DoctorReport` | 新增 `state_face_drift: ConformanceScanReport` 欄，預設 `not_scanned` |
| C | `doctor.py` `run_doctor` 尾段（`:1829` 旁） | 對每張有 body 的卡呼叫既有 `audit_state_face_drift(cid, body, status)`，裝進信封 |
| D | `doctor.py` `render_text` | 新增一節，⭐ 復用既有 `render_state_face_drift`（`:1625`），⛔ 不重寫渲染 |
| E | `doctor_cmd.py:167–183` | 在**同一次** `list_items` 內多建一個 `{card_id: item.delivery_status}`（`ItemSnapshot.delivery_status` 已存在，`project.py:131`）。⛔ 不新增第二次抓取 |
| F | `doctor_cmd.py` 旗標 | `--legacy-authority-notes` → `--conformance`（+ alias），help 逐字列出它會跑哪幾個掃描 |

⇒ **既有的判定邏輯與渲染一行都不用改**——它們早就寫好且有約 30 支測試。

### PM 單方面決定清冊（草稿）

1. **共用信封而非共用 finding 型別**——canonical §5.1.2 只說「通用機制」，⛔ 沒說併型別。
2. **`ConformanceCause` 三值與其字面**——⛔ canonical 無此語彙，出自本卡研究第三、四輪的實測。
3. **歸因的判準順序（`tool_cannot_read` 先判）**——⛔ 無條文依據，出自「34 筆會變成錯誤指控」的實測。
4. **`rule_epochs` 掛在規則層而非掃描層**——出自 `open_initial` 單條變更的實測。
5. **旗標改名 `--conformance` 並保留 alias**——⛔ 無人依賴（實查 0 命中），保留 alias 是對人不是對機器。
6. **`routine_gaps` 沿用 `missing` 的語意但改名**——⛔ 改名是我的選擇。

### T3 規劃閘門：核心痛點三問

- **痛點是什麼**：卡開完之後規則變了，⛔ 沒有任何動詞會回頭問「它現在還合規嗎」。
  ⭐ 本卡研究期**當場量到一個活例**：`1531666`（08-21）改了 `open` 初始狀態，14 張既有卡當場不合規，
  到 08-25 沒有任何東西發現——因為唯一看得到的那支檢查**沒有入口**。
- **成功怎麼觀察**：`wfcli doctor --conformance --owner ruan6047 --project 4` 跑得出一份
  **逐張帶歸因**的清冊；且那 14 筆標為 `rule_changed`、那 33 筆標為 `tool_cannot_read`、
  ⛔ 不是 `channel_bypassed`。⇒ 三個都是可執行指令。
- **最大的未驗證前提**：**76% 不判定的報告仍然有用**。⛔ 機械上證不了「有用」，
  ⚠️ 能證的只有「不判定的比例與原因逐條可統計」。⇒ 若實際上沒人讀它，本卡的價值不成立，
  而那要等它上線後才知道。**⛔ 本卡不得宣稱已解決可讀性。**

### 前提清單與實查證據（T2 以上義務）

| 前提 | 證據 | 狀態 |
|---|---|---|
| `audit_state_face_drift` 生產碼 0 呼叫端 | 全 repo grep（含 tests）：`cli/src/` 0 處、tests 約 30 處 | ✅ 實查 |
| 未接線是射程邊界非裁定 | `aiwf#65` release 留痕逐字「接線屬後續卡」；該後續卡搜遍兩 repo **不存在** | ✅ 實查 |
| `ItemSnapshot.delivery_status` 可用 | `project.py:79`／`:131` | ✅ 實查 |
| `--legacy-authority-notes` 無自動化依賴 | `*.yml`／`*.yaml`／`*.sh`／`*.md` grep 0 命中 | ✅ 實查 |
| `StateFaceDriftFinding.rule` 機械可枚舉 | 該 dataclass docstring 逐字 | ✅ 實查 |
| `card_bodies` 不得合流 | `doctor.py:1822–1827` 逐字 | ✅ 實查 |
| 14 筆屬 `rule_changed` | 14/14 開卡日早於 `1531666`（2026-08-21） | ✅ 實跑 |
| 34 筆屬 `tool_cannot_read` | 33 張標題帶後綴（＝`aiwf#105`，與其「0/33」逐字吻合）＋1 張未命名失敗 | ✅ 實跑 |
| **`render_state_face_drift` 的輸出是否適合直接嵌進 `render_text`** | ⛔ **未讀該函式本體** | ⚠️ **未驗，⛔ 不設為硬前置** |
| **`asdict(report)` 對新型別（含 Protocol list）是否序列化得動** | ⛔ 未驗（`doctor_cmd.py:101` 走 `asdict`，`--json` 會踩到） | ⚠️ **未驗——⛔ 但這會擋交付，實作第一步就要試** |

### ⚠️ 本次規劃未驗

- 上表最後兩列。⚠️ 第二列（`asdict` 對 Protocol list）**風險較高**：`--json` 是既有輸出面，
  型別選錯會在交付末期才炸。⇒ **實作順序建議把它排第一**，⛔ 不要留到最後。
- **`aiwf#105` 若在本卡執行期被修好**，那 33 筆會從 `tool_cannot_read` 消失 ⇒ 基線對帳會對不上。
  ⚠️ 處置：對帳時同時記錄**取樣時刻與當時 `aiwf#105` 的狀態**，⛔ 不是假設它不變。


## Comment 5404805716 · 2026-08-25T03:45:17Z

## 規劃補正（2026-08-25）：關掉兩個未驗項——一個是我多慮，一個**推翻了我的落點 D**

### 一、`asdict` ⇒ ⛔ 不是風險，我標錯了

實跑原型：`ConformanceScanReport`（含 `list[HasCardId]`、`dict[str, Literal]`）
經 `dataclasses.asdict` **正常遞迴**，`findings[0]` 變成 plain dict
（鍵 `actual_status／card_id／deciding_event／detail／expected_status／rule／skipped_transparent／verdict`），
`json.dumps` 成功。

⇒ `Protocol` 只是型別註記、**執行期不參與**，`asdict` 看的是實例本身是不是 dataclass。
⇒ ⛔ 我把它列為「風險較高、實作排第一」是**多慮**。⭐ 但測了才知道，⛔ 不是靠推論撤回的。

### 二、⛔ **落點 D 錯了**：既有渲染器把 (b) 的處置寫死了

我原本寫「復用既有 `render_state_face_drift`（`:1625`），⛔ 不重寫渲染」。**實跑它的輸出**：

```
## 狀態面漂移對帳（Log 最後一筆事件 → 交付狀態；唯讀；1 張卡）
- 一致 0／漂移 1／不判定 0（不判定佔比 0%）
- [drift/open_initial] CARD-A　預期 💡需求／實際 📥Backlog
  - 漂移：…本檢查唯讀，只列舉不阻止；修復請補跑對應的 wfcli 動詞讓事件與欄位重新同源，
    勿手動搬看板。
- 偵測不等於強制：本檢查擋不住漏跑 handoff…強制面承接者是 CI（DEV-AIWF-MINIMAL-CI1，#48）…
```

⭐ 好消息：它**已經自己算不判定佔比**（`- 一致 X／漂移 Y／不判定 Z（不判定佔比 N%）`）
⇒ 那一段可以原樣留。

⛔ 壞消息：每一筆 drift 的處置逐字是「**補跑對應的 wfcli 動詞…勿手動搬看板**」，
**無條件輸出**。⇒ 對那 14 筆 `rule_changed` 的卡，它會叫人去補跑一個
**根本沒有漏跑的動詞**，並暗示有人手搬了看板。

⇒ **那正是本卡要消滅的「錯誤指控」，而它今天就寫在渲染器裡。**

### ⇒ 落點 D 改寫

| # | 落點 | 動作（修正後） |
|---|---|---|
| D1 | `doctor.py:1625` `render_state_face_drift` | 改為**依 cause 分流處置文案**：`channel_bypassed` 才輸出現行那句；`rule_changed` 改為「規則於 `<rule_epochs[rule]>` 變更，本卡最後相關事件早於該時刻 ⇒ **⛔ 無人繞過通道**，處置是遷移或明示接受」；`tool_cannot_read` 改為「宣告存在但解析失敗（`<原因>`）⇒ **修工具**，⛔ 不是修卡」 |
| D2 | 同函式 | ⭐ 保留既有的「一致／漂移/不判定＋佔比」統計行與「偵測不等於強制」那段，⛔ 不刪——後者逐字指名強制面承接者是 `aiwf#48`，是誠實聲明 |
| D3 | 摘要行 | 三類各自計數（現行只有 consistent／drift／undecidable 三格），⇒ 加 cause 維度 |

⚠️ ⇒ 這使本卡對 `doctor.py` 的改動**不只是接線**，還包含既有渲染器的行為變更。
`doctor.py` 已在本卡資源宣告內 ✅，⛔ 但交付時須明列「本卡改了一個既有函式的輸出」，
並附**變更前後的逐字對照**，⛔ 不得混在新功能裡帶過。

### ⇒ PM 單方面決定清冊追加

7. **改寫既有渲染器而非新增第二個**——⛔ 可以選擇「保留原函式、另寫 cause-aware 版本」，
   我選改寫，理由是兩個渲染器會讓「哪一個是真的」變成下一個問題。⚠️ 這是取捨不是必然。

### ⚠️ 補正後仍未驗

- **既有約 30 支測試中有幾支斷言了那句處置文案**：⛔ 未查。
  ⚠️ 若有，改寫渲染器會讓它們轉紅——那是**預期的紅**，但須在交付中逐支列出並說明為何該改。
  ⇒ 實作第一步就跑一次 `pytest cli/tests/test_doctor.py -k state_face` 取基線。


## Comment 5404809800 · 2026-08-25T03:45:58Z

## 規劃補正之二：⛔ 我寫在卡上的基線指令是錯的，附正確值

前一則我寫「實作第一步就跑一次 `pytest cli/tests/test_doctor.py -k state_face` 取基線」。
**⛔ 那條指令選到 0 支**（`161 deselected`）——測試函式名裡沒有 `state_face` 字樣。

**正確的 selector 與基線（實跑於 `d4ba7ce5`）**：

```
uv run pytest tests/test_doctor.py -k drift -q
⇒ 31 passed, 130 deselected
```

（cwd＝`cli/`。函式名形如 `test_drift_open_derives_requirement_and_flags_moved_face`、
`test_equivalent_shape_47_manual_board_move_without_event_is_drift`、
`test_drift_render_reports_counts_share_and_itemizes_only_noteworthy_cards` …）

### ⇒ 順帶關掉「有幾支測試斷言了處置文案」

grep 三個關鍵短語（`補跑對應的 wfcli 動詞`／`勿手動搬看板`／`重新同源`）於 `cli/tests/*.py`：
**0 命中**。

⇒ ⭐ 改寫渲染器的處置文案**不會因為文案本身讓任何測試轉紅**。
⚠️ 但 `test_drift_render_reports_counts_share_and_itemizes_only_noteworthy_cards`
確實斷言 render 輸出（依名稱是「計數／佔比／只列值得注意的卡」）⇒ 補正一的 D2
「保留統計行」不只是設計偏好，**是那支測試的前提**。⛔ 動它要連測試一起處理並說明。

⚠️ ⇒ 交付時的回歸基線逐字記為 **`-k drift` 31 passed（`d4ba7ce5`）**，
⛔ 不得只寫「全過」，也⛔ 不得沿用我上一則那條選不到東西的指令。


## Comment 5404840089 · 2026-08-25T03:50:48Z

## 研究交付（規劃期第五輪，2026-08-25）：⭐「76% 不判定還有沒有用」——不用辯論，把報告產出來看

我在規劃交付把「報告仍然有用」列為最大未驗證前提。**本輪把四個掃描全部對今天的看板跑一次，
產出報告該有的樣子。**

### 一、原始 findings（⛔ 未歸因前）

母體 **193 張**（Project #4 中有卡ID且有 body 者）；未結案 62 張。取樣時刻 2026-08-25。

| 掃描 | 原始輸出 |
|---|---|
| `legacy-authority-notes` | **17 行**，涉及 **11 張**卡 |
| `brief-drift` | 漂移 **0** 張；**缺簡介 190 張** |
| `state-face-drift`（未結案 62 張） | 不判定 **47**（76%）／一致 **1**／漂移 **14** |
| `open-fields` | 不合規 **41** 張 |

⇒ 攤平來看是 **200 多筆**。⛔ 那個量沒有人會讀。

### 二、⭐ 歸因之後：**32 筆**，而其中 14 筆還會再被降級

| 扣除項 | 筆數 | 依據 |
|---|---|---|
| `routine_gaps`（缺簡介） | **−190** | 既有設計已分開（`BriefDriftReport.missing`）——⭐ 本輪把它量化了：**沒有這個分離，報告有 78% 是這一類** |
| `tool_cannot_read` | **−34** | 33 張標題帶後綴（`aiwf#105`）＋1 張未命名失敗 |
| **剩下** | **32** | |
| ↳ 其中 `rule_changed`（epoch 接上後降級） | 14 | 全部 `open_initial`，14/14 開卡日早於 2026-08-21 |
| ⇒ **真正要有人動手** | **18** | 7 張缺核心痛點 ＋ 11 張舊措辭授權留痕 |

⇒ ⭐ **200+ → 18，約 93% 的雜訊被歸因欄擋掉。18 是一個人做得完的數字。**

### ⇒ 對那個前提的答覆

「76% 不判定」**不傷害可讀性**——因為不判定的那 47 筆**構造上就不在待辦集合裡**，
報告只需要說「47 筆判不出來，主因 `handoff_status_not_in_log` 45 筆，
其修法無承接卡」。⇒ **可讀性由歸因欄提供，⛔ 不由判定率提供。**

⚠️ 但誠實界線不變：本輪證明的是**待辦集合小到可讀**，⛔ **不是**「有人會去讀」。
後者仍然要等上線後才知道，⇒ 卡面該欄措辭維持。

### 三、⛔ 更正第四輪：那 7 張 `card_deficient` **也是遷移卡**

第四輪我說 40 筆缺核心痛點、抽驗 3 張全是遷移卡。本輪拆細後是
**34 `tool_cannot_read` ＋ 7 `card_deficient`**，而抽驗 `INGEST-PA-DAILY1`（cpbl#55）、
`UX-GAME-PA1`（cpbl#79）、`OPS-CODE-BRANCH-PROTECT1`（cpbl#83）：
章節同樣是 `## Spec`／`## 現況摘要`／`## 新制欄位`，⛔ 全文 0 個「痛點」。

⇒ 它們落到 `card_deficient` 而非 `tool_cannot_read`，**只因為資源解析成功了**——
而資源解析成功是因為它們有**兩個** `## 資源宣告` 章節（帶後綴的舊的 ＋ 後來補的新的）。

### 四、⭐⭐ 由此撞出一個跨卡風險，⛔ 不在本卡射程但必須指名

實測全母體 `^## 資源宣告` 前綴命中數分佈：**187 張命中 1 次、6 張命中 2 次**。

那 6 張（各為「精確標題 1 個 ＋ 帶後綴 1 個」）：
`INGEST-GAME-TM-REFACTOR1-G4`（⏸阻塞）、`INGEST-PA-DAILY1`（🏁完成）、
`INGEST-SPLITS-IBB-GHOST1`（🏁完成）、`OPS-WEB-DEPS1`（🏁完成）、
`UX-GAME-PA1`（📦已合併）、`OPS-CODE-BRANCH-PROTECT1`（🏁完成）。

⚠️ `aiwf#105` 的修法若是「放寬為前綴比對」，其**「恰好 1 次」不變量**會讓這 6 張
**由可解析翻轉成被拒**。⇒ 修 `#105` 會**製造** 6 筆新的 `tool_cannot_read`。

⭐ 影響範圍實測：6 張中 5 張是終態（🏁完成／📦已合併，依既有裁定終態卡宣告不再被讀）
⇒ **實際受影響的活卡只有 1 張**（`INGEST-GAME-TM-REFACTOR1-G4`，⏸阻塞）。

⇒ **建議把這一段轉貼給 `aiwf#105`**——它是那張卡的驗收該涵蓋的邊界案例，
⛔ 本卡不代它處理。

### ⚠️ 本輪未驗

- **`aiwf#105` 的實際修法是否真的是「放寬為前綴比對」**：⛔ 未讀該卡驗收，
  只依既有記載的判準推論。⚠️ **有進推理鏈**（第四節整段依賴它）⇒ 若它採別的修法，
  該風險可能不存在。**轉貼前必須先讀 `#105` 卡面。**
- **11 張舊措辭授權留痕是否真的需要處理**：`legacy_authority_notes` 的既有立場逐字是
  「報的是**留痕強度不足，不是授權無效**」⇒ ⚠️ 那 11 張可能**不需要任何動作**，
  ⛔ 本輪把它們算進「18 筆要動手」可能高估。⇒ 下一輪關掉。


## Comment 5404849912 · 2026-08-25T03:52:25Z

## 研究交付（規劃期第六輪，2026-08-25）：⛔ 我上一輪的「18 筆要動手」高估了 9 倍——實際是 **2 張活卡**

上一輪我自標兩個未驗項。**兩個都關掉了，而兩個都推翻了上一輪的數字。**

### 一、⛔ 那 11 張舊措辭授權留痕**不需要任何動作**

`LegacyAuthorityNoteFinding` 的 docstring 逐字：

> **本 finding 陳述的是留痕強度，不是授權真假**…欄位刻意只有定位資訊，
> 不含任何對該次授權的評價：doctor 讀不到那則留言的內文，**沒有立場評價它**。

旗標 help（`doctor_cmd.py:54–55`）也逐字：「報的是**留痕強度不足，不是授權無效**；
既存事件不得改寫」。

⇒ ⛔ **它們不進待辦集合。** 上一輪把 11 張算進「18 筆要動手」是錯的。

### 二、⛔ 剩下的 7 張裡，只有 **2 張**是活卡

| 卡 | 交付狀態 | |
|---|---|---|
| `INGEST-GAME-TM-REFACTOR1-G4` | ⏸阻塞 | ⭐ 活卡 |
| `UX-GAME-PA1` | 📦已合併 | ⭐ 活卡 |
| `INGEST-PA-DAILY1`／`INGEST-SPLITS-IBB-GHOST1`／`OPS-WEB-DEPS1`／`UX-GAME-RECAP1`／`OPS-CODE-BRANCH-PROTECT1` | 🏁完成 ×5 | 終態 |

⇒ 依既有裁定「終態卡的宣告不再被讀」，那 5 張屬檔案衛生。

### ⇒ 修正後的完整帳

**200+ 筆原始 → 歸因後 32 → 扣掉 rule_changed 14 → 扣掉不需動作的 11 → 扣掉終態 5 → 剩 2。**

### 三、⭐ 所以要誠實面對一個反問：待辦只有 2 張，這個機制值得做嗎？

**⛔ 用今天的筆數證成它是錯的**——它是**偵測器**，偵測器該用「**它會不會抓到過去發生過的事故**」來評價。

拿兩類已知事故實測：

| 事故 | 會不會被抓到 | 依據 |
|---|---|---|
| **2026-08-21 規則變更**（`1531666` 改 `open` 初始狀態），14 張既有卡當場不合規、**到 08-25 沒有任何東西發現** | ✅ **會**——本輪實跑當場列出 14 張 | 本卡研究第三輪實測 |
| **PM 漏跑 handoff 四次**（`#38`／`#47`／`#52`／`#57`），看板失真靠需求方發問才浮出 | ⛔ **不會，而且是結構性的** | `aiwf#65` 執行者自陳逐字：「事件缺席時 Log 與欄位一起過期、彼此一致，Log→欄位這條軸構造上看不見」 |

⇒ **兩類事故抓到一類。** ⭐ 而抓到的那一類（規則變更殘餘）正是 canonical §5.1.2 立節的理由，
⛔ 抓不到的那一類 `#65` 已明指強制面承接者是 CI（`aiwf#48`）＋ ruleset。

⚠️ **這是需求方該裁的取捨，⛔ 不是我該替你決定的**：
「一個能抓 A 類不能抓 B 類、今天待辦 2 張、但下次改版會再響」的偵測器，值不值得。

### 四、⛔ 更正上一輪的「跨卡風險」——`aiwf#105` **已經知道了**

上一輪我說「修 `#105` 會讓 6 張由可解析翻轉成被拒」。讀了 `#105` 卡面：
它的驗收第一段逐字**已經寫著**：

> ⚠️「恰好 1 次」的不變量在新比對下仍須成立…實測放寬後，真區段前插一個帶後綴的假區段
> 命中 2 次仍拒收、**兩種標題並存命中 2 次仍拒收**

⇒ ⛔ 機制不是我的發現。⭐ **我能加的只有數量與名單**：那是 **6 張**，其中**活卡 1 張**
（`INGEST-GAME-TM-REFACTOR1-G4`，⏸阻塞）。⇒ 值得轉貼給 `#105` 作為邊界案例的實測值，
⛔ 但不是新風險。

⭐ 而讀 `#105` 另外查到一件**對本卡更重要**的：它的驗收第一段逐字
「33 張的資源宣告區段內 **begin/end 哨兵命中 0/33**，parse_block 會改卡在缺哨兵。
『amend 可達由 0/33 變 33/33』**為假**」，且哨兵的遷移屬**第二段**（尚未有人做）。

⇒ **即使 `#105` 的第一段落地，那 33 張仍然 `tool_cannot_read`。**
⇒ ⭐ 歸因欄不是為了繞過一張短期未修的卡——**那一類會存在相當長一段時間**。

### ⚠️ 本輪未驗

- **`UX-GAME-PA1`（📦已合併）算不算「活卡」**：我用「非終態」當判準，
  而 📦已合併 在既有語彙裡是待部署而非終態。⛔ 未確認它是否還會被 amend。
  ⚠️ 影響的是 2 還是 1，⛔ 不影響「個位數」這個結論。


## Comment 5404875156 · 2026-08-25T03:56:26Z

## 研究交付（規劃期第七輪，2026-08-25）：規則變更的**基礎發生率**，以及 `rule_changed` 會變成下一堆雜訊

上一輪把取捨丟回給需求方，卻沒給「下次改版多久會來」這個數字。**本輪量它。**

### 一、基礎發生率：最近 20 天至少 **6 次**會產生殘餘的規則變更

掃 `validation.py`／`card.py`／`project.py`／`AI_WORKFLOW.md` 的 commit，
取「改必填欄／值域／預設狀態／新增範本必填」這一類：

| 日期 | commit | 造成的殘餘 |
|---|---|---|
| 2026-08-06 | `f180659` review 輸出契約 | 既有裁決不合新契約 |
| 2026-08-11 | `26a0149` **open 必填能力路由** | 見下 |
| 2026-08-18 | `ae8f741` **交付狀態語彙對齊＋三個前授權階段** | 語彙變更 |
| 2026-08-21 | `1531666` open 初始狀態 `📥Backlog`→`💡需求` | **14 張**（第三輪實測） |
| 2026-08-22 | `fe296ad` Backlog 閘門依級別分流 | 閘門前提變更 |
| 2026-08-25 | `d4ba7ce` **簡介欄上線** | 見下 |

⇒ **約每 3–4 天一次。** ⛔ 08-21 不是一次性事件。

### 二、⭐⭐ 殘餘**只累積不清除**——08-11 的到今天原封不動

實測（母體 193 張，活卡 62 張，取樣時刻 2026-08-25）：

**`wf-routing:v1`（`26a0149` 起 `open` 必填，已 14 天）**
- 缺該標記：**107 張**（其中**活卡 38 張**）
- 其中開卡日早於 2026-08-11：**45 張** ⇒ 明確屬 `rule_changed` 殘餘
- ⚠️ 開卡日在 08-11 當日或之後卻仍缺：**21 張**（前 5 張的開卡日全是 `2026-08-11` 當天）
  ⇒ ⚠️ 我的判準只到「日」的粒度，⛔ 分不出「commit 落地前開的」與「落地後仍缺」。
  **實作時 epoch 必須用完整 ISO-8601 時刻，⛔ 不能用日期。**

**`card-brief` 哨兵（`d4ba7ce`，今天）**
- 缺：**190 張**（活卡 60 張），其中 149 張開卡日早於今天 ⇒ 今天剛產生的殘餘
- ⭐ **開卡日在生效後仍缺：0 張** ⇒ 新通道對新卡是有效的，殘餘純粹是歷史。

### 三、⇒ 這推翻了我上一輪暗示的「待辦只有 2 張」是穩態

若偵測器從 08-11 就存在，今天的 `rule_changed` 桶會是
**45（路由）＋149（簡介）＋14（初始狀態）＋…＝數百筆**。

⇒ ⭐⭐ **`rule_changed` 會變成下一個 190。** 那正是 `routine_gaps` 分離所要避免的形態，
⛔ 而我目前的設計只把它分出來，**沒有給它出口**。

### ⇒ 本輪產出的新設計需求

**每一個 `rule_epoch` 必須帶一個宣告過的「處置」，⛔ 不能只有時刻。**

```python
@dataclass
class RuleEpoch:
    rule_id: str
    effective_from: str          # ⭐ 完整 ISO-8601，⛔ 不是日期（見第二節）
    disposition: Literal["migrate", "accept_as_legacy"]
    declared_by: str             # 需求方裁定的留言 URL 或 commit
```

- `migrate`：殘餘應被清掉 ⇒ 報告**列出並計數**，那是待辦。
- `accept_as_legacy`：⭐ 需求方已裁定既有卡不追溯 ⇒ 報告**只給一行摘要數字**
  （「路由標記：45 張既有卡依 2026-08-xx 裁定不追溯」），⛔ **不逐張列出**。

⇒ 沒有這一層，本卡交付第一天的報告就是數百筆——**與它要解決的問題同形**。

### ⇒ 對第六輪那個取捨的補充（⛔ 仍不替需求方決定）

| | 第六輪只講了 | 本輪補上 |
|---|---|---|
| 今天待辦 | 2 張 | — |
| 下次會響 | 「下次改版」 | ⭐ **約 3–4 天一次**，最近 20 天 6 次 |
| 沉默成本 | 08-21 沉默 4 天 | ⭐ **08-11 的殘餘沉默 14 天且從未被發現** |
| 代價 | — | ⭐ 若不設 `disposition`，第一天就產出數百筆雜訊 |

### ⚠️ 本輪未驗

- **那 6 次 commit 是否每一次都真的產生殘餘**：只逐一實測了 `26a0149`、`1531666`、`d4ba7ce` 三次。
  ⛔ `f180659`／`ae8f741`／`fe296ad` 未測。⚠️ 影響的是「6 次」這個數字的精確度，
  ⛔ 不影響「不是一次性事件」與「殘餘只累積」兩個結論（那兩個各有實測支撐）。
- **21 張「生效後仍缺」的真實成因**：⛔ 日期粒度分不出來。⚠️ 這一項**有進推理鏈**——
  若它們真的是生效後開的，那代表 `open` 的必填檢查有洞，那是另一張卡而不是殘餘。
  ⇒ 下一輪用 commit 時刻而非日期重算。


## Comment 5404887674 · 2026-08-25T03:58:30Z

## 研究交付（規劃期第八輪，2026-08-25）：⭐⭐ 實測逼出**第四種成因**——三類歸因不夠

第七輪自標「⚠️ 有進推理鏈：21 張『生效後仍缺』的成因，日期粒度分不出來」。**用時刻重算了。**

### 一、⛔ 先更正：我第七輪挑錯了 epoch

我用 `26a0149`（`2026-08-11T13:01:38+08:00`，「open 必填能力路由」）。
但 `wf-routing:v1` 這個**標記字面**實際由 `6325ae2` 引入
（`2026-08-11T18:29:56+08:00`，「decide routing format by migration marker, not by content」）
——晚 5.5 小時。⇒ ⭐ **規則與它的標記不是同一個 commit**，epoch 要釘標記那個。

⚠️ 這對本卡是設計層的教訓：`rule_epochs` 的值必須釘**檢查所依據的那個構件**落地的時刻，
⛔ 不是「大家覺得規則什麼時候開始」的那個 commit。

### 二、用時刻重算（epoch＝`2026-08-11T18:29:56+08:00`）

缺 `wf-routing:v1` 的 **107 張**拆成：

| | 張數 | 判讀 |
|---|---|---|
| 開卡於 epoch **之前** | **50** | ✅ `rule_changed` 殘餘 |
| ⚠️ 開卡於 epoch **之後仍缺** | **16** | ⛔ **三類都套不上** |
| Log 無可解析 open 行 | 41 | 多為 2026-08-04 遷移卡 |

那 16 張的開卡時刻橫跨 **2026-08-12T00:11 → 2026-08-15T10:07**，⇒ 全部遠在 epoch 之後。

### 三、⭐⭐ 抽驗那 16 張，三類歸因**全部套不上**

抽 5 張（`OPS-CLEANUP-SMOKE1`／`WF-MARKER-SCOPE-CLEARANCE1`／`PROD-SYNC-STATUS-REVISIONS1`／
`DEV-ROADMAP-VERIFIER1`／`WF-DISPOSITION-FIX1`），逐張看：

- **標記：無**
- **路由行：有**（`- 執行：待指派　查核：待指派` 這種**舊格式**，⛔ 無括號內的能力建議）
- **`## Log` 段落：完整**

⇒ ⛔ **不是 body 被 `gh issue edit` 覆寫**（Log 還在）。
⇒ ⛔ 不是 `rule_changed`（開卡在 epoch 之後）。
⇒ ⛔ 不是 `tool_cannot_read`（解析器讀得到，就是內容不合）。
⇒ ⛔ 也不是 `channel_bypassed`——**沒有人繞過通道，它們就是 `wfcli open` 開出來的**。

### ⇒ 需要**第四種成因**

```
(d) writer_nonconformant ── 卡是**經由**正規通道建立的、規則當時已生效，
                            而寫入端產出了不合規的內容。
                            處置＝查寫入端，⛔ 不是修卡、也⛔ 不是修讀取端。
```

⚠️ ⇒ **本卡的 `ConformanceCause` 要從三值改成四值**，且歸因判準要多一條：

```
(d) 若 卡的建立事件晚於 rule_epoch，且解析成功，且內容不合規 ⇒ writer_nonconformant
```

⭐ 這一類的價值特別高：**它指向的是工具的洞，而工具的洞會持續產出新的不合規卡**
——⛔ 前三類都只是存量。

### ⚠️ 那 16 張的真正根因，本輪**沒有查出來**

可能是：`open` 在某些路徑上不寫標記／當時操作者用的是較舊的安裝版本／
路由行由別的路徑補寫。⛔ **三個我都沒有驗，不猜。**

⚠️ 依 §6.4.2 標明驗不了的原因：要查它得比對每張卡開卡當下 `wfcli` 的實際版本，
而**卡面不記錄 CLI 版本** ⇒ 需要另外的證據來源（安裝紀錄或 commit 時序推論）。
⇒ ⭐ **那本身就是一個發現**：狀態面沒有記錄「這筆是哪個版本的工具寫的」，
⇒ `writer_nonconformant` 這一類今天**指得出來、但追不下去**。
⛔ 本卡不解決它，但要在條文中指名這個限制。

### ⚠️ 本輪未驗

- **16 張是否全部同形**：只抽了 5 張（全部命中「有行無標記、Log 完整」）。⛔ 未逐張。
  ⚠️ 影響的是 (d) 的筆數精確度，⛔ 不影響「(d) 這一類存在」。
- **41 張無 open 行的卡該歸哪一類**：⛔ 未定。⚠️ 它們多為遷移卡（Log 由遷移產生、無 `open by` 行）
  ⇒ 可能需要第五種「無法建立時間軸」的處置（比照既有 `undecidable`）。
  ⚠️ **有進推理鏈**（四類是否夠用依賴它）⇒ 下一輪關掉。


## Comment 5404894912 · 2026-08-25T03:59:41Z

## 研究交付（規劃期第九輪，2026-08-25）：關掉「41 張無 open 行」——⭐ 第五類可以避免，但有代價

### 一、那 41 張的形狀

| 第一筆 Log 事件 | 張數 |
|---|---|
| `handoff`（無 `open`） | 21 |
| **完全沒有帶時戳的事件** | 12 |
| `assign`（無 `open`） | 8 |

⇒ 其中**活卡 25 張**。最早的第一筆事件是 `2026-08-05`（`OPS-STATE-PLANE-MIG1`）。

⇒ 對這 41 張，**卡面上讀不出「這張卡什麼時候存在的」** ⇒ 無法與 `rule_epoch` 比較
⇒ 落 `undecidable`（比照既有 `DriftVerdict` 的第三值）。

### 二、⭐ 但它**可以避免**：Issue 的 `createdAt` 是機械可得的第二來源

`gh issue view --json createdAt` 是平台事實，⛔ 不需要卡面配合。
⇒ 取值優先序建議：

```
card_exists_since =
  1. 卡面 `## Log` 的 `open by` 事件時戳      （最準：卡自己說的）
  2. Issue 的 createdAt                       （退而求其次：平台事實）
  3. 都沒有 → undecidable                     （⛔ 不猜）
```

⇒ 以第 2 層接手後，41 張裡**只有真正抓不到的才會落 undecidable**。

### ⚠️ 三、代價要講清楚，⛔ 不是免費

1. **語意不完全相同**：`createdAt` 是 **Issue 建立時刻**，而 2026-08-04 遷移卡的
   **工作**早於該時刻。⇒ 對 08-04 之後的 epoch 是對的比較，
   ⛔ 對更早的規則會把遷移卡誤判成「規則生效後才建立」（落入第八輪的 (d)）。
   ⇒ **須在條文釘死：`createdAt` 只能用於比較 2026-08-04 之後的 epoch。**
2. **取數成本**：`doctor_cmd.py` 現行走 `list_items`（Project GraphQL），
   ⛔ 本輪未確認 `ItemSnapshot` 是否帶 `createdAt`。若沒有，要嘛擴 `list_items` 的查詢、
   要嘛多打一次 `gh issue list`——⚠️ 而後者會違反既有的「**同一次抓取**」紀律
   （`doctor_cmd.py:167–183` 逐字：分兩次讀會讓 body 與欄位跨了時間）。
   ⇒ **正解是擴既有查詢，⛔ 不是加第二次抓取。**

### ⇒ 歸因設計的最終形狀（第八、九輪合併）

```python
ConformanceCause = Literal[
    "rule_changed",          # 卡早於規則 → 遷移或依 disposition 接受
    "writer_nonconformant",  # ⭐ 卡晚於規則卻仍不合規 → 查寫入端（第八輪）
    "channel_bypassed",      # 欄位被手搬、無對應事件 → 補跑動詞
    "tool_cannot_read",      # 解析失敗 → 修工具
    "undecidable",           # ⭐ 建立時刻不可得 → ⛔ 不猜（第九輪）
]
```

⚠️ 判準順序（不可換）：`tool_cannot_read` → `undecidable` → `rule_changed`
→ `writer_nonconformant` → `channel_bypassed`。
⇒ 理由：前兩者是**我們自己的侷限**，⛔ 不該讓它們變成對卡或對人的指控。

### ⚠️ 本輪未驗

- **`ItemSnapshot` 是否已帶 `createdAt`**：⛔ 未查。⚠️ 影響的是實作成本（擴查詢 vs 已有），
  ⛔ 不影響取值優先序的設計。⇒ 實作第一步查。
- **12 張「完全沒有帶時戳事件」的卡**：⛔ 未看它們的 Log 究竟長什麼樣。
  ⚠️ 若它們連 `## Log` 都沒有，那是另一種不合規（範本缺章節），
  ⛔ 與「讀不出建立時刻」是兩件事，本輪把它們混在一起算了。


## Comment 5404946150 · 2026-08-25T04:06:33Z

## 研究交付（規劃期第十輪，2026-08-25）：⛔ 我全部探針走的是壞掉的路；重驗後數字全對，但撞出**欄位層**的缺陷

### 一、⛔ 先自首：我所有探針都用 `gh project item-list`，而碼裡明文說它壞

`project.py:377–378` 逐字：

> 刻意走原生 GraphQL 分頁查詢，**不用 `gh project item-list`**——後者對**中文欄位名稱的
> JSON key 有編碼錯誤**（見 OPS-STATE-PLANE-MIG1 Task 1「意外發現」）。

⇒ 我先前輸出裡出現的 `"���付狀態"`、`"���別"` 就是它。我用「後綴比對」繞過，
⛔ 但那是繞過一個**已知壞掉**的介面，而正規介面就在旁邊。

### 二、用 `list_items`（正規路徑）重跑，**數字逐一重現**

| 量測 | 壞路徑 | **正規路徑** |
|---|---|---|
| item 數 | 193 | **193** ✅ |
| 未結案 | 62 | **62** ✅ |
| state-face-drift | 47／1／14 | **47／1／14** ✅ |
| open-fields 不合規 | 41（34＋7） | **41（34＋7）** ✅ |
| 缺 `wf-routing` | 107 | **107** ✅ |

⇒ 結論不變。⚠️ 但方法從「繞過壞介面」換成「用對的介面」，⇒ 後續交付一律以此為準。

### 三、⭐⭐ 而正規路徑露出一個**欄位層**缺陷：`分支／worktree`

看板上實際帶過值的欄位比 `FIELD_SPECS` 多一個：**`分支／worktree`（全形斜線）**，
而 `FIELD_SPECS` 宣告的是 **`分支worktree`（無斜線）**。

⇒ ⛔ **沒有任何程式讀 `分支／worktree`**（`CARD_FIELD_MAP`／`FIELD_SPECS` 只知道後者）。

**影響實測（⛔ 不誇大）**：

| | 張數 |
|---|---|
| 舊欄位有值 | 41 |
| 兩個欄位都有值 | 8 |
| 只有舊欄位有值 | 33 |
| ↳ 其中值是佔位 `—` | 30 |
| ↳ **⭐ 真正讀不到的登記** | **3** |
| ↳ 其中**非終態** | **0** |

那 3 張：`OPS-STATE-PLANE-MIG1`／`INGEST-PLAYER-BIO-GAP2`／`INGEST-SPLITS-IMPORT-RESTATE1`，
**全部 🏁完成**。⇒ **今天的實際危害是零。**

### 四、⇒ 但機制值得記，因為它是**另一種殘餘產生器**

`ensure_fields` 的既有語意是**冪等但只增不減**（「已存在的原樣保留，含既有 option id」）。
⇒ ⭐ **每一次欄位改名都會留下一個孤兒欄位，而沒有任何東西會說。**

⇒ **本卡的通用機制應含一個「欄位層掃描」**：看板實際欄位集合 vs `FIELD_SPECS`，
列出 (i) 有值但未宣告的孤兒欄位、(ii) 宣告了但零張卡有值的欄位（本輪實測 **0 個**）。

⚠️ 這與現行五類歸因**正交**——它不是某一張卡的問題，是**狀態面本身的形狀問題**。
⇒ 報告需要一個與 per-card findings 分開的區段，⛔ 不要把 41 張卡各報一筆。

⭐ 而這一條本身就是本卡價值的證據：**它是被「拿現行規則重驗既有狀態」這個動作找出來的**，
⛔ 不是任何既有檢查找到的。

### 五、關掉第九輪的未驗項：`createdAt` 的取得成本

`ItemSnapshot`（`project.py:112–120`）**沒有 `createdAt` 欄位**。
⭐ 但 `list_items`（`:374`）走的是**原生 GraphQL 查詢** `_LIST_ITEMS_QUERY`
⇒ 加 `createdAt` 只是擴查詢片段，**同一次抓取內完成**，
⛔ 不需要第二次抓取、不違反 `doctor_cmd.py:167–183` 的紀律。⇒ **成本低，第九輪的顧慮解除。**

### ⚠️ 本輪未驗

- **`分支／worktree` 是什麼時候、被哪個 commit 改名的**：⛔ 未追。
  ⚠️ 影響的是它的 `rule_epoch` 值，⛔ 不影響「孤兒欄位存在且無人讀」這個事實。
- **12 張「完全無時戳事件」的卡**（第九輪留的）：⛔ 本輪仍未看它們的 Log 形狀。
  ⚠️ 若它們連 `## Log` 都沒有，那是範本缺章節、與「讀不出建立時刻」是兩件事。


## Comment 5404979025 · 2026-08-25T04:11:27Z

## 研究交付（規劃期第十一輪，2026-08-25）：⭐⭐ 本卡最有價值的輸出不是「卡不整齊」，是「**24 張活卡的寫入通道打不到**」

### 一、實測拒收（⛔ 不是推論）

對 `ML-FIELD-OF1`（cpbl，**💡需求，活卡**）跑 `wfcli amend --dry-run`（零寫入）：

```
[amend] 拒收（未寫入任何狀態）：`- Initiative：…　spec 基線：…` 這一行在 Log 之前命中 0 次，必須恰好 1 次
```

⇒ **那張卡永遠 amend 不動。** 不是「不合規」，是**唯一的寫入通道打不到它**。

### 二、全母體量測（走 `list_items` 正規路徑）

| | 張數 |
|---|---|
| 母體 | 193 |
| **`amend` 構造上打不到** | **41（21%）** |
| ↳ **其中非終態（活卡）** | **24** |
| ↳ 活卡中處於 `💡需求` | **21** |

成因分佈：

| 成因 | 張數 |
|---|---|
| 缺 `- 需求：…　規劃：…` 與 `- Initiative：…　spec 基線：…` 兩行 | 28 |
| 上述＋**連 `## Log` 段落都沒有** | 12 |
| **排版損壞**（`split_at_log` 直接拋錯） | 1 |

活卡 24 張逐一列於本輪探針輸出，含 `INIT-PRODUCT-UX`、`ML-PT3`、`OPS-REMOTE-*` 全系列、
`INGEST-GAME-TM-REFACTOR1-G4`（⏸阻塞）、`UX-GAME-PA1`（📦已合併）等。

### 三、⭐ 那張「排版損壞」的卡，根因逮到了——**而它就是第四輪那張未命名的**

`WF-REVIEW-EVENT-MARKER-CONTRACT1`（🏁完成）。body 的實際位元組：

```
…須另開後續程式卡。\n\\n## Log\n\n- 2026-08-09T00:15:32+08:00 open by GPT-5@Codex…
```

⇒ `## Log` 前面是一個**字面的反斜線-n**（`\\n`），⛔ 不是真的換行
⇒ `## Log` 不在行首 ⇒ `split_at_log` 拒絕、`try_parse_block` 也讀不到。

⭐ **第四輪我標「1 張有合格哨兵卻仍解析失敗、⚠️ 另一種未命名的失敗」——就是這張，現在命名了。**

⚠️ 而這正是 `aiwf#35` 規則二（**寫入端拒收**，逐字「⛔ 不得靜默寫出一個自己讀不回的字串」）
要防的形態。它於 2026-08-09 由 `open by GPT-5@Codex` 寫入，⛔ 至今沒有任何東西發現。

### 四、⇒ 這給本卡一個比「歸因」更前面的維度

前十輪我把輸出設計成「不合規 ＋ 五類歸因」。**本輪顯示還缺一個更急的軸**：

```
reachability = reachable | unreachable
```

- `unreachable`：**唯一的寫入通道（wfcli）在構造上碰不到這張卡**
  ⇒ 它的任何其他不合規項**都修不了**，⛔ 列出來也沒用。
- ⭐ 所以報告要**先分可達性、再談合規性**：24 張活卡在「修不了」這一層，
  ⛔ 把它們和「缺核心痛點」混在同一份清單裡，會讓人以為那是可以動手的待辦。

⚠️ **而它會擋住 `aiwf#130` 的 S5（既有卡簡介回填）**：那 24 張的 `amend --brief` 必然失敗。
⇒ 本輪建議把這一段轉貼到 S5 的承接處，⛔ 本卡不代它處理。

### ⇒ 這也回答了第六輪那個取捨

第六輪我報「今天待辦只有 2 張」，並把「值不值得」丟回需求方。
⛔ **那個數字漏了這一整層**：真正的頭條是 **24 張活卡（21 張在 `💡需求`）連改都改不了**，
⇒ 它們看起來在待辦池裡等人做，實際上**一旦有人動它就會撞牆**。

⭐ 而這件事是**本卡的機制找出來的**，⛔ 不是任何既有檢查找到的——
它已經在那裡至少 21 天（2026-08-04 遷移）。

### ⚠️ 本輪未驗

- **`assign`／`handoff` 是否也打不到那 24 張**：⛔ 只驗了 `amend`（它有 `--dry-run`）。
  ⚠️ `handoff` 無 dry 路徑 ⇒ 驗它會有真實寫入風險。
  **⇒ 這一項要留給執行階段用密封探針處理，⛔ 我不在研究期對真實卡試寫。**
- **那 24 張的修法**：⛔ 未設計。⚠️ 可能需要一次性遷移（同 `aiwf#105` 第二段的形態），
  ⇒ 屬另一張卡，本卡只負責**發現並列出**。


## Comment 5405217030 · 2026-08-25T04:26:39Z

## 第十一輪的發現已交付給 `aiwf#105`，本卡射程不變

需求方 2026-08-25 裁定：**擴充 `aiwf#105` 的射程，⛔ 不另開遷移卡**
（依 canonical §3.2「三者皆不成立時，正解是擴充現卡授權，不是開卡」——同一批卡、同一根問題）。

已完成：
- `aiwf#105` 裁定留痕：[issuecomment-5405165599](https://github.com/ruan6047/ai-workflow/issues/105#issuecomment-5405165599)
- `#105` 核心痛點擴為兩個破口（op `682c9728`，附裁定 URL）
- `#105` 驗收新增**第四段**（卡面標頭與 Log 段落，41 張／活卡 24 張）、
  雞生蛋揭露義務、第三段母體 33→41、第一段補上 6 張「兩種標題並存」的邊界案例（op `15a04daf`）

### ⇒ 兩張卡的界線（⛔ 不重疊）

| | `aiwf#105` | **本卡 `aiwf#138`** |
|---|---|---|
| 職責 | **修**那 41 張，讓它們回到 wfcli 可達 | **發現並列出**不合規與不可達 |
| 寫入集 | `resources.py`／`card.py`／`amend_cmd.py`＋三支測試 | `doctor.py`／`doctor_cmd.py`／`test_doctor.py` |
| 交集 | ⛔ 無 | |

⇒ 本卡仍須實作 `reachability = reachable | unreachable` 這一軸——⭐ 理由不是為了等 `#105`，
而是**這一軸本身是通用機制的一部分**：任何時候都可能有新的卡因寫入端缺陷而變成不可達
（實測 `writer_nonconformant` 那 16 張就是活例）。

⚠️ 承接關係：`#105` 落地後本卡的 `unreachable` 清單**應該縮到 0**
⇒ ⭐ 那正好是本卡的一個**可證偽預測**，建議寫進交付：
「本卡上線時 unreachable = 41（活卡 24）；`aiwf#105` 落地後應為 0，否則其一有缺陷。」


## Comment 5405240624 · 2026-08-25T04:29:23Z

## T3 規劃閘門：核心痛點三問（更新版，2026-08-25）

規劃期十一輪之後，三問的答案與 [規劃交付](https://github.com/ruan6047/ai-workflow/issues/138#issuecomment-5404799028)
初版已有實質差異。**送閘門前更新，⛔ 不沿用舊答案。**

### 一、痛點是什麼

卡開完之後規則變了，⛔ 沒有任何動詞會回頭問「它現在還合規嗎」。

⭐ **研究期當場量到三個活例，全部無人發現**：
1. `1531666`（2026-08-21）改 `open` 初始狀態 ⇒ 14 張既有卡當場不合規，**沉默 4 天**。
2. `6325ae2`（2026-08-11）起 `open` 寫路由標記 ⇒ **50 張殘餘 ＋ 16 張規則生效後仍缺**，**沉默 14 天**。
3. ⭐⭐ **41 張卡（活卡 24、其中 21 張在 `💡需求`）`amend` 構造上打不到**，⇒ 它們躺在待辦池裡看起來可做，
   **一動就撞牆**；已在那裡至少 21 天。

⚠️ 而規則變更的基礎發生率實測 **約每 3–4 天一次**（最近 20 天 6 次）。

### 二、成功怎麼觀察

`wfcli doctor --conformance --owner ruan6047 --project 4` 跑得出一份報告，且：

1. **可達性先分**：`unreachable = 41`（活卡 24），逐張列出且與其他不合規項分開。
2. **歸因正確**：14 筆 `open_initial` 標 `rule_changed`（⛔ 不是 `channel_bypassed`）；
   33 筆標 `tool_cannot_read`；16 筆缺路由標記標 `writer_nonconformant`；
   41 筆讀不出建立時刻標 `undecidable`。
3. **欄位層獨立區段**：孤兒欄位 `分支／worktree` 出現在該區段，⛔ 不是 41 筆逐卡 findings。
4. ⭐ **可證偽預測**：`aiwf#105`（射程已擴充涵蓋這 41 張）落地後 `unreachable` **應為 0**。

⇒ 四項都是可執行指令或可對帳的數字，⛔ 沒有主觀判斷。

### 三、最大的未驗證前提

**⛔ 不是「報告有沒有用」——那一項研究期已量掉**：原始 200+ 筆經歸因後降到個位數待辦，
76% 不判定不傷可讀性（不判定者構造上不在待辦集合裡）。

⭐ **現在最大的未驗證前提是：`writer_nonconformant` 這一類指得出來卻追不下去。**
實測 16 張卡在規則生效後仍缺路由標記，而要查根因需要「這筆是哪個版本的工具寫的」，
⛔ **狀態面根本不記錄**。⇒ 本卡能報出這一類，**但報出來之後沒有下一步**。

⚠️ 若需求方認為「指得出來但追不下去」的一類不值得列，本卡的第 (d) 類就該降為警示或移除
——**那是需要裁定的，⛔ 不是我能自己決定的**。

---

⇒ **以上三問請需求方批註放行**（canonical §3.1：T3 須需求方批註放行後才進 `📥Backlog`）。


## Comment 5405269502 · 2026-08-25T04:33:20Z

## T3 規劃閘門：需求方批註放行（2026-08-25）

本則由 PM 依需求方於本次 session 的口頭裁定「放行」逐字轉錄寫入，⚠️ 帳號為需求方本人的 token。

canonical §3.1 對 T3 要求「**核心痛點三問**非同步輕質詢…需求方批註放行後才進 `📥Backlog`」。
三問（更新版）見 [issuecomment-5405240624](https://github.com/ruan6047/ai-workflow/issues/138#issuecomment-5405240624)。

### 一併裁定：`writer_nonconformant` **保留為完整一類**

PM 送閘門時把它列為最大未驗證前提（「指得出來卻追不下去」）。查證後**該說法過重**：

- 狀態面確實沒有工具版本可查——`cli/pyproject.toml` 的 `version` 自 2026-08-04 起
  凍在 `0.1.0` 未曾 bump、`wfcli` **沒有 `--version`**、Log 行只寫 `by wf-cli`。
- ⭐ **但追得下去**：研究期已用 commit 時序追出那 16 張的形狀
  （[issuecomment-5404887674](https://github.com/ruan6047/ai-workflow/issues/138#issuecomment-5404887674)）。
  缺的只是「為什麼」，而那是 git 考古，⛔ 不是不可能。

**保留的理由**：它是五類中**唯一分得出「還在持續產出新壞卡的洞」與「既有存量損害」**的一類。
⇒ 已補一條驗收：每筆 `writer_nonconformant` finding 須自帶 `rule_epoch` 與該卡建立時刻
（op `f754033d`）。

⚠️ 版本缺口本身（無 version／無 `--version`）**不在本卡射程**，僅記錄，⛔ 未開卡。

**⇒ 放行，進 `📥Backlog`。**


## Comment 5405395872 · 2026-08-25T04:52:07Z

## ⛔ 更正：本卡 issuecomment-5404979025 的「不可達」講得太滿

`aiwf#105` 研究第二輪（[issuecomment-5405392222](https://github.com/ruan6047/ai-workflow/issues/105#issuecomment-5405392222)）
以逐動詞讀碼＋三組 `amend --dry-run` 實跑，推翻了本卡先前的兩句話。

### 一、⛔ 「24 張活卡的寫入通道打不到」——過重

準確的分佈（實跑）：

| 動詞／旗標 | 對那 41 張 |
|---|---|
| `assign` | ⛔ 打不到（`assign_cmd.py:179` 對**目標卡**走嚴格 `parse_block`） |
| `amend --spec-baseline`／`--initiative`／`--resources`／`--core-pain`／`--acceptance`／`--verification` | ⛔ 打不到（各自需要對應章節或標頭行） |
| **`amend --brief`** | ✅ **打得到 40/41**（28 張缺標頭：rc=0；12 張連 `## Log` 都沒有：**也 rc=0**；僅排版損壞那 1 張被拒） |
| `handoff`／`review`／`checkpoint`／`deploy-declare`／`deploy-state` | ✅ 打得到（只做 `append_log_line`，而它逐字「沒有該區段就新增一個到 body 尾端」） |

⇒ ⭐ **擋人的是各個 `amend_*` 純函式各自的前提，⛔ 不是一道全域閘門。**

### 二、⛔ 「這會擋住 `aiwf#130` 的 S5——那 24 張的 `amend --brief` 必然失敗」——**完全錯**

實測 40/41 通過。**S5（既有卡簡介回填）沒有被擋。**
⚠️ 而 `amend_brief` 的插入錨點正是 `aiwf#134` 為既有卡設計的「第一個 `## ` 章節之前」
⇒ 它**構造上就繞過**缺標頭與缺 Log 兩種壞法。⭐ S1 當初那個設計決定，今天證明是對的。

### 三、⇒ 本卡的 `reachability` 軸要改寫，⛔ 不能只有二值

`reachable | unreachable` 這個二值**表達不了**上表——同一張卡對某些動詞可達、對某些不可達。

⇒ **改為 `reachability: dict[verb_or_flag, bool]`**（或至少 `reachable_for: list[str]`），
且報告須說**哪個動詞打不到**，⛔ 不是「這張卡打不到」。
⚠️ 理由是可操作性：「`assign` 打不到」的處置（先修卡才能派工）與
「`--resources` 打不到」的處置（該欄位暫時改不了）完全不同。

### 四、⭐ 真正的阻塞是 `assign`

那 41 張裡的 **21 張活卡（`💡需求`）今天無法被認領**——⛔ 不只是改不了，是**開不了工**。
⚠️ 該結論為**讀碼**所得，⛔ 未實跑（`assign` 無 `--dry-run`，實跑會真寫）。
⇒ 驗證要求已寫進 `aiwf#105`：執行階段以拋棄式卡驗證，⛔ 研究期不對真實卡試寫。

⇒ 卡面驗收將依此更正。


## Comment 5407338420 · 2026-08-25T08:03:49Z

## 📌 驗收條件與驗證的完整原文封存（2026-08-25，卡面精簡前）

⚠️ **不可變紀錄。** 卡面即將改為「判準＋指向本則的連結」，原文一字不刪保存於此。

**為什麼現在做**（實測，⛔ 非預防性潔癖）：`amend` 把被改欄位**全文寫進 Log 兩遍**（`_fold` 逐字「不截斷：Log 是唯一還原點」）⇒ 本卡驗收 6,348 字元 ⇒ **每改一次付 12,696**。
本卡 body 已 68,521、amend 11 次，⇒ **只剩 4 次驗收 amend 的餘裕**就會撞上 GitHub body 上限（實測 ~130,000）。⚠️ 而 `aiwf#105` 今天已經撞上並**永久不可寫**。
⇒ 現在壓到 ~1,200 字元：本次付 7,748，之後每次僅 ~2,400 ⇒ **可再改 22 次**。

---

### 驗收條件（25 條，原文）

**A1.** doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復。⚠️ 分層依既有形狀：判定放 doctor.py（純函式、不碰 gh），取卡放 doctor_cmd.py（既有 list_items／resolve_project／find_item_by_card_id，實測 :20／:169-170／:221-222）。

**A2.** ⭐ **報告須逐張歸因，值域恰為五類**（⛔ 三類不夠，實測逼出後兩類）：`tool_cannot_read`（解析失敗 ⇒ 修工具）／`undecidable`（建立時刻不可得 ⇒ ⛔ 不猜）／`rule_changed`（卡早於規則 ⇒ 依 disposition 處置）／`writer_nonconformant`（⭐ 卡**晚於**規則卻仍不合規、且經正規通道建立 ⇒ **查寫入端**）／`channel_bypassed`（欄位被手搬、無對應事件 ⇒ 補跑動詞）。

**A3.** ⭐ **判準順序不可換**：tool_cannot_read → undecidable → rule_changed → writer_nonconformant → channel_bypassed。⇒ 理由：前兩者是**我們自己的侷限**，⛔ 不得讓它們變成對卡或對人的指控。實測支持：41 張不合規中 34 張屬 tool_cannot_read（issuecomment-5404753163）。

**A4.** ⭐ **報告須先分可達性、再談合規性；而可達性是「逐動詞」的，⛔ 不是卡的二值屬性**（⛔ 更正本卡 issuecomment-5404979025 的二值設計，依 aiwf#105 issuecomment-5405392222 的實跑）。⇒ 欄位形狀為 `reachable_for: list[verb_or_flag]` 或等價映射，報告須說**哪個動詞打不到**。⚠️ 理由是可操作性：「assign 打不到」的處置（先修卡才能派工）與「--resources 打不到」的處置（該欄位暫時改不了）完全不同。實測分佈（2026-08-25，母體 193 張中 41 張至少一項不可達）：`assign` ⛔（assign_cmd.py:179 對目標卡走嚴格 parse_block）；`amend` 的 --spec-baseline／--initiative／--resources／--core-pain／--acceptance／--verification ⛔；**`amend --brief` ✅ 40/41**（28 張缺標頭 rc=0、12 張連 ## Log 都沒有也 rc=0，僅排版損壞 1 張被拒）；`handoff`／`review`／`checkpoint`／`deploy-declare`／`deploy-state` ✅（只做 append_log_line，而它逐字「沒有該區段就新增一個到 body 尾端」）。⭐ **真正的阻塞是 `assign`**：那 41 張裡 21 張活卡（💡需求）今天無法被認領。⚠️ 該項為讀碼結論，⛔ 未實跑（assign 無 --dry-run）⇒ 驗證須以拋棄式卡進行，⛔ 不對真實卡試寫。⛔ **並更正**：先前寫「這會擋住 aiwf#130 的 S5」為**錯誤**——S5 走 `amend --brief`，實測 40/41 通過，未被擋。

**A5.** ⭐ **可證偽預測須寫進交付**：本卡上線時 `unreachable = 41`（活卡 24）；`aiwf#105`（其射程已於 2026-08-25 擴充涵蓋這 41 張）落地後**應為 0**，否則兩者之一有缺陷。⛔ 不得只報一個數字而不說它應該往哪走。⚠️ 交付須同時記錄取樣時刻與當時 aiwf#105 的狀態。

**A6.** ⭐ **每個 rule_epoch 必須帶宣告過的 disposition，⛔ 不能只有時刻**：`migrate`（殘餘應清掉 ⇒ 報告逐張列出）或 `accept_as_legacy`（需求方已裁定不追溯 ⇒ 報告**只給一行摘要數字**，⛔ 不逐張列）。⚠️ 依據：實測規則變更約**每 3–4 天一次**（最近 20 天 6 次），且殘餘**只累積不清除**——26a0149／6325ae2（2026-08-11）的殘餘至今 14 天原封不動（107 張缺標記、活卡 38 張）。⇒ 沒有 disposition，rule_changed 桶會變成下一個 190，與本卡要解的問題同形。

**A7.** ⭐ **rule_epoch 的值須釘「檢查所依據的那個構件」落地的完整 ISO-8601 時刻**，⛔ 不是日期、也⛔ 不是「大家覺得規則何時開始」的那個 commit。實測教訓：wf-routing 的規則卡是 26a0149（13:01:38），但標記字面由 6325ae2 引入（18:29:56），晚 5.5 小時；用日期粒度會把 21 張誤判，用正確時刻是 16 張。

**A8.** ⭐ 卡的「存在時刻」取值優先序：(1) 卡面 Log 的 `open by` 事件時戳；(2) Issue 的 createdAt；(3) 都沒有 → undecidable。⚠️ 條文須釘死 (2) **只能用於比較 2026-08-04 之後的 epoch**——遷移卡的 Issue 建立於 08-04 而工作早於它，用它比更早的規則會誤判成 writer_nonconformant。⚠️ 取 createdAt 須**擴既有 list_items 查詢**，⛔ 不得加第二次抓取（會違反 doctor_cmd.py:167-183 的「同一次抓取」紀律）。實測母體：41 張無 open by 行（21 首筆 handoff／12 完全無時戳事件／8 assign；活卡 25 張）。

**A9.** ⭐ 通用機制的做法是**把三個既有掃描已共用的形狀抽出來，並讓它們成為第一批實作**，⛔ 不是再蓋第四個單一形態。三個是：legacy_authority_notes（doctor.py:1255）、brief_drift（:1298）、**state_face_drift（:1574——生產碼 0 呼叫端，接線屬 aiwf#65 明列而從未開過的「後續卡」）**。共用形狀含：純函式 audit_X(card_bodies)→XReport、status scanned／not_scanned（⛔ 未掃描不得讀成乾淨）、scanned_cards 記母體數、findings 與 routine_gaps 分開。

**A10.** ⭐ 抽取時**共用信封、⛔ 不共用 finding 型別**：三者攜帶資訊不同（timestamp／op_id／field_name vs reason vs verdict／expected／actual／rule），併型別會損失資訊。三者**都已有 card_id** ⇒ Protocol 約束即可。⚠️ 實測 dataclasses.asdict 對 list[Protocol] 正常遞迴、json.dumps 成功 ⇒ --json 輸出面無風險。

**A11.** ⭐ **改寫既有 render_state_face_drift（doctor.py:1625）使其依 cause 分流處置文案**：現行每筆 drift 無條件輸出「補跑對應的 wfcli 動詞…勿手動搬看板」，⇒ 對 rule_changed 的卡那是**錯誤的指控**。保留既有的「一致／漂移／不判定＋佔比」統計行與「偵測不等於強制」段（後者指名強制面承接者是 aiwf#48）。⚠️ 交付須附變更前後逐字對照，⛔ 不得混在新功能裡帶過。回歸基線：`uv run pytest tests/test_doctor.py -k drift -q` ⇒ **31 passed**（d4ba7ce5；⛔ `-k state_face` 選到 0 支，別用）。

**A12.** ⛔ **不得把 run_doctor 的 card_bodies 參數與掃描用的卡面合成一個**——doctor.py:1822-1827 逐字裁定：那個參數餵給 evaluate_cleanup_guard，順手填上會**沉默地改變 --cleanup-preview 的判定**。⭐ 正解是「同一次 list_items、多個獨立消費者各帶自己的參數」。

**A13.** ⭐ 基線清冊改用本卡自量的數字並附方法與取樣時刻：母體 193 張、不合規 41 張（21%），歸因為 tool_cannot_read 34／card_deficient 7，而 7 張中僅 **2 張非終態**。⛔ **不得引用 aiwf#136 的「161 張中 7 張」**。⚠️ 清冊須逐張帶歸因欄。

**A14.** ⚠️ 接線 state_face_drift 的兩個已知常態須逐字寫進交付：(1) **76% 不判定**（62 張未結案中 47 張，主因 handoff_status_not_in_log 45），其修法「handoff Log 行自帶 stage/status」**今天沒有承接卡**（aiwf#54 的驗收是「第一個遠端寫入帶載荷」，⛔ 不涵蓋 Log 行內容）；(2) **14 筆 open_initial 屬 rule_changed 而非 drift**（成因 1531666，2026-08-21；實測 14/14 開卡日早於該日）。

**A15.** ⚠️ 條文須指名一個本卡**解不掉**的限制：writer_nonconformant 指得出來但**追不下去**——狀態面不記錄「這筆是哪個版本的工具寫的」。實測 16 張卡在規則生效後仍缺 wf-routing 標記（開卡時刻橫跨 2026-08-12T00:11→08-15T10:07，抽驗 5 張全為「有路由行、無標記、Log 完整」），⛔ 根因未查出且本卡不查。

**A16.** ⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。

**A17.** ⚠️ 與既有 legacy_authority_notes 的關係由「合流或劃界」改為**抽取**。⚠️ 且該掃描的既有立場逐字是「報的是**留痕強度不足，不是授權無效**」⇒ 其 findings ⛔ **不進待辦集合**，報告須明示這一點（實測 11 張，本卡曾一度把它們誤算進待辦）。

**A18.** ⚠️ 旗標命名：簡介漂移目前掛在 --legacy-authority-notes 底下（doctor_cmd.py:121／:167 同一個 if），而該旗標 help（:54-55）⛔ 一個字沒提簡介漂移。改名為 --conformance（實查 CI／腳本／文件 0 命中，⛔ 不弄壞自動化），保留舊名為 deprecated alias。交付須明說連帶修正是不是刻意的。

**A19.** ⛔ 授權邊界：執行中若發現**必須修改**本卡未宣告的檔（如 validation.py／card.py），依 canonical §3.2「停 → 寫阻塞發現 → 由需求方裁決」，⛔ 執行者不得自行擴權。

**A20.** ⚠️ 與 aiwf#137（S7a）的介面：S7a 已合併時把 service_goal_still_served 納入檢查面；未合併時明列為**已知缺口**。⭐ 兩張寫入集不相交、可真平行；⛔ 先前「S7a 先」已作廢。

**A21.** 回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）。

**A22.** ⚠️ 交付時須附「PM 單方面決定清冊」。

**A23.** ⭐ **欄位層掃描（與 per-card findings 正交）**：比對看板實際帶過值的欄位集合 vs `project.FIELD_SPECS`，列出 (i) **有值但未宣告的孤兒欄位**、(ii) 宣告了但零張卡有值的欄位。⚠️ 這不是某一張卡的問題，是**狀態面本身的形狀問題** ⇒ 報告須有獨立區段，⛔ 不得把 N 張卡各報一筆。實測基線（2026-08-25）：孤兒欄位 **1 個**＝`分支／worktree`（全形斜線；`FIELD_SPECS` 宣告的是 `分支worktree`），41 張卡有值、8 張兩欄都有值、33 張只有舊欄（其中 30 張是佔位 `—`）⇒ **真正讀不到的登記 3 張、非終態 0 張**；(ii) 實測 **0 個**。⚠️ 成因是遷移用 Ledger 欄名建欄、CLI 同日用自己的常數建了第二個（`registry.py:261` 逐字有 `分支／worktree` 欄名；`9ef3154` 的 FIELD_SPECS 從一開始就是 `分支worktree`），而 `ensure_fields` **冪等但只增不減** ⇒ ⭐ 每次欄位命名分歧都會留一個孤兒，而沒有任何東西會說。

**A24.** ⚠️ 稽核取值一律走 `wf_cli.project.list_items` 正規路徑，⛔ **不得用 `gh project item-list`**——`project.py:377-378` 逐字記載後者「對中文欄位名稱的 JSON key 有編碼錯誤」。⚠️ 本卡研究期 PM 十餘支探針全踩此坑（結論重驗後不變，但方法錯）。⭐ 且判定一律直接呼叫 `wf_cli` 的純函式（`audit_state_face_drift`／`validate_open_fields`／`resources.try_parse_block`／`card.split_at_log`），⇒ 盤點結果與守衛判定**同源**。

**A25.** ⭐ **`writer_nonconformant` 的 finding 必須自帶可追溯的兩個時刻**（需求方 2026-08-25 裁定：本類保留為完整一類）：(1) 該規則的 `rule_epoch`、(2) 該卡的建立時刻。⇒ 接手的人可直接做 git 考古比對寫入端的 commit 時序，⛔ 不用重新推導一次。⚠️ 依據：狀態面**沒有任何工具版本可查**——`cli/pyproject.toml` 的 `version` 自 2026-08-04 起凍在 `0.1.0` 未曾 bump，`wfcli` 也**沒有 `--version`**，Log 行只寫 `by wf-cli` ⇒ 「這筆是哪個版本寫的」構造上無解。⭐ 但**追得下去**：本卡研究期即以 commit 時序追出那 16 張的形狀（開卡於 2026-08-12→08-15、有路由行、無標記、Log 完整，見 issuecomment-5404887674）。⚠️ 該類的真正風險是 **epoch 精確度**（實測挑錯 commit 會讓 16 變成 21）⇒ 由既有的「epoch 須釘構件落地的完整 ISO-8601 時刻」那條驗收承接。⚠️ 本卡**不解決**版本缺口本身（無 version／無 --version），僅在條文中指名。

---

### 驗證（13 條，原文）

**V1.** 對至少 3 張真實既有卡（含一張 2026-08-04 遷移卡）實跑，附原始輸出。⛔ 不接受自造樣本。

**V2.** ⛔ 非阻擋的**負控**：對一張被判不合規的既有卡實跑 amend --dry-run 證明不受阻；handoff 無 dry 路徑，須明列原因與密封探針設計。

**V3.** ⭐ **五類歸因各取真實樣本證明**：rule_changed 取 14 筆 open_initial 中至少 3 張；tool_cannot_read 取 33 張帶後綴標題中至少 3 張；writer_nonconformant 取 16 張缺 wf-routing 中至少 3 張；undecidable 取 41 張無 open 行中至少 3 張；channel_bypassed 母體中實測 **0 筆** ⇒ 須**明說是零筆**並以構造樣本證明該分支可達，⛔ 不得靜默略過。

**V4.** ⭐ **判準順序的變異檢驗**：把 tool_cannot_read 從第一順位移到最後，證明那 34 張會改被報成其他類（即順序真的承重）。⛔ 只跑正確順序是零資訊。

**V5.** ⭐ disposition 兩種取值各驗一次：migrate 的 epoch 其殘餘**逐張列出**；accept_as_legacy 的 epoch **只出現摘要行、⛔ 不逐張**。附兩份輸出對照。

**V6.** ⭐ createdAt 退路的邊界：取一張 2026-08-04 遷移卡，證明它對 08-04 之前的 epoch **落 undecidable 而非 writer_nonconformant**。⛔ 只驗 happy path 是零資訊。

**V7.** ⭐ state_face_drift 接線的**前後對照**：附接線前（直接 import 呼叫）與接線後（wfcli doctor 實跑）的輸出，證明那 14 筆不再被報成 drift。⛔ 只附接線後是零資訊。

**V8.** ⭐ 掃描結果與基線清冊**逐張**對帳，差異逐筆附原因；⛔「掃到 N 張」不算。同時記錄母體數與取樣時刻。

**V9.** ⭐ 證明對本卡未宣告的檔零寫入：附本卡分支對 validation.py 與 card.py 的 git diff 為空（附指令與輸出）。⛔ 自述不算。

**V10.** ⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因；⛔ 標不出原因者代表驗得了、不得列入。

**V11.** ⭐ **可達性判準的變異檢驗**：取 41 張中至少 3 張（三種成因各一）以 `amend --dry-run` 實跑，附拒收原文；再取一張 reachable 的真實卡證明**不誤報**。⛔ 只驗 unreachable 那側是零資訊。

**V12.** ⭐ **欄位層掃描的負控**：構造一個「宣告了但零卡有值」的情形證明 (ii) 分支可達（實測母體為 0，⇒ 不構造就永遠測不到）；並證明孤兒欄位 `分支／worktree` 被列在**獨立區段**而非逐卡 findings。

**V13.** ⚠️ 證明本卡的盤點與守衛同源：附至少一項量測，其結果由**直接呼叫 wf_cli 純函式**與**經 wfcli doctor 輸出**兩條路徑取得且逐字相同。⛔ 只跑一條無法排除自寫判定與工具判定不一致。


## Comment 5415168406 · 2026-08-25T18:51:40Z

## 裁定：授權本卡擴 `cli/src/wf_cli/project.py`（A6 的 `createdAt` 取值來源）

交付報告第 10 節列的第一項阻塞，裁定**授權**，理由三點皆為實跑取得：

1. **零衝突成本**。以 `wf_cli.resources.find_conflicts` 對全部非終態卡實跑，`project.py` 的**持有者為 0 張**。⇒ 授權不排擠任何人。
2. **不授權的代價是虛的觀測**。85/237 findings 落 `undecidable`，而交付報告自己逐字寫：「那些卡不是『時刻不可得』，是**我們沒去拿**」。⇒ 留著它等於讓一個可解的缺口長期偽裝成不可判定。
3. **判準與守衛已就緒**。`predates_rule` 對 cutover 前的 epoch 一律回 `None`、M20/M21 兩條變異釘住 `created_at_available` 的恆真／恆假 ⇒ 接上來源即生效，⛔ 不需重新設計。

**射程限定**：只加 `_LIST_ITEMS_QUERY` 的 `createdAt` 與 `ItemSnapshot` 的對應欄位。⛔ 不改 `list_items` 的呼叫次數、⛔ 不改欄位快取策略。

⚠️ **併帶提醒（⛔ 不擴射程，只登記）**：`WF-CARD-BRIEF-BACKFILL1` 的研究輪實測 `project.py` 的 `ensure_fields` 在零建立時仍會第二次呼叫 `list_fields`，該次**102 點／5.2 秒**，佔單次寫入動詞成本的 92%。⇒ 若動這支檔時順手看到，登記為另一張卡的證據，本卡**不順手修**。

## 另兩項阻塞的處置

- **V2 的 handoff 密封探針**（需建拋棄式真實卡）：⛔ **本輪不做**。理由：它要往 Project 寫一張真卡，而本卡是唯讀的事後檢查卡，射程不含寫入。⇒ 登記為未驗並標明原因（canonical §6.4.2 的「驗不了」類）。
- **`WF-MARKER-SCOPE-CLEARANCE1`（#30）寫入集完全相同**：#30 今日仍是 📥Backlog／未認領 ⇒ 無活衝突。派工 #30 之前須先讀本卡的交付。

## 對 A14 被推翻的裁定

⭐ **A14 的設計是對的，被推翻正是它的價值。** `assign` 軸 41→5 證明 `WF-RESOURCE-HEADING-SUFFIX1` 有效；`amend --core-pain` 軸 42 張打不到是**本卡的機制才看得見的東西**。裁定：**把「可達性逐動詞」留在 doctor 裡當常態量測**，⛔ 不退回成單一數字。

## 41 張空核心痛點的裁定

⛔ **不開卡，也不視為 `WF-RESOURCE-HEADING-SUFFIX1` 的缺陷。** `card.py` 的 `restore_migration_header` docstring 逐字：「⛔ **只補結構與可溯的值，不產生內容。** 章節一律留空 ⇒ 補完之後事後掃描仍會把它們報成『缺核心痛點／缺驗收』，**那是對的**，⛔ 不得視為本操作沒做完。」⇒ 那是**記錄在案的刻意結果**。

⚠️ 而交付報告說它們「執行者動不了」——實跑複驗：`amend --brief --dry-run` 對其中 4 張**全部 rc=0**（`OPS-STATE-PLANE-MIG1`／`DEV-CI-RED-OWNERSHIP1`／`INIT-PRODUCT-UX`／`ML-FIELD-OF1`）⇒ 打得到。真正動不了的只有 `--core-pain` 那一條軸，而那是**設計如此**：核心痛點是需求方的，執行者本來就不該代寫。

⇒ 那 41 張改列為 `WF-CARD-BRIEF-BACKFILL1` 的**最壞樣本子集**：它們的唯一素材是 `功能` 欄一句話（0/41 有驗收或驗證、body 平均 2,770 字元 vs 全母體 8,895）⇒ 為它們寫的簡介在構造上最可能退化成摘要，正是該卡要測的東西。

---
以上由 PM（Claude Opus 5@Claude Code）以需求方的 token 發文；裁定內容轉錄自需求方在 2026-08-26 session 的逐字指示「①②③ 都動」（①＝授權 #138 擴 project.py）與「如果等等有要裁定的麻煩直接幫我跑」。⛔ 合併與部署不在此授權內。

## Comment 5422113758 · 2026-08-26T07:36:22Z

<!-- wf-review-event:v1 card_id=WF-POSTHOC-CONFORMANCE1 source_sha=2470738def020c0dd4304545ec237dea95759fe6 attempt_id=WF-POSTHOC-CONFORMANCE1-e0-2470738def020c0dd4304545ec237dea95759fe6 -->
## 查核裁決：APPROVE

- 卡：`WF-POSTHOC-CONFORMANCE1`　attempt_id：`WF-POSTHOC-CONFORMANCE1-e0-2470738def020c0dd4304545ec237dea95759fe6`
- 查核者：跨家族查核者（身分未自述；需求方於對話中轉貼、PM 逐字轉錄）　escalation_epoch：0
- source_sha：`2470738def020c0dd4304545ec237dea95759fe6`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-26T15:36:21+08:00

### self_run（查核者實跑）

- `清除 PR worktree 的 __pycache__ 後重跑`
  - rc=0
- `cd .claude/worktrees/posthoc-conformance1/cli && uv run wfcli doctor <worktree> --registry none --conformance --owner ruan6047 --project 4`
  - rc=0
- `真實看板反事實量測（移除 CREATED_AT_TRUSTED_FROM）`
  - rc=0：44 筆全受樓地板影響；43 → rule_changed、1 → writer_nonconformant
- `真實 GraphQL 比對 203 筆 content.createdAt vs ProjectV2Item.createdAt`
  - rc=0：content.createdAt ≤ ProjectV2Item.createdAt 全數成立、無缺值與反向、最大差 3 秒
- `created_at_available 記憶體反注兩方向`
  - rc=0：兩個原分支斷言皆轉紅；4 個針對性測試通過
- `uv run pytest -q`
  - rc=0，1218 passed
- `git diff --check 4dd63dadc16a1626e81e2d6c50922f4137bf220a 2470738def020c0dd4304545ec237dea95759fe6`
  - rc=0

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-POSTHOC-CONFORMANCE1-e0-2470738def020c0dd4304545ec237dea95759fe6
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
