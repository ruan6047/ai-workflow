"""typed 失敗。缺必要層一律 raise，⛔ 不靜默略過、⛔ 不以空結果冒充。"""


class WfxError(Exception):
    """所有 wfx 失敗的基底；CLI 以 rc≠0 結束。"""


class LayerMissing(WfxError):
    """四層注入中，某個必要層取不到。

    使用者層的模型資料檔缺失⛔ 不走這條——那是合法的 unknown。
    """

    def __init__(self, kind: str, path: str, detail: str = "") -> None:
        self.kind = kind
        self.path = path
        self.detail = detail
        msg = f"缺少必要層 {kind}：{path}"
        if detail:
            msg = f"{msg}（{detail}）"
        super().__init__(msg)


class MalformedInput(WfxError):
    """輸入的形狀不對（JSON 壞掉、必要鍵缺、出現未知鍵）。⛔ 不判內容好壞。"""


class ValueNotInDomain(WfxError):
    """值不在 rules/core/values.md 的值域內。訊息只談值域。"""

    def __init__(self, concept: str, value: str, allowed: tuple[str, ...]) -> None:
        super().__init__(
            f"{concept} 的值 {value!r} 不在值域內；值域＝{'／'.join(allowed)}"
        )
