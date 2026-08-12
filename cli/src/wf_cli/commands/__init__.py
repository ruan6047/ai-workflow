"""動詞註冊清單（DEV-CLI-VERB-REGISTRY1）。

新增一個 CLI 動詞＝在 ``COMMAND_MODULES`` **append 一行** ＋ 放進自己的新檔。
append 是最容易合併的形狀，所以多張新動詞卡不再因為共改 ``cli.py`` 的兩處
（import 區塊＋``add_parser`` 呼叫清單）而互相衝突、被迫序列化。

## 為什麼是顯式 tuple，不是 ``pkgutil`` 自動探索

自動探索雖然讓新動詞零共用檔改動，但會讓註冊集合變成**隱式且開放**——與本 repo
一貫的「顯式、封閉鍵集合、fail-closed」紀律相反（同 marker 鍵集合封閉的理由），
且 ``--help`` 的動詞順序會退化成檔案系統順序。用便利換掉可稽核性在這個 repo 裡
是錯的方向。本清單的**順序即 ``--help`` 的動詞順序**，由這裡的字面順序決定。

## 為什麼元素是模組名字串，不是 import 進來的模組物件

模組物件版（``from . import handoff_cmd`` 後放進 tuple）會讓本 ``__init__`` 在套件
被觸及的當下就 eager import 全部動詞模組，而 ``wf_cli.cleanup`` 反向 import
``wf_cli.commands.assign_cmd``（``TERMINAL_STATUSES``）、``wf_cli.doctor`` 又 import
``wf_cli.cleanup``——於是「先 import ``wf_cli.cleanup`` 或 ``wf_cli.doctor``」這條路徑
會撞上循環 import 而炸掉（實測：``python -c "import wf_cli.cleanup"`` → ImportError
「partially initialized module」）。該環在 ``cli.py`` 當入口時剛好不會觸發，現有測試
也不會照出來，屬於**潛伏**故障。字串版讓本 ``__init__`` 完全不 import 子模組，環就
不存在；模組在 ``cli.build_parser()`` 迭代時才逐一 import。

字串的代價是打錯字不會在 import 期爆掉——這由 ``tests/test_cli_registry.py``
補上：它以檔案系統窮舉 ``*_cmd.py`` 與本清單雙向比對，漏註冊或打錯字都會轉紅。
"""

from __future__ import annotations

#: 動詞模組名（``wf_cli.commands`` 底下的模組，不含 ``.py``）。
#: **順序有意義**：等於 ``wfcli --help`` 列出動詞的順序。
#: 新增動詞請 append 一行；插到中間只在確實要改 help 排序時才做。
COMMAND_MODULES: tuple[str, ...] = (
    "open_cmd",
    "assign_cmd",
    "amend_cmd",
    "deploy_declare_cmd",
    "deploy_state_cmd",
    "handoff_cmd",
    "review_cmd",
    # checkpoint_cmd 註冊 `checkpoint` 與 `contract-baseline` 兩個同源動詞；
    # 位置緊接 review_cmd 之後是為了保住既有的 --help 動詞順序（escalation
    # 帳的兩個事件型別排在查核裁決旁邊），不是 append 到尾端。
    "checkpoint_cmd",
    "doctor_cmd",
    "snapshot_cmd",
)

__all__ = ["COMMAND_MODULES"]
