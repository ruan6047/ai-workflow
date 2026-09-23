"""`brief` 第 4 層的 GitHub 唯讀來源：Issue body ＋ 七個核心概念 ＋ **該卡全部留言**。

⛔ 不分類留言：`github.md` §3 的四類是**內容分類**，CLI 判不得——自己加篩選＝CLI 做內容判讀。
`.wf/config.json` 未設 `project`、或該卡尚⛔ 無 Project item 時，七概念照 `facts` 同一形狀
印 `unknown` 且 rc=0，⛔ 不 typed fail（否則採用入口與空板情境會被自己擋掉）。
本模組⛔ 無任何 mutation 能力，走的是與 `facts` 同一條唯讀 `wfx.gh`。
"""
from __future__ import annotations

from dataclasses import dataclass

from wfx.gh import facts as F
from wfx.gh.client import GhClient
from wfx.gh.target import parse_task

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


class GhTaskSource:
    """正式路徑：每次即時讀遠端，⛔ 不快取。測試以注入固定快照的 client 或 TaskSource 取代。"""

    def __init__(self, *, client=None, runner=None, env=None):
        self.client = client
        self.runner = runner
        self.env = env

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
