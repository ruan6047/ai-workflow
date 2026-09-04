"""待審清單收件表單（`WF-REDESIGN-W1` 驗收 1／5）與它的讀取端。

⭐ 本檔的承重之處是**模板與程式碼的逐字對照**：GitHub Issue Forms 把每個欄位渲染成
``### <label>``，那就是 ``wf_cli.intake`` 的定位錨點。⇒ 兩邊漂了，**每一張照表單開的
清單項都升不了級**，而那個失敗只會在有人真的跑 ``open --from-issue`` 時才出現。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from wf_cli.intake import NO_RESPONSE, REQUIREMENTS, missing_requirements, read_form, remediation

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "list-intake.yml"

#: 撤銷程序的註記字面（`WF-REDESIGN-W1` 驗收 5 逐字）。⛔ 本卡只在說明欄註記，
#: ⛔ 不新增 CLI 動詞、⛔ 不先行生效任何 stage-rule——條文化歸 W2A。
REVOCATION_NOTE = "降回清單＝PM 執行 deleteProjectV2Item＋轉移留言"


def _template_labels() -> list[str]:
    """從模板抓 ``label:`` 的值，**依出現順序**。

    ⛔ 刻意不引入 YAML 剖析器：``cli/pyproject.toml`` 的 ``dependencies = []``，為了讀
    五個字串多一個相依不划算。本正則只吃 ``      label: <值>`` 這一種行，模板改成別的
    縮排或引號形式時它會**讀不到**（⇒ 下面的相等斷言轉紅），⛔ 不會靜默漏讀。
    """
    return re.findall(r"^\s+label: (.+)$", TEMPLATE.read_text(encoding="utf-8"), re.MULTILINE)


def test_the_form_exists_and_has_one_field_per_requirement():
    """五條件各一欄（驗收 1 逐字），且**順序與字面**都與程式碼一致。"""
    assert TEMPLATE.exists(), f"收件表單不存在：{TEMPLATE}"
    assert _template_labels() == list(REQUIREMENTS), (
        "模板欄位標題與 wf_cli.intake.REQUIREMENTS 不一致 ⇒ 照表單開的清單項會升不了級"
    )


def test_every_field_is_required_in_the_form():
    """五欄在表單側就是必填——⛔ 不把「有沒有填」整個推給 CLI 事後檢查。"""
    text = TEMPLATE.read_text(encoding="utf-8")
    assert text.count("required: true") == len(REQUIREMENTS)


def test_the_form_carries_the_revocation_note_verbatim():
    """驗收 5：撤銷程序**只**在收件模板的說明欄註記。"""
    assert REVOCATION_NOTE in TEMPLATE.read_text(encoding="utf-8")


def test_the_card_adds_no_cli_verb_for_revocation():
    """⛔ 驗收 5 逐字「不新增 CLI 動詞」——這條把它釘成機械事實。"""
    from wf_cli.commands import COMMAND_MODULES

    names = {m if isinstance(m, str) else getattr(m, "__name__", str(m)) for m in COMMAND_MODULES}
    joined = " ".join(sorted(names))
    for forbidden in ("revoke", "撤銷", "demote", "delete_project"):
        assert forbidden not in joined


# ==========================================================================
# 讀取端
# ==========================================================================


def _rendered(**answers: str) -> str:
    """模擬 GitHub Issue Forms 的渲染輸出。"""
    return "\n".join(f"### {label}\n\n{answers.get(label, '填答')}\n" for label in REQUIREMENTS)


def test_a_complete_form_reads_back_every_answer_verbatim():
    body = _rendered(**{label: f"答-{i}" for i, label in enumerate(REQUIREMENTS)})
    assert missing_requirements(body) == []
    assert read_form(body) == {label: f"答-{i}" for i, label in enumerate(REQUIREMENTS)}


def test_multi_line_and_fenced_answers_survive_verbatim():
    """查重留痕那一欄實務上會貼指令；⛔ 不得被切段規則吃掉。"""
    answer = '搜了「開卡閘」「from-issue」，命中 #177 #217\n\n```bash\ngh issue list --state all\n```'
    body = _rendered(**{"查重留痕": answer})
    assert read_form(body)["查重留痕"] == answer


@pytest.mark.parametrize("label", REQUIREMENTS)
def test_a_single_missing_field_is_named(label):
    body = "\n".join(
        f"### {other}\n\n填答\n" for other in REQUIREMENTS if other != label
    )
    assert missing_requirements(body) == [label]


def test_an_unfilled_optional_field_counts_as_missing():
    """GitHub 對「有欄位但沒填」渲染 ``_No response_``——⚠️ 它**看起來非空**。"""
    body = _rendered(**{"提案者身分": NO_RESPONSE})
    assert missing_requirements(body) == ["提案者身分"]


def test_a_whitespace_only_answer_counts_as_missing():
    body = _rendered(**{"出處可指": "   "})
    assert missing_requirements(body) == ["出處可指"]


def test_a_body_that_is_not_the_form_at_all_reports_all_five():
    assert missing_requirements("我發現一個問題，應該改成 Z。") == list(REQUIREMENTS)


def test_a_duplicated_heading_refuses_to_take_the_first_one():
    """同一個欄位標題出現兩次 ⇒ ⛔ 拒絕猜哪一個是填答（判成缺項）。

    紀律與 ``resources._declaration_section``／``brief._brief_section`` 同一組：
    定位不唯一就 fail-closed，⛔ 不取第一個。
    """
    body = _rendered() + "\n### 出處可指\n\n另一份填答\n"
    assert missing_requirements(body) == ["出處可指"]


# ==========================================================================
# 拒絕訊息必須含**跑得出**的補救指令（驗收 2 逐字）
# ==========================================================================


def test_remediation_is_runnable_and_carries_the_real_repo_and_number():
    text = remediation("https://github.com/ruan6047/ai-workflow/issues/218", ["查重留痕"])
    assert "gh issue view 218 --repo ruan6047/ai-workflow" in text
    assert "gh issue edit 218 --repo ruan6047/ai-workflow --body-file /tmp/intake-218.md" in text
    # ⛔ 指令本身不得留 <佔位>：只有**內容**那一格可以。
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("gh "):
            assert "<" not in stripped, f"補救指令留了佔位符：{stripped}"


def test_remediation_names_every_missing_field():
    text = remediation("https://github.com/acme/wf/issues/7", list(REQUIREMENTS))
    for label in REQUIREMENTS:
        assert f"### {label}" in text
