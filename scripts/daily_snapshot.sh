#!/usr/bin/env bash
# LIFECYCLE: standing · 常設工具——這就是給你跑的；不要刪
#
# 每日狀態面快照 export 回 git（AI_WORKFLOW.md §4.1／§4.3 的補償控制）。
#
# 為什麼需要這支：canonical 說「事件載體＝Issue timeline ＋結構化 comment；因其
# 非嚴格不可覆寫，必須以每日 snapshot export 回 git 建立離線稽核副本」。在 2026-08-19
# 之前，那句話沒有任何機器在執行——兩個 repo 零 snapshot 產物、.github/workflows 無
# schedule。本檔＋一支 launchd plist 就是那句話的實作。
#
# ⚠️ 它做不到的事（別把它當成 event log 的備份）：`wfcli snapshot` 匯出的是**看板
#    當前狀態**（13 個凍結欄位＋卡面資源宣告），**不含 Issue timeline 上的 lifecycle
#    event 留言**。也就是說：被事後編輯或刪除的結構化 comment，本快照偵測不到。
#    canonical AI_WORKFLOW.md §4.1 那條——
#    「因其非嚴格不可覆寫，必須以**每日 snapshot export 回 git** 建立離線稽核副本」
#    ——想要的是「事件流」的離線副本，本檔只完成了「狀態面」那一半。
#    詳見 snapshots/README.md「這份快照證明得了什麼」。
#
# 三個寫死的決策（刻意不留第二種可能；要改就改本檔，不是加旗標）：
#   1. 排程＝**獨立 plist** `com.wf.daily-snapshot`，每日 10:40。不掛 cpbl 的 10:10
#      爬蟲鏈：跨 repo 相依會讓爬蟲鏈失敗時連坐拖掉快照，而這兩件事沒有任何共同前置。
#      10:40 選在 cpbl 鏈之後同一個「機器醒著」的時段（10:10 實測穩定），不排深夜。
#   2. 檔名策略＝**逐日目錄** `snapshots/YYYY-MM-DD/`，不覆寫。理由是本卡要解的病灶
#      正是「宣稱有、其實沒有」：逐日目錄讓缺漏可以用 `ls snapshots/` 一眼看出來，
#      覆寫式則要翻 git log 才知道哪天沒跑，偵測成本高一個數量級。
#   3. 落點＝本 repo 的 **`snapshots` 孤兒分支**（orphan branch），不是 main。
#      為什麼不是 main：repo ruleset「main must be green」對 default branch 要求
#      status check `tests` 且 `strict_required_status_checks_policy=true`、
#      `bypass_actors` 為空，無人值守的直接 push 到 main 過不了；而 repo 的
#      `allow_auto_merge=false`，走 PR 就得由這支腳本自己合併 PR——「機器自行 merge」
#      在本專案的治理下是違規動作。孤兒分支同時避開三件事：與 main 的樹永不衝突、
#      不觸發 CI（`[skip ci]`）、不會在 `wfcli doctor` 的 worktree 對帳裡長出孤兒
#      worktree（本腳本用獨立 clone，不用 `git worktree add`）。
#
# 產物與可觀測面（全部在 repo 外，不污染宣告的寫入集）：
#   $STATE_DIR/repo/                 專用 clone（只 checkout `snapshots` 分支）
#   $STATE_DIR/last-status.json      最近一次結果（trigger／exit／commit／phase）
#   $STATE_DIR/logs/*.log            每次執行的完整輸出（只留最近 30 份）
#   ~/Library/Logs/wf-daily-snapshot/launchd.{out,err}.log   launchd 自己的 stdio
#
# 用法：
#   scripts/daily_snapshot.sh --help
#   scripts/daily_snapshot.sh --check       # 唯讀：驗工具＋憑證＋真的跑一次 snapshot 到暫存目錄，不碰 git
#   scripts/daily_snapshot.sh               # 正式：產生當日快照，commit＋push 到 snapshots 分支
#   scripts/daily_snapshot.sh --install     # 產生並安裝 launchd plist（10:40）
#   scripts/daily_snapshot.sh --uninstall   # 移除 launchd 註冊與 plist
#
# 離開碼：0 成功 · 64 參數錯 · 69 缺工具 · 70 狀態檔寫入失敗 · 75 鎖被佔用
#         · 77 遠端／憑證不可用 · 78 wfcli snapshot 失敗 · 79 git commit／push 失敗
set -uo pipefail

# ⚠️ 本檔訊息幾乎全是中文，而 `set -u` ＋ 中文字元有一個 locale 依賴的地雷：
#    未加花括號的 `$VAR` 若**緊鄰非 ASCII 字元**（全形括號、中文字、`／`、`·`…），
#    bash 3.2 在 UTF-8 locale 下會把該字元的 lead byte 當成識別符字元吃進變數名，
#    於是 `$OUT_TMP` 後面直接接一個全形左括號時，整串被解析成變數 `OUT_TMP\xef`，
#    `set -u` 於是判定 unbound variable 並中止。（此處刻意不寫出相鄰的原形，否則
#    下面那條守衛會把這行註解自己算成一次命中——實際上 2026-08-19 就發生過一次。）
#    實測（2026-08-19，/bin/bash 3.2.57）：0x80–0xFF 共 65 個 byte 會被吃進變數名，
#    涵蓋全部 CJK／全形的 lead byte（0xC2–0xEF）。
#    ⚠️ **C locale 下驗不出來**（LANG／LC_ALL 未設時就是 C，launchd 也是 C），
#    所以「本機跑過沒事」不構成證據——參見 docs/ROADMAP.md「runner 不是 UTF-8」那一節。
#    這條地雷特別毒的地方在於受害者多半落在 die() 錯誤回報路徑上：錯誤處理自己二次
#    崩潰，離開碼退化成 1、last-status.json 也不會被寫出來。
#
#    不變式：**具名變數展開一律 `${VAR}`**（`$?`／`$1`／`$#` 等單字元特殊參數不受影響）。
#    守衛（期望輸出 `0`，任何非 0 都是回歸）：
#      perl -ne '$n++ while /\$[A-Za-z_][A-Za-z0-9_]*[\x80-\xFF]/g;
#                END{printf "%d\n", $n||0}' scripts/daily_snapshot.sh
#    刻意**不**在此固定 locale：固定 C 會把地雷埋回去（腳本永遠走驗不出來的那一側），
#    固定 UTF-8 則會連帶改變 git／gh／wfcli 子行程的輸出編碼。修的是程式碼，不是環境。

# ============================================================== argv 守衛（放最前面）
usage() {
  cat <<'EOF'
scripts/daily_snapshot.sh — 每日狀態面快照 export 回 git（launchd 觸發）

在做什麼
  1. 確認 uv／gh／git 都在、遠端可達，然後取鎖（--check 唯讀，不取鎖）
  2. 跑 `wfcli snapshot`（唯讀 GraphQL，實測 6 個 request／次）產出
     snapshot.json＋SNAPSHOT.md
  3. 寫進專用 clone 的 snapshots/YYYY-MM-DD/，commit（訊息帶 trigger 與來源 SHA）
     並 push 到 ruan6047/ai-workflow 的 `snapshots` 孤兒分支
  4. 結果寫 last-status.json 供人／AI 事後診斷

會寫什麼
  · GitHub：ruan6047/ai-workflow 的 `snapshots` 分支（append-only，一天一筆）
  · 本機：${WF_SNAPSHOT_STATE_DIR}（預設 ~/.local/state/wf-daily-snapshot）
  · ⚠️ 不碰 main、不碰任何 Issue／Project 欄位（snapshot 是唯讀動詞）

怎麼呼叫
  scripts/daily_snapshot.sh            # 正式
  scripts/daily_snapshot.sh --check    # 唯讀自我檢查（不 commit、不 push）
  scripts/daily_snapshot.sh --install  # 安裝 launchd 排程（每日 10:40）
  scripts/daily_snapshot.sh --uninstall

環境變數（只有測試接縫；排程時間、分支名、路徑策略是寫死的常數）
  WF_SNAPSHOT_TRIGGER    manual（預設）／launchd／任意標記；會寫進 commit 訊息
  WF_SNAPSHOT_STATE_DIR  本機狀態目錄（預設 ~/.local/state/wf-daily-snapshot）
  WF_SNAPSHOT_REMOTE     推去哪（預設 git@github.com:ruan6047/ai-workflow.git）；
                         測試時可指向本機 bare repo，用來在不碰 GitHub 的情況下驗機制

背景：snapshots/README.md（落點、稽核方法、這份快照證明不了什麼）
EOF
}

MODE="run"
if [ "$#" -gt 0 ]; then
  case "$1" in
    -h|--help)      usage; exit 0 ;;
    --check)        MODE="check" ;;
    --install)      MODE="install" ;;
    --uninstall)    MODE="uninstall" ;;
    *)              echo "未知參數：$1（只接受 --help／--check／--install／--uninstall）" >&2; exit 64 ;;
  esac
fi
if [ "$#" -gt 1 ]; then
  echo "只接受一個參數" >&2; exit 64
fi

# ============================================================== 寫死的常數
LABEL="com.wf.daily-snapshot"
SCHEDULE_HOUR=10
SCHEDULE_MINUTE=40
BRANCH="snapshots"                     # 孤兒分支；不是 main（理由見檔頭決策 3）
WFCLI_OWNER_FIXED="ruan6047"
WFCLI_PROJECT_FIXED=4
# 排程要跑的腳本路徑＝主 checkout 的這個檔案。刻意不複製一份到 state dir：
# 安裝副本會與 repo 版本 drift，而 drift 的那一天沒有人會發現。代價是本卡 merge
# 進 main 之前，排程呼叫的路徑還不存在（launchd 會記 exit=127），這是已知且刻意
# 接受的空窗——見交付報告「驗收條 2 尚未成立」。
CANONICAL_SCRIPT="/Users/ruanruan/Dev/ai-workflow/scripts/daily_snapshot.sh"
LAUNCHD_LOG_DIR="$HOME/Library/Logs/wf-daily-snapshot"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"

STATE_DIR="${WF_SNAPSHOT_STATE_DIR:-$HOME/.local/state/wf-daily-snapshot}"
# SSH 而非 HTTPS：本機對這個 repo 既有的 origin 就是 SSH，金鑰已在 ssh-agent 且
# `launchctl getenv SSH_AUTH_SOCK` 有值（launchd job 拿得到同一個 agent）。走 HTTPS
# 反而要另外裝 credential helper——多一套沒人在維護的憑證路徑就是多一個靜默失敗點。
REMOTE="${WF_SNAPSHOT_REMOTE:-git@github.com:ruan6047/ai-workflow.git}"
TRIGGER="${WF_SNAPSHOT_TRIGGER:-manual}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"      # 本腳本所屬的 checkout；wfcli 原始碼由此取
CLI_DIR="$SRC_REPO/cli"

CLONE_DIR="$STATE_DIR/repo"
LOG_DIR="$STATE_DIR/logs"
LOCK_DIR="$STATE_DIR/run.lock"
STATUS_FILE="$STATE_DIR/last-status.json"

STARTED_AT="$(date '+%Y-%m-%dT%H:%M:%S%z')"
TODAY="$(date '+%Y-%m-%d')"

# ============================================================== install／uninstall
if [ "$MODE" = "install" ]; then
  mkdir -p "$HOME/Library/LaunchAgents" "$LAUNCHD_LOG_DIR" || exit 70
  cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!-- 由 scripts/daily_snapshot.sh --install 產生；手改會在下次 --install 被覆蓋。
     安裝：  scripts/daily_snapshot.sh --install
     受據：  launchctl print gui/\$(id -u)/${LABEL}
     手動測跑：launchctl kickstart -k gui/\$(id -u)/${LABEL}
     停用：  scripts/daily_snapshot.sh --uninstall
     ⚠️ ProgramArguments 指向主 checkout 的腳本；本卡 merge 進 main 之前該檔不存在，
        launchd 會每天記一次失敗到 StandardErrorPath——這是刻意可見的空窗，不是靜默。 -->
<plist version="1.0">
<dict>
  <key>Label</key><string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${CANONICAL_SCRIPT}</string>
  </array>
  <key>WorkingDirectory</key><string>$(dirname "$(dirname "$CANONICAL_SCRIPT")")</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>WF_SNAPSHOT_TRIGGER</key><string>launchd</string>
  </dict>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>${SCHEDULE_HOUR}</integer>
    <key>Minute</key><integer>${SCHEDULE_MINUTE}</integer>
  </dict>
  <key>RunAtLoad</key><false/>
  <key>StandardOutPath</key><string>${LAUNCHD_LOG_DIR}/launchd.out.log</string>
  <key>StandardErrorPath</key><string>${LAUNCHD_LOG_DIR}/launchd.err.log</string>
</dict>
</plist>
PLIST
  launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null   # 已註冊就先卸載，讓 --install 冪等
  if ! launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"; then
    echo "launchctl bootstrap 失敗" >&2; exit 70
  fi
  echo "[install] ${LABEL} 已註冊，每日 ${SCHEDULE_HOUR}:$(printf '%02d' "$SCHEDULE_MINUTE") 執行 ${CANONICAL_SCRIPT}"
  launchctl print "gui/$(id -u)/${LABEL}" | sed -n '1,12p'
  exit 0
fi

if [ "$MODE" = "uninstall" ]; then
  launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null
  rm -f "$PLIST_PATH"
  echo "[uninstall] ${LABEL} 已移除"
  exit 0
fi

# ============================================================== 共用工具
mkdir -p "$STATE_DIR" "$LOG_DIR" || { echo "無法建立 $STATE_DIR" >&2; exit 70; }
RUN_LOG="$LOG_DIR/snapshot-$(date '+%Y%m%d-%H%M%S').log"
exec > >(tee -a "$RUN_LOG") 2>&1

PHASE="init"
COMMIT_SHA=""
CARD_COUNT=""

write_status() {
  local code="$1"
  cat > "$STATUS_FILE" <<JSON
{
  "started_at": "${STARTED_AT}",
  "finished_at": "$(date '+%Y-%m-%dT%H:%M:%S%z')",
  "trigger": "${TRIGGER}",
  "mode": "${MODE}",
  "date": "${TODAY}",
  "phase": "${PHASE}",
  "exit": ${code},
  "commit": "${COMMIT_SHA}",
  "cards": "${CARD_COUNT}",
  "branch": "${BRANCH}",
  "remote": "${REMOTE}",
  "source_repo": "${SRC_REPO}",
  "log": "${RUN_LOG}"
}
JSON
}

die() {   # die <code> <訊息>
  local code="$1"; shift
  echo "[fail:${PHASE}] $*" >&2
  write_status "$code"
  exit "$code"
}

# 只留最近 30 份 log；壞掉時要能翻歷史，但不能無限長大。
prune_logs() {
  # shellcheck disable=SC2012
  ls -1t "$LOG_DIR"/snapshot-*.log 2>/dev/null | tail -n +31 | while read -r old; do rm -f "$old"; done
}

# ============================================================== 前置檢查
PHASE="preflight"
for tool in git uv gh; do
  command -v "$tool" >/dev/null 2>&1 || die 69 "找不到 ${tool}（PATH=${PATH}）"
done
[ -d "$CLI_DIR" ] || die 69 "找不到 wfcli 原始碼目錄：$CLI_DIR"

# 憑證／連線：ls-remote 是唯讀的，失敗就不必往下走（launchd 環境下 keychain 沒解鎖
# 就是在這裡現形，而不是在 push 那一步才炸掉半成品）。
git ls-remote --heads "$REMOTE" >/dev/null 2>&1 || die 77 "遠端不可達或憑證不可用：$REMOTE"

# ============================================================== 取鎖（正式模式才需要）
# 擺在 snapshot 之前：鎖被佔用時就不該再打那 6 個 GraphQL request。`--check` 唯讀，
# 不取鎖，所以診斷永遠不會被一把殘留的鎖擋住。
if [ "$MODE" = "run" ]; then
  PHASE="lock"
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    die 75 "另一次執行仍持有鎖：${LOCK_DIR}（確認沒有殘留後手動 rmdir）"
  fi
  trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT
fi

# ============================================================== 產生快照
PHASE="snapshot"
OUT_TMP="$(mktemp -d "${TMPDIR:-/tmp}/wf-snapshot.XXXXXX")" || die 70 "mktemp 失敗"
if [ "$MODE" = "run" ]; then
  trap 'rmdir "$LOCK_DIR" 2>/dev/null; rm -rf "$OUT_TMP"' EXIT
else
  trap 'rm -rf "$OUT_TMP"' EXIT
fi

SNAPSHOT_OUT="$(cd "$CLI_DIR" && uv run --project "$CLI_DIR" --frozen wfcli snapshot \
  --owner "$WFCLI_OWNER_FIXED" --project "$WFCLI_PROJECT_FIXED" --out-dir "$OUT_TMP" 2>&1)"
SNAPSHOT_RC=$?
echo "$SNAPSHOT_OUT"
[ "$SNAPSHOT_RC" -eq 0 ] || die 78 "wfcli snapshot 失敗（rc=${SNAPSHOT_RC}）"
[ -s "$OUT_TMP/snapshot.json" ] && [ -s "$OUT_TMP/SNAPSHOT.md" ] || die 78 "snapshot 產物缺失或為空"
CARD_COUNT="$(echo "$SNAPSHOT_OUT" | sed -n 's/^\[snapshot\] \([0-9]*\) 張卡.*/\1/p' | tail -1)"

if [ "$MODE" = "check" ]; then
  PHASE="check-done"
  echo "[check] 遠端可達、snapshot 可產生（${CARD_COUNT} 張卡）；本模式不 commit、不 push"
  echo "[check] 產物暫存於 ${OUT_TMP}（本次結束即刪）"
  write_status 0
  prune_logs
  exit 0
fi

# ============================================================== 專用 clone 就位
PHASE="clone"
if [ ! -d "$CLONE_DIR/.git" ]; then
  rm -rf "$CLONE_DIR"
  # --no-checkout：預設分支的樹一個位元組都不需要，本 clone 只服務孤兒分支。
  # blob filter 只有伺服器開了 uploadpack.allowFilter 才吃（GitHub 有，本機 bare
  # repo 預設沒有），所以失敗就退回完整 clone，不讓測試接縫變成生產失敗點。
  git clone --no-checkout --filter=blob:none "$REMOTE" "$CLONE_DIR" 2>/dev/null \
    || git clone --no-checkout "$REMOTE" "$CLONE_DIR" \
    || die 79 "clone 失敗"
fi
git -C "$CLONE_DIR" remote set-url origin "$REMOTE" || die 79 "設定 remote 失敗"
git -C "$CLONE_DIR" fetch origin "$BRANCH" 2>/dev/null
if git -C "$CLONE_DIR" rev-parse --verify "origin/$BRANCH" >/dev/null 2>&1; then
  # 遠端才是事實：本機任何殘留一律丟棄，不做 merge／rebase（append-only 日誌不需要）。
  git -C "$CLONE_DIR" checkout -B "$BRANCH" "origin/$BRANCH" --quiet || die 79 "checkout $BRANCH 失敗"
  git -C "$CLONE_DIR" reset --hard "origin/$BRANCH" --quiet || die 79 "reset 失敗"
else
  # 第一次：建孤兒分支，並把 index 與工作樹一起清乾淨——孤兒分支只放 snapshots/，
  # 不帶 main 的任何檔案（`--orphan` 會沿用起點的 index／工作樹，不清就會把整個
  # main 的樹一起 commit 進來）。
  git -C "$CLONE_DIR" checkout --orphan "$BRANCH" --quiet || die 79 "建立孤兒分支失敗"
  git -C "$CLONE_DIR" rm -rf --quiet . >/dev/null 2>&1
  # 順手把說明放進分支根目錄：孤兒分支不含 main 的任何檔案，checkout 它的人
  # 需要一份「這是什麼、怎麼稽核、它證明不了什麼」在手邊。
  if [ -f "$SRC_REPO/snapshots/README.md" ]; then
    cp "$SRC_REPO/snapshots/README.md" "$CLONE_DIR/README.md"
    git -C "$CLONE_DIR" add README.md
  fi
fi

# ============================================================== 寫入並 commit
PHASE="commit"
DEST="$CLONE_DIR/snapshots/$TODAY"
mkdir -p "$DEST" || die 79 "無法建立 $DEST"
cp "$OUT_TMP/snapshot.json" "$OUT_TMP/SNAPSHOT.md" "$DEST/" || die 79 "複製產物失敗"

SRC_SHA="$(git -C "$SRC_REPO" rev-parse HEAD 2>/dev/null || echo unknown)"
git -C "$CLONE_DIR" add "snapshots/$TODAY" || die 79 "git add 失敗"
if git -C "$CLONE_DIR" diff --cached --quiet; then
  PHASE="no-change"
  echo "[snapshot] 內容與上一筆完全相同，無 commit（理論上不會發生：generated_at 每次都不同）"
  write_status 0
  prune_logs
  exit 0
fi

# commit 訊息把 trigger 寫進去：驗收條 2 要能分辨「排程跑的」與「人手動補跑的」，
# 那個分辨點必須留在產物本身，事後才可稽核（人工聲明不算證據）。
git -C "$CLONE_DIR" \
  -c user.name="wf-daily-snapshot" \
  -c user.email="ruan6047@gmail.com" \
  commit --quiet -m "chore(snapshot): state-face export ${TODAY} [skip ci]" \
  -m "trigger: ${TRIGGER}
cards: ${CARD_COUNT}
generated_at: ${STARTED_AT}
wfcli-source: ${SRC_SHA} (${SRC_REPO})" || die 79 "commit 失敗"
COMMIT_SHA="$(git -C "$CLONE_DIR" rev-parse HEAD)"

PHASE="push"
git -C "$CLONE_DIR" push origin "$BRANCH" --quiet || die 79 "push 失敗（commit $COMMIT_SHA 留在本機 ${CLONE_DIR}）"

PHASE="done"
echo "[snapshot] ${TODAY} ${CARD_COUNT} 張卡 → ${BRANCH} @ ${COMMIT_SHA}（trigger=${TRIGGER}）"
write_status 0
prune_logs
exit 0
