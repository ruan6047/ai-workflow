# #154 WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1 ensure_fields 會送 field-create 而它被排在 assign 的能力閘門之前
- state: closed  created: 2026-08-26T09:13:43Z  closed: 2026-08-26T20:05:55Z
- url: https://github.com/ruan6047/ai-workflow/issues/154
- comments: 6

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；要把一個既有函式拆成唯讀取值與建立兩條路徑，而它是所有寫入動詞的共用前置；失敗模式是靜默寫到錯的 field id（動詞照樣 rc=0）⇒ 須自己看出兩條路徑的回傳必須等價，⛔ 非機械替換。）　查核：待指派（建議 高階型；動的是所有寫入動詞共用的前置＋一個逐字記載為刻意的既有行為；查核者須獨立判斷「把它改成唯讀」有沒有讓某個動詞在該建欄位時不建，而該路徑在正常環境構造上跑不到（需刻意造欄位缺失）。屬跨家族查核。）
- Initiative：—　spec 基線：b169c2424c0401c169104312f2fa807c01345feb
- DB：db_scope=none
- 服務的原始目標：ROADMAP §0 目標 1「防止低級事故」——判準逐字「有機械執行者會擋下它」。今天「閘門前零寫入」是每個呼叫點各自的紀律，⛔ 沒有任何機制擋得住下一個人把閘門排在 ensure_fields 之後。

## 簡介
<!-- card-brief:begin -->
把 ensure_fields 改成預設唯讀，讓「閘門前零寫入」成為函式的性質而不是每個呼叫點各自的紀律。**適用時機**：要主張某個 wfcli 動詞的拒收路徑零寫入時；或要搬動 ensure_fields 的呼叫點時。⛔ 非射程：不改 handoff（`WF-STAGE-PITFALL-LIST1` 已就地修好該實例）、⛔ 不改 list_fields 的查詢方式（那是 `WF-CLI-ENSURE-FIELDS-DOUBLE-READ1`）、⛔ 不改 FIELD_SPECS。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：**`project.ensure_fields` 會送 `gh project field-create`，而 `assign` 把它排在能力閘門之前 ⇒ 被閘門拒收的 `assign` 仍可能已經建立 Project 欄位。** 這不是推測：同一個形狀在 `handoff` 上已由跨家族查核者以空欄位 Project 探針**實際重現**（2026-08-26，PR #153 的 issuecomment-5421266988：`handoff rc=2`、`field_created_before_gate=True`、`project_state_unchanged=False`），並已在該卡就地修好。⚠️ 而 `assign` 這一側**至今未修**，且 `cli/tests/test_commands_mocked.py` 逐字把它記載成**刻意的**、明說「『絕對零寫入』不是本指令在所有情境下的保證」。⇒ 兩個動詞今天的保證強度不同，而差異只寫在測試註解裡。⭐ **併帶的可觀測後果**：既有測試以`深拷 runner.items`為比對面，⛔ 不含 Project 欄位定義 ⇒ 這類寫入在測試面上不可見；`handoff` 那次是查核者另建探針才看到的。⛔ 本卡不主張現行設計是錯的——它有就地記錄的理由；本卡主張的是**那個理由今天只在一個呼叫點成立，而函式本身不提供該性質**。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/open_cmd.py",
    "file:cli/src/wf_cli/commands/amend_cmd.py",
    "file:cli/src/wf_cli/commands/assign_cmd.py",
    "file:cli/src/wf_cli/commands/review_cmd.py",
    "file:cli/src/wf_cli/commands/handoff_cmd.py",
    "file:cli/tests/conftest.py",
    "file:cli/tests/test_gate_before_write.py",
    "file:cli/tests/test_commands_mocked.py",
    "file:cli/tests/test_pitfalls.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⚠️ 本清單於 2026-08-26 依 65 輪研究輪**改形狀**（需求方裁定）。⭐ **卡面 `功能` 欄與核心痛點的一個前提已被推翻，執行者與查核者一律以本清單為準。**
- [ ] **A0 ⛔ 核心痛點的「`assign` 逐字記載為刻意」被推翻——從來沒有那個理由。** `test_commands_mocked.py` 那段的**主詞是測試的保證範圍與用詞強度**（「因此不用那個更強的詞」），⛔ **全段沒有一句主張早建欄位有好處**。實查：`assign` 的呼叫位置來自 **2026-08-04 五動詞建檔樣板，無任何決策紀錄**。⇒ 兩動詞保證強度不同是**尚未收斂**，⛔ 不是刻意分歧。⚠️ **三處證據的位置逐字更正**（先前寫「三處就地註解」為誤）：**一處是 `aiwf#148` 的 commit body**（⛔ 不是就地註解），另兩處才是就地註解（`open_cmd` 記「本 repo 明令要消滅的形狀」、`amend_cmd` 記「既有缺陷」）。三處**沒有一處記成「應當如此」**。
- [ ] **A0b ⛔ 「這是第四次」的頻率歸納撐不起本卡，已改為直接觀測。** ⚠️ 頻率歸納正撞 ROADMAP §5 的明確禁止與 §0 第 3 問，而 A6 已承認**沒有受害者**。⇒ 撐得起的是本輪的直接觀測：**`WF-STAGE-PITFALL-LIST1`（`aiwf#148`）自己沒修完，而且沒有任何機械會告訴你沒修完**——實測其全部查核留言中 `_release_with_cleanup` 出現 **0 次**，而該函式內三條拒收在缺欄位世界下**執行期全部到得了**（見 A7）。⇒ 落在 ROADMAP §0 **目標 1**（不受「現在有人受害嗎」管轄）。
- [ ] **A1 ⛔ 射程是「六處改動、跨五個命令模組」，⛔ 不是「四動詞」。** 先前寫的「四動詞」與 A2 的 `60→2` **互相矛盾**——報告逐字：「採四處搬動時 **N = 15（strict 9）**；採**六處改動**時 **N = 2**」。⇒ 六處 ＝ 四處搬動（`open`／`assign`／`review`／`amend`）＋ **`handoff` 搬進 `write_status_face` closure** ＋ **`amend` 拆呼叫**；資源宣告含**五個** `*_cmd.py`。⚠️ AST 可見的拒收 13 條是**可見集合、⛔ 非母體**；行為面基線（`b169c242` 重量）**549 次動詞入口／137 次 rc≠0／60 次違規（strict 54）**。⛔ 先前的 491/114/57 是掛 `mod.run` 的數字（`checkpoint_cmd` 沒有 `run` ⇒ 只看得到 5 個動詞）。
- [ ] **A2 ⭐ 主力守衛＝行為型，AST 降輔助。** **掛法**：`COMMAND_MODULES` ＋ `build_parser()` 反查的動詞入口 func ＋ `functools.wraps`（涵蓋 **11 個動詞**）。**判準＝順序事實**：`ensure_fields` 是否早於本輪第一次真寫入；⛔ `ensure_fields` 自己送的 `field-create` 不得算成先前寫入。⭐ 實測鑑別力 **60 → 2**。⛔ **「弄紅 4 條既有測試」整句刪除**——那是擾動式觀測法的產物（1 條是原型沒加 `functools.wraps` 的 bug、3 條是擾動式的下限）；**不擾動世界的觀測法附帶紅測 0 條**（實測 `1267 passed／3 failed`，與基線逐條相同）。⚠️ 執行能力仍建議高階型，理由改為「**判準的邊界條件多，研究者自己連錯兩次**」（見 V13）。
- [ ] **A2d ⭐ AST 單獨不足的三個理由**：**(a) 靜默漏報** M-C 使 AST 報 0 且該檔從報表消失（行為型報 10）；**(b) M-B**——⚠️ **口徑須先講明**：若判準是「不能靠搬動修」，AST 是**誤報**；若判準是「拒收前不得呼叫**可能寫入**的 `ensure_fields`」，它其實是**真報**，而正解是改用唯讀的 `list_fields`。⭐ **本卡採後者**（第 3 輪已推翻「不可修」）⇒ ⛔ 不得把 M-B 稱為「守衛誤報」而不加限定；**(c)** ⛔ 「搬完後 AST 全 0」須更正——拿第 2 輪自己的 `r2fixed` 跑 **20 次，全 0 只有 10 次** ⇒ 那個對照**有一半是不決定性的產物**。
- [ ] **A2b ⛔ 守衛的執行位置：`cli/tests/`。** ruleset 實查 `main must be green`／`enforcement=active`／required context **`tests`**／`bypass_actors=[]`／`current_user_can_bypass="never"`，且 `ci.yml` 對 `push` 與 `pull_request` 都跑 `uv run --frozen pytest -q` ⇒ 放那裡**是真執行者**。⚠️ ⛔ **交付不得引用 `docs/DEV_AIWF_MINIMAL_CI1.md`**——它逐字仍寫「本 repo 沒有任何 required status check」，而 ruleset 建於 2026-08-13 ⇒ **該文件落後現實**。
- [ ] **A2c ⛔ AST 輔助守衛不交付**（2026-08-26 更正——先前這條預設它存在，而那是 PM 的第九處卡面錯誤：它既不在資源宣告的落點裡，也不在第 3 輪報告的交付形狀裡 ⇒ **卡面自我不自洽**）。執行者的理由採納：此時新寫一支**語意自訂**的 AST 掃描，其「基線 13 條」**不會是報告那一支的數字**，反而製造新的對不上。⭐ 並且 **A2d 主張「兩支都要」的唯一論證是 M-B，而 MB2／MB3 已把它量化**——該類拒收今天**從未被執行到**（MB2 把它換成 `raise 哨兵`，哨兵出現 **0 次**），一旦被執行到**行為型就抓得到**（MB3 使它每輪成立 ⇒ 守衛 rc=1、點名 33 條）。⚠️ **保留的事實**：不 descend 版的 AST 20 次全 13、descend 版 20 次得兩種答案且**修好之後的樹也會擲**（`r2fixed` 20 次只有 10 次全 0）⇒ ⛔ **不得把任何 AST 0 讀成 `handoff` 乾淨**（守衛旁第 7 件）。
- [ ] **A3 ⛔ 不採惰性 Mapping。** 它能做到「呼叫端字面一行不改」，但實跑**紅 5 條**（全落在 `aiwf#151` 剛交付的 `test_project_mocked.py`，且**紅得正確**），另有兩個不由測試表達的代價：`open` 的失敗面變差（先建 Issue 再炸 ⇒ 孤兒卡）、例外時點改變。⇒ **能，但不該。**
- [ ] **A4 ⛔ 資源敘述先前是第 2 輪舊版、與卡面 JSON 直接矛盾，已更正。** 正確集合為**三加二減**：**加入** `handoff_cmd.py` 與 `cli/tests/conftest.py`（守衛落點）；**移除** `test_commands_mocked.py` 與 `test_review.py`（⭐ **六處改動下這兩檔一字不改**）。⇒ 現行七項：五個 `*_cmd.py`（`open`／`amend`／`assign`／`review`／`handoff`）＋ `cli/tests/conftest.py` ＋ `cli/tests/test_gate_before_write.py`。⛔ **不含 `project.py`**（`ensure_fields` 本體不動，本卡只改呼叫時點）。實跑 `find_conflicts`：**25 撞／0 擋**。
- [ ] **A5 ✅ `aiwf#151` 已於 2026-08-26 合併**（`b169c242`，issue CLOSED）。⇒ **spec 基線由 `6148bd4` 更新為 `b169c242`**；⛔ 沒有東西要等，⛔ 先前的假設分析（「再退一次或被停卡」）全部刪除。
- [ ] **A6 ⭐ 交付必須逐字寫下最強的反面論據。** **多建一個凍結欄位是冪等且無害的**——⛔ 不寫錯值、⛔ 不弄丟資料、⛔ 不讓看板說謊；生產側**受害者 0**。`aiwf#148` 判 blocking 的理由是它**違反了閘門逐字宣稱的契約**，⛔ **不是建欄位本身有害**。⇒ 本卡能宣稱的只有「**收掉一個契約不一致**」。⛔ **先前這條結尾寫「價值論證只能建立在 A0b（第四次、無法防第五次）之上」，那與 A0b 及 A15 直接互斥，已刪除**——A0b 早已把頻率歸納換成直接觀測（`aiwf#148` 自己沒修完、且沒有任何機械會告訴你沒修完），⇒ 價值論證建立在**那個直接觀測**上。
- [ ] **A7 ⛔ `handoff` 的數字與修法皆須更正。** 既有測試套件裡 `handoff` 有 **11 條**（⛔ 不是 3 條）rc≠0 且 `ensure_fields` 排在第一次寫入之前（rc=2×1、rc=5×10，逐條見交付）。⭐ **修法比卡面想的簡單**：`fields` **只在 `write_status_face` 內被用到**（AST 與實跑皆可證）⇒ 整支 `ensure_fields` 搬進那個 closure 即可，實測 **11 → 0**。⛔ 並更正先前寫的「守衛須掛在 `run()`」——掛法是 parser 註冊的 func（見 A2）。
- [ ] **A8 ⚠️ 觸發條件不是 0。** 卡面說「今天觸發條件多常見」——實測 Project **#4 缺 0 欄**，但 **#1 與 #5 各缺 15 欄，是現成觸發實例**。生產側今天 0 的四類歸因：①部分成立（窗口窄）②⛔ 不成立（機制天天跑）③**成立且是主因**（比對面看不見欄位定義、生產無遙測）④⛔ 不成立但要標界線（只量欄位名集合，⛔ 不含 option 漂移與孤兒欄）。⭐ **窗口由 `FIELD_SPECS` 下一次成長開啟，而上一次成長距今 1 天。**
- [ ] **A9 ⛔ 整條前提拿掉——不需要缺欄位世界。** 判準是**順序事實**（`ensure_fields` 是不是排在本輪第一次真寫入之前），在**欄位齊全**的世界一樣成立。實測對照：不擾動觀測法 **549 runs／60 違規／附帶紅測 0**；擾動式（forget 一個欄位）**57 違規／附帶紅測下限 3**，且 **15 個欄位逐一試過換不掉那 3 條**。⇒ ⛔ 不必新寫任何測試、⛔ 不必挑欄位、⛔ 不必 `_world()` 比對面。
- [ ] **A10 ⛔ 級別與執行能力是兩個欄位，⛔ 不是同一句。** `級別` 值域 `T0–T4`、`執行能力` 值域 `主力型／高階型`。⇒ **(a) `級別` 維持 `T3`**；**(b) `執行能力` ＝ 高階型**，⛔ **理由不得寫「判斷密度回升」這種泛稱**（報告明文否決），須逐字列**三項具體**：**①** 「整套跑」判準的邊界條件研究者**連錯兩次**（`invocation_params.args` 被 `-p no:cacheprovider` 的值騙、`config.args` 被 `testpaths` 填滿）；**②** 噪音判準必須**方向非對稱**（對稱式會讓任何子集跑變紅）；**③** 六處改動中有**兩處非機械搬動**（`handoff` 搬進 closure、`amend` 拆呼叫）。⚠️ `amend` 無 `--exec-capability` 旗標 ⇒ 於 `assign --actual-capability 高階型` 落實並在偏離理由逐字引本條。
- [ ] **A11 ⭐ 守衛旁必須逐字列出八件「⛔ 不得由它綠燈推出」**（就地註解，⛔ 寫在 commit message 或交付報告不算）。**(1)** ⛔ 不得推出「`ensure_fields` 已是唯讀」——本卡只改呼叫時點；⚠️ 那句話**就寫在本卡的卡 ID 裡**；**(2)** ⛔ 不得推出「生產環境安全」——**守衛只掛 `FakeGhRunner`**，真 `GhRunner` 子類未窮舉；**(3)** ⛔ 不得推出「`ensure_fields` 具併發安全性」——本卡未改變也未驗證該性質（缺口記於 `WF_EVENT_IDEMPOTENCY1.md`）；**(4)** ⛔ 不得推出「所有寫入都在拒收之後」——守衛只看得到 gh 出口、⛔ 看不到 git 側寫入；**(5)** ⛔ 不得推出「殘餘的 N 條是缺陷」；**(6)** ⛔ 不得推出「本 repo 的同族問題已解決」（`root_cause_id` 全 repo 0 命中）；**(7)** ⛔ 不得把不 descend 的 AST 0 讀成 `handoff` 乾淨；**(8)** ⛔ 不得把 M-B 的「2→2 不動」讀成「守衛判它合法」（見 A2d）。
- [ ] **A12 ⛔ 驗收口徑是「逐字黃金值 ＋ 方向非對稱」，⛔ 不是 `≤N`、⛔ 不是 `==0`。** 報告逐字否決 `<= N`。實作：`_FROZEN: dict[tuple[str,int],int] = {("amend", 5): 2}`（鍵＝`(動詞, rc)`）；**方向非對稱**——**多出來的一律紅；少掉的只在整套跑時紅**（對稱式比對會讓任何子集跑變紅，那是實測的噪音源）。⛔ 並更正三處先前的轉寫錯誤：**(i)** 那兩條是 **`amend` rc=5**，⛔ **不是 rc=6**（`test_tier_write_failure_aborts_before_touching_body`、`test_exit5_message_points_to_record_unlogged_change`）；**(ii)** 分母是「**15 條裡 12 條**歸本卡且修得掉」，⛔ **不是「60 條裡」**——60 是**未修基線**；**(iii)** 15 條的組成是 12 修得掉 ＋ **1 條非違規** ＋ **2 條觀測盲點**。⭐ 那 2 條的成因：**測試自己 `monkeypatch.setattr(amend_cmd, "set_field_value", …)`** ⇒ 觀測面**必然**看不到那次寫入。⇒ 就地註解**必須寫出「為什麼看不到」，否則就是死條目**。
- [ ] **A13 ⚠️ 守衛失敗時 pytest 摘要行仍印 `passed`。** `pytest_sessionfinish` 設 `session.exitstatus` 的形狀讓**退出碼變 1、訊息在 stderr**，但摘要行仍是 `1254 passed`。⇒ 交付須就地登記這個限制，並⛔ **禁止在任何驗證指令裡接 `| tail`**（本 repo 已有同族事故）。
- [ ] **A14 ⛔ 明文：這是專用守衛，⛔ 不是涵蓋整個家族的通用機制**（需求方 2026-08-26 裁定的射程定位）。判準逐字只認「`ensure_fields` 有沒有排在本輪第一次真寫入之前」⇒ ⛔ **下一個「寫入早於閘門」的形狀它抓不到**。⚠️ `aiwf#148` 給本缺陷家族的 `root_cause_id` = `gate-placed-after-a-writing-precondition` **全 repo 0 命中**。⇒ ⭐ **本卡提供的是「`ensure_fields` 這個子形狀」的機械執行者（見 A2b），⛔ 不提供涵蓋整個家族的通用執行者。** ⛔ 先前寫的「本卡也不提供（任何機械執行者）」與 A2b 字面衝突，已更正。交付須逐字寫下這個界線。
- [ ] **A15 ⛔ 交付不得宣稱「防止了損害」。** A6 逐字維持且本輪第三度複驗成立：**多建一個凍結欄位是冪等且無害的**——⛔ 不寫錯值、⛔ 不弄丟資料、⛔ 不讓看板說謊；生產側**受害者 0**。⇒ 本卡能宣稱的只有「**收掉一個契約不一致**」（`aiwf#148` 判 blocking 的理由是違反閘門逐字宣稱的契約，⛔ 不是建欄位本身有害）。⚠️ ⛔ 亦不得以「這是第四次」的頻率歸納當價值論證（見 A0b）。

## 驗證

- [ ] ⚠️ 本清單依 65 輪研究輪填實。⭐ **V1 已在研究輪跑過並具鑑別力**、**V4 是守衛的變異檢驗，⛔ 不可省**。
- [ ] **V1 ⭐ 守衛本身就是缺陷復現，⛔ 不必另寫單條測試。** 把交付的守衛**原封不動**放上未搬動的 `b169c242` ⇒ 必須 **rc≠0 並列出 60 條**；搬動後 **rc=0 且安靜**。⛔ 只跑搬動後是零資訊。
- [ ] **V2 守衛覆蓋 `COMMAND_MODULES` 全部 11 個動詞的入口**（由 `build_parser()` 反查，**fail-closed**）。⚠️ ⛔ 不是 4 個、⛔ 不是 5 個——`checkpoint`／`deploy-*`／`doctor`／`snapshot` 都在內。交付附**基線 60 條的逐條輸出**（動詞／rc／nodeid／序列）。⛔ **不需要 `_world()` 比對面**（守衛不擾動世界）。
- [ ] **V3 負控**：帶合格輸入時欄位**確實被建立**。⛔ 沒有這條，「拒收路徑變綠」與「`ensure_fields` 被弄丟」在觀測面上長得一樣。
- [ ] **V4 ⭐ 三個突變，⛔ 不可省**：**M-A** 須轉紅（實測行為型 2→10）；**M-C** 須轉紅**且輸出與 M-A 相同**（實測；⛔ AST 版是 0 且該檔從報表消失）；**M-B ⛔ 須說明為什麼不動**——實測行為型 **2→2**，理由是**該拒收在既有測試裡從未被走到**，⛔ **不得讀成「守衛不誤紅」**，那是覆蓋不足的另一面。⭐ **並依 A2d 的口徑登記**：若該類拒收真的被走到，守衛會紅**而且紅得對**，正解是改用唯讀的 `list_fields`。⛔ 派審詞仍須逐字要求查核者獨立重跑 M-C。
- [ ] **V5 守衛的執行位置證明**：附釘死交付 SHA 的 CI run，證明該守衛**真的在 required check `tests` 裡跑**。⛔ 「有加測試」不算。
- [ ] **V6 回歸**：`pytest`（基線現場重量）、`contract_tool_reconcile --check` rc=0、`canonical_citation_scan` rc=0、`wfcli doctor` rc=0。⛔ 不得接管線。
- [ ] **V7 ⭐ 改為無條件事實**：`("project","field-list")` 在唯讀白名單上已是**死條目**（`aiwf#151` 已合併，`src/` 字面呼叫實查 **0 處**，只剩 6 處註解）。⇒ 依 repo 自己的「排除集不是垃圾桶」紀律，交付**要嘛刪掉它、要嘛就地寫明為何保留**。
- [ ] **V8 ⛔ 三輪無效證據的教訓必須被避開**：研究輪的第 36／39／40 輪「1254 passed」**全部無效**——`cp -R` 連 `.venv` 一起複製，而 `.venv/bin/pytest` 啟動器 `exec` 的是**來源樹**的 python ⇒ 三次測的都是未改動的樹。⇒ 交付的每一次「在副本上跑」都必須**先驗身分**（證明跑的是改過的那棵樹），⛔ 不得只看 passed 數。
- [ ] **V9 未驗清單依 canonical §6.4.2** 逐項標明原因。⭐ 本輪更新：**已消解兩項**——`_forget_field` 的普適性（不再擾動世界）、`amend rc=5` 那 2 次的分類（⛔ 不是分類未定，是兩條測試 monkeypatch 掉寫入函式 ⇒ 觀測面必然看不到）。**仍必列**：生產環境真實重現（需寫入權）；守衛長期噪音率（**`undecidable`**）；⭐ **`handoff --cleanup` 的 git 側寫入順序**——11 條全消掉，**但沒有一條是靠證明 git 側消掉的**；操作程序窮盡性；守衛 monkeypatch 有沒有改變既有測試語意；AST 的 10/3 覆蓋本輪未重量；**V14 本輪未跑**；真 `GhRunner` 子類未窮舉。
- [ ] **V10 ⛔ 只驗行為型的決定性**（2026-08-26 更正——先前的「AST 輔助連跑 20 次」那半句隨 A2c 一併刪除）。行為型須「**說明為什麼結構上不會不決定性**」（判定是 dict 相等、決策路徑無 `set` 迭代）＋ 至少 3 次 `PYTHONHASHSEED=random` 複跑逐字相同。
- [ ] **V11 ⭐ 行為面前後對照 ＋ 殘餘逐條具名**：基線 **549 runs／137 rc≠0／60 違規（strict 54）**；**四處搬動 → 15（strict 9）**；**六處改動 → 2**。⚠️ **兩份都要給**，⛔ 不得只報 2 而不說它需要六處。逐條具名（動詞／rc／nodeid／序列），並附 `ensure_fields` 呼叫次數 **482 → 437 → 402**（⭐ 六處改動順帶砍掉 80 次呼叫，16.6%）。
- [ ] **V12 ⭐ 子集跑不得變紅**，至少四格：乾淨樹整套 rc=0／乾淨樹 `-k` 子集 rc=0／注入假死條目整套 rc≠0／注入假死條目子集 rc=0。⛔ **沒有這條，守衛上線第一天就會被開發者關掉**（實測噪音源＝對稱式黃金值讓子集跑天天紅，非對稱判準解決）。
- [ ] **V13 ⭐ 「整套跑」判準本身的變異檢驗。** 研究者本輪**兩次寫錯**（`invocation_params.args` 被 `-p no:cacheprovider` 的值騙；`config.args` 被 `testpaths` 填滿）⇒ 交付須對**這個判準本身**做變異檢驗，⛔ 不得只驗守衛主體。
- [ ] **V14 ⭐ 負控要驗到「守衛沒被弄丟」。** 除 V3 之外再加一條：把任一處 `ensure_fields` **整個刪掉**時，既有測試必須轉紅——⛔ 否則「守衛綠 ＋ 功能壞」與「守衛綠 ＋ 功能好」長得一樣。⚠️ **本輪未跑此突變。**

## Log

- 2026-08-26T17:13:42+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-26T18:11:26+08:00 amend by wf-cli（op 959b2bd0）→ 驗收條件：原值「[ ] ⚠️ 刻意留白至研究輪產出。已知須被回答的四件：(1) 拆成「唯讀取值」與「建立」兩步之後，**呼叫端一行不改**做不做得到（若做不到，改動範圍會擴到五個動詞）；(2) `assign` 的既有行為是逐字記載為刻意的 ⇒ 改它必須先推翻那個理由，⛔ 不得逕行更動；(3) 與 `WF-CLI-ENSURE-FIELDS-DOUBLE-READ1`（同檔、執行中）的序位——⚠️ 該卡正在把 `list_fields` 換成原生 GraphQL 查詢，兩者對 `ensure_fields` 的改動會相交；(4) 既有測試以深拷 `runner.items` 為比對面而看不見欄位定義 ⇒ 比對面要不要一併換成封閉快照（`WF-STAGE-PITFALL-LIST1` 的 `_world()` 是現成樣板）。⭐ 留白依據：2026-08-26 的實測教訓，開卡時把尚未複驗的結論寫進驗收會被研究輪連續推翻。」→ 新值「⚠️ 本清單於 2026-08-26 依 65 輪研究輪**改形狀**（需求方裁定）。⭐ **卡面 `功能` 欄與核心痛點的一個前提已被推翻，執行者與查核者一律以本清單為準。** - [ ] **A0 ⛔ 核心痛點的「`assign` 逐字記載為刻意」被推翻——從來沒有那個理由。** `test_commands_mocked.py` 那段的**主詞是測試的保證範圍與用詞強度**（「因此不用那個更強的詞」），⛔ **全段沒有一句主張早建欄位有好處**。實查：`assign` 的呼叫位置來自 **2026-08-04 五動詞建檔樣板，無任何決策紀錄**。⇒ 兩動詞保證強度不同是**尚未收斂**，⛔ 不是刻意分歧。⚠️ 三處就地註解分別記成「不在本卡射程」「本 repo 明令要消滅的形狀」「既有缺陷」，**沒有一處記成「應當如此」**。 - [ ] **A0b ⭐ 這是第四次，⛔ 不是第二次。** 實例：`2026-08-11 assign`（只記未修）、`08-25 open --brief`、`08-25 amend --dry-run`（就地註解逐字稱「既有缺陷」）、`08-26 handoff`（R1-001）。⇒ **四實例、三種修法、⛔ 沒有一種防得住第五次。** 那是本卡改形狀的唯一理由。 - [ ] **A1 ⭐ 射程改為「四動詞 ＋ AST 守衛」，⛔ 不是「只修 `assign`」。** 實測 `open` 1／`amend` 2／`assign` 6／`handoff` 0／`review` 4，共 **13 個**拒收落在 `ensure_fields` 之後（AST，第一次寫入為界，含一層 helper 可達性）。⇒ 只修 `assign` 是把「靠人記得」從 5 處減到 4 處，**⛔ 不值得一張卡**。 - [ ] **A2 ⭐ 守衛必須放在 `cli/tests/`。** 實查：CI 對 push 與 PR 合併結果**都跑 pytest**，且 job name `tests` 是 **required check** ⇒ 放那裡的 AST 守衛**是真執行者**（ROADMAP §0 判準逐字「有機械執行者會擋下它」）。⛔ `contract_tool_reconcile` 與 `canonical_citation_scan` **不在 CI**，放那裡不算達成。研究輪實測該守衛：基線 **13 違規**／修後 **0**；`handoff` 兩邊皆 0（`aiwf#148` 已修）。 - [ ] **A3 ⛔ 不採惰性 Mapping。** 它能做到「呼叫端字面一行不改」，但實跑**紅 5 條**（全落在 `aiwf#151` 剛交付的 `test_project_mocked.py`，且**紅得正確**），另有兩個不由測試表達的代價：`open` 的失敗面變差（先建 Issue 再炸 ⇒ 孤兒卡）、例外時點改變。⇒ **能，但不該。** - [ ] **A4 ⛔ 資源宣告已更正**：`assign` 的零寫入斷言在 `test_commands_mocked.py`，⛔ **不在** `test_project_mocked.py`（卡面原宣告寫錯）。移除 `project.py` 與 `test_project_mocked.py`，加入四個 `*_cmd.py` ＋ `test_commands_mocked.py`／`test_review.py`／新守衛檔。實跑 `find_conflicts`：**0 筆會被 `assign` 擋下**。 - [ ] **A5 ⚠️ 與 `aiwf#151` 不相交、⛔ 不必等它。** 建議形狀的資源集不含 `project.py`；守衛在 `main` 單獨與合併結果上輸出相同 ⇒ 對 `#151` 成敗不敏感。⚠️ **但機械不會替你把關序位**——`#151` 的 owner 是佔位字串 ⇒ `is_owner_assigned=False` ⇒ `assign` 實跑 **0 筆會擋**。⛔ 卡面原寫的「宣告字串相同 ⇒ `assign` 硬退」機械上不成立。 - [ ] **A6 ⭐ 交付必須逐字寫下最強的反面論據。** **多建一個凍結欄位是冪等且無害的**——⛔ 不寫錯值、⛔ 不弄丟資料、⛔ 不讓看板說謊。`aiwf#148` 判 blocking 的理由是它**違反了閘門逐字宣稱的契約**，⛔ **不是建欄位本身有害**。⚠️ **卡面原本沒有寫這一點**。⇒ 本卡的價值論證只能建立在 A0b（第四次、無法防第五次）之上，⛔ 不得宣稱建欄位有害。 - [ ] **A7 ⚠️ `handoff` 只修了一半。** `_release_with_cleanup` 內仍有 **3 條**先於自身寫入的拒收落在 `ensure_fields` 之後（AST 一層推導，⛔ 未執行期重現）。⇒ 交付須決定：納入本卡、或明文交回 `aiwf#148`。 - [ ] **A8 ⚠️ 觸發條件不是 0。** 卡面說「今天觸發條件多常見」——實測 Project **#4 缺 0 欄**，但 **#1 與 #5 各缺 15 欄，是現成觸發實例**。生產側今天 0 的四類歸因：①部分成立（窗口窄）②⛔ 不成立（機制天天跑）③**成立且是主因**（比對面看不見欄位定義、生產無遙測）④⛔ 不成立但要標界線（只量欄位名集合，⛔ 不含 option 漂移與孤兒欄）。⭐ **窗口由 `FIELD_SPECS` 下一次成長開啟，而上一次成長距今 1 天。** - [ ] **A9 比對面只換 `assign` 那兩條。** 成本已量：`aiwf#151` 沒對 `FakeGhRunner.__init__` 加任何屬性 ⇒ `aiwf#148` 的 `_world()` 可直接複製。⚠️ **換比對面本身不會讓現有測試轉紅**，必須另外造缺欄位狀態（113 次拒收中只有 1 次落在缺欄位世界）。 - [ ] **A10 級別由 T3 降為執行 主力型**（需求方裁定）：機械搬動 ＋ 一支 AST 守衛，判斷密度低於原評估——原評估假設要拆 `ensure_fields` 本體，而 A3 已裁定不拆。查核維持**高階型／跨家族**。」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 需求方裁定依 65 輪研究輪改形狀：射程由「只修 assign」改為「四動詞＋放在 cli/tests/ 的 AST 守衛」（CI 的 required check tests 是真執行者）；A0 登記「assign 逐字記載為刻意」被推翻（那段主詞是測試的用詞強度、位置來自 08-04 建檔樣板無決策紀錄）；A0b 登記這是第四次；A6 要求交付逐字寫下「多建欄位冪等無害」這個卡面沒寫的反面論據；資源宣告更正（assign 的零寫入斷言在 test_commands_mocked.py 不在 test_project_mocked.py）。
- 2026-08-26T18:11:26+08:00 amend by wf-cli（op 959b2bd0）→ 驗證：原值「[ ] ⚠️ 同上留白。已知紅線三條：⛔ **不得只驗零建立情境**——實測 M1／M2／M3 三種錯誤實作在零建立情境全部 PASS、只在有建立情境 FAIL；⛔ **鍵集合相同不算通過**——off-by-one 與 option id 全錯兩種變異的鍵集合與型別都與正確版相同；⛔ **不得以「動詞還能跑」當通過**——失敗模式是靜默寫到錯的 field id，動詞照樣 rc=0。」→ 新值「⚠️ 本清單依 65 輪研究輪填實。⭐ **V1 已在研究輪跑過並具鑑別力**、**V4 是守衛的變異檢驗，⛔ 不可省**。 - [ ] **V1 缺陷復現（研究輪已跑通，交付須重跑）**：復用套件自己的 `fake_runner`／`_open_for_assign`／`_assign_argv`，在 `main ⊕ 8bfa088` 上必須**紅**（訊息逐字「拒收路徑上建了 Project 欄位（缺陷復現）」），搬動後**綠**。⛔ 只跑搬動後是零資訊。 - [ ] **V2 四動詞逐一**：`open`／`amend`／`assign`／`review` 各自的拒收路徑在缺欄位世界下 rc≠0 **且 Project 欄位 schema 逐位元不變**。⛔ 比對面須用封閉快照（`aiwf#148` 的 `_world()` 樣板），⛔ 不得只深拷 `runner.items`。 - [ ] **V3 負控**：帶合格輸入時欄位**確實被建立**。⛔ 沒有這條，「拒收路徑變綠」與「`ensure_fields` 被弄丟」在觀測面上長得一樣。 - [ ] **V4 ⭐ 守衛的變異檢驗，⛔ 不可省**：把任一個 `ensure_fields` 呼叫搬回拒收之前 ⇒ AST 守衛必須轉紅。並附**基線違規數**（研究輪實測 13）與**修後**（0）。⛔ 只報「修後 0」是零資訊。 - [ ] **V5 守衛的執行位置證明**：附釘死交付 SHA 的 CI run，證明該守衛**真的在 required check `tests` 裡跑**。⛔ 「有加測試」不算。 - [ ] **V6 回歸**：`pytest`（基線現場重量）、`contract_tool_reconcile --check` rc=0、`canonical_citation_scan` rc=0、`wfcli doctor` rc=0。⛔ 不得接管線。 - [ ] **V7 `_READ_ONLY_GH` 不得被動**（只改時點不改唯讀性）。⚠️ 但須登記一筆：`aiwf#151` 落地後 `src/` 對 `field-list` 的呼叫歸零 ⇒ **該白名單項成死條目**。 - [ ] **V8 ⛔ 三輪無效證據的教訓必須被避開**：研究輪的第 36／39／40 輪「1254 passed」**全部無效**——`cp -R` 連 `.venv` 一起複製，而 `.venv/bin/pytest` 啟動器 `exec` 的是**來源樹**的 python ⇒ 三次測的都是未改動的樹。⇒ 交付的每一次「在副本上跑」都必須**先驗身分**（證明跑的是改過的那棵樹），⛔ 不得只看 passed 數。 - [ ] **V9 未驗清單依 canonical §6.4.2** 逐項標明原因。⭐ 已知必列：`_release_with_cleanup` 那 3 條是 AST 一層推導、⛔ 未執行期重現。」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 需求方裁定依 65 輪研究輪改形狀：射程由「只修 assign」改為「四動詞＋放在 cli/tests/ 的 AST 守衛」（CI 的 required check tests 是真執行者）；A0 登記「assign 逐字記載為刻意」被推翻（那段主詞是測試的用詞強度、位置來自 08-04 建檔樣板無決策紀錄）；A0b 登記這是第四次；A6 要求交付逐字寫下「多建欄位冪等無害」這個卡面沒寫的反面論據；資源宣告更正（assign 的零寫入斷言在 test_commands_mocked.py 不在 test_project_mocked.py）。
- 2026-08-26T18:11:26+08:00 amend by wf-cli（op 959b2bd0）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/project.py", "file:cli/src/wf_cli/commands/assign_cmd.py", "file:cli/tests/test_project_mocked.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/commands/open_cmd.py、file:cli/src/wf_cli/commands/amend_cmd.py、file:cli/src/wf_cli/commands/assign_cmd.py、file:cli/src/wf_cli/commands/review_cmd.py、file:cli/tests/test_commands_mocked.py、file:cli/tests/test_review.py、file:cli/tests/test_gate_before_write.py」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 需求方裁定依 65 輪研究輪改形狀：射程由「只修 assign」改為「四動詞＋放在 cli/tests/ 的 AST 守衛」（CI 的 required check tests 是真執行者）；A0 登記「assign 逐字記載為刻意」被推翻（那段主詞是測試的用詞強度、位置來自 08-04 建檔樣板無決策紀錄）；A0b 登記這是第四次；A6 要求交付逐字寫下「多建欄位冪等無害」這個卡面沒寫的反面論據；資源宣告更正（assign 的零寫入斷言在 test_commands_mocked.py 不在 test_project_mocked.py）。
- 2026-08-26T19:10:07+08:00 amend by wf-cli（op 44d9286a）→ 驗收條件：原值指紋 sha256:94b352c7bb673576bbf6250b80dc1d224ae07027fa927c3a1921d8fad3b65654 (5097 bytes) → 新值指紋 sha256:93dff05ac6c51085ad79aeb670eee78959f34cd0df7432fc3298ac10186298ed (9144 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定第三次改形狀：主力守衛由 AST 改行為型（掛 491 次 run()，鑑別力 57→15 實測，涵蓋 handoff、M-C 繞不過去），AST 降輔助且須決定性；A0b 由頻率歸納改為「#148 沒修完且無機械告知」的直接觀測；A7 刪「未執行期重現」（三條全部重現 rc 2/2/5）；A10 拆開級別與執行能力；新增 A2b/A2c/A11/A12 與 V10/V11。
- 2026-08-26T19:10:07+08:00 amend by wf-cli（op 44d9286a）→ 驗證：原值指紋 sha256:80726c4e16df9b8de122e5df9f8f6f751d233b79e5f09d1d4f5d19aad04387c9 (2312 bytes) → 新值指紋 sha256:fcbcc65deb3fe0e0a699a56ace4f8413cec2cb6be3746457e10875a4b82eeff5 (3784 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定第三次改形狀：主力守衛由 AST 改行為型（掛 491 次 run()，鑑別力 57→15 實測，涵蓋 handoff、M-C 繞不過去），AST 降輔助且須決定性；A0b 由頻率歸納改為「#148 沒修完且無機械告知」的直接觀測；A7 刪「未執行期重現」（三條全部重現 rc 2/2/5）；A10 拆開級別與執行能力；新增 A2b/A2c/A11/A12 與 V10/V11。
- 2026-08-26T20:18:38+08:00 amend by wf-cli（op 0b17a60c）→ spec 基線：原值指紋 sha256:a7eedca4f45e88ea46ffaeab1257b40b24544de394221241f43d8a9546658349 (40 bytes) → 新值指紋 sha256:1f53cd83053cfbb3726cd99b267f1c6b9795d00b5d2e3eb330c44890b0fcc996 (40 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 第 3 輪研究（57 輪）更正 16 條、新增 4 條：掛法由 mod.run 改 parser 註冊的 func（11 動詞 549 runs，checkpoint_cmd 沒有 run）；鑑別力 60→2；刪掉「弄紅 4 條」（不擾動觀測法附帶紅測 0）；A9 整條前提拿掉（不需缺欄位世界）；A12 的 N 由 15 改 2（amend rc=6 修得掉）；A2d 登記第 2 輪的「AST 全 0」20 次只出現 10 次；A11 補到六件且第一件是「⛔ 不得推出 ensure_fields 已是唯讀」；spec 基線改 b169c242；資源宣告換成含 handoff_cmd.py 與 conftest.py、移除兩個測試檔。
- 2026-08-26T20:18:38+08:00 amend by wf-cli（op 0b17a60c）→ 驗收條件：原值指紋 sha256:b9d6140db234f60e8b4024ba79644e5bd297901945997163cb7f683bd565e52d (9148 bytes) → 新值指紋 sha256:6664feae02aca4dda956e051f64de37decda264d136219f71f0f19342e42cbab (9729 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 第 3 輪研究（57 輪）更正 16 條、新增 4 條：掛法由 mod.run 改 parser 註冊的 func（11 動詞 549 runs，checkpoint_cmd 沒有 run）；鑑別力 60→2；刪掉「弄紅 4 條」（不擾動觀測法附帶紅測 0）；A9 整條前提拿掉（不需缺欄位世界）；A12 的 N 由 15 改 2（amend rc=6 修得掉）；A2d 登記第 2 輪的「AST 全 0」20 次只出現 10 次；A11 補到六件且第一件是「⛔ 不得推出 ensure_fields 已是唯讀」；spec 基線改 b169c242；資源宣告換成含 handoff_cmd.py 與 conftest.py、移除兩個測試檔。
- 2026-08-26T20:18:38+08:00 amend by wf-cli（op 0b17a60c）→ 驗證：原值指紋 sha256:afaaa29d118bf4d21eac1cee63f3f43c1df4699925993f6d3cb3632147ac2016 (3788 bytes) → 新值指紋 sha256:2a4d237741fbc664019acaf212585e26868c22913c3a3ab71950ec1f25cbaa84 (4811 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 第 3 輪研究（57 輪）更正 16 條、新增 4 條：掛法由 mod.run 改 parser 註冊的 func（11 動詞 549 runs，checkpoint_cmd 沒有 run）；鑑別力 60→2；刪掉「弄紅 4 條」（不擾動觀測法附帶紅測 0）；A9 整條前提拿掉（不需缺欄位世界）；A12 的 N 由 15 改 2（amend rc=6 修得掉）；A2d 登記第 2 輪的「AST 全 0」20 次只出現 10 次；A11 補到六件且第一件是「⛔ 不得推出 ensure_fields 已是唯讀」；spec 基線改 b169c242；資源宣告換成含 handoff_cmd.py 與 conftest.py、移除兩個測試檔。
- 2026-08-26T20:18:38+08:00 amend by wf-cli（op 0b17a60c）→ 資源宣告：原值指紋 sha256:2242992b9d554a31c9f443b6a90db7e958ba06d6aa711428a0a7bc2635a09e78 (427 bytes) → 新值指紋 sha256:7c5d0b08cbc20fa04f11586e0f204055356d96c87e9e58a0775817b86c6349f5 (308 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 第 3 輪研究（57 輪）更正 16 條、新增 4 條：掛法由 mod.run 改 parser 註冊的 func（11 動詞 549 runs，checkpoint_cmd 沒有 run）；鑑別力 60→2；刪掉「弄紅 4 條」（不擾動觀測法附帶紅測 0）；A9 整條前提拿掉（不需缺欄位世界）；A12 的 N 由 15 改 2（amend rc=6 修得掉）；A2d 登記第 2 輪的「AST 全 0」20 次只出現 10 次；A11 補到六件且第一件是「⛔ 不得推出 ensure_fields 已是唯讀」；spec 基線改 b169c242；資源宣告換成含 handoff_cmd.py 與 conftest.py、移除兩個測試檔。
- 2026-08-26T20:19:48+08:00 handoff by wf-cli → owner 待指派（規劃）；iteration 0；SHA b169c2424c0401c169104312f2fa807c01345feb；階段 需求；踩坑回應 8 族（已檢查 1／不適用 1／發現 6）；證據 第 3 輪研究（57 輪）完成並已 amend 卡面（16 條更正、4 條新增）。⭐ 停卡理由已消解：研究者把行為型守衛做成真的 conftest.py 並實測——乾淨樹 rc=0 且安靜／未修樹 rc=1 印 60 條／M-A rc=1／M-C rc=1（AST 版是靜默 0）／全套 1267 passed 與基線逐條相同。主要更正：掛法由 mod.run 改為 build_parser() 反查的動詞入口 func（11 動詞、549 runs，checkpoint_cmd 沒有 run 故先前只看得到 5 個）；鑑別力 60→2；「弄紅 4 條既有測試」整句刪除（1 條是原型沒加 functools.wraps 的 bug、3 條是擾動式的下限，不擾動觀測法附帶紅測 0）；A9 整條前提拿掉（不需缺欄位世界）；A7 的 handoff 由 3 條更正為 11 條且修法簡化（fields 只在 write_status_face 內被用到，整支搬進該 closure 即 11→0）；A12 的 N 由 15 更正為 2。⚠️ 研究者留下一個它明說判不了的問題：三次改形狀、三輪研究（65+47+57 輪）換六行搬動＋約 90 行守衛，研究成本已遠超交付成本，該比例是不是訊號屬需求方判準。⭐ 需求方 2026-08-26 裁定續做（逐字「amend 然後派 147」即含對本卡 amend 的批准）。踩坑清冊逐族內文見上方 --pitfall-report 段落。。
- 2026-08-26T20:33:48+08:00 amend by wf-cli（op 5886b0ab）→ 驗收條件：原值指紋 sha256:70f8695eb26426e89faafdb90368faf83c06c3a7b91492a25dbba4fdfce10777 (9733 bytes) → 新值指紋 sha256:c5faf14db33e82411c2f09cb93211e9a54e25578376d62911b4384c14945d4a6 (10828 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定派規劃並限定射程為「收洞＋專用守衛」：新增 A14（明文這是專用守衛非通用機制，root_cause_id 家族至今無執行者且本卡不提供）與 A15（⛔ 不得宣稱防止了損害，A6 第三度複驗成立、生產受害者 0，本卡只能宣稱收掉一個契約不一致）。
- 2026-08-26T20:34:16+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code (規劃)；分支worktree ai/opus-5/WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/ef-readonly；交付狀態 🧭規劃中；實際能力層級 高階型（偏離卡面建議 主力型；偏離理由：卡面 A10 逐字裁定執行能力應為高階型（amend 無 --exec-capability 旗標故於此落實）；A2 更正後理由改為「判準的邊界條件多，研究者自己連錯兩次」（V13））；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-26T20:50:37+08:00 amend by wf-cli（op 656cace5）→ 驗收條件：原值指紋 sha256:48f70f18016230b126166cf819ce9d26401df1db073ed4c4c767da4bc034d956 (10832 bytes) → 新值指紋 sha256:f0d702c685d3210ebd6366d40d19f61a7f87ea980a064b938b18a7dca90bbc05 (13065 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 跨家族卡面確認找到第四次轉寫錯誤（7 確定＋3 需消歧義，PM 另自查出第 8 項）：A1 射程「四動詞」與 A2 的 60→2 矛盾（後者需六處改動）；A4 資源敘述是第 2 輪舊版與 JSON 直接矛盾；A6 結尾仍引用已被 A0b/A15 廢棄的頻率歸納；A12 分母「60 條裡 12 條」應為「15 條裡」、驗收口徑「≤2」被報告明文否決（應為逐字黃金值＋方向非對稱）、且那兩條是 amend rc=5 不是 rc=6；A0「三處就地註解」實為一處 commit body＋兩處就地註解；A10 高階型理由的泛稱改為三項具體；A11 由六件補到八件（生產環境安全、併發安全性）；A14 的絕對量詞與 A2b 衝突已限定；A2d 對 M-B 補上口徑。
- 2026-08-26T20:50:37+08:00 amend by wf-cli（op 656cace5）→ 驗證：原值指紋 sha256:4602d22bd8f1cf19d4cddcdc414835afc1feebc0cf13e5c014ee9dea91460faf (4815 bytes) → 新值指紋 sha256:9ea6ccc4afc49a7e9266d4865c0cf98d35609daecc29caed4f7b5bef4f7d977b (5023 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 跨家族卡面確認找到第四次轉寫錯誤（7 確定＋3 需消歧義，PM 另自查出第 8 項）：A1 射程「四動詞」與 A2 的 60→2 矛盾（後者需六處改動）；A4 資源敘述是第 2 輪舊版與 JSON 直接矛盾；A6 結尾仍引用已被 A0b/A15 廢棄的頻率歸納；A12 分母「60 條裡 12 條」應為「15 條裡」、驗收口徑「≤2」被報告明文否決（應為逐字黃金值＋方向非對稱）、且那兩條是 amend rc=5 不是 rc=6；A0「三處就地註解」實為一處 commit body＋兩處就地註解；A10 高階型理由的泛稱改為三項具體；A11 由六件補到八件（生產環境安全、併發安全性）；A14 的絕對量詞與 A2b 衝突已限定；A2d 對 M-B 補上口徑。
- 2026-08-26T22:31:26+08:00 handoff by wf-cli → owner 待認領（跨家族查核）；iteration 0；SHA c69280e9a5a4b504ea2f64a4c9404e9a68ecaf8b；階段 規劃；踩坑回應 8 族（已檢查 2／不適用 1／發現 5）；證據 PR #157。六處改動、五個命令模組，⛔ project.py／test_commands_mocked.py／test_review.py 一字未動。違規 60→15（四處搬動）→2（六處改動）；ensure_fields 觸發 482→437→402。殘餘 2 條為 amend rc=5 同一根因（測試自己 monkeypatch 掉 set_field_value ⇒ 觀測面必然看不到），黃金值 {(amend,5):2} ＋方向非對稱。⭐ V14 卡面標「本輪未跑」，一跑就發現 assign/review/amend 三格不成立（守衛綠＋功能壞與守衛綠＋功能好在既有觀測面長得一模一樣），已補四條負控。M-B 的「為什麼不動」未用論證而用兩個追加突變：MB2 把該拒收換成 raise 哨兵得 3 failed/1283 passed 且哨兵出現 0 次 ⇒ 該拒收從未被走到；MB3 把條件反過來使它每輪成立 ⇒ 守衛 rc=1 點名 33 條。V1 上半 rc=1 印全部 60 條、下半 rc=0 安靜。M-C rc=1 且裁決逐位元與 M-A 相同（sha256 5eed5b6c）。V12 四格全過。回歸 pytest 1290 passed、四守衛 rc=0、ruff 全 repo 逐（檔,規則）差異 0 筆。⛔ 兩項未交付待裁定：V5 需 push 故 PR 開出後才補；AST 輔助守衛未做而 A2c/V10 前半句預設它存在 ⇒ 卡面不自洽（PM 第九處錯）。⭐ 執行者逐條回源頭複驗卡面，未找到第五次轉寫錯誤，但列出三處不精確。⛔ 依 A15/A6 不宣稱防止了損害。。
- 2026-08-26T22:33:36+08:00 amend by wf-cli（op 63b415f9）→ 驗收條件：原值指紋 sha256:160e951d843cbb3287690b5f26288ab74a92f22adc533ba0e05fdb41e6749b42 (13069 bytes) → 新值指紋 sha256:86c14f4804c73d01a879a08bb3f7d72d4dbe3af8f7354f6968a3113fad526134 (13497 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 更正 PM 的第九處卡面錯誤：A2c 與 V10 前半句預設有一支 AST 輔助守衛，而它既不在資源宣告落點也不在第 3 輪報告的交付形狀裡（卡面自我不自洽）。採納執行者理由改為「AST 輔助不交付」，並保留「⛔ 不得把任何 AST 0 讀成 handoff 乾淨」這個事實。
- 2026-08-26T22:33:36+08:00 amend by wf-cli（op 63b415f9）→ 驗證：原值指紋 sha256:55911b32130b0a43a67b7f57cdfdfa3349821a1c568300a0abada8f0e4651568 (5027 bytes) → 新值指紋 sha256:86762102dad87cd0f05c6eafa575deab5230a630c2ed580d342c344b20cdd8da (5038 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 更正 PM 的第九處卡面錯誤：A2c 與 V10 前半句預設有一支 AST 輔助守衛，而它既不在資源宣告落點也不在第 3 輪報告的交付形狀裡（卡面自我不自洽）。採納執行者理由改為「AST 輔助不交付」，並保留「⛔ 不得把任何 AST 0 讀成 handoff 乾淨」這個事實。
- 2026-08-26T23:03:50+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 跨家族查核者（需求方轉貼；PM 逐字轉錄）；core_pain_resolved yes；self_run 11 項；findings 3 項（blocking 2）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-e0-c69280e9a5a4b504ea2f64a4c9404e9a68ecaf8b。
- 2026-08-26T23:04:31+08:00 amend by wf-cli（op 03146e87）→ 資源宣告：原值指紋 sha256:572d0bce330fdc809de63480d290daf0c493aaf8921c996669035dea5b49123d (429 bytes) → 新值指紋 sha256:631beb6a2a510bdb9cfa473d3862e0defcd5d2f343ad1c742257f0248b086fe5 (383 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 查核 R1 finding WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R1-02 裁定「本卡修」並指定由 PM 先擴充資源宣告：cli/tests/test_commands_mocked.py 與 cli/tests/test_pitfalls.py 兩段敘述的前提已被本卡改動推翻（assign/open 的 ensure_fields 現在都排在所有非 0 拒收之後），屬同一根問題直接造成的過期敘述，開後續卡會違反一根問題一張卡。⚠️ --resources 為整份取代，故連同原有 7 條一併傳入。
- 2026-08-26T23:05:58+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (執行)；iteration 1；SHA c69280e9a5a4b504ea2f64a4c9404e9a68ecaf8b；階段 審核；踩坑回應 8 族（已檢查 3／不適用 0／發現 5）；證據 R1 裁決 REQUEST_CHANGES，兩則阻塞 finding 交回執行者。R1-01：5/5 commits 缺 Requested-by／Planned-by／Implemented-by，須重寫五筆 commit message、產生新 head SHA、重新 handoff 並由 CI 重驗。R1-02：test_commands_mocked.py:514-517 與 test_pitfalls.py:723-724 兩段過期敘述本卡修；PM 已依裁定把這兩檔擴進資源宣告（op 03146e87，7→9 條）。R1-03 非阻塞：MB3 的 33 條釘 SHA 或改為 current-head 的 34 條。⛔ 核心痛點已判為解除（ensure_fields 已移至各拒收閘門之後，指定基線上違規 60→2），R2 依 canonical §6 只做 R1 finding 逐項閉環驗證＋回歸不倒退，⛔ 不擴審新範圍。。
- 2026-08-26T23:08:29+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code (執行)；分支worktree ai/opus-5/WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/ef-readonly；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-26T23:48:22+08:00 handoff by wf-cli → owner codex；iteration 1；SHA 05958a1d80ac24fdb090603733dc595d8e6e82a2；階段 執行；踩坑回應 13 族（已檢查 5／不適用 0／發現 8）；證據 R2 交付：R1 三則 finding 逐項閉環，執行者複驗後前提全部成立、⛔ 無一需要反駁。R1-01：五筆 commit 重寫為六筆（新增 05958a1d 承載 R1-02），每筆四個 trailer 均由 git interpret-trailers --parse 解析出、末端連續單一區塊無空行切斷；doctor --commit-trailers --require-planned-by 讀內容為「違規 0／合規 6（共 6 筆）」，修前為「違規 5／合規 0」。⭐ 內容零變動已證：前五筆重寫後 head tree 27c6b9461ab784e1b19e0fd9801585e21db4a962 與原 c69280e 逐位元相同、五筆 git patch-id --stable 逐筆相同。R1-02：test_commands_mocked.py +25/-4、test_pitfalls.py +21/-2，前提先自行 AST 複驗（open_cmd 266 行其前 5 條非 0 return、assign_cmd 267 行其前 6 條，其中 189 行正是能力閘門的 return 2）；兩處依「刻意行為就地留註解」改寫為 (a) 現在的順序 (b) 為什麼 (c)(d) ⛔ 不得推出什麼，⛔ 未把舊句刪掉了事。R1-03：實測 34 非 33，+1 來源具名；⛔ PR 描述未改（gh 在禁區，屬 PM 的面）。回歸逐項 rc=0：pytest 1290／-k amend 202／test_pitfalls 43／uv lock --check；乾淨樹守衛 stdout 0 行 stderr 0 行；ensure_fields_oracle 觸發 410／模組 11／不一致 0（⛔ 不是 0/0）；守衛放回未搬動 b169c242 為 rc=1、入口 557／rc≠0 137／違規 60。全部導檔再讀，⛔ 無一接管線。PM 已獨立重跑其中六項，數字逐格相同。執行者自報 6 項失誤、6 項未驗清單，全在踩坑報告與交付報告內。。
- 2026-08-27T03:54:50+08:00 review by wf-cli → APPROVE（✅通過）；查核者 codex；core_pain_resolved yes；self_run 15 項；findings 4 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-e0-05958a1d80ac24fdb090603733dc595d8e6e82a2。
- 2026-08-27T04:05:40+08:00 handoff by wf-cli → owner —（已合併）；iteration 1；SHA 2e53c09215140fa10f8b59e96174492a0c467f4f；階段 審核；踩坑回應 8 族（已檢查 2／不適用 0／發現 6）；證據 PR #157 已於 2026-08-26T20:02:50Z 合併，merge commit a46af717233cb3f04ad3d40d06a4934c613d4239 落 origin/main。六筆 commit 經 merge-base --is-ancestor 逐筆確認皆在 main 上。合併前 gate=CLEAN、必要 context tests=SUCCESS、tests (branch head)=SUCCESS、落後 main 0 筆。merge commit 帶三個 trailer 且經 git parser 解析得出（Requested-by: ruan6047／Planned-by: Claude Opus 5@Claude Code (PM)／Reviewed-by: codex（#154 的 issuecomment-5430369803，APPROVE、阻塞 findings 0））。⚠️ 首次 release 被 merge_verified_local 擋下（證明=diverged、9 個路徑在 main 上與分支不同）——成因是本機 main 落後 7 筆而守衛比對的是本地 main 非 origin/main；ff-only 更新後重跑。裁決依據：codex 於 R2 給 APPROVE、core_pain_resolved=yes、無阻塞 finding。核心痛點解除的機械證據：指定基線 b169c242 上違規 60→2，殘餘 2 條經查核者以清空 FROZEN 後單獨重跑確認為觀測面盲點（兩者皆在 test_amend.py:437 monkeypatch amend_cmd.set_field_value 成 no-op，寫入不可能抵達 FakeGhRunner 出口），⛔ 非產品缺陷。；收尾清理：已清除 worktree、本地分支、遠端分支。


## Comment 5425408143 · 2026-08-26T12:38:30Z

## ⏸ 執行已暫停：卡面先送跨家族確認

需求方 2026-08-26 裁定：**在執行者照卡面做事之前，先讓另一個 AI 檢查卡面本身有沒有錯**。PM 已停掉規劃／執行代理（未產生 commit）。

### 理由：PM 在這張卡上已經連錯三次，每次都是別人抓到的

| 次 | PM 寫進卡面的 | 誰抓到 | 實際 |
|---|---|---|---|
| 1 | 「`assign` 逐字記載為刻意」 | 第 1 輪研究（65 輪） | ⛔ 那段主詞是**測試的保證範圍與用詞強度**，全段沒有一句主張早建欄位有好處；位置來自 2026-08-04 建檔樣板、**無任何決策紀錄** |
| 2 | 「AST 守衛就夠」 | 第 2 輪研究（47 輪） | ⛔ AST 對 M-C **靜默漏報**（報 0 且該檔從報表消失）；且「搬完後全 0」20 次只出現 10 次 |
| 3 | 掛 `mod.run`／`amend rc=6` 不可修／「弄紅 4 條」 | 第 3 輪研究（57 輪） | ⛔ **三個數字全錯**（`checkpoint_cmd` 沒有 `run` 故只看得到 5 個動詞；`rc=6` 修得掉、N 是 2 不是 15；4 條裡 1 條是原型 bug） |

⇒ ⭐ **卡面現有 A0–A15／V1–V14 共 29 條，全部是 PM 從三份研究報告「轉寫」來的——而轉寫正是 PM 犯過三次錯的那個動作。** 第四次在先驗上是最可能的。

### ⛔ 送審的射程限定

送出去問的**不是**「這張卡該不該做」——⭐ 那是需求方的判準，第 3 輪研究者逐字說它判不了，第二個 AI 也判不了。

問的是：**卡面的數字與宣稱，回到報告原文逐條比對，有沒有第四次錯。**

### 為什麼是現在而不是等交付

⭐ **卡面錯誤最貴的時點就是執行者正照著做的時候**。等交付出來再查，錯誤已經寫進碼裡。代價是浪費已跑的幾分鐘，⛔ 那比重寫一輪便宜。

---
本帖由 PM（Claude Opus 5@Claude Code）以需求方的 token 發文；暫停決定轉錄自需求方在 2026-08-26 session 對「甲／乙」的逐字回覆「甲」（甲＝現在就送並停掉代理）。⛔ 卡面未動、狀態仍為 🧭規劃中。

## Comment 5427274807 · 2026-08-26T15:03:51Z

<!-- wf-review-event:v1 card_id=WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1 source_sha=c69280e9a5a4b504ea2f64a4c9404e9a68ecaf8b attempt_id=WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-e0-c69280e9a5a4b504ea2f64a4c9404e9a68ecaf8b -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1`　attempt_id：`WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-e0-c69280e9a5a4b504ea2f64a4c9404e9a68ecaf8b`
- 查核者：跨家族查核者（需求方轉貼；PM 逐字轉錄）　escalation_epoch：0
- source_sha：`c69280e9a5a4b504ea2f64a4c9404e9a68ecaf8b`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-26T23:03:50+08:00

### self_run（查核者實跑）

- `指定基線 diff（merge-base b169c2424c0401c169104312f2fa807c01345feb）`
  - 7 files，+893/-32
- `uv run pytest -q（全套）`
  - RC=0，1290 passed
- `乾淨樹守衛訊息`
  - stdout 0、stderr 0
- `ensure_fields oracle`
  - 410 觸發／11 模組／0 判不了／0 不一致
- `守衛放回未搬動基線 b169c242`
  - RC=1，557 入口／137 rc≠0／60 違規
- `uv run pytest -q -k amend`
  - 202 passed
- `uv run pytest -q tests/test_pitfalls.py`
  - 43 passed
- `import conftest 讀 MUST_NOT_CONCLUDE`
  - tuple，8 條
- `PR #157 required checks`
  - tests、tests (branch head) 均通過
- `清空 FROZEN 後只跑兩條測試`
  - 均得到 seq=['EF']；兩者都在 test_amend.py:437 monkeypatch amend_cmd.set_field_value 成 no-op，因此寫入不可能抵達 FakeGhRunner 出口
- `MB2／MB3 等價突變重跑`
  - MB2 哨兵 0 次；MB3 確實令守衛紅，current head 等價重跑為 34 條（PR 記載的 33 條為新增四條 V14 負控前的歷史量）

### findings（3，其中 blocking 2）

- **WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R1-01**　severity=major　blocking=true　class=governance　attribution=executor　root_cause_id=`missing-provenance-trailers`
  - evidence：wfcli doctor ... --commit-trailers --require-planned-by 列出五筆皆缺 Requested-by、Planned-by、Implemented-by。Doctor 的 RC=0 是因為它刻意只報告、不阻擋；不能解讀為合規。
  - disposition：5/5 commits 缺必填 provenance trailers。需重寫五筆 commit message、產生新 head SHA，重新 handoff 並由 CI 重驗。這是 review preflight failure，不應為目前 SHA 建立有效 review event。
- **WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R1-02**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`stale-narrative-after-behaviour-change`
  - evidence：cli/tests/test_commands_mocked.py:514-517 仍宣稱 assign 在能力檢查前呼叫 ensure_fields；cli/tests/test_pitfalls.py:723-724 仍寫 assign/open 刻意在前置段呼叫 ensure_fields。本卡已把 assign 的 ensure_fields 搬到能力、歸屬、觀測與資源衝突閘門之後；assign、open 與 review 現在各自把 ensure_fields 放在最後拒收之後，amend 另有已凍結的兩條觀測盲點。已與 current head 行為相反。
  - disposition：兩段已被本卡改動推翻的註解必須在本卡修正。裁定：本卡修。它們是同一根問題直接造成的過期敘述；開後續卡違反「一根問題一張卡」，標為已知過期則會長期保留錯誤前提。應由 PM 先透過 wfcli 擴充這兩個資源宣告，再交回執行者修改；查核者不代改。
- **WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R1-03**　severity=minor　blocking=false　class=authoritative-artifact　attribution=executor　root_cause_id=`evidence-number-not-pinned-to-sha`
  - evidence：PR 的 MB3「33 條」是新增四條 V14 負控前的歷史量；current head 等價重跑為 34 條，新增的正是 assign 負控。
  - disposition：建議把 33 釘到當時 SHA，或更新為 current-head 數字，避免被讀成現況黃金值。這是非阻塞證據標註瑕疵。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-e0-c69280e9a5a4b504ea2f64a4c9404e9a68ecaf8b
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待認領（跨家族查核）
findings:
  - finding_id: WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R1-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: governance
    attribution: executor
    root_cause_id: missing-provenance-trailers
    counting_eligible: false
  - finding_id: WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R1-02
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: stale-narrative-after-behaviour-change
    counting_eligible: true
  - finding_id: WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R1-03
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: evidence-number-not-pinned-to-sha
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5427318873 · 2026-08-26T15:08:00Z

## 更正：R1 查核者身分

上一則裁決的 `reviewer` 欄我填的是「跨家族查核者（需求方轉貼；PM 逐字轉錄）」——那是因為轉貼進來的收據沒有自述身分，⛔ 當時我驗不了 canonical §5「紅線卡須跨模型家族或人工」是否成立，所以只寫了模糊字串。

需求方於 2026-08-26 補述：**R1 查核者為 codex**。

⇒ 跨模型家族要求**成立**（codex 屬 OpenAI 家族；執行者與 PM 皆為 Anthropic 家族的 Claude Opus 5）。

⚠️ 我**不編輯原事件**，改以本則留言更正——原因是留痕的價值在於「當時寫下的就是當時知道的」。原事件的 `reviewer` 欄仍為模糊字串，請以本則為準。

⛔ 另外三件當時由我補上、⛔ 不是 codex 給的：`finding_id`、`root_cause_id`（`missing-provenance-trailers` / `stale-narrative-after-behaviour-change` / `evidence-number-not-pinned-to-sha`，這三個家族名是我造的）、`attribution`。findings 的 `evidence` 與 `disposition` 內文一字未動。

⛔ 還有一項落差：收據原文有 `preflight_passed: false`，但裁決 schema 沒有這個鍵 ⇒ 它沒有落成欄位，只活在 R1-01 的 `disposition` 內文裡。


## Comment 5427375574 · 2026-08-26T15:14:09Z

## 更正：R1-01 的 root_cause_id 我造錯了

我在轉錄 codex 的 R1 裁決時，補上了 schema 必填但收據沒給的 `root_cause_id`，其中 R1-01 我填的是 `missing-provenance-trailers`。

⛔ **那是我自己造的名字。** canonical 對這個缺陷家族已有既定的 id——`wfcli doctor --commit-trailers` 的輸出逐字印出：

```
- canonical root_cause_id: `commit-trailer-required-but-missing`
```

⇒ **R1-01 的 root_cause_id 應為 `commit-trailer-required-but-missing`**，請以本則為準。

⚠️ 這使我先前那則更正留言裡的說法要再收窄一次：我說「這三個家族名是我造的」，其中 R1-01 這個**本來就有 canonical 名字**，是我沒查就造 ⇒ 不只是「補上結構欄位」，而是**蓋掉了既有的家族 id**，會讓同族缺陷在統計上被切成兩堆。

另兩個（`stale-narrative-after-behaviour-change`、`evidence-number-not-pinned-to-sha`）我重查過 `doctor` 與 canonical，**沒有**對應的既定 id ⇒ 仍為我造，維持原值但標明來源。

⭐ 同一個缺陷家族今日在 `WF-CARD-BRIEF-BACKFILL1`（#147）也命中一次：PM 的 commit `80eb3440` 同樣三個 trailer 全缺，已 amend 為 `292f5303` 修正。另注意 repo 內有一張 `claude/DEV-COMMIT-TRAILER-GUARD1` 尚未併入 main——那正是這個家族的守衛。


## Comment 5430369803 · 2026-08-26T19:54:52Z

<!-- wf-review-event:v1 card_id=WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1 source_sha=05958a1d80ac24fdb090603733dc595d8e6e82a2 attempt_id=WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-e0-05958a1d80ac24fdb090603733dc595d8e6e82a2 -->
## 查核裁決：APPROVE

- 卡：`WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1`　attempt_id：`WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-e0-05958a1d80ac24fdb090603733dc595d8e6e82a2`
- 查核者：codex　escalation_epoch：0
- source_sha：`05958a1d80ac24fdb090603733dc595d8e6e82a2`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-27T03:54:50+08:00

### self_run（查核者實跑）

- `git identity、merge-base、tree 與 patch-id 對帳`
  - HEAD 05958a1d；merge-base b169c242；前五筆 tree 與 patch-id 全同
- `git interpret-trailers --parse ＋ wfcli doctor 前後對照`
  - 修後 0/6、修前 5/0；兩者 RC=0 ⇒ 證實 doctor 只報告、不阻擋
- `AST 定位 open/assign ensure_fields 與前置非零 return`
  - open 266/5；assign 267/6；能力閘門 return 2 在 189
- `R1-02 單測呼叫時點突變`
  - 測試本體 1 passed；gate-guard 令行程 RC=1 ⇒「該測試對呼叫時點零資訊」的揭露充分
- `MB3 等價重建`
  - RC=1，('assign', 2): 34，新增來源確為 test_assign_recreates_the_field_it_is_about_to_write
- `pytest -q ／ -k amend ／ tests/test_pitfalls.py`
  - 1290 passed／202 passed／43 passed
- `uv lock --check`
  - RC=0
- `乾淨 head gate-guard`
  - stdout／stderr 均 0 行
- `ensure_fields oracle`
  - 410 次／11 模組／判不了 0／不一致 0
- `現行守衛＋測試覆回 b169c242`
  - RC=1，557 入口／137 個非零 RC／60 違規
- `Implemented-by 慣例全史掃描（git interpret-trailers --parse）`
  - 裸值 Claude Opus 5@Claude Code 為 117 次、…(執行) 為 0 次。⚠️ 裸 grep 會得到 118，是 commit 06ac31f 的 body 中有一行長得像 trailer 但不在可解析 trailer 區塊 ⇒ 117 才是正確口徑
- `gh pr/run/ruleset 唯讀查詢`
  - ruleset active 且 strict、唯一 required context 是 tests、無 bypass actor；CI run 33001299046 的 headSha 為 05958a1d、tests SUCCESS
- `PR workflow 實際 checkout 對象查證`
  - checkout 的是 GitHub 產生的 merge commit 07171ce（把 05958a1d merge 到 079c9ee）⇒ 確實對應指定 head，但不是 detached checkout 裸 05958a1d
- `GitHub incident 時間對帳`
  - Actions 於 2026-08-26T15:11:58Z 開始 Critical 中斷、18:01:30Z resolved；close／reopen 為 18:43:37Z／18:43:49Z，隨後產生成功 run ⇒ 與舊 run 的 queued／startup_failure 時段吻合
- `worktree 最終狀態`
  - 乾淨，HEAD 未變

### findings（4，其中 blocking 0）

- **WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R1-03**　severity=minor　blocking=false　class=authoritative-artifact　attribution=executor　root_cause_id=`evidence-number-not-pinned-to-sha`
  - evidence：PR #157 的 MB3 仍寫未釘 SHA 的 33；現行 head 等價重建為 34。
  - disposition：PM 將 PR 描述更新為 34，或把 33 明確釘到原始突變 artifact SHA，並另記現行 head 為 34。
- **WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R2-01**　severity=minor　blocking=false　class=coordination　attribution=coordinator　root_cause_id=`diffstat-total-reported-as-additions`
  - evidence：R1-02 的行數寫法需更正：test_commands_mocked.py 為 +21/−4、test_pitfalls.py 為 +19/−2。git diff --stat 顯示的 25／21 是各檔「總變動行數」，不是新增行數。
  - disposition：⛔ 記號誤用，⛔ 但不影響 R1-02 的實質閉環。PM 交付敘述中的 +25/−4、+21/−2 應更正。
- **WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R2-02**　severity=info　blocking=false　class=governance　attribution=reviewer　root_cause_id=`ruling-mb3-rebuild-not-replay`
  - evidence：MB3 是依現行描述做的等價「重建」，得到 34；原始突變 patch 不在樹中。
  - disposition：裁決（非缺陷）：⛔ 不能宣稱逐位元重播。執行者的自陳正確。
- **WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R2-03**　severity=info　blocking=false　class=environment　attribution=external　root_cause_id=`ruling-force-with-lease-unexplained`
  - evidence：--force-with-lease=<ref>:<sha> 的拒絕原因仍無法重現。
  - disposition：裁決（非缺陷）：保留「原因不明」是正確處置。它不屬 R1 finding，R2 不擴審，⛔ 也不應編造解釋。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-e0-05958a1d80ac24fdb090603733dc595d8e6e82a2
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: codex
findings:
  - finding_id: WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R1-03
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: evidence-number-not-pinned-to-sha
    counting_eligible: false
  - finding_id: WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R2-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: coordination
    attribution: coordinator
    root_cause_id: diffstat-total-reported-as-additions
    counting_eligible: false
  - finding_id: WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R2-02
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: reviewer
    root_cause_id: ruling-mb3-rebuild-not-replay
    counting_eligible: false
  - finding_id: WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1-R2-03
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: environment
    attribution: external
    root_cause_id: ruling-force-with-lease-unexplained
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5433546240 · 2026-08-27T02:21:19Z

## ⛔ 留痕：本卡的合併方式違反了 ROADMAP §3.5 的裁定

`a46af717233cb3f04ad3d40d06a4934c613d4239` 是我（PM）用 **`gh pr merge --merge`** 合的，⛔ **而 `docs/ROADMAP.md` §3.5 逐字裁定「合併方式：一律 squash（2026-08-13 裁定）」。**

⚠️ **我沒查 ROADMAP 就自己推理**，還在需求方面前論證 `--merge` 比較好，理由是「要有地方放 `Reviewed-by`，`--rebase` 沒有 merge commit 就沒地方放」。⇒ 那個推理的**結論方向是對的**（`Reviewed-by` 確實要有地方放），⛔ **但正確答案早就裁定在 ROADMAP 裡**，而且比我的方案好。

### §3.5 的裁定理由（逐字）

> `AI_WORKFLOW.md` §6 要求「merge commit、PR 結案紀錄或 B2 權威文件的核可 commit 另必加 `Reviewed-by`」，而 **GitHub 的 merge 按鈕結構上產不出這一行**。`TRAILER_GUARD_EPOCH`（`2026-08-13T00:00:00+08:00`）跨過之後，**每一次以 merge 按鈕合併的 PR 都會是一筆違規** —— 實測 `0ea7aba` 與 `dbf18d7` 的 `git interpret-trailers --parse` 解析出**零個** trailer。

### ⭐ 而 §3.5 還有一個我完全沒想到的好處

> **`gh pr update-branch` 產生的 merge commit 只存在於 PR 分支上，squash 會把它壓掉**，不落 main。既滿足 strict 政策，又不製造違規。

⇒ 我為了避開 `update-branch` 會產生無 trailer 的 merge commit，**做了兩次本機 rebase**（`#154` 一次、`#147` 一次）。⛔ **那兩次都是不必要的** —— squash 本來就把它壓掉了。

### 實際後果：⛔ 沒有違規，但方法錯

`a46af717` 那筆 merge commit 我**手動用 `--body-file` 塞了三個 trailer**，`git interpret-trailers --parse` 讀得到 ⇒ ⛔ 沒有落入 §3.5 說的那個違規。⚠️ **但那是靠我剛好知道有這條規則、剛好手動補了**，⛔ 不是流程保證的。§3.5 自己也逐字寫著「**這是約定，沒有機械執行者**」。

⚠️ 另一項代價**已經發生且改不了**：`a46af717` 是 merge commit ⇒ 被審 SHA `05958a1d` **有**出現在 main 的歷史上（那反而是 §3.5 說 squash 會損失的東西）。⇒ 本卡在這一點上**偶然優於**規定的做法，⛔ 但那不構成違反裁定的理由。

### 對照：`#147` 已照裁定做

`764a59ff10bbb073952b4c20ebb830e6a787d7fc` 是 **squash**，四個 trailer 經 parser 確認（含 `Reviewed-by: GPT-5@Codex`），被審 SHA `6e8beca4…` 逐字記在訊息裡（§3.5 的緩解條款）。

---

⭐ **教訓，⛔ 不限本卡**：`ROADMAP.md` 有 §3.5 這種「已裁定的操作方式」章節，而我合併前只查了 ruleset 與 PR 狀態、**沒查它**。⇒ 動不可逆操作之前先 `grep` ROADMAP 有沒有對應裁定，⛔ 不要從第一原理推。

