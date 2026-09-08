"""消費 roles/conduct-common.md §1；第 6 步規格的離線測試護欄。"""
import os
from pathlib import Path
import subprocess

import pytest


def pytest_sessionstart(session):
    if os.environ.get('WF_S05_OFFLINE') != '1':
        return
    real_run = subprocess.run

    def offline_run(argv, *args, **kwargs):
        if isinstance(argv, (str, bytes)) or Path(argv[0]).name in {'gh', 'curl', 'wget', 'ssh'}:
            raise AssertionError('OFFLINE_NETWORK_DENIED')
        return real_run(argv, *args, **kwargs)

    subprocess.run = offline_run
    with pytest.raises(AssertionError, match='OFFLINE_NETWORK_DENIED'):
        subprocess.run(['gh', 'api', 'offline-negative-control'])
    print('OFFLINE_NETWORK_DENIED negative control passed')
