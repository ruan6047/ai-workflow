"""待審清單收件表單的讀取端（`WF-REDESIGN-W1` 驗收 1／驗收 2）。

清單項＝**不在 Project #4 的 issue**；卡＝在板 issue。`wfcli open --from-issue <url>`
是清單項升級成卡的**唯一**路徑，本模組是那條路徑上的收件檢查。

判準
----

``stage-rules/list-intake-requirements.md`` 的五條件，**一條件一欄**。本模組只判
**五欄有沒有填**（該檔「PM 的動作」逐字：「四項齊 ⇒ …；缺任一項 ⇒ 退回提案者補」，
第五條同形）。

⛔ **不判內容**：出處指得對不對、觀察是不是真的觀察、關鍵字選得好不好、repo 填得對
不對、session ID 核不核得到——⛔ 一律不在本模組射程。那些是開卡之後、需求階段 R1
的事，而 R1 的條文歸 W2A。

⚠️ **這道閘門擋得住什麼，⛔ 說清楚**：它擋的是「表單沒填完就想升級」。它⛔ 擋不住
「五欄都填了但內容是廢話」，也⛔ 擋不住 PM 自己提案自己收件（那一條在
``list-intake-requirements.md`` 逐字寫著「機械上不成立，效力只來自留痕」）。

欄位標題是介面
--------------

:data:`REQUIREMENTS` 的五個字面**必須**與 ``.github/ISSUE_TEMPLATE/list-intake.yml``
的 ``label:`` 逐字相同——GitHub Issue Forms 把每個欄位渲染成 ``### <label>``，那就是
本模組的定位錨點。兩邊漂了，**每一張照表單開的清單項都會升不了級**。
⛔ 不靠約定：``tests/test_intake.py`` 以模板檔為來源做逐字對照。
"""

from __future__ import annotations

from .brief import _reuse_probe as _split_at_log_reuse_probe
from .resources import ResourceDeclarationError, _split_at_log

# ⭐ 探測⛔ 不重打一份，見 ``card_face`` 同一行的說明。
_split_at_log_reuse_probe()

#: 五條件的欄位標題，**順序即表單順序**。⛔ 封閉集合——值域的 owner 是
#: ``stage-rules/list-intake-requirements.md`` 的節名，⛔ 不是本檔。
REQUIREMENTS: tuple[str, ...] = (
    "出處可指",
    "是觀察不是結論",
    "查重留痕",
    "屬哪個 repo",
    "提案者身分",
)

#: GitHub Issue Forms 對「有欄位但沒填」渲染的字面。⚠️ 它**看起來非空**，
#: 逐字比對才分得出「填了」與「跳過了」。
NO_RESPONSE = "_No response_"

_HEADING_PREFIX = "### "


class IntakeError(ValueError):
    """收件表單缺欄位、欄位空白，或標題重複。"""


def _section_text(lines: list[str], label: str) -> str | None:
    """回傳 ``### <label>`` 之後、下一個 markdown 標題之前的內文。

    ``None`` ＝找不到該標題（或找到多於一個——重複時⛔ 拒絕取第一個，理由與
    ``resources._declaration_section``／``brief._brief_section`` 逐字相同）。
    """
    starts = [i for i, ln in enumerate(lines) if ln.strip() == f"{_HEADING_PREFIX}{label}"]
    if len(starts) != 1:
        return None
    start = starts[0]
    end = next(
        (j for j in range(start + 1, len(lines)) if lines[j].lstrip().startswith("#")),
        len(lines),
    )
    return "\n".join(lines[start + 1 : end]).strip()


def read_form(body: str) -> dict[str, str]:
    """把清單項 body 讀成 ``{欄位標題: 填答}``；只收讀得到且非空的欄位。

    ⛔ 不拋例外——缺欄位由 :func:`missing_requirements` 表達，讓呼叫端一次印出全部
    缺項而不是一輪修一格。
    """
    try:
        head, _ = _split_at_log(body or "")
    except ResourceDeclarationError:
        # ⚠️ 這裡**刻意吞掉排版例外並退回全文**，⛔ 與 card.py 那些讀取端不同：
        # (a) 現在的行為：`## Log` 標題重複／被字面 \n 打壞時，改用整份 body 定位。
        # (b) 為什麼：本模組讀的是**清單項**，而清單項構造上沒有 `## Log`（它不是卡）。
        #     真的出現 Log 字樣時，那是提案者引文裡帶的，⛔ 不是 append-only 留痕
        #     ⇒ 沒有「歷史回音會被當成現況」這個風險，切段的唯一效果只剩誤拒。
        # (c) ⛔ **不得由此推出「卡面讀取端也可以這樣吞」**：那些讀的是卡，卡的 Log
        #     裡真的有舊值回音，fail-closed 在那邊是承重的。
        head = body or ""
    lines = head.splitlines()
    found: dict[str, str] = {}
    for label in REQUIREMENTS:
        text = _section_text(lines, label)
        if text is None or not text or text == NO_RESPONSE:
            continue
        found[label] = text
    return found


def missing_requirements(body: str) -> list[str]:
    """回傳讀不到（或空白）的欄位標題，**依表單順序**。空清單＝五欄齊。"""
    filled = read_form(body)
    return [label for label in REQUIREMENTS if label not in filled]


def remediation(issue_url: str, missing: list[str]) -> str:
    """缺欄位時的**可跑**補救指令（卡面驗收 2 逐字要求「跑得出」）。

    ⭐ 三行都是真指令、參數已代入實際的 repo 與編號，⛔ 不是 ``<在此填寫>`` 這種
    示意——本 repo 量到 37+ 則拒絕訊息沒有可跑補救，那正是 W3′ 要收的洞；本卡不得
    再產出一則。

    ⚠️ 第二行的 ``<在此填寫>`` 是**內容**佔位，⛔ 不是指令佔位：三行照抄貼上會跑完，
    產出的 issue body 帶著待填的空欄位，人接著編輯它。⛔ 不宣稱它能自動填好內容。
    """
    owner_repo, number = _split_issue_url(issue_url)
    tmp = f"/tmp/intake-{number}.md"
    blocks = "".join(f"\\n### {label}\\n\\n<在此填寫>\\n" for label in missing)
    return (
        f"⇒ 補齊後重跑。缺的 {len(missing)} 欄可用下列三行補進原 issue（已代入實際 repo 與編號）：\n"
        f"    gh issue view {number} --repo {owner_repo} --json body --jq .body > {tmp}\n"
        f'    printf \'{blocks}\' >> {tmp}\n'
        f"    gh issue edit {number} --repo {owner_repo} --body-file {tmp}\n"
        f"  （或改用收件表單重開一張：gh issue create --repo {owner_repo} "
        f"--template list-intake.yml --web）"
    )


def _split_issue_url(issue_url: str) -> tuple[str, str]:
    """``https://github.com/<owner>/<repo>/issues/<n>`` → ``("<owner>/<repo>", "<n>")``。

    ⚠️ 呼叫端必須已驗過 URL 形狀（``open`` 走 :func:`validate_issue_url`）；本函式
    ⛔ 不再驗一次，也⛔ 不猜——形狀不對時切出來的值只會讓補救指令跑不動，而那正是
    上游該擋的。
    """
    parts = issue_url.rstrip("/").split("/")
    return f"{parts[-4]}/{parts[-3]}", parts[-1]


__all__ = [
    "NO_RESPONSE",
    "REQUIREMENTS",
    "IntakeError",
    "missing_requirements",
    "read_form",
    "remediation",
]
