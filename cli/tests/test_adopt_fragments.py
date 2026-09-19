"""WF-015 A9–A14：片段資產（承載檔內的一個 job）。消費 core/adopt.md §2（片段表、片段資產判定、
`path` 兩類文法、頂層骨架）／§3 `install`／§5（位元組級可逆）。

片段名集合、承載檔與片段來源檔三者皆由 `wf.verbs._adopt` `import` 或由 `core/adopt.md` 的片段表解析
取得（F-執行者-04 逐字「驗證器 `import` 使用，⛔ 不重打常數」）；兩側比對相等才成立。
合成 consumer 樹＝`test_adopt_gitlink.py` 的 `adopted_consumer`（`core/adopt.md` §0）。
`.github/workflows/ci.yml` 在本卡是唯讀端：本檔對它只讀、只比對，⛔ 不改。
"""
import json
from pathlib import Path
import subprocess
import tomllib

import pytest

from wf.verbs import _adopt
from wf.verbs.main import main
from .fakes import FakeGhClient
from .test_adopt_gitlink import adopted_consumer
from .test_adoption_contract import adopt_section, table_named
from .test_compose_schema import ROOT
from .test_context_roots import git_env

MERGE_BASE = '372fe7f3bcdea7d7681910938387fd36a730c369'
CI = '.github/workflows/ci.yml'
DELTA = 'submodules: true'
CHECKOUT = 'actions/checkout@'
REQUIRED_FRAGMENTS = ('secret-scan', 'commit-trailer')      # A10 逐字要求必含的兩名
EXCLUDED_FRAGMENTS = ('reachability', 'cli-tests')          # A10 明示排除的兩名
FRAGMENT_COLUMNS = ('片段名', '承載檔', '片段來源檔', '是否帶 `actions/setup-python`')


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


def run_step(consumer, step, client=None):
    client = FakeGhClient() if client is None else client
    rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', step],
              client=client, root=None, env={})
    return rc, client


def fragment_table(rules=None):
    """`core/adopt.md` §2 的「consumer 面 job 片段表」：以欄名取表、⛔ 不以出現位置取。"""
    from wf.context import FilesystemRulesSource, Provenance
    rules = FilesystemRulesSource(ROOT, Provenance('cli', '--rules-root')) if rules is None else rules
    _, body = adopt_section(rules, '2')
    return [[cell.strip('`') for cell in row] for row in table_named(body, *FRAGMENT_COLUMNS)]


def changed_files():
    """本卡分支對合併基底的 `git diff --name-only`；基底物件取不到時**失敗並印出原因**，⛔ 不 skip。"""
    done = subprocess.run(['git', '-C', str(ROOT), 'diff', '--name-only', f'{MERGE_BASE}..HEAD'],
                          capture_output=True, text=True)
    assert done.returncode == 0, (done.returncode, done.stderr)
    return [line for line in done.stdout.splitlines() if line]


def manifest_of(consumer):
    return json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))


def carrier_text(consumer):
    return (consumer / _adopt.CARRIER).read_text(encoding='utf-8')


def top_keys(text):
    return tuple(line.split(':')[0] for line in text.splitlines()
                 if line.strip() and not line.startswith((' ', '#')) and ':' in line)


def children_of(text, key):
    lines, found = text.splitlines(), []
    start = next(i for i, line in enumerate(lines) if line.strip() == f'{key}:' and not line.startswith(' '))
    for line in lines[start + 1:]:
        if not line.strip():
            continue
        if not line.startswith(' '):
            break
        if len(line) - len(line.lstrip(' ')) == 2:
            found.append(line.strip().rstrip(':'))
    return tuple(found)


def carrier_with(consumer, body):
    path = consumer / _adopt.CARRIER
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding='utf-8')
    return path.read_bytes()


CONSUMER_JOB = """name: consumer own
on:
  push:

jobs:
  mine:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
"""
NO_JOB = """name: consumer own
# 只有設定與註解，⛔ 無任何 job
on:
  push:

permissions:
  contents: read
"""


# ── A10：片段集合的下界與實作常數獨立 ──────────────────────────────────────────────
def test_the_required_fragment_set_has_an_independent_lower_bound(tmp_path, env, capsys):
    rows = fragment_table()
    declared = [row[0] for row in rows]
    assert set(declared) == set(_adopt.FRAGMENTS), sorted(set(declared) ^ set(_adopt.FRAGMENTS))
    assert set(REQUIRED_FRAGMENTS) <= set(declared), (REQUIRED_FRAGMENTS, declared)
    assert not set(EXCLUDED_FRAGMENTS) & set(declared), declared
    assert {row[1] for row in rows} == {_adopt.CARRIER}, rows
    assert {row[2] for row in rows} == {_adopt.FRAGMENT_SOURCE}, rows
    adoption = (ROOT / 'ADOPTION.md').read_text(encoding='utf-8')
    clause, = [line for line in adoption.splitlines() if line.startswith('- required status checks')]
    for name in REQUIRED_FRAGMENTS:
        assert f'`{name}`' in clause, (name, clause)
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='frag-lower')
    rc, _ = run_step(consumer, 'install')
    capsys.readouterr()
    assert rc == 0
    present = _adopt.job_names(carrier_text(consumer))
    registered = {e['path'] for e in _adopt.entries_of(manifest_of(consumer), _adopt.OWNERSHIPS[0])}
    for name in REQUIRED_FRAGMENTS:
        assert name in present, (name, present)
        assert f'{_adopt.CARRIER}#{name}' in registered, (name, sorted(registered))
    print('FRAGMENT_TABLE', rows, 'constant', list(_adopt.FRAGMENTS), 'landed', list(present))


def test_the_fragment_table_parser_is_effective(tmp_path):
    """負控（必須會響）：合成副本內刪掉表格任一列後，解析出的片段名集合必須少一項。"""
    from .test_adoption_contract import synthetic
    for victim in _adopt.FRAGMENTS:
        rules = synthetic(tmp_path, f'frag-{victim}')
        path = Path(rules.identity) / 'core/adopt.md'
        kept = [line for line in path.read_text(encoding='utf-8').splitlines()
                if not line.startswith(f'| `{victim}` |')]
        path.write_text('\n'.join(kept) + '\n', encoding='utf-8')
        names = {row[0] for row in fragment_table(rules)}
        assert names == set(_adopt.FRAGMENTS) - {victim}, (victim, names)
        print('NEGATIVE_CONTROL fragment_table dropped', victim, '->', sorted(names))


# ── A9：片段以 job 粒度登記，digest 的前像是片段本身 ────────────────────────────────
def test_fragments_are_registered_at_job_granularity(tmp_path, env, capsys):
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name='frag-grain')
    before = carrier_with(consumer, CONSUMER_JOB)
    rc, _ = run_step(consumer, 'install')
    capsys.readouterr()
    assert rc == 0
    version = tomllib.loads((rules / _adopt.VERSION_HOME).read_text(encoding='utf-8'))['project']['version']
    entries = {e['path']: e for e in manifest_of(consumer)['assets']}
    source_text = (rules / _adopt.FRAGMENT_SOURCE).read_text(encoding='utf-8')
    landed = carrier_text(consumer)
    for name in _adopt.FRAGMENTS:
        path = f'{_adopt.CARRIER}#{name}'
        matched = [e for e in manifest_of(consumer)['assets'] if e['path'] == path]
        assert len(matched) == 1, (path, matched)
        entry = entries[path]
        assert _adopt.fragment_of(path) == (_adopt.CARRIER, name), path
        assert entry['ownership'] == _adopt.OWNERSHIPS[0] and entry['pin'] == version, entry
        block = _adopt.job_text(source_text, name)
        assert _adopt.job_text(landed, name) == block, name          # 逐字落地
        assert entry['digest'] == _adopt.digest_of(block.encode('utf-8')), entry
    assert before != (consumer / _adopt.CARRIER).read_bytes()        # install 確實動了承載檔
    mine = _adopt.job_text(landed, 'mine')
    edited = landed.replace(mine, mine.replace('echo hi', 'echo changed'))
    (consumer / _adopt.CARRIER).write_text(edited, encoding='utf-8')
    for name in _adopt.FRAGMENTS:
        path = f'{_adopt.CARRIER}#{name}'
        assert _adopt.asset_digest(consumer, path) == entries[path]['digest'], path
    print('FRAGMENT_DIGEST_STABLE', {n: entries[f'{_adopt.CARRIER}#{n}']['digest'][:19]
                                     for n in _adopt.FRAGMENTS})


def test_the_carrier_and_source_values_have_exactly_one_literal_home():
    """A9 後半：`_adopt` 層對承載檔與片段來源檔兩個值各只有一個字面居所，且⛔ 不由設定鍵宣告。"""
    sources = sorted((ROOT / 'cli/src/wf').rglob('*.py'))
    for value in (_adopt.CARRIER, _adopt.FRAGMENT_SOURCE):
        homes = [p.relative_to(ROOT).as_posix() for p in sources
                 if f"'{value}'" in p.read_text(encoding='utf-8')]
        assert homes == ['cli/src/wf/verbs/_adopt_manifest.py'], (value, homes)
    config_home = (ROOT / 'cli/src/wf/compose/project_config.py').read_text(encoding='utf-8')
    for value in (_adopt.CARRIER, _adopt.FRAGMENT_SOURCE, 'carrier', 'fragment'):
        assert value not in config_home, value
    seed = json.loads((ROOT / 'ADOPTION.md').read_text(encoding='utf-8')
                      .split('```json\n')[1].split('```')[0])
    assert not [key for key in seed if 'carrier' in key or 'fragment' in key], sorted(seed)
    print('LITERAL_HOMES', _adopt.CARRIER, _adopt.FRAGMENT_SOURCE, '-> _adopt_manifest.py only')


# ── A11：新建承載檔是一個完整 workflow，骨架逐字取自片段來源檔 ──────────────────────
def test_a_new_carrier_file_is_a_complete_workflow(tmp_path, env, capsys):
    fresh, rules, _, _, _ = adopted_consumer(tmp_path, env, name='frag-new')
    assert not (fresh / _adopt.CARRIER).exists()
    assert run_step(fresh, 'install')[0] == 0
    capsys.readouterr()
    text = carrier_text(fresh)
    keys = top_keys(text)
    for key in ('name', 'on', 'permissions', 'jobs'):
        assert key in keys, (key, keys)
    events = children_of(text, 'on')
    assert 'push' in events and 'pull_request' in events, events
    source_text = (rules / _adopt.FRAGMENT_SOURCE).read_text(encoding='utf-8')
    assert text.startswith(_adopt.skeleton_of(source_text)), text[:200]
    print('NEW_CARRIER keys', keys, 'on', events)
    kept, _, _, _, _ = adopted_consumer(tmp_path, env, name='frag-keep')
    before = carrier_with(kept, CONSUMER_JOB)
    assert run_step(kept, 'install')[0] == 0
    capsys.readouterr()
    after = (kept / _adopt.CARRIER).read_bytes()
    head = before.split(b'jobs:')[0]
    assert after.startswith(head), (head, after[:len(head)])        # 既有頂層骨架位元組逐一不變
    assert _adopt.job_text(after.decode('utf-8'), 'mine') == _adopt.job_text(CONSUMER_JOB, 'mine')
    print('EXISTING_CARRIER skeleton_unchanged', len(head), 'bytes')


# ── A12：⛔ 不覆寫承載檔內未登記的同名 job ────────────────────────────────────────
def test_install_never_overwrites_a_foreign_job(tmp_path, env, capsys):
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='frag-foreign')
    foreign = CONSUMER_JOB.replace('  mine:', f'  {_adopt.FRAGMENTS[0]}:')
    before = carrier_with(consumer, foreign)
    rc, _ = run_step(consumer, 'install')
    out = capsys.readouterr().out
    assert rc == 0
    assert (consumer / _adopt.CARRIER).read_bytes() == before        # 位元組逐一不變
    registered = {e['path'] for e in _adopt.entries_of(manifest_of(consumer), _adopt.OWNERSHIPS[0])}
    assert not [p for p in registered if p.startswith(f'{_adopt.CARRIER}#')], sorted(registered)
    explained = [line for line in out.splitlines() if _adopt.FOREIGN_JOB in line]
    assert explained, out                                            # 印一行說明
    print('FOREIGN_JOB_KEPT', explained)


# ── A13：install 與 deactivate 對承載檔位元組級可逆 ───────────────────────────────
@pytest.mark.parametrize('case,body', [('absent', None), ('consumer_job', CONSUMER_JOB),
                                       ('no_job', NO_JOB)])
def test_install_then_deactivate_is_byte_reversible(tmp_path, env, capsys, case, body):
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name=f'frag-rev-{case}')
    before = None if body is None else carrier_with(consumer, body)
    assert run_step(consumer, 'install')[0] == 0
    capsys.readouterr()
    assert (consumer / _adopt.CARRIER).is_file()
    for name in _adopt.FRAGMENTS:
        assert name in _adopt.job_names(carrier_text(consumer)), (case, name)
    assert run_step(consumer, 'deactivate')[0] == 0
    capsys.readouterr()
    if before is None:
        assert not (consumer / _adopt.CARRIER).exists(), case
    else:
        assert (consumer / _adopt.CARRIER).is_file(), case
        assert (consumer / _adopt.CARRIER).read_bytes() == before, case
    print('REVERSIBLE', case, 'before', None if before is None else len(before),
          'exists_after', (consumer / _adopt.CARRIER).exists())


# ── A14：consumer 面片段與框架自身 CI 的同名 job 同步 ─────────────────────────────
def job_lines(text, name):
    block = _adopt.job_text(text, name)
    assert block is not None, name
    return block.splitlines()


def declared_delta(ci_lines, consumer_lines):
    """回 (consumer 側多出的行, 其餘差異)；⛔ 不以 difflib 的相似度判，逐行走一次。"""
    extra, mismatched, i = [], [], 0
    for line in consumer_lines:
        if i < len(ci_lines) and line == ci_lines[i]:
            i += 1
        else:
            extra.append(line)
    if i != len(ci_lines):
        mismatched = ci_lines[i:]
    return extra, mismatched


def in_checkout_with_block(lines, line):
    """該行落在 `actions/checkout` 步驟的 `with:` 區塊內。"""
    index = lines.index(line)
    saw_checkout = False
    for earlier in lines[:index]:
        if CHECKOUT in earlier:
            saw_checkout = True
        elif saw_checkout and earlier.strip().startswith('- '):
            saw_checkout = False
    return saw_checkout and any(l.strip() == 'with:' for l in lines[:index][::-1][:6])


def test_consumer_fragments_differ_from_ci_by_exactly_the_declared_delta():
    rows = fragment_table()
    source_path, = {row[2] for row in rows}
    ci_text = (ROOT / CI).read_text(encoding='utf-8')
    source_text = (ROOT / source_path).read_text(encoding='utf-8')
    for name in sorted({row[0] for row in rows}):
        ci_lines, consumer_lines = job_lines(ci_text, name), job_lines(source_text, name)
        extra, mismatched = declared_delta(ci_lines, consumer_lines)
        assert mismatched == [], (name, mismatched)
        assert [line.strip() for line in extra] == [DELTA], (name, extra)
        assert in_checkout_with_block(consumer_lines, extra[0]), (name, extra)
        print('DELTA', name, 'extra', extra, 'ci_lines', len(ci_lines))
    assert CI not in changed_files(), CI      # 唯讀端：本卡分支⛔ 不改它
    for name in EXCLUDED_FRAGMENTS:           # 明示排除：⛔ 不進比對母體
        assert name not in {row[0] for row in rows}, name
    print('READONLY_CI_UNCHANGED', CI, 'excluded', list(EXCLUDED_FRAGMENTS))


@pytest.mark.parametrize('side', ['ci', 'consumer'])
def test_the_delta_comparison_is_effective(tmp_path, side):
    """負控（必須會響）：在暫存副本內改任一側的一行⛔ 非 delta 內容後，同一個判準必須轉紅。"""
    name = _adopt.FRAGMENTS[0]
    ci_text = (ROOT / CI).read_text(encoding='utf-8')
    source_text = (ROOT / _adopt.FRAGMENT_SOURCE).read_text(encoding='utf-8')
    if side == 'ci':
        ci_text = ci_text.replace('timeout-minutes: 10', 'timeout-minutes: 11', 1)
    else:
        source_text = source_text.replace('timeout-minutes: 10', 'timeout-minutes: 11', 1)
    extra, mismatched = declared_delta(job_lines(ci_text, name), job_lines(source_text, name))
    assert mismatched or [line.strip() for line in extra] != [DELTA], (side, extra, mismatched)
    print('NEGATIVE_CONTROL delta', side, 'extra', extra, 'mismatched', mismatched)
