"""`brief` 第 4 層的 GitHub 唯讀來源：Issue body ＋ 七個核心概念 ＋ **該卡全部留言**，
以及（只在帶入角色時）本卡登記的相連卡（`core/github.md` §1「選用章節：相連任務登記」）。

⛔ 不分類留言：`github.md` §3 的四類是**內容分類**，CLI 判不得——自己加篩選＝CLI 做內容判讀。
`.wf/config.json` 未設 `project`、或該卡尚⛔ 無 Project item 時，七概念照 `facts` 同一形狀
印 `unknown` 且 rc=0，⛔ 不 typed fail（否則採用入口與空板情境會被自己擋掉）。
本模組⛔ 無任何 mutation 能力，走的是與 `facts` 同一條唯讀 `wfx.gh`。

相連卡只照 PM 的登記行讀：行格式是 GitHub URL，因此解讀住這裡（adapter），⛔ 不進 `wfx.core`。
⛔ 不推斷哪些卡相連、⛔ 不判規劃是否已核定、⛔ 不遞迴讀相連卡的相連卡。
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from wfx.core import rules
from wfx.gh import facts as F
from wfx.gh.client import GhClient, GhError
from wfx.gh.target import parse_task, same_repository

UNKNOWN_CONCEPT = 'unknown（Project ⛔ 無此欄，或該卡⛔ 無 item）'


@dataclass(frozen=True)
class TaskData:
    """第 4 層的原樣資料。`fields` 恰七個核心概念鍵（''＝已讀到且未填）。"""
    task: str
    issue_body: str
    fields: dict
    comments: tuple


def _rendered(fact):
    if fact.field_name is None:      # 取不到⛔ 不得印成空值——那是冒充「已讀到且未填」
        return UNKNOWN_CONCEPT
    return '' if fact.value is None else fact.value


_ISSUE = r'https://github\.com/(?P<{p}owner>[A-Za-z0-9_.-]+)/(?P<{p}name>[A-Za-z0-9_.-]+)/issues/(?P<{p}number>\d+)'
# 登記行：`- <issue URL>`，可再接一個空白與 `<issue URL>#issuecomment-<id>`。⛔ 無其他寫法。
LINKED_LINE = re.compile('^- ' + _ISSUE.format(p='') + '(?: (?P<comment>'
                         + _ISSUE.format(p='c_') + r'#issuecomment-(?P<comment_id>\d+)))?$')
# REST 留言回應的 `issue_url`：`https://api.github.com/repos/<owner>/<name>/issues/<n>`
_COMMENT_ISSUE = re.compile(r'/repos/(?P<owner>[^/]+)/(?P<name>[^/]+)/issues/(?P<number>\d+)$')


@dataclass(frozen=True)
class LinkedTask:
    """一筆登記的讀取結果（純資料，`wfx.core` 只讀屬性）。

    `issue_url` 為 None＝行格式不合；`duplicate_of`＝與第幾筆是同一張卡（1-based，⛔ 不重讀）；
    `error`＝相連卡讀取失敗（類別＋首行原因）。規劃留言四態：`comment_url` None＝未登記、
    `comment_error`＝讀取失敗、`comment_foreign`＝回應的 issue_url 不屬於該卡、否則 `comment_body`。
    """
    line: str
    issue_url: str | None = None
    duplicate_of: int | None = None
    error: str | None = None
    state: str | None = None
    body: str | None = None
    comment_url: str | None = None
    comment_error: str | None = None
    comment_foreign: str | None = None
    comment_body: str | None = None


def _failure(exc):
    text = str(exc).strip()
    return f'{type(exc).__name__}: {text.splitlines()[0] if text else ""}'.rstrip()


class GhTaskSource:
    """正式路徑：每次即時讀遠端，⛔ 不快取。測試以注入固定快照的 client 或 TaskSource 取代。

    `linked_clients`＝相連卡用的 client 工廠（slug → client），內部注入點、⛔ 不是公開旗標；
    相連卡一律走**另一個** client 實例，⛔ 不重用本卡 client（它的讀取週期屬於本卡）。
    """

    def __init__(self, *, client=None, runner=None, env=None, linked_clients=None):
        self.client = client
        self.runner = runner
        self.env = env
        self.linked_clients = linked_clients

    def _linked_client(self, slug):
        if self.linked_clients is None:
            return GhClient(slug, runner=self.runner)
        return self.linked_clients(slug)

    def fetch(self, context) -> TaskData:
        task = parse_task(context.task_id)
        slug, _, _ = F.resolve_slug(context, task, env=self.env, runner=self.runner)
        client = GhClient(slug, runner=self.runner) if self.client is None else self.client
        issue = client.issue(task.number)
        comments = tuple((comment.get('url') or '', comment.get('body') or '')
                         for comment in client.issue_comments(issue['id']))
        fields = {concept: UNKNOWN_CONCEPT for concept in F.CONCEPTS}
        location = context.config.get('project')
        if location is not None:
            project = client.project(location['owner'], location['number'])
            field_names = [f['name'] for f in client.project_field_names(project['id'])]
            item = F.locate_item(client.project_items(project['id'], field_names), slug, task.number)
            if item is not None:
                # 七概念以外的平台欄位在此被逐名查略過＝原樣忽略，⛔ 不是第八個核心概念
                fields = {fact.concept: _rendered(fact)
                          for fact in F.concept_facts(field_names, item['fieldValues'])}
        return TaskData(context.task_id, issue.get('body') or '', fields, comments)

    def fetch_linked(self, body, spec):
        """本卡 body 的選用章節逐行讀；章節缺席＝None（未登記）。

        每筆依登記順序回一個 `LinkedTask`。讀取失敗照類別記下，⛔ 不帶內容、⛔ 不當作未登記；
        一筆失敗⛔ 不影響其他筆，也⛔ 不讓整份 brief 失敗。
        """
        text = rules.section_text(body, spec.title)
        if text is None:
            return None
        out, seen = [], []
        for line in (raw.strip() for raw in text.splitlines()):
            if not line:
                continue
            match = LINKED_LINE.match(line)
            if match is None:
                out.append(LinkedTask(line))
                continue
            slug, number = f'{match["owner"]}/{match["name"]}', int(match['number'])
            issue_url = line[2:].split(' ', 1)[0]          # 登記的字面，⛔ 不改寫
            # 序號＝第幾筆登記（含無法解讀的行），與首屏的編號一致
            first = next((index for s, n, index in seen
                          if n == number and same_repository(s, slug)), None)
            seen.append((slug, number, len(out) + 1))
            if first is not None:
                out.append(LinkedTask(line, issue_url, duplicate_of=first))
                continue
            out.append(self._read_linked(line, slug, number, issue_url, match))
        return tuple(out)

    def _read_linked(self, line, slug, number, issue_url, match):
        try:
            issue = self._linked_client(slug).issue(number)
        except GhError as exc:
            return LinkedTask(line, issue_url, error=_failure(exc))
        found = dict(line=line, issue_url=issue_url, state=issue.get('state') or '',
                     body=issue.get('body') or '')
        if match['comment'] is None:
            return LinkedTask(**found)
        found['comment_url'] = match['comment']
        try:
            comment = self._linked_client(f'{match["c_owner"]}/{match["c_name"]}').issue_comment(
                int(match['comment_id']))
        except GhError as exc:
            return LinkedTask(**found, comment_error=_failure(exc))
        where = _COMMENT_ISSUE.search(comment.get('issue_url') or '')
        if where is None or int(where["number"]) != number or not same_repository(
                f"{where['owner']}/{where['name']}", slug):
            return LinkedTask(**found, comment_foreign=comment.get('issue_url') or '（回應⛔ 無 issue_url）')
        return LinkedTask(**found, comment_body=comment.get('body') or '')
