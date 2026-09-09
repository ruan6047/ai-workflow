"""消費 roles/conduct-common.md §1、core/verbs.md §1 edit；突變只在子行程記憶體。"""
import os
from pathlib import Path
import subprocess
import sys

import pytest

from .test_compose_schema import ROOT

MUTATIONS = {
    'version': ("updated['spec_version'] += 1", "updated['spec_version'] += 0", 'test_spec_version'),
    'hash': ("return hashlib.sha256(raw.encode('utf-8')).hexdigest()", "return 'broken'", 'test_hash_and_non_spec_version'),
    'same': ("if key in current and _equal(current[key], value):", "if False:", 'test_same_value_is_silent'),
    'review': ("'edit during review')", "'broken')", 'test_review_comments'),
}


def pytest_sessionstart(session):
    mutation = os.environ.get('WF_EDIT_MUTATION')
    if not mutation:
        return
    from wf.verbs import edit
    old, new, _ = MUTATIONS[mutation]
    source = Path(edit.__file__).read_text()
    assert source.count(old) == 1
    exec(compile(source.replace(old, new), edit.__file__, 'exec'), edit.__dict__)
    print('MUTATION_APPLIED', mutation)


@pytest.mark.parametrize('mutation', MUTATIONS)
def test_mutation_fails_acceptance(mutation):
    target = MUTATIONS[mutation][2]
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-s', '--tb=no',
        '-p', 'cli.tests.test_edit_negative', 'cli/tests/test_edit_flow.py', '-k', target],
        cwd=ROOT, env=dict(os.environ, PYTHONPATH='cli/src', WF_EDIT_MUTATION=mutation),
        capture_output=True, text=True)
    print(result.stdout, end='')
    print(result.stderr, end='')
    assert result.returncode == 1
    assert 'MUTATION_APPLIED ' + mutation in result.stdout
    assert 'FAILED cli/tests/test_edit_flow.py::' + target in result.stdout
