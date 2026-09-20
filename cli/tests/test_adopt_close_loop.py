"""WF-015 iteration 4 兩位查核者九條 finding 的回歸形狀。

一條 finding 一個具名測試，形狀逐一取自該條 `evidence` 描述的重現步驟（⛔ 不改寫成別的形狀）：

| finding_id | 本檔的測試 |
|---|---|
| WF-015-R4.1-1 | `test_r411_carrier_without_trailing_newline_is_byte_reversible` |
| WF-015-R4.1-2 | `test_r412_bare_jobs_header_survives_deactivate` |
| WF-015-R4.1-3 | `test_r413_the_carrier_header_rule_is_internally_consistent` |
| WF-015-R4.2-1 | `test_r421_crlf_carrier_is_byte_reversible` |
| WF-015-R4.2-2 | `test_r422_consumer_owned_carrier_is_never_rewritten` |
| WF-015-R4.2-3 | `test_r423_inline_commented_job_key_is_recognised` |
| WF-015-R4.2-4 | `test_r424_symlinked_managed_path_never_touches_its_target` |
| WF-015-R4.1-4／-5 | `test_r414_r415_return_numbering_has_a_mechanical_check` |

判準的居所是 `core/adopt.md` §2／§5，常數一律 `import`（F-執行者-04）。合成 consumer 樹＝
`test_adopt_gitlink.adopted_consumer`（`core/adopt.md` §0）；⛔ 不依賴本 repo 歷史存在。
每個形狀都附負控：install 真的改過承載檔（否則位元組相等恆真、零資訊，F-共用-05）。
"""
import json
from pathlib import Path

import pytest

from wf.context import FilesystemRulesSource, Provenance
from wf.verbs import _adopt
from wf.verbs.main import main
from .fakes import FakeGhClient
from .test_adopt_fragments import CONSUMER_JOB, carrier_with, manifest_of
from .test_adopt_gitlink import adopted_consumer
from .test_adoption_contract import adopt_section
from .test_compose_schema import ROOT
from .test_context_roots import git_env

BARE_JOBS = '# 只有設定與註解\nname: mine\non:\n  push:\njobs:\n'
COMMENTED_JOB = CONSUMER_JOB.replace('  mine:', f'  {_adopt.FRAGMENTS[0]}: # consumer job')
UNSAFE_CARRIER = CONSUMER_JOB.replace('  mine:', '  mine: {}')


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


def step(consumer, name, capsys):
    """跑一個 `--adopt` step，回 (rc, stdout)。stdout 每次取走，⛔ 不跨 step 累積。"""
    rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', name],
              client=FakeGhClient(), root=None, env={})
    return rc, capsys.readouterr().out


def carrier_bytes(consumer):
    return (consumer / _adopt.CARRIER).read_bytes()


def round_trip(consumer, capsys):
    """install→deactivate，回 (install 後的承載檔位元組, install stdout, deactivate stdout)。"""
    rc_in, out_in = step(consumer, 'install', capsys)
    assert rc_in == 0, out_in
    landed = carrier_bytes(consumer) if (consumer / _adopt.CARRIER).is_file() else None
    rc_out, out_out = step(consumer, 'deactivate', capsys)
    assert rc_out == 0, out_out
    return landed, out_in, out_out


# ── WF-015-R4.1-1：承載檔⛔ 不以換行結尾（A13②） ────────────────────────────────────
def test_r411_carrier_without_trailing_newline_is_byte_reversible(tmp_path, env, capsys):
    """查核序 1 的 `shape2_owned_nonl`：`upsert_job` 為了接行而補的那個換行⛔ 不得留在檔尾。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='r411')
    before = carrier_with(consumer, CONSUMER_JOB.rstrip('\n'))
    assert not before.endswith(b'\n')                      # 母體前提：確實⛔ 不以換行結尾
    landed, _, _ = round_trip(consumer, capsys)
    assert landed is not None and landed != before          # 負控：install 真的改過承載檔
    for name in _adopt.FRAGMENTS:                           # 片段確實落地過（⛔ 非因未安裝而相等）
        assert name in _adopt.job_names(landed.decode('utf-8')), name
    assert carrier_bytes(consumer) == before
    print('R4.1-1 no_trailing_newline before', len(before), 'landed', len(landed), 'restored True')


# ── WF-015-R4.1-2：⛔ 無子鍵的 `jobs:` 標頭（A13③） ─────────────────────────────────
def test_r412_bare_jobs_header_survives_deactivate(tmp_path, env, capsys):
    """查核序 1 的 `shape3_bare_jobs`：consumer 原有的 `jobs:` 標頭行⛔ 不得被 deactivate 移除。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='r412')
    before = carrier_with(consumer, BARE_JOBS)
    assert _adopt.job_names(BARE_JOBS) == ()                # 母體前提：⛔ 無任何 job
    landed, _, _ = round_trip(consumer, capsys)
    assert landed is not None and landed != before          # 負控：install 真的改過承載檔
    for name in _adopt.FRAGMENTS:
        assert name in _adopt.job_names(landed.decode('utf-8')), name
    after = carrier_bytes(consumer)
    assert after == before
    assert b'jobs:\n' in after                              # 標頭行仍在（查核序 1 的直接證否點）
    print('R4.1-2 bare_jobs restored', after == before, 'header_kept', b'jobs:\n' in after)


def test_r412_negative_control_the_header_removal_would_be_detected(tmp_path, env, capsys):
    """負控（必須會響）：手動移除標頭行後，同一個位元組比對必須判⛔ 不相等。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='r412-neg')
    before = carrier_with(consumer, BARE_JOBS)
    round_trip(consumer, capsys)
    tampered = carrier_bytes(consumer).replace(b'jobs:\n', b'')
    assert tampered != before, tampered
    print('NEGATIVE_CONTROL header_removed ->', tampered != before)


# ── WF-015-R4.1-3：`core/adopt.md` §2 與 §5 的內部矛盾 ──────────────────────────────
def test_r413_the_carrier_header_rule_is_internally_consistent():
    """裁定取 §5（位元組級可逆）那一邊：§2 ⛔ 不得再要求 deactivate 移除 `jobs:` 標頭行。

    機械判準（⛔ 不讀散文推論）：§2 ⛔ 無「一併移除該標頭行」、有「⛔ 不移除該標頭行」；
    §5 的可逆條列出本輪四種被證否或新增的形狀名。兩段解析自規則本體、⛔ 不重打條文。
    """
    rules = FilesystemRulesSource(ROOT, Provenance('cli', '--rules-root'))
    _, two = adopt_section(rules, '2')
    _, five = adopt_section(rules, '5')
    assert '一併移除該標頭行' not in two, two
    assert '⛔ 不移除該標頭行' in two, two
    assert '⛔ 不新增該標頭行' in two, two
    reversible, = [line for line in five.splitlines() if '位元組級可逆' in line]
    for shape in ('⛔ 無 `jobs:` 鍵', '⛔ 無子鍵的 `jobs:` 標頭', '檔尾⛔ 無換行', 'CRLF'):
        assert shape in reversible, (shape, reversible)
    print('R4.1-3 ruling=§5', 'two_has_removal_clause', '一併移除該標頭行' in two)


# ── WF-015-R4.2-1：CRLF 承載檔 ─────────────────────────────────────────────────────
@pytest.mark.parametrize('case,body', [
    ('crlf_owned', CONSUMER_JOB.replace('\n', '\r\n')),
    ('crlf_no_newline', CONSUMER_JOB.replace('\n', '\r\n').rstrip('\r\n')),
])
def test_r421_crlf_carrier_is_byte_reversible(tmp_path, env, capsys, case, body):
    """查核序 2 的 `crlf_owned`／`no_newline`：⛔ 非片段位元組（含 CRLF 行尾）逐一保留。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name=f'r421-{case}')
    before = carrier_with(consumer, body)
    assert b'\r\n' in before                                # 母體前提：確實是 CRLF
    landed, _, _ = round_trip(consumer, capsys)
    assert landed is not None and landed != before          # 負控：install 真的改過承載檔
    for name in _adopt.FRAGMENTS:
        assert name in _adopt.job_names(landed.decode('utf-8')), name
    assert landed.count(b'\r\n') >= before.count(b'\r\n')   # consumer 行尾在 install 後仍是 CRLF
    assert carrier_bytes(consumer) == before
    print('R4.2-1', case, 'crlf_before', before.count(b'\r\n'), 'restored True')


# ── WF-015-R4.2-2：整檔登記為 consumer-owned 的承載檔 ──────────────────────────────
def test_r422_consumer_owned_carrier_is_never_rewritten(tmp_path, env, capsys):
    """查核序 2 的 `owned_carrier`：整檔 `consumer-owned` 登記涵蓋承載檔全部位元組。"""
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name='r422')
    before = carrier_with(consumer, CONSUMER_JOB)
    entry = _adopt.asset_entry(_adopt.CARRIER, _adopt.OWNERSHIPS[1],
                               _adopt.digest_of(before), '0.0.0')
    _adopt.write_manifest(consumer, [entry], None, '0.0.0')
    rc, out = step(consumer, 'install', capsys)
    assert rc == 0, out
    assert carrier_bytes(consumer) == before                        # 位元組逐一不變
    after = {e['path']: e for e in manifest_of(consumer)['assets']}
    assert after[_adopt.CARRIER] == entry, after[_adopt.CARRIER]     # 登記項逐鍵不變
    assert not [p for p in after if p.startswith(f'{_adopt.CARRIER}#')], sorted(after)
    assert [line for line in out.splitlines()
            if _adopt.KEPT_OWNED in line and _adopt.CARRIER in line], out
    print('R4.2-2 owned_carrier bytes_kept True entry_kept True')


def test_r422_negative_control_an_unowned_carrier_is_installed(tmp_path, env, capsys):
    """負控（必須會響）：同一棵樹上⛔ 不做整檔 owned 登記時，install 必須改到承載檔並登記片段。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='r422-neg')
    before = carrier_with(consumer, CONSUMER_JOB)
    rc, out = step(consumer, 'install', capsys)
    assert rc == 0, out
    assert carrier_bytes(consumer) != before
    registered = {e['path'] for e in manifest_of(consumer)['assets']}
    assert {f'{_adopt.CARRIER}#{n}' for n in _adopt.FRAGMENTS} <= registered, sorted(registered)
    print('NEGATIVE_CONTROL unowned_carrier installed ->', sorted(registered))


# ── WF-015-R4.2-3：帶行尾註解的同名 job ────────────────────────────────────────────
def test_r423_inline_commented_job_key_is_recognised(tmp_path, env, capsys):
    """查核序 2 的 `foreign_comment`：`  secret-scan: # consumer job` 仍是一個 job 鍵。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='r423')
    before = carrier_with(consumer, COMMENTED_JOB)
    assert _adopt.FRAGMENTS[0] in _adopt.job_names(COMMENTED_JOB), COMMENTED_JOB
    rc, out = step(consumer, 'install', capsys)
    assert rc == 0, out
    assert carrier_bytes(consumer) == before                        # 位元組逐一不變
    registered = {e['path'] for e in manifest_of(consumer)['assets']}
    assert not [p for p in registered if p.startswith(f'{_adopt.CARRIER}#')], sorted(registered)
    assert [line for line in out.splitlines() if _adopt.FOREIGN_JOB in line], out
    print('R4.2-3 inline_comment FOREIGN_JOB printed, carrier unchanged')


def test_r423_an_unrecognisable_job_key_line_stops_the_write(tmp_path, env, capsys):
    """同源形狀：`  mine: {}` 這種本層無法安全辨識邊界的鍵行 ⇒ 零寫入並印一行說明，⛔ 不猜。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='r423-unsafe')
    before = carrier_with(consumer, UNSAFE_CARRIER)
    assert _adopt.unsafe_job_lines(UNSAFE_CARRIER), UNSAFE_CARRIER
    rc, out = step(consumer, 'install', capsys)
    assert rc == 0 and carrier_bytes(consumer) == before, out
    assert [line for line in out.splitlines() if _adopt.UNSAFE_JOB in line], out
    assert _adopt.unsafe_job_lines(CONSUMER_JOB) == ()               # 負控：正常形狀⛔ 不誤判
    print('R4.2-3b unsafe_job_line zero_write True')


# ── WF-015-R4.2-4：登記路徑是樹內符號連結 ─────────────────────────────────────────
def test_r424_symlinked_managed_path_never_touches_its_target(tmp_path, env, capsys):
    """查核序 2 的 `symlink_target`：install ⛔ 不寫穿連結、deactivate ⛔ 不刪連結指向的⛔ 未登記檔。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='r424')
    managed = _adopt.MANAGED_ASSETS[0]
    victim = consumer / 'consumer.txt'
    victim.write_bytes('採用專案自己的資料，⛔ 未登記\n'.encode('utf-8'))
    before = victim.read_bytes()
    link = consumer / managed
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(Path('..') / '..' / victim.name)
    assert link.is_symlink() and link.read_bytes() == before
    rc_in, out_in = step(consumer, 'install', capsys)
    assert rc_in == 0, out_in
    assert victim.read_bytes() == before, '寫穿符號連結改到了⛔ 未登記的 consumer 檔'
    assert link.is_symlink()
    registered = {e['path'] for e in manifest_of(consumer)['assets']}
    assert managed not in registered, sorted(registered)             # ⛔ 未寫入就⛔ 不登記
    assert [line for line in out_in.splitlines()
            if _adopt.SYMLINK_PATH in line and managed in line], out_in
    rc_out, out_out = step(consumer, 'deactivate', capsys)
    assert rc_out == 0, out_out
    assert victim.is_file() and victim.read_bytes() == before, 'deactivate 刪到了連結指向的目標'
    print('R4.2-4 symlink target_kept True link_kept', link.is_symlink())


def test_r424_a_registered_symlink_is_skipped_by_deactivate(tmp_path, env, capsys):
    """同源形狀：manifest 內已登記該路徑、樹上卻是符號連結時，deactivate 零處置並印一行說明
    （處置對象是**那個名字本身**，⛔ 不是 `resolve()` 後的目標）。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='r424-registered')
    managed = _adopt.MANAGED_ASSETS[0]
    victim = consumer / 'consumer.txt'
    victim.write_bytes(b'unregistered\n')
    link = consumer / managed
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(Path('..') / '..' / victim.name)
    _adopt.write_manifest(consumer, [_adopt.asset_entry(managed, _adopt.OWNERSHIPS[0],
                                                        'sha256:0', '0.0.0')], None, '0.0.0')
    rc, out = step(consumer, 'deactivate', capsys)
    assert rc == 0, out
    assert victim.is_file() and victim.read_bytes() == b'unregistered\n'
    assert link.is_symlink()
    assert [line for line in out.splitlines()
            if _adopt.SYMLINK_PATH in line and managed in line], out
    print('R4.2-4b registered_symlink skipped, target kept')


def test_r424_negative_control_a_plain_registered_file_is_removed(tmp_path, env, capsys):
    """負控（必須會響）：同一條路徑上的**一般檔**必須照 §5 被移除，否則符號連結那條恆真、零資訊。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='r424-neg')
    managed = _adopt.MANAGED_ASSETS[0]
    plain = consumer / managed
    plain.parent.mkdir(parents=True, exist_ok=True)
    plain.write_bytes(b'# framework\n')
    _adopt.write_manifest(consumer, [_adopt.asset_entry(managed, _adopt.OWNERSHIPS[0],
                                                        'sha256:0', '0.0.0')], None, '0.0.0')
    rc, out = step(consumer, 'deactivate', capsys)
    assert rc == 0 and not plain.exists(), out
    print('NEGATIVE_CONTROL plain_registered_file removed ->', not plain.exists())


# ── WF-015-R4.1-4／-5：交回單的條數與條號 ──────────────────────────────────────────
def acceptance_labels(count):
    return tuple(f'A{index + 1}' for index in range(count))


def stale_ids(text, count):
    """文字內出現、但超出現行 acceptance 條數的條號（`A<n>`，n > count）。"""
    import re
    return sorted({found for found in re.findall(r'A(\d+)', text) if int(found) > count},
                  key=int)


def test_r414_r415_return_numbering_has_a_mechanical_check():
    """兩條 minor 的機械化檢查：條號超出現行條數時必須會響（⛔ 不靠人眼核對）。

    本測試釘的是**檢查本身**，⛔ 不是某一份交回單：交回單⛔ 不在 repo 內，故以正負控兩個合成字串
    證明 `stale_ids` 有效——這正是 R4.1-4／-5 缺的那個「由指令輸出產生」的完整性檢查（F-共用-18）。
    """
    assert acceptance_labels(3) == ('A1', 'A2', 'A3')
    assert stale_ids('現行 28 條：A7／A8／A26', 28) == []
    assert stale_ids('現行 32 條：A7／A29／A30／A32', 28) == ['29', '30', '32']
    print('R4.1-4/-5 stale_ids negative', stale_ids('A7／A8', 28),
          'positive', stale_ids('A29／A30／A32', 28))
