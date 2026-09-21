"""`brief --task <id> --role <r> --stage <s> [--rules-root <p>]`：四層注入、必要清單與模型資料。

⛔ 不判內容品質、⛔ 不選模型、⛔ 不呼叫 AI、⛔ 不查額度、⛔ 不判備註是否過期、
⛔ 不解析散文語意、⛔ 不判退回是否合法、⛔ 不認識「工作包」。
第 4 層走與 `facts` 同一條唯讀 `wfx.gh`；`task_source` 是**內部**注入點（測試用固定快照），
⛔ 不是公開旗標。全域 `--project-root` 由入口的前綴迴圈消耗。
"""
from __future__ import annotations

import argparse
from pathlib import Path

from wfx.core import layers, values
from wfx.core.context import Context, RulesSource
from wfx.core.render import render
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


def build(context, role, stage, *, user_root, task_source) -> str:
    rules_root = context.rules.root
    values.check(rules_root, '角色', role)
    values.check(rules_root, '階段', stage)
    sections = [
        ('適用規則', layers.framework_rules(rules_root, role, stage)),
        ('必要清單', layers.required_checklist(rules_root, role, stage)),
        ('使用者層', layers.user_model_data(user_root)),
        ('專案層', layers.project_layer(context.project_root)),
        ('任務層', layers.task_layer(task_source.fetch(context))),
    ]
    return render(context.task_id, role, stage, sections)


def run(argv, *, project_root, config, client=None, runner=None, env=None,
        task_source=None, user_root=None):
    args = parse_args(argv)
    context = Context(project_root, args.task, config,
                      RulesSource(args.rules_root or default_rules_root()))
    source = GhTaskSource(client=client, runner=runner, env=env) if task_source is None else task_source
    print(build(context, args.role, args.stage,
                user_root=Path.home() / '.wf' if user_root is None else user_root,
                task_source=source), end='')
    return 0
