"""W1.7 驗收 (1)(2)(3)(4)(6)：遠端來源的四類事實，以注入式固定／序列快照驗。

⛔ 不 mutation 官方 Project #9 或 Issue #370：本檔全部走替身，零網路。
"""
import pytest

from wfx.core.context import Context
from wfx.core.layers import issue_section_index
from wfx.core.rules import issue_section_titles
from wfx.gh.client import NotFound, TransportError
from wfx.gh.facts import CONCEPTS, SECTIONS, base_resolver
from wfx.gh.target import TargetError
from wfx.gh.task import TaskData
from wfx.verbs.facts import collect, render

from .fakes import BASE_REF, FakeClient, snapshot

CONFIG = {'rules': None, 'remote': None, 'project': {'owner': 'o', 'number': 9}}


def gather(tmp_path, *snapshots, sha=None, client=None):
    client = FakeClient(*snapshots) if client is None else client
    context = Context(tmp_path, 'o/r#370', CONFIG)
    return collect(context, 'o/r#370', sha, client=client), client


def test_five_sections_positive(tmp_path):
    facts, _ = gather(tmp_path)
    assert [(s.name, s.state) for s in facts.sections] == [(n, '非空') for n in SECTIONS]


def test_five_sections_negative_points_at_each_one(tmp_path):
    """一缺一空一在：逐項指出，⛔ 不判內容好壞（訊息只有三態，⛔ 無品質字眼）。"""
    body = '## 需求\n\n有內容\n\n## 限制與非目標\n\n   \n\n## 驗收\n\n有\n\n## 風險與假設\n\n有\n'
    facts, _ = gather(tmp_path, snapshot(body=body))
    assert [(s.name, s.state) for s in facts.sections] == [
        ('需求', '非空'), ('限制與非目標', '空'), ('驗收', '非空'),
        ('風險與假設', '非空'), ('裁定紀錄', '缺章節')]
    text = render(facts)
    assert '章節 ## 限制與非目標: 空' in text and '章節 ## 裁定紀錄: 缺章節' in text


def test_seven_concepts_current_values(tmp_path):
    facts, _ = gather(tmp_path)
    assert tuple(c.concept for c in facts.concepts) == CONCEPTS
    assert [(c.field_name, c.value) for c in facts.concepts] == [
        ('Status', '進行中'), ('階段', '執行'), ('owner', 'ruan6047'), ('風險', '重要'),
        ('緊急性', '一般'), ('期限', '2026-09-30'), ('Resource', None)]
    assert 'Resource[Resource]: (空)' in render(facts)


def test_status_lives_in_status_or_renamed_field_but_never_both(tmp_path):
    renamed = ('Title', '狀態', '階段', 'owner', '風險', '緊急性', '期限', 'Resource')
    facts, _ = gather(tmp_path, snapshot(field_names=renamed))
    assert facts.concepts[0].field_name == '狀態'
    with pytest.raises(TargetError, match='狀態欄不唯一'):
        gather(tmp_path, snapshot(field_names=renamed + ('Status',)))


def test_two_baselines_are_labelled_by_source_object(tmp_path):
    facts, _ = gather(tmp_path)
    assert [(b.object_kind, b.object_ref, b.updated_at) for b in facts.baselines] == [
        ('project_item', 'PVTI_1', '2026-09-21T11:05:20Z'),
        ('issue', 'o/r#370', '2026-09-21T10:49:13Z')]
    text = render(facts)
    assert 'project_item PVTI_1 updatedAt=2026-09-21T11:05:20Z' in text
    assert 'issue o/r#370 updatedAt=2026-09-21T10:49:13Z' in text


def test_remote_change_changes_output_no_cache(tmp_path):
    """序列快照：同一 client 兩次 collect 讀到不同遠端實況 ⇒ 輸出（含 updatedAt）跟著變。"""
    client = FakeClient(snapshot(),
                        snapshot(item_updated='2026-09-21T12:00:00Z',
                                 issue_updated='2026-09-21T11:59:00Z', status='待確認'))
    first, _ = gather(tmp_path, client=client)
    second, _ = gather(tmp_path, client=client)
    assert client.reads == 2
    assert first.baselines != second.baselines
    assert (first.concepts[0].value, second.concepts[0].value) == ('進行中', '待確認')
    assert render(first) != render(second)


def test_same_snapshot_twice_is_byte_identical(tmp_path):
    client = FakeClient(snapshot())
    first, _ = gather(tmp_path, client=client)
    second, _ = gather(tmp_path, client=client)
    assert render(first) == render(second)


def test_missing_item_is_typed_unknown_not_a_fake_empty(tmp_path):
    """item 不存在時：概念欄位標 unknown、基準逐項說明缺哪個物件，⛔ 不冒充「沒有值」。"""
    facts, _ = gather(tmp_path, snapshot(item=False))
    assert facts.item_id is None
    assert all(c.field_name is None for c in facts.concepts)
    text = render(facts)
    assert 'unknown: project_item：o/projects/9 內⛔ 無 o/r#370 的 item' in text
    assert 'issue o/r#370 updatedAt=' in text        # Issue 側基準仍取得
    assert '狀態: unknown（Project ⛔ 無此欄，或該卡⛔ 無 item）' in text
    assert '(空)' not in text.split('## 3 ·')[0]   # 取不到⛔ 不得冒充「已讀到且未填」


def test_permission_three_states(tmp_path):
    allowed, _ = gather(tmp_path)
    assert [(p.subject, p.state) for p in allowed.permissions] == [
        ('repository', 'allowed'), ('project', 'allowed')]
    denied, _ = gather(tmp_path, snapshot(viewer_permission='READ', viewer_can_update=False))
    assert [p.state for p in denied.permissions] == ['denied', 'denied']
    unknown, _ = gather(tmp_path, snapshot(viewer_permission=None, viewer_can_update=None))
    assert [p.state for p in unknown.permissions] == ['unknown', 'unknown']
    assert '缺欄位' in render(unknown)


def test_ci_conclusions_are_reported_verbatim(tmp_path):
    """`--sha` 給定時直接用它問 CI，⛔ 不因本機解不到該 revision 就略過這類事實。"""
    facts, _ = gather(tmp_path, snapshot(check_conclusion='skipped'), sha='deadbeef')
    assert facts.ci.check_runs == (('vnext-tests', 'completed', 'skipped'),)
    assert 'check_run vnext-tests: status=completed conclusion=skipped' in render(facts)


def test_ci_without_any_resolvable_sha_is_typed_unknown(tmp_path):
    facts, _ = gather(tmp_path)          # tmp_path 非 git 工作樹且未給 --sha
    assert facts.ci.check_runs is None
    assert 'unknown: CI check：未解析出 SHA' in render(facts)


def test_output_is_exactly_the_six_fact_categories(tmp_path):
    """節數與節名固定為六；renderer 自己的詞彙⛔ 無退回次數、轉移歷史或工作包完成度。

    禁用字串只檢查**本 CLI 產生的模板**在固定快照下的輸出，⛔ 不是對散文或規則文件的判讀。
    """
    text = render(gather(tmp_path)[0])
    headings = [line for line in text.splitlines() if line.startswith('## ')]
    assert [h.split('·')[0].strip() for h in headings] == [f'## {n}' for n in range(1, 7)]
    for banned in ('退回', '轉移歷史', '工作包', 'iteration'):
        assert banned not in text


# base 解析鏈：以**受查 head SHA** 查開啟中 PR，涵蓋 detached 與 --sha（E W1.7 (5)）
HEAD_SHA = '4b968cd7712af5dd5b4d9c453f92cb3ddda0dda4'


def test_base_is_the_open_pr_base_ref_not_the_default_branch():
    client = FakeClient()
    client.repository('o/r')                      # 綁定當次快照
    branch, provenance, reason = base_resolver(client, 'main')(HEAD_SHA)
    assert (branch, reason) == (BASE_REF, None)
    assert str(provenance) == f'api:associatedPullRequests[OPEN].baseRefName={BASE_REF}'


def test_multiple_open_prs_with_different_bases_are_unknown_not_a_guess():
    client = FakeClient(snapshot(pull_requests=({'number': 1, 'state': 'OPEN', 'baseRefName': 'main'},
                                                {'number': 2, 'state': 'OPEN', 'baseRefName': BASE_REF})))
    client.repository('o/r')
    branch, provenance, reason = base_resolver(client, 'main')(HEAD_SHA)
    assert (branch, provenance) == (None, None)
    assert '對到多個開啟中 PR 且 base 不同' in reason


def test_query_failure_is_unknown_and_never_falls_back_to_the_default_branch():
    client = FakeClient(pull_request_error=TransportError('HTTP 500'))
    client.repository('o/r')
    branch, provenance, reason = base_resolver(client, 'main')(HEAD_SHA)
    assert (branch, provenance) == (None, None)
    assert '⛔ 不當成沒有 PR' in reason
    client = FakeClient(pull_request_error=NotFound('HTTP 404'))
    client.repository('o/r')
    assert base_resolver(client, 'main')(HEAD_SHA)[0] is None


def test_closed_and_merged_prs_do_not_decide_the_base():
    """只認 OPEN；已關閉／已合併的關聯 PR ⛔ 不是本次的預期合併目標。"""
    client = FakeClient(snapshot(pull_requests=({'number': 1, 'state': 'MERGED', 'baseRefName': 'x'},
                                                {'number': 2, 'state': 'CLOSED', 'baseRefName': 'y'})))
    client.repository('o/r')
    assert base_resolver(client, 'main')(HEAD_SHA)[0] == 'main'


def test_only_a_confirmed_absence_of_prs_uses_the_default_branch_and_says_so():
    client = FakeClient(snapshot(pull_requests=()))
    client.repository('o/r')
    branch, provenance, reason = base_resolver(client, 'main')(HEAD_SHA)
    assert (branch, reason) == ('main', None)
    assert '⛔ 無關聯的開啟中 PR' in str(provenance)


def test_unresolved_head_sha_never_falls_back_to_a_branch_name():
    client = FakeClient()
    client.repository('o/r')
    branch, provenance, reason = base_resolver(client, 'main')(None)
    assert (branch, provenance) == (None, None)
    assert '⛔ 不以分支名代查' in reason


def test_no_default_branch_and_no_pr_is_unknown():
    client = FakeClient(snapshot(pull_requests=()))
    client.repository('o/r')
    assert base_resolver(client, None)(HEAD_SHA)[2] == 'base ref：repository 無預設分支（API 回 null）'


# ── 固定五章節：facts 與 brief 必須由同一份機械解析得到同一組事實 ──────────────

def brief_index(rules_root, body):
    return issue_section_index(rules_root, TaskData('o/r#370', body, {}, ())).body


def test_the_five_titles_have_one_contract(rules_root):
    """章節標題的居所是 `core/github.md`；facts 的常數只是同一份契約的投影。"""
    assert issue_section_titles(rules_root) == SECTIONS


def test_h1_headings_are_not_the_required_h2_sections(tmp_path, rules_root):
    """契約寫的是 `## `；facts 曾連 `# ` 也收，於是對 brief 說缺的 body 回報五章節皆非空。"""
    body = '\n'.join(f'# {name}\n內容 {name}\n' for name in SECTIONS)
    facts, _ = gather(tmp_path, snapshot(body=body))
    assert [(s.name, s.state) for s in facts.sections] == [(n, '缺章節') for n in SECTIONS]
    index = brief_index(rules_root, body)
    for name in SECTIONS:
        assert f'- {name}：⛔ 標題不在 body' in index


def test_a_duplicate_section_never_fills_in_for_an_empty_first_one(tmp_path, rules_root):
    """同名重複時兩邊都只看**第一個**；facts 曾把重複的內容併進同一節而回非空。"""
    body = '## 需求\n\n## 限制與非目標\n內容\n## 需求\n後來補的\n'
    facts, _ = gather(tmp_path, snapshot(body=body))
    assert [(s.name, s.state) for s in facts.sections] == [
        ('需求', '空'), ('限制與非目標', '非空'), ('驗收', '缺章節'),
        ('風險與假設', '缺章節'), ('裁定紀錄', '缺章節')]
    index = brief_index(rules_root, body)
    assert '- 需求：標題在第 1 行、其下空' in index
    assert '- 限制與非目標：在（第 3 行，1 非空行）' in index
    assert '- （同名重複）需求：第 5 行' in index
