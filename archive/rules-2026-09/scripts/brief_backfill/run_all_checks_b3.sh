#!/usr/bin/env bash
# 第三批（剩餘全部）交付的全部量測，一次跑完。
# ⛔ 不接管線截斷（`| tail` 會把 $? 換成 tail 的，本 repo 同族已犯三次）。
# 用法：run_all_checks_b3.sh <scratch_dir>
set -u
SD="$1"
CLI="$(cd "$(dirname "$0")/../../cli" && pwd)"
S="$(cd "$(dirname "$0")" && pwd)"
cd "$CLI" || exit 1

echo "############ 0. 回填後全母體快照（唯讀）############"
uv run python "$S/snapshot_population.py" "$SD/pop-b3-after.json"; echo "rc=$?"

echo; echo "############ 1. A1 母體四數字 ＋ V1 兩份具名清單（現場重算）############"
uv run python "$S/census.py" "$SD/pop-b3-after.json" --missing; echo "rc=$?"

echo; echo "############ 2. A10 三條價值論證（現場重算）############"
uv run python "$S/measure_a10.py" "$SD/pop-b3-after.json"; echo "rc=$?"

echo; echo "############ 3. V2 覆蓋率＋統計檢定（正式版簡介）############"
uv run python "$S/measure_b2.py" "$SD/pop-b3-after.json" "$SD/b3/b3_writable.txt" "" "第三批"; echo "rc=$?"

echo; echo "############ 4. V3 變異檢驗（摘要版覆寫 10 張，離線 override）############"
uv run python "$S/measure_b2.py" "$SD/pop-b3-after.json" "$SD/b3/v3-sample.txt" "$SD/b3/briefs-b3-summary.json" "V3摘要版10張"; echo "rc=$?"

echo; echo "############ 4b. V3 對照：同 10 張的正式版簡介 ############"
uv run python "$S/measure_b2.py" "$SD/pop-b3-after.json" "$SD/b3/v3-sample.txt" "" "V3同10張正式版"; echo "rc=$?"

echo; echo "############ 5. B 層零命中歸因（凍結 spec 檔為 GT 來源）############"
uv run python "$S/measure_v2_blayer.py" "$SD/pop-b3-after.json" "$SD/b3/rest_b.txt"; echo "rc=$?"

echo; echo "############ 6. V4 卡面不變量（逐張 before → after）############"
uv run python "$S/verify_invariants.py" "$SD/b3/run" "$SD/b3/briefs-b3.json"; echo "rc=$?"

echo; echo "############ 7. V5 注入負控的純函式那一半（守衛承重）############"
uv run python "$S/prove_guard_load_bearing.py" "$SD/b3/run/before/$(head -n 1 "$SD/b3/b3_writable.txt").md"; echo "rc=$?"
