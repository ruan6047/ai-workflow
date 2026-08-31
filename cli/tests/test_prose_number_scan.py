# 規劃文書敘述數字掃描器的守衛測試（P1-38，R15 修訂）。
#
# 負控是本測試的核心：R14/R15 兩輪證明「掃描 0 命中」可以是假陰性。這裡分三層：
# (1) detector-escape suite——R15 裁決列出的五個漏報＋一個錯誤 class-c 逐一釘死；
# (2) ID_PATS 成對表——每一條剝除規則配（真識別子→不產列；identifier＋相鄰裸現況數
#     →必產列）一對，表長以不變量釘等於 len(ID_PATS)，新增 pattern 不配對即紅；
# (3) 白名單封閉——reason 只認 pm-conduct (b) 的兩類（字面釘死，⛔ 不讀 inventory
#     自宣告的集合自證），且每筆必有 line-specific rationale。
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "prose_number_scan.py"

_spec = importlib.util.spec_from_file_location("prose_number_scan", _SCRIPT)
assert _spec is not None and _spec.loader is not None
pns = importlib.util.module_from_spec(_spec)
sys.modules["prose_number_scan"] = pns
_spec.loader.exec_module(pns)


def _scan_text(tmp_path: Path, text: str, inventory=None) -> list[dict]:
    f = tmp_path / "probe.md"
    f.write_text(text + "\n", encoding="utf-8")
    return pns.scan_file(f, inventory=inventory, rel="probe.md")


def _classes(tmp_path, text):
    return [r["class"] for r in _scan_text(tmp_path, text)]


# ---- 基本負控（R14 反例形狀） ----

def test_negative_control_arabic_undated(tmp_path):
    assert _classes(tmp_path, "目前看板上有 42 張卡待處理。") == ["unclassified"]


def test_negative_control_chinese_numerals(tmp_path):
    assert _classes(tmp_path, "實測十二條 amend 中六條是可合併的。") == ["unclassified"]


def test_dated_line_classified_a(tmp_path):
    assert _classes(tmp_path, "2026-08-30 實測：看板上有 42 張卡。") == ["a"]


# ---- detector-escape suite（R15 裁決逐項） ----

def test_escape_inline_code_number(tmp_path):
    assert _classes(tmp_path, "目前有 `42` 張卡。") == ["unclassified"]


def test_escape_numeric_heading(tmp_path):
    assert _classes(tmp_path, "## 目前有 43 張卡") == ["unclassified"]


def test_escape_7_digit_decimal_not_sha(tmp_path):
    assert _classes(tmp_path, "目前有 1234567 張卡。") == ["unclassified"]


def test_escape_12_digit_decimal_not_hash(tmp_path):
    assert _classes(tmp_path, "目前有 123456789012 張卡。") == ["unclassified"]


def test_escape_chinese_measure_word_ren(tmp_path):
    assert _classes(tmp_path, "目前三人正在執行。") == ["unclassified"]


def test_escape_bare_json_is_not_artifact(tmp_path):
    # R15 反例：單獨 .json 路徑不構成 (c)
    assert _classes(tmp_path, "inventory.json 目前有 44 張卡。") == ["unclassified"]


# ---- fence 狀態機成對測試（R16 反例＋CommonMark 三規則） ----

def test_fence_four_backtick_outer_with_three_inner(tmp_path):
    # R16 反例：四反引號外層＋三反引號內文是合法 Markdown；close 後的裸數必轉紅
    text = "````markdown\n```\n````\n目前有 42 張卡。"
    assert _classes(tmp_path, text) == ["unclassified"]


def test_fence_shorter_closer_does_not_close(tmp_path):
    text = "````\n```\n目前有 42 張卡。"
    assert _classes(tmp_path, text) == []  # 仍在 fence 內


def test_fence_backtick_and_tilde_do_not_interclose(tmp_path):
    text = "```\n~~~\n目前有 42 張卡。"
    assert _classes(tmp_path, text) == []  # ~~~ 不關反引號 fence
    text2 = "~~~\n```\n目前有 42 張卡。"
    assert _classes(tmp_path, text2) == []  # ``` 不關波浪號 fence


def test_fence_info_string_line_is_not_closer(tmp_path):
    text = "```\n```python\n目前有 42 張卡。"
    assert _classes(tmp_path, text) == []  # 帶 info string 的行不是 closer


def test_fence_plain_block_still_excluded(tmp_path):
    text = "```\n目前有 42 張卡。\n```\n2026-08-30 有 7 張卡。"
    assert _classes(tmp_path, text) == ["a"]


def test_ordinal_heading_still_stripped(tmp_path):
    # 章節序號不是敘述數字；heading 其餘內容照掃
    assert _classes(tmp_path, "## 八 · 注意事項") == []
    assert _classes(tmp_path, "## 八 · 目前有 43 張卡") == ["unclassified"]


# ---- (c) artifact 訊號的正反面 ----

def test_artifact_measure_contract_is_c(tmp_path):
    assert _classes(tmp_path, "拒絕點全集 144 項開卡時 artifact 重量。") == ["c"]


def test_artifact_file_plus_hash_is_c(tmp_path):
    line = ("baseline-universe.json 54 個缺口，sha256="
            "c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68。")
    assert _classes(tmp_path, line) == ["c"]


def test_hash_alone_with_count_not_c(tmp_path):
    line = "指紋 a690e2008618bddf10ebe4937c7ce7 之外另有 42 張卡。"
    assert _classes(tmp_path, line) == ["unclassified"]


# ---- ID_PATS 成對表：真識別子剝除／identifier＋相鄰裸數必響 ----
# 每列 ＝ 一條 ID_PATS 的代表識別子行（行內無其他數字）。
# clean：該行不產列；adjacent：同行加「，另有 42 張卡」後 42 必 unclassified。
_ID_PAIR_TABLE = [
    "指向 deadbeefcafe0123 的物件",           # sha hex（含 a-f）
    "P1-38 延續",                              # P1-NN
    "§6.4.2 承接",                             # §數字節次
    "§三之二 指定句",                          # §中文節次
    "#177 的留言",                             # issue 號
    "issuecomment-5476075199 裁決",            # 留言 id
    "W2A 波卡",                                # W 識別子
    "R15 重審",                                # R 輪次
    "T4 級別",                                 # T 級別
    "L4 路由",                                 # L 路由
    "v1 schema 消費",                          # 版本
    "canonical-v1 序列化",                     # 具名版本
    "054_champion 遷移檔",                     # 遷移檔名
    "UUIDv5 命名",                             # UUID
    "sha-256 摘要",                            # hash 演算法名
    "128-bit 識別子",                          # 位元寬度
    "issues/177 路徑",                         # issue 路徑
    "PR #203 合併",                            # PR 號
    "Q4 問題",                                 # Q 編號
    "16:53 記錄",                              # 時刻
    "+08:00 時區",                             # 時區
    "版本 0.1.0 發佈",                         # semver
    "op b17f325c 落帳",                        # op id
    "WF-REDESIGN1 父卡",                       # 卡 ID
    "aiwf#165 的掃描",                         # repo#issue
    "cpbl#176 已關",                           # repo#issue
    "phase 1 dual reader",                     # phase
    "ruan6047 的帳號",                         # 帳號名
    "first:100 分頁",                          # GraphQL 參數
    "shasum -a 256 產出",                      # 指令
    "AC 1,1b 對照",                            # AC 引用
    "3. 執行後續動作",                         # 行首編號
    "| 7 | 內容 |",                            # 表格列號
    "- **3.** 項目",                           # 清單編號
    "[0-9]{3,} ?行 樣式",                      # regex 量詞
    "deleteProjectV2Item 執行",                # V2 API 名
    "見 doctor.py:502。",                      # file:line 引用
    "掃描步驟 A3 完成",                        # 步驟 id
    "條件 4 已填",                             # 條件節標
    "波 2 開工",                               # 波識別子
    "row 10 已刪",                             # 取代清單列
    "replacement_rows: [1, 3]",                # frontmatter 欄
    "spec_version: 3",                         # frontmatter 欄
    "rc=0 回傳",                               # 退出碼字面
    "WF_RESOURCE_WRITESET1 語意",              # 常數名
]


def test_id_pair_table_covers_every_pattern():
    # 不變量：每條 ID_PATS 恰有一列成對測試；新增 pattern 不配對即紅
    assert len(_ID_PAIR_TABLE) == len(pns.ID_PATS)


def test_id_patterns_clean_and_adjacent(tmp_path):
    failures = []
    for id_line in _ID_PAIR_TABLE:
        rows = _scan_text(tmp_path, id_line)
        if rows:
            failures.append(f"id 未剝除：{id_line} → {[r['tokens'] for r in rows]}")
        rows2 = _scan_text(tmp_path, id_line + "，另有 42 張卡。")
        if not any(r["class"] == "unclassified" and "42" in r["tokens"] for r in rows2):
            failures.append(f"相鄰量測被吃掉：{id_line}")
    assert failures == []


# ---- inventory 契約 ----

def _claim(token, occ, reason="design-closed-set", rationale="「樣例」＝測試用枚舉理由"):
    return {"token": token, "occurrence": occ, "reason": reason, "rationale": rationale}


def _entry(line, claims):
    key = pns._line_key(line)
    return {("probe.md", key): {"path": "probe.md", "line_sha1": key,
                                "excerpt": line[:20], "claims": claims}}


def test_inventory_pins_line_text(tmp_path):
    line = "信封固定為 8 欄，缺一即拒。"
    inv = _entry(line, [_claim("8", 0, rationale="「8 欄」＝信封欄位枚舉")])
    assert [r["class"] for r in _scan_text(tmp_path, line, inventory=inv)] == ["b"]
    rows2 = _scan_text(tmp_path, "信封固定為 9 欄，缺一即拒。", inventory=inv)
    assert [r["class"] for r in rows2] == ["unclassified"]


def test_claims_must_cover_every_token(tmp_path):
    # R16：行級單一 rationale 放行整列 tokens 被退回——漏 token 即紅
    line = "信封 8 欄共 3 類。"
    inv = _entry(line, [_claim("8", 0, rationale="「8 欄」＝信封欄位枚舉")])
    assert [r["class"] for r in _scan_text(tmp_path, line, inventory=inv)] == ["claims-mismatch"]


def test_claims_must_not_exceed_tokens(tmp_path):
    line = "信封固定為 8 欄，缺一即拒。"
    inv = _entry(line, [_claim("8", 0, rationale="「8 欄」＝枚舉"),
                        _claim("3", 1, rationale="幽靈 claim 佔位")])
    assert [r["class"] for r in _scan_text(tmp_path, line, inventory=inv)] == ["claims-mismatch"]


def test_repeated_token_needs_occurrence_bound_claims(tmp_path):
    # R17：multiset 只證數量——兩個 8 綁在同一 occurrence 即紅，⛔ 數量對就放行
    line = "共 8 份檔案，預期 8 全綠。"
    both_on_first = _entry(line, [
        _claim("8", 0, rationale="「8 份」＝檔案枚舉"),
        _claim("8", 0, "threshold-ruling", "「預期 8」＝oracle 期望值"),
    ])
    assert [r["class"] for r in _scan_text(tmp_path, line, inventory=both_on_first)] \
        == ["claims-mismatch"]
    bound = _entry(line, [
        _claim("8", 0, rationale="「8 份」＝檔案枚舉"),
        _claim("8", 1, "threshold-ruling", "「預期 8」＝oracle 期望值"),
    ])
    assert [r["class"] for r in _scan_text(tmp_path, line, inventory=bound)] == ["b"]


# ---- closed claim schema：主 scanner 自驗，⛔ 不倚賴 pytest 對當下檔案（R17） ----

def test_illegal_reason_is_fail_closed(tmp_path):
    line = "目前有 42 張卡。"
    inv = _entry(line, [_claim("42", 0, reason="environment-fact",
                               rationale="非法類別測試")])
    assert [r["class"] for r in _scan_text(tmp_path, line, inventory=inv)] == ["invalid-claims"]


def test_empty_rationale_is_fail_closed(tmp_path):
    line = "目前有 42 張卡。"
    inv = _entry(line, [_claim("42", 0, rationale="")])
    assert [r["class"] for r in _scan_text(tmp_path, line, inventory=inv)] == ["invalid-claims"]


def test_extra_claim_key_is_fail_closed(tmp_path):
    line = "目前有 42 張卡。"
    c = _claim("42", 0, rationale="「42 張」測試")
    c["note"] = "偷渡欄位"
    inv = _entry(line, [c])
    assert [r["class"] for r in _scan_text(tmp_path, line, inventory=inv)] == ["invalid-claims"]


def _fake_corpus(tmp_path, monkeypatch, text, entries):
    corpus = tmp_path / "corpus.md"
    corpus.write_text(text + "\n", encoding="utf-8")
    invp = tmp_path / "inv.json"
    invp.write_text(json.dumps({"_meta": {}, "entries": entries}, ensure_ascii=False),
                    encoding="utf-8")
    monkeypatch.setattr(pns, "INVENTORY_PATH", invp)
    monkeypatch.setattr(pns, "corpus_paths", lambda: [corpus])
    monkeypatch.setattr(pns, "REPO_ROOT", tmp_path)


def test_dead_entry_reported_without_crash(tmp_path, monkeypatch, capsys):
    # R17：dead-entry 路徑曾 KeyError 'reason'——新 schema 下必須可讀輸出且 rc=1
    _fake_corpus(tmp_path, monkeypatch, "2026-08-30 有 7 張卡。", [
        {"path": "corpus.md", "line_sha1": "0" * 40, "excerpt": "早已被改掉的行",
         "claims": [_claim("9", 0)]},
    ])
    rc = pns.main([])
    out = capsys.readouterr().out
    assert rc == 1 and "[dead-entry]" in out and "早已被改掉的行"[:8] in out


# ---- load 期 entry identity 驗證（R18：缺欄曾 class b／KeyError） ----

def _load_case(tmp_path, monkeypatch, capsys, entry):
    _fake_corpus(tmp_path, monkeypatch, "2026-08-30 有 7 張卡。", [entry])
    rc = pns.main([])
    return rc, capsys.readouterr().out


def _valid_load_entry():
    return {"path": "corpus.md", "line_sha1": "a" * 40, "excerpt": "樣例行",
            "claims": [_claim("9", 0)]}


def test_missing_excerpt_is_invalid_not_b(tmp_path, monkeypatch, capsys):
    e = _valid_load_entry(); del e["excerpt"]
    rc, out = _load_case(tmp_path, monkeypatch, capsys, e)
    assert rc == 1 and "[invalid-claims]" in out and "excerpt" in out


def test_missing_path_reported_not_keyerror(tmp_path, monkeypatch, capsys):
    e = _valid_load_entry(); del e["path"]
    rc, out = _load_case(tmp_path, monkeypatch, capsys, e)
    assert rc == 1 and "[invalid-claims]" in out


def test_missing_line_sha1_reported_not_keyerror(tmp_path, monkeypatch, capsys):
    e = _valid_load_entry(); del e["line_sha1"]
    rc, out = _load_case(tmp_path, monkeypatch, capsys, e)
    assert rc == 1 and "[invalid-claims]" in out


def test_wrong_sha1_type_is_invalid(tmp_path, monkeypatch, capsys):
    e = _valid_load_entry(); e["line_sha1"] = "not-a-sha"
    rc, out = _load_case(tmp_path, monkeypatch, capsys, e)
    assert rc == 1 and "40 位 hex" in out


def test_duplicate_identity_fails_closed(tmp_path, monkeypatch, capsys):
    _fake_corpus(tmp_path, monkeypatch, "2026-08-30 有 7 張卡。",
                 [_valid_load_entry(), _valid_load_entry()])
    rc = pns.main([])
    out = capsys.readouterr().out
    assert rc == 1 and "duplicate" in out


def test_json_mode_carries_mismatch_evidence(tmp_path, monkeypatch, capsys):
    # R17：--json 曾只吐兩個空清單——mismatch 證據與各項計數必須全數在 payload
    line = "信封 8 欄共 3 類。"
    _fake_corpus(tmp_path, monkeypatch, line, [
        {"path": "corpus.md", "line_sha1": pns._line_key(line), "excerpt": line[:20],
         "claims": [_claim("8", 0, rationale="「8 欄」＝枚舉")]},
    ])
    rc = pns.main(["--json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert payload["counts"]["claims_mismatch"] == 1
    assert payload["claims_mismatch"][0]["uncovered"], payload


def test_inventory_reasons_pinned_to_pm_conduct_b():
    # 字面釘死 pm-conduct (b) 兩類；⛔ 不以 inventory 自宣告的集合自證
    assert pns.ALLOWED_B_REASONS == frozenset({"threshold-ruling", "design-closed-set"})
    data = json.loads(pns.INVENTORY_PATH.read_text(encoding="utf-8"))
    bad = [c for e in data["entries"] for c in e["claims"]
           if c["reason"] not in pns.ALLOWED_B_REASONS]
    assert bad == []


def test_every_claim_carries_line_specific_rationale():
    data = json.loads(pns.INVENTORY_PATH.read_text(encoding="utf-8"))
    bad = [c for e in data["entries"] for c in e["claims"]
           if not c.get("rationale") or c["rationale"].strip() == c["reason"]
           or len(c["rationale"]) < 10]
    assert bad == []


def test_every_inventory_claim_is_occurrence_bound():
    data = json.loads(pns.INVENTORY_PATH.read_text(encoding="utf-8"))
    for e in data["entries"]:
        occs = sorted(c["occurrence"] for c in e["claims"])
        assert occs == list(range(len(occs))), e["excerpt"]


# ---- 語料與 CLI ----

def test_corpus_is_fully_classified():
    result = pns.scan_corpus()
    assert result["unclassified"] == [], [
        f'{r["path"]}:{r["line"]} {r["text"][:80]}' for r in result["unclassified"]
    ]
    assert result["dead_entries"] == [], [
        f'{e["path"]} {e.get("excerpt", "")[:60]}' for e in result["dead_entries"]
    ]
    assert result["uncovered_claims"] == [], result["uncovered_claims"][:5]
    assert result["extra_claims"] == [], result["extra_claims"][:5]


def test_cli_exit_code_red_on_unclassified(tmp_path):
    f = tmp_path / "probe.md"
    f.write_text("目前有 7 張卡。\n", encoding="utf-8")
    assert pns.main(["--file", str(f)]) == 1
    f.write_text("2026-08-30 有 7 張卡。\n", encoding="utf-8")
    assert pns.main(["--file", str(f)]) == 0
