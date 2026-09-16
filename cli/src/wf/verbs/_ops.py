"""消費 core/verbs.md §2（檢查先於首次遠端寫入、寫入順序、留痕、CLI 只讀三種留言區塊）、
core/naming.md §3 首行標記、core/return.md 區塊。

動詞層純計算的唯一居所：結果物件與五鍵收據、遠端寫入失敗分類、write plan 帳本、
同一操作重跑的身分比對（operation fingerprint），以及 `open` D2／`move` D1 的回讀分流。
⛔ 不自己發遠端請求（`wf.gh.writes` 的六原語仍是唯一出口）、⛔ 不 retry、⛔ 不 rollback、
⛔ 不讀任何事件留言 body。兩個留痕出口（`reject`／`blocked`）刻意留在 `_write.py`：
`wf:reject` 的 `post_comment` 呼叫點是 core/verbs.md §2 留痕條的居所，⛔ 不因本卡而搬家。
"""
from dataclasses import dataclass, replace
import functools
import hashlib
import json

from wf.compose.validate import _equal
from wf.gh.client import GhError, NotFound, NotLoggedIn, PermissionDenied, TransportError
from wf.gh.writes import MUTATIONS, dry_run


@dataclass(frozen=True)
class WriteResult:
    rc: int
    card: dict | None = None
    reason: str = ''
    rejection: dict | None = None
    printed: tuple[str, ...] = ()


@dataclass(frozen=True)
class OperationOutcome(WriteResult):
    """帶五鍵收據的結果物件（WF-016）：六原語寫入失敗的共同出口（rc≠0），以及回讀分流的
    收斂／續作出口（rc=0，只填 completed_writes）。

    五鍵刻意長在本子類、⛔ 不長在 WriteResult：共用五欄的欄位序不動（CLI-002 釘住
    `OpenResult` 的第六位置參數仍是 unverified）。「這一次是遠端寫入失敗」用 isinstance
    加 error_kind 判，⛔ 不用字串比對 reason。
    ⛔ 不得推出「CLI 會自動重試或回滾」——`retryable` 只是交給人的事實。
    """
    error_kind: str | None = None
    phase: str | None = None
    retryable: bool | None = None
    completed_writes: tuple[str, ...] = ()
    next_action: str = ''


def receipt(result, completed, next_action=''):
    """把已完成的遠端寫入掛上結果物件：續作與收斂（rc=0）也要帶收據，否則讀者會把
    「沒有這幾個鍵」反推成「這一次什麼都沒寫過」。result 須是共用五欄的 WriteResult。"""
    return OperationOutcome(**vars(result), completed_writes=tuple(completed),
                            next_action=next_action)


# 例外類別由 wf.gh.client import 使用，⛔ 不重打類名（F-執行者-04）。次序＝由窄到寬：
# NotFound／PermissionDenied／TransportError／NotLoggedIn 都是 GhError 的子類，寬的放最後。
# 需求方 2026-09-16 裁定 G3 甲案逐字「契約涵蓋 PermissionDenied、NotFound、NotLoggedIn、GhError、
# OSError 五類失敗，驗證只驗已量過的 TransportError，其餘逐項列 unverified」。
_KINDS = ((NotLoggedIn, 'not_logged_in'), (PermissionDenied, 'permission_denied'),
          (NotFound, 'not_found'), (TransportError, 'transport'), (GhError, 'gh_error'),
          (OSError, 'os_error'))
PHASES = {'update_card_body': '卡面 JSON', 'write_project_field': '投影欄',
          'add_to_project': '加入 Project', 'remove_from_project': '移出 Project',
          'close_issue': '關閉 issue', 'post_comment': '留言'}
# 事件留言的判定只看 core/naming.md §3 的首行標記；⛔ 不讀 body、⛔ 不為事件留言新增可讀區塊。
EVENT_MARKERS = ('wf:move', 'wf:edit', 'wf:reject')
EVENT_PHASE = '事件留言'
EVENT_NEXT = '事件留言未貼出：CLI ⛔ 不自動補發，請人工確認該事件是否需要補貼'
RESUME_NEXT = '先回讀遠端狀態再決定是否重跑本動詞；CLI ⛔ 不自動 retry、⛔ 不自動 rollback'
# 需求方 2026-09-16 裁定 G8 取甲：`edit` 的「全項等值＝沉默」出口**無條件**印這一行。
# 為什麼無條件：CLI ⛔ 不讀事件留言 body，跨進程重跑時分辨不出上一次的 `wf:edit` 是貼成功
# 還是失敗未補，使用者仍須能得知事件可能未補上（需求方 2026-09-16 裁定 G1）。
# ⛔ 不得推出「事件已補上」，也⛔ 不得推出「CLI 會去補」；`edit` 的非等值路徑⛔ 不得印同一行
# ——兩條路徑印同一行即判變異沒生效（F-共用-06），該負控住 test_edit_flow.py。
EQUAL_SILENT = '事件留言結果不明：CLI ⛔ 不讀事件留言，等值沉默⛔ 不得讀成事件已補上'


def classify(exc):
    """例外 → (error_kind, retryable)。retryable 只在傳輸類為真，且只是事實宣告：
    core/verbs.md §2 與本卡非射程逐字「⛔ 不做盲目自動 retry」。"""
    for cls, kind in _KINDS:
        if isinstance(exc, cls):
            return kind, cls is TransportError
    return 'unknown', False


def resource(primitive, args):
    """收據與 plan 上的資源字串。六原語在 cli/src/wf/verbs/ 內一律以位置引數呼叫，故只讀 args。
    post_comment 另帶首行標記——事件留言的判定只看標記，⛔ 不讀 body。"""
    head = args[0] if args else ''
    if primitive == 'post_comment':
        return f'#{head} {args[1]}' if len(args) > 1 else f'#{head}'
    if primitive == 'write_project_field':
        return str((head[2] if len(head) > 2 else {}).get('fieldId', ''))
    if primitive in ('add_to_project', 'remove_from_project'):
        return str(args[1] if len(args) > 1 else head)
    return f'#{head}'


def is_event_comment(primitive, target):
    return primitive == 'post_comment' and any(marker in target for marker in EVENT_MARKERS)


class WriteLedger:
    """一次動詞執行的 write plan 與部分完成收據。
    plan＝依序登記的（原語, 資源），⛔ 不管成敗；completed＝實際完成的那些（`--dry-run` 下恆空，
    因為六原語一次都沒發請求）；pending＝正在發的那一筆，供失敗時定位 phase。
    ⛔ 不存 body、⛔ 不存 payload、⛔ 不存憑證。"""

    def __init__(self, verb, dry):
        self.verb, self.dry = verb, dry
        self.plan, self.completed, self.pending = [], [], None

    def begin(self, primitive, target):
        self.pending = (primitive, target)
        self.plan.append(self.pending)

    def done(self):
        if not self.dry:
            self.completed.append(self.pending)
        self.pending = None

    def receipt(self):
        return tuple(f'{primitive}・{target}' for primitive, target in self.completed)


class WriteProxy:
    """包住 client 的六個 mutation 原語，只為了記帳；其餘屬性一律轉給被包的 client。
    ⛔ 不改引數、⛔ 不改回傳、⛔ 不吞例外。原語名由 wf.gh.writes.MUTATIONS import 使用，⛔ 不重打。"""

    def __init__(self, client, verb):
        self.client = client
        self.ledger = WriteLedger(verb, dry_run(client))

    def __getattr__(self, name):
        target = getattr(self.client, name)
        if name not in MUTATIONS:
            return target

        @functools.wraps(target)
        def recorded(*args, **kwargs):
            self.ledger.begin(name, resource(name, args))
            result = target(*args, **kwargs)
            self.ledger.done()
            return result
        return recorded


def failure(verb, exc, ledger, emit):
    """六原語逸出的失敗 → rc≠0 的 OperationOutcome，收據逐行印出。
    completed_writes 取自本次帳本，⛔ 不重建、⛔ 不猜；事件留言另有逐字的 next_action。"""
    primitive, target = ledger.pending or ('', '')
    event = is_event_comment(primitive, target)
    kind, retryable = classify(exc)
    phase = EVENT_PHASE if event else PHASES.get(primitive, primitive or '未知')
    action = f'{EVENT_NEXT}（{target}）' if event else RESUME_NEXT
    done = ledger.receipt()
    lines = [f'遠端寫入失敗・{verb}・{kind}・{phase}・{target}・retryable={retryable}',
             *(f'已完成的寫入：{entry}' for entry in done), f'後續動作：{action}']
    for line in lines:
        emit(line)
    return OperationOutcome(1, reason=' '.join(str(exc).split()), printed=tuple(lines),
                            error_kind=kind, phase=phase, retryable=retryable,
                            completed_writes=done, next_action=action)


def planned(result, ledger, emit):
    """`--dry-run` 的出口：印出本次的 write plan（原語名與順序，⛔ 不印 body 與 payload）。
    刻意⛔ 不在不帶旗標時印：成功路徑的 stdout 行集合必須與基線相同。"""
    if not ledger.dry:
        return result
    lines = [f'write plan・{ledger.verb}・--dry-run・本次遠端 mutation 0 次',
             *(f'write plan・{index}・{primitive}・{target}'
               for index, (primitive, target) in enumerate(ledger.plan, 1))]
    for line in lines:
        emit(line)
    return replace(result, printed=(*result.printed, *lines))


def guarded(verb):
    """動詞本體的共同失敗出口（core/verbs.md §2）。包一層 WriteProxy 記帳，把六原語逸出的
    GhError／OSError 收斂成 OperationOutcome（rc≠0），例外⛔ 不再逸出動詞。
    刻意只在帳本有 in-flight 的那一筆時才接：讀取路徑的 GhError 維持基線行為往上拋，
    ⛔ 不得推出「本卡把所有 API 失敗都吞掉」。
    巢狀呼叫（review→notes、brief→notes）沿用外層帳本並讓例外往上，⛔ 不各自印一份收據。"""
    def decorate(run):
        @functools.wraps(run)
        def guard(*args, **kwargs):
            client = kwargs['client']
            if isinstance(client, WriteProxy):
                return run(*args, **kwargs)
            proxy = WriteProxy(client, verb)
            try:
                return planned(run(*args, **{**kwargs, 'client': proxy}), proxy.ledger,
                               kwargs.get('emit', print))
            except (GhError, OSError) as exc:
                if proxy.ledger.pending is None:
                    raise
                return failure(verb, exc, proxy.ledger, kwargs.get('emit', print))
        return guard
    return decorate


def fingerprint(payload):
    """同一操作重跑的身分比對（需求方 2026-09-16 裁定①逐字「operation fingerprint／operation ID
    只用於同一操作重跑的身分比對，⛔ 不用它判斷內容語意」）。

    口徑＝canonical JSON 的 sha256 逐字相等，與 `wf.compose.validate._equal` 同層級的機械比對；
    ⛔ 不比對內容同義、⛔ 不判斷該不該（core/verbs.md §2）。
    只回字串給本機判定用：⛔ 不得被送進任何請求的 payload 或 header、⛔ 不寫進卡面、⛔ 不新增 D 類。
    """
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                     separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def already_posted(previous, payload):
    """卡上既有的那些 `wf-return` 區塊裡，有沒有與本次交回單逐字相同的一則。
    判定證據只取 `wf-return` 區塊（在 `wf.gh.writes.LABELS` 內），⛔ 不讀散文、⛔ 不讀首行。"""
    mine = fingerprint(payload)
    return any(isinstance(block, dict) and fingerprint(block) == mine for block in previous)


@dataclass(frozen=True)
class BoardDecision:
    """`open` 在板上時的回讀分流結果；verdict ∈ new／resume／converge／refuse。"""
    verdict: str
    item_id: str | None = None
    completed: tuple[str, ...] = ()
    line: str = ''


def board_decision(plan_card, current, item):
    """core/verbs.md §2 D2 的回讀分流（WF-016）。純計算：⛔ 不碰 client、⛔ 不寫任何遠端。

    回讀證據只取卡面 `wf-card` 區塊與板上有沒有這一項，⛔ 不讀 `wf:move`／`wf:edit`／`wf:reject`
    事件留言的 body（其 body 無任何 CLI 可讀區塊，本卡⛔ 不為它新增可讀區塊）。

    ⓐ 不在板上＝`new`，照常 add_to_project。
    ⓑ 在板上而卡面無 `wf-card`＝回讀是本次 write plan 的前綴（上一次只完成 add_to_project）：
       `resume`——沿用板上既有 item、⛔ 不重複 add_to_project，已完成項列進 completed_writes。
    ⓒ 在板上而卡面與本次 plan 全等＝`converge`：rc=0、⛔ 不重寫。
    ⓓ 其餘（他人已推進的卡）＝`refuse`，維持基線的 D2 編號與逐字理由「已在板上」。
    """
    if item is None:
        return BoardDecision('new')
    done = (f'add_to_project・{item["id"]}',)
    if current is None:
        return BoardDecision('resume', item['id'], done,
                             f'已在板上而卡面無 wf-card：續作剩餘寫入（已完成的寫入：{done[0]}）')
    if _equal(current, plan_card):
        return BoardDecision('converge', item['id'], (*done, 'update_card_body・卡面 JSON'),
                             '已在板上且卡面與本次寫入全等：收斂、⛔ 不重寫')
    return BoardDecision('refuse')


def move_resume(current, from_node, to_node, legal, printed, *, client, number, catalog,
                location, item_id):
    """core/verbs.md §2 D1 的回讀分流（WF-016）。回 None＝轉移合法、照常往下跑。

    回讀證據＝卡面 `wf-card` 區塊的 `stage`／`state` 與五個投影欄，⛔ 不讀事件留言 body。
    轉移不合法時：
    · 卡面回讀不是本次目標＝維持基線的 D1 編號與逐字理由 `<from> → <to> 不在合成表內`；
    · 卡面回讀已是本次目標而五欄全等＝上一次已整批完成 ⇒ rc=0 收斂、⛔ 不重寫；
    · 卡面回讀已是本次目標而五欄不等＝回讀是本次 plan 的前綴 ⇒ 續作剩餘的投影欄寫入，
      並把上一次已完成的卡面 JSON 寫入一併列進 completed_writes。
    ⛔ 不 retry、⛔ 不 rollback、⛔ 不補發事件留言（CLI ⛔ 不讀事件留言，無從得知它貼出與否）。
    """
    # 函式內 import：`_write` 模組級已 import 本檔的結果物件，互引會成環（同 move.py 對
    # move_modules 的既有做法）。⛔ 不得推出「本檔可以自己發遠端寫入」——寫入仍只經六原語。
    from wf.verbs._write import reconcile, reject
    if legal:
        return None
    if from_node != to_node:
        return reject(client, number, 'D1', f'{from_node} → {to_node} 不在合成表內')
    done = ['update_card_body・卡面 JSON']
    changed = [] if item_id is None else reconcile(
        current, client=client, catalog=catalog, item_id=item_id,
        project_owner=location['owner'], project_number=location['number'])
    if changed:
        printed.append('續作剩餘寫入・投影欄：' + '、'.join(changed))
        done += [f'write_project_field・{name}' for name in changed]
    else:
        printed.append(f'卡面回讀已等於本次目標 {to_node}：收斂、⛔ 不重寫')
    return receipt(WriteResult(0, card=current), done)
