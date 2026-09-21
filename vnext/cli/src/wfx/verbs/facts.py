"""`facts --task <id> [--sha <sha>]`：只輸出六類客觀事實，⛔ 不作任何內容判斷。

輸出形狀刻意逐行、固定順序：同一 SHA、同一次遠端讀取重跑可逐字 `diff`；
⛔ 不印工作樹路徑與執行時間（那會讓乾淨 checkout 的比對失敗，且不是被問的事實）。
第 ③ 節兩個 `updatedAt` 逐字可直接餵給 W1.8 `write --expect-updated-at`。
"""
from __future__ import annotations

import argparse
import os

from wfx.core.context import Context, Provenance
from wfx.gh import facts as F
from wfx.gh.client import GhClient, GhError, PermissionDenied
from wfx.gh.target import parse_task, permission_fact, resolve_repository

USAGE = 'wfx facts --task <id> [--sha <sha>]'


def parse_args(argv):
    parser = argparse.ArgumentParser(prog='wfx facts', usage=USAGE, add_help=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--sha')
    return parser.parse_args(argv)


def _locate_item(items, slug, number):
    """content 是本 repo 的該 Issue 者恰一個；⛔ 無＝事實缺席（回 None），多個＝fail-loud。"""
    matched = [item for item in items
               if (item.get('content') or {}).get('number') == number
               and ((item['content'].get('repository') or {}).get('nameWithOwner') in (None, slug))]
    if len(matched) > 1:
        raise GhError(f'{slug}#{number} 對應多個 Project item：{[i["id"] for i in matched]}')
    return matched[0] if matched else None


def collect(context, task_id, sha, *, client=None, runner=None, env=None):
    """遠端每次即時讀取，⛔ 不快取、⛔ 不凍結。"""
    env = os.environ if env is None else env
    task = parse_task(task_id)
    if task.slug:
        slug, provenance, remote_names = task.slug, Provenance('cli', '--task'), ()
    else:
        target = resolve_repository(context.project_root, configured=context.config.get('remote'),
                                    env_repo=env.get('GH_REPO'), runner=runner)
        slug, provenance, remote_names = target.slug, target.provenance, target.remote_names
    client = GhClient(slug, runner=runner) if client is None else client

    repository = client.repository(slug)
    issue = client.issue(task.number)
    sections = F.section_facts(issue.get('body'))

    location = context.config.get('project')
    concepts, baselines, unknown_baselines, item_id, project_ref = (), [], [], None, None
    permissions = [permission_fact('repository', 'repository.viewerPermission',
                                   repository.get('viewer_permission'))]
    if location is None:
        unknown_baselines.append('project_item：`.wf/config.json` 未設 project，⛔ 不猜')
        concepts = tuple(F.ConceptFact(name, None, None) for name in F.CONCEPTS)
    else:
        project_ref = f"{location['owner']}/projects/{location['number']}"
        try:
            project = client.project(location['owner'], location['number'])
        except PermissionDenied as exc:
            permissions.append(permission_fact('project', 'projectV2.viewerCanUpdate', exc))
            raise
        permissions.append(permission_fact('project', 'projectV2.viewerCanUpdate',
                                           project.get('viewerCanUpdate')))
        field_names = [f['name'] for f in client.project_field_names(project['id'])]
        item = _locate_item(client.project_items(project['id'], field_names), slug, task.number)
        if item is None:
            unknown_baselines.append(f'project_item：{project_ref} 內⛔ 無 {slug}#{task.number} 的 item')
            concepts = tuple(F.ConceptFact(name, None, None) for name in F.CONCEPTS)
        else:
            item_id = item['id']
            concepts = F.concept_facts(field_names, item['fieldValues'])
            baselines.append(F.Baseline('project_item', item_id, item['updatedAt']))

    baselines.append(F.Baseline('issue', f'{slug}#{task.number}', issue['updatedAt']))
    git = F.git_facts(context.project_root, default_branch=repository.get('default_branch'),
                      remote_names=remote_names, sha=sha, runner=runner)
    return F.GhFacts(task.raw, slug, provenance, issue['url'], project_ref, item_id, sections,
                     concepts, tuple(baselines), tuple(unknown_baselines), git,
                     F.ci_facts(client, git.head_sha or sha), tuple(permissions))


def _git_block(git, out):
    out(f'base ref: {git.base_ref or "unknown"}'
        + (f'（來源 {git.base_provenance}）' if git.base_provenance else ''))
    out(f'rev-parse base: {git.base_sha or "unknown"}')
    out(f'rev-parse {git.head_ref}: {git.head_sha or "unknown"}')
    for label, rows in (('log base..head', git.log), ('diff --stat base...head', git.diff_stat)):
        if rows is None:
            out(f'{label}: unknown')
            continue
        out(f'{label}: {len(rows)} 列')
        for row in rows:
            out(f'  {row}')
    out('merge-tree base head: ' + ('unknown' if git.merge_tree_rc is None else
                                    f'rc={git.merge_tree_rc}（git 語意：0＝可合併、1＝有衝突）'))
    for reason in git.unknown:
        out(f'unknown: {reason}')


def render(facts):
    lines = []
    out = lines.append
    out(f'# facts task={facts.task} repository={facts.repository}（{facts.repository_provenance}）')
    out(f'# issue={facts.issue_url} project={facts.project_ref or "unknown"} item={facts.item_id or "unknown"}')
    out('')
    out('## 1 · Issue 五章節（只驗標題在且其下非空，⛔ 不判內容）')
    for section in facts.sections:
        out(f'章節 ## {section.name}: {section.state}')
    out('')
    out('## 2 · 七個核心概念當下值（空＝未填，照實印）')
    for concept in facts.concepts:
        if concept.field_name is None:   # 取不到⛔ 不得印成「(空)」——那是冒充「已讀到且未填」
            out(f'{concept.concept}: unknown（Project ⛔ 無此欄，或該卡⛔ 無 item）')
        else:
            out(f'{concept.concept}[{concept.field_name}]: '
                + ('(空)' if concept.value is None else concept.value))
    out('')
    out('## 3 · 寫入基準 updatedAt（餵 write --expect-updated-at）')
    for baseline in facts.baselines:
        out(f'{baseline.object_kind} {baseline.object_ref} updatedAt={baseline.updated_at}')
    for reason in facts.unknown_baselines:
        out(f'unknown: {reason}')
    out('')
    out('## 4 · 本機 git')
    _git_block(facts.git, out)
    out('')
    out(f'## 5 · CI check（sha={facts.ci.sha or "unknown"}）')
    if facts.ci.unknown:
        out(f'unknown: {facts.ci.unknown}')
    else:
        for name, status, conclusion in facts.ci.check_runs:
            out(f'check_run {name}: status={status} conclusion={conclusion or "unknown"}')
        for context_name, state in facts.ci.statuses:
            out(f'status {context_name}: state={state}')
        if not facts.ci.check_runs and not facts.ci.statuses:
            out('(該 SHA 上⛔ 無 check run 與 status——這是遠端的事實，不是讀取失敗)')
    out('')
    out('## 6 · 權限（allowed／denied／unknown）')
    for permission in facts.permissions:
        out(f'{permission.subject}: {permission.state}（{permission.reason}）')
    return '\n'.join(lines)


def run(argv, *, project_root, config, client=None, runner=None, env=None):
    args = parse_args(argv)
    context = Context(project_root, args.task, config)
    print(render(collect(context, args.task, args.sha, client=client, runner=runner, env=env)))
    return 0
