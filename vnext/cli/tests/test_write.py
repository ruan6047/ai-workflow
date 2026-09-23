"""W1.8 驗收 (1)–(8)：值域檢查、基準比對、`--dry-run` 零 mutation 與退回事件的呼叫形狀。

全檔走注入式替身（`client`＝唯讀快照、`writer`＝記錄式 mutation 替身），
⛔ 不連網、⛔ 不 mutation 官方 Project #9 或 Issue #370。真實寫入的證據另存於 PR 說明與執行報告。
"""
import json

import pytest

from wfx.verbs.main import main

from .conftest import TASK_ID
from .fakes import FakeClient, FakeWriter, snapshot

ITEM_TS = '2026-09-21T11:05:20Z'
ISSUE_TS = '2026-09-21T10:49:13Z'


@pytest.fixture
def run_write(rules_root, project_root, capsys):
    def run(*extra, task=TASK_ID, client=None, writer=None, snapshots=None):
        client = FakeClient(*(snapshots or ())) if client is None else client
        writer = FakeWriter() if writer is None else writer
        rc = main(['--project-root', str(project_root), 'write', '--task', task,
                   '--rules-root', str(rules_root), *extra], client=client, writer=writer)
        captured = capsys.readouterr()
        return rc, captured.out, captured.err, writer, client
    return run


def test_normal_path_writes_seven_concepts_in_one_success(run_write):
    """(1) `facts` 的基準 → 一次成功；⛔ 無「先失敗再重送」。"""
    rc, out, _, writer, _ = run_write(
        '--field', '狀態=進行中', '--field', '階段=執行', '--field', 'owner=Codex PM',
        '--field', '風險=高風險', '--field', '緊急性=一般', '--field', '期限=',
        '--field', 'Resource=', '--expect-updated-at', ITEM_TS)
    assert rc == 0
    assert [(call[2], call[3]) for call in writer.calls] == [
        ('Status', '進行中'), ('階段', '執行'), ('owner', 'Codex PM'), ('風險', '高風險'),
        ('緊急性', '一般'), ('期限', None), ('Resource', None)]
    assert '比對：相符' in out
    assert 'owner[owner]: ruan6047 → Codex PM（已寫入）' in out
    assert '期限[期限]: 2026-09-30 → (空)（已寫入）' in out     # 空值＝清空，⛔ 不代填預設


def test_missing_baseline_refuses_and_the_returned_baseline_lets_it_resend(run_write):
    """(2) 缺基準＝負控：拒寫、rc≠0、零 mutation，並輸出當下值與當下基準。"""
    rc, out, err, writer, _ = run_write('--field', '狀態=待辦')
    assert rc == 1 and writer.calls == []
    assert 'BaselineMissing' in err and ITEM_TS in err
    assert f'當下基準：project_item PVTI_1 updatedAt={ITEM_TS}' in out
    assert '狀態[Status]: 進行中' in out and '比對：⛔ 無基準 ⇒ 拒寫（遠端零 mutation）' in out
    rc, out, _, writer, _ = run_write('--field', '狀態=待辦', '--expect-updated-at', ITEM_TS)
    assert rc == 0 and [(c[2], c[3]) for c in writer.calls] == [('Status', '待辦')]


def test_stale_baseline_refuses_with_both_current_value_and_current_baseline(run_write):
    """(3) 基準不符＝拒寫、rc≠0、零 mutation。"""
    rc, out, err, writer, _ = run_write('--field', '階段=審核',
                                        '--expect-updated-at', '2026-09-20T00:00:00Z')
    assert rc == 1 and writer.calls == []
    assert 'BaselineStale' in err and ITEM_TS in err
    assert '階段[階段]: 執行' in out and '比對：不符 ⇒ 拒寫（遠端零 mutation）' in out


def test_baseline_belongs_to_the_modified_object(run_write):
    """(4) 改欄位比 project_item、貼留言比 issue；輸出標示所用基準與其來源物件。"""
    _, field_out, _, _, _ = run_write('--field', '狀態=待辦', '--expect-updated-at', ITEM_TS)
    assert '# write task=o/r#370 目標物件=project_item PVTI_1' in field_out
    comment = tmp_comment()
    _, comment_out, _, writer, _ = run_write('--comment-file', str(comment),
                                             '--expect-updated-at', ISSUE_TS)
    assert '# write task=o/r#370 目標物件=issue o/r#370' in comment_out
    assert f'當下基準：issue o/r#370 updatedAt={ISSUE_TS}' in comment_out
    assert writer.calls[0][0] == 'post_comment'
    # 拿錯物件的基準＝不符 ⇒ 拒寫（item 的 ts 不能拿來貼留言）
    rc, _, err, writer, _ = run_write('--comment-file', str(comment),
                                      '--expect-updated-at', ITEM_TS)
    assert rc == 1 and writer.calls == [] and 'BaselineStale' in err


def tmp_comment(text='## 執行階段完成\n一個畫面的成果、疑慮與下一步。\n'):
    import tempfile
    path = tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8')
    path.write(text)
    path.close()
    return path.name


def test_dry_run_without_baseline_is_zero_mutation(run_write):
    """(5) 前半：⛔ 不要求基準、可執行、零 mutation，並標明未做基準比對。"""
    rc, out, _, writer, _ = run_write('--dry-run', '--field', '狀態=停止')
    assert rc == 0 and writer.calls == []
    assert '比對：未做基準比對' in out
    assert '狀態[Status]: 進行中 → 停止（would-write，遠端零 mutation）' in out
    assert '## 3 · would-write（⛔ 未送出任何 mutation）' in out


def test_dry_run_with_baseline_runs_the_same_comparison_and_still_writes_nothing(run_write):
    """(5) 後半：有基準則做相同 stale 比對並印出比對結果與 would-write，仍零 mutation。"""
    rc, matched, _, writer, _ = run_write('--dry-run', '--field', '狀態=停止',
                                          '--expect-updated-at', ITEM_TS)
    assert rc == 0 and writer.calls == [] and '比對：相符' in matched
    rc, stale, _, writer, _ = run_write('--dry-run', '--field', '狀態=停止',
                                        '--expect-updated-at', '2026-01-01T00:00:00Z')
    assert rc == 0 and writer.calls == []
    assert '比對：不符（非 dry-run 時會拒寫）' in stale and 'would-write' in stale


def test_output_never_claims_atomicity(run_write):
    """(6) 輸出只說基準縮小視窗、⛔ 不構成鎖。"""
    _, out, _, _, _ = run_write('--field', '狀態=待辦', '--expect-updated-at', ITEM_TS)
    assert '基準只縮小視窗、⛔ 不構成鎖' in out and '⛔ 不具原子性' in out
    assert '原子' not in out.replace('⛔ 不具原子性', '')


def test_value_domain_is_the_only_thing_checked(run_write):
    """(7) `狀態=待辦` 成功；`狀態=退回` 被拒且訊息只說值不在值域內。"""
    rc, _, _, writer, _ = run_write('--field', '狀態=待辦', '--expect-updated-at', ITEM_TS)
    assert rc == 0 and [(c[2], c[3]) for c in writer.calls] == [('Status', '待辦')]
    rc, out, err, writer, client = run_write('--field', '狀態=退回', '--expect-updated-at', ITEM_TS)
    assert rc == 1 and writer.calls == [] and out == ''
    assert 'ValueNotInDomain' in err and '不在值域內' in err
    assert not any(word in err for word in ('轉移', '合法', '階段', '品質'))
    assert client.reads == 0          # 值域檢查在任何遠端讀取之前＝該次完全沒碰遠端


def test_one_return_event_is_two_calls_and_the_cli_never_couples_them(run_write):
    """(8) ≥1 次欄位寫入 ＋ 1 則留言，各自帶自己物件的基準；單獨呼叫也⛔ 不被擋。"""
    rc_fields, _, _, field_writer, _ = run_write(
        '--field', '階段=執行', '--field', '狀態=待辦', '--expect-updated-at', ITEM_TS)
    rc_comment, _, _, comment_writer, _ = run_write(
        '--comment-file', str(tmp_comment('## 退回執行\n原因與證據。\n')),
        '--expect-updated-at', ISSUE_TS)
    assert (rc_fields, rc_comment) == (0, 0)
    assert len(field_writer.calls) == 2 and len(comment_writer.calls) == 1
    with pytest.raises(SystemExit) as exit_info:      # 同一次呼叫混兩個物件＝用法錯
        run_write('--field', '狀態=待辦', '--comment-file', str(tmp_comment()),
                  '--expect-updated-at', ITEM_TS)
    assert exit_info.value.code == 2


def test_usage_errors_are_rc_two_and_never_reach_the_remote(run_write):
    for extra in (('--field', '狀態'), ('--field', '級別=T1'), ('--field', '狀態=待辦',
                  '--field', '狀態=停止'), ()):
        with pytest.raises(SystemExit) as exit_info:
            run_write(*extra)
        assert exit_info.value.code == 2


def test_absent_item_or_project_is_typed_not_a_silent_write(run_write, project_root):
    rc, _, err, writer, _ = run_write('--field', '狀態=待辦', '--expect-updated-at', ITEM_TS,
                                      snapshots=(snapshot(item=False),))
    assert rc == 1 and writer.calls == [] and 'WriteTargetMissing' in err
    (project_root / '.wf' / 'config.json').write_text('{}', encoding='utf-8')
    rc, _, err, writer, _ = run_write('--field', '狀態=待辦', '--expect-updated-at', ITEM_TS)
    assert rc == 1 and writer.calls == [] and '未設 project' in err


def test_status_field_alias_is_resolved_before_writing(run_write):
    """狀態欄改名為 `狀態` 時寫的是同一欄；⛔ 不得另建第二個狀態居所。"""
    renamed = ('Title', '狀態', '階段', 'owner', '風險', '緊急性', '期限', 'Resource')
    rc, _, _, writer, _ = run_write('--field', '狀態=完成', '--expect-updated-at', ITEM_TS,
                                    snapshots=(snapshot(field_names=renamed),))
    assert rc == 0 and [(c[2], c[3]) for c in writer.calls] == [('狀態', '完成')]


@pytest.mark.parametrize('item_slug, task_slug', (('o/r', 'O/R'), ('O/R', 'o/r')))
def test_a_case_differing_task_writes_to_the_same_project_item(run_write, item_slug, task_slug):
    """`--task` 與 item 的 `repository.nameWithOwner` 只差大小寫＝同一個 repository。

    目標物件要是同一個 item（同 id、同基準），⛔ 不得變成「⛔ 無 item」而把一次正常寫入
    誤報成缺目標；也⛔ 不得挑到別的 item。全程走 `FakeWriter`，遠端零 mutation。
    """
    snap = snapshot()
    snap['items'][0]['content']['repository']['nameWithOwner'] = item_slug
    rc, out, _, writer, _ = run_write('--field', '狀態=待辦', '--expect-updated-at', ITEM_TS,
                                      task=f'{task_slug}#370', snapshots=(snap,))
    assert rc == 0 and writer.calls == [('set_field', 'PVTI_1', 'Status', '待辦')]
    assert f'# write task={task_slug}#370 目標物件=project_item PVTI_1' in out
    assert f'當下基準：project_item PVTI_1 updatedAt={ITEM_TS}' in out


def test_two_items_of_the_same_repository_still_fail_loud(run_write):
    """同一 repository 的兩個 item 撞號＝多義；⛔ 不得因大小寫比對放寬就改成挑第一個。"""
    snap = snapshot()
    second = json.loads(json.dumps(snap['items'][0]))
    second['id'] = 'PVTI_2'
    second['content']['repository']['nameWithOwner'] = 'O/R'
    snap['items'].append(second)
    rc, _, err, writer, _ = run_write('--field', '狀態=待辦', '--expect-updated-at', ITEM_TS,
                                      snapshots=(snap,))
    assert rc == 1 and writer.calls == []
    assert "對應多個 Project item：['PVTI_1', 'PVTI_2']" in err
