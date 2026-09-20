"""WF-015 iteration 4 兩位查核者十條 finding 的回歸形狀。

一條 finding 一個具名測試，形狀逐一取自該條 `evidence` 描述的重現步驟（⛔ 不改寫成別的形狀）：

| finding_id | 本檔的測試 |
|---|---|
| WF-015-R4.1-1 | `test_r411_carrier_without_trailing_newline_is_byte_reversible` |
| WF-015-R4.1-2 | `test_r412_bare_jobs_header_survives_deactivate` |
| WF-015-R4.1-3 | `test_r413_the_carrier_header_rule_is_internally_consistent` |
| WF-015-R4.2-1 | `test_r421_crlf_carrier_is_byte_reversible`（往返）＋ `test_r421_install_leaves_every_byte_outside_the_fragment_spans`（install 當下） |
| WF-015-R4.2-2 | `test_r422_consumer_owned_carrier_is_never_rewritten` |
| WF-015-R4.2-3 | `test_r423_inline_commented_job_key_is_recognised`、`test_r423_an_unrecognisable_job_key_line_stops_the_write`、`test_r423_a_four_space_jobs_block_is_not_recognised_and_stops_the_write` |
| WF-015-R4.2-4 | `test_r424_symlinked_managed_path_never_touches_its_target` |
| WF-015-R4.1-4／-5 | `test_r414_r415_return_numbering_has_a_mechanical_check` |
| WF-015-R5.2-1 | `test_r521_landed_fragment_bytes_equal_the_source_fragment_bytes` |

R4.2-1 的量測時點恰有兩個、⛔ 不可互相取代：**install 當下**（卡面 A5「對未登記的位元組零影響」）與
**install→deactivate 往返之後**（A13 位元組級可逆）。上一輪只驗往返，故 install 當下的片段外新增位元組
未被抓到；本檔兩個時點各有一個具名測試。

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


# ── 第二輪三條 blocking 的獨立位元組層 ────────────────────────────────────────────
# 判準一律對**原始 bytes**，⛔ 不經 `job_text`／`job_span`（F-共用-06 逐字「驗證對原件，⛔ 不對經任何
# 一層加工的字串」）。`cut()` 只認來源檔那兩個逐字 ASCII 標頭行；兩格縮排在此**刻意重打**：獨立比較器
# 要與被測物的縮排判定脫鉤，否則同一個 bug 會同時讓被測物與比較器失效。
NONL = CONSUMER_JOB.rstrip('\n')                       # 檔尾⛔ 無換行
CRLF_NONL = CONSUMER_JOB.replace('\n', '\r\n').rstrip('\r\n')
BARE_JOBS_NONL = 'name: own\njobs:'                     # 檔案恰好結束在 `jobs:` 這一行
FOUR_SPACE = CONSUMER_JOB.replace('  ', '    ').replace('    mine:', f'    {_adopt.FRAGMENTS[0]}:')


def cut(data):
    """回 (切掉兩個框架 job 區間後的剩餘 bytes, {job 名: 該區間的原始 bytes})。"""
    heads = {b'  ' + name.encode() + b':': name for name in _adopt.FRAGMENTS}
    lines, spans, blocks = data.splitlines(keepends=True), [], {}
    for index, line in enumerate(lines):
        if line.rstrip(b'\r\n') not in heads:
            continue
        end = index + 1
        while end < len(lines) and (not lines[end].strip()
                                    or len(lines[end]) - len(lines[end].lstrip(b' ')) > 2):
            end += 1
        while end > index + 1 and not lines[end - 1].strip():
            end -= 1
        spans.append((index, end))
        blocks[heads[line.rstrip(b'\r\n')]] = b''.join(lines[index:end])
    kept = b''.join(l for i, l in enumerate(lines) if not any(a <= i < z for a, z in spans))
    return kept, blocks


def source_blocks(rules):
    return cut((rules / _adopt.FRAGMENT_SOURCE).read_bytes())[1]


def test_cut_is_an_effective_comparator(tmp_path, env):
    """負控（必須會響）：比較器對「區間外多一個位元組」與「區間內少一個位元組」都必須判⛔ 不相等。"""
    _, rules, _, _, _ = adopted_consumer(tmp_path, env, name='cut-neg')
    blocks = source_blocks(rules)
    assert set(blocks) == set(_adopt.FRAGMENTS), sorted(blocks)
    body = CONSUMER_JOB.encode('utf-8')
    assert cut(body)[1] == {} and cut(body)[0] == body            # ⛔ 無框架 job ⇒ 全部算區間外
    spiked = body + blocks[_adopt.FRAGMENTS[0]]
    assert cut(spiked)[0] == body and cut(spiked)[1][_adopt.FRAGMENTS[0]] == blocks[_adopt.FRAGMENTS[0]]
    assert cut(spiked + b'\n')[0] != body                          # 區間外多一個位元組 ⇒ 響
    assert cut(body + blocks[_adopt.FRAGMENTS[0]][:-1])[1][_adopt.FRAGMENTS[0]] != blocks[_adopt.FRAGMENTS[0]]
    print('NEGATIVE_CONTROL cut outside_extra_byte=True inside_missing_byte=True')


# ── WF-015-R4.2-1：install **當下**片段區間之外的位元組逐一相等 ──────────────────────
@pytest.mark.parametrize('case,body,lands', [
    ('owned_nonl', NONL, True), ('crlf_nonl', CRLF_NONL, True), ('bare_jobs_nonl', BARE_JOBS_NONL, False),
    ('owned_lf', CONSUMER_JOB, True), ('crlf', CONSUMER_JOB.replace('\n', '\r\n'), True)])
def test_r421_install_leaves_every_byte_outside_the_fragment_spans(tmp_path, env, capsys, case, body, lands):
    """量測時點是 **install 當下**（⛔ 不是 install→deactivate 往返之後）：卡面 A5 逐字
    「`snapshot --adopt install` 對未登記的位元組零影響」。落地時區間外逐一相等；⛔ 無法⛔ 不補
    接行換行時（`bare_jobs_nonl`）對承載檔零寫入並印 `UNTERMINATED`。"""
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name=f'r421-outside-{case}')
    before = carrier_with(consumer, body)
    rc, out = step(consumer, 'install', capsys)
    assert rc == 0, out
    landed = carrier_bytes(consumer)
    outside, blocks = cut(landed)
    assert sorted(blocks) == (sorted(_adopt.FRAGMENTS) if lands else []), (case, sorted(blocks))
    assert outside == before, (case, outside, before)          # A5②：區間外位元組逐一相等
    registered = {e['path'] for e in manifest_of(consumer)['assets']}
    fragments = {p for p in registered if p.startswith(f'{_adopt.CARRIER}#')}
    if lands:
        assert landed != before, case                          # 負控：install 真的動過承載檔
        assert fragments == {f'{_adopt.CARRIER}#{n}' for n in _adopt.FRAGMENTS}, sorted(registered)
    else:
        assert landed == before and fragments == set(), (case, sorted(registered))
        assert [line for line in out.splitlines() if _adopt.UNTERMINATED in line], out
    print('R4.2-1', case, 'outside_preserved True lands', lands, 'bytes', len(before))


# ── WF-015-R4.2-3：⛔ 非兩格縮排的既有 jobs 區塊也算「無法安全辨識」 ────────────────────
def test_r423_a_four_space_jobs_block_is_not_recognised_and_stops_the_write(tmp_path, env, capsys):
    """查核序 2 的 `four_space`：四格縮排的既有 `secret-scan` 同時漏過 `job_names` 與保守拒寫時，
    install 會在同一個 `jobs:` 之下追加兩格縮排的同名鍵 ⇒ 改壞採用專案原本可解析的 workflow。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='r423-four-space')
    before = carrier_with(consumer, FOUR_SPACE)
    assert _adopt.job_names(FOUR_SPACE) == (), FOUR_SPACE      # 母體前提：本層辨識⛔ 不到任何 job
    assert _adopt.unsafe_job_lines(FOUR_SPACE), FOUR_SPACE     # ⇒ 必須收成「無法安全辨識」
    rc, out = step(consumer, 'install', capsys)
    assert rc == 0, out
    assert carrier_bytes(consumer) == before                   # 位元組逐一不變
    registered = {e['path'] for e in manifest_of(consumer)['assets']}
    assert not [p for p in registered if p.startswith(f'{_adopt.CARRIER}#')], sorted(registered)
    assert [line for line in out.splitlines() if _adopt.UNSAFE_JOB in line], out
    print('R4.2-3c four_space zero_write True, UNSAFE_JOB printed')


def test_r423_negative_control_the_two_space_sibling_is_installed(tmp_path, env, capsys):
    """負控（必須會響）：同一棵樹上把縮排改回兩格後，install 必須落地兩個片段——否則四格那條恆真。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='r423-four-space-neg')
    before = carrier_with(consumer, CONSUMER_JOB)
    assert _adopt.unsafe_job_lines(CONSUMER_JOB) == ()
    rc, out = step(consumer, 'install', capsys)
    assert rc == 0 and carrier_bytes(consumer) != before, out
    registered = {e['path'] for e in manifest_of(consumer)['assets']}
    assert {f'{_adopt.CARRIER}#{n}' for n in _adopt.FRAGMENTS} <= registered, sorted(registered)
    print('NEGATIVE_CONTROL two_space_sibling installed ->', sorted(registered))


# ── WF-015-R5.2-1：片段逐字落地，且 digest 與 smoke ⛔ 不得掩蓋差異 ───────────────────
@pytest.mark.parametrize('case,body', [
    ('owned_nonl', NONL), ('crlf_nonl', CRLF_NONL), ('owned_lf', CONSUMER_JOB),
    ('crlf', CONSUMER_JOB.replace('\n', '\r\n')), ('bare_jobs', BARE_JOBS), ('absent', None)])
def test_r521_landed_fragment_bytes_equal_the_source_fragment_bytes(tmp_path, env, capsys, case, body):
    """落地區間的**原始 bytes** 與來源檔同名 job 區間的**原始 bytes** 逐一相等，且該項 `digest`
    的前像就是落地的那段原始 bytes（⛔ 不是補過換行的加工字串）。"""
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name=f'r521-{case}')
    if body is not None:
        carrier_with(consumer, body)
    rc, out = step(consumer, 'install', capsys)
    assert rc == 0, out
    expected = source_blocks(rules)
    blocks = cut(carrier_bytes(consumer))[1]
    entries = {e['path']: e for e in manifest_of(consumer)['assets']}
    for name in _adopt.FRAGMENTS:
        assert blocks[name] == expected[name], (case, name, blocks[name], expected[name])
        entry = entries[f'{_adopt.CARRIER}#{name}']
        assert entry['digest'] == _adopt.digest_of(blocks[name]), (case, name, entry)
    rc_smoke, smoke = step(consumer, 'smoke', capsys)
    assert rc_smoke == 0
    row, = [l for l in smoke.splitlines() if _adopt.SMOKE_ITEMS[1] in l]
    assert f'・{_adopt.STATUSES[0]}・' in row, row
    print('R5.2-1', case, 'verbatim', {n: True for n in _adopt.FRAGMENTS}, row)


def test_r521_negative_control_a_one_byte_fragment_edit_is_not_masked(tmp_path, env, capsys):
    """負控（必須會響）：把落地片段的最後一個位元組拿掉後，同一條 `managed-assets` 必須轉 `fail`
    ——這正是上一輪被 `job_text` 補換行掩蓋掉的那一個位元組。"""
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name='r521-neg')
    carrier_with(consumer, CONSUMER_JOB)
    assert step(consumer, 'install', capsys)[0] == 0
    data = carrier_bytes(consumer)
    assert data.endswith(b'\n'), data[-20:]
    (consumer / _adopt.CARRIER).write_bytes(data[:-1])          # 只拿掉檔尾那一個 0a
    rc, smoke = step(consumer, 'smoke', capsys)
    assert rc == 0
    row, = [l for l in smoke.splitlines() if _adopt.SMOKE_ITEMS[1] in l]
    assert f'・{_adopt.STATUSES[1]}・' in row, row
    print('NEGATIVE_CONTROL one_byte_fragment_edit ->', row)
