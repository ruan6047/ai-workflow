#!/usr/bin/env python3
"""``wfcli doctor`` 的**純判定與純渲染**部分（`WF-REDESIGN-W3` 驗收 2「轉薄」）。

## 為什麼這些在 ``scripts/`` 而不在 CLI 裡

卡面驗收 2 逐字：「邏輯抽至 ``scripts/``＋``ci.yml`` 具名 job；``wfcli doctor``
**保留名稱／旗標／rc／輸出契約**、委派至抽出腳本」。⇒ 本檔是被委派的那一半，
``cli/src/wf_cli/doctor.py`` 以 ``importlib.util.spec_from_file_location`` 載入它
（既有做法：``cli/tests/test_pollution_check.py:11``；⛔ 不需 package、⛔ 不需改
``cli/pyproject.toml``）。

## 收錄判準：**雙向**窮舉的交集（⛔ 非「doctor 的全部純函式」）

一個定義能搬過來，四條**同時**成立：

1. ⛔ 無跨模組相依 —— 本檔只 import 標準庫，⛔ 一個 ``wf_cli`` 符號都不用
   （這也是新 CI job 能在不裝 ``wf_cli`` 的情況下跑它的前提）。
2. ⛔ 無內外呼叫牽連 —— ⛔ 不呼叫任何留在 ``doctor.py`` 的東西。
3. ⛔ 執行期不需要 ``doctor.py`` 的 dataclass —— 型別註解引用不算
   （``doctor.py`` 有 ``from __future__ import annotations``，註解執行期不求值）。
4. ⭐ **它的相依常數⛔ 沒有留在 ``doctor.py`` 的使用者。** 這一條是**反方向**的：
   前三條問「它需要什麼」，這一條問「它需要的東西還有誰在用」。一個被兩邊都用到
   的常數，搬過來就得在 ``doctor.py`` 留第二份 ⇒ 第二個真相源。

## ⛔ 七個明確排除（各附理由，⛔ 不是漏的）

| 排除 | 行 | 理由 |
|---|---|---|
| ``_build_reachability_probes`` | 26 | 函式體內 ``from . import resources`` ＋ ``from .card import`` ×5，違反 1 |
| ``render_reachability`` | 31 | 讀 ``_REACHABILITY_PROBES``——被**留下**的函式以 ``global`` 改寫的可變全域；搬過來會讀到本檔那份永遠空的副本，**輸出靜默改變而 rc 不變**，違反 2 |
| ``render_conformance`` | 80 | 閉包經 ``CONFORMANCE_RULES`` 觸 ``RuleEpoch``，違反 3 |
| ``find_legacy_authority_notes`` | 28 | 執行期建構 ``LegacyAuthorityNoteFinding``，違反 3 |
| ``scan_envelope`` | 10 | 執行期建構 ``ScanEnvelope``，違反 3 |
| ``derive_expected_status`` | 40 | 唯一用到 ``_TRANSPARENT_EVENT_PREFIXES`` 者，而該常數字面內嵌 ``review.py`` 的兩個 tag（PM 2026-09-02 裁定⛔ 不抽） |
| ``render_state_face_drift`` 55／``severed_declared_keys`` 35／``required_trailers`` 12／``canonical_cite`` 8 | 110 | 違反 4：``CAUSE_*`` 還被 ``CONFORMANCE_CAUSES``／``attribute_cause``／``render_conformance`` 用；``TIER2_TRAILER`` 還被 ``evaluate_commit_trailers`` 用；``CANONICAL_SECTION`` 還被 ``CommitTrailerReport`` 用——全部留在 ``doctor.py`` |

## ⚠️ 明文登記：這是**帳面**轉薄，而且帳面很小

``doctor.py`` 少了這些行，但**執行時邊界⛔ 未改變**——同一條 ``wfcli doctor``、
同樣輸出、同樣 rc，這些行照樣被載入執行。痛點「doctor 邏輯駐留 CLI」**⛔ 未關**；
真要關需要四個消費者（``AGENTS.md``／``dispatch-package.md``／``handoff-contract.md``
／``CONSUMER_CONFORMANCE.md``）之一改跑 CI job，那四檔⛔ 全不在本卡 write-set。

⚠️ 代價：``wfcli doctor`` 從自足套件變成**依賴 repo 佈局**（editable 安裝＋目錄結構
兩個前提）。腳本不在時的行為是**明示降級**（印警告＋標「未執行」＋rc 不變），
⛔ 不是靜默 fallback 回內建邏輯——那份邏輯已經不在 ``doctor.py`` 了。
"""

from __future__ import annotations

import pathlib
from typing import Any

#: ⚠️ **只給型別註解用的別名，⛔ 不是 ``doctor.py`` 那三個定義的第二份真相。**
#:
#: 本檔⛔ 不 import ``wf_cli``（收錄判準 1；也是新 CI job 能在不裝套件的情況下跑它
#: 的前提），而 ``from __future__ import annotations`` 使註解**執行期不求值** ⇒ 下面
#: 三個名字只需要「存在」。把它們綁成 ``Any`` 是刻意的：**它們⛔ 不承載任何值域**，
#: 所以⛔ 不會與 ``doctor.py`` 的定義漂開——那三個真正的定義仍是唯一真相源，
#: 且 ``doctor.py`` 內仍有留下的使用者（``CommitRecord.shape``／``required_trailers``／
#: ``render_conformance`` 一線），⇒ 依收錄判準 4 它們**搬不過來**。
#: ⛔ 不得把它們改寫成真的 ``Literal``／``dataclass``——那一刻就變成第二個真相源。
CommitRecord = Any
CommitShape = Any
FieldSurfaceReport = Any




def _expected_delivery_status(
    verdicts: dict[str, str | None], deciding_attempts: list[str]
) -> tuple[str | None, str | None]:
    """由**據以放行的那些事件自己的結論**決定交付狀態應有的值。

    回傳 ``(expected, 歧義說明)``：兩者恰有一個為 None。

    先前是事後重掃全部留言、以「有沒有提到這個 attempt」決定誰有資格提供結論，
    因而兩種誤報：討論串引用裁決標題並提及該 attempt 會被算進來；以及 ``in``
    子字串比對讓 ``…-e0-<sha>`` 命中 ``…-e0-<sha>x``（同一個陷阱第三次）。
    改為在第一輪分類時就從該事件留言自身取下結論，不再有「誰有資格」的問題。

    **不得依留言順序決定**（``review-escalation.md`` §2）：同一 SHA 在 replan 後
    重審時，e0 與 e1 可能都被正確索引且結論相反，取「第一則」會讓結果隨排序而變。
    """
    results = {verdicts.get(a) for a in deciding_attempts}
    if None in results:
        return None, (
            "據以放行的事件中，有留言的 `## 查核裁決：` 結論無法辨識或不唯一"
            "（缺標題、結論非列舉值、或同一則留言出現多個結論），無從比對交付狀態。"
        )
    if not results:
        return None, None
    if len(results) > 1:
        return None, (
            "據以放行的 attempt 對應到多種裁決結論"
            f"（{'、'.join(sorted(r for r in results if r))}），無從判斷交付狀態應為何。"
            "同一 SHA 在 replan 後重審且結論相反時會出現此形態；依 review-escalation.md "
            "§2 不得依留言順序決定，請人工裁定。"
        )
    return results.pop(), None


def _check_third_face(expected: str | None, actual: str | None) -> str | None:
    """三面一致的第三面。回傳不一致的說明；一致則回 None。

    ``wfcli review`` 先寫 Issue 留言、再寫交付狀態、最後寫 body Log，三次遠端呼叫
    沒有交易性。留言與 Log 都成功而狀態欄失敗，就是半寫入——先前兩面一致即回
    ``recorded``，這種卡因此看起來完全正常，實際上看板上仍是待查核。
    """
    if actual is None:
        return (
            "無法讀取 Project 交付狀態欄，第三面未能驗證。契約 §3.1.3 要求三面一致，"
            "只驗到留言與 Log 兩面時不得宣稱已有裁決。"
        )
    if expected is None:
        return (
            f"找到裁決留言與 Log 索引，但留言中沒有可辨識的 `## 查核裁決：` 結論，"
            f"無從比對 Project 交付狀態（現為 {actual!r}）。"
        )
    if expected != actual:
        return (
            f"半寫入：裁決留言與 Log 索引都在，但 Project 交付狀態為 {actual!r}，"
            f"與裁決結論應有的 {expected!r} 不符。`wfcli review` 的三次遠端寫入沒有"
            "交易性，留言成功而狀態欄失敗即為此形態；請補齊狀態欄，不要重跑查核。"
        )
    return None


_IDENTITY_ENDORSED_NOTE = (
    "身分基礎：需求方背書，非機械可驗。本卡找不到可對帳的外部收據，"
    "「誰查核的」只有 review event 的 reviewer 自由字串為憑，而該欄只驗非空——"
    "GitHub 平台層無從證明裁決確實出自該查核者。跨家族查核者沒有 GitHub 寫入通道，"
    "收據構造上取不到，**故這不是缺陷**：不改變上面的判定、不改變 exit code，"
    "也不表示查核沒做。它只界定上面那個結論的效力範圍——已進狀態面的是「裁決內容」，"
    "不是「查核者身分」。"
)


_IDENTITY_RECEIPT_NOTE = (
    "身分基礎：外部收據的 GitHub comment author（平台可驗證）。"
    "收據內文的模型／工具名稱仍只是自述，不是身分證明。"
)


def _identity_annotation(receipt_urls: list[str]) -> tuple[str, str]:
    """回傳 ``(identity_basis, 附註文字)``。

    唯一判準是「有沒有可對帳的收據」，因為那是這條通道上唯一由平台（而非由
    寫入者自己）產生的身分證據。刻意**不**做成警告或阻擋：需求方 2026-08-19
    裁定走「丙＋甲的殘留」，理由是收據在跨家族通道上構造上拿不到，凡以它為
    條件的警告必然每次都響、內容永遠一樣，資訊量等於靜默（ai-workflow#31
    停卡理由）。所以這裡只據實標明依據，不改判定。
    """
    if receipt_urls:
        return "receipt_backed", _IDENTITY_RECEIPT_NOTE
    return "requester_endorsed", _IDENTITY_ENDORSED_NOTE


def classify_commit_shape(record: CommitRecord) -> CommitShape:
    """判定 commit 形狀。**判準全部從 commit 自身導出**，不看卡面、不看人工標註。

    四種被明確裁定的形狀（卡面驗收第 2 條）：

    - **merge commit**（`parents >= 2`）：分兩種。combined diff（`--cc`）為空的是
      `merge_clean`——它的 tree 完全由 parent 解釋得出，**沒有自己著作的內容**，
      故不是實作 commit。combined diff 非空的是 `merge_with_content`：那些行與
      **每一個** parent 都不同，是在 merge 當下寫下的（衝突解法／evil merge），
      屬著作內容，故照實作 commit 辦。這也順手堵掉「把改動塞進 merge commit」
      這條規避路徑。
    - **基線更新 merge**：也是 merge commit，同一格處理。本模組**刻意不區分**
      它與整合 merge——兩者都只是 `parents >= 2`，誰是 main 取決於你站在哪個
      ref 上看，那是脈絡不是 commit 自身的性質。既然導不出來就不假裝導得出來；
      何況兩者要求相同（`ANCHOR_MERGE` 對 merge commit 一視同仁），區分了
      也不改變判定。
    - **cherry-pick**：不設特例，一律當普通實作 commit。理由是它**認不出來**：
      `-x` 才會留 `(cherry picked from commit …)`，而 `-x` 是選配，沒帶就與原生
      commit 完全無法區分。認不出來就 fail-closed。代價為零——cherry-pick 連
      訊息一起複製，來源合規則結果也合規；`-x` 那一行不是 `key: value`，
      `only=true` 會濾掉它，不影響同區塊其他 trailer 的解析。
    - **空 commit**（單 parent 且無任何路徑改動）：不是實作 commit。它沒有著作
      任何內容，也就沒有內容的來歷需要宣告——與 `merge_clean` 同一條原則
      （**要求 trailer 的是內容，不是 commit 這個容器**），不是兩條臨時規則。
      推論一：空 commit 藏不了東西，豁免它不開洞。推論二：本檢查器**逐 commit
      獨立判定、不繼承**——一筆帶齊 trailer 的空 commit 不會使它前面那筆裸的
      commit 變綠（git metadata 本來就不由 descendant 繼承）。至於治理層要不要
      **採認**那種補記，是規則層裁定，**不在本卡射程**（見卡面射程說明）；本模組
      只提供分流能力，不代替需求方裁定。

    root commit（`parents` 為空）走 `implementation`：它相對空樹的差異就是它的內容。
    """
    if len(record.parents) >= 2:
        return "merge_with_content" if record.merge_content_paths else "merge_clean"
    if not record.changed_paths:
        return "empty"
    return "implementation"


def _short_event(first_line: str | None, limit: int = 96) -> str | None:
    if first_line is None:
        return None
    return first_line if len(first_line) <= limit else first_line[: limit - 1] + "…"


def render_field_surface(report: FieldSurfaceReport) -> str:
    lines = ["## 5.8 欄位層對帳（看板實際欄位 vs 宣告；與逐卡 findings 正交）"]
    if report.status != "scanned":
        lines.append("（未掃描：本次未取得 Project 欄位值。**這不等於沒有**。）")
        return "\n".join(lines)
    lines.append(
        f"已比對 {report.scanned_cards} 張卡的欄位值；"
        f"已知內建欄位 {len(report.builtin_fields_seen)} 個"
        f"（{'、'.join(report.builtin_fields_seen) or '—'}）已排除。"
    )
    if not report.findings:
        lines.append("- 孤兒欄位：無；宣告但零值的欄位：無")
        return "\n".join(lines)
    for finding in report.findings:
        lines.append(
            f"- [{finding.kind}] `{finding.field_name}`（{finding.cards_with_value} 張有值）"
            f"　{finding.detail}"
        )
    return "\n".join(lines)


# ===========================================================================
# 自檢（`ci.yml` 的 `doctor-pure` job 直接跑本檔，退出碼即判定）
# ===========================================================================
#
# ⭐ **本自檢守的東西⛔ 不與 `tests` job 重疊。** `tests` 在裝好 `wf_cli` 的環境裡跑，
# 因此它**看不見**「本檔偷偷 import 了 `wf_cli`」這個回歸——那個 import 在那裡永遠
# 成功。本 job 以 `uv run --no-project` 跑（⛔ 不裝 `wf_cli`），⇒ 收錄判準第 1 條
# 一旦被破壞，這裡立刻紅。
#
# ⚠️ **本 job ⛔ 未接線為 required check**（規劃階段裁定 8）。它已具名，但 ruleset
# 20768920 的 required check 字面只有 `tests`；把新 job 接上去是**需求方**的動作，
# ⛔ 不由本卡代行。交付／結案報告須逐字寫「已具名、⛔ 未接線為 required check」。


def _selfcheck() -> int:  # pragma: no cover - 由 CI job 執行，⛔ 非 pytest 射程
    import ast
    import sys
    from types import SimpleNamespace

    failures: list[str] = []

    # (1) ⛔ 一個 `wf_cli` 符號都不用（收錄判準 1）。
    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (
            node.level > 0 or (node.module or "").startswith("wf_cli")
        ):
            failures.append(f"⛔ 第 {node.lineno} 行 import 了 wf_cli（收錄判準 1 被破壞）")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("wf_cli"):
                    failures.append(f"⛔ 第 {node.lineno} 行 import 了 {alias.name}")

    # (2) 六個函式各跑一組 fixture。⛔ 不重打判定邏輯——只釘「它跑得動且答得出東西」。
    cases: list[tuple[str, object, object]] = [
        ("_short_event", _short_event("abc"), "abc"),
        ("_short_event(截斷)", _short_event("x" * 200), "x" * 95 + "…"),
        ("_short_event(None)", _short_event(None), None),
        ("_identity_annotation(空)", _identity_annotation([])[0], "requester_endorsed"),
        ("_identity_annotation(有)", _identity_annotation(["u"])[0], "receipt_backed"),
        ("_check_third_face(一致)", _check_third_face("✅通過", "✅通過"), None),
        (
            "classify_commit_shape(merge_clean)",
            classify_commit_shape(
                SimpleNamespace(parents=["a", "b"], merge_content_paths=[], changed_paths=[])
            ),
            "merge_clean",
        ),
        (
            "classify_commit_shape(merge_with_content)",
            classify_commit_shape(
                SimpleNamespace(parents=["a", "b"], merge_content_paths=["x"], changed_paths=[])
            ),
            "merge_with_content",
        ),
        (
            "classify_commit_shape(empty)",
            classify_commit_shape(
                SimpleNamespace(parents=["a"], merge_content_paths=[], changed_paths=[])
            ),
            "empty",
        ),
        (
            "classify_commit_shape(implementation)",
            classify_commit_shape(
                SimpleNamespace(parents=["a"], merge_content_paths=[], changed_paths=["x"])
            ),
            "implementation",
        ),
    ]
    for name, got, want in cases:
        if got != want:
            failures.append(f"⛔ {name}：得 {got!r}，期望 {want!r}")

    # `_expected_delivery_status` 與 `render_field_surface` 只釘「回得出宣告的型別」——
    # 它們的**內容**判定由 `cli/tests/test_doctor.py` 負責，⛔ 不在本處重打一份。
    status, reason = _expected_delivery_status({}, [])
    if not (status is None or isinstance(status, str)):
        failures.append(f"⛔ _expected_delivery_status 回了 {type(status)}")
    if not (reason is None or isinstance(reason, str)):
        failures.append(f"⛔ _expected_delivery_status 第二元回了 {type(reason)}")
    text = render_field_surface(
        SimpleNamespace(status="unscanned", scanned_cards=0, builtin_fields_seen=(), findings=())
    )
    if "未掃描" not in text:
        failures.append("⛔ render_field_surface 的未掃描分支輸出不含「未掃描」")

    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(f"[doctor-pure] ⛔ 自檢失敗 {len(failures)} 項", file=sys.stderr)
        return 1
    print(f"[doctor-pure] ✅ 自檢通過（{len(cases) + 3} 項）")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_selfcheck())
