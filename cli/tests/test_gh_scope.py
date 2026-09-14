"""消費 core/verbs.md §2、roles/conduct-common.md §1；src 與依賴邊界。"""
import ast
import json
import sys

import pytest

from .test_compose_schema import ROOT
from .test_gh_write_recording import ensure_clean

NETWORK = {'subprocess', 'urllib', 'socket', 'http', 'requests', 'httpx', 'aiohttp', 'ftplib'}

# 刻意：本常數是暫行值。正式的 core／module-runtime 雙桶邊界與聚合上限歸 WF-011。
# 本次⛔ 不移除總量護欄。⛔ 不得推出「聚合後盾可以拿掉」或「分桶已經建立」。
# 上限只有這一個字面居所：真掃描與合成樹負控都從這裡取值，⛔ 不重打字面。
TOTAL_LIMIT = 5000


def aggregate(root):
    """遞迴 *.py 的聚合行數與 ≤ TOTAL_LIMIT 的判定。

    真掃描據以判過與判不過的比較函式就是這一個；合成樹負控用的也是這一個（同一函式，⛔ 不是複製品）。
    """
    total = sum(len(path.read_text().splitlines()) for path in sorted(root.rglob('*.py')))
    return total, total <= TOTAL_LIMIT


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
        total += count
        print('SRC', path.relative_to(ROOT), count, longest, json.dumps(sorted(names)))
    independent, within = aggregate(ROOT / 'cli/src/wf')
    assert independent == total, (independent, total)  # 逐檔迴圈累加與比較函式須獨立算出同一值
    assert within, (total, TOTAL_LIMIT)  # 寬鬆後盾；分桶由單檔與函式兩個觸發器守
    print('SRC_FILES', len(paths), 'SRC_TOTAL', total)
    for relative in ('compose/blocks.py', 'compose/project_config.py', 'gh/client.py', 'gh/writes.py', 'verbs/_write.py'):
        doc = ast.get_docstring(ast.parse((ROOT / 'cli/src/wf' / relative).read_text()))
        assert doc and '.md' in doc and '§' in doc, relative


def test_total_line_budget_boundary_negative_control(tmp_path):
    """合成樹負控：聚合恰 TOTAL_LIMIT 行判過、恰 TOTAL_LIMIT + 1 行判不過。

    兩棵樹的行數由 TOTAL_LIMIT 算出，⛔ 不重打任何上限字面；判過與判不過都由 aggregate 決定，
    與真掃描共用同一個比較函式。非 *.py 的檔放進樹裡，證明母體真的只收 *.py。
    """
    def tree(name, lines):
        root = tmp_path / name
        (root / 'pkg').mkdir(parents=True)
        head = lines // 2
        (root / 'a.py').write_text('\n'.join(['x = 0'] * head) + '\n')
        (root / 'pkg' / 'b.py').write_text('\n'.join(['y = 0'] * (lines - head)) + '\n')
        (root / 'pkg' / 'noise.txt').write_text('\n'.join(['z'] * lines) + '\n')
        return root

    assert aggregate(tree('at_limit', TOTAL_LIMIT)) == (TOTAL_LIMIT, True)
    print('TOTAL_AT_LIMIT', TOTAL_LIMIT, 'PASS')
    assert aggregate(tree('over_limit', TOTAL_LIMIT + 1)) == (TOTAL_LIMIT + 1, False)
    print('TOTAL_OVER_LIMIT', TOTAL_LIMIT + 1, 'FAIL')


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
