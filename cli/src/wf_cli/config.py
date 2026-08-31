"""跨專案目標解析：``--repo``／設定檔／環境變數決定這次指令打哪個 owner/Project/repo。

優先序（高到低）：CLI flag > --config 指定的設定檔 > 環境變數 > 內建預設。
設定檔讓不同下游專案（cpbl-analytics、ai-workflow 本身…）各自存一份
``.wfcli.json`` 而不必每次都打一長串旗標。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    pass


@dataclass
class Target:
    owner: str
    project: int
    repo: str | None = None  # 例如 "ruan6047/cpbl-analytics"；None＝本次指令沒有指定 repo


def _load_config_file(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"設定檔不存在：{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"設定檔 {path} 不是合法 JSON：{exc}") from exc


def resolve_target(
    *,
    owner: str | None = None,
    project: int | None = None,
    repo: str | None = None,
    config: str | None = None,
) -> Target:
    cfg: dict = {}
    if config:
        cfg = _load_config_file(Path(config))

    resolved_owner = owner or cfg.get("owner") or os.environ.get("WFCLI_OWNER")
    resolved_project = project if project is not None else cfg.get("project")
    if resolved_project is None:
        env_project = os.environ.get("WFCLI_PROJECT")
        resolved_project = int(env_project) if env_project else None
    resolved_repo = repo or cfg.get("repo") or os.environ.get("WFCLI_REPO")

    if not resolved_owner:
        raise ConfigError("缺少 --owner（或設定檔 owner／環境變數 WFCLI_OWNER）")
    if resolved_project is None:
        raise ConfigError("缺少 --project（或設定檔 project／環境變數 WFCLI_PROJECT）")

    return Target(owner=resolved_owner, project=int(resolved_project), repo=resolved_repo)


def add_target_args(parser) -> None:
    parser.add_argument("--owner", help="GitHub owner（user/org）；預設讀設定檔或 WFCLI_OWNER")
    parser.add_argument("--project", type=int, help="Project number；預設讀設定檔或 WFCLI_PROJECT")
    parser.add_argument(
        "--repo",
        help="owner/repo；amend／review／handoff 改 body 或留言時需要它。"
        "⚠️ `open` 的 repo 由 --from-issue 的 URL 決定（`WF-REDESIGN-W1` 驗收 2 之後"
        "它不再建立任何 Issue），此旗標在 open 上只用來**交叉核對**：與 URL 不一致即拒收。",
    )
    parser.add_argument("--config", help="JSON 設定檔路徑（可存 owner/project/repo 預設值）")


__all__ = ["ConfigError", "Target", "add_target_args", "resolve_target"]
