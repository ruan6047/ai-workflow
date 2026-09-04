"""``scripts/brief_backfill/`` 的額度歸因與 reset 反例（查核 R1-06）。

**為什麼放在 ``cli/tests/`` 而不是腳本旁邊**：``cli/pyproject.toml`` 的
``testpaths = ["tests"]`` 決定了 ``uv run pytest`` 只收 ``cli/tests/``，
CI（``.github/workflows/ci.yml``）跑的也是 ``working-directory: cli`` 的
``uv run --frozen pytest -q``。⇒ 放在 ``scripts/brief_backfill/`` 底下的測試**不會有
任何執行者**，等於沒寫。同 repo 已有兩個先例用同樣的做法測 ``scripts/*.py``：
``test_contract_tool_reconcile.py``、``test_canonical_citation_scan.py``。

⚠️ 本檔不連網：所有 GitHub 互動（``probe``／``resolve_project``／``list_items``）
都被替換掉，注入的取樣序列就是查核者 codex 逐字給的那組反例。

**變異檢驗的錨點**（改壞這兩處，對應測試必須轉紅）：

- 拿掉 ``quota.account_delta`` 的 ``resetAt`` 比對 → ``test_cross_window_forward_delta``
  與 ``test_reset_counterexample_negative_delta`` 轉紅（實測 2 failed / 17 passed）。
  ⭐ **兩者轉紅的份量不一樣**：``4990 → 7`` 那個反例的 ``usable is False`` 與
  ``delta is None`` 在變異後**仍然成立**（改由「倒退檢查」接住），它只在 ``reason``
  字串上轉紅——那是脆弱訊號。``10 → 50`` 跨視窗**正值**（非負、單調、量級合理）
  沒有任何算術性質抓得到，是唯一在**語意斷言**上把視窗比對釘死的樣本。
- 把 ``snapshot_population.main`` 的 ``return 3`` 改回 ``return 0``
  → ``test_reset_counterexample_end_to_end`` 轉紅。
- 把 ``cross_check`` 對「差值不可用」的判定改回 ``True``
  → ``test_cross_check_fails_when_delta_unusable`` 轉紅。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS = _REPO_ROOT / "scripts" / "brief_backfill"


def _load(name: str):
    """載入 ``scripts/brief_backfill/<name>.py``。

    ⚠️ 載入後把 ``sys.path`` 還原：那些腳本在 import 時會把自己的目錄插進
    ``sys.path``，留著會讓 ``census``／``guard``／``backfill`` 這些通用名字對
    **整個 pytest session** 可見。已經 import 進來的模組物件不受還原影響。
    """
    saved = list(sys.path)
    try:
        spec = importlib.util.spec_from_file_location(name, _SCRIPTS / f"{name}.py")
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = saved
    return mod


snapshot_population = _load("snapshot_population")
#: 刻意取腳本自己 import 到的那一個模組物件，⛔ 不另外載一份——
#: 另載一份會讓 monkeypatch 打在測試看得到、腳本看不到的地方（假陰性）。
quota = snapshot_population._quota_mod

W1 = "2026-08-26T19:56:10Z"
W2 = "2026-08-26T20:56:10Z"


def _s(used: int, reset: str, remaining: int | None = None) -> dict:
    return {
        "limit": 5000,
        "cost": 1,
        "used": used,
        "remaining": 5000 - used if remaining is None else remaining,
        "resetAt": reset,
    }


# ---------------------------------------------------------------- account_delta


def test_same_window_forward_is_usable():
    d = quota.account_delta(_s(4990, W1), _s(4997, W1))
    assert d.usable is True
    assert d.delta == 7


def test_reset_counterexample_negative_delta():
    """codex 逐字給的反例：``used 4990 → 7``。舊版由此算出 ``-4983`` 並照樣 rc=0。"""
    d = quota.account_delta(_s(4990, W1), _s(7, W2))
    assert d.usable is False
    assert d.delta is None
    assert "跨越 reset 視窗" in d.reason


def test_cross_window_forward_delta():
    """⭐ 跨視窗但差值**看起來完全正常**（+40，非負、量級合理）。

    這是「``used`` 單調遞增」那個錯誤前提最危險的形態：沒有任何算術性質抓得到它。
    拿掉 ``account_delta`` 的 ``resetAt`` 比對，本測試會判 usable/40 而轉紅。
    """
    d = quota.account_delta(_s(10, W1), _s(50, W2))
    assert d.usable is False
    assert d.delta is None


def test_same_window_backwards_is_unusable():
    d = quota.account_delta(_s(4990, W1), _s(7, W1))
    assert d.usable is False
    assert "倒退" in d.reason


def test_missing_reset_at_is_unusable():
    """取樣缺 ``resetAt`` ⇒ 判不了同不同視窗 ⇒ 不給數字。⛔ 驗不到 ≠ 通過。"""
    d = quota.account_delta({"used": 10}, _s(50, W1))
    assert d.usable is False
    assert d.delta is None


def test_control_returns_samples_with_reset_at(monkeypatch, capsys):
    """``control()`` 回整份取樣而非 ``int``：只回 ``used`` 會把同一個洞搬到呼叫端。"""
    seq = iter([_s(100, W1), _s(100, W1)])
    monkeypatch.setattr(quota, "probe", lambda: next(seq))
    a, b, ok = quota.control("（測試）")
    assert ok is True
    assert a["resetAt"] == W1 and b["resetAt"] == W1
    capsys.readouterr()


def test_control_fails_across_reset(monkeypatch, capsys):
    seq = iter([_s(4990, W1), _s(7, W2)])
    monkeypatch.setattr(quota, "probe", lambda: next(seq))
    _, _, ok = quota.control()
    assert ok is False
    assert "不可用" in capsys.readouterr().out


# ------------------------------------------------------------- inject_rate_limit


def test_injects_into_the_real_list_items_query():
    from wf_cli.project import _LIST_ITEMS_QUERY

    out = snapshot_population.inject_rate_limit(_LIST_ITEMS_QUERY)
    assert out is not None
    assert "rateLimit { cost used remaining resetAt }" in out
    # 注入點在最外層 selection set 開頭，而不是把原查詢包起來或替換掉。
    assert out.index("rateLimit") < out.index("node(id: $projectId)")
    assert "node(id: $projectId)" in out
    assert out.count("items(first: 50") == 1


def test_injection_never_smuggles_the_write_detection_keyword():
    """``tests/test_commands_mocked.py`` 以 ``"mutation" in query`` 判定寫入。

    注入字串若含該字，唯讀查詢會被記成寫入，把「拒絕路徑零寫入」那批斷言變成假紅。
    """
    assert "mutation" not in snapshot_population._RATE_LIMIT_SELECTION


@pytest.mark.parametrize(
    "query",
    [
        "mutation($id: ID!) { updateX(input: {id: $id}) { ok } }",
        "no braces at all",
        "",
    ],
)
def test_refuses_to_inject_when_shape_is_not_a_plain_query(query):
    """fail-closed：比對不上就放棄注入（那一支會落進未歸因），⛔ 不硬插。"""
    assert snapshot_population.inject_rate_limit(query) is None


def test_injects_into_anonymous_and_named_queries():
    assert snapshot_population.inject_rate_limit("{ viewer { login } }") is not None
    assert snapshot_population.inject_rate_limit("query Foo { viewer { login } }") is not None


# ------------------------------------------------------------------ cross_check


def test_cross_check_passes_when_account_covers_attributed():
    ok, verdict = snapshot_population.cross_check(5, quota.AccountDelta(True, 7, "同一視窗"))
    assert ok is True and "對帳通過" in verdict


def test_cross_check_fails_when_account_moved_less_than_self_report():
    ok, verdict = snapshot_population.cross_check(9, quota.AccountDelta(True, 5, "同一視窗"))
    assert ok is False and "對帳矛盾" in verdict


def test_cross_check_fails_when_delta_unusable():
    """⛔ 「檢驗不了」不得當成「通過」。"""
    ok, verdict = snapshot_population.cross_check(5, quota.AccountDelta(False, None, "跨越 reset 視窗"))
    assert ok is False and "無法對帳" in verdict


# ------------------------------------------------------- end-to-end（反例＋正控）


@dataclass(frozen=True)
class _FakeItem:
    item_id: str
    title: str


def _wire(monkeypatch, tmp_path: Path, probes: list[dict]) -> Path:
    """把整條網路路徑換掉，只留額度判定邏輯。回傳快照輸出路徑。"""
    seq = iter(probes)
    monkeypatch.setattr(quota, "probe", lambda: next(seq))

    class _Meta:
        id = "PVT_fake"
        url = "https://github.com/users/ruan6047/projects/4"

    def fake_resolve(runner, owner, number):
        # `gh project view` 走 run_json ⇒ 一支未歸因的 gh 呼叫。
        runner.gh_calls += 1
        return _Meta()

    def fake_list(runner, project):
        for _ in range(5):  # 5 頁，每頁自報 cost=1
            runner.gh_calls += 1
            runner.instrumented += 1
            runner.rate_samples.append({"cost": 1, "used": 0, "remaining": 0, "resetAt": W1})
        return [_FakeItem(f"i{n}", f"card {n}") for n in range(204)]

    monkeypatch.setattr(snapshot_population, "resolve_project", fake_resolve)
    monkeypatch.setattr(snapshot_population, "list_items", fake_list)
    out = tmp_path / "pop.json"
    monkeypatch.setattr(sys, "argv", ["snapshot_population.py", str(out)])
    return out


def test_reset_counterexample_end_to_end(monkeypatch, tmp_path, capsys):
    """⭐ codex 的注入原樣重現：前控制 100→100 通過／主量測 4990→7／後控制 7→7 通過。

    舊版對這組輸入印 ``graphql_cost=-4983``、``quota_control_ok=true``、``rc=0``。
    現版必須：不吐任何帳號層數字、對帳判不通過、rc=3；而**自報成本仍然成立**
    （5 點，來自逐回應的 cost，跟視窗無關）。
    """
    probes = [
        _s(100, W1), _s(100, W1),  # 前控制：通過
        _s(4990, W1),              # before
        _s(7, W2),                 # after ← 視窗翻了
        _s(7, W2), _s(7, W2),      # 後控制：通過
    ]
    out = _wire(monkeypatch, tmp_path, probes)

    assert snapshot_population.main() == 3

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["account_used_delta"] is None
    assert payload["account_delta_usable"] is False
    assert payload["quota_reconciled"] is False
    # 兩個控制組都通過 ⇒ ⛔ 光靠控制組抓不到這個反例，這正是 R1-06 的第二半。
    assert payload["quota_control_ok"] is True
    # 自報成本不受視窗影響，仍然是本腳本真正花掉的 5 點。
    assert payload["graphql_cost_attributed"] == 5
    assert payload["gh_calls_unattributed"] == 1
    assert payload["cost_attribution_complete"] is False
    # 快照本體仍完整寫出（rc=3 只針對額度帳）。
    assert payload["item_count"] == 204 and len(payload["items"]) == 204

    stdout = capsys.readouterr().out
    assert "-4983" not in stdout
    assert "不可用" in stdout


def test_same_window_run_reconciles_and_returns_zero(monkeypatch, tmp_path, capsys):
    """正控：同一視窗、帳號層 (+7) 蓋得住自報 (5) ⇒ 對帳通過、rc=0。"""
    probes = [
        _s(100, W1), _s(100, W1),
        _s(4990, W1),
        _s(4997, W1),
        _s(4997, W1), _s(4997, W1),
    ]
    out = _wire(monkeypatch, tmp_path, probes)

    assert snapshot_population.main() == 0

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["account_used_delta"] == 7
    assert payload["graphql_cost_attributed"] == 5
    assert payload["quota_reconciled"] is True
    assert "對帳通過" in capsys.readouterr().out


def test_account_delta_smaller_than_self_report_is_caught(monkeypatch, tmp_path, capsys):
    """帳號層只動 2 點、卻自報 5 點 ⇒ 前提被推翻，必須判紅而不是印出來就算。"""
    probes = [
        _s(100, W1), _s(100, W1),
        _s(4990, W1),
        _s(4992, W1),
        _s(4992, W1), _s(4992, W1),
    ]
    _wire(monkeypatch, tmp_path, probes)
    assert snapshot_population.main() == 3
    assert "對帳矛盾" in capsys.readouterr().out
