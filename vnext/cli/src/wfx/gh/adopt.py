"""採用清單的**外部探測**：`git`／`gh` 子行程與 Project schema 讀取。

分類與渲染都不在這裡（那住 `wfx/core/adopt.py`）——本模組只把外部世界的逐字事實
裝進 `core.adopt.Probe`／`Field`／`Expectation`，核心因此仍然⛔ 不 import subprocess、
⛔ 不知道 GitHub 的欄位型別字面。

⛔ 不登入、⛔ 不保存憑證、⛔ 不安裝工具、⛔ 不建立或修改任何 Project schema：
全部呼叫都是唯讀探測，失敗就照實回「環境阻塞」，⛔ 不重試、⛔ 不推論資源不存在。
"""
from __future__ import annotations

import re
import subprocess

from wfx.core.adopt import Blocked, Expectation, Facts, Field, Probe
from wfx.core.errors import LayerMissing
from wfx.core.rules import CORE_DIR, core_concept_rows
from wfx.gh.client import GhClient, GhError
from wfx.gh.facts import STATUS_FIELD_ALIASES
from wfx.gh.localgit import LocalGitUnavailable
from wfx.gh.target import TargetError, resolve_repository

# `core/github.md` §2「落地」欄的措辭 → GitHub Projects v2 的 `dataType` 字面。
# 平台字面只住這裡；核心只拿它當不透明字串比對。
DATA_TYPES = (('SingleSelect', 'SINGLE_SELECT'), ('text', 'TEXT'), ('date', 'DATE'))
# 「值」欄指向 values.md 或寫明有幾個值 ⇒ 該概念是有值域的單選（狀態那一列就是這樣落地的）。
ENUMERATED = re.compile(r'values\.md|\d+\s*值|[一二三四五六七八九十]+\s*值')

NOT_PROBED = Probe(False, reason='未探測（上游未滿足）')


def first_line(text) -> str:
    lines = (text or '').strip().splitlines()
    return lines[0].strip() if lines else ''


def _capture(args, *, runner):
    """回 (rc, stdout, stderr)；工具起不來＝rc None（⛔ 不冒充某個 rc）。"""
    runner = subprocess.run if runner is None else runner
    try:
        result = runner(tuple(args), capture_output=True, text=True, check=False, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, '', str(exc)
    return result.returncode, result.stdout or '', result.stderr or ''


def probe_tool(name, args, *, runner) -> Probe:
    """工具可執行＝rc 0；其餘一律環境阻塞，附工具名、rc 與 stderr 首行。"""
    rc, stdout, stderr = _capture(args, runner=runner)
    if rc == 0:
        return Probe(True, first_line(stdout) or first_line(stderr) or f'{name}（rc=0）')
    return Probe(False, blocked=Blocked(name, rc, first_line(stderr)))


def probe_login(*, runner) -> Probe:
    """`gh auth status` 只讀不寫；**⛔ 不印 stdout**——那裡有帳號與 token scope。"""
    rc, _, stderr = _capture(('gh', 'auth', 'status'), runner=runner)
    if rc == 0:
        return Probe(True, 'gh auth status rc=0')
    return Probe(False, blocked=Blocked('gh auth status', rc, first_line(stderr)))


def probe_worktree(project_root, *, runner) -> Probe:
    """rc≠0＝這個目錄不在 git 工作樹內（事實缺席）；git 起不來才是環境阻塞。"""
    rc, _, stderr = _capture(('git', '-C', str(project_root), 'rev-parse', '--git-dir'),
                             runner=runner)
    if rc == 0:
        return Probe(True, '--project-root 在 git 工作樹內')
    if rc is None:
        return Probe(False, blocked=Blocked('git', None, first_line(stderr)))
    return Probe(False, reason=f'git rev-parse --git-dir rc={rc}｜{first_line(stderr)}')


def probe_repository(project_root, config, *, env, runner) -> Probe:
    """走 `facts`／`write` 同一條 remote precedence，⛔ 不另立第二套解析。"""
    try:
        target = resolve_repository(project_root, configured=(config or {}).get('remote'),
                                    env_repo=(env or {}).get('GH_REPO'), runner=runner)
    except TargetError as exc:
        return Probe(False, reason=str(exc))
    except LocalGitUnavailable as exc:
        return Probe(False, blocked=Blocked('git', None, first_line(str(exc))))
    return Probe(True, f'{target.slug}（來源 {target.provenance}）')


class _Recorder:
    """包住 runner，記下最後一次呼叫的 rc 與 stderr 首行。

    `GhClient` 的 typed 例外⛔ 不帶 rc，而「環境阻塞」這一類要求逐字附上工具名、rc 與
    stderr 首行——記錄在這裡取，⛔ 不為此在 client 上開第二條錯誤通道。
    """

    def __init__(self, runner):
        self.runner = subprocess.run if runner is None else runner
        self.rc = None
        self.stderr = ''

    def __call__(self, args, **kwargs):
        result = self.runner(args, **kwargs)
        self.rc, self.stderr = result.returncode, first_line(result.stderr)
        return result


def probe_schema(location, *, runner, client=None):
    """(Probe, 欄位逐字投影)。唯讀：只查 Project 本體與欄位，⛔ 不建立、⛔ 不修改 schema。"""
    recorder = _Recorder(runner)
    # adopt 只用 owner／number 範圍的查詢，repository slug 在這條路徑上用不到。
    client = GhClient('', runner=recorder) if client is None else client
    ref = f'{location["owner"]}/projects/{location["number"]}'
    try:
        project = client.project(location['owner'], location['number'])
        nodes = client.project_field_names(project['id'])
    except GhError as exc:
        return Probe(False, blocked=Blocked('gh', recorder.rc,
                                            recorder.stderr or first_line(str(exc)))), ()
    fields = tuple(Field(node['name'], node.get('dataType') or 'unknown',
                         tuple(option['name'] for option in (node.get('options') or ())))
                   for node in nodes)
    return Probe(True, ref), fields


def expectations(rules_root) -> tuple[Expectation, ...]:
    """`core/github.md` §2 → 每個核心概念該有的欄位型別；⛔ 不內建概念名、⛔ 不內建值。"""
    out = []
    for concept, landing, allowed in core_concept_rows(rules_root):
        data_type = next((value for word, value in DATA_TYPES if word in landing), None)
        if data_type is None and ENUMERATED.search(allowed):
            data_type = 'SINGLE_SELECT'
        if data_type is None:
            raise LayerMissing('framework', f'{CORE_DIR}/github.md',
                               f'§2「{concept}」的落地欄位型別讀不出來')
        builtin = (STATUS_FIELD_ALIASES
                   if any(f'`{alias}`' in landing for alias in STATUS_FIELD_ALIASES) else ())
        out.append(Expectation(concept, builtin, data_type))
    return tuple(out)


def collect(project_root, rules_root, config, *, env=None, runner=None, client=None) -> Facts:
    """全部外部探測的唯一入口。上游不成立就**不探測**下游，由核心分類成「無法確認」。"""
    git = probe_tool('git', ('git', '--version'), runner=runner)
    gh = probe_tool('gh', ('gh', '--version'), runner=runner)
    login = probe_login(runner=runner) if gh.ok else NOT_PROBED
    worktree = probe_worktree(project_root, runner=runner) if git.ok else NOT_PROBED
    repository = (probe_repository(project_root, config, env=env, runner=runner)
                  if git.ok and worktree.ok else NOT_PROBED)
    location = (config or {}).get('project')
    project, fields = NOT_PROBED, ()
    if location is not None and gh.ok and login.ok:
        project, fields = probe_schema(location, runner=runner, client=client)
    return Facts(git, gh, login, worktree, repository, project, fields,
                 expectations(rules_root))
