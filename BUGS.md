# BUG 滾動 log — ai-workflow

> **快線** bug 的流水痕跡（canonical §2.1）：根因已知、改動局部 → 免開卡，先寫失敗回歸測試 → 修到綠 → 審核一次 → merge，於此滴一行。
> **慢線** bug（根因不明／跨檔／高風險）→ 開卡於 [`tasks/`](tasks/)、見 [`TASKS.md`](TASKS.md)。
> git 為單一事實來源。行數過多時把舊行移 [`archive/`](archive/)（§6.4 算力衛生）。
>
> 格式：`- MM-DD <症狀> → <commit> (by <模型@工具>；回歸測試 <檔:test>)`

---

_（本 repo 為文件治理、幾無程式碼 bug；此檔為 canonical 範例＋dogfood 佔位。各採用專案於自身 repo 起一份。）_
