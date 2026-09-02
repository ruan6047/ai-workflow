"""釘住卡面規格節的 reader（`WF-REDESIGN-W3` 驗收 1，決議 §二 row 10 的取代者）。

## 這個模組要擋的四件事

1. **歷史回音被當成現行規格。** `## Log` 是 append-only；某次 amend 留下的哨兵字面
   會原樣躺在那裡。⛔ 不先切分 Log 就會讀到過去的版本。
2. **缺規格節變成擋人點。** 2026-09-02 實測全板 **217 張只有 1 張**有 `## 規格`
   標題（內容還是「規格不在卡面」）⇒ 缺區塊是**構造上合法**的狀態，
   `try_parse_block` 必須回 `None`、⛔ 不得讓那 216 張卡無法 `amend`／`handoff`。
3. **兩個版本號被互相代用。** 哨兵字面的 `v1` ＝**區塊格式**版本；區塊第一行的
   `spec_version` ＝**規格內容**版本。⛔ 不得由其中一個推導另一個。
4. **版本行被「推導」出來。** `planning.md:10` 逐字「每次改必 bump」——推導出來的
   版本⛔ 無法證明它被 bump 過，⇒ 第一行不是 `spec_version: <整數>` 就拒。

⛔ **本檔⛔ 不測 W1 的 v1 fenced JSON**——那是 `test_card_face.py` 的射程，且本卡對
它的「擴充」**＝零**（v1 頂層與三子物件皆 `additionalProperties: false`，加鍵實測
被拒 ⇒ 加鍵必然變成另立 v2，被卡面驗收 1 逐字「⛔ 不另立 schema」禁止）。
「讀取端雙路徑（舊卡切割 no-op）」的既有證據在
`test_card_face.py::test_legacy_card_without_a_block_falls_back_to_none`，
⛔ 不在此重打一份。
"""

from __future__ import annotations

import pytest

from wf_cli import card_spec as cs

_SPEC = cs.CardSpec(spec_version=4, text="## 一 · 目標\n\n把規格搬進卡面。")


def _body(*sections: str) -> str:
    return "\n\n".join(sections) + "\n\n## Log\n\n- 2026-09-01 open by PM。\n"


# ------------------------------------------------------------------ 往返

def test_round_trip_through_a_card_body():
    assert cs.parse_block(_body(cs.render_block(_SPEC))) == _SPEC


def test_render_puts_the_version_on_the_first_line_inside_the_sentinel():
    rendered = cs.render_block(_SPEC)
    inner = rendered.split(cs.BEGIN, 1)[1].split(cs.END, 1)[0].strip()
    assert inner.splitlines()[0] == "spec_version: 4"


def test_markdown_body_survives_verbatim():
    """規格內容是 markdown，⛔ 不做任何結構化——含 `##` 標題也不能被當成區段邊界。"""
    spec = cs.CardSpec(spec_version=9, text="### 子標題\n\n- 一\n- 二\n\n```json\n{}\n```")
    assert cs.parse_block(_body(cs.render_block(spec))).text == spec.text


# ------------------------------------------------------------ fail-open

def test_a_legacy_card_without_the_section_falls_back_to_none():
    """216/217 張今日就是這個形狀。⛔ 不得讓它們因缺區塊而無法 amend／handoff。"""
    body = _body("## 核心痛點\n\n- **痛點**：舊卡沒有規格節")
    assert cs.try_parse_block(body) is None
    with pytest.raises(cs.CardSpecError):
        cs.parse_block(body)


def test_the_section_heading_without_the_sentinel_is_still_a_failure():
    """⭐ 今日板上那唯一一張的形狀：有 `## 規格` 標題、內容是散文、⛔ 無哨兵。"""
    body = _body("## 規格\n\n規格不在卡面，見 docs/。")
    assert cs.try_parse_block(body) is None


# --------------------------------------------------------- Log 歷史回音

def test_a_sentinel_echo_inside_the_log_is_not_the_declaration():
    """`## Log` 是 append-only 留痕，裡面的哨兵字面是歷史回音、⛔ 不是宣告。"""
    body = (
        "## 核心痛點\n\n- **痛點**：舊卡\n\n## Log\n\n"
        f"- 2026-09-01 amend → 舊值 {cs.BEGIN} spec_version: 1 舊規格 {cs.END}\n"
    )
    assert cs.try_parse_block(body) is None


def test_the_current_block_wins_over_a_log_echo():
    """現行區塊在 Log 之前 ⇒ 讀得到，且讀到的是**現行**那一份、⛔ 不是回音。"""
    body = (
        cs.render_block(_SPEC)
        + "\n\n## Log\n\n"
        + f"- 2026-09-01 amend → 舊值 {cs.BEGIN} spec_version: 1 舊規格 {cs.END}\n"
    )
    parsed = cs.parse_block(body)
    assert parsed.spec_version == 4
    assert "舊規格" not in parsed.text


def test_two_section_headings_are_rejected_rather_than_taking_the_first():
    """⛔ 拒絕取第一個——形狀沿 `brief._brief_section`。"""
    body = _body(cs.render_block(_SPEC), cs.render_block(_SPEC))
    with pytest.raises(cs.CardSpecError) as exc:
        cs.parse_block(body)
    assert "無法判定哪一個是現行規格" in str(exc.value)


def test_a_second_sentinel_under_another_heading_is_also_rejected():
    """標題只有一個、哨兵有兩個 ⇒ 同樣⛔ 拒絕取第一個。

    ⭐ 這一格是「⛔ 不在下一個 `## ` 截斷」換來的**代價**：區段邊界由哨兵負責，
    於是後面別的 `## ` 區段裡的哨兵也落進射程。⇒ 明文拒收，⛔ 不靜默取第一個。
    """
    body = _body(cs.render_block(_SPEC) + "\n\n## 附錄\n" + cs.render_block(_SPEC).split("\n", 1)[1])
    with pytest.raises(cs.CardSpecError) as exc:
        cs.parse_block(body)
    assert "⛔ 拒絕取第一個" in str(exc.value)


# ------------------------------------------------------------ 版本行

@pytest.mark.parametrize(
    "first_line",
    [
        "spec_version: 四",
        "spec_version: 1.0",
        "spec_version: v4",
        "spec-version: 4",
        "版本: 4",
        "## 一 · 目標",
        "",
    ],
)
def test_a_malformed_version_line_is_rejected(first_line):
    """⛔ 不由內容推導版本——推導出來的版本⛔ 無法證明它被 bump 過。"""
    body = _body(f"{cs.SECTION_HEADING}\n{cs.BEGIN}\n{first_line}\n\n文字\n{cs.END}")
    with pytest.raises(cs.CardSpecError):
        cs.parse_block(body)


@pytest.mark.parametrize("version", [0, 1, 4, 42, 1000])
def test_any_decimal_integer_is_accepted(version):
    spec = cs.CardSpec(spec_version=version, text="x")
    assert cs.parse_block(_body(cs.render_block(spec))).spec_version == version


def test_an_empty_block_is_rejected():
    body = _body(f"{cs.SECTION_HEADING}\n{cs.BEGIN}\n{cs.END}")
    with pytest.raises(cs.CardSpecError):
        cs.parse_block(body)


# ---------------------------------------------------- 兩個版本號⛔ 不同

def test_the_sentinel_carries_the_format_version_not_the_content_version():
    """哨兵字面的 `v1` ＝**區塊格式**版本，⛔ 與 `spec_version` 無關。

    ⭐ 反證：`spec_version: 4` 的區塊仍住在 `card-spec:**v1**` 哨兵裡。若有人把
    兩者合併，這一條就會逼他先解釋合併後 `v1` 是什麼意思。
    """
    assert cs.BEGIN == "<!-- card-spec:v1:begin -->"
    assert cs.END == "<!-- card-spec:v1:end -->"
    assert cs.parse_block(_body(cs.render_block(_SPEC))).spec_version == 4
    assert "v1" in cs.render_block(_SPEC)


# ------------------------------------------------- 沿用既有切分，⛔ 不重打

def test_it_reuses_the_resources_log_splitter():
    """`F-執行-06` 逐字「驗證器要 import ⛔ 不重打」——本模組⛔ 不自寫 Log 切分。"""
    import inspect

    source = inspect.getsource(cs)
    assert "from .resources import ResourceDeclarationError, _split_at_log" in source
    # ⛔ 不得自己寫一份 Log 切分：那會是 `"## Log"` 這個**字串字面**出現在碼裡。
    # ⚠️ 只比字面 `## Log` 會誤中 docstring（本模組的說明大量提到它），⇒ 比帶引號的形式。
    assert '"## Log"' not in source and "'## Log'" not in source


def test_a_broken_log_heading_surfaces_as_a_card_spec_error():
    """切分失敗⛔ 不得靜默——`resources` 的紀律是「定位失效即拒」。"""
    body = "## 規格\n\n## Log\n\n- a\n\n## Log\n\n- b\n"
    with pytest.raises(cs.CardSpecError) as exc:
        cs.parse_block(body)
    assert "無法以 Log 標題切分" in str(exc.value)


# ------------------------------------------------------------ 零擋人點

def test_the_reader_never_raises_on_the_fail_open_path():
    """`try_parse_block` 對**任何**輸入都⛔ 不得丟例外——它是 0 擋人點的那一半。"""
    for body in ("", "沒有任何標題", "## Log\n- a\n## Log\n- b", "## 規格\n亂七八糟"):
        assert cs.try_parse_block(body) is None
