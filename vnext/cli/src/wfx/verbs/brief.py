"""`brief --task <id> --role <r> --stage <s> [--rules-root <p>] [--full] [--omit-user-layer]`：四層注入、必要清單與模型資料。

預設輸出＝有界首屏＋一行指標（#434）：`## 派工首屏` 只由機械資料組成，資料驅動的索引清單超出
上限時依位置只列一部分並印省略數，每列（與任務識別）escape 成恰一個實體行，總量受硬性上限約束（數字與性質的定義居所＝`rules/core/flow.md` §4，
由 `tests/test_brief_bounded.py` 釘住）；⛔ 無附錄。`--full`＝完整輸出，與 #434 前的輸出逐字相同（#370 裁定 issuecomment-5763204699）：
首屏索引不設上限，後接 `## 完整原文附錄`＝四層原文逐字、順序固定、同一來源只出現一次，邊界可機械定位
（`render.split_output`）。兩種輸出都⛔ 無摘要、⛔ 不截斷原文、⛔ 不以 rc≠0 擋行數；被省略的只有首屏索引的列，
原文與完整索引一律在 `--full`。兩種輸出讀同一組來源，typed 失敗也相同。

⛔ 不判內容品質、⛔ 不選模型、⛔ 不呼叫 AI、⛔ 不查額度、⛔ 不判備註是否過期、
⛔ 不解析散文語意、⛔ 不判退回是否合法、⛔ 不認識「工作包」。
第 4 層走與 `facts` 同一條唯讀 `wfx.gh`；`task_source` 是**內部**注入點（測試用固定快照），
⛔ 不是公開旗標。全域 `--project-root` 由入口的前綴迴圈消耗。

`--omit-user-layer`（#440，預設關）：省略使用者層——`~/.wf/` 兩檔⛔ 不讀、附錄⛔ 無 `### 使用者層` 區塊、
首屏「模型資料狀態」換成一行固定說明；其餘區塊、順序、來源標記與內容逐字不變。不帶時程式路徑與輸出不變。
旗標只描述輸出內容，何時加由呼叫端決定（`rules/roles/PM.md` §3），CLI ⛔ 不判目的地。

相連任務（`core/github.md` §1 選用章節）：帶入角色與帶入章節都從規則樹抽出，程式碼⛔ 不內建角色值。
角色不在帶入角色內時**在讀相連卡之前**就分流——零相連讀取、零相連區塊，輸出與未登記相同。
"""
from __future__ import annotations

import argparse
from pathlib import Path

from wfx.core import layers, rules, values
from wfx.core.errors import MalformedInput
from wfx.core.context import Context, RulesSource, load_config
from wfx.core.render import Block, render
from wfx.core.rules import default_rules_root
from wfx.gh.task import GhTaskSource

USAGE = ('wfx [--project-root <p>] brief --task <id> --role <r> --stage <s> [--rules-root <p>] [--full]'
         ' [--omit-user-layer]')


def parse_args(argv):
    parser = argparse.ArgumentParser(prog='wfx brief', usage=USAGE, add_help=True)
    parser.add_argument('--task', required=True, help='不透明任務識別（核心⛔ 不理解其格式）')
    parser.add_argument('--role', required=True, help='角色六值之一，見 rules/core/values.md')
    parser.add_argument('--stage', required=True, help='階段五值之一，見 rules/core/values.md')
    parser.add_argument('--rules-root', type=Path, default=None,
                        help='第 1 層：規則來源，指向含 core/ 的 rules/ 目錄本身（⛔ 不是 checkout 根目錄）')
    parser.add_argument('--full', action='store_true',
                        help='完整輸出：首屏索引不設上限＋完整原文附錄（預設只印有界首屏與一行指標）')
    parser.add_argument('--omit-user-layer', action='store_true',
                        help='省略使用者層：不讀也不附 ~/.wf/ 的原文（預設附上）')
    return parser.parse_args(argv)


FIRST_SCREEN_NOTE = (
    '只有機械資料（欄位值／路徑／節錨／行號／url）；原文逐字在下方「完整原文附錄」，⛔ 不需再連網。'
)
BOUNDED_NOTE = (
    '只有機械資料（欄位值／路徑／節錨／行號／url）；原文逐字只在 `--full` 輸出的「完整原文附錄」。'
)
FULL_POINTER = '完整原文附錄未印出（本輸出只有有界首屏）：四層原文逐字與完整索引，在同一指令加 `--full` 取得。'
APPENDIX_NOTE = '四層原文逐字保留、順序固定，同一來源只出現一次。'
# `--omit-user-layer` 時的結構說明：⛔ 不得與實際內容（只有三層）矛盾
OMITTED_FULL_POINTER = ('完整原文附錄未印出（本輸出只有有界首屏）：使用者層以外的三層原文逐字與完整索引，'
                        '在同一指令加 `--full` 取得。')
OMITTED_APPENDIX_NOTE = ('使用者層以外的三層原文逐字保留、順序固定，同一來源只出現一次；'
                         '使用者層以 `--omit-user-layer` 省略。')

# 預設輸出的首屏索引上限（依位置保留，超出印省略數；`--full` 一律不設上限）。只限資料驅動的清單：
# 留言、Issue body 五章節以外的標題、`.wf/*.md`、相連任務登記。規則樹決定的清單（必要清單、core 節錨、
# 啟用模組）由框架版本決定長度、不在此列。總量上限（flow.md §4）由測試在極端輸入下釘住；規則樹變大使其轉紅
# 是設計壓力，由該次框架變更處理，⛔ 不在此預放寬。
COMMENT_LIMIT = 15        # 最新的 K 則
EXTRA_SECTION_LIMIT = 5   # 最先的 K 個
POLICY_LIMIT = 8          # 檔名序最先的 K 份
LINKED_LIMIT = 8          # 登記序最先的 K 筆


def linked_spec(rules_root):
    """`core/github.md` §1 的相連任務登記規則；帶入角色每值都須在 values.md 的角色值域內。

    不論當前角色都驗：規則樹寫錯在任何角色都 typed 失敗，⛔ 不靜默變成「永遠不帶」。
    """
    spec = rules.linked_task_spec(rules_root)
    allowed = values.domain(rules_root, '角色')
    stray = [role for role in spec.roles if role not in allowed]
    if stray:
        raise MalformedInput(f"framework:core/github.md 的「帶入角色」不在角色值域內：{'、'.join(stray)}")
    return spec


def build(context, role, stage, *, user_root, task_source, full=False, omit_user_layer=False) -> str:
    rules_root = context.rules.root
    values.check(rules_root, '角色', role)
    values.check(rules_root, '階段', stage)
    spec = linked_spec(rules_root)
    # 選用文件模組（boundaries.md §5）：未啟用（缺鍵／null）時這兩個值都是空的，⛔ 不注入模組內容。
    enabled = context.config.get('modules') or []
    modules = layers.module_docs(rules_root, enabled, values.domain(rules_root, '階段'), stage)

    project_segments = layers.project_layer(context.project_root)
    # 使用者層與專案層都排在讀卡之前：檔案讀不出（如不是 UTF-8）時不連網就報錯。只改讀取時點，輸出順序不動。
    # `--omit-user-layer`：兩檔⛔ 不讀（壞檔也不會讓這次 brief 失敗）
    if omit_user_layer:
        user_index, user_segments = layers.user_layer_omitted_index(), None
    else:
        user_index = layers.user_model_index(user_root)
        user_segments = layers.user_model_data(user_root)
    data = task_source.fetch(context)
    task_segments = layers.task_layer(data)
    # 只有帶入角色才讀登記；章節缺席＝None＝未登記，兩處都⛔ 不出現相連區塊
    linked = task_source.fetch_linked(data.issue_body, spec) if role in spec.roles else None

    # 上限只作用在首屏索引的列；None＝不設上限（`--full`）
    def limit(value):
        return None if full else value

    # 預設輸出：首屏每列與任務識別都 escape 成恰一個實體行，上限才由列數保證（單筆值或檔名內含換行時）；
    # `--full` 原樣、逐字不變
    one = not full
    first_screen = [
        Block('派工首屏', note=FIRST_SCREEN_NOTE if full else BOUNDED_NOTE),
        Block('核心概念現值', [layers.core_concept_values(data, single_line=one)], level=3),
        Block('必要清單', layers.required_checklist(rules_root, role, stage), level=3),
        Block('Issue body 章節定位', [layers.issue_section_index(
            rules_root, data, limit=limit(EXTRA_SECTION_LIMIT), single_line=one)], level=3),
        Block('留言定位索引',
              [layers.comment_index(data, limit=limit(COMMENT_LIMIT), single_line=one)], level=3),
        Block('模型資料狀態', [user_index], level=3),
        Block('專案政策來源', [layers.project_policy_index(
            project_segments, limit=limit(POLICY_LIMIT), single_line=one)], level=3),
        Block('適用 core 規則定位', [layers.rules_index(rules_root)], level=3),
    ]
    if enabled:
        first_screen.append(Block('啟用模組定位', [layers.module_index(modules, single_line=one)], level=3))
    if linked is not None:
        first_screen.append(Block('相連任務定位', [layers.linked_index(
            context.task_id, linked, spec.sections, limit=limit(LINKED_LIMIT), single_line=one)], level=3))
    appendix = [
        Block('完整原文附錄', note=OMITTED_APPENDIX_NOTE if omit_user_layer else APPENDIX_NOTE),
        Block('適用規則', layers.framework_rules(rules_root, role, stage)
              + layers.module_segments(modules), level=3),
    ]
    if not omit_user_layer:
        appendix.append(Block('使用者層', user_segments, level=3))
    appendix += [
        Block('專案層', project_segments, level=3),
        Block('任務層', task_segments, level=3),
    ]
    linked_segments = layers.linked_segments(linked or (), spec.sections)
    if linked_segments:
        appendix.append(Block('相連任務原文', linked_segments, level=3))
    # 預設輸出與 `--full` 讀同一組來源、走同一組 typed 失敗；差別只在呈現
    if not full:
        return render(layers.one_line(context.task_id), role, stage, first_screen, [],
                      tail=OMITTED_FULL_POINTER if omit_user_layer else FULL_POINTER)
    return render(context.task_id, role, stage, first_screen, appendix)


def run(argv, *, project_root, client=None, runner=None, env=None,
        task_source=None, user_root=None, linked_clients=None):
    args = parse_args(argv)
    context = Context(project_root, args.task, load_config(project_root),
                      RulesSource(args.rules_root or default_rules_root()))
    source = (GhTaskSource(client=client, runner=runner, env=env, linked_clients=linked_clients)
              if task_source is None else task_source)
    print(build(context, args.role, args.stage,
                user_root=Path.home() / '.wf' if user_root is None else user_root,
                task_source=source, full=args.full, omit_user_layer=args.omit_user_layer), end='')
    return 0
