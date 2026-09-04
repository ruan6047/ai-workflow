# #238 [清單] persistent Log writer sink（原 W3′ 驗收 1；P1-33 一事件一留言）
- state: open  created: 2026-09-01T21:31:49Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/238
- comments: 3

## Body

### 出處可指

ai-workflow `docs/research/drafts/wave-specs/w3.md` 的驗收 1（規劃 Gate 通過版之不可變 git 物件 `93bb8c086f0cf8870537390511b5f0aa2d037c97:docs/research/drafts/wave-specs/w3.md`，`git show` 可核）。該條之定稿依據為需求方 2026-08-31 對 P1-33 的裁定（**乙′：一事件一留言**）。

本項成立於 2026-09-02：需求方於 `WF-REDESIGN-W3`（`ruan6047/ai-workflow#221`）開卡前裁定將該條**拆為獨立清單項**，⛔ 不在該卡射程。⛔ 本裁定不推翻 P1-33 的內容，只改其落地時程。

### 是觀察不是結論

**規格全文逐字保留**（來源同上，⛔ 未增刪）：

> （P1-33 critical，需求方 2026-08-31 裁定**乙′：一事件一留言**——GraphQL updateIssueComment 僅 id+body、REST 無文件化條件更新，固定留言無 CAS 必丟並行更新）persistent Log writer sink 封閉全集＝**7 個**（open 初始 Log＋assign／amend／checkpoint×2／review／handoff；具名排除 doctor 非持久化 probe；inventory test 以 predicate 實跑、多一少一即紅）。每事件新建一則留言；**保證模型＝實體 at-least-once／邏輯 exactly-once**（GitHub 建立留言無文件化伺服端冪等）。（P1-33 定稿 v2）**immutable event envelope 於第一次遠端寫入前凍結並落本機 pending journal**（`<repo>/.wf-pending/<op-id>.json`；`.gitignore` 新增 `/.wf-pending/` 條目，oracle＝`git check-ignore -q .wf-pending/probe.json`）——**原子落盤**：同目錄 temp＋fsync＋no-clobber rename，於首次遠端呼叫前完成；發佈時遇既有同 op 檔只接受 byte／hash 等價（冪等重發佈），異值 fail-closed：**closed `event-v1` schema**＝schema version＋card id＋verb＋128-bit UUID op id＋event payload＋**凍結 timestamp**＋hash（逐層 additionalProperties=false，schema 外欄位載入即拒）——**hash canonicalization 具名**：對 envelope（不含 hash 欄）做 canonical-v1 序列化（`sort_keys=True, ensure_ascii=False, separators=(',',': ')`, UTF-8）後 sha256。**跨程序恢復**＝既有動詞加 `--event-envelope <journal 路徑>`（⛔ 非新動詞；`--op-id` 僅作 journal 查找鍵）——retry **載入閘**（全部通過才碰遠端；任一不符**於 remote write 前拒絕**）：path resolve 後必須位於目前 repo `.wf-pending/`、檔名＝op id、regular file ⛔ 拒 symlink；schema 解析通過；重算 canonical-v1 sha256 與 hash 欄一致；envelope 之 card id／verb／payload 與本次命令逐項綁定核對（⛔ 任意外部 JSON 不得成為事件注入通道）。通過後**整份重用凍結 envelope**⛔ 不重建任何欄位 ⇒ 重掃暫時不可見時最壞結果＝同 hash 實體重複（reader collapse＋warning，at-least-once 語意內）⛔ 不可能觸發 corruption gate；journal 缺失時**拒絕 retry 並指示人工比對**⛔ 不重建。失敗訊息內含可直接重跑的 retry 命令（帶 journal 路徑）；writer（含重啟後）寫入前重掃既有留言比對 op id；journal 僅於 remote read-back 證 same op id＋same hash 後刪除；unlink 遇 ENOENT（多 session 併發）視為冪等成功。**feature flags 具名**：`WF_COMMENT_READER`／`WF_COMMENT_WRITER`，off/on 讀寫矩陣封閉四格＝off/off 純 body（現狀）；on/off dual read＋body write（phase 1）；on/on 留言寫（phase 2）；**off/on 非法組合 fail-closed 拒啟動**。reader 按 op id 分組——同 hash collapse＋warning、**不同 hash＝corruption fail-closed**；索引只由 canonical deduped set 重建。tests 必模擬「server 已 create、client timeout、程序重啟、同 token 重跑」證 logical event 仍一筆；同 op id 異 hash 必紅；journal 邊界 fixtures 至少含：截斷 JSON／hash tamper／同 op 異 payload／card 或 verb 不符／repo 外路徑／symlink／發佈遇既有異值 journal／create 成功但 delete 前 crash——每例結果唯一（fail-closed 或冪等收斂），⛔ 無實作者自選分支。部署兩階段各為**獨立可回退 commit＋明文 feature flag**：phase 1＝dual reader（含 backout rehearsal）、phase 2＝writer epoch——**phase 2 關閉後 phase 1 reader 仍在**；⛔ 刪除 materialize 未定分支（回退＝關 phase 2 flag）。rehearsal 以事件 op id 集合＋內容 hash 證⛔ 不少一筆；舊 body Log 原地凍結⛔ 不搬

**2026-09-02 重量（PM 於開卡前所量，指令與統計量逐字如下）**：

- 量法＝`Σ Log 段字元 / Σ body 字元`（`## Log` 起算至 body 末端），語料＝Project #4 全部 216 個 items 的 issue body：`1704766 / 2281696 = 74.7%`。
- 216 張**全部**有 `## Log` 段；Log 事件（Log 段內以 `- 20` 起首之行）共 **2,175** 則，每則平均 **784** 字元。
- body 上限實測 **129,486** bytes。最大 body ＝ `ruan6047/ai-workflow#130`，**76,462** 字元＝上限的 **59.1%**。
- ⭐ body 最大的 8 張（`aiwf#130`／`aiwf#138`／`cpbl#159`／`cpbl#134`／`aiwf#146`／`aiwf#141`／`aiwf#105`／`cpbl#154`）**交付狀態全為 `🏁完成`** ⇒ 皆不再有 Log 寫入。
- **非終態卡 50 張**（排除 `🏁完成`／`🛑已停止`／`📦已合併`）中最大 body ＝ `ruan6047/ai-workflow#57` 的 **32,459** 字元＝上限的 **25.1%**；依各卡自身「Log 字元 ÷ Log 事件數」推算離上限的餘裕，最緊者為 `ruan6047/ai-workflow#137`（`⏸阻塞`）的 **≈57 則**，`#57` 為 **≈95 則**。歷史上一張卡一生平均 **2175 ÷ 216 ≈ 10** 則 Log 事件。

⇒ 可觀測現象是：**Log 段佔 body 的比例高（pooled 74.7%），但今日無任何仍在推進的卡接近 body 上限**。⚠️ 「多久會撞牆」是推估，⛔ 非量測；上述餘裕係以各卡自身歷史均值外推，⛔ 未考慮未來事件長度變化。

其他可觀測事實：

- 新 Log 條目**無留言載體**——現行寫入路徑一律 append 進 body 的 `## Log` 段（`cli/src/wf_cli/card.py` 的 `_LOG_HEADING = "## Log"` 與 `append_log_line`）。
- 平台保有 body 的逐位元前一版（`userContentEdits`），但 `DraftIssue` 型別沒有；`open`／`amend` 的覆寫留痕僅記 `sha256` 指紋。

### 查重留痕

已跑（`gh issue list --repo ruan6047/ai-workflow --state all --search <關鍵字>`）：

```bash
gh issue list --repo ruan6047/ai-workflow --state all --search "Log 留言"
gh issue list --repo ruan6047/ai-workflow --state all --search "writer sink"
gh issue list --repo ruan6047/ai-workflow --state all --search "一事件一留言"
gh issue list --repo ruan6047/ai-workflow --state all --search "envelope"
```

命中：`#30`／`#86`／`#214`／`#16`／`#170`／`#217`／`#177`／`#221`／`#115`／`#58`／`#234`／`#66`／`#42`。逐一核對最近的三張：`#30`（`WF-MARKER-SCOPE-CLEARANCE1`）痛點為「doctor 以全文子字串比對事件 marker 前綴，任何留言只要提到該字樣就隔離整張卡」——對象是 marker 判準，⛔ 非 Log 的居所；`#86`（`WF-REVIEW-RECEIPT-WRITEBACK1`）痛點為「跨家族查核者沒有寫入通道，裁決靠人工轉貼致 `report_sha256` 失效」——對象是裁決收據，⛔ 非 Log 段容量；`#170`（`WF-SNAPSHOT-SCHEMA-BODY-GAP1`）痛點為 canonical 兩條條文互斥致「簡介覆蓋率」無法合規引用——⛔ 非本項。**四個關鍵字都沒有命中以本項為痛點的既有清單項或卡。**

### 屬哪個 repo

ai-workflow

### 提案者身分

- GitHub 帳號：`ruan6047`（本 issue 的 author 欄即為此帳號，可核）
- session ID：`cc0a7952-07a5-4978-8d03-8b5f48fbc690`（PM session，Claude Code，模型 `claude-fable-5`）
- 該則訊息定位：規格內容之提案者為需求方（2026-08-31 P1-33 裁定）；本項之**建立**由該 PM session 於 2026-09-02 依需求方當日裁定執行，量測與拆卡討論之 transcript 於需求方本機 `~/.claude/projects/-Users-ruanruan-Dev-cpbl-analytics--claude-worktrees-workflow-review-optimization-33882b/` 可核。

---

⚠️ **提案者即 PM**：本項由 PM 依需求方裁定建立，⛔ 非 PM 自行發起。收件閘的「提案者≠肇因者」成立、「提案者≠收件者」不成立 ⇒ 由需求方決定是否補一次第二 PM 收件裁決。

> ⛔ 本項不配卡ID、⛔ 不掛成任何卡的 sub-issue、⛔ 不進 Project #4；升級走 `wfcli open --from-issue <本 URL>`。


## Comment 5503141006 · 2026-09-02T01:51:44Z

## 排程裁定：本項排在 `WF-REDESIGN-W3` 結案之後（2026-09-02）

**轉錄來源自述**：決定者＝**需求方本人**（`ruan6047`，2026-09-02 於 PM session `cc0a7952-07a5-4978-8d03-8b5f48fbc690` 的對話中逐字「好，AC1 排 W3′ 之後」）。本則由該 PM session 撰寫發佈；GitHub token 為 `ruan6047`，⇒ author 欄⛔ 不足以區分撰寫者與決定者，故在此明示。

### 裁定

本項（persistent Log writer sink）**排在 `ruan6047/ai-workflow#221`（`WF-REDESIGN-W3`）結案之後**。⛔ 不與該卡並行、⛔ 不提前。

### 依據（PM 2026-09-02 量測，需求方據以裁定）

1. ⭐ **寫入集重疊 81%。** 本項的 Log writer 封閉全集為 7 個動詞所在的檔；`WF-REDESIGN-W3` 驗收 4 的拒絕訊息全集為 **73 則**（關鍵字集逐字 `/\[[a-z-]+\] 拒[絕收]/`、語料 `cli/src` 之 `.py`、計 occurrence），其中 **59 則（81%）** 落在那 7 個檔內。逐檔：`handoff_cmd.py` 13／`open_cmd.py` 12／`amend_cmd.py` 11／`review_cmd.py` 10／`assign_cmd.py` 5／`checkpoint_cmd.py` 5／`card.py` 3。
   ⇒ 本項若在前，驗收 4 的全集會被本項新增的 journal 拒絕訊息撐大，且驗收 4 剛補好的補救文字會被本項重寫一次。本項在後 ⇒ 全集固定在 73，本項新增的訊息直接按已生效的補救規範寫。
2. **第二處同形重疊**：`WF-REDESIGN-W3` 驗收 6b 動 `handoff_cmd.py`（13 則，最大宗）與 `pitfalls.py`，本項亦動 `handoff_cmd.py`。
3. **延後的代價為零**：非終態卡 50 張中離 body 上限最緊者為 `ruan6047/ai-workflow#137`（`⏸阻塞`），依其自身「Log 字元 ÷ Log 事件數」推算仍可寫 **≈57 則**；歷史上一張卡一生平均 **≈10 則**（2,175 則 ÷ 216 張）。

**已查過的反方論據**：切換 Initiative 波次將產生約 121 次 `amend`（36 張舊卡處置＋57 份 spec 封存＋13 個 `db:` 正規化＋15 張 write+ 補宣告，數字取自 `docs/research/WORKFLOW-REDESIGN-2026-08-30.md:97` 與 `:111`），是否會在本項落地前撐爆 body？該量分散於不同卡、每張約 +1～3 則，⛔ 未達上述 ≈57 則餘裕 ⇒ **不構成提前理由**。

⚠️ 「多久會撞上限」為外推、⛔ 非量測；以各卡自身歷史均值為基礎，⛔ 未考慮未來事件長度變化。

### ⚠️ 升級前的已知前置（PM 登記，⛔ 未代為處置）

父卡 `ruan6047/ai-workflow#177`（`WF-REDESIGN1`）驗收逐字：「四波五卡（WF-REDESIGN-W0／W1／W2A／W2B／W3）全數誕生於本卡規劃階段並各自結案；**中途追加子卡須升級裁定留痕**」。

⇒ 本項若於升級時要掛 Initiative `WF-REDESIGN1`，即屬「中途追加子卡」，須需求方另作升級裁定並留痕。⛔ 本則不代為裁定該項。


## Comment 5508207949 · 2026-09-02T10:34:15Z

## 補登：拆出時 PM 未提供的依據（2026-09-02）

**轉錄來源自述**：本則由 PM session `cc0a7952-07a5-4978-8d03-8b5f48fbc690` 撰寫；GitHub token 為 `ruan6047`，決定者為**需求方本人**（同日逐字「甲」＝維持拆出、「甲，父卡 bump 基線後跑 amend」）。

### 一 · 本項是父卡 discovery brief 拆卡定稿表的第一項

`docs/research/drafts/WORKFLOW-REDESIGN-INITIATIVE-BRIEF.md:57` 逐字：

> | W3′ | CLI 內部：**Log→留言（7 persistent sinks＝open 1＋append 6）**／fenced JSON／doctor 抽出／拒絕訊息全集（開卡時 artifact 重量）／find_conflicts／snapshot | T3 | 獨立查核 |

同檔「**存活的反駁（＝待驗證假設）**」另有三條逐字綁在本項上：

- 「（R9–13 累增）epoch＋dual reader 的部署可行性——**W3′ 執行期 spike**」
- 「（R9–13 累增）journal 多 session 同時 retry 同 op 的行為——未 spike；envelope 整份重用使最壞為同 hash 重複」
- 「（R9–13 累增）reader 按 op id 去重＋corruption gate 的實作可行性——**W3′ 執行期第一步**」

⚠️ **PM 於 2026-09-02 建議拆卡時，未告知上述任何一項。** 需求方當時的裁定依據不完整；本則為補齊。

### 二 · 補齊後維持原裁定的理由

父卡 `ruan6047/ai-workflow#177` 驗證逐字：「對照 discovery brief 的待驗證假設**逐項有處置留痕（驗證／降級／延後）**」⇒ **「延後」是明文允許的處置**，標「延後至本項」即合規。

拆出的兩條原始依據量測未變：該條佔草稿全部驗收字數 **61.6%**（3,737 / 6,064 bytes）；非終態卡離 body 上限最緊者 `ruan6047/ai-workflow#137` 依自身均值仍可寫 **≈57 則**，而歷史平均一張卡一生 **≈10 則**（2,175 則 ÷ 216 張）。

### 三 · 父卡 cascade 已完成（`scope` 級）

依 `templates/baseline-cascade.md` §2–§3：

- 父卡 `#177` `spec 基線` **`93bb8c086f0cf8870537390511b5f0aa2d037c97` → `7d798062b9b37be3ab98d1de58ceebaf42bdcc2e`**（op `70dcc44a`，附註遺失後以 op `6b5ae6e3` 補回）
- 受影響卡與級別：`#221` **`scope`**（驗收 6→8 條，已 amend，op `efdad853`／`7fa2ddee`）；`#214`／`#217`／`#219`／`#220` **`none`**（皆終態，依 `baseline-cascade` 逐字「已合併卡不回改」）
- 上述三條待驗證假設之處置＝**延後至本項**
- ⚠️ 父卡卡面**⛔ 無「基線變更紀錄」章節**（`templates/baseline-cascade.md:7` 逐字指定它為基線載體，而 `amend` 無新增章節旗標）⇒ 本次紀錄落父卡 **Log** 與 `#221` 的 `issuecomment-5508136680`。此落差**已登記、⛔ 未處置**。

### 四 · 開卡前置（重申，⛔ 未變）

父卡 `#177` 驗收逐字「四波五卡…全數誕生於本卡規劃階段並各自結案；**中途追加子卡須升級裁定留痕**」⇒ 本項若於升級時要掛 Initiative `WF-REDESIGN1`，即屬中途追加子卡，須需求方另作升級裁定。⛔ 本則不代為裁定。


## Comment 5508681939 · 2026-09-02T11:16:39Z

## 更正：母體判準錯誤（2026-09-02）

**轉錄來源自述**：本則由 PM session `cc0a7952-07a5-4978-8d03-8b5f48fbc690` 自撰；GitHub token 為 `ruan6047`。⛔ 非需求方裁定——是 PM 對自己前一則留言（`issuecomment-5503141006`）的更正。

### 錯在哪

該則 §依據 3 逐字寫「**非終態卡 50 張**中離 body 上限最緊者為 `ruan6047/ai-workflow#137`」。我當時的量法是排除交付狀態 ∈ `{🏁完成, 🛑已停止, 📦已合併}`。

**多排除了 `📦已合併`，那是錯的。** 逐字證據三則：

1. `cli/src/wf_cli/commands/assign_cmd.py:89` 逐字 `TERMINAL_STATUSES = {"🏁完成", "🛑已停止"}`——**⛔ 不含 `📦已合併`**；`:233` 的交集檢查即以它 `continue`
2. `cli/src/wf_cli/cleanup.py:19` 逐字「**終態列舉**：`commands/assign_cmd.TERMINAL_STATUSES` 是**既有權威，直接 import**」（`:141` 實際 import）
3. `AI_WORKFLOW.md:741` 逐字：「**現役的定義含 `📦已合併`**：只要卡未走完結案收尾就仍佔交集檢查。停在 `📦已合併` 不收尾＝**假活卡，會把後續卡卡死**」

⇒ 我排除的 4 張，正是 `AI_WORKFLOW.md:176` 逐字點名的「上述快照顯示**四張卡正停在該值**，最久 **20 天**」。

⚠️ 本項由 `WF-REDESIGN-W3` 的規劃者（session `c180d66f-f0b9-4c0a-8e16-52a30df4269a@Claude Code`）於 2026-09-02 反駁 PM 的判準時指出，PM 以碼常數 `import` 獨立重驗後接受。

### 更正後的值

以 `TERMINAL_STATUSES` 為準：**活卡 55 張**（⛔ 非 50），其中 `📦已合併` 4 張全為 cpbl：`INGEST-GAME-TM-REFACTOR1`（資源宣告 0 條）／`UX-GAME-PA1`（0）／`UX-HOME-LIVE-STRIP1`（0）／`DATA-TIE-REMEDY1`（1 條）。

### ⭐ 結論不變

以正確母體重算，前一則的兩個關鍵數字**逐位元不變**：

- 最大 body 仍為 `ruan6047/ai-workflow#57`（`WF-WORKTREE-REPO-OWNERSHIP1`，`⏸阻塞`）**32,459 字元＝上限 129,486 的 25.1%**
- 離上限最緊者仍為 `ruan6047/ai-workflow#137`（`WF-REVIEW-SERVICE-GOAL1`，`⏸阻塞`），依自身「Log 字元 ÷ Log 事件數」推算仍可寫 **≈57 則**

⇒ 那 4 張 `📦已合併` 的 body 皆小，⛔ 不進前五。**本項排在 `WF-REDESIGN-W3` 結案之後的裁定⛔ 不受影響。**

⚠️ 「多久撞上限」仍為外推、⛔ 非量測（同前則）。

