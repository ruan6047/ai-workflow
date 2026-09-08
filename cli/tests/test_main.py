from wf.verbs.main import VERBS, main


def test_seven_verbs_fixed():
    assert VERBS == ("open", "move", "edit", "notes", "brief", "review", "snapshot")


def test_unknown_verb_rc2(capsys):
    assert main(["nope"]) == 2
