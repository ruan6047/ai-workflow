# 責任表述不一致的母體（36 組）

> 產生者：`gpt-6-astra`，2026-09-10，基線 `f70c7ef2b7903b2cddac0f9b90418413d830dc9e`。
> **⛔ 覆蓋率未知。** 產生者逐字：「這是全檔掃描後的**人工語意歸組**，不是程式能證明『所有語意衝突皆已找到』的數字；36 也不是缺陷數。」
> 本檔是**已知待裁定集合**，⛔ 不是完整性宣稱（決策紀錄逐字：「⛔ 不得再寫『清盡』『零殘留』這類完整性宣稱」）。

## 產生方式（可稽核，但⛔ 不能取代固定交付邊界）

文件母體＝`core/`、`roles/`、`stages/`、`modules/` 全檔。基線與規模逐字量測：

```
$ git rev-parse HEAD
f70c7ef2b7903b2cddac0f9b90418413d830dc9e
$ python3 - <<'PY'
from pathlib import Path
for root in ('core','roles','stages','modules'):
    files=sorted(p for p in Path(root).rglob('*') if p.is_file())
    print(f'{root}: {len(files)} files, {sum(len(p.read_text().splitlines()) for p in files)} lines')
PY
core: 13 files, 682 lines
roles: 5 files, 222 lines
stages: 5 files, 238 lines
modules: 11 files, 682 lines
```

合計 **34 檔、1,824 行**。歸組準則＝「同一動作／欄位、相同或可能重疊的適用情境，其執行者被寫在兩處」。

**限制**：歸組是人工語意判讀；「判相容」是產生者的評估、⛔ 不是事實，可被反例推翻。優先度「高／中／低」是報告建議，⛔ 不是框架的 P- 編號。

## 三種機制（產生者的分類，⛔ 不是裁定）

1. **把不同責任壓成「誰填／誰做」**——起草、核可後轉錄、操作工具、工具實際寫入混在一起。
2. **例外沒有接回通則，或適用範圍遺失**——PM 自審、代貼、低級別兼任、查核者寫 notes。
3. **判斷權與副作用邊界未定義**——實質抽查、子卡影響分析、研究反測，以及 `review` 自動修復投影。

產生者同時舉了反證（#17／#21／#27）：**責任分散寫在不同檔仍能相容**，故「責任只能住一處」⛔ 既不是已證根因、也不是必要修法。

## 36 組

PM 於落檔時自驗的分佈（`grep -o` 逐組數，編號 1–36 完整無缺口）：

```
判讀   張力 11 ／ 待釐清 11 ／ 相容 14        （張力＋待釐清 ＝ 22）
優先度 高 14 ／ 中 8 ／ 低 14
```

⚠️ 「相容」那 14 組是產生者的評估。依 `roles/pm.md` F-PM-09 逐字「兩份不同作者的自評⛔ 不混為一份」，**14 組仍須受審、⛔ 不豁免**；查核者提出反例且成立時就地改判並處理，⛔ 不算新增第 37 組、⛔ 不算擴射程。

mise WARN  failed to write cache file: /Users/ruanruan/Library/Caches/mise/lua/5.5.0/exec_env_f7585075c2323b5b-f6f83.msgpack.z Operation not permitted (os error 1)
```

以下引號均為連續逐字節錄。**優先度「高／中／低」是本報告建議，不是框架的 P- 編號。**

| #／判讀 | 同一動作的兩處依據逐字 | 具體建議 |
|---|---|---|
| **1 高・張力：驗收／驗證誰填** | `core/card-schema.md:79`：「\| acceptance（≥1）、verification（≥1） \| PM \| 離開規劃前 \| brief、R3 \|」；`stages/planning.md:34`：「執行者：寫規格、驗收條件、驗證項目」 | 分清起草、落欄、判定、核可；WF-001 的個案裁定不能自動升成全框架通則。 |
| **2 高・待釐清：另兩個規格欄** | `core/card-schema.md:77`：「feature、non_scope、stage_plan、list_convergence、tier、tier_basis、exec_capability、review_capability、db_scope、resources、when \| PM」；`stages/planning.md:28`：「執行者 `edit` 規格欄」；四欄定義在 `core/card-schema.md:85`：「規格欄＝acceptance／verification／non_scope／resources」 | 建卡初填與規劃修訂可能分工不同；把 `non_scope`、`resources` 一起處理，不能只修 #1。 |
| **3 高・張力：規格實際落欄** | `stages/planning.md:28`：「執行者 `edit` 規格欄」；`roles/pm.md:38`：「需求方裁定改到規格欄時以 `edit --ruling` 落卡面」 | 區分草案首次填寫、核可後轉錄、後續修訂，逐情境指定操作人。 |
| **4 高・待釐清：執行者修資源宣告** | `stages/implementation.md:45`：「交回前對照 `git diff --name-status` 修正資源宣告的漏列交付檔、宣告過寬、不存在路徑。」；`core/card-schema.md:77` 將 `resources` 指派 PM | 指定執行者是提修訂清單還是直接改欄；並銜接規格退回程序。 |
| **5 高・張力：更正核心痛點** | `stages/planning.md:47`：「核心痛點的成功條件與裁定矛盾時更正痛點並逐字列排除與歸屬」；同檔 `:34`：「⛔ 不改核心痛點」；`roles/pm.md:25`：「⛔ 不改需求方原文」 | F-規劃-07 必須指定提案者、裁定者與逐字回寫者，不能把「更正」直接丟給當階段執行者。 |
| **6 高・張力：PM 自審** | `roles/pm.md:17`：「以同一份 R1–R4 表自審」；`:23`：「⛔ 不檢查自己的產出」；`:22`：「只判流程，⛔ 不判內容」 | 裁定 PM 是否可做自己的交付前檢查；若可，說清它不具有獨立查核效力，以及是否包含 R3／R4。 |
| **7 中・待釐清：PM 實質抽查** | `roles/pm.md:35`：「注意事項回應實質抽查、每條驗收條件有無著落」；`:15`：「⛔ 不判內容對錯」 | 定義抽查是查證據存在／對應，還是判證據充分；後者已接近內容判斷。 |
| **8 中・待釐清：PM 判子卡影響** | `modules/initiative/module.md:50`：「PM 對照父卡依賴序逐張標受影響卡的影響級別（無影響／需改規格／前提失效／方向失效）」；`roles/pm.md:22`：「只判流程，⛔ 不判內容」 | 區分協調分類與技術影響分析；後者應有執行者提供的依據。 |
| **9 高・待釐清：PM 更新他人規格** | `modules/initiative/module.md:54`：「核可後 PM 更新待辦中受影響卡的規格與 `parent_spec_version`」；`roles/pm.md:24`：「⛔ 不代填、⛔ 不代修、⛔ 不代寫他人產出或判定」 | 核可後逐字同步可以與重新撰寫不同；明寫同步範圍與禁止自由改寫。 |
| **10 高・待釐清：PM 維護階段檔** | `roles/pm.md:56`：「維護 `.wf/stages/<階段>.md` 與卡面 `notes` 只加條目」；`:24`：「只修自己的產出物」；`modules/pitfalls-13/module.md:51`：「同一 repo 既有解法的索引由 PM 寫進專案層 `.wf/stages/<階段>.md`」 | **追加指定條目有正面授權；改既有散文明文不允許。** 仍應明定交付後維護權按條目／內容種類劃分，不以檔案最初作者包辦所有權。 |
| **11 高・張力：查核者追加卡面 notes** | `core/card-schema.md:83`：「任何角色經 `edit --set notes+=`」；`roles/reviewer.md:24`：「裁決留言以外⛔ 不寫任何東西」 | 裁定查核者是否有 notes 追加例外；兩條不可原樣並存。 |
| **12 高・張力：查核者貼候選留言** | `roles/conduct-common.md:34`：「發現候選注意事項即在該卡貼一則 `wf:note`」；`roles/reviewer.md:24`：「裁決留言以外⛔ 不寫任何東西」 | 與 #11 分別裁定：留言與卡面寫入不是同一權限。 |
| **13 高・張力：卡面所有者與 PM 操作** | `roles/conduct-common.md:20`：「交接完成前非所有者⛔ 不動卡、分支、worktree」；`roles/pm.md:12`：「狀態的唯一 writer，只有 PM 跑 `move`」 | 卡面 `owner` 可是執行者；應分開工作產出所有權與 PM 的流程操作權，補交接過程的操作範圍。 |
| **14 高・張力：PM 代貼裁決** | `roles/reviewer.md:37`：「把裁決全文原樣印在最後回覆交需求方或 PM 代貼」；`stages/review.md:38`：「⛔ 不代轉錄內容」 | 保留無網路代貼時，明寫逐字轉載例外及來源標記；禁止改寫判定。 |
| **15 低・相容：需求方裁定由 PM 代貼** | `core/handoff.md:10`：「人填段只由該角色本人填」；`roles/requester.md:14`：「PM 可代貼」 | 作者與傳送者不同即可相容；引用 `roles/conduct-common.md:36` 的「原文從第二行起一字不改」。 |
| **16 中・待釐清：前輪 finding 狀態誰更新** | `core/glossary.md:82`：「finding 狀態 \| `status`：open／resolved／withdrawn，查核者填」；`core/return.md:63`：「`wf-return` 逐條重列前輪 finding 的原 `finding_id` 與新 `status`」 | 後者沒有排除執行者交回單；應明定執行者回報修復證據、查核者確認狀態，或明定兩者各自陳述的效力。 |
| **17 低・相容：第三次退回換人** | `roles/pm.md:45`：「預設換人（換執行者實體），需求方可否決；escalation 模組啟用時依其 delta」；`modules/escalation/module.md:63`：「需求方以一則 `wf:ruling` 四選一裁定」 | 已明示模組啟用時另走其流程，不是 PM 與需求方爭奪同一裁定。 |
| **18 中・待釐清：F-PM-11 要求開卡** | `roles/pm.md:55`：「是實例則先量母體、開一張窮舉卡」；`:25`：「未經需求方明確指示⛔ 不 merge、⛔ 不部署、⛔ 不裁定、⛔ 不開卡」 | 改成提出一張窮舉卡的完整射程，經需求方授權開卡；避免把 F- 注意事項讀成常設授權。 |
| **19 中・張力：T0／T1 的 PM 兼任** | `roles/pm.md:27`：「T0／T1 可兼執行者」；`:46`：「同一張卡同一 iteration 一人一角」 | 後者補相同的級別適用範圍或直接引用兼任條款。 |
| **20 低・相容：執行者不自審與低級別自查** | `stages/implementation.md:34`：「⛔ 不自審」；`core/tiers.md:14`：「審核階段由執行者以 `role=reviewer` 自貼裁決（自查即裁決）」 | 階段不同即可相容；可補級別引用，避免把執行階段禁令帶到 T0／T1 審核階段。 |
| **21 低・相容：PM 合併授權** | `roles/pm.md:25`：「未經需求方明確指示⛔ 不 merge」；`stages/closeout.md:31`：「常態由 PM merge：APPROVE＋裁決完整時直行 merge→收尾」 | `roles/pm.md:26` 已明示「結案直行例外」，例外連結完整。 |
| **22 低・相容：PM 封存與 CLI 封存** | `stages/closeout.md:41`：「PM：merge、收尾、組裁定單、封存」；`core/verbs.md:17`：「進終態即關 issue 並封存」 | PM 操作 `move`、CLI 執行關閉；依 `core/glossary.md:94` 的定義相容。應澄清詞義引用，不直接新增 Project 封存。 |
| **23 低・相容：需求階段派填表與 PM 填欄** | `stages/requirement.md:29`：「PM `brief --for executor` 派填表」；`:36`：「執行者：提供卡面散文素材（觀察、出處）；⛔ 不落欄」 | 同檔已拆素材與落欄；「派填表」可改成「派提供素材」以減少誤讀。 |
| **24 低・相容：需求方填 service_goal** | `core/card-schema.md:78`：「\| service_goal \| 需求方 \| 建卡 \| R1 \|」；`roles/requester.md:26`：「⛔ 不代填表單」 | 填自己負責的欄位不是「代填」他人表單。 |
| **25 低・相容：誰判痛點仍成立** | `stages/requirement.md:34`：「需求方：決定升級、填 `service_goal`、判痛點還成立嗎」；`roles/pm.md:15`：「判完整性（缺段、格數、值域）與 R1 前提、R2 射程」 | `roles/requester.md:13` 已寫「PM 判 R1 後保留否決」；初判與最終否決分工成立。 |
| **26 低・相容：誰做質詢與誰填連結** | `roles/requester.md:17`：「T4 卡離開規劃前做質詢，紀錄落 `wf:log` 留言」；`core/card-schema.md:80`：「\| grilling \| PM（`edit`）」 | 進行質詢與登記紀錄 URL 是不同動作。 |
| **27 低・相容：owner 由 move 或 PM edit** | `core/card-schema.md:82`：「`owner` 在 escalation 換人時由 PM `edit`」；`modules/escalation/module.md:64`：「此邊⛔ 不是派工邊，`--actor` 不寫 owner」 | 通則已有具名例外，沒有必要另建優先序。 |
| **28 中・待釐清：實際分支誰登記** | `modules/resource-lock/module.md:54`：「認領時把實際 worktree 路徑與分支寫回卡面 `worktree`、`branch`」；`core/naming.md:19`：「一卡一分支，名 `wf/<card_id>`；`move` 到執行／進行中時寫回 `branch`」 | 指定認領的操作者、登記時點，以及模組是否允許實際分支偏離固定命名；目前前者省略主詞。 |
| **29 低・相容：快照誰做** | `modules/snapshot/module.md:42`：「PM 每 `params.schedule`（種子 daily）跑一次 `snapshot`」；`core/verbs.md:22`：「本機 JSON＋Markdown」 | PM 啟動／保存、CLI 產生檔案是上下游分工；模組 `:43` 另要求 commit 輸出。 |
| **30 中・待釐清：研究查核是否判結論** | `modules/research/module.md:65`：「只驗可重跑；⛔ 不裁結論真值」；`modules/stat-redline/module.md:47`：「在裁決的對抗性反測表逐角度寫支持／推翻／未能檢定」 | 說清「推翻」的對象是特定測試命題／紅線，還是整體研究結論；目前兩模組可同時啟用。 |
| **31 中・待釐清：研究查核者讀取範圍** | `modules/research/module.md:71`：「研究前先讀該卡全部留言，⛔ 不只讀派工單」；`roles/reviewer.md:13`：「只讀派工單給的東西；無看板讀取權、看不到其他卡」 | 將 F-research-03 指定給研究執行者，或要求 PM 完整附入留言；避免查核者被要求自行擴讀。 |
| **32 低・相容：查核實跑與唯讀** | `roles/reviewer.md:24`：「裁決留言以外⛔ 不寫任何東西」；`modules/resource-lock/module.md:65`：「驗證命令會改 tracked file 時在拋棄式 worktree 執行；查核沙箱無 lease、無 owner」 | 結合 `roles/reviewer.md:26` 的密封探針／容器條款，可解為隔離驗證例外；建議把「不寫」限定到權威產出與狀態面。 |
| **33 低・相容：父子卡要求三人分離** | `modules/initiative/module.md:51`：「觸發者（執行者）、評估者（PM）、核可者（需求方）⛔ 不合於一人」；`roles/pm.md:27`：「T0／T1 可兼執行者」 | 通則允許兼任不等於要求兼任；啟用模組後三者分離仍可同時滿足。 |
| **34 高・張力：查核者跑 review 卻可能改狀態面** | `stages/review.md:29`：「查核者 `review --file --role reviewer` 貼裁決」；`core/verbs.md:33`：「下一次動詞先對帳卡面 JSON 與五個投影欄；不等＝以卡面 JSON 重寫該欄後續跑」；`roles/reviewer.md:24`：「⛔ 不動狀態面」 | 指定自動修復投影是否算查核者被禁止的操作；目前指派的命令與紅線沒有共同可操作的說明。 |
| **35 高・張力：notes／brief 寫入責任** | `core/verbs.md:19` 的寫欄：「無」；`:20`：「無；stdout 由 PM 貼進留言」；同檔 `:33`：「以卡面 JSON 重寫該欄後續跑」 | 動詞表明列共通對帳／拒收留言副作用，或引用共通寫入例外；不能把兩動詞無條件稱為唯讀。 |
| **36 低・相容：來源 SHA 誰提供** | `roles/executor.md:13`：「推分支到 origin、回報 40 碼來源 SHA」；`core/verbs.md:21`：「executor＝卡面 `branch` 在遠端的分支頭」 | 執行者報告與 CLI 取權威來源是不同責任；兩者不符應揭露，不能互相冒充。 |

這是**全檔掃描後的人工語意歸組**，不是程式能證明「所有語意衝突皆已找到」的數字；36 也不是缺陷數。特別是 #11／#12、#34／#35，雖共用禁止條款，處理的是不同寫入動作，故分列。

