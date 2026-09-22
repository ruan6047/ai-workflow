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
WORKTREE_BLOCKED = ('先排除 git 對既有 `.git` 的錯誤（例如修好 gitfile 或移除它）；'
                    '本清單⛔ 不推論工作樹缺少、⛔ 不建議 git init。')
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


def _tool_item(name: str, probe: Probe, remedy: tuple[str, ...] = (), *,
               blocked_remedy: tuple[str, ...] | None = None) -> Item:
    """`remedy` 給「事實缺席」那一支；`blocked_remedy` 給「外部工具客觀錯誤」那一支。

    兩支的下一步⛔ 不能共用：對一個**已經存在但壞掉**的目標建議「建立它」必然失敗。
    未指定時沿用 `remedy`（工具本身跑不起來的項目只會走 blocked 那一支）。
    """
    if probe.ok:
        return Item(name, DONE, probe.fact)
    if probe.blocked is not None:
        return Item(name, BLOCKED, probe.blocked.line(),
                    remedy if blocked_remedy is None else blocked_remedy)
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


def _present(path: Path) -> bool:
    """路徑上有東西（壞掉的 symlink 也算）——**存在與否**這一件事，⛔ 不判它是什麼型別。"""
    return path.exists() or path.is_symlink()


def _displace(rel: str) -> str:
    return f'mv {rel} {rel}.bak   # 或自行移除；CLI ⛔ 不代刪、⛔ 不代改名'


def _document_item(path: Path, rel: str, skeleton: tuple[str, ...]) -> Item:
    """文件類只判「存在且非空」，但**不存在**與**型別／編碼錯**要分開報。

    三種失敗各有自己的下一步：不存在＝照骨架建；路徑上不是一般檔案、或讀不出 UTF-8 文字＝
    先讓開再建（直接 `cat >` 會被目錄擋掉，覆蓋既有內容也不是 CLI 該做的事）。
    讀取只包住這一個檔案，⛔ 不吞掉清單上其他項目的診斷。例外訊息裡的絕對路徑換成相對寫法。
    """
    if not _present(path):
        return Item(rel, MISSING, f'{rel} 不存在', skeleton)
    if not path.is_file():
        return Item(rel, MALFORMED, f'{rel} 存在但不是一般檔案', (_displace(rel),) + skeleton)
    try:
        text = path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError) as exc:
        return Item(rel, MALFORMED, f'{rel} 讀不出 UTF-8 文字：{str(exc).replace(str(path), rel)}',
                    (_displace(rel),) + skeleton)
    if not text.strip():
        return Item(rel, MALFORMED, '檔案存在但為空（文件類只判存在且非空）', skeleton)
    return Item(rel, DONE, '存在且非空')


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
    # `.wf` 有三種型別事實：目錄／路徑上有東西但不是目錄／不存在。中間那種**⛔ 不是「缺少」**
    # ——報成缺少會讓下一步給出必然失敗的 `mkdir -p`，使用者照著做也收斂不了。
    wf_is_dir = wf.is_dir()
    wf_displaced = _present(wf) and not wf_is_dir
    if wf_is_dir:
        items = [Item(f'{wf.name}/ 目錄', DONE, f'{wf.name}/ 存在')]
    elif wf_displaced:
        items = [Item(f'{wf.name}/ 目錄', MALFORMED, f'{wf.name} 存在但不是目錄',
                      (_displace(wf.name), f'mkdir -p {wf.name}'))]
    else:
        items = [Item(f'{wf.name}/ 目錄', MISSING, f'{wf.name}/ 不存在', (f'mkdir -p {wf.name}',))]

    # `.wf` 被占著時，底下兩個路徑連「存不存在」都問不出來（作業系統一律回不存在）：
    # 那是上游未滿足，⛔ 不是「缺少」。
    if wf_displaced:
        items.append(Item(CONFIG_REL, UNVERIFIED, _upstream(f'{wf.name}/ 目錄')))
    elif result.state == CONFIG_OK:
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

    policy_skeleton = (
        f"cat > {POLICY_REL} <<'MD'",
        '# 專案層政策',
        '',
        '具體模型名稱、額度與帳號狀態⛔ 不住這裡（core/boundaries.md §2／§3）。',
        'MD',
    )
    items.append(Item(POLICY_REL, UNVERIFIED, _upstream(f'{wf.name}/ 目錄')) if wf_displaced
                 else _document_item(project_root / POLICY_REL, POLICY_REL, policy_skeleton))
    return Section(SECTION_TITLES[2], tuple(items))


def _repository(facts: Facts) -> Section:
    if not facts.git.ok:
        return Section(SECTION_TITLES[3], (
            Item('git 工作樹', UNVERIFIED, _upstream('git 可執行')),
            Item('github.com repository 身分', UNVERIFIED, _upstream('git 可執行')),
        ))
    items = [_tool_item('git 工作樹', facts.worktree, ('git init',),
                        blocked_remedy=(WORKTREE_BLOCKED,))]
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


def _options(rules_root: Path, expectation: Expectation) -> tuple[str, ...]:
    """該概念的 SingleSelect 值域；⛔ 無值域的概念回空 tuple。值只住 `core/values.md`。"""
    row = values.DOMAINS.get(expectation.concept)
    return () if row is None else values.domain(rules_root, row)


def _expected_field(expectation: Expectation) -> str:
    """欄名的預期寫法：內建欄位取平台自己的那個寫法，其餘就是概念名。"""
    return expectation.builtin_names[-1] if expectation.builtin_names else expectation.concept


def _expected_spec(expectation: Expectation, options: tuple[str, ...]) -> str:
    """框架已知的**預期規格**：欄型、SingleSelect 值域、唯一居所。

    這一串**⛔ 不依賴任何 Project 讀取結果**——「實際 schema 無法確認」與「預期規格未知」是
    兩件事，前者常常成立，後者從來不成立（三項都讀得出來）。上游未滿足時照樣印，
    採用者才能只靠清單完成首次設定。
    """
    parts = [f'型別 {expectation.data_type}']
    if options:
        parts.append(f'選項逐字＝{"／".join(options)}')
    if expectation.builtin_names:
        parts.append(f'唯一居所＝內建欄位（{"／".join(expectation.builtin_names)} 恰一個；'
                     '兩個都在＝該概念有第二個居所）')
    else:
        parts.append(f'欄名「{expectation.concept}」')
    return '、'.join(parts)


def _field_remedy(expectation: Expectation, name: str, options: tuple[str, ...],
                  project_ref: str | None) -> tuple[str, ...]:
    where = f'Project {project_ref}' if project_ref else 'Project'
    spec = f'欄位「{name}」型別 {expectation.data_type}'
    if options:
        spec += f'、選項逐字＝{"／".join(options)}'
    lines = [f'在 {where} 上讓 {spec}。']
    if expectation.builtin_names:
        lines.append(f'「{expectation.concept}」的唯一居所＝內建欄位'
                     f'（{"／".join(expectation.builtin_names)} 恰一個）；⛔ 不另建同義欄。')
    lines.append('CLI ⛔ 不代建、⛔ 不改 Project schema——由人在平台操作，或用 '
                 '`gh project field-create`（旗標形狀見 `gh project field-create --help`）。')
    return tuple(lines)


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
    # Project 讀不到就整節停在這裡：頭一項照實分類（上游未滿足＝無法確認，gh 給出客觀錯誤＝
    # 環境阻塞），其餘核心概念一律「無法確認」——⛔ 不把「讀不到」冒充成「缺少欄位」。
    # 但**分類是無法確認、預期規格照印**：欄型、值域與唯一居所都來自規則樹，與 Project 讀不讀
    # 得到無關，少印它們等於把兩件事混成一件，採用者就無法只靠清單做完首次設定。
    if reason or not facts.project.ok:
        head = (Item('Project 可讀', UNVERIFIED, reason) if reason
                else _tool_item('Project 可讀', facts.project))
        pending = []
        for expectation in facts.expectations:
            options = _options(rules_root, expectation)
            pending.append(Item(
                f'核心概念「{expectation.concept}」', UNVERIFIED,
                f'{_upstream("Project 可讀")}｜預期規格：{_expected_spec(expectation, options)}',
                _field_remedy(expectation, _expected_field(expectation), options, project_ref)))
        return Section(SECTION_TITLES[4], (head,) + tuple(pending))

    by_name = {field.name: field for field in facts.fields}
    items = [Item('Project 可讀', DONE, f'{facts.project.fact}｜欄位 {len(facts.fields)} 個')]
    for expectation in facts.expectations:
        options = _options(rules_root, expectation)
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
                                  f'⛔ 無欄位（收 {"、".join(expectation.builtin_names)}）'
                                  f'｜預期規格：{_expected_spec(expectation, options)}',
                                  _field_remedy(expectation, _expected_field(expectation),
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
