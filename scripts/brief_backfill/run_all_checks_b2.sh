#!/usr/bin/env bash
# 第二批（20 張純隨機）交付的全部量測，一次跑完。
# ⛔ 不接管線截斷（`| tail` 會把 $? 換成 tail 的，本 repo 同族已犯三次）。
# 用法：run_all_checks_b2.sh <scratch_dir>
set -u
SD="$1"
CLI="$(cd "$(dirname "$0")/../../cli" && pwd)"
S="$(cd "$(dirname "$0")" && pwd)"
cd "$CLI" || exit 1

echo "############ 0. 回填後全母體快照（唯讀）############"
uv run python "$S/snapshot_population.py" "$SD/pop-b2-after.json"; echo "rc=$?"

echo; echo "############ 1. A1 母體四數字 ＋ V1 具名清單（現場重算）############"
uv run python "$S/census.py" "$SD/pop-b2-after.json"; echo "rc=$?"

echo; echo "############ 2. V2 覆蓋率＋統計檢定（正式版簡介）############"
uv run python "$S/measure_b2.py" "$SD/pop-b2-after.json" "$SD/batch2.txt" "" "第二批20張"; echo "rc=$?"

echo; echo "############ 2b. V2 對照：A6 修訂前的原始草稿（離線 override）############"
uv run python "$S/measure_b2.py" "$SD/pop-b2-after.json" "$SD/batch2.txt" "$SD/briefs-b2-v0.json" "第二批20張-A6修訂前"; echo "rc=$?"

echo; echo "############ 3. V3 變異檢驗（摘要版覆寫 10 張）############"
uv run python "$S/measure_b2.py" "$SD/pop-b2-after.json" "$SD/v3-sample.txt" "$SD/briefs-b2-summary.json" "V3摘要版10張"; echo "rc=$?"

echo; echo "############ 3b. V3 對照：同 10 張的正式版簡介 ############"
uv run python "$S/measure_b2.py" "$SD/pop-b2-after.json" "$SD/v3-sample.txt" "" "V3同10張正式版"; echo "rc=$?"

echo; echo "############ 4. B 層零命中歸因（凍結 spec 檔為 GT 來源）############"
uv run python "$S/measure_v2_blayer.py" "$SD/pop-b2-after.json" "$SD/b2-blayer.txt"; echo "rc=$?"

echo; echo "############ 5. V4 卡面不變量（逐張 before → after）############"
uv run python "$S/verify_invariants.py" "$SD/run-b2" "$SD/briefs-b2.json"; echo "rc=$?"
