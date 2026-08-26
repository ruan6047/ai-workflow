#!/usr/bin/env bash
# 先導批交付的全部量測，一次跑完。⛔ 不接管線截斷（| tail 會把 rc 換成 tail 的）。
# 用法：run_all_checks.sh <scratch_dir>
set -u
SD="$1"
CLI="$(cd "$(dirname "$0")/../../cli" && pwd)"
S="$(cd "$(dirname "$0")" && pwd)"
cd "$CLI" || exit 1

echo "############ 0. 回填後全母體快照（唯讀）############"
uv run python "$S/snapshot_population.py" "$SD/pop-after.json"; echo "rc=$?"

echo; echo "############ 1. A1 母體四數字 ＋ V1 具名清單 ############"
uv run python "$S/census.py" "$SD/pop-after.json"; echo "rc=$?"

echo; echo "############ 2. V2 覆蓋率（正式版簡介）############"
uv run python "$S/measure_v2.py" "$SD/pop-after.json" "$SD/pilot10.txt"; echo "rc=$?"

echo; echo "############ 3. V3 變異檢驗（摘要版覆寫）############"
uv run python "$S/measure_v2.py" "$SD/pop-after.json" "$SD/pilot10.txt" "$SD/briefs-summary.json"; echo "rc=$?"

echo; echo "############ 4. B 層零命中的歸因（凍結 spec 檔為 GT 來源）############"
uv run python "$S/measure_v2_blayer.py" "$SD/pop-after.json" "$SD/blayer4.txt"; echo "rc=$?"

echo; echo "############ 5. V4 卡面不變量（原始 before → 最終 after）############"
uv run python "$S/verify_invariants.py" "$SD/run-final" "$SD/briefs.json"; echo "rc=$?"
