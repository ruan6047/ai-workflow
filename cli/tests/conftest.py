"""消費 roles/conduct-common.md §1；離線測試護欄。"""
import os
from pathlib import Path
import subprocess

import pytest


def pytest_sessionstart(session):
    if os.environ.get('WF_OFFLINE') != '1':
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


@pytest.fixture(autouse=True)
def no_item_lookup_wait(monkeypatch):
    """有界唯讀重試的間隔在測試裡一律歸零：測試 ⛔ 不真睡（次數仍由常數決定）。
    等待本身由注入假 sleep 的那一例證明——test_write_flow.py 的
    test_invisible_item_lookup_waits_between_retries 自己把間隔設成可辨識的值。"""
    monkeypatch.setattr('wf.verbs._write._ITEM_LOOKUP_INTERVAL', 0)
