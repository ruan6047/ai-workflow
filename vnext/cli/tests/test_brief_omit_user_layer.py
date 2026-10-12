"""#440：`brief --omit-user-layer`＝省略使用者層（`~/.wf/`）原文；帶上時不讀、不附。

不帶旗標的輸出逐字不變（既有測試原樣通過）；帶旗標時只動三處：附錄⛔ 無 `### 使用者層` 區塊、
首屏 `### 模型資料狀態` 換成一行固定說明、結構說明（附錄開頭／預設輸出指標）不再說「四層」。
何時加旗標住 `rules/roles/PM.md` §3；CLI 只描述內容、⛔ 不判目的地。全部走注入式快照，零網路、零 mutation。
"""

import pytest

from wfx.core.layers import UNKNOWN_MODEL_DATA, USER_LAYER_OMITTED
from wfx.verbs.brief import (
    APPENDIX_NOTE, FULL_POINTER, OMITTED_APPENDIX_NOTE, OMITTED_FULL_POINTER, parse_args,
)

from .conftest import TASK_ID
from .test_brief import section

FLAG = "--omit-user-layer"

# 使用者層原文：含與框架規則同字的行（`---`）與會被誤當切點的 `### ` 標題
USAGE = ("---\nname: usage\n---\n# 模型使用說明（測試）\n### 專案層\n"
         "家族甲：只在使用者層出現的一行。\n來源：需求方；最後確認時間：2026-10-12\n")
AVAILABILITY = "# 可用性備註（測試）\n家族乙：額度受限，只在使用者層出現。\n"

USER_STATUS_ROW_PREFIXES = ("- ~/.wf/model-usage.md：", "- ~/.wf/model-availability.md：")


def nonempty(text):
    return [line for line in text.splitlines() if line.strip()]


@pytest.fixture
def user_files(user_root):
    user_root.mkdir(parents=True)
    (user_root / "model-usage.md").write_text(USAGE, encoding="utf-8")
    (user_root / "model-availability.md").write_text(AVAILABILITY, encoding="utf-8")
    return user_root


def replace_status_rows(lines):
    """首屏 `### 模型資料狀態` 的兩列（每檔一列）換成固定說明一行。"""
    status = lines.index("[來源: user:~/.wf/#狀態]") + 1
    assert [line.startswith(USER_STATUS_ROW_PREFIXES) for line in lines[status:status + 3]] == [
        True, True, False]
    return lines[:status] + [USER_LAYER_OMITTED] + lines[status + 2:]


def without_user_layer(full_output):
    """不帶旗標的 `--full` 輸出，機械套上帶旗標應有的三處差異（測試端的期望值，⛔ 不是產品程式）。

    附錄的使用者層區塊從 `### 使用者層` 切到**最後一個** `### 專案層`（使用者層原文自己也含這一行）。
    """
    lines = full_output.splitlines()
    start = lines.index("### 使用者層")
    end = len(lines) - 1 - lines[::-1].index("### 專案層")
    lines = replace_status_rows(lines[:start] + lines[end:])
    return "\n".join(lines).replace(APPENDIX_NOTE, OMITTED_APPENDIX_NOTE) + "\n"


# T1（驗收 2）：⛔ 無 `### 使用者層`；使用者層每個非空行扣除框架／專案層同字行後零出現；其餘逐字不變
def test_full_with_flag_drops_only_the_user_layer(run_cli, user_files):
    rc, baseline, err = run_cli()
    assert (rc, err) == (0, "")
    rc, omitted, err = run_cli(FLAG)
    assert (rc, err) == (0, "")

    assert "### 使用者層" not in omitted.splitlines()
    assert "[來源: user:~/.wf/model-usage.md#全文]" not in omitted
    assert "[來源: user:~/.wf/model-availability.md#全文]" not in omitted

    # 扣除：同字行也出現在框架規則或專案層者（這組輸入是 `---` 與結構標題 `### 專案層`）
    out_lines = omitted.splitlines()
    user_lines = nonempty(USAGE) + nonempty(AVAILABILITY)
    deducted = [line for line in user_lines if line in out_lines]
    assert deducted == ["---", "---", "### 專案層"]
    assert omitted.count("\n### 專案層\n") == 1          # 只剩結構標題本身

    assert omitted == without_user_layer(baseline)
    assert section(omitted, "模型資料狀態") == f"[來源: user:~/.wf/#狀態]\n{USER_LAYER_OMITTED}\n"
    assert UNKNOWN_MODEL_DATA not in omitted


# 預設有界輸出同樣適用首屏規則；指標不再說「四層」
def test_bounded_with_flag_replaces_status_and_pointer(run_cli, user_files):
    _, baseline, _ = run_cli(full=False)
    rc, omitted, err = run_cli(FLAG, full=False)
    assert (rc, err) == (0, "")
    lines = replace_status_rows(baseline.splitlines())
    assert omitted == "\n".join(lines).replace(FULL_POINTER, OMITTED_FULL_POINTER) + "\n"
    assert len(nonempty(omitted)) < len(nonempty(baseline))


# T2（驗收 2）：帶旗標時⛔ 不讀 `~/.wf/`——兩檔都不是 UTF-8 仍 rc=0（不帶旗標時同一輸入是 rc=1）
@pytest.mark.parametrize("full", [True, False])
def test_flag_does_not_read_user_files(run_cli, user_root, full):
    user_root.mkdir(parents=True)
    for name in ("model-usage.md", "model-availability.md"):
        (user_root / name).write_bytes(b"\xff# x\n")
    assert run_cli(full=full)[0] == 1
    rc, out, err = run_cli(FLAG, full=full)
    assert (rc, err) == (0, "")
    assert USER_LAYER_OMITTED in out and UNKNOWN_MODEL_DATA not in out


# 驗收 3：同一輸入不帶旗標＝照舊附使用者層全文
def test_without_flag_user_layer_is_still_reproduced(run_cli, user_files):
    rc, out, _ = run_cli()
    assert rc == 0
    block = out.split("\n### 使用者層\n", 1)[1]
    assert USAGE.strip("\n") in block and AVAILABILITY.strip("\n") in block
    assert USER_LAYER_OMITTED not in out and OMITTED_APPENDIX_NOTE not in out


# T3：旗標預設關、與 `--full` 正交；說明文字只描述內容，⛔ 不以目的地為條件
def test_flag_defaults_off_and_describes_content_only():
    base = ["--task", TASK_ID, "--role", "執行者", "--stage", "執行"]
    assert parse_args(base).omit_user_layer is False
    assert parse_args(base + [FLAG]).omit_user_layer is True
    both = parse_args(base + ["--full", FLAG])
    assert (both.full, both.omit_user_layer) == (True, True)
    texts = (USER_LAYER_OMITTED, OMITTED_APPENDIX_NOTE, OMITTED_FULL_POINTER)
    for word in ("外送", "外部", "external", "審核者"):
        assert not any(word in text for text in texts), word
