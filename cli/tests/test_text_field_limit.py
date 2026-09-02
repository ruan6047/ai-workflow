"""釘住 Project TEXT 欄的位元上限檢查（`WF-REDESIGN-W3` 驗收 7）。

本檔要擋的四件事：

1. **半寫入回來。** 卡面驗收 7 的痛點⛔ 不是「今天有多少張超標」（實測 217 張 **0 張**），
   而是**超標時的失敗模式**：寫入順序是「body 先、欄位後並讀回驗證」（`brief.py:19`
   逐字），所以在欄位那一步才發現超標＝body 已經寫出去了 ⇒ 兩居所不一致
   （`#217`、`#219` 各發生一次，兩次都靠人工補欄收尾）。
   ⇒ 拒收路徑上**世界狀態必須逐位元不變**。
2. **有人把它改成截斷。** `brief.py:19`／`:59` 逐字「TEXT 欄位為**恆等導出**（非摘要、
   **非截斷**）」是**規範句**（需求方 2026-09-02 裁定 B-1）。截斷 `簡介` 會讓該卡的
   `brief.drifted` **恆為 True**。
3. **檢查點被下移。** 只要它排到第一次遠端寫入之後，第 1 條就自動失效。
4. **訊息退化成沒有可跑補救。** 拒收訊息本身必須通過裁定 17 的三條機械必要條件——
   否則本卡在收 ≥37 則舊訊息的同時又新產一則。

⛔ 本檔⛔ 不測「1024 這個數字對不對」——那是 GitHub 伺服端行為，已於 2026-09-01 實測
（ASCII 1024 rc=0／1025 rc=1；中文 ×342＝1026B rc=1），⛔ 不在單元測試裡打遠端。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from wf_cli.project import (
    TEXT_FIELD_BYTE_LIMIT,
    oversized_text_fields,
    render_oversize_rejection,
)

# `F-執行-06` 逐字「驗證器要 import ⛔ 不重打」：閘門前零寫入的世界快照、CLI 入口、
# 目標參數、以及 `open` 的必填欄，全部沿用 `test_amend` 既有的那一份。
from .test_amend import (  # noqa: F401  (fake_runner／card 是 fixture，pytest 由模組層名字取用)
    BASE_TARGET,
    UNSEEDED_OPEN_EXTRAS,
    _world,
    card,
    fake_runner,
    run_cli,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "rejection_inventory", _REPO_ROOT / "scripts" / "rejection_inventory.py"
)
assert _spec is not None and _spec.loader is not None
ri = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("rejection_inventory", ri)
_spec.loader.exec_module(ri)


# ------------------------------------------------------------------ 純函式：邊界

@pytest.mark.parametrize(
    "value,expected_bytes,rejected",
    [
        ("a" * 1024, 1024, False),
        ("a" * 1025, 1025, True),
        # ⚠️ 中文一字 3 bytes：341 字＝**1023** bytes（⛔ 非卡面實測欄寫的「恰 1024B」，
        # 該處疑為筆誤；342 字＝1026B 與卡面相符，故 rc 邊界的結論不受影響）。
        ("中" * 341, 1023, False),
        ("中" * 342, 1026, True),
    ],
)
def test_the_boundary_is_utf8_bytes_not_characters(value, expected_bytes, rejected):
    assert len(value.encode("utf-8")) == expected_bytes
    found = oversized_text_fields({"簡介": value})
    assert bool(found) is rejected
    if rejected:
        assert found[0].actual_bytes == expected_bytes
        assert found[0].excess_bytes == expected_bytes - TEXT_FIELD_BYTE_LIMIT


def test_only_text_fields_are_measured():
    """`NUMBER`／`SINGLE_SELECT` 的值域另有閘門，⛔ 不在本檢查射程。"""
    long = "x" * 2000
    assert oversized_text_fields({"iteration": long}) == []
    assert oversized_text_fields({"交付狀態": long}) == []
    assert [f.name for f in oversized_text_fields({"簡介": long})] == ["簡介"]


def test_unregistered_field_names_are_measured_not_skipped():
    """⛔ 不靜默略過未登記的名字——那代表別處有缺陷，⛔ 不該由本檢查吸收掉。"""
    assert [f.name for f in oversized_text_fields({"沒登記的欄": "x" * 2000})] == ["沒登記的欄"]


def test_every_oversized_field_is_reported_not_just_the_first():
    found = oversized_text_fields(
        {"簡介": "a" * 1100, "資源宣告": "b" * 1200, "服務的原始目標": "c" * 10}
    )
    assert sorted(f.name for f in found) == ["簡介", "資源宣告"]


# ------------------------------------------------------------------ 訊息四要件

def _brief(total_bytes: int) -> str:
    """組一個**恰好 N bytes** 且過得了 `brief.validate_shape` 的簡介。

    ⚠️ 兩個標記是 canonical §6.3 的必含項（`brief.MARKER_WHEN`／`MARKER_NON_SCOPE`），
    且該檢查排在本卡的長度閘門**之前** ⇒ 不帶標記的字串量不到長度那一關。
    """
    head = "適用時機：測試。⛔ 非射程：無。"
    pad = total_bytes - len(head.encode("utf-8"))
    assert pad >= 0, f"{total_bytes} 太小，塞不下必含標記"
    return head + "a" * pad


def _message() -> str:
    found = oversized_text_fields({"簡介": "中" * 400})
    return render_oversize_rejection(
        "amend",
        found,
        "  ⇒ 縮短後重跑同一條 amend。權威值在 body：\n"
        "    gh issue view 221 --repo ruan6047/ai-workflow "
        "--json body --jq .body > /tmp/card-221-body.md",
    )


def test_the_message_names_the_field_the_actual_bytes_the_excess_and_the_target():
    text = _message()
    assert "簡介" in text
    assert "1200 bytes" in text                       # 實際
    assert f"超出 {1200 - TEXT_FIELD_BYTE_LIMIT} bytes" in text  # 超出多少
    assert f"縮短到 {TEXT_FIELD_BYTE_LIMIT} bytes" in text        # 縮到多少


def test_the_message_passes_the_three_mechanical_conditions():
    """裁定 17 三條**同時**成立。⛔ 那只是必要條件——「補救跑不跑得出」由 PM 判。"""
    mechanical = ri._evaluate(_message())
    assert mechanical.has_command is True
    assert mechanical.head_ok is True
    assert mechanical.no_placeholder is True
    assert mechanical.passes is True


def test_the_message_says_it_does_not_truncate():
    assert "不截斷" in _message()


# ------------------------------------------------------------------ 零遠端寫入

def _oversize_open_argv() -> list[str]:
    """`--from-issue` 指向**刻意不存在**的清單項（沿 `UNSEEDED_OPEN_EXTRAS` 的用法）。

    ⭐ 這就是失敗訊號：檢查點若被下移到第一次遠端呼叫之後，`issue view` 會在替身上
    炸成 `AssertionError`，⛔ 而不是安靜地照樣通過。
    """
    return [
        "open", *BASE_TARGET, "OVERSIZE-DEMO1",
        *UNSEEDED_OPEN_EXTRAS,
        "--feature", "示範", "--tier", "T2", "--db-scope", "none",
        "--core-pain", "痛點", "--service-goal", "目標",
        "--brief", _brief(1200),
        "--exec-capability", "主力型", "--exec-capability-reason", "理由甲",
        "--review-capability", "高階型", "--review-capability-reason", "理由乙",
    ]


def test_open_rejects_before_any_remote_call_at_all(fake_runner, capsys):
    before_world = _world(fake_runner)
    before_graphql = len(fake_runner.graphql_calls)

    assert run_cli(_oversize_open_argv()) == 2

    assert len(fake_runner.graphql_calls) == before_graphql, "超標拒收路徑⛔ 不得有任何遠端呼叫"
    assert _world(fake_runner) == before_world, "拒收必須零寫入"
    err = capsys.readouterr().err
    assert "[open] 拒絕（零遠端寫入）" in err
    assert "簡介" in err


def test_amend_rejects_before_its_first_remote_write(card, capsys):
    before_world = _world(card)

    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1",
         "--brief", _brief(1200), "--reason", "測試超標拒收"]
    )

    assert rc == 2
    assert _world(card) == before_world, "拒收必須零寫入——body 與欄位都不得動"
    err = capsys.readouterr().err
    assert "[amend] 拒絕（零遠國寫入）" not in err  # 錯字防呆
    assert "[amend] 拒絕（零遠端寫入）" in err


def test_amend_still_accepts_a_brief_at_exactly_the_limit(card):
    """邊界另一側的正控：**恰好** 1024 bytes 必須寫得進去，且**逐位元原樣**。

    ⛔ 這條同時是「⛔ 不截斷」的機械證明——若有人加了截斷，寫進去的值會變短。
    """
    value = _brief(TEXT_FIELD_BYTE_LIMIT)
    assert run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--brief", value, "--reason", "邊界正控"]
    ) == 0

    from wf_cli.project import find_item_by_card_id, list_items, resolve_project

    project = resolve_project(card, "acme", 1)
    item = find_item_by_card_id(list_items(card, project), "AMEND-DEMO1")
    assert item is not None
    assert item.text("簡介") == value
    assert len(item.text("簡介").encode("utf-8")) == TEXT_FIELD_BYTE_LIMIT


# ------------------------------------------------------------------ 負控

def test_negative_control_the_gate_actually_fires(fake_runner):
    """⛔ 不改語料改期望值：把同一條指令的簡介縮到上限內，必須**過**。

    若這條也回 2，上面那兩條的綠燈就是零資訊（閘門恆擋而非依長度擋）。
    """
    argv = _oversize_open_argv()
    argv[argv.index("--brief") + 1] = _brief(900)
    # 清單項仍是不存在的那一個 ⇒ 過了長度閘門之後必然在 `issue view` 出事，
    # ⇒ 只要**不是** rc=2 的長度拒收，就證明閘門是依長度動作的。
    with pytest.raises(AssertionError):
        run_cli(argv)
