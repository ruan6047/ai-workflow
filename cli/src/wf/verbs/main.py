"""入口。動詞集合固定為七個（core/verbs.md §1）；本檔只做分派，各動詞住 verbs/<name>.py。

消費 core/verbs.md §1 七列／§2（檢查先於首次遠端寫入；任何遠端寫入前須先取得 static 身分已驗證的 context；
身分衝突走本機硬擋零寫入）、ADOPTION.md §2（`.wf/modules.json`、`rules`／`remote` 鍵、三個全域旗標）、core/modules.md §5（模組可用性 fail-closed）。
本檔只解析全域旗標、定 project_root 與 rules source、載 catalog、解析 resolved target identity、建 client 並
綁定 static Context gate，再把其餘 argv 交給該動詞的 `run`；⛔ 不判內容、⛔ 不代動詞印、⛔ 不寫遠端。
public shape：`wf [--project-root <p>] [--rules-root <p>] [--remote <name>] <verb> [動詞參數…]`；三旗標只認
動詞之前，由前綴迴圈消耗、⛔ 不傳給動詞的 parse_args。precedence：project_root＝旗標 > main(root=…) 自舉
簡寫 > invocation cwd；rules source＝旗標 > `rules.path` > 預設等於 project_root；remote＝旗標 > `remote` 鍵 >
current branch upstream > 唯一 remote（gh/target.py）。相對 base：旗標值以 invocation cwd，`rules.path` 以
project_root。`GH_REPO` 不在任何 precedence 內：本機 repository 身分缺席時成唯一候選，存在時只作 stable ID
核對；再缺時取注入 client 自帶的 repo（自舉直呼／測試）。本機 git 事實經 gh/target.py（`gh/` 是唯一可
import subprocess 的層，test_gh_scope.py）。
"""
import os
from pathlib import Path
import sys

from wf.compose.blocks import BlockError, load_blocks
from wf.compose.project_config import ProjectConfigError, load_project_config
from wf.context import (Context, ContextError, IdentityError, ProjectRoot, Provenance, Resolved,
                        open_rules_source, resolve_path, static_identity_verified)
from wf.gh.client import GhClient
from wf.gh.localgit import LocalGitUnavailable
from wf.gh.target import (RepositoryCandidate, local_git_facts, permission_facts, resolve_project,
                          resolve_repository, select_remotes, slug_of)
from wf.module_validation import ModuleValidationError, validate_modules
from wf.verbs import _adopt, brief, edit, move, notes, review, snapshot
from wf.verbs import open as open_verb

DISPATCH = {'open': open_verb, 'move': move, 'edit': edit, 'notes': notes,
            'brief': brief, 'review': review, 'snapshot': snapshot}
VERBS = tuple(DISPATCH)
GLOBAL_FLAGS = ('--project-root', '--rules-root', '--remote')
# 無值的全域旗標（需求方 2026-09-16 裁定 G4：`--dry-run` 掛總入口、⛔ 不逐動詞加）。
# 刻意與 GLOBAL_FLAGS 分開宣告：那三個是「旗標帶一個值」的形狀，共用一組會把 `--dry-run` 的
# 下一個 token 吃掉；也讓既有釘住 GLOBAL_FLAGS 內容的測試維持原義。
BOOLEAN_FLAGS = ('--dry-run',)


def global_flags(argv):
    """前綴迴圈：只消耗動詞之前的全域旗標（帶值的三個寫 `--x v` 或 `--x=v`，重複以後者為準；
    `--dry-run` 不帶值）；形狀不對、或全域旗標出現在動詞之後（⛔ 不傳給動詞的 parse_args）
    ＝None（呼叫端印用法、rc=2）。"""
    flags, rest = {}, list(argv)
    while rest and rest[0].startswith('--'):
        name, has_value, value = rest[0].partition('=')
        if name in BOOLEAN_FLAGS and not has_value:
            flags[name], rest = True, rest[1:]
            continue
        if name not in GLOBAL_FLAGS or (not has_value and len(rest) < 2):
            return None
        flags[name] = value if has_value else rest[1]
        rest = rest[1 if has_value else 2:]
    if any(token.partition('=')[0] in GLOBAL_FLAGS + BOOLEAN_FLAGS for token in rest[1:]):
        return None
    return flags, rest


def candidates(facts, flags, config, env, client):
    """repository 候選與 assertion（A4／A5）：本機 remote 經 precedence；本機缺席時 `GH_REPO` 成唯一候選，
    再缺時取注入 client 自帶的 repo；本機存在時 `GH_REPO` 只作核對。"""
    remotes, provenance = select_remotes(facts, explicit=flags.get('--remote'), configured=config.get('remote'))
    found = [RepositoryCandidate(slug, Provenance(provenance.kind, f'{provenance.detail} {remote.name}'))
             for remote in remotes for slug in [slug_of(remote.fetch_url)] if slug]
    asserted = RepositoryCandidate(env['GH_REPO'], Provenance('env', 'GH_REPO')) if env.get('GH_REPO') else None
    if found:
        return found, asserted
    if asserted is not None:
        return [asserted], None
    if getattr(client, 'repo', None):
        return [RepositoryCandidate(client.repo, Provenance('default', 'client.repo'))], None
    return [], None


def bootstrap(flags, *, root, env, client):
    """失敗最晚時點：旗標／root／設定／rules／catalog 都在任何 API 讀取之前；remote 多義、`GH_REPO` 不符、
    Project 解析不到都在第一次 API 讀取之後、client 綁定 context 之前（六原語尚未綁定即 raise）。"""
    cwd = resolve_path('.', os.getcwd(), Provenance('default', 'invocation cwd'))
    if '--project-root' in flags:
        project_path = resolve_path(flags['--project-root'], cwd.canonical, Provenance('cli', '--project-root'))
    elif root is not None:
        project_path = resolve_path(str(root), cwd.canonical, Provenance('default', 'main(root=…)'))
    else:
        project_path = cwd
    config = load_project_config(project_path.canonical)
    project = ProjectRoot(project_path, str(Path(project_path.canonical) / '.wf/modules.json'), config,
                          Provenance('project_config', '.wf/modules.json'))
    if '--rules-root' in flags:
        rules_path = resolve_path(flags['--rules-root'], cwd.canonical, Provenance('cli', '--rules-root'))
    elif config.get('rules') is not None:
        rules_path = resolve_path(config['rules']['path'], project_path.canonical,
                                  Provenance('project_config', 'rules.path'))
    else:
        rules_path = Resolved(project_path.canonical, project_path.canonical, project_path.canonical,
                              Provenance('default', 'project_root'))
    rules = open_rules_source(rules_path.canonical, rules_path.provenance)
    catalog = load_blocks(rules)
    # core/modules.md §5 fail-closed：模組可用性在任何 API 讀取與任何遠端寫入之前判定。
    # 刻意放在 client 綁定之前 ⇒ 不過時該次執行對 GitHub 與 Project 零呼叫；
    # ⛔ 不得推出「可用旗標或環境變數放行」——無效設定自下一次相關指令起一律拒絕操作。
    validate_modules(catalog, config).raise_for_status()
    try:
        facts = local_git_facts(project_path.canonical)
    except LocalGitUnavailable:
        facts = None  # git 不可執行＝本機事實缺席，交給 GH_REPO／注入 client 決定，⛔ 不猜 origin
    found, asserted = candidates(facts, flags, config, env, client)
    if not found:
        raise ContextError('未能取得 repo：設 GH_REPO 或在有 remote 的 git repo 內執行')
    probe = GhClient(found[0].slug) if client is None else client
    repository, payload = resolve_repository(found, lookup=probe.repository, assertion=asserted)
    client = GhClient(repository.name_with_owner) if client is None else client
    board, board_payload = resolve_project(config['project'], client.capability)
    context = Context(project, rules, catalog, facts, repository, board, permission_facts(payload, board_payload),
                      cwd, static_identity_verified(project, rules, repository, board))
    client.bind_context(context)
    return context, client


def main(argv=None, *, client=None, root=None, env=None) -> int:
    """全域旗標之後的 argv[0]＝動詞；client／env 供測試注入，缺省走真實 GhClient 與環境變數。"""
    argv = sys.argv[1:] if argv is None else list(argv)
    parsed = global_flags(argv)
    if parsed is None or not parsed[1] or parsed[1][0] not in DISPATCH:
        print('wf <' + '|'.join(VERBS) + '> …', file=sys.stderr)
        return 2
    flags, argv = parsed
    adopt_requested = argv[0] == 'snapshot' and any(
        token.partition('=')[0] == '--adopt' for token in argv[1:])
    try:
        context, client = bootstrap(flags, root=root, env=os.environ if env is None else env, client=client)
    # WF-015 A7：下面三個分支各自在原有輸出之後呼叫 `_adopt` 的純計算聚合函式，印出與 `--adopt preflight`
    # 同一份項名清單常數（`import` 使用、⛔ 不重打），bootstrap 未成功而取不到的項一律標 `unknown`。
    # 純計算、落 stdout、對 GitHub 與 Project 零 mutation（client 在 `bootstrap()` 內尚未 bind_context 即 raise）。
    # 刻意只在本次呼叫就是 `snapshot --adopt <step>` 時印（`adopt_requested`）：⛔ 不把採用診斷加到別的
    # 動詞的失敗輸出上——`cli/tests/test_main_wiring.py::test_broken_project_config_prints_one_line_and_
    # writes_nothing` 對 `notes` 的同一分支有既有逐字斷言 `captured.out == ''` 與 stderr 恰一行，而該檔
    # ⛔ 不在本卡 `resources` 內。⛔ 不得推出「聚合函式沒有接上三個分支」——接線在此，只是收斂到採用入口。
    except ProjectConfigError as exc:
        print(f'.wf/modules.json 不合法：{exc}', file=sys.stderr)
        if adopt_requested:
            _adopt.print_unavailable()
        return 1
    except ModuleValidationError as exc:
        # core/modules.md §5：完整修正資訊落 stdout（⛔ 不是 stderr），逐條、⛔ 不折疊。
        for line in exc.lines:
            print(f'模組宣告或設定不可用・{line}')
        if adopt_requested:
            _adopt.print_unavailable()
        return 1
    except IdentityError as exc:
        print(f'硬擋・{exc.code}・{exc}', file=sys.stderr)
        return 1
    except (ContextError, BlockError) as exc:
        print(str(exc), file=sys.stderr)
        if adopt_requested:
            _adopt.print_unavailable()
        return 1
    # G4：`--dry-run` 只在此掛上 client 一顆布林，gate 住 gh/writes.py 的六原語（⛔ 不逐動詞加旗標）。
    client.dry_run = '--dry-run' in flags
    for fact in context.permissions:  # 只印事實；逐 operation 的放行或阻擋⛔ 不在此（WF-016）
        print(f'permission・{fact.subject}・{fact.state}・{fact.source}・{fact.reason}', file=sys.stderr)
    return DISPATCH[argv[0]].run(argv[1:], client=client, root=Path(context.project.root.canonical),
                                 catalog=context.catalog, context=context)


if __name__ == '__main__':
    sys.exit(main())
