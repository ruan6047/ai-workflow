"""消費 core/verbs.md §2、roles/conduct-common.md §1；src 與依賴邊界。"""
import ast
import importlib.util
import json
import sys

import pytest

from .test_compose_schema import ROOT
from .test_gh_write_recording import ensure_clean

NETWORK = {'subprocess', 'urllib', 'socket', 'http', 'requests', 'httpx', 'aiohttp', 'ftplib'}


def _budget():
    """門檻與比較函式只有一個居所＝`.github/scripts/source_budget.py`；此處 import 使用，⛔ 不重打。"""
    path = ROOT / '.github/scripts/source_budget.py'
    spec = importlib.util.spec_from_file_location('wf_source_budget', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BUDGET = _budget()
TOTAL_LIMIT, aggregate = _BUDGET.TOTAL_LIMIT, _BUDGET.aggregate


def imports(text):
    found = set()
    for node in ast.walk(ast.parse(text, feature_version=(3, 11))):
        if isinstance(node, ast.Import):
            found.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level:
            found.add(node.module.split('.')[0])
    return found


def test_source_inventory_and_negative_controls():
    assert imports('import socket\nimport requests') & NETWORK == {'socket', 'requests'}
    assert imports('import requests') - sys.stdlib_module_names == {'requests'}
    print('IMPORT_NEGATIVE_CONTROL socket, requests detected')
    paths = sorted((ROOT / 'cli/src/wf').rglob('*.py'))
    total = 0
    for path in paths:
        source = path.read_text()
        names = imports(source)
        assert not (names - sys.stdlib_module_names - {'wf'}), path
        if path.parent.name != 'gh':
            assert not names & NETWORK, path
        count = len(source.splitlines())
        assert count <= 400, (path, count)  # 單檔觸發器；觸發後可決定不拆，理由寫交回單
        longest = max((f.end_lineno - f.lineno + 1 for f in ast.walk(ast.parse(source))
                       if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))), default=0)
        assert longest <= 150, (path, longest)  # 單一函式觸發器（舊 wfcli 的 god function 形狀）
        total += sum(1 for line in source.splitlines() if line.strip())  # 聚合口徑排除空行
        print('SRC', path.relative_to(ROOT), count, longest, json.dumps(sorted(names)))
    independent, reached = aggregate(ROOT / 'cli/src/wf')
    assert independent == total, (independent, total)  # 逐檔迴圈累加與比較函式須獨立算出同一值
    # 刻意⛔ 無 `assert within`：聚合值在**本函式**內⛔ 無獨立的門檻斷言，只印出來供人讀。
    # ⛔ 但不得推出「達門檻⛔ 不會轉紅」——那是錯的，且已誤導過兩個讀者（WF-015 iteration 6 失誤登記）。
    # 同檔 `test_source_budget_script_is_a_soft_warning` 的**第一段**對**真樹**跑 `_BUDGET.main([...])`
    # 並斷言 `'::warning' not in quiet`：`cli/src/wf` 一旦達 8,000 行治理門檻，那一行就失敗、本檔轉紅、
    # CI 的 cli-tests job 跟著紅。腳本 `rc` 恆 0 是**另一件事**（同函式第二段以 monkeypatch 樁驗的），
    # 兩者⛔ 不得互相冒充。⇒ 對 `cli/src/wf` 而言 8,000 是**硬上限**、⛔ 不是可以超過的軟警示。
    # 說明義務（stages/planning.md §5、stages/review.md §5）是門檻**之下**的治理、⛔ 不是超過它的豁免；
    # 分桶另由單檔 400 行與單一函式 150 行兩個觸發器守。
    print('SRC_FILES', len(paths), 'SRC_TOTAL', total, 'LIMIT', TOTAL_LIMIT, 'REACHED', reached)
    for relative in ('compose/blocks.py', 'compose/project_config.py', 'gh/client.py', 'gh/writes.py', 'verbs/_write.py'):
        doc = ast.get_docstring(ast.parse((ROOT / 'cli/src/wf' / relative).read_text()))
        assert doc and '.md' in doc and '§' in doc, relative


def test_total_line_budget_boundary_negative_control(tmp_path):
    """合成樹負控：聚合恰 TOTAL_LIMIT 行判達警示、TOTAL_LIMIT − 1 行判未達。

    兩棵樹的行數由 TOTAL_LIMIT 算出，⛔ 不重打任何上限字面；判達與判未達都由 aggregate 決定，
    與真掃描共用同一個比較函式。非 *.py 的檔與空行放進樹裡，證明母體只收 *.py 且口徑排除空行。
    """
    def tree(name, lines):
        root = tmp_path / name
        (root / 'pkg').mkdir(parents=True)
        head = lines // 2
        (root / 'a.py').write_text('\n'.join(['x = 0'] * head + [''] * 11) + '\n')
        (root / 'pkg' / 'b.py').write_text('\n'.join(['y = 0'] * (lines - head)) + '\n')
        (root / 'pkg' / 'noise.txt').write_text('\n'.join(['z'] * lines) + '\n')
        return root

    assert aggregate(tree('at_limit', TOTAL_LIMIT)) == (TOTAL_LIMIT, True)
    print('TOTAL_AT_LIMIT', TOTAL_LIMIT, 'WARN')
    assert aggregate(tree('over_limit', TOTAL_LIMIT + 1)) == (TOTAL_LIMIT + 1, True)
    print('TOTAL_OVER_LIMIT', TOTAL_LIMIT + 1, 'WARN')
    assert aggregate(tree('under_limit', TOTAL_LIMIT - 1)) == (TOTAL_LIMIT - 1, False)
    print('TOTAL_UNDER_LIMIT', TOTAL_LIMIT - 1, 'QUIET')


def test_source_budget_script_is_a_soft_warning(capsys, monkeypatch):
    """腳本本身：rc 恆 0；達門檻印含當前行數與門檻的 ::warning:: 行，未達不印。

    負控用 monkeypatch 把 aggregate 換成回報「已達」的樁——⛔ 不改真樹、⛔ 不重打門檻字面。
    """
    assert _BUDGET.main(['source_budget.py']) == 0
    quiet = capsys.readouterr().out
    assert '::warning' not in quiet, quiet
    monkeypatch.setattr(_BUDGET, 'aggregate', lambda root: (TOTAL_LIMIT + 7, True))
    assert _BUDGET.main(['source_budget.py']) == 0  # 達門檻仍 rc=0：軟警示⛔ 不擋
    loud = capsys.readouterr().out
    assert '::warning' in loud and str(TOTAL_LIMIT + 7) in loud and str(TOTAL_LIMIT) in loud, loud
    print('SOURCE_BUDGET_SOFT_WARNING', repr(quiet.strip()), repr(loud.strip()))


def test_source_budget_selftest_passes():
    assert _BUDGET.main(['source_budget.py', '--selftest']) == 0


def test_all_gh_fixtures_are_secret_free():
    with pytest.raises(ValueError, match='憑證'):
        ensure_clean({'body': 'github_pat_' + 'Z' * 30})
    paths = sorted(path for directory in ('gh', 's05')
                   for path in (ROOT / 'cli/tests/fixtures' / directory).glob('*.json'))
    for path in paths:
        ensure_clean(json.loads(path.read_text()))
        print('SECRET_SCANNED', path.relative_to(ROOT))
    assert paths
    print('SECRET_SCANNED_FILES', len(paths))


def test_verbs_layout_matches_the_dispatch_table():
    """verbs/ 的結構不變式：不以 _ 開頭的檔＝一個動詞，必在 DISPATCH 且導出 run。
    HELPERS 是明列的例外（brief 的第二個 --for 目標、move 的模組層），⛔ 不得默默增加。"""
    from wf.verbs.main import DISPATCH
    HELPERS = {'main.py', 'closeout.py', 'move_modules.py'}
    files = {p.name for p in (ROOT / 'cli/src/wf/verbs').glob('*.py')
             if not p.name.startswith('_')}
    assert files - HELPERS == {f'{verb}.py' for verb in DISPATCH}, sorted(files - HELPERS)
    for verb, module in DISPATCH.items():
        assert callable(getattr(module, 'run', None)), verb
    assert not [name for name in DISPATCH if f'{name}.py' in HELPERS]
    print('VERBS_LAYOUT', len(DISPATCH), sorted(files - HELPERS))
