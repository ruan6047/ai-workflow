"""機械檢查：open 的必填欄、handoff 的 source SHA／證據格式。

集中在這裡是因為卡面把「機械檢查」列為紅線相關的驗收條件（open 的必填欄、
handoff 的 SHA／證據），測試要能單獨鎖住這些規則，不want 散在各 command 裡各自
判斷、drift 出不一致的檢查標準。
"""

from __future__ import annotations

import re

from .card import TIERS
from .resources import DB_SCOPES, ResourceDeclaration

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ValidationError(ValueError):
    """攜帶多筆錯誤訊息，讓呼叫端一次印出全部而非一個一個修。"""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("；".join(errors))


def validate_source_sha(sha: str) -> None:
    if not SHA_RE.fullmatch(sha or ""):
        message = (
            f"source_sha 必須是完整 40 字元小寫 hex SHA，收到 {sha!r}"
            "（不接受 branch name、短 SHA 或未提交工作區——見 handoff-contract.md §1）"
        )
        raise ValidationError([message])


def validate_evidence(evidence: str) -> None:
    if not evidence or not evidence.strip():
        raise ValidationError(["證據欄必填，不得為空字串"])


def validate_open_fields(
    *,
    card_id: str,
    feature: str,
    tier: str,
    core_pain: str,
    service_goal: str,
    db_scope: str,
    resources: ResourceDeclaration | None,
) -> None:
    """open 的機械檢查：核心痛點、服務的原始目標、tier、db_scope、資源宣告。"""
    errors: list[str] = []
    if not card_id or not card_id.strip():
        errors.append("卡ID 必填")
    if not feature or not feature.strip():
        errors.append("功能 必填")
    if tier not in TIERS:
        errors.append(f"tier 必須是 {TIERS} 之一，收到 {tier!r}")
    if not core_pain or not core_pain.strip():
        errors.append("核心痛點 必填")
    if not service_goal or not service_goal.strip():
        errors.append("服務的原始目標 必填")
    if db_scope not in DB_SCOPES:
        errors.append(f"db_scope 必須是 {sorted(DB_SCOPES)} 之一，收到 {db_scope!r}")
    if resources is None:
        errors.append("資源宣告必填（至少 db_scope；resources 可為空陣列）")
    elif resources.db_scope != db_scope:
        errors.append(
            f"資源宣告內 db_scope（{resources.db_scope!r}）與 --db-scope（{db_scope!r}）不一致"
        )
    if errors:
        raise ValidationError(errors)


__all__ = [
    "SHA_RE",
    "ValidationError",
    "validate_evidence",
    "validate_open_fields",
    "validate_source_sha",
]
