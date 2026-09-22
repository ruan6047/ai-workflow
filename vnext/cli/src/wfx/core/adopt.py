"""採用清單：純本機**分類**與**穩定渲染**。

⛔ 不探測外部工具、⛔ 不起子行程、⛔ 不連網、⛔ 不寫入任何檔案——外部事實一律由
`wfx/gh/adopt.py` 先取好再傳進來，本模組只把它們分成五類並渲染成固定七節。

五類（唯一居所在此）：**已完成**＝目標存在且形狀合法｜**缺少**＝目標不存在｜**格式錯誤**＝存在
但形狀不合法｜**環境阻塞**＝外部工具給出客觀錯誤（附工具名、rc 與 stderr 首行）｜**無法確認**＝
本清單內的上游項未滿足。文件類一律只判「存在且非空」，⛔ 不判內容品質。

輸出⛔ 無時間戳、⛔ 無絕對路徑、⛔ 無隨機序：同一狀態重跑逐字相同。
rc ⛔ 不承載「就緒與否」——可機械消費的替代品是第 7 節的計數行。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from wfx.core import values
from wfx.core.context import (CONFIG_MALFORMED, CONFIG_MISSING, CONFIG_OK, CONFIG_REL,
                              ConfigResult)
from wfx.core.errors import WfxError
from wfx.core.rules import CORE_DIR, ROLES_DIR, STAGES_DIR

DONE, MISSING, MALFORMED, BLOCKED, UNVERIFIED = '已完成', '缺少', '格式錯誤', '環境阻塞', '無法確認'
STATES = (DONE, MISSING, MALFORMED, BLOCKED, UNVERIFIED)

# 七節固定順序；第 6 節只印、第 7 節只算。⛔ 不加第八節、⛔ 不依狀態改順序。
SECTION_TITLES = ('執行環境', '框架套件', f'`{CONFIG_REL.split("/")[0]}/` 骨架', 'repository 身分',
                  'Project schema', '下一步', '摘要')

POLICY_REL = '.wf/model-policy.md'
HEADER = '# adopt 採用清單（唯讀：CLI ⛔ 不建立、⛔ 不修改、⛔ 不刪除任何檔案或 Project schema）'
LEGEND = '# 五類：' + '｜'.join(STATES)
NEXT_NOTE = ('CLI 只印，⛔ 不代為套用——下列骨架與指令一律由人或執行 AI 自行執行。'
             '已完成的項目⛔ 不列在這裡。')
NEXT_NONE = '（全部已完成，⛔ 無下一步）'
NO_COMMAND = '（⛔ 無可直接套用的指令：先解決上游那一項，或由人在平台上處理）'
SUMMARY_NOTE = ('註：rc ⛔ 不表達就緒與否（清單產得出來就是 rc 0）；'
                '要機械判斷就緒與否請讀上面的計數。')


class AdoptUnavailable(WfxError):
    """連清單都產不出來（`--project-root` 不存在、規則樹取不到）；rc=1，⛔ 不印半份清單。"""


@dataclass(frozen=True)
class Blocked:
    """外部工具給出的客觀錯誤。三欄都是事實，⛔ 不解讀成「沒有」或「不允許」。"""
    tool: str
    rc: int | None
    stderr: str

    def line(self) -> str:
        return (f'{self.tool}｜rc={"unknown" if self.rc is None else self.rc}'
                f'｜{self.stderr or "(stderr 空)"}')


@dataclass(frozen=True)
class Probe:
    """一次外部探測的結果。`ok` 帶逐字事實；否則 `blocked`（工具錯）或 `reason`（事實缺席）。"""
    ok: bool
    fact: str = ''
    blocked: Blocked | None = None
    reason: str = ''

    def detail(self) -> str:
        return self.fact if self.ok else (self.blocked.line() if self.blocked else self.reason)


@dataclass(frozen=True)
class Field:
    """Project 上一個欄位的逐字投影：欄名、型別字面、選項字面。"""
    name: str
    data_type: str
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class Expectation:
    """一個核心概念該長什麼樣；由 `wfx/gh/adopt.py` 依 `core/github.md` §2 機械產生。

    `builtin_names` 非空＝該概念落在**內建**欄位，且這些是平台允許的欄名寫法：
    恰一個才合法，兩個都在＝該概念有第二個居所（格式錯誤）。
    """
    concept: str
    builtin_names: tuple[str, ...]
    data_type: str


@dataclass(frozen=True)
class Facts:
    """`wfx/gh/adopt.py` 交給核心的全部外部事實。核心⛔ 不再探測任何東西。"""
    git: Probe
    gh: Probe
    login: Probe
    worktree: Probe
    repository: Probe
    project: Probe
    fields: tuple[Field, ...] = ()
    expectations: tuple[Expectation, ...] = ()


@dataclass(frozen=True)
class Item:
    """清單上的一項：名稱、五類之一、逐字細節，以及非已完成時可直接套用的下一步。"""
    name: str
    state: str
    detail: str = ''
    remedy: tuple[str, ...] = ()


@dataclass(frozen=True)
class Section:
    title: str
    items: tuple[Item, ...] = ()
    lines: tuple[str, ...] = ()


def _upstream(name: str) -> str:
    return f'上游未滿足：{name}'


def _tool_item(name: str, probe: Probe, remedy: tuple[str, ...] = ()) -> Item:
    if probe.ok:
        return Item(name, DONE, probe.fact)
    if probe.blocked is not None:
        return Item(name, BLOCKED, probe.blocked.line(), remedy)
    return Item(name, MISSING, probe.reason, remedy)


def _environment(facts: Facts) -> Section:
    running = '.'.join(str(part) for part in sys.version_info[:3])
    items = [
        Item('python 直譯器', DONE, f'python {running}｜本清單正由它產生'),
        _tool_item('git 可執行', facts.git, ('安裝 git 後重跑本清單。',)),
        _tool_item('gh 可執行', facts.gh, ('安裝 GitHub CLI（gh）後重跑本清單。',)),
    ]
    if not facts.gh.ok:
        items.append(Item('gh 已登入', UNVERIFIED, _upstream('gh 可執行')))
    else:
        items.append(_tool_item('gh 已登入', facts.login,
                                ('gh auth login   # CLI ⛔ 不代為登入、⛔ 不保存憑證',)))
    return Section(SECTION_TITLES[0], tuple(items))


def _framework(rules_root: Path, rules_source: str, version: str) -> Section:
    counts = '、'.join(f'{name} {len(list((rules_root / name).glob("*.md")))} 份'
                      for name in (CORE_DIR, STAGES_DIR, ROLES_DIR))
    installed = version != 'unknown'
    return Section(SECTION_TITLES[1], (
        Item('ai-workflow-vnext 已安裝', DONE if installed else MISSING,
             f'版本 {version}' if installed else
             'importlib.metadata 取不到版本｜以原始碼樹直跑就是這個結果',
             () if installed else
             ('pip install ai_workflow_vnext-<版本>-py3-none-any.whl',)),
        Item('規則樹隨套件可讀', DONE, f'來源 {rules_source}｜{counts}'),
    ))


def _skeleton(project_root: Path, result: ConfigResult, project_ref: str | None) -> Section:
    wf = project_root / CONFIG_REL.split('/')[0]
    config_skeleton = (
        f"mkdir -p {wf.name} && cat > {CONFIG_REL} <<'JSON'",
        '{',
        '  "rules": null,',
        '  "remote": null,',
        '  "project": {"owner": "<owner>", "number": <Project 編號>}',
        '}',
        'JSON',
    )
    items = [Item(f'{wf.name}/ 目錄', DONE if wf.is_dir() else MISSING,
                  f'{wf.name}/ 存在' if wf.is_dir() else f'{wf.name}/ 不存在',
                  () if wf.is_dir() else (f'mkdir -p {wf.name}',))]
    if result.state == CONFIG_OK:
        items.append(Item(CONFIG_REL, DONE, '形狀合法｜只認 rules／remote／project 三鍵'))
    elif result.state == CONFIG_MISSING:
        items.append(Item(CONFIG_REL, MISSING, result.reason, config_skeleton))
    else:
        items.append(Item(CONFIG_REL, MALFORMED, result.reason, config_skeleton))

    if result.state != CONFIG_OK:
        items.append(Item(f'{CONFIG_REL} 的 project', UNVERIFIED, _upstream(CONFIG_REL)))
    elif project_ref is None:
        items.append(Item(f'{CONFIG_REL} 的 project', MISSING,
                          'project 為 null：⛔ 不猜要用哪個 Project', config_skeleton))
    else:
        items.append(Item(f'{CONFIG_REL} 的 project', DONE, project_ref))

    policy = project_root / POLICY_REL
    policy_skeleton = (
        f"cat > {POLICY_REL} <<'MD'",
        '# 專案層政策',
        '',
        '具體模型名稱、額度與帳號狀態⛔ 不住這裡（core/boundaries.md §2／§3）。',
        'MD',
    )
    if not policy.is_file():
        items.append(Item(POLICY_REL, MISSING, f'{POLICY_REL} 不存在', policy_skeleton))
    elif not policy.read_text(encoding='utf-8').strip():
        items.append(Item(POLICY_REL, MALFORMED, '檔案存在但為空（文件類只判存在且非空）',
                          policy_skeleton))
    else:
        items.append(Item(POLICY_REL, DONE, '存在且非空'))
    return Section(SECTION_TITLES[2], tuple(items))


def _repository(facts: Facts) -> Section:
    if not facts.git.ok:
        return Section(SECTION_TITLES[3], (
            Item('git 工作樹', UNVERIFIED, _upstream('git 可執行')),
            Item('github.com repository 身分', UNVERIFIED, _upstream('git 可執行')),
        ))
    items = [_tool_item('git 工作樹', facts.worktree, ('git init',))]
    if not facts.worktree.ok:
        items.append(Item('github.com repository 身分', UNVERIFIED, _upstream('git 工作樹')))
    elif facts.repository.ok:
        items.append(Item('github.com repository 身分', DONE, facts.repository.fact))
    elif facts.repository.blocked is not None:
        items.append(Item('github.com repository 身分', BLOCKED, facts.repository.blocked.line()))
    else:
        items.append(Item('github.com repository 身分', MISSING, facts.repository.reason,
                          ('git remote add origin git@github.com:<owner>/<name>.git',
                           f'# 或在 {CONFIG_REL} 的 "remote" 指名要用哪一個既有 remote')))
    return Section(SECTION_TITLES[3], tuple(items))


def _field_remedy(expectation: Expectation, name: str, options: tuple[str, ...],
                  project_ref: str | None) -> tuple[str, ...]:
    where = f'Project {project_ref}' if project_ref else 'Project'
    spec = f'欄位「{name}」型別 {expectation.data_type}'
    if options:
        spec += f'、選項逐字＝{"／".join(options)}'
    return (f'在 {where} 上讓 {spec}。',
            'CLI ⛔ 不代建、⛔ 不改 Project schema——由人在平台操作，或用 '
            '`gh project field-create`（旗標形狀見 `gh project field-create --help`）。')


def _schema(rules_root: Path, facts: Facts, project_ref: str | None,
            config_ready: bool) -> Section:
    if not config_ready:
        reason = _upstream(f'{CONFIG_REL} 的 project')
    elif not facts.gh.ok:
        reason = _upstream('gh 可執行')
    elif not facts.login.ok:
        reason = _upstream('gh 已登入')
    else:
        reason = ''
    if reason:
        items = [Item('Project 可讀', UNVERIFIED, reason)]
        items += [Item(f'核心概念「{e.concept}」', UNVERIFIED, _upstream('Project 可讀'))
                  for e in facts.expectations]
        return Section(SECTION_TITLES[4], tuple(items))
    if not facts.project.ok:
        state, detail = ((BLOCKED, facts.project.blocked.line()) if facts.project.blocked
                         else (MISSING, facts.project.reason))
        items = [Item('Project 可讀', state, detail)]
        items += [Item(f'核心概念「{e.concept}」', UNVERIFIED, _upstream('Project 可讀'))
                  for e in facts.expectations]
        return Section(SECTION_TITLES[4], tuple(items))

    by_name = {field.name: field for field in facts.fields}
    items = [Item('Project 可讀', DONE, f'{facts.project.fact}｜欄位 {len(facts.fields)} 個')]
    for expectation in facts.expectations:
        options = ()
        row = values.DOMAINS.get(expectation.concept)
        if row is not None:
            options = values.domain(rules_root, row)
        name = expectation.concept
        if expectation.builtin_names:
            present = tuple(n for n in expectation.builtin_names if n in by_name)
            unique = f'「{expectation.concept}」欄唯一居所'
            if len(present) > 1:
                # 最後一個別名＝平台自己的內建欄名；其餘都是另建出來的第二個居所。
                builtin = expectation.builtin_names[-1]
                extra = '、'.join(name for name in present if name != builtin)
                items.append(Item(unique, MALFORMED,
                                  f'同時存在 {"、".join(present)}：該概念有第二個居所',
                                  (f'刪掉另建的「{extra}」欄，只留內建的「{builtin}」；'
                                   'CLI ⛔ 不代刪。',)))
                items.append(Item(f'核心概念「{expectation.concept}」', UNVERIFIED,
                                  _upstream(unique)))
                continue
            if not present:
                items.append(Item(unique, MISSING,
                                  f'⛔ 無 {"、".join(expectation.builtin_names)} 任一欄'))
                items.append(Item(f'核心概念「{expectation.concept}」', MISSING,
                                  f'⛔ 無欄位（收 {"、".join(expectation.builtin_names)}）',
                                  _field_remedy(expectation, expectation.builtin_names[-1],
                                                options, project_ref)))
                continue
            items.append(Item(unique, DONE, f'落在「{present[0]}」欄'))
            name = present[0]
        field = by_name.get(name)
        label = f'核心概念「{expectation.concept}」'
        if field is None:
            items.append(Item(label, MISSING, f'Project ⛔ 無「{name}」欄位',
                              _field_remedy(expectation, name, options, project_ref)))
        elif field.data_type != expectation.data_type:
            items.append(Item(label, MALFORMED,
                              f'{name} 的型別＝{field.data_type}，'
                              f'core/github.md §2 要求 {expectation.data_type}',
                              _field_remedy(expectation, name, options, project_ref)))
        elif options and tuple(field.options) != tuple(options):
            items.append(Item(label, MALFORMED,
                              f'{name} 的選項＝{"／".join(field.options) or "(空)"}，'
                              f'core/values.md 的值域＝{"／".join(options)}',
                              _field_remedy(expectation, name, options, project_ref)))
        else:
            items.append(Item(label, DONE, f'{name}｜{field.data_type}'
                              + (f'｜{"／".join(field.options)}' if field.options else '')))
    return Section(SECTION_TITLES[4], tuple(items))


def _next_steps(sections) -> Section:
    pending = [(section, item) for section in sections for item in section.items
               if item.state != DONE]
    if not pending:
        return Section(SECTION_TITLES[5], (), (NEXT_NOTE, '', NEXT_NONE))
    lines = [NEXT_NOTE, '']
    for section, item in pending:
        lines.append(f'- {section.title} / {item.name}：{item.state}')
        for line in (item.remedy or (NO_COMMAND,)):
            lines.append(f'    {line}'.rstrip())   # ⛔ 不留行尾空白：逐字 diff 會被它絆到
    return Section(SECTION_TITLES[5], (), tuple(lines))


def _summary(sections) -> Section:
    items = [item for section in sections for item in section.items]
    lines = [f'{state}: {sum(1 for item in items if item.state == state)}' for state in STATES]
    lines.append(f'總計: {len(items)}')
    lines.append(SUMMARY_NOTE)
    return Section(SECTION_TITLES[6], (), tuple(lines))


def build(project_root: Path, rules_root: Path, *, rules_source: str, version: str,
          config: ConfigResult, facts: Facts) -> tuple[Section, ...]:
    """七節固定順序；⛔ 不因狀態增刪節、⛔ 不重排。"""
    project = (config.config or {}).get('project') if config.state == CONFIG_OK else None
    project_ref = None if project is None else f'{project["owner"]}/projects/{project["number"]}'
    diagnosed = (
        _environment(facts),
        _framework(rules_root, rules_source, version),
        _skeleton(project_root, config, project_ref),
        _repository(facts),
        _schema(rules_root, facts, project_ref, project_ref is not None),
    )
    return diagnosed + (_next_steps(diagnosed), _summary(diagnosed))


def render(sections) -> str:
    lines = [HEADER, LEGEND]
    for number, section in enumerate(sections, start=1):
        lines += ['', f'## {number} · {section.title}']
        for item in section.items:
            lines.append(f'- {item.name}：{item.state}'
                         + (f'（{item.detail}）' if item.detail else ''))
        lines += list(section.lines)
    return '\n'.join(lines)
