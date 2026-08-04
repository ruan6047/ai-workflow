"""``gh`` CLI 底層包裝：所有對 GitHub 的呼叫都走這裡，方便測試時整體 mock。

刻意不用任何第三方 GitHub SDK——``gh`` 已經處理好認證與 rate limit，且環境已登入
（見卡面「gh CLI 已登入 ruan6047，具 project scope」）。所有 subprocess 呼叫集中在此模組，
其餘模組只呼叫這裡的函式，測試時只需 mock ``run``/``run_json``/``graphql`` 三個入口。
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


class GhError(RuntimeError):
    """``gh`` 呼叫失敗（非 0 退出碼）。"""

    def __init__(self, args: Sequence[str], returncode: int, stderr: str) -> None:
        self.args_used = list(args)
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(
            f"gh {' '.join(args)} failed (exit {returncode}): {stderr.strip()}"
        )


@dataclass
class GhRunner:
    """可替換的 gh 執行器；測試用假物件覆寫 ``execute`` 即可整包 mock。"""

    binary: str = "gh"

    def execute(self, args: Sequence[str], input: str | None = None) -> str:
        proc = subprocess.run(
            [self.binary, *args],
            input=input,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise GhError(args, proc.returncode, proc.stderr)
        return proc.stdout

    def run_json(self, args: Sequence[str]) -> Any:
        out = self.execute(args)
        if not out.strip():
            return None
        return json.loads(out)

    def graphql(self, query: str, **variables: str) -> dict:
        """執行一次 GraphQL query／mutation，變數一律以字串型別傳入（``-f``）。

        注意：刻意不使用 ``gh project item-list --format json`` 讀欄位值——
        該指令對中文欄位名稱的 JSON key 有已知編碼錯誤（見
        ``OPS-STATE-PLANE-MIG1_field_mapping.md``「意外發現與操作陷阱」）。
        所有批次讀取一律走這裡的原生 GraphQL。
        """
        args = ["api", "graphql", "-f", f"query={query}"]
        for key, value in variables.items():
            args += ["-f", f"{key}={value}"]
        out = self.execute(args)
        return json.loads(out)


# 模組層級預設實例；commands/* 直接 import 這個，測試以 monkeypatch 替換其方法。
default_runner = GhRunner()
