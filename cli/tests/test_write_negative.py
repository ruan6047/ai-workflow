"""core/verbs.md §2 與 roles/conduct-common.md §1：直接破壞被測流程，驗證測試會 FAIL。"""
import os
from pathlib import Path
import subprocess
import sys

import pytest

from .test_compose_schema import ROOT


def pytest_sessionstart(session):
    mutation = os.environ.get('WF_S05_MUTATION')
    if not mutation:
        return
    from wf.verbs import _write
    source = Path(_write.__file__).read_text()
    if mutation == 'readback':
        old = 'if not _equal(actual_card, card) or not _equal(actual, values):'
        new = 'if False:'
    elif mutation == 'prevalidation':
        old = "errors = validate(card, compose_schema(catalog, 'wf-card', enabled_modules))"
        new = 'errors = []'
    elif mutation == 'order':
        old = '''    try:
        client.update_card_body(number, card, create=create)
    except CardBodyError as exc:
        return reject(client, number, 'D3', str(exc), printed)
    if write_projection:
        for name, value in values.items():
            client.set_project_field(project, item_id, name, value)
'''
        new = '''    if write_projection:
        for name, value in values.items():
            client.set_project_field(project, item_id, name, value)
    try:
        client.update_card_body(number, card, create=create)
    except CardBodyError as exc:
        return reject(client, number, 'D3', str(exc), printed)
'''
    else:
        raise AssertionError(mutation)
    assert source.count(old) == 1
    exec(compile(source.replace(old, new), _write.__file__, 'exec'), _write.__dict__)
    print('MUTATION_APPLIED', mutation)


@pytest.mark.parametrize('mutation,target', [
    ('readback', 'test_readback_mismatch_rejects_once'),
    ('prevalidation', 'test_prevalidation_rejects_before_data_writes[change0]'),
    ('order', 'test_write_order_and_equal_readback'),
])
def test_mutations_make_acceptance_fail(mutation, target):
    env = dict(os.environ, PYTHONPATH='cli/src', WF_S05_MUTATION=mutation)
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-s', '--tb=line', '--assert=plain',
                             '-p', 'cli.tests.test_write_negative',
                             'cli/tests/test_write_flow.py::' + target],
                            cwd=ROOT, env=env, capture_output=True, text=True)
    print(result.stdout, end='')
    print(result.stderr, end='')
    assert result.returncode == 1
    assert 'MUTATION_APPLIED ' + mutation in result.stdout
    assert '1 failed' in result.stdout
    assert target.split('[')[0] in result.stdout
