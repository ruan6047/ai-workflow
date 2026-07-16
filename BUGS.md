# BUG 滾動 log — ai-workflow

> **T2 快線** bug 的流水痕跡（canonical §3）：根因已知、改動局部、可逆 → 分支、先寫失敗回歸測試、修到綠、獨立輕量查核、merge，於此滴一行。T1 純文案／typo 只留 commit 說明。
> **慢線** bug（根因不明／跨檔／高風險）→ 開卡於 [`tasks/`](tasks/)、見 [`TASKS.md`](TASKS.md)。
> git 是程式碼／文件事實來源；adapter event log 是作業狀態事實來源。行數過多時把舊行移 [`archive/`](archive/)。
>
> 格式：`- <ISO 8601> <症狀> → <commit/SHA> (by <模型@工具>；iteration <n>；回歸測試 <檔:test>；查核 <actor>)`

---

_（本 repo 為文件治理、幾無程式碼 bug；此檔為 canonical 範例＋dogfood 佔位。各採用專案於自身 repo 起一份。）_
