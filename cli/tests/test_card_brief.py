"""卡片簡介（canonical §6.3）與階段軸（§0.1）的寫入端測試。

⚠️ **變異檢驗紀律**：本檔的每一組斷言都要能回答「什麼結果會讓它不成立」。
只驗「正常輸入會過」是零資訊——本 repo 已為此付過代價（`DEV-PROSE-MUTATION-CLAIM-AUDIT1`
逐字：121 個「改了就會轉紅」的散文宣稱沒人驗過，抽驗到的三個全假）。故每個守衛都同時
驗**會過的輸入**與**會被拒的輸入**。
"""

from __future__ import annotations

import pytest

from wf_cli import brief
from wf_cli.card import Card, amend_brief, render_issue_body
from wf_cli.commands.handoff_cmd import STAGE_PHASE, STAGE_STATUS
from wf_cli.doctor import audit_brief_drift, find_brief_drift
from wf_cli.project import CARD_FIELD_MAP, FIELD_SPECS
from wf_cli.resources import ResourceDeclaration

GOOD = "做什麼：建簡介寫入通道。適用時機：要判斷一張卡跟手上的問題相不相關時。⛔ 非射程：既有卡回填。"


def _card(**over) -> Card:
    kw = dict(
        card_id="TEST1",
        feature="f",
        tier="T2",
        db_scope="none",
        core_pain="p",
        service_goal="g",
        resources=ResourceDeclaration(db_scope="none"),
        executor_capability="主力型",
        executor_capability_reason="r",
        reviewer_capability="主力型",
        reviewer_capability_reason="r",
    )
    kw.update(over)
    return Card(**kw)


# ---------------------------------------------------------------- 形狀要求


def test_brief_accepts_a_well_formed_value() -> None:
    assert brief.Brief(text=GOOD).text == GOOD


@pytest.mark.parametrize(
    "bad, missing",
    [
        ("做什麼：X。⛔ 非射程：Z。", brief.MARKER_WHEN),
        ("做什麼：X。適用時機：Y。", brief.MARKER_NON_SCOPE),
        ("只有做什麼。", brief.MARKER_WHEN),
        ("   ", None),
    ],
)
def test_brief_rejects_missing_markers(bad: str, missing: str | None) -> None:
    """⛔ 缺任一標記即拒。這一組是本檔的**負控**：拿掉 validate_shape 就會全綠。"""
    with pytest.raises(brief.BriefError) as exc:
        brief.Brief(text=bad)
    if missing:
        assert missing in str(exc.value)


def test_brief_does_not_check_length() -> None:
    """⛔ 不驗字數（canonical §6.3 逐字）。極短與極長只要帶兩個標記都必須通過。

    ⚠️ 這個測試的用途是**釘住「不做什麼」**：若日後有人加回字數下限／上限，
    它會轉紅。canonical 撤回長度數值的理由是母體未經品質檢查。
    """
    tiny = f"X。{brief.MARKER_WHEN}Y。{brief.MARKER_NON_SCOPE}Z。"
    huge = tiny + "補充。" * 500
    for text in (tiny, huge):
        brief.Brief(text=text)


# ---------------------------------------------------------------- 哨兵往返


def test_render_and_parse_round_trip() -> None:
    body = f"x\n\n{brief.render_block(brief.Brief(text=GOOD))}\n\n## Log\n\n- y\n"
    assert brief.parse_block(body).text == GOOD


def test_parse_ignores_a_historical_echo_inside_log() -> None:
    """⛔ ``## Log`` 之後的哨兵是 append-only 的歷史回音，不是現行簡介。

    ⚠️ 這正是 ``resources`` 模組要消滅的失敗形態，本模組沿用其紀律。
    """
    body = (
        "x\n\n## 核心痛點\n\n- p\n\n## Log\n\n"
        f"- 舊留痕：{brief.render_block(brief.Brief(text=GOOD))}\n"
    )
    assert brief.try_parse_block(body) is None


def test_parse_refuses_when_two_brief_headings_exist() -> None:
    """兩個 ``## 簡介`` 標題時拒絕取第一個——⛔ 無聲取第一個是本 repo 的既有根因族。"""
    block = brief.render_block(brief.Brief(text=GOOD))
    body = f"{block}\n\n{block}\n\n## Log\n\n- y\n"
    with pytest.raises(brief.BriefError):
        brief.parse_block(body)


def test_reuse_probe_is_not_vacuous() -> None:
    """⭐ 釘住「本模組沿用 resources 的切分函式」這件事本身。

    ``_reuse_probe`` 在 import 時跑一次；這裡以注入的壞函式再跑一次，證明它**會判**。
    ⛔ 只驗「正常時不炸」是零資訊——那個結果在探針被整支刪掉時也成立。
    """
    from wf_cli import resources

    brief._reuse_probe(resources._split_at_log)  # 正常路徑：不拋

    with pytest.raises(brief.BriefError) as exc:
        brief._reuse_probe(lambda _body: ("WRONG", "WRONG"))
    assert "拒絕退回自寫 markdown 解析" in str(exc.value)


# ---------------------------------------------------------------- fail-open


def test_existing_cards_without_a_brief_are_not_broken() -> None:
    """⚠️ 既有卡沒有簡介。⛔ 不得因缺欄位而讓 body 渲染或解析失敗。"""
    body = render_issue_body(_card())
    assert brief.SECTION_HEADING not in body
    assert brief.try_parse_block(body) is None


def test_amend_inserts_a_brief_section_into_an_existing_card() -> None:
    """188 張既有卡的補寫通道：找不到區段時**插入**，⛔ 不是報錯。"""
    body = render_issue_body(_card())
    new_body, old = amend_brief(body, GOOD)
    assert old is None
    assert brief.parse_block(new_body).text == GOOD
    assert new_body.count(brief.SECTION_HEADING) == 1


def test_amend_updates_an_existing_brief_and_returns_the_old_value() -> None:
    body = render_issue_body(_card(brief=GOOD))
    second = f"做什麼：改過。{brief.MARKER_WHEN}新。{brief.MARKER_NON_SCOPE}新。"
    new_body, old = amend_brief(body, second)
    assert old == GOOD
    assert brief.parse_block(new_body).text == second
    assert new_body.count(brief.SECTION_HEADING) == 1


def test_amend_rejects_a_malformed_brief_before_touching_the_body() -> None:
    body = render_issue_body(_card())
    with pytest.raises(brief.BriefError):
        amend_brief(body, "沒有標記")


# ---------------------------------------------------------------- 雙居所


def test_project_has_both_new_fields() -> None:
    assert FIELD_SPECS["簡介"] == ("TEXT", None)
    assert FIELD_SPECS["階段"][0] == "SINGLE_SELECT"
    assert CARD_FIELD_MAP["brief"] == "簡介"


def test_drift_detection_covers_every_combination() -> None:
    """四種組合逐一驗。⚠️ 只驗「一致回 None」是零資訊——三種漂移也要各驗一次。"""
    body = render_issue_body(_card(brief=GOOD))
    empty = render_issue_body(_card())
    assert find_brief_drift("C", body, GOOD) is None  # 一致
    assert find_brief_drift("C", empty, None) is None  # 兩居所皆空＝既有卡的預期狀態
    assert find_brief_drift("C", body, None) is not None  # 欄位過期
    assert find_brief_drift("C", body, "別的值") is not None  # 值不同
    assert find_brief_drift("C", empty, GOOD) is not None  # 欄位有值但 body 無


def test_audit_reports_not_scanned_instead_of_lying_clean() -> None:
    """⛔ 沒拿到卡面時回 ``not_scanned``，不謊報乾淨。"""
    assert audit_brief_drift(None).status == "not_scanned"
    assert audit_brief_drift({}).status == "not_scanned"
    report = audit_brief_drift({"C": render_issue_body(_card(brief=GOOD))}, {"C": GOOD})
    assert report.status == "scanned" and not report.findings


# ---------------------------------------------------------------- 階段軸


def test_backlog_is_deliberately_absent_from_the_phase_map() -> None:
    """⭐ ``backlog`` 改的是狀態不是階段（canonical §0.1）。

    依據有三：§0.1 的範例逐字示範同階段換狀態；Backlog 不在 7 階段裡而「待辦」在
    8 個通用狀態裡；碼內 ``BACKLOG_REQUIRED_PRIOR_STATUS`` 強制 T2 以上進 Backlog
    前必為 ``🧭規劃中`` ⇒ 階段本來就是規劃。⛔ 把它加進 ``STAGE_PHASE`` 會讓
    ``BACKLOG_GATE_EXEMPT_TIERS`` 的 T0／T1 被寫錯階段。
    """
    assert "backlog" in STAGE_STATUS
    assert "backlog" not in STAGE_PHASE


def test_phase_map_covers_six_of_canonical_seven_stages() -> None:
    """⚠️ 只覆蓋 6 個——``維護`` 缺席且是**已知且已記錄**的缺口，不是漏寫。

    維護專屬狀態「運行中」「失效」不在現行交付狀態選項裡，新增屬語彙變更
    ⇒ 須待子卡 S2（cpbl 相容層）落地。本測試釘住這個事實：若日後有人補上
    ``maintenance`` 卻沒同步加狀態值，它會轉紅。
    """
    canonical_seven = {"需求", "研究", "規劃", "執行", "審核", "部署", "維護"}
    assert set(STAGE_PHASE.values()) == canonical_seven - {"維護"}
    options = FIELD_SPECS["階段"][1]
    assert options is not None
    for phase in STAGE_PHASE.values():
        assert phase in options, f"{phase} 不在 Project 階段欄位的選項裡"


def test_maintenance_states_are_still_absent_from_delivery_status() -> None:
    """釘住「維護缺口尚未關閉」這個事實本身。

    ⚠️ 這不是希望它永遠為真——而是**當它變成假的時候要有人知道**：若有人加了
    「運行中」／「失效」卻沒同步加 ``maintenance`` 階段，兩軸會再次不一致。
    """
    options = FIELD_SPECS["交付狀態"][1]
    assert options is not None
    joined = "".join(options)
    assert "運行中" not in joined
    assert "失效" not in joined


# ---------------------------------------------------------------- 一次一張


def test_no_bulk_or_autogenerate_path_exists() -> None:
    """⛔ 回填必須一張一張人工看（需求方 2026-08-25 裁定，issuecomment-5398180153）。

    ⚠️ 條文層的「不得批次」沒有機械執行者，⇒ 這裡把它釘成測試。

    ⛔ **但本檢查的範圍有限，不得讀成完整保證**（查核 R2 逐字指出）：它只攔得下
    ``open``／``amend`` 上這五個**具名**旗標。攔不到的有三類——新增的子命令、
    不同拼字的旗標、以及藏在既有 ``--brief`` 之後的自動生成。⇒ 它是**封閉集合的
    逐字比對**，而繞過封閉集合正是本 repo 已付過代價的形狀。

    ⭐ 理由不是偏好而是量測：aiwf#128 的研究顯示關鍵字重疊抓得到的是**命名相似**，
    而命名相似的那些不是缺陷 ⇒ 從核心痛點機械導出的「簡介」會複製其詞彙分佈，
    而 canonical §6.3 逐字「⛔ 它不是摘要」。機械產物必然是摘要。
    """
    from wf_cli.cli import build_parser

    parser = build_parser()
    subs = parser._subparsers._group_actions[0].choices  # type: ignore[attr-defined]
    banned = ("--brief-all", "--brief-bulk", "--backfill-brief", "--generate-brief", "--auto-brief")
    for verb in ("open", "amend"):
        opts = {o for a in subs[verb]._actions for o in (a.option_strings or [])}
        assert "--brief" in opts, f"{verb} 應有 --brief"
        for bad in banned:
            assert bad not in opts, f"{verb} 不得有批次／自動生成旗標 {bad}"


def test_brief_shape_check_cannot_tell_a_routing_signal_from_a_summary() -> None:
    """⚠️ 釘住本卡形狀驗證的**上限**，⛔ 不讓後人以為它擋得住敷衍。

    兩個標記都在、但內容是摘要而非路由訊號的簡介，機械上必然通過。
    ⇒ 「寫的人有沒有真的讀懂那張卡」沒有機械檢查擋得住；那是人工回填的殘餘風險，
    已記於 issuecomment-5398180153。
    """
    summary_not_routing = (
        f"這張卡在講 wfcli 的欄位。{brief.MARKER_WHEN}：不知道。{brief.MARKER_NON_SCOPE}不知道。"
    )
    brief.Brief(text=summary_not_routing)  # ⛔ 通過——這正是本測試要記錄的事實


def test_insert_works_on_cards_without_a_core_pain_section() -> None:
    """⭐ 插入錨點是「第一個 ``## `` 章節之前」，⛔ 不是「``## 核心痛點`` 之前」。

    實測 61 張活卡中有 **24 張（39%）** 沒有 ``## 核心痛點``——MIG1 一次性遷移卡用
    ``## Spec``／``## 現況摘要``。只認核心痛點會讓那 24 張永遠補不了簡介，而
    ``amend_brief`` 的存在理由正是給既有卡一條通道。
    ⚠️ 這個缺陷是查核 V5 要求「拿三張**真實**既有卡驗」時才浮出來的——
    ⛔ 自己造的樣本永遠有核心痛點章節，測不出它。
    """
    mig_shaped = (
        "- 需求：ruan6047\n\n## Spec\n\n- x\n\n## 現況摘要\n\n- y\n\n## Log\n\n- z\n"
    )
    assert "## 核心痛點" not in mig_shaped
    new_body, old = amend_brief(mig_shaped, GOOD)
    assert old is None
    assert brief.parse_block(new_body).text == GOOD
    # 簡介必須排在第一個既有章節之前，⛔ 不得落到 Log 裡
    assert new_body.index(brief.SECTION_HEADING) < new_body.index("## Spec")


# ---------------------------------------------------------------- dry-run 零寫入


def test_amend_dry_run_never_creates_project_fields(monkeypatch) -> None:
    """⛔ ``amend --dry-run`` 不得呼叫 ``project field-create``（查核 R3-001／R4-001）。

    ⚠️ **本測試的前一版是零資訊的**：它只直接呼叫 ``ac.list_fields``，沒有經過
    ``amend_cmd.run`` 的分流 ⇒ 把實作改回無條件 ``ensure_fields`` 後它照樣綠
    （PM 實跑變異檢驗確認：1 passed）。而它的 docstring 當時宣稱「負控會轉紅」——
    ⛔ 那個宣稱是假的。⭐ 本版改為**指令層**：跑真正的 ``run()``，並讓
    ``ensure_fields`` 一旦被呼叫就炸。

    **變異檢驗（PM 於本版寫成後實跑）**：把 ``run()`` 內的分流改回無條件
    ``ensure_fields`` ⇒ 本測試轉紅（``ensure_fields 不該在 dry-run 被呼叫``）。
    """
    import argparse

    import wf_cli.commands.amend_cmd as ac

    created: list[list[str]] = []

    class FakeRunner:
        def run_json(self, argv, **_):
            created.append(argv)
            if argv[:2] == ["project", "field-list"]:
                return {"fields": []}  # ⚠️ 刻意回空：缺欄位才會觸發 field-create
            if argv[:2] == ["project", "view"]:
                return {"id": "PVT_x", "owner": {"login": "o"}, "number": 4, "url": "u"}
            if argv[:2] == ["project", "item-list"]:
                return {"items": []}
            return {}

        def run(self, argv, **_):
            created.append(argv)
            return ""

        def graphql(self, *_a, **_k):
            return {"data": {"node": {"items": {"pageInfo": {}, "nodes": []}}}}

    def boom(*_a, **_k):
        raise AssertionError("ensure_fields 不該在 dry-run 被呼叫")

    monkeypatch.setattr(ac, "default_runner", FakeRunner())
    monkeypatch.setattr(ac, "ensure_fields", boom)

    args = argparse.Namespace(
        card_id="NOPE1", owner="o", project=4, repo=None, config=None,
        reason="probe", dry_run=True, brief=GOOD,
        spec_baseline=None, acceptance=None, verification=None, preserve_checked=False,
        db_scope=None, resources=None, tier=None, initiative=None,
        core_pain=None, ruling_url=None, record_unlogged_change=False, escalate=None,
    )
    ac.run(args)  # 找不到卡會回非 0，⛔ 但那不是本測試的斷言對象
    assert all("field-create" not in " ".join(c) for c in created), (
        f"dry-run 路徑呼叫了 field-create：{created}"
    )
