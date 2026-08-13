"""WF-CLEANUP-GUARD1：破壞性收尾操作的守衛（T4 紅線）。

canonical ``AI_WORKFLOW.md:146``：「lease 可續約、可到期回收；**回收前先檢查未提交
變更，禁止靜默刪除工作內容**。」本模組把那句話變成機械守衛：任何會移除 worktree
或刪除本地／遠端分支的自動化路徑，都必須先讓**全部前提可機械驗證成立**；任一不成
立（含「無法觀測」）即降為純偵測，只回報、不動手。

## 這個模組在既有分工中的位置（引用，不重述）

- **刪除順序**：`templates/worktree-lifecycle.md` 第 11 行（第 5 點）的七步結案清單
  是唯一權威。本模組**只引用不重述**：`AUTHORITY_PATH` 指向該檔，`STEP_ROLES` 只
  記錄「第幾步扮演什麼角色」，步驟內容本身不在此複製一份。
  `tests/test_cleanup.py::test_destructive_order_matches_authority` 直接解析該檔驗
  證順序，讓權威檔漂移時本模組會轉紅，而不是靜靜地帶著過期副本繼續跑。
- **worktree 分類**：`doctor.py` 的 `WorktreeClass`（registered_active／orphan_*／
  detached_sandbox）是既有權威，其軸是「這個 worktree 對得上哪張卡」。本模組的
  `GuardCheck` 是**另一條軸**：「刪掉它會不會毀掉工作內容」。兩者不互相覆蓋，也
  不重新定義對方的分類。
- **終態列舉**：`commands/assign_cmd.TERMINAL_STATUSES` 是既有權威，直接 import。
- **lease 語意**：`registry.RegisteredCard.owner_assigned()` 是既有權威。

## 三段分離（卡面驗收，#16 §2.3 把整個收尾轉換交給本卡）

七步清單的角色**不是**「全部都是前置」——那會構成循環（第 4 步正是 release 自己
的效果，若列為前置則 release 永遠發動不了）：

- 第 1–3 步 = **前置條件**（merge 複驗＋push／worktree 與分支清理／資源宣告釋放）
- 第 4 步 = **本轉換的效果本身**（Issue 關閉＋release 事件＋終態落地），**守衛不得
  檢查它**
- 第 5–7 步 = **其後義務**（卡檔封存／Ledger 投影重建／對帳三件套），三者皆不寫狀
  態面，**未完成不得阻擋 release**

## 唯一機械 executor

收尾轉換只有一個機械 executor：`execute_closeout_transition`。**現況：只有 `release`
（操作者當場發動）呼叫它**；`reconcile --apply` 白名單第 2 條（批次）尚不存在，
**該側因此完全沒有守衛**（卡面驗收第 4 條把它劃出本卡射程，歸 #16 §9 的 G 卡）。

它被寫出來時必須呼叫同一個函式，而不是自己另寫一條。這件事在本模組內能保證的是
「這份實作不會為了單一觸發者而分叉」，而保證的方式是**資料流限制**而非行為約定：
真正做事的 `_execute_closeout()` **收不到觸發者標籤**——不是參數、不是自由變數、也
沒有同名模組全域，`execute_closeout_transition()` 在它回傳之後才把標籤 `replace`
上去。`evaluate_cleanup_guard()` 的簽章同樣沒有 trigger 參數。強度、釘住它的三條測試
與**買不到的部分**（走呼叫堆疊仍讀得到外層 frame）見 `docs/WF_CLEANUP_GUARD1.md`
§4.0。**「不會有人繞過它」不在本模組能保證的範圍內。**

## --force 為何是「不可用」而非「不建議」

`_forbid_force()` 掛在**本模組唯一的 git 執行入口**上。任何帶 ``--force`` ／``-f``
／``-D`` 等旗標的 git 呼叫會在送進 subprocess 之前就丟 `CleanupGuardError`。這不是
文件約定，是呼叫點的硬阻擋——日後有人「順手加個 --force」會直接炸在測試上。

## 遠端刪除是**條件式**的（R1-001 → R2-001）

前提檢查與 `git push --delete` 之間**有一段時間窗**：本機 worktree 移除與本地分支
刪除就發生在其中。另一個 clone 在這段窗內把新提交推上同一條遠端分支時，只重新確認
「分支還在」是不夠的——分支確實還在，但它指的已經是別人的新工作。

`recheck_remote_branch()` 因此在按下刪除鍵前重讀 tip SHA、確認該 commit 可觀測、
重驗祖先關係。**但「重讀」只是讀**：R2-001 的隔離實測證明，在 recheck 回傳
``delete`` 之後、`push --delete` 送出之前推入的新提交仍會被刪掉——兩者之間沒有
compare-and-swap，窗只是變窄，沒有被關上。

修法是讓檢查與刪除變成**同一個原子操作**：recheck 讀到的那個 tip 原樣成為刪除的
租約期望值（`RemoteDeleteDecision.expected_tip` → `conditional_delete_args()` →
``--force-with-lease=refs/heads/<branch>:<tip>``）。遠端在這之間變動過，git 在
**送出任何更新指令之前**就以 ``(stale info)`` 拒絕（見下方 `_LEASE_RE` 的註解）。
拒絕即 `mode="aborted"`，效果（第 4 步）一併扣住——與守衛其餘拒絕路徑同型，
不靜默略過、不重試、不降級為無條件刪除。

## 「內容已在 main」為何不能只用祖先關係（WF-CLEANUP-SQUASH-AWARE1）

`ROADMAP.md §3.5`（2026-08-13）裁定**卡片一律以 squash 合併**——因為 GitHub 的 merge
按鈕產不出 `Reviewed-by`，界線跨過後每次按鈕合併都是 `DEV-COMMIT-TRAILER-GUARD1`
檢查器的違規。而 squash 產生的是一筆**全新 commit**，分支 tip 永遠不會是 main 的
祖先，於是 `merge-base --is-ancestor` **對之後每一張卡都恆拒**（實測：#9、#63、#73
三張已 APPROVE 並合併的卡全被擋，唯一通過的 #48 是當日唯一用 merge 合併的）。

**守衛沒有擋錯。** 它問的是「這個分支的內容真的在 main 上嗎」，而 squash 之後那個
答案在 git 拓撲上確實是「不知道」。修法不是放寬它，是**補一條在 squash 之後仍能回答
同一個問題的證明**——見 `prove_content_in_main()`，該函式的 docstring 逐條寫明它證明
了什麼、比祖先關係弱在哪、以及**在什麼情況下會誤放行**。

兩條判準是 **OR**：先試祖先（強），不成立才試內容吸收（弱一級）。守衛其餘九項前提
與它們之間的 AND 關係**完全不動**——放寬的風險全部集中在這一條 disjunct 上，且它
落在 `MergeProof.kind` 這個具名欄位裡，報告看得出是哪一條放行的。
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Literal, Mapping, Protocol, Sequence

from .commands.assign_cmd import TERMINAL_STATUSES
from .registry import TasksMdRegistry
from .resources import try_parse_block

# ---------------------------------------------------------------------------
# 權威來源錨點
# ---------------------------------------------------------------------------

AUTHORITY_PATH = "templates/worktree-lifecycle.md"
AUTHORITY_ANCHOR = "第 11 行（第 5 點）的七步結案清單"

StepRole = Literal["precondition", "effect", "subsequent_obligation"]

#: 七步清單中每一步扮演的角色。**內容不在此重述**，只記角色。
STEP_ROLES: Mapping[int, StepRole] = {
    1: "precondition",
    2: "precondition",
    3: "precondition",
    4: "effect",
    5: "subsequent_obligation",
    6: "subsequent_obligation",
    7: "subsequent_obligation",
}

PRECONDITION_STEPS: tuple[int, ...] = (1, 2, 3)
EFFECT_STEP: int = 4
SUBSEQUENT_OBLIGATION_STEPS: tuple[int, ...] = (5, 6, 7)

#: 第 2 步之內的破壞性動作順序，沿用權威清單（先離開 worktree 屬前提檢查
#: ``not_self_cwd``，不是本模組能代替別的 process 執行的動作）。
DESTRUCTIVE_ORDER: tuple[str, ...] = (
    "remove_worktree",
    "delete_local_branch",
    "delete_remote_branch",
)

Trigger = Literal["release", "reconcile"]


class CleanupGuardError(RuntimeError):
    """守衛本身被違反（例如有人試圖對 git 送出 --force）。"""


# ---------------------------------------------------------------------------
# git 執行入口：唯一出口，--force 在此被硬擋
# ---------------------------------------------------------------------------

#: 明確禁止的旗標。凡以 ``--force`` 起頭者一律擋，其餘逐字列舉。
_FORBIDDEN_EXACT = frozenset({"-f", "-D", "-M", "--delete-force"})
_FORBIDDEN_PREFIX = "--force"

#: **唯一**被放行的 ``--force*`` 形態：帶明確期望 SHA 的條件式刪除租約。
#:
#: 之所以只開這一個窄口，是因為它與其他 force 旗標**方向相反**：其他 force 的語意
#: 是「不管遠端現在是什麼都照做」，而這一個是「遠端不是我剛讀到的那個值就不要做」
#: ——它正是本模組原本缺的 compare-and-swap，不是繞過守衛的後門。
#:
#: 三個形狀要求，缺一不放行（每一個都對應一種會退化回無條件刪除的寫法）：
#:
#: 1. **必須有 ``=``**：裸的 ``--force-with-lease`` 是「拿本機 remote-tracking ref
#:    當期望值」——那份 ref 可能是幾小時前 fetch 的，正是本卡要消滅的 stale
#:    本機資訊。
#: 2. **必須是 refspec 全名**（``refs/heads/<branch>``）：短名不會被 git 認成
#:    lease 的目標，租約會靜默失效。
#: 3. **期望值必須是 40／64 碼 hex 且非全零**：全零＝「期望這個 ref 不存在」，
#:    對「刪除一條既有分支」而言是自相矛盾的期望，而且它會讓租約在分支已消失時
#:    通過——與 fail-closed 相反。
_LEASE_RE = re.compile(
    r"^--force-with-lease=refs/heads/(?P<ref>[^\s:~^?*\[\\]+)"
    r":(?P<expect>[0-9a-f]{40}|[0-9a-f]{64})$"
)


def is_conditional_delete_lease(arg: str) -> bool:
    """這個 argv 是不是**唯一被允許**的那種租約旗標。"""
    m = _LEASE_RE.match(arg)
    return m is not None and set(m.group("expect")) != {"0"}


def _forbid_force(args: Sequence[str]) -> None:
    for a in args:
        if is_conditional_delete_lease(a):
            continue
        if a in _FORBIDDEN_EXACT or a.startswith(_FORBIDDEN_PREFIX):
            raise CleanupGuardError(
                f"reconcile／release 路徑禁用強制旗標（收到 {a!r}）。"
                "需要強制的情境即為需要人判斷的定義——請人工處理，不要繞過守衛。"
            )


@dataclass(frozen=True)
class GitResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


GitRunner = Callable[[Path, Sequence[str]], GitResult]


def default_git_runner(cwd: Path, args: Sequence[str]) -> GitResult:
    """執行 git 並回傳**git 自己的** returncode。

    刻意不經 shell（無 ``shell=True``、無管線、無 ``tee``／``tail``）：一旦把 git 接
    進管線，``$?`` 就變成管線最後一段的結果，一個被 ``(stale info)`` 拒絕的 push 會
    看起來像成功。本 repo 已經因為這個形態出過一次事故（review 被拒卻照跑後續指令），
    所以判斷成敗的唯一依據是 `GitResult.returncode`，而它只可能來自 git 本身。
    """
    _forbid_force(args)
    proc = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False
    )
    return GitResult(proc.returncode, proc.stdout, proc.stderr)


def _run(runner: GitRunner, cwd: Path, args: Sequence[str]) -> GitResult:
    # 即使呼叫端換了 runner（測試常換），禁用旗標仍在此被擋一次，
    # 避免「換 runner 就繞過守衛」。
    _forbid_force(args)
    return runner(cwd, args)


# ---------------------------------------------------------------------------
# 佔用探測（非任何 shell 的 cwd）
# ---------------------------------------------------------------------------

OccupancyOutcome = Literal["free", "occupied", "unobservable"]
OccupancyProber = Callable[[Path], tuple[OccupancyOutcome, str]]


def lsof_cwd_prober(path: Path) -> tuple[OccupancyOutcome, str]:
    """以 ``lsof -d cwd`` 列出全機 process 的 cwd，判斷目標是否被佔用。

    探不到（沒有 lsof／輸出無法解析）一律回 ``unobservable``，由聚合層轉成拒絕。
    「觀測不到」不等於「沒人佔用」——把它當成 free 就是本卡要消滅的 fail-open。
    """
    try:
        proc = subprocess.run(
            ["lsof", "-w", "-d", "cwd", "-Fn"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return "unobservable", f"無法執行 lsof（{type(exc).__name__}）"
    cwds = [line[1:] for line in proc.stdout.splitlines() if line.startswith("n")]
    if not cwds:
        return "unobservable", "lsof 沒有回傳任何可解析的 cwd 行"
    target = path.resolve()
    for raw in cwds:
        try:
            candidate = Path(raw).resolve()
        except OSError:
            continue
        if candidate == target or target in candidate.parents:
            return "occupied", f"有 process 的 cwd 位於目標之內：{raw}"
    return "free", f"掃描 {len(cwds)} 個 process cwd，無一位於目標之內"


# ---------------------------------------------------------------------------
# 目標與檢查結果
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CleanupTarget:
    repo_root: Path
    card_id: str
    branch: str
    worktree_path: Path | None
    remote: str = "origin"
    main_ref: str = "main"


CheckOutcome = Literal["pass", "fail", "unobservable"]
GuardMode = Literal["proceed", "detect_only"]


@dataclass(frozen=True)
class GuardCheck:
    check_id: str
    outcome: CheckOutcome
    detail: str
    step_ref: int  # 對應權威清單第幾步

    @property
    def blocking(self) -> bool:
        return self.outcome != "pass"


#: 全部前提，逐條列舉（卡面驗收第 1 條）。順序即回報順序。
CHECK_IDS: tuple[str, ...] = (
    "merge_verified_local",
    "merge_verified_remote",
    "no_uncommitted_changes",
    "no_stash",
    "no_locked_worktree",
    "not_self_cwd",
    "not_occupied_by_process",
    "not_primary_worktree",
    "no_foreign_active_lease",
    "resources_released",
)

CHECK_STEP_REF: Mapping[str, int] = {
    "merge_verified_local": 1,
    "merge_verified_remote": 1,
    "no_uncommitted_changes": 2,
    "no_stash": 2,
    "no_locked_worktree": 2,
    "not_self_cwd": 2,
    "not_occupied_by_process": 2,
    "not_primary_worktree": 2,
    "no_foreign_active_lease": 2,
    "resources_released": 3,
}


def aggregate_mode(outcomes: Sequence[CheckOutcome]) -> GuardMode:
    """全函數：只有全部 ``pass`` 才 proceed；``fail`` 與 ``unobservable`` 同等阻擋。

    刻意不留「其餘」分支——三值輸入的每一種都落在且僅落在一格。
    """
    return "proceed" if all(o == "pass" for o in outcomes) else "detect_only"


@dataclass(frozen=True)
class GuardDecision:
    mode: GuardMode
    checks: tuple[GuardCheck, ...]

    @property
    def blocking(self) -> tuple[GuardCheck, ...]:
        return tuple(c for c in self.checks if c.blocking)

    @property
    def reasons(self) -> tuple[str, ...]:
        return tuple(f"[{c.check_id}] {c.detail}" for c in self.blocking)


# ---------------------------------------------------------------------------
# worktree porcelain：只多讀一個 locked 位
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WorktreeRecord:
    path: str
    branch: str | None
    locked: bool
    lock_reason: str
    prunable: bool
    is_primary: bool


def parse_worktree_records(text: str) -> list[WorktreeRecord]:
    """解析 ``git worktree list --porcelain``，**額外保留 ``locked``**。

    `git_ops.parse_worktree_porcelain` 是既有權威解析器，但它的 `WorktreeEntry`
    不暴露 locked（doctor 用不到）。`git_ops.py` 不在本卡資源宣告內，因此不改它，
    改在此提供一個只多讀一個位元的解析器；
    `test_cleanup.py::test_worktree_parsers_agree` 對同一份輸入比對兩者的 path／
    branch，確保兩份解析不會各自漂移。
    """
    records: list[WorktreeRecord] = []
    current: dict[str, str] = {}
    first = True

    def flush() -> None:
        nonlocal first
        if not current:
            return
        branch_ref = current.get("branch")
        records.append(
            WorktreeRecord(
                path=current["worktree"],
                branch=branch_ref.removeprefix("refs/heads/") if branch_ref else None,
                locked="locked" in current,
                lock_reason=current.get("locked", "") if current.get("locked") != "true" else "",
                prunable="prunable" in current,
                is_primary=first,
            )
        )
        first = False

    for line in text.splitlines():
        if not line.strip():
            flush()
            current = {}
            continue
        parts = line.split(" ", 1)
        current[parts[0]] = parts[1] if len(parts) > 1 else "true"
    flush()
    return records


_STASH_BRANCH_RE = re.compile(r"^(?:WIP on|On) (?P<branch>[^:]+):")


# ---------------------------------------------------------------------------
# 逐項前提檢查
# ---------------------------------------------------------------------------


#: 「內容已在 main」的證明種類。**這是本模組唯一被放寬的那條軸**，因此它是具名
#: 欄位而不是一個布林：任何一次放行都必須說得出是哪一種證明放的行。
#:
#: - ``ancestor``：分支 tip 是 main 的祖先。**最強**：分支上每一筆 commit（含中間
#:   狀態）都在 main 的歷史裡，刪掉分支之後全都還原得回來。
#: - ``content_absorbed``：tip 不在 main 歷史裡，但**分支改動過的每一個路徑，main 上
#:   的內容都已與 tip 逐位元相同**。squash 之後成立的就是這一條。
#: - ``diverged``：分支上有 main 沒有的內容。**這是「別刪」。**
#: - ``unobservable``：判不出來。與 `diverged` 同樣阻擋（`aggregate_mode` 三值語意）。
MergeProofKind = Literal["ancestor", "content_absorbed", "diverged", "unobservable"]

#: `MergeProofKind` → `CheckOutcome`。兩種證明都放行，其餘一律擋。
_PROOF_OUTCOME: Mapping[MergeProofKind, CheckOutcome] = {
    "ancestor": "pass",
    "content_absorbed": "pass",
    "diverged": "fail",
    "unobservable": "unobservable",
}


@dataclass(frozen=True)
class MergeProof:
    kind: MergeProofKind
    detail: str

    @property
    def outcome(self) -> CheckOutcome:
        return _PROOF_OUTCOME[self.kind]


def _changed_paths(
    runner: GitRunner, repo_root: Path, a: str, b: str
) -> frozenset[str] | None:
    """``a`` 與 ``b`` 之間有差異的路徑集合；讀不到回 ``None``（呼叫端一律降 unobservable）。

    ``--no-renames`` **是正確性所需**，不是風格。開啟改名偵測時，一次改名只回報新路徑，
    舊路徑（＝被刪掉的那個）不會進入 A，而**刪除正是最不能漏的那種分歧**。實測（分支把
    ``keep.txt`` 改名為 ``moved.txt``；main 另外加了同內容的 ``moved.txt`` 但 ``keep.txt``
    仍在）：

        --find-renames → A={moved.txt}            B={keep.txt}  交集=∅   → 誤放行
        --no-renames   → A={keep.txt, moved.txt}  B={keep.txt}  交集={keep.txt} → 擋下

    ``-z`` 則是防禦性的，**不是**這裡的正確性關鍵：兩次 diff 跑在同一個 repo、同一份
    ``core.quotePath`` 設定下，就算被轉義也會是兩邊一致地轉義，交集不受影響。用 ``-z``
    的理由是拿到的是原始路徑位元組、不必依賴「兩邊轉義方式必然相同」這個前提，順帶
    免除以換行切分的疑慮。
    """
    res = _run(runner, repo_root, ["diff", "--name-only", "--no-renames", "-z", a, b])
    if not res.ok:
        return None
    return frozenset(p for p in res.stdout.split("\0") if p)


def prove_content_in_main(
    runner: GitRunner, repo_root: Path, tip: str, main_ref: str
) -> MergeProof:
    """裁定「``tip`` 的內容是否已經在 ``main_ref`` 上」，並**具名回報是哪一種證明**。

    ## 判準本身

    1. **祖先關係**（`merge-base --is-ancestor`）——沿用 WF-CLEANUP-GUARD1 原判準，
       先試，成立即回 ``ancestor``。這條沒有被動過。
    2. **內容吸收**——令 ``base = merge-base(tip, main)``：

           A = 分支改動過的路徑 = paths(diff base tip)
           B = 與 main 仍有差異的路徑 = paths(diff main tip)
           內容已吸收  ⟺  A ∩ B = ∅

       白話：**分支動過的每一個路徑，main 上的內容都已經與分支 tip 逐位元相同。**
       不在 A 的路徑無關緊要——分支沒碰過它們，分支上是 base 的舊內容，main 之後怎麼
       改都不是分支的貢獻。

    ## 它證明了什麼（以及沒證明什麼）

    **證明**：分支 tip 這個快照所帶的檔案內容，main 上一份不缺。以「刪掉分支會不會
    毀掉已提交的檔案內容」而論，答案是不會。

    **沒證明**：分支的 commit 物件本身在 main 上。squash 之後它們**確實不在**——那正
    是 `ROADMAP §3.5` 已經承認並接受的代價（「被審 SHA 不會出現在 main 的歷史上」）。

    ## ⚠️ 它比祖先關係弱在哪（不掩飾）

    弱在**只看 tip 這一個快照**。`ancestor` 保住分支上每一個中間 commit；
    ``content_absorbed`` 只保住 tip。因此：

    - **中間 commit 才有的內容會永久消失**：某檔案在分支第 1 個 commit 新增、第 3 個
      commit 又刪掉，tip 沒有它、main 也沒有它（squash 只帶 tip 的樹），刪掉分支之後
      就再也拿不回來。⚠️ 這個損失**是 squash 本身造成的、不是本判準造成的**——main
      無論如何都收不到那份內容；本判準的責任在於它讓「刪除」這個不可逆動作得以發生。
    - **commit 訊息、作者、分支上的 SHA 一併消失**。同上，squash 已經放棄它們。

    ## ⚠️ 它會在什麼情況下誤放行

    1. **淨零分支**：分支有 commit，但相對 base 淨改動為零（做完又自己 revert 回去）。
       此時 A = ∅，交集空，回 ``content_absorbed`` 放行——**而祖先關係會拒絕它**。
       這是本判準相對舊判準最清楚的一次放寬，且與 squash 無關。損失是「那次嘗試的
       commit 紀錄」；檔案內容零損失。
    2. **內容撞號**：另一張卡（或另一條路徑）把一模一樣的內容送上 main，本分支其實
       從未被合併，但 A ∩ B = ∅ 成立。此時檔案內容仍然一份不缺在 main 上，損失同 1。
    3. **繼承自舊判準的邊界**：本函式與 `merge-base --is-ancestor` 一樣，把 ``main_ref``
       指到的東西**當成真的 main**。main 被改寫過（force push、base 被重寫）時，兩條
       判準會一起失去意義——這不是新增的破口，是原本就在的那一個。

    **不會誤放行的**（沙箱矩陣逐一取證，見 `test_cleanup.py` 的判準矩陣）：完全未合併、
    squash 之後分支又推了新提交、squash 之後 main 又 revert 掉、分支刪檔而 main 未刪、
    同檔衝突。這五種全部落在 ``diverged``。
    """
    if _run(runner, repo_root, ["merge-base", "--is-ancestor", tip, main_ref]).ok:
        return MergeProof(
            "ancestor", f"{tip} 已是 {main_ref} 的祖先（分支上每一筆 commit 都在 main 歷史內）"
        )

    base_res = _run(runner, repo_root, ["merge-base", tip, main_ref])
    if not base_res.ok or not base_res.stdout.strip():
        return MergeProof(
            "unobservable",
            f"{tip} 與 {main_ref} 找不到共同祖先（{base_res.stderr.strip() or '無錯誤訊息'}）；"
            "無共同基準即無法判斷內容是否已吸收，不放行",
        )
    base = base_res.stdout.split()[0]

    touched = _changed_paths(runner, repo_root, base, tip)
    if touched is None:
        return MergeProof("unobservable", f"讀不到 {base[:12]}..{tip} 的改動路徑，無法判斷")
    if not touched:
        return MergeProof(
            "content_absorbed",
            f"{tip} 相對共同祖先 {base[:12]} 淨改動為零（分支上的 commit 互相抵銷）；"
            "無任何檔案內容可毀。⚠️ 祖先關係會拒絕這種分支，本判準放行——"
            "損失的是那次嘗試的 commit 紀錄，不是檔案內容",
        )

    differing = _changed_paths(runner, repo_root, main_ref, tip)
    if differing is None:
        return MergeProof("unobservable", f"讀不到 {main_ref} 與 {tip} 的差異路徑，無法判斷")

    unmatched = sorted(touched & differing)
    if unmatched:
        shown = ", ".join(unmatched[:5])
        return MergeProof(
            "diverged",
            f"{tip} 改動過的 {len(touched)} 個路徑中，有 {len(unmatched)} 個在 {main_ref} 上"
            f"的內容與分支不同：{shown}"
            f"{' …' if len(unmatched) > 5 else ''}；"
            "這些內容不在 main 上，刪掉分支就沒了",
        )
    return MergeProof(
        "content_absorbed",
        f"{tip} 相對共同祖先 {base[:12]} 改動的 {len(touched)} 個路徑，"
        f"在 {main_ref} 上的內容已與分支 tip 逐位元相同（squash 合併後的形狀）；"
        "⚠️ 分支的 commit 物件本身不在 main 歷史內——squash 已放棄它們（ROADMAP §3.5）",
    )


def _check_merge_local(target: CleanupTarget, runner: GitRunner) -> GuardCheck:
    tip = _run(runner, target.repo_root, ["rev-parse", "--verify", "--quiet", target.branch])
    if not tip.ok or not tip.stdout.strip():
        return GuardCheck(
            "merge_verified_local", "pass",
            f"本地分支 {target.branch!r} 不存在（已刪或從未建立），無可刪對象", 1,
        )
    proof = prove_content_in_main(runner, target.repo_root, target.branch, target.main_ref)
    return GuardCheck(
        "merge_verified_local", proof.outcome,
        f"本地 {target.branch}／證明={proof.kind}：{proof.detail}", 1,
    )


def _read_remote_heads(
    target: CleanupTarget, runner: GitRunner
) -> tuple[dict[str, str] | None, str]:
    """一次 ls-remote 同時取回待刪分支與 main 的**當下** SHA。

    兩端取自同一次觀測，避免「分支讀一次、main 再讀一次」之間又開一個窗。
    """
    ls = _run(runner, target.repo_root,
              ["ls-remote", "--heads", target.remote, target.branch, target.main_ref])
    if not ls.ok:
        return None, ls.stderr.strip() or "無錯誤訊息"
    heads: dict[str, str] = {}
    for line in ls.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            heads[parts[1].removeprefix("refs/heads/")] = parts[0]
    return heads, ""


def _commit_observable(target: CleanupTarget, runner: GitRunner, sha: str) -> bool:
    """該 commit object 在**本地物件庫**看得見嗎。

    看不見＝這是本機從未見過的提交（例如別人剛推上去的新工作）。本守衛不代為
    fetch，也拒絕對看不見的東西下祖先判斷——「查不到」不是「沒問題」。
    """
    return _run(runner, target.repo_root, ["cat-file", "-e", f"{sha}^{{commit}}"]).ok


def _check_merge_remote(target: CleanupTarget, runner: GitRunner) -> GuardCheck:
    heads, err = _read_remote_heads(target, runner)
    if heads is None:
        return GuardCheck("merge_verified_remote", "unobservable",
                          f"ls-remote 失敗（{err}），"
                          "無法驗證遠端分支是否已併入", 1)
    branch_sha = heads.get(target.branch)
    if branch_sha is None:
        return GuardCheck("merge_verified_remote", "pass",
                          f"遠端 {target.remote} 無 {target.branch!r}，無可刪對象", 1)
    main_sha = heads.get(target.main_ref)
    if main_sha is None:
        return GuardCheck("merge_verified_remote", "unobservable",
                          f"遠端 {target.remote} 讀不到 {target.main_ref}，無法比對祖先", 1)
    for sha in (branch_sha, main_sha):
        if not _commit_observable(target, runner, sha):
            return GuardCheck("merge_verified_remote", "unobservable",
                              f"遠端 commit {sha[:12]} 不在本地物件庫，"
                              "未 fetch 前無法驗證祖先關係（本守衛不代為 fetch）", 1)
    proof = prove_content_in_main(runner, target.repo_root, branch_sha, main_sha)
    return GuardCheck(
        "merge_verified_remote", proof.outcome,
        f"遠端 {target.branch}／證明={proof.kind}：{proof.detail}", 1,
    )


def _check_uncommitted(target: CleanupTarget, runner: GitRunner) -> GuardCheck:
    if target.worktree_path is None or not target.worktree_path.exists():
        return GuardCheck("no_uncommitted_changes", "pass",
                          "worktree 不存在於磁碟，無工作內容可毀", 2)
    res = _run(runner, target.worktree_path, ["status", "--porcelain"])
    if not res.ok:
        return GuardCheck("no_uncommitted_changes", "unobservable",
                          f"git status 失敗：{res.stderr.strip()}", 2)
    dirty = [ln for ln in res.stdout.splitlines() if ln.strip()]
    if dirty:
        return GuardCheck("no_uncommitted_changes", "fail",
                          f"有 {len(dirty)} 筆未提交變更／未追蹤檔："
                          f"{', '.join(ln.strip() for ln in dirty[:5])}", 2)
    return GuardCheck("no_uncommitted_changes", "pass", "工作樹乾淨", 2)


def _check_stash(target: CleanupTarget, runner: GitRunner) -> GuardCheck:
    res = _run(runner, target.repo_root, ["stash", "list", "--format=%gd%x09%gs"])
    if not res.ok:
        return GuardCheck("no_stash", "unobservable",
                          f"git stash list 失敗：{res.stderr.strip()}", 2)
    hits: list[str] = []
    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        ref, _, subject = line.partition("\t")
        match = _STASH_BRANCH_RE.match(subject.strip())
        if match is None:
            # 歸屬不明的 stash 一律擋：無法證明它不屬於待刪分支。
            return GuardCheck("no_stash", "unobservable",
                              f"stash {ref} 的訊息無法解析出所屬分支：{subject.strip()!r}", 2)
        if match.group("branch").strip() == target.branch:
            hits.append(ref)
    if hits:
        return GuardCheck("no_stash", "fail",
                          f"{target.branch} 上仍有 stash：{', '.join(hits)}", 2)
    return GuardCheck("no_stash", "pass", f"{target.branch} 上無 stash", 2)


def _worktree_records(target: CleanupTarget, runner: GitRunner) -> list[WorktreeRecord] | None:
    res = _run(runner, target.repo_root, ["worktree", "list", "--porcelain"])
    if not res.ok:
        return None
    return parse_worktree_records(res.stdout)


def _check_locked(records: list[WorktreeRecord] | None, target: CleanupTarget) -> GuardCheck:
    if target.worktree_path is None or not target.worktree_path.exists():
        return GuardCheck("no_locked_worktree", "pass", "worktree 不存在於磁碟", 2)
    if records is None:
        return GuardCheck("no_locked_worktree", "unobservable",
                          "git worktree list 失敗，無法判斷是否 locked", 2)
    resolved = target.worktree_path.resolve()
    for rec in records:
        if Path(rec.path).resolve() == resolved:
            if rec.locked:
                return GuardCheck("no_locked_worktree", "fail",
                                  f"worktree 被 lock（{rec.lock_reason or '未附原因'}）", 2)
            return GuardCheck("no_locked_worktree", "pass", "worktree 未被 lock", 2)
    return GuardCheck("no_locked_worktree", "unobservable",
                      f"路徑存在但不在 git worktree list 內：{target.worktree_path}", 2)


def _check_self_cwd(target: CleanupTarget) -> GuardCheck:
    if target.worktree_path is None:
        return GuardCheck("not_self_cwd", "pass", "無 worktree 目標", 2)
    try:
        cwd = Path.cwd().resolve()
    except OSError as exc:
        return GuardCheck("not_self_cwd", "unobservable", f"讀不到目前 cwd：{exc}", 2)
    target_path = target.worktree_path.resolve()
    if cwd == target_path or target_path in cwd.parents:
        return GuardCheck("not_self_cwd", "fail",
                          "目前 process 的 cwd 位於待刪 worktree 之內"
                          "（權威清單：禁止在 worktree 內移除自身目錄）", 2)
    return GuardCheck("not_self_cwd", "pass", "本 process 的 cwd 不在待刪 worktree 內", 2)


def _check_occupied(target: CleanupTarget, prober: OccupancyProber) -> GuardCheck:
    if target.worktree_path is None or not target.worktree_path.exists():
        return GuardCheck("not_occupied_by_process", "pass", "worktree 不存在於磁碟", 2)
    outcome, detail = prober(target.worktree_path)
    mapped: CheckOutcome = {
        "free": "pass", "occupied": "fail", "unobservable": "unobservable",
    }[outcome]
    return GuardCheck("not_occupied_by_process", mapped, detail, 2)


def _check_primary(records: list[WorktreeRecord] | None, target: CleanupTarget) -> GuardCheck:
    if target.worktree_path is None:
        return GuardCheck("not_primary_worktree", "pass", "無 worktree 目標", 2)
    resolved = target.worktree_path.resolve()
    if resolved == target.repo_root.resolve():
        return GuardCheck("not_primary_worktree", "fail", "目標即 repo 主工作樹", 2)
    if records is None:
        return GuardCheck("not_primary_worktree", "unobservable",
                          "git worktree list 失敗，無法確認目標非主工作樹", 2)
    for rec in records:
        if rec.is_primary and Path(rec.path).resolve() == resolved:
            return GuardCheck("not_primary_worktree", "fail", "目標是 git 回報的主工作樹", 2)
    return GuardCheck("not_primary_worktree", "pass", "目標非主工作樹", 2)


def _check_foreign_lease(target: CleanupTarget, registry: TasksMdRegistry | None) -> GuardCheck:
    """目標是否仍被**別張卡**的有效 lease 佔用。

    刻意排除目標卡自己：它的 lease 正是本轉換要釋放的東西，把它算進來會讓守衛
    永遠不可能通過（循環）。
    """
    if registry is None:
        return GuardCheck("no_foreign_active_lease", "unobservable",
                          "沒有卡註冊來源，無法判斷是否有其他卡持有有效 lease", 2)
    wt = target.worktree_path.resolve() if target.worktree_path else None
    for rc in registry.active:
        if rc.card_id == target.card_id:
            continue
        same_branch = bool(rc.branch) and rc.branch == target.branch
        same_worktree = False
        if wt is not None and rc.worktree_path:
            candidate = Path(rc.worktree_path)
            if not candidate.is_absolute():
                candidate = target.repo_root / candidate
            same_worktree = candidate.resolve() == wt
        if not (same_branch or same_worktree):
            continue
        if rc.owner_assigned() and (rc.delivery_status or "") not in TERMINAL_STATUSES:
            return GuardCheck("no_foreign_active_lease", "fail",
                              f"{rc.card_id}（owner={rc.owner}，交付狀態"
                              f"{rc.delivery_status}）仍持有同一分支／worktree 的 lease", 2)
    return GuardCheck("no_foreign_active_lease", "pass", "無其他活卡持有此分支／worktree", 2)


_AUTO_RELEASED_PREFIX = "file:"


def _check_resources(target: CleanupTarget, card_body: str | None) -> GuardCheck:
    """第 3 步：資源宣告釋放。

    權威清單：「merge 後該卡 `file:` 資源即釋放」。反面即本檢查的內容——``port:``／
    ``container:``／``db:`` 不因 merge 自動釋放，仍列在宣告內就是尚未釋放，須人工
    改宣告後才可收尾。
    """
    if card_body is None:
        return GuardCheck("resources_released", "unobservable",
                          "未提供卡 body，無法確認資源宣告已釋放", 3)
    decl = try_parse_block(card_body)
    if decl is None:
        return GuardCheck("resources_released", "unobservable",
                          "卡 body 的資源宣告區塊缺失或無法解析", 3)
    held = [r for r in decl.resources if not r.startswith(_AUTO_RELEASED_PREFIX)]
    if held:
        return GuardCheck("resources_released", "fail",
                          f"非 file: 資源不因 merge 自動釋放，仍在宣告內：{', '.join(held)}", 3)
    return GuardCheck("resources_released", "pass",
                      f"僅宣告 {len(decl.resources)} 項 file: 資源，merge 後即釋放", 3)


# ---------------------------------------------------------------------------
# 守衛聚合（注意：簽章裡沒有 trigger）
# ---------------------------------------------------------------------------


def evaluate_cleanup_guard(
    target: CleanupTarget,
    *,
    registry: TasksMdRegistry | None,
    card_body: str | None,
    runner: GitRunner | None = None,
    occupancy_prober: OccupancyProber | None = None,
) -> GuardDecision:
    """回傳 proceed／detect_only。**沒有 trigger 參數，也沒有 force 參數。**

    「reconcile 側前提不得放寬」不是靠紀律維持的：兩個觸發者要呼叫的是同一個函式，
    而它根本沒有可以區分兩者的輸入。（reconcile 目前尚未接線，見模組 docstring。）
    """
    runner = runner or default_git_runner
    prober = occupancy_prober or lsof_cwd_prober
    records = _worktree_records(target, runner)
    checks = (
        _check_merge_local(target, runner),
        _check_merge_remote(target, runner),
        _check_uncommitted(target, runner),
        _check_stash(target, runner),
        _check_locked(records, target),
        _check_self_cwd(target),
        _check_occupied(target, prober),
        _check_primary(records, target),
        _check_foreign_lease(target, registry),
        _check_resources(target, card_body),
    )
    return GuardDecision(mode=aggregate_mode([c.outcome for c in checks]), checks=checks)


# ---------------------------------------------------------------------------
# 遠端刪除前的二次確認（R1-001：守衛通過後、push --delete 之前的時間窗）
# ---------------------------------------------------------------------------

#: 二次確認的 check_id。刻意與前提 `merge_verified_remote` 分開命名——它們問的是
#: **不同時刻**的同一件事，混用會讓報告看不出「是在哪一刻被擋下的」。
RECHECK_REMOTE_ID = "remote_tip_still_merged"

#: 條件式刪除被遠端拒絕時的 check_id。與 `RECHECK_REMOTE_ID` 分開命名：後者是
#: 「我讀到的當下不該刪」，前者是「我讀到的當下可以刪，但送出的那一刻遠端已經不是
#: 那個值了」——兩者是不同時刻、不同機制擋下的，混用會讓報告看不出是哪一層接住的。
REMOTE_DELETE_CAS_ID = "remote_delete_lease_refused"

#: 對「該不該送出 push --delete」的三值裁決。``absent`` 不是放行也不是拒絕：
#: 遠端分支已不存在，本來就無事可做。
RemoteDeleteVerdict = Literal["delete", "absent", "refuse"]


@dataclass(frozen=True)
class RemoteDeleteDecision:
    """複驗的裁決，**連同它據以裁決的那個 tip 一起回傳**。

    `expected_tip` 不是附帶資訊而是裁決的一部分：它會原樣成為刪除指令的租約期望
    值，讓「檢查」與「刪除」共用同一個觀測值。把它丟掉再送一個無條件刪除，就是
    R2-001 被隔離實測打穿的那個版本。
    """

    verdict: RemoteDeleteVerdict
    check: GuardCheck
    #: 僅 ``verdict == "delete"`` 時非 None。
    expected_tip: str | None = None


def conditional_delete_args(target: CleanupTarget, expected_tip: str) -> list[str]:
    """組出**唯一**被允許的遠端刪除指令：帶租約的條件式刪除。

    本模組沒有第二條刪遠端分支的路——想刪就得先有一個期望 tip，而期望 tip 只能來自
    `recheck_remote_branch()`。租約字串在回傳前自我驗證一次；驗不過即丟
    `CleanupGuardError`，而不是靜靜地退回成無條件刪除（那正是要防的退化方向）。
    """
    lease = f"--force-with-lease=refs/heads/{target.branch}:{expected_tip}"
    if not is_conditional_delete_lease(lease):
        raise CleanupGuardError(
            f"組不出合法的條件式刪除租約（branch={target.branch!r}，"
            f"expected_tip={expected_tip!r}）。無條件刪除不是後備選項——"
            "組不出租約就不刪。"
        )
    return ["push", lease, target.remote, "--delete", target.branch]


def recheck_remote_branch(target: CleanupTarget, runner: GitRunner) -> RemoteDeleteDecision:
    """按下 `push --delete` 前的最後一次確認：tip 是誰、看得見嗎、還是 main 祖先嗎。

    **為什麼只重新確認「分支還在」不夠**：前提檢查與遠端刪除之間隔著本機 worktree
    移除與本地分支刪除。另一個 clone 在這段窗內把新提交推上同一條遠端分支後，分支
    當然還在——但它指的已經是別人的新工作，照刪就把那份工作刪掉了。這是本模組唯一
    真的會毀掉他人已提交內容的路徑，因此在此重讀三件事，缺一即拒：

    1. 遠端 branch 與 main 的**當下** SHA（同一次 ls-remote，兩端同一次觀測）；
    2. branch tip 的 commit object 在**本地物件庫可觀測**（觀測不到＝本機沒見過的
       新提交，守衛不代為 fetch，也不對看不見的東西做祖先判斷）；
    3. `prove_content_in_main(<tip>, <遠端 main tip>)` 仍給得出證明。**這裡與前提檢查
       用的是同一個函式**——複驗不得比前提寬，也不得比前提嚴，否則會出現「前提放行、
       複驗恆拒」（squash 之後原本就是這個形狀）或反過來的破口。

    回傳的 `GuardCheck` 走與前提檢查同一套三值語意，因此
    ``aggregate_mode([check.outcome])`` 在拒絕時就是 ``detect_only``——「驗不過或
    觀測不到就降純偵測、不刪」在這裡與前提檢查是同一條規則，不是另立的例外。

    **本函式只是讀，不構成保證**（R2-001）：它回傳 ``delete`` 到指令真的送出之間
    仍有一段（雖然很短的）時間。關掉那一段的不是這裡的任何一次讀，而是把讀到的
    `expected_tip` 交給 `conditional_delete_args()` 當租約——因此本函式**必須**把
    tip 一起回傳，呼叫端**必須**用它，兩者少一邊，這段窗就還開著。
    """
    heads, err = _read_remote_heads(target, runner)
    if heads is None:
        return RemoteDeleteDecision("refuse", GuardCheck(
            RECHECK_REMOTE_ID, "unobservable",
            f"刪除前重讀遠端失敗（{err}）；無法確認 tip 未變動，不刪", 2,
        ))
    branch_sha = heads.get(target.branch)
    if branch_sha is None:
        return RemoteDeleteDecision("absent", GuardCheck(
            RECHECK_REMOTE_ID, "pass",
            f"遠端 {target.remote} 已無 {target.branch!r}，無可刪對象", 2,
        ))
    main_sha = heads.get(target.main_ref)
    if main_sha is None:
        return RemoteDeleteDecision("refuse", GuardCheck(
            RECHECK_REMOTE_ID, "unobservable",
            f"刪除前讀不到遠端 {target.main_ref}，無法比對祖先，不刪", 2,
        ))
    if not _commit_observable(target, runner, branch_sha):
        return RemoteDeleteDecision("refuse", GuardCheck(
            RECHECK_REMOTE_ID, "unobservable",
            f"遠端 {target.branch} 的 tip 現在是 {branch_sha[:12]}，"
            "該 commit 不在本地物件庫——很可能是守衛通過後才被推上來的新提交；"
            "守衛不代為 fetch，也不刪自己沒看過的東西", 2,
        ))
    if not _commit_observable(target, runner, main_sha):
        return RemoteDeleteDecision("refuse", GuardCheck(
            RECHECK_REMOTE_ID, "unobservable",
            f"遠端 {target.main_ref} 的 tip {main_sha[:12]} 不在本地物件庫，"
            "無法驗證祖先關係，不刪", 2,
        ))
    proof = prove_content_in_main(runner, target.repo_root, branch_sha, main_sha)
    if proof.outcome != "pass":
        return RemoteDeleteDecision("refuse", GuardCheck(
            RECHECK_REMOTE_ID, proof.outcome,
            f"刪除前複驗：遠端 {target.branch} 的 tip 現在是 {branch_sha[:12]}，"
            f"對遠端 {target.main_ref}（{main_sha[:12]}）證不出內容已在 main"
            f"（{proof.kind}：{proof.detail}）；"
            "在 executor 內走到這一步代表前提檢查當時是通過的，"
            "也就是窗內有新提交進來——刪掉它會毀掉那份工作", 2,
        ))
    return RemoteDeleteDecision("delete", GuardCheck(
        RECHECK_REMOTE_ID, "pass",
        f"刪除前複驗：遠端 {target.branch} tip {branch_sha[:12]} 的內容仍證明在遠端 "
        f"{target.main_ref}（{main_sha[:12]}）上（證明={proof.kind}）；"
        f"該 tip 將原樣作為刪除租約的期望值", 2,
    ), expected_tip=branch_sha)


# ---------------------------------------------------------------------------
# 觀測式續作：狀態分類
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RemoteCardFacts:
    """狀態面事實。由呼叫端讀 GitHub 後傳入——本模組不持有任何本機「做到哪」紀錄。"""

    terminal_status_written: bool
    issue_open: bool


@dataclass(frozen=True)
class CloseoutObservation:
    worktree_present: bool
    local_branch_present: bool
    remote_branch_present: bool
    terminal_status_written: bool
    issue_open: bool

    @property
    def cleanup_done(self) -> bool:
        return not (
            self.worktree_present or self.local_branch_present or self.remote_branch_present
        )

    @property
    def effect_started(self) -> bool:
        return self.terminal_status_written or not self.issue_open

    @property
    def effect_done(self) -> bool:
        return self.terminal_status_written and not self.issue_open


IntermediateClass = Literal[
    "cleanup_in_progress",
    "cleanup_done_effect_pending",
    "effect_in_progress",
    "completed",
    "illegal_terminal_before_cleanup",
]

#: 合法的暫時中間態（卡面驗收：本機資源可部分完成；遠端僅限非終態）。
LEGAL_STATES: frozenset[str] = frozenset(
    {"cleanup_in_progress", "cleanup_done_effect_pending", "effect_in_progress", "completed"}
)


def classify_state(obs: CloseoutObservation) -> IntermediateClass:
    """全函數：五個可觀測布林的 32 種組合，每一種落在且僅落在一格，沒有「其餘」。

    `test_cleanup.py::test_classification_is_total` 窮舉 32 格驗證。
    """
    if not obs.cleanup_done:
        if obs.effect_started:
            return "illegal_terminal_before_cleanup"
        return "cleanup_in_progress"
    if obs.effect_done:
        return "completed"
    if obs.effect_started:
        return "effect_in_progress"
    return "cleanup_done_effect_pending"


def remaining_status_face_steps(obs: CloseoutObservation) -> tuple[int, ...]:
    """尚未完成、且會寫狀態面或動到資源的步驟。**不含第 5–7 步**。"""
    steps: list[int] = []
    if not obs.cleanup_done:
        steps.append(2)
    if not obs.effect_done:
        steps.append(EFFECT_STEP)
    return tuple(steps)


def observe(
    target: CleanupTarget,
    remote_facts: RemoteCardFacts,
    runner: GitRunner | None = None,
) -> CloseoutObservation:
    """純讀當下事實。不讀任何「上次做到哪」的本機紀錄——那種紀錄不存在。"""
    runner = runner or default_git_runner
    local = _run(runner, target.repo_root, ["rev-parse", "--verify", "--quiet", target.branch])
    ls = _run(runner, target.repo_root, ["ls-remote", "--heads", target.remote, target.branch])
    remote_present = bool(ls.ok and ls.stdout.strip())
    return CloseoutObservation(
        worktree_present=bool(target.worktree_path and target.worktree_path.exists()),
        local_branch_present=bool(local.ok and local.stdout.strip()),
        remote_branch_present=remote_present,
        terminal_status_written=remote_facts.terminal_status_written,
        issue_open=remote_facts.issue_open,
    )


# ---------------------------------------------------------------------------
# 效果寫入者（第 4 步）
# ---------------------------------------------------------------------------


class CloseoutEffectWriter(Protocol):
    """第 4 步的兩次狀態面寫入。順序沿用權威清單：先關 Issue，終態最後落地。"""

    def close_issue(self, target: CleanupTarget) -> None: ...

    def write_release_terminal(self, target: CleanupTarget) -> None: ...


def _noop_hook(_: str) -> None:
    return None


#: 本次 run 的結局。三者互斥：
#: - ``applied``：守衛放行，破壞性動作全部執行或（本來就不存在而）跳過；
#: - ``detect_only``：**什麼都沒動**（守衛擋下或狀態非法）；
#: - ``aborted``：守衛放行、部分動作已執行，但刪除前的二次確認拒絕了後續動作。
#:
#: ``aborted`` 不併入 ``detect_only``：一個已經移除了 worktree 的 run 自稱「純偵測」
#: 是不誠實的。呼叫端只需記住「只有 applied 代表轉換完成」。
CloseoutMode = Literal["applied", "detect_only", "aborted"]


@dataclass(frozen=True)
class CloseoutResult:
    mode: CloseoutMode
    decision: GuardDecision
    observation_before: CloseoutObservation
    observation_after: CloseoutObservation
    state_after: IntermediateClass
    actions_performed: tuple[str, ...]
    actions_skipped_absent: tuple[str, ...]
    remaining_status_face_steps: tuple[int, ...]
    outstanding_obligations: tuple[int, ...]
    blocking_reasons: tuple[str, ...]
    #: 刪除前二次確認拒絕、因而未執行的動作。
    actions_aborted: tuple[str, ...] = ()
    #: 二次確認的逐項結果（供報告與對帳；正常放行時也會有一筆 pass）。
    recheck_checks: tuple[GuardCheck, ...] = ()
    #: 觸發者標籤。**破壞性函式體 `_execute_closeout()` 造不出這個欄位的值**——它
    #: 收不到 `trigger`，構造 `CloseoutResult` 時一律留 `None`，由外層的
    #: `execute_closeout_transition()` 在**函式回傳之後**貼上（R4-002，見 §4.0）。
    #: 因此欄位型別是 `Trigger | None`：`None` 只在那一瞬間存在，任何呼叫端拿到的
    #: 結果都已貼好標籤。
    trigger: Trigger | None = None

    @property
    def legal_state(self) -> bool:
        return self.state_after in LEGAL_STATES


def execute_closeout_transition(
    target: CleanupTarget,
    *,
    trigger: Trigger,
    registry: TasksMdRegistry | None,
    card_body: str | None,
    remote_facts: RemoteCardFacts,
    effect_writer: CloseoutEffectWriter | None = None,
    runner: GitRunner | None = None,
    occupancy_prober: OccupancyProber | None = None,
    step_hook: Callable[[str], None] = _noop_hook,
) -> CloseoutResult:
    """收尾轉換的公開入口：**跑完破壞性轉換，然後貼上觸發者標籤**。

    本函式刻意只有一個運算式，而且它做的兩件事在時間上是分開的：先呼叫
    `_execute_closeout()`（真正的機械 executor，**簽章裡沒有 `trigger`**），拿到結果
    之後才 `replace(..., trigger=trigger)` 把標籤補上。

    **這個切法是 R4-002 的處置，不是排版偏好。** 先前 `trigger` 是 executor 自己的
    參數，於是「不得依觸發者分叉」只能靠一條 AST 規則維持；查核者用
    `locals()["trig" + "ger"]` 這種動態名稱在兩行內繞過了它。現在該值**根本不在破壞
    性函式體的 scope 裡**——不是參數、不是自由變數、也不是模組全域，動態名稱查表因此
    查不到東西。強度與其邊界見 `docs/WF_CLEANUP_GUARD1.md` §4.0；釘住它的是
    `test_the_destructive_body_cannot_name_the_trigger`（名稱面，窮舉 CPython 的名稱
    表）與 `test_the_destructive_body_frame_never_holds_a_trigger_value`（值面，抓改
    名夾帶）。本函式自身則由 `test_the_labelling_wrapper_is_pinned_to_call_and_relabel`
    以位元碼符號集合釘死——它只准認得 `_execute_closeout` 與 `replace` 兩個名字。
    """
    return replace(
        _execute_closeout(
            target,
            registry=registry,
            card_body=card_body,
            remote_facts=remote_facts,
            effect_writer=effect_writer,
            runner=runner,
            occupancy_prober=occupancy_prober,
            step_hook=step_hook,
        ),
        trigger=trigger,
    )


def _execute_closeout(
    target: CleanupTarget,
    *,
    registry: TasksMdRegistry | None,
    card_body: str | None,
    remote_facts: RemoteCardFacts,
    effect_writer: CloseoutEffectWriter | None = None,
    runner: GitRunner | None = None,
    occupancy_prober: OccupancyProber | None = None,
    step_hook: Callable[[str], None] = _noop_hook,
) -> CloseoutResult:
    """收尾轉換的**唯一機械 executor**（設計為兩個觸發者共用；目前只有 release 接線）。

    **本函式看不到是誰叫它的。** 觸發者標籤不是參數、不是自由變數、也沒有同名的模
    組全域，因此「依觸發者分叉」在這裡連寫都寫不出來——不必再靠一條「不准讀
    `trigger`」的規則去追各種寫法。它回傳的 `CloseoutResult.trigger` 恆為 `None`，
    由 `execute_closeout_transition()` 在回傳後貼上。

    `step_hook` 是故障注入點（正常執行為 no-op），讓測試能在每個步驟間隙中斷並驗證
    續作；`test_the_destructive_body_frame_never_holds_a_trigger_value` 也借它在每個
    間隙探本函式的 frame，確認沒有任何區域變數（含換名夾帶的）帶著觸發者的值。

    續作安全性靠兩件事，都不依賴本機紀錄：
    1. 每個破壞性動作**執行前重讀當下事實**，已不存在就跳過（不重複刪除）；
    2. 效果（第 4 步）只在清理確實完成後才發動（不產生非法半完成組合）。

    遠端分支這一步另外做**二次確認**（`recheck_remote_branch`）：不只確認「還在」，
    還要確認 tip 沒被別人換掉。拒絕時本次 run 以 ``aborted`` 收場，效果一併扣住，
    狀態停在合法的 `cleanup_in_progress`——重跑會重新觀測，人也還有機會介入。
    """
    runner = runner or default_git_runner
    before = observe(target, remote_facts, runner)

    if classify_state(before) == "illegal_terminal_before_cleanup":
        return CloseoutResult(
            mode="detect_only",
            decision=GuardDecision("detect_only", ()),
            observation_before=before, observation_after=before,
            state_after="illegal_terminal_before_cleanup",
            actions_performed=(), actions_skipped_absent=(),
            remaining_status_face_steps=remaining_status_face_steps(before),
            outstanding_obligations=SUBSEQUENT_OBLIGATION_STEPS,
            blocking_reasons=(
                "[illegal_state] 狀態面已寫終態／已關 Issue，但第 1–3 步尚未完成；"
                "這是非法組合，須人工判斷，守衛不代為修復",
            ),
        )

    decision = evaluate_cleanup_guard(
        target, registry=registry, card_body=card_body,
        runner=runner, occupancy_prober=occupancy_prober,
    )
    if decision.mode == "detect_only":
        return CloseoutResult(
            mode="detect_only", decision=decision,
            observation_before=before, observation_after=before,
            state_after=classify_state(before),
            actions_performed=(), actions_skipped_absent=(),
            remaining_status_face_steps=remaining_status_face_steps(before),
            outstanding_obligations=SUBSEQUENT_OBLIGATION_STEPS,
            blocking_reasons=decision.reasons,
        )

    performed: list[str] = []
    skipped: list[str] = []
    aborted: list[str] = []
    rechecks: list[GuardCheck] = []
    step_hook("guard_passed")

    for action in DESTRUCTIVE_ORDER:
        if action == "remove_worktree":
            present = bool(target.worktree_path and target.worktree_path.exists())
            if not present:
                skipped.append(action)
            else:
                res = _run(runner, target.repo_root,
                           ["worktree", "remove", str(target.worktree_path)])
                if not res.ok:
                    raise CleanupGuardError(
                        f"git worktree remove 失敗（不重試、不加 --force）：{res.stderr.strip()}"
                    )
                performed.append(action)
        elif action == "delete_local_branch":
            probe = _run(runner, target.repo_root,
                         ["rev-parse", "--verify", "--quiet", target.branch])
            if not (probe.ok and probe.stdout.strip()):
                skipped.append(action)
            else:
                # -d（安全刪除）而非 -D：未合併時 git 自己也會拒絕，形成第二道防線。
                res = _run(runner, target.repo_root, ["branch", "-d", target.branch])
                if not res.ok:
                    raise CleanupGuardError(
                        f"git branch -d 失敗（不升級為 -D）：{res.stderr.strip()}"
                    )
                performed.append(action)
        else:
            # R1-001：這裡不能只問「分支還在嗎」。守衛通過後、本機清理進行中的這段
            # 時間窗裡，別的 clone 可能已經把新提交推上同一條遠端分支——分支還在，
            # 但它指的已經是別人的新工作。因此重讀 tip、確認可觀測、重驗祖先。
            #
            # R2-001：但「重讀」到「送出」之間還有一段窗，而且它被隔離實測打穿過。
            # 因此複驗讀到的 tip 不是印出來就算，它會**原樣**成為刪除指令的租約
            # 期望值——檢查與刪除自此是同一個原子操作，不是先後兩件事。
            recheck = recheck_remote_branch(target, runner)
            rechecks.append(recheck.check)
            if recheck.verdict == "absent":
                skipped.append(action)
            elif recheck.verdict == "refuse":
                aborted.append(action)
                break
            elif recheck.expected_tip is None:
                # 到不了的分支；真的到了代表複驗的回傳被改壞了，寧可停也不要
                # 退回無條件刪除。
                raise CleanupGuardError(
                    "複驗回報可刪卻沒有帶回期望 tip，無法組出條件式刪除；不刪。"
                )
            else:
                res = _run(runner, target.repo_root,
                           conditional_delete_args(target, recheck.expected_tip))
                if not res.ok:
                    # 判成敗的依據是 git 自己的 returncode（`default_git_runner` 不經
                    # 管線），不是輸出長相。拒絕的處置與守衛其餘拒絕路徑同型：降
                    # aborted、效果扣住、留下具名理由——不重試，也不改用無條件刪除。
                    detail = (res.stderr.strip() or res.stdout.strip() or "無錯誤訊息")
                    rechecks.append(GuardCheck(
                        REMOTE_DELETE_CAS_ID, "fail",
                        f"條件式刪除被拒（租約期望 tip "
                        f"{recheck.expected_tip[:12]}，git returncode="
                        f"{res.returncode}）：{detail}；"
                        "遠端在複驗之後、刪除送出之前變動過，或遠端拒絕了本次刪除。"
                        "不重試、不降級為無條件刪除——請人工確認遠端現在是誰的工作", 2,
                    ))
                    aborted.append(action)
                    break
                performed.append(action)
        step_hook(f"after_{action}")

    if aborted:
        # 已執行的動作不回頭（也回不了頭），但**效果一律扣住**：狀態面不寫，
        # Issue 不關。停在合法的暫時態，交給下一次觀測式續作或人判斷。
        halted = observe(target, remote_facts, runner)
        return CloseoutResult(
            mode="aborted", decision=decision,
            observation_before=before, observation_after=halted,
            state_after=classify_state(halted),
            actions_performed=tuple(performed), actions_skipped_absent=tuple(skipped),
            actions_aborted=tuple(aborted), recheck_checks=tuple(rechecks),
            remaining_status_face_steps=remaining_status_face_steps(halted),
            outstanding_obligations=SUBSEQUENT_OBLIGATION_STEPS,
            blocking_reasons=tuple(
                f"[{c.check_id}] {c.detail}" for c in rechecks if c.blocking
            ),
        )

    mid = observe(target, remote_facts, runner)
    if effect_writer is not None and mid.cleanup_done:
        if mid.issue_open:
            effect_writer.close_issue(target)
            step_hook("after_close_issue")
        if not mid.terminal_status_written:
            effect_writer.write_release_terminal(target)
            step_hook("after_write_terminal")
        remote_facts = RemoteCardFacts(terminal_status_written=True, issue_open=False)

    after = observe(target, remote_facts, runner)
    return CloseoutResult(
        mode="applied", decision=decision,
        observation_before=before, observation_after=after,
        state_after=classify_state(after),
        actions_performed=tuple(performed), actions_skipped_absent=tuple(skipped),
        remaining_status_face_steps=remaining_status_face_steps(after),
        outstanding_obligations=SUBSEQUENT_OBLIGATION_STEPS,
        blocking_reasons=(),
        recheck_checks=tuple(rechecks),
    )


__all__ = [
    "AUTHORITY_ANCHOR",
    "AUTHORITY_PATH",
    "CHECK_IDS",
    "CHECK_STEP_REF",
    "DESTRUCTIVE_ORDER",
    "EFFECT_STEP",
    "LEGAL_STATES",
    "PRECONDITION_STEPS",
    "RECHECK_REMOTE_ID",
    "REMOTE_DELETE_CAS_ID",
    "STEP_ROLES",
    "SUBSEQUENT_OBLIGATION_STEPS",
    "CleanupGuardError",
    "CleanupTarget",
    "CloseoutEffectWriter",
    "CloseoutMode",
    "CloseoutObservation",
    "CloseoutResult",
    "GuardCheck",
    "GuardDecision",
    "GitResult",
    "MergeProof",
    "MergeProofKind",
    "RemoteCardFacts",
    "RemoteDeleteDecision",
    "WorktreeRecord",
    "aggregate_mode",
    "classify_state",
    "conditional_delete_args",
    "default_git_runner",
    "evaluate_cleanup_guard",
    "execute_closeout_transition",
    "is_conditional_delete_lease",
    "lsof_cwd_prober",
    "observe",
    "parse_worktree_records",
    "prove_content_in_main",
    "recheck_remote_branch",
    "remaining_status_face_steps",
]
