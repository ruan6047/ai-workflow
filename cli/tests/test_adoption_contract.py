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
    for step in STEPS:
        assert homes.get(step), step
        assert len(homes[step]) == 1, (step, homes[step])
        print('STEP_HOME', step, homes[step][0])
    assert set(homes) == set(STEPS), sorted(set(homes) ^ set(STEPS))
    domain = verb_domain(rules)
    assert domain == set(STEPS), sorted(domain ^ set(STEPS))
    print('DOMAIN verbs.md', sorted(domain), 'adopt.md', sorted(homes), 'constant', sorted(STEPS))
    numbers = [heading.split(' ')[0] for heading, _ in sections(rules.read_text(ADOPT_HOME))]
    assert numbers == ['1', '2', '3', '4', '5'], numbers  # 五個固定節齊備且順序不可換
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
