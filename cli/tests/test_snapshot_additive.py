"""釘住 snapshot 的 additive 補欄（`WF-REDESIGN-W3` 驗收 5）。

## 這一條的全部風險在「additive」這三個字

補欄本身很簡單；會出事的是**順手改了既有的東西**。三個既有 root 鍵各有其消費者：

- `generated_at` —— canonical 有三處拿它當基準（〈狀態〉「年齡以該快照的
  generated_at 為基準」、〈終態卡的封存〉、〈為什麼不下放〉），而 `AI_WORKFLOW.md`
  **⛔ 不在本卡 write-set** ⇒ 改名就是製造一個本卡修不了的漂移。
- `schema`／`cards` —— `test_commands_mocked.py` 有斷言。

⇒ 本檔第一組測試就是「既有鍵一字不動」。

## ⛔ 一個⛔ 不得由本卡綠燈推出的東西

`inv-v1` artifact 的 producer 是 **W1 前置**的一次性唯讀查詢
（`archive/wave-specs/w1.md`），時序上早於本卡。本卡做的是把它的**形狀產品化**進
snapshot ⇒ **⛔ 不得稱本卡的後置產物為 W1 Gate 的來源**。卡面逐字寫了這一句，
本檔最後一組測試釘住那個登記還在。
"""

from __future__ import annotations

import json

import pytest

from wf_cli import card_spec as cs
from wf_cli import snapshot as sn
from wf_cli.project import ItemSnapshot

_SPEC = cs.CardSpec(spec_version=4, text="## 一 · 目標\n\n把規格搬進卡面。")


def _item(card_id: str, *, body: str = "", **fields) -> ItemSnapshot:
    base = {"卡ID": card_id}
    base.update(fields)
    return ItemSnapshot(
        item_id=f"PVTI_{card_id}",
        content_type="Issue",
        title=card_id,
        body=body or "## Log\n\n- 2026-09-01 open by PM。\n",
        issue_number=1,
        issue_url=f"https://github.com/ruan6047/ai-workflow/issues/1",
        fields=base,
    )


def _payload(items, project_id="PVT_x"):
    return json.loads(sn.render_json(sn.build_rows(items), "2026-09-02T00:00:00+08:00", project_id))


# ------------------------------------------------- (1) 既有鍵一字不動

def test_the_three_existing_root_keys_are_untouched():
    payload = _payload([_item("A1")])
    assert payload["generated_at"] == "2026-09-02T00:00:00+08:00"
    assert payload["schema"] == "wf-cli/state-snapshot/v1"
    assert isinstance(payload["cards"], list)


def test_query_version_is_carried_by_schema_and_is_not_a_separate_key():
    """規格逐字「`query_version` **以既有 `schema` 承載**」⇒ ⛔ 不另立鍵。"""
    payload = _payload([_item("A1")])
    assert "query_version" not in payload
    assert payload["schema"].startswith("wf-cli/state-snapshot/")


def test_the_row_ordering_is_still_by_card_id():
    """⚠️ `inv-v1` 依 `item_id` 排，本模組仍依 `card_id` 排——**⛔ 未改**。

    改排序會動到 `SNAPSHOT.md` 的每一行，而卡面只要求**補欄**。
    """
    payload = _payload([_item("C1"), _item("A1"), _item("B1")])
    assert [c["card_id"] for c in payload["cards"]] == ["A1", "B1", "C1"]


# ------------------------------------------- (2) inv-v1 的三欄全部涵蓋

def test_the_snapshot_now_covers_every_inv_v1_row_field():
    """`inv-v1` 的 row 三欄：`item_id`／`content_type`／`card_id`。

    ⭐ 補 `item_id` 之前只有後兩欄（交集 2/3）；補完為 3/3。
    """
    card = _payload([_item("A1")])["cards"][0]
    for field in ("item_id", "content_type", "card_id"):
        assert field in card, f"缺 {field}"
    assert card["item_id"] == "PVTI_A1"


def test_project_id_is_on_the_root():
    assert _payload([_item("A1")], project_id="PVT_kwDO")["project_id"] == "PVT_kwDO"


def test_render_json_makes_no_remote_call_so_project_id_defaults_to_none():
    """`render_json` 是**純渲染**——project id 只有呼叫端拿得到，⛔ 不在此處自己查。"""
    payload = json.loads(sn.render_json(sn.build_rows([_item("A1")])))
    assert payload["project_id"] is None


# ------------------------------------------------------ (3) 三欄來源

def test_phase_comes_from_the_project_field():
    card = _payload([_item("A1", **{"階段": "執行"})])["cards"][0]
    assert card["phase"] == "執行"


def test_phase_is_not_the_delivery_status():
    """⚠️ 階段與交付狀態是**兩軸**（canonical §0.1）。同時給不同值，兩欄各自回各自的。"""
    card = _payload([_item("A1", **{"階段": "執行", "交付狀態": "🔨執行中"})])["cards"][0]
    assert card["phase"] == "執行"
    assert card["delivery_status"] == "🔨執行中"


def test_brief_comes_from_the_project_field_not_from_the_body():
    """⛔ 不在此重跑 body 解析。

    ⭐ 兩居所不一致時該由 `doctor` **報漂移**，⛔ 不由 snapshot 自己選一邊而把
    漂移抹平——本測試刻意讓兩居所不同，斷言 snapshot 取的是**欄位**那一份。
    """
    body = "## 簡介\n<!-- card-brief:begin -->\nbody 側的值\n<!-- card-brief:end -->\n\n## Log\n\n- x\n"
    card = _payload([_item("A1", body=body, **{"簡介": "欄位側的值"})])["cards"][0]
    assert card["brief"] == "欄位側的值"


def test_the_spec_section_comes_from_the_card_spec_sentinel():
    body = cs.render_block(_SPEC) + "\n\n## Log\n\n- 2026-09-01 open by PM。\n"
    card = _payload([_item("A1", body=body)])["cards"][0]
    assert card["spec_version"] == 4
    assert card["spec_text"] == _SPEC.text


def test_a_card_without_a_spec_section_gets_nulls_not_an_error():
    """216/217 張今日就是這個形狀 ⇒ 缺區塊**⛔ 不是異常**。"""
    card = _payload([_item("A1")])["cards"][0]
    assert card["spec_version"] is None
    assert card["spec_text"] is None


def test_all_three_new_columns_are_present_together():
    """卡面逐字「snapshot 補欄（階段／簡介／規格節）」⇒ **三欄齊全**，⛔ 不是兩欄。"""
    body = cs.render_block(_SPEC) + "\n\n## Log\n\n- x\n"
    card = _payload([_item("A1", body=body, **{"階段": "執行", "簡介": "b"})])["cards"][0]
    assert (card["phase"], card["brief"], card["spec_version"]) == ("執行", "b", 4)


# --------------------------------------------------- (4) 人類可讀那一面

def test_the_ledger_gains_the_phase_column():
    assert "階段" in sn.LEDGER_COLUMNS
    md = sn.render_markdown(sn.build_rows([_item("A1", **{"階段": "執行"})]))
    assert "| 階段 |" in md
    assert "| 執行 |" in md


@pytest.mark.parametrize("column", ["簡介", "規格節", "spec_version"])
def test_the_ledger_deliberately_omits_the_long_form_columns(column):
    """⚠️ **本卡的裁斷**：卡面⛔ 未指明兩種輸出各補哪些欄。

    簡介與規格節都是長文，塞進表格會讓整份 `SNAPSHOT.md` 不可讀 ⇒ 只進 JSON。
    """
    assert column not in sn.LEDGER_COLUMNS


def test_the_ledger_row_width_matches_the_header():
    """加欄最容易出的錯：表頭加了、資料列沒加（或反過來）。"""
    md = sn.render_markdown(sn.build_rows([_item("A1", **{"階段": "執行"})]))
    lines = [line for line in md.splitlines() if line.startswith("| ")]
    widths = {line.count("|") for line in lines}
    assert len(widths) == 1, f"表頭與資料列欄數不一致：{widths}"


# ------------------------------------------------------- (5) 登記還在

def test_the_w1_gate_prohibition_is_still_recorded():
    """⛔ 不得稱本卡後置產物為 W1 Gate 的來源——producer 在 W1 **前置**。

    ⛔ 這⛔ 不是文件測試：那句話是卡面逐字要求的登記，刪掉它就等於刪掉一個
    「未來的人可能會拿本卡的 snapshot 去當 W1 退場證據」的防呆。
    """
    source = sn.__doc__ or ""
    assert "⛔ **不得稱本卡的後置產物為 W1 Gate 的來源**" in source
    assert "W1 前置" in source
