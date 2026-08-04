from __future__ import annotations

import pytest

from wf_cli.resources import ResourceDeclaration
from wf_cli.validation import (
    ValidationError,
    validate_evidence,
    validate_open_fields,
    validate_source_sha,
)


def test_valid_full_sha_passes():
    validate_source_sha("a" * 40)  # 不拋例外即算通過


@pytest.mark.parametrize(
    "bad_sha",
    [
        "short",
        "a" * 39,
        "a" * 41,
        "ai/claude-sonnet-5/DEMO-CARD1",  # branch name，非 SHA
        "ABCDEF0123456789ABCDEF0123456789ABCDEF01",  # 大寫不接受（既有慣例小寫 hex）
        "",
    ],
)
def test_invalid_sha_rejected(bad_sha):
    with pytest.raises(ValidationError):
        validate_source_sha(bad_sha)


def test_evidence_required():
    validate_evidence("some real evidence")
    with pytest.raises(ValidationError):
        validate_evidence("")
    with pytest.raises(ValidationError):
        validate_evidence("   ")


def _valid_open_kwargs(**overrides):
    kwargs = {
        "card_id": "DEMO-CARD1",
        "feature": "示範",
        "tier": "T3",
        "core_pain": "痛點",
        "service_goal": "目標",
        "db_scope": "none",
        "resources": ResourceDeclaration(db_scope="none", resources=[]),
    }
    kwargs.update(overrides)
    return kwargs


def test_validate_open_fields_accepts_complete_card():
    validate_open_fields(**_valid_open_kwargs())  # 不拋例外


def test_validate_open_fields_reports_all_missing_fields_at_once():
    with pytest.raises(ValidationError) as exc_info:
        validate_open_fields(
            **_valid_open_kwargs(
                card_id="", feature="", tier="T9", core_pain="", service_goal="", db_scope="bogus", resources=None
            )
        )
    errors = exc_info.value.errors
    assert len(errors) >= 6  # 一次列出全部缺漏，而非只回報第一個


def test_validate_open_fields_rejects_db_scope_mismatch_with_declaration():
    with pytest.raises(ValidationError):
        validate_open_fields(
            **_valid_open_kwargs(
                db_scope="write",
                resources=ResourceDeclaration(db_scope="read", resources=[]),
            )
        )
