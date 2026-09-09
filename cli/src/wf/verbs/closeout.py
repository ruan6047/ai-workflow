"""消費 core/verbs.md §1 brief／§2、core/ruling.md 表、core/dispatch.md
wf-module-sections.closeout、core/handoff.md 每段首行、core/platform.md P5、
core/return.md findings／review_result、stages/closeout.md §2／§4。
"""
from pathlib import Path
import re

from wf.compose.enable import is_enabled
from wf.compose.project_config import module_names
from wf.gh.client import GhError
from wf.gh.localgit import LocalGitUnavailable, merge_tree
from wf.verbs._common import board_facts, comment_blocks

RULING = 'core/ruling.md'


def _returns(ctx):
    from wf.verbs.brief import _plain
    lines, records, complete = [], [], True
    try:
        comments = ctx.client.comments(ctx.number)
    except GhError as exc:
        return [f'未能取得留言：{exc}'], [], False
    for comment in sorted(comments, key=lambda c: str(c.get('created_at') or '')):
        parsed = comment_blocks(comment)
        present, data = parsed['blocks']['wf-return']
        if parsed['errors'] or (present and not isinstance(data, dict)):
            lines.append(f"未能取得 wf-return：{comment.get('url')} {_plain(parsed['errors'])}")
            complete = False
        if not isinstance(data, dict):
            continue
        if parsed['issue'] not in (None, ctx.number):
            lines.append(f"留言不在本卡：{parsed['issue']} ≠ {ctx.number}")
            continue
        evidence = f"{comment.get('created_at')} {comment.get('url')}"
        lines.append(f"{evidence} iteration：{_plain(data.get('iteration'))} · "
                     f"role：{_plain(data.get('role'))} · 作者：{_plain(parsed['author'])}")
        if data.get('role') == 'reviewer':
            lines.append(f"review_result：{_plain(data.get('review_result'))}")
        lines.append(f"reason：{_plain(data.get('reason'))}")
        findings = data.get('findings', [])
        if not isinstance(findings, list):
            lines.append(f'未能取得 findings：{_plain(findings)}')
            findings, complete = [], False
        for finding in findings:
            lines.append(_plain(finding))
            if not isinstance(finding, dict) or not isinstance(finding.get('finding_id'), str):
                complete = False
        records.append((parsed['author'], data, evidence, findings))
    return lines or ['無 wf-return'], records, complete


def _current(ctx, records, complete):
    from wf.verbs.brief import _plain
    latest, lines = {}, []
    for _, _, evidence, findings in records:
        for finding in findings:
            if isinstance(finding, dict) and isinstance(finding.get('finding_id'), str):
                latest[finding['finding_id']] = (finding, evidence)
    opened = [(f, e) for f, e in latest.values()
              if f.get('status') == 'open' and f.get('blocking') is True]
    state = '成立' if opened else '不成立' if complete else '未能取得完整留言'
    lines.append(f'open 且 blocking：{state}；證據：依留言時間序取各 finding_id 最後狀態')
    lines += [f'{e} {_plain(f)}' for f, e in (opened or list(latest.values()))]
    branch = ctx.card.get('branch')
    try:
        pulls = ctx.client.pulls_for_branch(branch) if branch else []
        if not pulls:
            lines += ['無 PR', '未能取得 merge SHA；main 祖先與 CI 略過', 'CI 非綠：未能取得 CI（無 PR）']
        for pull in pulls:
            pr = ctx.client.pull_request(pull['number'])
            sha = pr.get('merge_commit_sha')
            lines.append(f"PR #{pull['number']} merge SHA：{sha or '未能取得 merge SHA'}")
            try:
                ancestor = ctx.client.is_ancestor(sha) if sha else None
                lines.append('是否 main 祖先：' + (_plain(ancestor) if ancestor is not None else '未能取得'))
            except GhError as exc:
                lines.append(f'未能取得 main 祖先關係：{exc}')
            try:
                ci_sha = sha or (pr.get('head') or {}).get('sha')
                checks = ctx.client.ci_checks(ci_sha) if ci_sha else None
                lines.append(f'CI 狀態（{ci_sha}）：{_plain(checks)}')
                results = ([c.get('conclusion') for c in checks.get('check_runs', [])]
                           + [s.get('state') for s in checks.get('statuses', [])]) if checks else []
                state = ('成立' if any(r != 'success' for r in results) else '不成立') if results else '未能取得 CI'
                lines.append(f'CI 非綠：{state}；證據：上述 CI 狀態')
            except GhError as exc:
                lines.append(f'CI 非綠：未能取得 CI：{exc}')
    except GhError as exc:
        lines += [f'未能取得 PR／merge SHA：{exc}', '未能取得 main 祖先關係', 'CI 非綠：未能取得 CI']
    try:  # 取源同 brief 的 reviewer 段＝遠端 main 頭 vs 卡面 source_sha。
        head = ctx.card.get('source_sha')
        if not head:
            raise LocalGitUnavailable('來源 SHA 未填')
        base = ctx.client.branch_head('main')
        rc = merge_tree(base, head, root=ctx.root)
        lines.append(f"分支衝突：{'成立' if rc == 1 else '不成立'}；證據：merge-tree {base} {head} rc={rc}")
    except (GhError, LocalGitUnavailable) as exc:
        lines.append(f'分支衝突：未能取得 merge-tree：{exc}')
    return lines


def sections(ctx):
    from wf.verbs.brief import HUMAN, MODULE_SECTION, _mark
    timeline, ctx.closeout_returns, complete = _returns(ctx)
    builders = iter((timeline, _current(ctx, ctx.closeout_returns, complete)))
    rows = [line.strip('|').split('|') for line in (Path(ctx.root) / RULING).read_text().splitlines()
            if line.startswith('| ')][1:]
    declared, = ctx.catalog.by_label('json wf-module-sections')
    modules = {b.data['name']: b.data for b in ctx.catalog.by_label('yaml wf-module')}
    facts = board_facts(ctx.project, ctx.catalog, self_number=ctx.number, repo=ctx.client.repo)
    out, mark = [], _mark(ctx, 'core', RULING, '')
    for name, who, note in ([c.strip() for c in row] for row in rows):
        if 'wf-module-sections.closeout' in note:
            for module, titles in declared.data['closeout'].items():
                if module in modules and is_enabled(modules[module], modules_list=module_names(ctx.cfg),
                                                     card=ctx.card, board_facts=facts):
                    out += [(title, _mark(ctx, 'module', f'modules/{module}/module.md', MODULE_SECTION),
                             [HUMAN]) for title in titles]
        else:
            out.append((name, mark, next(builders) if who == 'CLI' else [HUMAN]))
    return out


def squash(ctx):
    from wf.verbs.brief import _plain
    verdicts = [(author, data) for author, data, _, _ in ctx.closeout_returns
                if data.get('role') == 'reviewer' and data.get('iteration') == ctx.card.get('iteration')]
    text = (Path(ctx.root) / 'core/platform.md').read_text()
    allowed = re.search(r'P5 允許集合＝([^；]+)', text)[1].split('、')
    lines, trailers = [], []
    for key in allowed:
        values = ctx.trailers.get(key.lower().replace('-', '_'))
        if key == 'Reviewed-by' and values is None:
            values = [author for author, _ in verdicts if author is not None]
        values = values if isinstance(values, list) else [] if values is None else [values]
        trailers += [f'{key}: {value}' for value in values]
        if not values and key != 'Co-Authored-By':
            lines.append(f'缺 {key}')
    body = [f"{_plain(ctx.card.get('card_id'))} {_plain(ctx.card.get('feature'))}", '',
            f"被審 SHA：{_plain(ctx.card.get('source_sha'))}"]
    body += [f"{_plain(author)}：{_plain(data.get('review_result'))}" for author, data in verdicts]
    if trailers:
        body += ['', *trailers]
    return lines + ['squash 訊息', '```text', '\n'.join(body), '```']
