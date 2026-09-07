"""WF-STEP6-S05 交回證據；core/return.md self_run、roles/conduct-common.md §1–2。"""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from .test_compose_schema import ROOT

DEST = ROOT / 'cli/tests/fixtures/s05-evidence'


def capture(name, args, **extra):
    result = subprocess.run(args, cwd=ROOT, env=dict(os.environ, PYTHONPATH='cli/src', **extra),
                            capture_output=True, text=True)
    for suffix, text in (('stdout', result.stdout), ('stderr', result.stderr), ('rc', str(result.returncode) + '\n')):
        (DEST / f'{name}.{suffix}').write_text(text)
    command = ' '.join([f'{k}={shlex.quote(v)}' for k, v in {'PYTHONPATH': 'cli/src', **extra}.items()])
    command += ' ' + shlex.join(args)
    print(name, 'rc=', result.returncode, flush=True)
    return {'command': command, 'rc': result.returncode, 'stdout': name + '.stdout', 'stderr': name + '.stderr'}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    commands = []
    commands.append(capture('negative', [sys.executable, '-m', 'pytest', 'cli/tests/test_write_negative.py', '-q', '-s']))
    commands.append(capture('offline', [sys.executable, '-m', 'pytest', 'cli/tests', '-q',
                                       '-p', 'cli.tests.test_gh_scope'], WF_S05_OFFLINE='1'))
    commands.append(capture('online', [sys.executable, '-m', 'pytest', 'cli/tests', '-q'], WF_S05_LIVE='1'))
    commands.append(capture('inventory', [sys.executable, '-m', 'pytest', '-q', '-s',
        'cli/tests/test_compose_blocks.py::test_repo_inventory', 'cli/tests/test_gh_scope.py',
        'cli/tests/test_write_flow.py::test_projection_original_order_and_runtime_reload',
        'cli/tests/test_gh_write_recording.py::test_recorded_prose_and_restore_hash',
        'cli/tests/test_gh_write_recording.py::test_recorded_read_inventories',
        'cli/tests/test_gh_write_recording.py::test_recordings_secret_negative_control']))
    commands.append(capture('compile', [sys.executable, '-m', 'compileall', '-q', 'cli/src/wf']))
    paths = sorted((ROOT / 'cli/src/wf').rglob('*.py'))
    counts = {str(p.relative_to(ROOT)): len(p.read_text().splitlines()) for p in paths}
    delta = subprocess.run(['git', 'diff', '--numstat', '--', 'cli/src/wf'], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout
    added = sum(int(row.split('\t')[0]) for row in delta.splitlines())
    metrics = {'source_lines': counts, 'total': sum(counts.values()), 'slice_added': added, 'diff_numstat': delta}
    assert metrics['total'] <= 3000 and added <= 480
    (DEST / 'source-metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n')
    (DEST / 'commands.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(metrics, ensure_ascii=False), flush=True)
    assert all(command['rc'] == 0 for command in commands)


if __name__ == '__main__':
    main()
