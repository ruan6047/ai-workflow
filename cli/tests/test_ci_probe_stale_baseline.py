"""DEV-AIWF-MINIMAL-CI1 取證探針：陳舊基線的語意衝突。**DO NOT MERGE。**

這支檔案模擬「一張卡在 02b5d9a 這個基線上開工、寫了一條對當時 cli.py 內部結構為真的
測試」。它在自己的分支頭上是綠的；併入 main 之後是紅的——因為 a7e5e21
（DEV-CLI-VERB-REGISTRY1，#59）把動詞註冊從 cli.py 的 import 區塊改成
commands/__init__.py 的 COMMAND_MODULES tuple，cli 模組命名空間不再有那些屬性。

兩邊改的是不同檔案，`git merge-tree` 沒有文字衝突可報。只有跑在**合併結果**上的
測試看得見，而 `pull_request` 事件取的正是合併結果（refs/pull/N/merge）。

這就是 2026-08-12 事故的形狀，用今天的 main 重現。取證後即關閉 PR，不合併。
"""

from __future__ import annotations

from wf_cli import cli


def test_verb_modules_reachable_from_cli_namespace() -> None:
    # 基線 02b5d9a 的 cli.py：`from .commands import (amend_cmd, assign_cmd, ...)`
    # 這些名字因此是 wf_cli.cli 的模組屬性。
    for name in ("open_cmd", "assign_cmd", "review_cmd", "doctor_cmd"):
        assert hasattr(cli, name), f"wf_cli.cli 沒有屬性 {name}"
