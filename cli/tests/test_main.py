"""消費 core/verbs.md §1 七動詞、§2（`--dry-run` 全域旗標）。"""
import pytest

from .fakes import FakeGhClient
from .test_compose_schema import ROOT
from wf.verbs import notes as notes_verb
from wf.verbs.main import BOOLEAN_FLAGS, GLOBAL_FLAGS, VERBS, global_flags, main


def test_seven_verbs_fixed():
    assert VERBS == ("open", "move", "edit", "notes", "brief", "review", "snapshot")


def test_unknown_verb_rc2(capsys):
    assert main(["nope"]) == 2


def test_dry_run_is_a_valueless_global_flag():
    """裁定 G4：`--dry-run` 掛總入口、⛔ 不逐動詞加。無值旗標與帶值的三個分開宣告，
    故⛔ 不會把下一個 token 當成它的值。"""
    assert BOOLEAN_FLAGS == ('--dry-run',)
    assert not set(BOOLEAN_FLAGS) & set(GLOBAL_FLAGS)
    assert global_flags(['--dry-run', 'notes', 'WF-001']) == ({'--dry-run': True}, ['notes', 'WF-001'])
    assert global_flags(['--dry-run', '--remote=up', 'snapshot']) == (
        {'--dry-run': True, '--remote': 'up'}, ['snapshot'])
    assert global_flags(['notes', 'WF-001', '--dry-run']) is None   # 動詞之後＝⛔ 不傳給動詞
    assert global_flags(['--dry-run=yes', 'notes']) is None         # 無值旗標⛔ 不收 `=`
    assert global_flags(['notes', 'WF-001']) == ({}, ['notes', 'WF-001'])


@pytest.mark.parametrize('argv,expected', [(['notes', 'WF-001'], False),
                                           (['--dry-run', 'notes', 'WF-001'], True)])
def test_main_puts_the_dry_run_decision_on_the_client(monkeypatch, argv, expected):
    """總入口把那一顆布林掛上 client（gate 本身住 gh/writes.py 六原語）；
    負控＝不帶旗標時同一路徑必須是 False。"""
    seen = []
    monkeypatch.setattr(notes_verb, 'run', lambda argv_, **kwargs: seen.append(kwargs['client'].dry_run) or 0)
    client = FakeGhClient()
    assert main(argv, client=client, root=ROOT, env={}) == 0
    assert seen == [expected] and client.dry_run is expected
