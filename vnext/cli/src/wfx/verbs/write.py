"""`write --task <id> [--field k=v …] [--comment-file <f>] [--expect-updated-at <ts>] [--dry-run]`

只有兩種能力：寫七個核心概念之一、貼一則留言。**正常路徑＝`facts` 取基準 → `write
--expect-updated-at <該基準>` 一次成功**；缺基準即拒寫是**負控與安全網**，⛔ 不是預期路徑。

⛔ 不判轉移是否合法、⛔ 不判內容品質、⛔ 不要求欄位與留言成對出現、⛔ 不認識工作包、
⛔ 不推導退回次數、⛔ 無開卡／關卡／改 body 能力、⛔ 不在缺基準時代呼叫者讀回後逕行寫入。
比對只在**第一個 mutation 之前**做一次：基準只縮小視窗、⛔ 不構成鎖，
基準讀取與寫入之間⛔ 不具原子性（rules/core/github.md §7）。
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from wfx.core import values
from wfx.core.context import Context
from wfx.core.errors import WfxError
from wfx.core.rules import default_rules_root
from wfx.gh import facts as F
from wfx.gh.client import GhClient
from wfx.gh.target import parse_task
from wfx.gh.writes import GhWriter

USAGE = ('wfx [--project-root <p>] write --task <id> [--field k=v …] [--comment-file <f>] '
         '[--expect-updated-at <ts>] [--dry-run] [--rules-root <p>]')

# 概念名 → values.md 的表格列名。**值本身只住 values.md**；本表只記兩處命名的對應，
# ⛔ 不是第二個值域居所。未列入者（owner／期限／Resource）⛔ 無值域，CLI 只原樣送出。
DOMAINS = {'狀態': '狀態', '階段': '階段', '風險': '風險影響', '緊急性': '緊急性'}
NOTE = '註：基準只縮小視窗、⛔ 不構成鎖；基準讀取與寫入之間⛔ 不具原子性（core/github.md §7）。'
EMPTY = '(空)'


class BaselineMissing(WfxError):
    """⛔ 無 `--expect-updated-at`：拒寫，遠端零 mutation。"""


class BaselineStale(WfxError):
    """基準與被改物件的當下 `updatedAt` 不符：拒寫，遠端零 mutation。"""


class WriteTargetMissing(WfxError):
    """被改的物件本身取不到（未設 project、⛔ 無 item、⛔ 無該欄位）；⛔ 不代建。"""


@dataclass(frozen=True)
class Target:
    """被改的**一個**物件與其基準。欄位寫入比 project_item、貼留言比 issue。"""
    kind: str                # project_item｜issue
    ref: str
    updated_at: str
    current: tuple           # (顯示名, 當下值) 逐行原樣
    before: dict = None      # 概念 → 當下值（欄位寫入用）
    project_id: str | None = None
    item_id: str | None = None
    fields: dict | None = None   # 概念 → 該 Project 的欄位 metadata
    issue_id: str | None = None


def parse_args(argv):
    parser = argparse.ArgumentParser(prog='wfx write', usage=USAGE, add_help=True)
    parser.add_argument('--task', required=True, help='不透明任務識別（核心⛔ 不理解其格式）')
    parser.add_argument('--field', action='append', default=[], metavar='k=v',
                        help='七個核心概念之一；`k=` ＝清空該欄位')
    parser.add_argument('--comment-file', type=Path, help='留言內容檔，逐字貼出')
    parser.add_argument('--expect-updated-at', help='寫入基準，取自 facts §3 的同一物件')
    parser.add_argument('--dry-run', action='store_true', help='零遠端 mutation；⛔ 不要求基準')
    parser.add_argument('--rules-root', type=Path, default=None, help='值域來源（core/values.md）')
    args = parser.parse_args(argv)
    fields = {}
    for pair in args.field:
        key, sep, value = pair.partition('=')
        if not sep or not key:
            parser.error(f'--field 形狀須為 k=v：{pair!r}')
        if key not in F.CONCEPTS:
            parser.error(f'--field 的鍵只收七個核心概念之一（{"／".join(F.CONCEPTS)}）：{key!r}')
        if key in fields:
            parser.error(f'--field {key} 重複；同一次呼叫每個概念只寫一次')
        fields[key] = value
    if not fields and args.comment_file is None:
        parser.error('⛔ 無寫入目標：至少要有一個 --field 或 --comment-file')
    if fields and args.comment_file is not None:
        parser.error('一次呼叫只改一個物件（欄位比 project_item、留言比 issue 的基準）；'
                     '一次退回事件＝兩次呼叫，各自帶自己物件的基準')
    return args, fields


def check_domain(rules_root, fields):
    """純本機檢查，在任何遠端讀寫之前。空值＝清空，⛔ 不套值域。訊息只談值域。"""
    for concept, value in fields.items():
        if value and concept in DOMAINS:
            values.check(rules_root, DOMAINS[concept], value)


def field_target(context, client, task, slug, concepts):
    location = context.config.get('project')
    if location is None:
        raise WriteTargetMissing('`.wf/config.json` 未設 project：⛔ 不猜要寫哪個 Project')
    project = client.project(location['owner'], location['number'])
    nodes = client.project_field_names(project['id'])
    names = [node['name'] for node in nodes]
    item = F.locate_item(client.project_items(project['id'], names), slug, task.number)
    if item is None:
        raise WriteTargetMissing(f'{slug}#{task.number} 在 {location["owner"]}'
                                 f'/projects/{location["number"]} 內⛔ 無 item')
    by_name = {node['name']: node for node in nodes}
    fields = {}
    for concept in concepts:
        name = F.status_field_name(names) if concept == '狀態' else concept
        if name not in by_name:
            raise WriteTargetMissing(f'Project ⛔ 無「{name}」欄位：⛔ 不代建欄位')
        fields[concept] = by_name[name]
    facts = F.concept_facts(names, item['fieldValues'])
    before = {fact.concept: EMPTY if fact.value is None else fact.value for fact in facts}
    current = tuple((f'{fact.concept}[{fact.field_name}]' if fact.field_name else fact.concept,
                     before[fact.concept]) for fact in facts)
    return Target('project_item', item['id'], item['updatedAt'], current, before,
                  project_id=project['id'], item_id=item['id'], fields=fields)


def issue_target(client, task, slug):
    issue = client.issue(task.number)
    comments = client.issue_comments(issue['id'])
    current = (('state', issue.get('state') or 'unknown'), ('留言數', str(len(comments))))
    return Target('issue', f'{slug}#{task.number}', issue['updatedAt'], current, {},
                  issue_id=issue['id'])


def compare(target, expect, *, dry_run, out):
    """印出當下基準與比對結果；拒寫一律 raise（rc≠0、遠端零 mutation）。

    ⛔ 不在缺基準時代呼叫者讀回後逕行寫入——當下基準只印給呼叫者，由他重送。
    """
    out(f'當下基準：{target.kind} {target.ref} updatedAt={target.updated_at}')
    out(f'--expect-updated-at：{expect if expect is not None else "⛔ 未提供"}')
    if expect is None:
        out('比對：未做基準比對' if dry_run else '比對：⛔ 無基準 ⇒ 拒寫（遠端零 mutation）')
        out(NOTE)
        if dry_run:
            return
        raise BaselineMissing(f'⛔ 無 --expect-updated-at：拒絕寫入 {target.kind} {target.ref}；'
                              f'當下基準＝{target.updated_at}（重送時帶它）')
    matched = expect == target.updated_at
    out('比對：相符' if matched else
        ('比對：不符（非 dry-run 時會拒寫）' if dry_run else '比對：不符 ⇒ 拒寫（遠端零 mutation）'))
    out(NOTE)
    if matched or dry_run:
        return
    raise BaselineStale(f'基準不符：--expect-updated-at={expect}，'
                        f'{target.kind} {target.ref} 當下 updatedAt={target.updated_at}；'
                        '重新確認後以當下基準重送')


def apply_fields(writer, target, fields, *, dry_run, out):
    for concept in F.CONCEPTS:
        if concept not in fields:
            continue
        field = target.fields[concept]
        value = fields[concept] or None
        before, after = target.before[concept], EMPTY if value is None else value
        if dry_run:
            out(f'{concept}[{field["name"]}]: {before} → {after}（would-write，遠端零 mutation）')
            continue
        writer.set_field(target.project_id, target.item_id, field, value)
        out(f'{concept}[{field["name"]}]: {before} → {after}（已寫入）')


def run(argv, *, project_root, config, client=None, runner=None, env=None, writer=None):
    args, fields = parse_args(argv)
    context = Context(project_root, args.task, config)
    check_domain(args.rules_root or default_rules_root(), fields)
    task = parse_task(args.task)
    slug, _, _ = F.resolve_slug(context, task, env=env, runner=runner)
    client = GhClient(slug, runner=runner) if client is None else client
    body = args.comment_file.read_text(encoding='utf-8') if args.comment_file else None
    target = (field_target(context, client, task, slug, fields) if fields
              else issue_target(client, task, slug))

    def out(line):
        print(line, flush=True)

    out(f'# write task={task.raw} 目標物件={target.kind} {target.ref}'
        + ('（--dry-run：遠端零 mutation）' if args.dry_run else ''))
    out('')
    out('## 1 · 目標物件當下值（本次即時讀取，⛔ 不快取）')
    for name, value in target.current:
        out(f'{name}: {value}')
    out('')
    out('## 2 · 基準比對')
    compare(target, args.expect_updated_at, dry_run=args.dry_run, out=out)
    out('')
    out('## 3 · would-write（⛔ 未送出任何 mutation）' if args.dry_run else '## 3 · 寫入')
    writer = GhWriter(runner=runner) if writer is None else writer
    if fields:
        apply_fields(writer, target, fields, dry_run=args.dry_run, out=out)
    elif args.dry_run:
        out(f'留言 → {target.kind} {target.ref}：{len(body.splitlines())} 行'
            '（would-write，遠端零 mutation）')
    else:
        out(f'留言 → {target.kind} {target.ref}：{writer.post_comment(target.issue_id, body)}')
    return 0
