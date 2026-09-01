# ai-workflow — 跨專案 AI 協作治理 (Governance)

多 AI／多模型協作的**中央治理專案**。規則只有一個家：本 repo。各專案採用後，只在自己 repo 放**指向本檔的 stub**與自己的狀態面；部署平台由各專案自訂，依 canonical contract 回報狀態。

## L0 · 三分鐘上手（讀這裡就好，其餘用查的）

**要讀的只有三塊，⛔ 不要通讀 canonical：**

1. [`AI_WORKFLOW.md`](AI_WORKFLOW.md) **§1 角色與所有權**——誰規劃、誰執行、誰查核，以及「同卡同輪一人一角」。
2. [`AI_WORKFLOW.md`](AI_WORKFLOW.md) **§2 不可違反的規則**——踩到就是紅線的那幾條。
3. 下面那張「一分鐘心智模型」。

§1／§2 就排在 §0 之前，⛔ 不需要先捲過分類與狀態表。**其餘一律用查的**——canonical 是查詢對象，⛔ 不是入門讀物。

### 一分鐘心智模型

- **規則本體＝ [`AI_WORKFLOW.md`](AI_WORKFLOW.md)**，唯一權威。衝突時以它為準；程式碼與文件衝突時以程式碼為準。
- **一件事一張卡。** 卡由**待審清單項升級**而來（`wfcli open --from-issue` 是唯一路徑），⛔ 不直接開 issue。收件條件見 [`stage-rules/list-intake-requirements.md`](stage-rules/list-intake-requirements.md)。
- **狀態面只有一個寫入通道**＝ [`cli/`](cli/README.md) 的 `wfcli`。不經它的狀態寫入（例如在 GitHub UI 手改欄位）即違規。
- **一張卡走階段**，每個階段跑同一個五步迴圈：① 印注意事項 → ② 派工 → ③ 交回 → ④ 對完整性 → ⑤ 路由。
- **`stage-rules/＝八份 SOP，① 印給你、③ 逐條回`**——八份指八個階段（需求／研究／規劃／執行／審核／部署／維護／結案）各一份；同目錄另有三份角色準則（PM／執行者／查核者）與一份清單收件條件，那四份不是階段檔。
  ⚠️ 「① 印給你」的**機械列印尚未生效**（機制歸 `WF-REDESIGN-W3`；沿 canonical §0.1 先例，⛔ 不啟用尚無 writer 的規則）。在那之前 ① 由 PM 人工把該階段 §5 的編號清單交給執行者，③ 的逐條回應照跑。
- **交接一律走範本**：派工包／交付報告／派審詞／裁決／狀態變更裁定單，全部在 [`templates/`](templates/)，共用同一個四段信封。
- **改規則＝一張卡**：開分支 → 獨立審核（≠ 執行者）→ merge main。規則錯了影響全專案 ⇒ 視為 🔴 紅線，審核**必換模型家族或使用者 sign-off**。

### 現況要用查的，⛔ 不寫在入口

入口只指向**不會變的東西**。活卡、範本清單、目錄內容一律查：

```bash
gh project item-list 4 --owner ruan6047        # 本 repo 的活卡（狀態面）
ls stage-rules/ templates/                     # SOP 與交接範本的實況
```

⛔ 本檔**不列**檔案樹——上一版列了，然後它就爛了：樹上有六個檔早已不存在，而那一段自己寫著「與 `ls` 實況一致」。清單型入口的壽命以「下一次有人加減檔案」計，`ls` 沒有這個問題。

## 這是什麼／不是什麼

- **是**：規則的單一權威來源（who plans / implements / reviews、分支制、部署閘門、獨立性紅線、留痕格式）。
- **不是**：任務集中地。任務住各專案自己的狀態面。

## 往下走

| 你要做的事 | 去哪 |
|---|---|
| 新專案採用本工作流 | [`ADOPTION.md`](ADOPTION.md) |
| 查某個階段該產出什麼 | [`stage-rules/`](stage-rules/) 對應階段檔 |
| 組裝派工／派審／交付／裁決文件 | [`templates/`](templates/)；範本異動對照見 [`templates/template-migration-map.md`](templates/template-migration-map.md) |
| 判一張卡該派多強的模型 | [`MODEL_ROUTING.md`](MODEL_ROUTING.md)、[`tier-rules.md`](tier-rules.md) |
| 跑 `wfcli` | [`cli/README.md`](cli/README.md) |
| 在本 repo 內工作的 AI 準則 | [`AGENTS.md`](AGENTS.md)（工具中立）／[`CLAUDE.md`](CLAUDE.md)（Claude Code） |

## 自我治理 (dogfooding)

本 repo **受自己定義的機制管理**：改規則走一張卡、獨立審核、merge main。卡的現況查上面那條 `gh project item-list`；結案卡與封存 Ledger 在 [`archive/`](archive/)。
