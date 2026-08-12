"""⚠️ 拋棄式取證檔案 — DO NOT MERGE。

本檔**不是**任何卡的交付物，只為 DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1（#73）重現
2026-08-12 的事故形狀：**分支在自己的基線上綠、併進 main 之後才紅**。

它刻意複製 `test_release_cleanup.py` 當初的處境，而不是另造一個容易紅的例子：

- 本檔的**主題**是「open 寫進 Issue body 的資源宣告區塊」，與能力層級旗標無關。
  旗標只出現在 setup 的呼叫慣例裡——事故的碰撞就是這種**附帶**碰撞，不是正面衝突。
- `_open_argv()` 使用基線 `7451b72` 當下**合法且完整**的 `open` 呼叫慣例。
  `WF-CLI-ROUTING-TIER1` 的 `26a0149` 之後才多出四個必填旗標，
  而 `git merge-base --is-ancestor 26a0149 7451b72` 為否——本檔的基線從未見過它們。
- 本檔是**新增檔**，main 上不存在同名檔，故 `git merge-tree` 這種文字比對
  兩邊各改各的、判為無衝突。這正是 2026-08-12 放行的那個判準。

因此：在 `7451b72` 上 pytest 為綠是**真的**；併進 main 後 argparse 在 setup 期
以必填旗標缺漏拋 SystemExit，與當初 14 個 error 同一個失敗模式。

用完即刪，不得併入 main。
"""

from __future__ import annotations

import pytest
from wf_cli.cli import build_parser
from wf_cli.commands import assign_cmd, handoff_cmd, open_cmd
from wf_cli.project import list_items, resolve_project

from .fake_gh import FakeGhRunner

BASE_TARGET = ["--owner", "acme", "--project", "1"]
CARD_ID = "GATE-EVIDENCE-SANDBOX1"


@pytest.fixture
def fake_runner(monkeypatch):
    runner = FakeGhRunner()
    for module in (open_cmd, assign_cmd, handoff_cmd):
        monkeypatch.setattr(module, "default_runner", runner)
    return runner


def _open_argv(card_id: str) -> list[str]:
    """基線 7451b72 當下合法且完整的 open 呼叫慣例。

    ⚠️ 這裡沒有 --exec-capability／--exec-capability-reason／--review-capability／
    --review-capability-reason，**不是漏寫**：在本檔的基線上它們還不存在。
    """
    return [
        "open", *BASE_TARGET, card_id,
        "--feature", "取證用沙箱卡",
        "--tier", "T3",
        "--db-scope", "none",
        "--core-pain", "痛點文字",
        "--service-goal", "服務的原始目標文字",
        "--resources", "file:cli/src/wf_cli/cli.py",
    ]


def test_open_writes_the_resource_claim_block_into_the_issue_body(fake_runner):
    """主題與能力旗標無關：驗 open 把資源宣告寫進 body。"""
    parser = build_parser()
    args = parser.parse_args(_open_argv(CARD_ID))
    assert args.func(args) == 0

    project = resolve_project(fake_runner, "acme", 1)
    items = list_items(fake_runner, project)
    assert len(items) == 1
    item = items[0]
    assert item.fields["卡ID"] == CARD_ID
    assert "## 資源宣告" in item.body
    assert "file:cli/src/wf_cli/cli.py" in item.body


def test_open_records_the_tier_on_the_ledger_item(fake_runner):
    parser = build_parser()
    args = parser.parse_args(_open_argv(CARD_ID))
    assert args.func(args) == 0

    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["級別"] == "T3"
    assert item.fields["交付狀態"] == "📥Backlog"
