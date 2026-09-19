"""WF-015 A1／A2。消費 core/adopt.md §3、core/verbs.md §1 `snapshot` 列、core/naming.md §1／§5、
ADOPTION.md §2。

A1 判準＝「該 step 名在條文中**解析得到一個居所**」，⛔ 不是自我指涉的字面 grep：居所的定義是
「掃描面內某個標題含 `step` 的節，以 `- \\`<名>\\`：` 的條目形狀定義它」。封閉值域從 `wf.verbs._adopt`
`import` 取得（F-執行者-04 逐字「驗證器 `import` 使用，⛔ 不重打常數」）。
兩個負控都在 `tmp_path` 的合成樹上做（⛔ 不改本 repo）：刪掉任一 step 的條目後解析器必須少一項；
把本 repo 的 `areas` 改成與種子相同後 A2 的判準必須轉紅。
"""
import json
from pathlib import Path
import re
import shutil

from wf.context import FilesystemRulesSource, Provenance, rules_of
from wf.verbs._adopt import STEPS
from .test_compose_schema import ROOT
from .test_context_roots import RULE_DIRS

SCAN = ('core/*.md', 'roles/*.md', 'stages/*.md', 'modules/*/module.md', 'ADOPTION.md')
STEP_ENTRY = re.compile(r'^- `([a-z]+)`：', re.M)
HEADING = re.compile(r'^## (.+)$', re.M)
ADOPT_HOME = 'core/adopt.md'


def scan_paths(rules):
    return [path for pattern in SCAN for path in rules_of(rules).iter_assets(pattern)]


def sections(text):
    """(標題, 節內文) 依出現序；⛔ 不寫行號（F-共用-16）。"""
    marks = list(HEADING.finditer(text))
    return [(m[1].strip(), text[m.end():marks[i + 1].start() if i + 1 < len(marks) else len(text)])
            for i, m in enumerate(marks)]


def step_homes(rules):
    """{step 名: [`<檔>#<節>`…]}：掃描面內標題含 `step` 的節，逐條解析其條目。"""
    source, homes = rules_of(rules), {}
    for path in scan_paths(source):
        for heading, body in sections(source.read_text(path)):
            if 'step' not in heading:
                continue
            for name in STEP_ENTRY.findall(body):
                homes.setdefault(name, []).append(f'{path}#{heading}')
    return homes


def verb_domain(rules):
    """`core/verbs.md` §1 `snapshot` 列輸入欄裡 `--adopt` 之後被反引號包住的值域。"""
    row, = [line for line in rules_of(rules).read_text('core/verbs.md').splitlines()
            if line.startswith('| `snapshot')]
    return set(re.findall(r'`([a-z]+)`', row.split('|')[2].split('--adopt', 1)[1]))


def core_file_limit(rules):
    """行數上限只有一個居所＝`core/naming.md` §5「core 各檔」列；⛔ 不重打字面。"""
    row, = [line for line in rules_of(rules).read_text('core/naming.md').splitlines()
            if line.startswith('| core 各檔')]
    return int(re.search(r'(\d+) 行', row)[1])


def synthetic(tmp_path, name='synth'):
    """合成規則樹＝把交付檔當**資料**複製進來再驗；⛔ 不改本 repo、⛔ 不依賴 repo 歷史。"""
    root = tmp_path / name
    root.mkdir()
    for part in RULE_DIRS:
        shutil.copytree(ROOT / part, root / part)
    shutil.copy(ROOT / 'ADOPTION.md', root / 'ADOPTION.md')
    return FilesystemRulesSource(root, Provenance('cli', '--rules-root'))


def test_every_adopt_step_has_a_named_home(tmp_path):
    rules = FilesystemRulesSource(ROOT, Provenance('cli', '--rules-root'))
    homes = step_homes(rules)
    assert len(STEPS) == 5, STEPS                     # 基數恰 5：空集合或殘缺集合⛔ 不滿足本條
    for step in STEPS:
        assert homes.get(step), step
        assert len(homes[step]) == 1, (step, homes[step])
        print('STEP_HOME', step, homes[step][0])
    assert set(homes) == set(STEPS), sorted(set(homes) ^ set(STEPS))
    domain = verb_domain(rules)
    assert domain == set(STEPS), sorted(domain ^ set(STEPS))
    print('DOMAIN verbs.md', sorted(domain), 'adopt.md', sorted(homes), 'constant', sorted(STEPS))
    numbers = [heading.split(' ')[0] for heading, _ in sections(rules.read_text(ADOPT_HOME))]
    assert numbers == ['0', '1', '2', '3', '4', '5'], numbers  # 六個固定節齊備且順序不可換
    lines = len(rules.read_text(ADOPT_HOME).splitlines())
    assert lines <= core_file_limit(rules), (lines, core_file_limit(rules))
    print('ADOPT_MD sections', numbers, 'lines', lines, 'limit', core_file_limit(rules))


def test_the_step_home_resolver_is_effective(tmp_path):
    """負控（必須會響）：合成樹上刪掉任一 step 的條目後，解析器必須少掉那一項、其餘不變。"""
    for victim in STEPS:
        rules = synthetic(tmp_path, f'drop-{victim}')
        path = Path(rules.identity) / ADOPT_HOME
        kept = [line for line in path.read_text(encoding='utf-8').splitlines()
                if not line.startswith(f'- `{victim}`：')]
        path.write_text('\n'.join(kept) + '\n', encoding='utf-8')
        homes = step_homes(rules)
        assert victim not in homes, victim
        assert set(homes) == set(STEPS) - {victim}, (victim, sorted(homes))
        print('NEGATIVE_CONTROL dropped', victim, '->', sorted(homes))


def seed_areas(rules):
    text = rules_of(rules).read_text('ADOPTION.md')
    return json.loads(text.split('```json\n')[1].split('```')[0])['areas']


def test_seed_areas_are_not_this_repo_areas():
    rules = FilesystemRulesSource(ROOT, Provenance('cli', '--rules-root'))
    seed = seed_areas(rules)
    mine = json.loads((ROOT / '.wf/modules.json').read_text(encoding='utf-8'))['areas']
    assert seed != mine, (seed, mine)
    assert isinstance(seed, list) and seed and all(isinstance(a, str) for a in seed), seed
    print('AREAS seed', seed, 'repo', mine)
    section = dict(sections(rules.read_text('ADOPTION.md')))
    clause, = [line for line in section['2 · `.wf/modules.json` 種子'].splitlines()
               if line.startswith('- 種子裡的 `areas`')]
    assert '採用專案的需求方' in clause and '第一張卡 `open` 之前' in clause, clause
    print('WHO_AND_WHEN', clause)
    naming, = [line for line in rules.read_text('core/naming.md').splitlines()
               if line.startswith('- aiwf ')]
    assert '本 repo 自己的' in naming and '⛔ 不是採用專案的預設值' in naming, naming
    print('NAMING_§1', naming)


def test_the_areas_comparison_is_effective(tmp_path):
    """負控（必須會響）：把合成樹的 `.wf/modules.json` 改成與種子相同的 `areas` 後判準必須轉紅。"""
    rules = synthetic(tmp_path, 'areas')
    config = Path(rules.identity) / '.wf/modules.json'
    config.parent.mkdir(parents=True, exist_ok=True)
    seed = seed_areas(rules)
    config.write_text(json.dumps({'modules': [], 'areas': seed, 'project': None}), encoding='utf-8')
    same = json.loads(config.read_text(encoding='utf-8'))['areas']
    assert same == seed, (same, seed)  # 判準在這棵樹上不成立 ⇒ 判準有分辨力
    print('NEGATIVE_CONTROL areas_equal', same)


def tables(text):
    """(表頭欄名, 逐列欄值) 依出現序；⛔ 不解析非表格行、⛔ 不寫行號（F-共用-16）。"""
    found, rows = [], None
    for line in text.splitlines():
        if not line.strip().startswith('|'):
            rows = None
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if rows is None:
            rows = []
            found.append((tuple(cells), rows))
        elif set(''.join(cells)) - set('-: '):
            rows.append(cells)
    return found


def table_named(text, *headers):
    """取表頭欄名逐字等於 `headers` 的那一個表；⛔ 以欄名取、⛔ 不以出現位置取。"""
    matched = [rows for head, rows in tables(text) if head == headers]
    assert len(matched) == 1, (headers, [head for head, _ in tables(text)])
    return matched[0]


def repo_rules():
    return FilesystemRulesSource(ROOT, Provenance('cli', '--rules-root'))


def adopt_section(rules, number):
    """`core/adopt.md` 的第 number 節 (標題, 內文)；`rules` 給 None 即本 repo 的規則本體。"""
    source = repo_rules() if rules is None else rules_of(rules)
    found = [(heading, body) for heading, body in sections(source.read_text(ADOPT_HOME))
             if heading.split(' ')[0] == number]
    assert len(found) == 1, (number, found)
    return found[0]


SOURCE_ID = re.compile(r'`([a-z]+\.[a-z_]+)`')
RECONCILIATION_COLUMNS = ('列名', '左側（取源 ID）', '右側（取源 ID）', '粒度')
SMOKE_COLUMNS = ('項名', '取源 ID')
DEFECT_COLUMNS = ('缺陷代號', '⛔ 不合法的形狀')


def reconciliation_sources(rules=None):
    """`core/adopt.md` §1 對帳表的 (列名 → 取源 ID 集合)；⛔ 不重打。"""
    _, body = adopt_section(rules, '1')
    return {row[0].strip('`'): tuple(SOURCE_ID.findall(row[1]) + SOURCE_ID.findall(row[2]))
            for row in table_named(body, *RECONCILIATION_COLUMNS)}


def smoke_sources(rules=None):
    """`core/adopt.md` §3 smoke 取源表的 (項名 → 取源 ID 集合)；⛔ 不重打。"""
    _, body = adopt_section(rules, '3')
    return {row[0].strip('`'): tuple(SOURCE_ID.findall(row[1]))
            for row in table_named(body, *SMOKE_COLUMNS)}


def manifest_defects(rules=None):
    """`core/adopt.md` §2 結構宣告表的缺陷代號，依出現序。"""
    _, body = adopt_section(rules, '2')
    return tuple(row[0].strip('`') for row in table_named(body, *DEFECT_COLUMNS))


def consumers_of(mapping, source):
    return tuple(name for name, ids in mapping.items() if source in ids)


SYNTHETIC_EXCLUSIONS = ('本 repo 工作樹', '`.git/`', '`archive/`')
SYNTHETIC_INDEPENDENCE = '⛔ 不依賴本 repo 歷史存在'


def test_the_synthetic_tree_definition_is_a_named_home():
    """A1 後半：`core/adopt.md` §0 是「合成 consumer 樹」的具名居所，逐字含三個排除項與獨立性條文，
    且其餘各條引用的掃描面字串與該段的段名逐字一致。"""
    rules = FilesystemRulesSource(ROOT, Provenance('cli', '--rules-root'))
    heading, body = adopt_section(rules, '0')
    name = heading.split('·')[1].strip()
    assert body.strip(), heading
    for token in SYNTHETIC_EXCLUSIONS:
        assert token in body, (token, body)
    assert SYNTHETIC_INDEPENDENCE in body, body
    quoted = re.search(r'掃描面＝(.+?)（`core/adopt\.md` §0）', body)
    assert quoted and quoted[1] == name, (name, quoted and quoted[1])
    print('SYNTHETIC_TREE_HOME', f'{ADOPT_HOME}#{heading}', 'name', name,
          'exclusions', list(SYNTHETIC_EXCLUSIONS), 'independence', SYNTHETIC_INDEPENDENCE)


def test_the_synthetic_tree_definition_check_is_effective(tmp_path):
    """負控（必須會響）：合成副本內刪掉 §0 的任一排除項或獨立性條文後，同一個判準必須轉紅。"""
    for victim in (*SYNTHETIC_EXCLUSIONS, SYNTHETIC_INDEPENDENCE):
        rules = synthetic(tmp_path, f'zero-{abs(hash(victim))}')
        path = Path(rules.identity) / ADOPT_HOME
        kept = [line for line in path.read_text(encoding='utf-8').splitlines() if victim not in line]
        path.write_text('\n'.join(kept) + '\n', encoding='utf-8')
        _, body = adopt_section(rules, '0')
        assert victim not in body, victim
        print('NEGATIVE_CONTROL synthetic_definition dropped', victim)
