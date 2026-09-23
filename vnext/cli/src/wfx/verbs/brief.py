"""`brief --task <id> --role <r> --stage <s> [--rules-root <p>]`：四層注入、必要清單與模型資料。

輸出恰兩部分（#370 裁定 issuecomment-5763204699）：`## 派工首屏`＝只由機械資料組成的派工索引，
`## 完整原文附錄`＝四層原文逐字、順序固定、同一來源只出現一次。邊界是後者那一行，可機械定位
（`render.split_output`）。⛔ 無行數 gate、⛔ 無截斷、⛔ 無摘要——首屏行數會隨留言則數成長，
整份輸出本來就不是一個畫面。

⛔ 不判內容品質、⛔ 不選模型、⛔ 不呼叫 AI、⛔ 不查額度、⛔ 不判備註是否過期、
⛔ 不解析散文語意、⛔ 不判退回是否合法、⛔ 不認識「工作包」。
第 4 層走與 `facts` 同一條唯讀 `wfx.gh`；`task_source` 是**內部**注入點（測試用固定快照），
⛔ 不是公開旗標。全域 `--project-root` 由入口的前綴迴圈消耗。
"""
from __future__ import annotations

import argparse
from pathlib import Path

from wfx.core import layers, values
from wfx.core.context import Context, RulesSource, load_config
from wfx.core.render import Block, render
from wfx.core.rules import default_rules_root
from wfx.gh.task import GhTaskSource

USAGE = 'wfx [--project-root <p>] brief --task <id> --role <r> --stage <s> [--rules-root <p>]'


def parse_args(argv):
    parser = argparse.ArgumentParser(prog='wfx brief', usage=USAGE, add_help=True)
    parser.add_argument('--task', required=True, help='不透明任務識別（核心⛔ 不理解其格式）')
    parser.add_argument('--role', required=True, help='角色六值之一，見 rules/core/values.md')
    parser.add_argument('--stage', required=True, help='階段五值之一，見 rules/core/values.md')
    parser.add_argument('--rules-root', type=Path, default=None,
                        help='第 1 層：規則來源，可指向本機 checkout')
    return parser.parse_args(argv)


FIRST_SCREEN_NOTE = (
    '只有機械資料（欄位值／路徑／節錨／行號／url）；原文逐字在下方「完整原文附錄」，⛔ 不需再連網。'
)
APPENDIX_NOTE = '四層原文逐字保留、順序固定，同一來源只出現一次。'


def build(context, role, stage, *, user_root, task_source) -> str:
    rules_root = context.rules.root
    values.check(rules_root, '角色', role)
    values.check(rules_root, '階段', stage)
    # 選用文件模組（boundaries.md §5）：未啟用時這兩個值都是空的，輸出與未支援模組前逐字相同。
    enabled = context.config.get('modules') or []
    modules = layers.module_docs(rules_root, enabled, values.domain(rules_root, '階段'), stage)

    project_segments = layers.project_layer(context.project_root)
    data = task_source.fetch(context)
    task_segments = layers.task_layer(data)

    first_screen = [
        Block('派工首屏', note=FIRST_SCREEN_NOTE),
        Block('核心概念現值', [layers.core_concept_values(data)], level=3),
        Block('必要清單', layers.required_checklist(rules_root, role, stage), level=3),
        Block('Issue body 章節定位', [layers.issue_section_index(rules_root, data)], level=3),
        Block('留言定位索引', [layers.comment_index(data)], level=3),
        Block('模型資料狀態', [layers.user_model_index(user_root)], level=3),
        Block('專案政策來源', [layers.project_policy_index(project_segments)], level=3),
        Block('適用 core 規則定位', [layers.rules_index(rules_root)], level=3),
    ]
    if enabled:
        first_screen.append(Block('啟用模組定位', [layers.module_index(modules)], level=3))
    appendix = [
        Block('完整原文附錄', note=APPENDIX_NOTE),
        Block('適用規則', layers.framework_rules(rules_root, role, stage)
              + layers.module_segments(modules), level=3),
        Block('使用者層', layers.user_model_data(user_root), level=3),
        Block('專案層', project_segments, level=3),
        Block('任務層', task_segments, level=3),
    ]
    return render(context.task_id, role, stage, first_screen, appendix)


def run(argv, *, project_root, client=None, runner=None, env=None,
        task_source=None, user_root=None):
    args = parse_args(argv)
    context = Context(project_root, args.task, load_config(project_root),
                      RulesSource(args.rules_root or default_rules_root()))
    source = GhTaskSource(client=client, runner=runner, env=env) if task_source is None else task_source
    print(build(context, args.role, args.stage,
                user_root=Path.home() / '.wf' if user_root is None else user_root,
                task_source=source), end='')
    return 0
