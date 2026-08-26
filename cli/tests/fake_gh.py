"""FakeGhRunner：純記憶體模擬 `gh project`／`gh issue`／`gh api graphql` 的子集，
只實作 project.py／commands/* 實際會呼叫到的路徑。不打真實網路，讓 open／assign／
handoff／snapshot 的邏輯（必填檢查、交集比對、欄位派發、body 附加 Log）可以在
CI 裡快速、確定性地跑，不依賴 GitHub。

真實的 gh 互動另由本卡交付報告內的「實跑證據」（對 throwaway test Project 的
live smoke run）驗證；這裡只保證「CLI 組裝出的呼叫序列邏輯正確」。
"""

from __future__ import annotations

import json
import re
from typing import Any

from wf_cli.gh import GhRunner


def _parse_flags(args: list[str]) -> dict[str, Any]:
    flags: dict[str, Any] = {}
    i = 0
    while i < len(args):
        tok = args[i]
        if tok.startswith("--"):
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                flags[tok] = args[i + 1]
                i += 2
            else:
                flags[tok] = True
                i += 1
        else:
            i += 1
    return flags


class FakeGhRunner(GhRunner):
    def __init__(self) -> None:
        self.projects: dict[tuple[str, int], dict[str, Any]] = {}
        self.items: dict[str, dict[str, Any]] = {}
        self.issues: dict[str, dict[str, Any]] = {}
        self.content_id_to_item_id: dict[str, str] = {}
        self._seq = 0
        self._issue_seq = 0
        self.graphql_calls: list[str] = []
        #: 測試旋鈕：設成 True 時 `userContentEdits` 的 node 回 `diff: None`
        #: ——模擬「平台記了版本但內容拿不到」，⇒ 呼叫端必須退回寫全文。
        #: ⚠️ 這條退路是必要的：A9 的實測只把已驗證區間由 39 版推到 50 版
        #: （`aiwf#16`），⛔ 沒有證明無上限、⛔ 也沒有官方保證。
        self.revision_content_unavailable = False

    def _next(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}{self._seq}"

    def _ensure_project(self, owner: str, number: str | int) -> dict[str, Any]:
        key = (owner, int(number))
        if key not in self.projects:
            self.projects[key] = {"id": self._next("PVT_"), "fields": {}}
        return self.projects[key]

    def add_builtin_status(self, owner: str, number: int, options: list[str]) -> None:
        """放入 GitHub Projects 內建 Status 的最小測試替身。

        它不是 ``field-create``，因此可驗證 deploy-state 不會為了寫值而修改
        Project 欄位定義。
        """
        project = self._ensure_project(owner, number)
        project["fields"]["Status"] = {
            "id": self._next("PVTF_STATUS_"),
            "gh_type": "ProjectV2SingleSelectField",
            "options": [{"id": self._next("OPT_STATUS_"), "name": name} for name in options],
        }

    def _find_field_by_id(self, field_id: str) -> tuple[str, str]:
        for proj in self.projects.values():
            for name, f in proj["fields"].items():
                if f["id"] == field_id:
                    return name, f["gh_type"]
        raise AssertionError(f"unknown field id {field_id}")

    def _find_option_name(self, field_id: str, option_id: str) -> str:
        for proj in self.projects.values():
            for f in proj["fields"].values():
                if f["id"] == field_id:
                    for opt in f["options"]:
                        if opt["id"] == option_id:
                            return opt["name"]
        raise AssertionError(f"unknown option id {option_id} for field {field_id}")

    def execute(self, args, input: str | None = None) -> str:  # type: ignore[override]
        args = list(args)
        flags = _parse_flags(args)

        if args[:2] == ["project", "view"]:
            number, owner = args[2], flags["--owner"]
            proj = self._ensure_project(owner, number)
            return json.dumps(
                {
                    "id": proj["id"], "owner": {"login": owner}, "number": int(number),
                    "url": f"https://github.com/users/{owner}/projects/{number}",
                }
            )

        if args[:2] == ["project", "field-list"]:
            # ⚠️ **刻意留著，雖然 project.py 已經不再走這條**（`list_fields` 改用原生
            # GraphQL，見 `_LIST_FIELDS_QUERY`）。理由：本分支是「gh 的欄位輸出長怎樣」
            # 的可執行規格，`graphql` 那邊新增的欄位定義分支就是照著它做的，兩者形狀
            # 必須一致。⛔ 不得由「沒有 src 呼叫它」推出「可以刪」——刪掉等於刪掉
            # 等價性的參照物。
            number, owner = args[2], flags["--owner"]
            proj = self._ensure_project(owner, number)
            fields = []
            for name, f in proj["fields"].items():
                entry = {"id": f["id"], "name": name, "type": f["gh_type"]}
                if f["options"]:
                    entry["options"] = f["options"]
                fields.append(entry)
            return json.dumps({"fields": fields, "totalCount": len(fields)})

        if args[:2] == ["project", "field-create"]:
            number, owner = args[2], flags["--owner"]
            proj = self._ensure_project(owner, number)
            name, dtype = flags["--name"], flags["--data-type"]
            options: list[dict[str, str]] = []
            gh_type = "ProjectV2Field"
            if dtype == "SINGLE_SELECT":
                gh_type = "ProjectV2SingleSelectField"
                options = [
                    {"id": self._next("OPT_"), "name": n}
                    for n in flags["--single-select-options"].split(",")
                ]
            field_id = self._next("PVTF_")
            proj["fields"][name] = {"id": field_id, "gh_type": gh_type, "options": options}
            result: dict[str, Any] = {"id": field_id, "name": name, "type": gh_type}
            if options:
                result["options"] = options
            return json.dumps(result)

        if args[:2] == ["project", "item-create"]:
            number, owner = args[2], flags["--owner"]
            self._ensure_project(owner, number)
            item_id = self._next("PVTI_")
            content_id = self._next("DI_")
            self.items[item_id] = {
                "content_type": "DraftIssue", "title": flags["--title"],
                "body": flags.get("--body", ""), "issue_number": None, "issue_url": None,
                "repo": None, "fields": {}, "_project_key": (owner, int(number)),
                "content_id": content_id,
            }
            self.content_id_to_item_id[content_id] = item_id
            return json.dumps(
                {"id": item_id, "title": flags["--title"], "body": flags.get("--body", ""), "type": "DraftIssue"}
            )

        if args[:2] == ["project", "item-add"]:
            number, owner = args[2], flags["--owner"]
            self._ensure_project(owner, number)
            url = flags["--url"]
            issue = self.issues[url]
            item_id = self._next("PVTI_")
            self.items[item_id] = {
                "content_type": "Issue", "title": issue["title"], "body": issue["body"],
                "issue_number": issue["number"], "issue_url": url, "repo": issue["repo"],
                "fields": {}, "_project_key": (owner, int(number)),
            }
            return json.dumps({"id": item_id})

        if args[:2] == ["project", "item-edit"]:
            edit_id = flags["--id"]
            if "--field-id" in flags:
                # 欄位值編輯：--id 必須是 ProjectV2Item 的 PVTI_ id（field-id/project-id 那條路）。
                item = self.items[edit_id]
                name, ftype = self._find_field_by_id(flags["--field-id"])
                if ftype == "ProjectV2SingleSelectField":
                    item["fields"][name] = self._find_option_name(
                        flags["--field-id"], flags["--single-select-option-id"]
                    )
                elif "--number" in flags:
                    item["fields"][name] = float(flags["--number"])
                else:
                    item["fields"][name] = flags["--text"]
                return json.dumps(
                    {"id": edit_id, "title": item["title"], "body": item["body"], "type": item["content_type"]}
                )

            # body／title 編輯：真實 gh 要求 --id 是 draft issue 內容本身的 DI_ id，
            # 用 PVTI_（ProjectV2Item）id 呼叫會被拒絕——這裡刻意重現該限制，
            # 否則本測試替身會比真實 gh 寬鬆，測不出 project.py 對 id 用錯的迴歸。
            if edit_id in self.items:
                raise AssertionError(
                    "FakeGhRunner: gh 真實行為會拒絕用 PVTI_ id 改 body/title，"
                    "必須用 DraftIssue 內容自己的 DI_ id（見 project.set_item_body）"
                )
            item_id = self.content_id_to_item_id[edit_id]
            item = self.items[item_id]
            if "--body" in flags:
                item["body"] = flags["--body"]
            if "--title" in flags:
                item["title"] = flags["--title"]
            return json.dumps(
                {"id": edit_id, "title": item["title"], "body": item["body"], "type": item["content_type"]}
            )

        if args[:2] == ["issue", "create"]:
            repo = flags["--repo"]
            self._issue_seq += 1
            number = self._issue_seq
            url = f"https://github.com/{repo}/issues/{number}"
            self.issues[url] = {
                "title": flags["--title"], "body": flags.get("--body", ""), "number": number, "repo": repo,
            }
            return url + "\n"

        if args[:2] == ["issue", "comment"]:
            repo = flags["--repo"]
            number = int(args[2])
            url = f"https://github.com/{repo}/issues/{number}"
            if url not in self.issues:
                raise AssertionError(f"FakeGhRunner: 對不存在的 issue 留言 {url}")
            self.issues[url].setdefault("comments", []).append(flags["--body"])
            return url + "#issuecomment-1\n"

        if args[:2] == ["issue", "edit"]:
            repo = flags["--repo"]
            number = int(args[2])
            url = f"https://github.com/{repo}/issues/{number}"
            if "--body" in flags:
                # ⭐ 每次改 body 都留一版——這是真實 `userContentEdits` 的語意
                # （2026-08-25 對 aiwf#16 實測：totalCount 50、first:100 全數取回、
                # 每個 node 的 diff 都是**該版的完整 body**、⛔ 不是 diff）。
                self.issues[url].setdefault("revisions", []).append(self.issues[url]["body"])
                self.issues[url]["body"] = flags["--body"]
                for item in self.items.values():
                    if item.get("issue_url") == url:
                        item["body"] = flags["--body"]
            return ""

        raise AssertionError(f"FakeGhRunner: unhandled gh args {args}")

    def graphql(self, query: str, **variables: str) -> dict:  # type: ignore[override]
        self.graphql_calls.append(query)
        if "updateProjectV2ItemFieldValue" in query:
            item = self.items[variables["itemId"]]
            name, field_type = self._find_field_by_id(variables["fieldId"])
            if field_type == "ProjectV2SingleSelectField":
                item["fields"][name] = self._find_option_name(
                    variables["fieldId"], variables["value"]
                )
            else:
                item["fields"][name] = variables["value"]
            return {
                "data": {
                    "updateProjectV2ItemFieldValue": {
                        "projectV2Item": {"id": variables["itemId"]}
                    }
                }
            }

        if "userContentEdits" in query:
            # 形狀：{repository(owner:"o",name:"n"){issue(number:N){userContentEdits(last:1){...}}}}
            m = re.search(r'owner:"([^"]+)",name:"([^"]+)"\)\{issue\(number:(\d+)\)', query)
            if not m:
                raise AssertionError(f"FakeGhRunner: 認不得的 userContentEdits 查詢：{query[:120]}")
            owner, name, number = m.group(1), m.group(2), int(m.group(3))
            url = f"https://github.com/{owner}/{name}/issues/{number}"
            issue = self.issues.get(url)
            if issue is None:
                raise AssertionError(f"FakeGhRunner: 查不存在的 issue 版本 {url}")
            revs = issue.get("revisions", [])
            nodes = [
                {"diff": None if self.revision_content_unavailable else r}
                for r in revs[-1:]
            ]
            return {
                "data": {
                    "repository": {
                        "issue": {
                            "userContentEdits": {"totalCount": len(revs), "nodes": nodes}
                        }
                    }
                }
            }

        if "ProjectV2SingleSelectField" in query:  # 欄位**定義**查詢（project.list_fields）
            # ⛔ 這個判別字串刻意選 `ProjectV2SingleSelectField`：它只出現在欄位定義
            # 查詢裡。items 查詢用的是 `ProjectV2ItemFieldSingleSelectValue`，⚠️ 兩者
            # 看起來很像但**互不為子字串**（Item／Value 夾在中間），故不會誤配。
            #
            # 回傳形狀與上面 `project field-list` 分支**必須一致**（同一組 id／name／
            # 型別／option），只是換成 GraphQL 的外殼：`type` -> `__typename`。
            project_id = variables["projectId"]
            owner_number = next(k for k, v in self.projects.items() if v["id"] == project_id)
            proj = self.projects[owner_number]
            field_nodes = []
            for name, f in proj["fields"].items():
                node: dict[str, Any] = {
                    "__typename": f["gh_type"], "id": f["id"], "name": name
                }
                if f["options"]:
                    node["options"] = f["options"]
                field_nodes.append(node)
            # 單頁：本替身的 project 欄位數遠少於 100。分頁迴圈本身由
            # `tests/test_project_mocked.py` 的兩頁 stub 驗證，不在這裡混進來。
            return {
                "data": {
                    "node": {
                        "fields": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": field_nodes,
                        }
                    }
                }
            }

        if "ProjectV2ItemFieldTextValue" in query:  # 批次讀取 items 的查詢特徵
            project_id = variables["projectId"]
            owner_number = next(k for k, v in self.projects.items() if v["id"] == project_id)
            proj = self.projects[owner_number]
            nodes = []
            for item_id, item in self.items.items():
                if item["_project_key"] != owner_number:
                    continue
                content: dict[str, Any] = {
                    "__typename": item["content_type"], "title": item["title"], "body": item["body"],
                }
                if item["content_type"] == "Issue":
                    content.update(
                        {"number": item["issue_number"], "url": item["issue_url"], "state": "OPEN"}
                    )
                else:
                    content["id"] = item["content_id"]
                field_value_nodes = []
                for name, value in item["fields"].items():
                    ftype = proj["fields"][name]["gh_type"]
                    if ftype == "ProjectV2SingleSelectField":
                        field_value_nodes.append(
                            {"__typename": "ProjectV2ItemFieldSingleSelectValue", "name": value,
                             "field": {"name": name}}
                        )
                    elif isinstance(value, float):
                        field_value_nodes.append(
                            {"__typename": "ProjectV2ItemFieldNumberValue", "number": value,
                             "field": {"name": name}}
                        )
                    else:
                        field_value_nodes.append(
                            {"__typename": "ProjectV2ItemFieldTextValue", "text": value,
                             "field": {"name": name}}
                        )
                nodes.append({"id": item_id, "content": content, "fieldValues": {"nodes": field_value_nodes}})
            return {
                "data": {
                    "node": {"items": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": nodes}}
                }
            }
        raise AssertionError("FakeGhRunner: unhandled graphql query shape")
