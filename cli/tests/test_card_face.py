"""卡面表單（`WF-REDESIGN-W1` 驗收 3）的 schema、哨兵與升版規則。

卡面逐字要求「writer／reader tests 對**同一** validator 跑正負 fixture」⇒ 本檔每一條
正例／反例都打 ``card_face.validate``（reader 側）與 ``card_face.render_block``
（writer 側，它自己就先跑 validate）**兩邊**，⛔ 不各驗一半。
"""

from __future__ import annotations

import json

import pytest
from wf_cli import card_face as cf
from wf_cli.resources import ResourceDeclaration, render_block as render_resource_block

VALID = {
    "schema_version": "1",
    "stage_plan": [
        {"stage": "需求", "goal": "把清單項變成一張可派工的卡"},
        {"stage": "執行", "goal": "實作與自測"},
    ],
    "tier_basis": {
        "sensitive_surfaces": "wfcli 狀態面寫入通道",
        "recoverability": "git revert",
        "blast_radius": "單一 repo",
    },
    "list_convergence": [
        {"issue_url": "https://github.com/ruan6047/ai-workflow/issues/177", "claim": "covers"}
    ],
}


def _with(**overrides) -> dict:
    return {**json.loads(json.dumps(VALID)), **overrides}


def _both_sides_accept(data: dict) -> None:
    """正例必須同時過 reader（validate）與 writer（render_block）。"""
    cf.validate(data)
    cf.render_block(data)


def _both_sides_reject(data: dict, *, exc=cf.CardFaceError) -> str:
    """反例必須被**同一個** validator 擋下，writer 側同樣擋。回傳訊息供斷言。"""
    with pytest.raises(exc) as reader:
        cf.validate(data)
    with pytest.raises(exc):
        cf.render_block(data)
    return str(reader.value)


# ==========================================================================
# 哨兵字面：卡面逐字釘死，⛔ 不得漂
# ==========================================================================


def test_sentinel_literals_are_verbatim_and_distinct_from_resource_claims():
    """哨兵字面是**規格**，⛔ 不是實作細節。

    卡 `#217` body 的「AC3 規格全文」段逐字寫著這兩串。⛔ 與 resource-claims 不同名
    是同一段逐字要求的一部分——兩個 fenced JSON 區塊在同一張卡面上共存是常態，同名
    就會互搶。
    """
    assert cf.BEGIN == "<!-- card-face-form:v1:begin -->"
    assert cf.END == "<!-- card-face-form:v1:end -->"
    from wf_cli.resources import CLAIMS_BEGIN_MARKER, CLAIMS_END_MARKER

    assert cf.BEGIN != CLAIMS_BEGIN_MARKER and cf.END != CLAIMS_END_MARKER


def test_schema_text_is_the_single_source_and_parses_as_draft_2020_12():
    """schema 全文只此一份，且 ``$schema`` 逐字指向 draft 2020-12。"""
    assert cf.SCHEMA is json.loads(cf.SCHEMA_TEXT) or cf.SCHEMA == json.loads(cf.SCHEMA_TEXT)
    assert cf.SCHEMA["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert set(cf.SCHEMA["required"]) == {
        "schema_version", "stage_plan", "tier_basis", "list_convergence"
    }


def test_the_walker_refuses_a_schema_keyword_it_cannot_execute():
    """⭐ 承重檢查：schema 長出走訪器不懂的關鍵字 ⇒ **模組載入期**就炸。

    ⛔ 沒有這條，加一個 ``oneOf`` 會變成一條**靜默失效**的約束——schema 上寫著、
    validate() 從不執行它。
    """
    with pytest.raises(cf.CardFaceError) as exc:
        cf._assert_schema_is_understood({"type": "object", "oneOf": [{"type": "string"}]})
    assert "oneOf" in str(exc.value)
    # 型別值域同樣是封閉的：宣告一個走訪器不認得的 type 也要炸。
    with pytest.raises(cf.CardFaceError):
        cf._assert_schema_is_understood({"type": "integer"})


# ==========================================================================
# schema 正負 fixture
# ==========================================================================


def test_valid_form_is_accepted_by_writer_and_reader():
    _both_sides_accept(VALID)


def test_empty_list_convergence_is_allowed():
    """卡面逐字：``list_convergence`` **允許空陣列**（⛔ 不是必填 ≥1）。"""
    _both_sides_accept(_with(list_convergence=[]))


@pytest.mark.parametrize(
    ("data", "case"),
    [
        ({k: v for k, v in VALID.items() if k != "tier_basis"}, "缺 tier_basis"),
        (_with(stage_plan=[]), "stage_plan 空陣列違反 minItems:1"),
        (_with(stage_plan=[{"stage": "上線", "goal": "x"}]), "stage 不在封閉列舉內"),
        (_with(stage_plan=[{"stage": "需求", "goal": ""}]), "goal 違反 minLength:1"),
        (_with(stage_plan=[{"stage": "需求", "goal": "x", "who": "PM"}]), "多餘鍵"),
        (_with(tier_basis={"sensitive_surfaces": "a", "recoverability": "b"}), "三子問缺一"),
        (_with(tier_basis={"sensitive_surfaces": "", "recoverability": "b", "blast_radius": "c"}),
         "三子問之一為空字串"),
        (_with(list_convergence=[{"issue_url": "https://github.com/a/b/issues/1", "claim": "x"}]),
         "claim 不在封閉列舉內"),
        (_with(extra="x"), "頂層多餘鍵（additionalProperties: false）"),
    ],
)
def test_schema_negatives_are_rejected_by_the_same_validator(data, case):
    _both_sides_reject(data)


# ==========================================================================
# schema 外的附加拒收規則（卡面逐字列的兩條）
# ==========================================================================


def test_duplicate_stage_is_rejected():
    msg = _both_sides_reject(
        _with(stage_plan=[{"stage": "需求", "goal": "甲"}, {"stage": "需求", "goal": "乙"}])
    )
    assert "重複的 stage" in msg


def test_duplicate_issue_url_is_rejected():
    url = "https://github.com/ruan6047/ai-workflow/issues/177"
    msg = _both_sides_reject(
        _with(list_convergence=[{"issue_url": url, "claim": "covers"},
                                {"issue_url": url, "claim": "related"}])
    )
    assert "重複的 issue_url" in msg


# ==========================================================================
# issue_url 正規形：四類拒收 fixture ＋ 正例（卡面逐字）
# ==========================================================================

_GOOD_URL = "https://github.com/acme/wf/issues/12"
_BAD_URLS = {
    "repo 首頁": "https://github.com/acme/wf",
    "issues 列表頁": "https://github.com/acme/wf/issues",
    "pull request URL": "https://github.com/acme/wf/pull/12",
    "issue 編號為 0": "https://github.com/acme/wf/issues/0",
    "issue 編號為負": "https://github.com/acme/wf/issues/-1",
    # 「正規形唯一」的三個變體（卡面逐字：⛔ 不允許 trailing slash／query／fragment）
    "結尾斜線": "https://github.com/acme/wf/issues/12/",
    "query": "https://github.com/acme/wf/issues/12?utm=1",
    "fragment": "https://github.com/acme/wf/issues/12#issuecomment-1",
    # ⚠️ ECMA-262 的 `$` 只匹配真結尾，Python 的 `$` 也匹配結尾換行之前。
    # 這一格釘住 `_ecma_regex` 的存在理由——它若被改回 `re.compile`，這條轉紅。
    "結尾換行": "https://github.com/acme/wf/issues/12\n",
}


def test_issue_url_positive_fixture():
    cf.validate_issue_url(_GOOD_URL)
    _both_sides_accept(_with(list_convergence=[{"issue_url": _GOOD_URL, "claim": "related"}]))


@pytest.mark.parametrize(("case", "url"), sorted(_BAD_URLS.items()))
def test_issue_url_negative_fixtures(case, url):
    with pytest.raises(cf.CardFaceError):
        cf.validate_issue_url(url)
    _both_sides_reject(_with(list_convergence=[{"issue_url": url, "claim": "covers"}]))


def test_from_issue_and_list_convergence_share_one_normal_form():
    """⛔ 兩處不得各寫一份正規形——``ISSUE_URL_PATTERN`` 就是 schema 裡那個字面。"""
    assert cf.ISSUE_URL_PATTERN == (
        cf.SCHEMA["properties"]["list_convergence"]["items"]["properties"]["issue_url"]["pattern"]
    )


# ==========================================================================
# 區塊定位：round-trip／legacy fallback／同類兩區塊／malformed／共存
# ==========================================================================


def _body(*blocks: str) -> str:
    return "\n\n".join(blocks) + "\n\n## Log\n\n- 2026-09-01 open by PM。\n"


def test_round_trip_through_a_card_body():
    body = _body(cf.render_block(VALID))
    assert cf.parse_block(body) == VALID


def test_legacy_card_without_a_block_falls_back_to_none():
    """本欄位上線前開的卡沒有這個區塊 ⇒ ``try_parse_block`` 回 ``None``、⛔ 不阻擋動詞。"""
    body = _body("## 核心痛點\n\n- **痛點**：舊卡沒有卡面表單")
    assert cf.try_parse_block(body) is None
    with pytest.raises(cf.CardFaceError):
        cf.parse_block(body)


def test_two_blocks_of_the_same_kind_are_rejected():
    body = _body(cf.render_block(VALID), cf.render_block(_with(list_convergence=[])))
    with pytest.raises(cf.CardFaceError) as exc:
        cf.parse_block(body)
    assert "必須各恰好 1 個" in str(exc.value)


def test_a_sentinel_echo_inside_the_log_is_not_the_declaration():
    """``## Log`` 是 append-only 留痕，裡面的哨兵字面是歷史回音、⛔ 不是宣告。"""
    body = (
        "## 核心痛點\n\n- **痛點**：舊卡\n\n## Log\n\n"
        f"- 2026-09-01 amend → 舊值 {cf.BEGIN} …… {cf.END}\n"
    )
    assert cf.try_parse_block(body) is None


def test_malformed_json_inside_the_sentinels_is_rejected():
    body = _body(f"## 卡面表單\n{cf.BEGIN}\n```json\n{{not json}}\n```\n{cf.END}")
    with pytest.raises(cf.CardFaceError) as exc:
        cf.parse_block(body)
    assert "JSON 解析失敗" in str(exc.value)


def test_a_non_fenced_payload_is_rejected():
    """⛔ 不以「找到一個 JSON fence」定位，也⛔ 不接受沒有 fence 的 payload。"""
    body = _body(f"## 卡面表單\n{cf.BEGIN}\n{json.dumps(VALID)}\n{cf.END}")
    with pytest.raises(cf.CardFaceError) as exc:
        cf.parse_block(body)
    assert "fenced" in str(exc.value)


def test_coexists_with_the_resource_claims_block():
    """兩個 fenced JSON 區塊同卡共存，各自讀回各自的東西、⛔ 不互搶。"""
    decl = ResourceDeclaration(db_scope="none", resources=["file:cli/src/wf_cli/card_face.py"])
    body = _body(render_resource_block(decl), cf.render_block(VALID))
    from wf_cli.resources import parse_block as parse_resources

    assert cf.parse_block(body) == VALID
    assert parse_resources(body) == decl


# ==========================================================================
# 升版：v1 reader 對未知版本 fail-closed
# ==========================================================================


def test_unknown_schema_version_is_fail_closed_and_points_at_migration():
    msg = _both_sides_reject(_with(schema_version="2"), exc=cf.CardFaceVersionError)
    assert "migration" in msg
    assert cf.SCHEMA_VERSION in msg


def test_unknown_version_inside_a_body_is_refused_not_silently_ignored():
    """⛔ ``try_parse_block`` 對未知版本回 ``None`` 是**已知且刻意**的界線。

    ⚠️ 兩者不同：``parse_block`` 拋 :class:`CardFaceVersionError`（寫入端走這條，
    ⇒ 拒收）；``try_parse_block`` 是給「缺區塊不阻擋動詞」的 fail-open 路徑用的，
    它把「沒有」與「壞掉」都收成 ``None``。⛔ 不得拿 ``try_parse_block`` 當寫入端判準。
    """
    body = _body(
        f"## 卡面表單\n{cf.BEGIN}\n```json\n{json.dumps(_with(schema_version='2'))}\n```\n{cf.END}"
    )
    with pytest.raises(cf.CardFaceVersionError):
        cf.parse_block(body)
    assert cf.try_parse_block(body) is None


def test_version_error_is_a_card_face_error_subclass():
    """呼叫端只 ``except CardFaceError`` 也接得住升版拒收，⛔ 不會漏成 traceback。"""
    assert issubclass(cf.CardFaceVersionError, cf.CardFaceError)
