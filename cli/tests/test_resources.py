from __future__ import annotations

import pytest

from wf_cli.resources import (
    declaration_heading,
    ResourceDeclaration,
    ResourceDeclarationError,
    find_conflicts,
    parse_block,
    render_block,
    try_parse_block,
)


def test_valid_declaration_round_trips_through_render_and_parse():
    decl = ResourceDeclaration(db_scope="write", resources=["file:a.py", "port:8080"])
    body = f"intro text\n\n{render_block(decl)}\n\nmore text"
    parsed = parse_block(body)
    assert parsed.db_scope == "write"
    assert parsed.resources == ["file:a.py", "port:8080"]


def test_invalid_db_scope_rejected():
    with pytest.raises(ResourceDeclarationError):
        ResourceDeclaration(db_scope="bogus", resources=[])


@pytest.mark.parametrize(
    "bad_resource",
    ["nofile.py", "port:notanumber", "db:dev:badkind", "container:", "random:thing"],
)
def test_invalid_resource_strings_rejected(bad_resource):
    with pytest.raises(ResourceDeclarationError):
        ResourceDeclaration(db_scope="none", resources=[bad_resource])


@pytest.mark.parametrize(
    "good_resource",
    ["file:cli/src/wf_cli/card.py", "port:8080", "container:api", "db:dev:schema", "db:dev:table:players"],
)
def test_valid_resource_prefixes_accepted(good_resource):
    decl = ResourceDeclaration(db_scope="write", resources=[good_resource])
    assert decl.resources == [good_resource]


def test_parse_block_missing_raises():
    with pytest.raises(ResourceDeclarationError):
        parse_block("no resource section here at all")


def test_parse_block_malformed_json_raises():
    body = "## 資源宣告\n<!-- resource-claims:begin -->\n```json\n{not valid json\n```\n<!-- resource-claims:end -->"
    with pytest.raises(ResourceDeclarationError):
        parse_block(body)


def test_try_parse_block_returns_none_instead_of_raising():
    assert try_parse_block("nothing here") is None
    decl = ResourceDeclaration(db_scope="none", resources=[])
    assert try_parse_block(render_block(decl)) is not None


# ---------------------------------------------------------------------------
# 兩層定位（WF-RESOURCE-BLOCK-ANCHOR1）
# ---------------------------------------------------------------------------
#
# 舊版以 `_BLOCK_RE.search(body)` 全文搜尋取第一個命中，任何寫在真區塊之前的同名
# 哨兵字面都會贏，且無錯誤訊息——結果直接餵給 find_conflicts 與 assign 的寫入集
# 閘門，是靜默 fail-open。以下每一條都釘住一種定位失效的裁定；「拒絕優先」是通則，
# 唯一例外是 `## Log` 區段內的歷史回音（它是 append-only 留痕，結構上就不是宣告，
# 故直接排除在定位範圍外，而不是讓整張卡讀不出宣告）。

REAL_DECL = ResourceDeclaration(db_scope="none", resources=["file:REAL.py"])

# 誘餌：完整、合法、但寫在別的章節裡的哨兵示範。
DECOY_BLOCK = (
    "<!-- resource-claims:begin -->\n"
    '```json\n{"db_scope": "write", "resources": ["file:DECOY.py"]}\n```\n'
    "<!-- resource-claims:end -->"
)

# amend 寫進 Log 的歷史回音：舊區段原文被 `" ".join(old_repr.split())` 壓成單行，
# 含標題字樣與整組哨兵（見 card.amend_resource_block）。
LOG_ECHO_LINE = (
    "- 2026-08-12T00:00:00+08:00 amend by wf-cli → 資源宣告：## 資源宣告 "
    "<!-- resource-claims:begin --> ```json "
    '{ "db_scope": "write", "resources": [ "file:OLD.py" ] } '
    "``` <!-- resource-claims:end -->"
)


def _card(*sections: str) -> str:
    return "- 需求：ruan6047　規劃：PM\n\n" + "\n\n".join(sections) + "\n"


def test_decoy_block_in_acceptance_section_does_not_hijack_parse():
    """PM 實測案例：把哨兵示範寫進驗收條件（誘餌在前），真區塊在其後。

    改動前 parse_block 回的是誘餌（db_scope=write／file:DECOY.py）且無任何錯誤；
    改動後必須回真宣告。這正是「卡片能寫下自己的格式規範」的那條線。
    """
    body = _card(
        "## 驗收條件",
        "- [ ] 資源宣告區塊的格式必須長這樣：",
        DECOY_BLOCK,
        render_block(REAL_DECL),
        "## Log",
        "- open。",
    )
    parsed = parse_block(body)
    assert parsed.resources == ["file:REAL.py"]
    assert parsed.db_scope == "none"


def test_log_echo_is_excluded_and_real_section_wins():
    """情境 1（歷史回音）：裁定＝排除 Log、取 Log 之前的真宣告，不拒絕。"""
    body = _card(render_block(REAL_DECL), "## Log", LOG_ECHO_LINE)
    parsed = parse_block(body)
    assert parsed.resources == ["file:REAL.py"]


def test_log_echo_alone_is_not_a_declaration():
    """情境 1 的另一半：只有 Log 回音、沒有真區段時必須拒絕，不得拿回音當宣告。"""
    body = _card("## 核心痛點", "- **痛點**：略", "## Log", LOG_ECHO_LINE)
    with pytest.raises(ResourceDeclarationError, match="歷史回音"):
        parse_block(body)


def test_missing_section_heading_rejects_even_with_sentinels_present():
    """情境 2（區段標題缺失）：裁定＝拒絕。哨兵在但標題不在，無從判定它是不是宣告。"""
    body = _card("## 驗收條件", "- [ ] 示範：", DECOY_BLOCK, "## Log", "- open。")
    with pytest.raises(ResourceDeclarationError, match="找不到獨立標題行"):
        parse_block(body)


def test_multiple_declaration_sections_reject_instead_of_taking_first():
    """情境 3（多個宣告區段）：裁定＝拒絕，不取第一個。"""
    body = _card(
        render_block(ResourceDeclaration(db_scope="write", resources=["file:A.py"])),
        render_block(ResourceDeclaration(db_scope="none", resources=["file:B.py"])),
        "## Log",
        "- open。",
    )
    with pytest.raises(ResourceDeclarationError, match="2 個"):
        parse_block(body)


def test_sentinel_outside_section_rejects():
    """情境 4（哨兵在區段外）：裁定＝拒絕，且錯誤訊息要點出哨兵在區段外。"""
    body = _card(
        "## 資源宣告",
        "（待補）",
        "## 驗收條件",
        DECOY_BLOCK,
        "## Log",
        "- open。",
    )
    with pytest.raises(ResourceDeclarationError, match="區段之外"):
        parse_block(body)


def test_duplicate_sentinels_inside_section_reject():
    """自我適用：有人在 `## 資源宣告` 區段**內部**多貼一組哨兵時，區段定位救不了，
    因為兩組都在管轄內。裁定＝拒絕（不取第一個），否則同一個劫持形態只是往內縮一層。
    """
    body = _card(
        "## 資源宣告",
        DECOY_BLOCK,
        "<!-- resource-claims:begin -->",
        '```json\n{"db_scope": "none", "resources": ["file:REAL.py"]}\n```',
        "<!-- resource-claims:end -->",
        "## Log",
        "- open。",
    )
    with pytest.raises(ResourceDeclarationError, match="必須各恰好 1 個"):
        parse_block(body)


def test_duplicate_log_headings_reject():
    """對齊 card.split_at_log：兩個 `## Log` 標題時無法安全切出定位範圍。"""
    body = _card(render_block(REAL_DECL), "## Log", "- a", "## Log", "- b")
    with pytest.raises(ResourceDeclarationError, match="2 個"):
        parse_block(body)


def test_literal_newline_corrupted_log_rejects():
    """對齊 card.split_at_log（ai-workflow#17 事故）：`## Log` 字樣在但不是獨立標題行，
    排版已壞，此時依標題切段可能把 Log 的回音當成現況——拒絕而不是猜。
    """
    body = _card(render_block(REAL_DECL)) + "\\n## Log\\n\\n" + LOG_ECHO_LINE
    with pytest.raises(ResourceDeclarationError, match="不是獨立標題行"):
        parse_block(body)


def test_try_parse_block_degrades_to_none_not_to_decoy():
    """報告型指令（doctor／snapshot）的降級方向：讀不出宣告是 None，不是誘餌的值。"""
    body = _card("## 驗收條件", DECOY_BLOCK, "## Log", "- open。")
    assert try_parse_block(body) is None


def test_find_conflicts_detects_shared_file_resource():
    mine = ResourceDeclaration(db_scope="write", resources=["file:shared.py"])
    other = ResourceDeclaration(db_scope="write", resources=["file:shared.py", "file:other.py"])
    assert find_conflicts(mine, "OTHER-CARD", other) == ["file:shared.py"]


def test_find_conflicts_no_overlap_is_empty():
    mine = ResourceDeclaration(db_scope="write", resources=["file:a.py"])
    other = ResourceDeclaration(db_scope="write", resources=["file:b.py"])
    assert find_conflicts(mine, "OTHER-CARD", other) == []


def test_find_conflicts_db_resource_shared_when_both_read_only():
    mine = ResourceDeclaration(db_scope="read", resources=["db:dev:table:players"])
    other = ResourceDeclaration(db_scope="read", resources=["db:dev:table:players"])
    assert find_conflicts(mine, "OTHER-CARD", other) == []


def test_find_conflicts_db_resource_still_conflicts_if_either_side_writes():
    mine = ResourceDeclaration(db_scope="write", resources=["db:dev:table:players"])
    other = ResourceDeclaration(db_scope="read", resources=["db:dev:table:players"])
    assert find_conflicts(mine, "OTHER-CARD", other) == ["db:dev:table:players"]


def test_find_conflicts_file_resource_always_conflicts_even_if_both_read_scope():
    # file/port/container 是獨佔宣告本身，不受 db_scope=read 影響。
    mine = ResourceDeclaration(db_scope="read", resources=["file:shared.py"])
    other = ResourceDeclaration(db_scope="read", resources=["file:shared.py"])
    assert find_conflicts(mine, "OTHER-CARD", other) == ["file:shared.py"]


def test_summary_lists_resources_or_notes_empty():
    empty = ResourceDeclaration(db_scope="none", resources=[])
    assert "無共享可寫資源" in empty.summary()
    non_empty = ResourceDeclaration(db_scope="write", resources=["file:a.py"])
    assert "file:a.py" in non_empty.summary()


# ---------------------------------------------------------------------------
# 標題後綴相容（WF-RESOURCE-HEADING-SUFFIX1）
#
# 2026-08-04 的 state-plane 遷移把補述寫進標題行，而本模組原以逐字相等定位
# ⇒ 那批卡的 amend --resources 可達 0/33（實測）。放寬為「相等或以 `## 資源宣告（` 起始」。
#
# ⚠️ 擋住 #43 劫持的**不是**兩層定位本身，是「恰好 1 次」那條不變量——放寬後
# 攻擊樣本反而讓命中數變 2 而被拒。下面兩支就是在守那條不變量。
# ---------------------------------------------------------------------------

SUFFIXED = "## 資源宣告（機器可讀；`null`／`[]` 代表未正式宣告，不代表無資源）"
_PAYLOAD = (
    "<!-- resource-claims:begin -->\n```json\n"
    '{"db_scope": "none", "resources": ["file:a.py"]}\n'
    "```\n<!-- resource-claims:end -->\n"
)


def _body(*sections: str) -> str:
    return "- 需求：x　規劃：y\n\n" + "\n".join(sections) + "\n\n## Log\n\n- x\n"


def test_suffixed_heading_locates_the_section():
    decl = parse_block(_body(SUFFIXED + "\n" + _PAYLOAD))
    assert decl.resources == ["file:a.py"]


def test_declaration_heading_returns_the_suffix_verbatim():
    body = _body(SUFFIXED + "\n" + _PAYLOAD)
    assert declaration_heading(body) == SUFFIXED


def test_declaration_heading_returns_the_short_form_when_that_is_what_is_there():
    body = _body("## 資源宣告\n" + _PAYLOAD)
    assert declaration_heading(body) == "## 資源宣告"


def test_suffixed_decoy_before_the_real_section_still_rejects():
    # 真區段**前**插一個帶後綴的假區段 → 命中 2 次 → 「恰好 1 次」不變量擋下。
    #
    # ⚠️ 假區段的 payload 必須是**合法宣告**（原本寫 `HIJACK`，⛔ 那是零資訊）：
    # 內容非法的話，關掉「恰好 1 次」之後解析仍會在哨兵／JSON 層失敗，
    # ⇒ 測試照樣綠、但通過的理由不是本測試宣稱的那一個。變異檢驗當場抓到。
    # 合法 payload 讓「拒收」的唯一可能理由就是命中數。
    hijacked = _PAYLOAD.replace("file:a.py", "file:HIJACKED.py")
    body = _body(SUFFIXED + "\n" + hijacked, "## 資源宣告\n" + _PAYLOAD)
    with pytest.raises(ResourceDeclarationError):
        parse_block(body)


def test_both_heading_forms_present_rejects_instead_of_taking_one():
    # 兩種標題並存（實測母體有 6 張）→ 放寬後命中 2 次 → 仍拒收，⛔ 不靜默取其一。
    body = _body("## 資源宣告\n" + _PAYLOAD, SUFFIXED + "\n" + _PAYLOAD)
    with pytest.raises(ResourceDeclarationError):
        parse_block(body)
