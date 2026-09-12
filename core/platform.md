---
name: platform
when: 設定 repo、改 ruleset、改 CI、判一條硬擋是不是平台委託時讀
non_scope: ⛔ 不寫 CLI 側硬擋 D1–D4（住 core/verbs.md §2）；⛔ 不寫怎麼操作 GitHub UI
last_confirmed: 2026-09-05
---

# 平台委託 P1–P5

## 1 · 資料模型

每條＝規則一句＋執行 artifact 的**穩定身分**：平台規則型別、repo 設定鍵、CI job 名、腳本路徑。只有新增、刪除或改寫一條 P 時才改本檔。

artifact 的**當下值**⛔ 不寫在本檔：ruleset 的數字 id 與名稱、required check 的 context 集合、merge 按鈕的開關狀態、第三方 action 的版本 pin。改動這些值⛔ 不需回改本檔；要知道當下值用 §2 的唯讀查法現查。

| # | 規則 | 執行 artifact（穩定身分） |
|---|---|---|
| P1 | main 禁改史、禁刪 | 預設分支 ruleset 的規則型別 `deletion`、`non_fast_forward`、`required_linear_history`，bypass 清空 |
| P2 | T2 以上走分支＋獨立查核；執行者不 merge | 預設分支 ruleset 的規則型別 `required_status_checks`：required check 未綠的 commit ⛔ 不進 main。本條委託給平台的只有這一項；走分支與 PR、獨立查核、執行者不 merge 都由紀律承擔，平台⛔ 不擋（`core/tiers.md` §1、`roles/conduct-common.md` §1） |
| P3 | 合併方式＝專案層 `merge_method`，由平台強制 | repo 設定鍵 `allow_merge_commit`／`allow_squash_merge`／`allow_rebase_merge`：只留 `.wf/modules.json` `merge_method` 指定的那一顆 |
| P4 | secrets 不進 git | CI job `secret-scan`（`.github/workflows/ci.yml`，`gitleaks/gitleaks-action`） |
| P5 | commit trailer 鍵在允許集合且為末端連續單一區塊 | CI job `commit-trailer`（`.github/scripts/trailer_check.py`） |

- ⚠️ P5 的已知漏洞（2026-09-06 起）：合併訊息由平台預設組時 trailer 會被空行切散，本檔擋不到；訊息組法的居所＝`core/verbs.md` §1 brief 列（`brief --for closeout` 印 squash 訊息），⛔ 不由平台預設組。
- P5 允許集合＝Requested-by、Planned-by、Implemented-by、Reviewed-by、Co-Authored-By；哪些必須出現＝約定，住 `roles/conduct-common.md` §2，CI ⛔ 不驗。
- P2 的獨立性判定（不同實體、跨家族）是 PM 注意事項，⛔ 不機械化。
- 平台擋不到的（UI 手改投影欄、繞過 `core/tiers.md` §1 該級別的交付路徑直推 main）＝紀律，住 `roles/conduct-common.md` §1。
- 新增平台委託須需求方裁定；⛔ 不加沒有被測物的 CI job。

## 2 · 唯讀查法

`{owner}`／`{repo}`／`{branch}` 自填（`{branch}`＝預設分支）；查到的值只在當下用，⛔ 不回寫本檔。⛔ 不用三重反引號圍欄是刻意的——`core/*.md` 的圍欄只給 CLI 讀的宣告區塊用（`cli/tests/test_compose_blocks.py` 對帳圍欄數與區塊數），散文指令一律走行內碼；⛔ 不得推出「本檔不該寫指令」。

- 生效於該分支的規則型別（P1、P2）：`gh api "repos/{owner}/{repo}/rules/branches/{branch}" --jq '[.[].type]'`
- 哪些 CI job 現在被設為 required check（P2）：`gh api "repos/{owner}/{repo}/rules/branches/{branch}" --jq '[.[]|select(.type=="required_status_checks").parameters.required_status_checks[].context]'`
- ruleset 清單與其數字 id、名稱、目標、enforcement（P1、P2）：`gh api "repos/{owner}/{repo}/rulesets" --jq '[.[]|{id,name,target,enforcement}]'`
- merge 按鈕現在開哪幾顆（P3）：`gh api "repos/{owner}/{repo}" --jq '{allow_merge_commit,allow_squash_merge,allow_rebase_merge}'`
- 負控（`roles/conduct-common.md` §1）：`gh api "repos/{owner}/{repo}/rules/branches/{不存在的分支}" --jq 'length'` 回 `0`；上面四條的非空回傳因此⛔ 不是恆真。
- P4 的 action 版本 pin ⛔ 不在本檔登記，讀 `.github/workflows/ci.yml` 該 step 的 `uses:` 與其後的版本註解。
- 查到的當下值與本檔對不上時，先判它是不是 §1 列的當下值：是 ⇒ 平台改了、本檔⛔ 不需動；否 ⇒ 穩定身分變了，開卡改本檔（`core/tiers.md` §3 `sensitive` 含 `rules`）。
