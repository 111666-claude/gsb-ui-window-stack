"""UI 窗口栈：窗口层级、模态阻断、关闭顺序、焦点恢复与栈上限。

缺陷：模态不阻断下层、可以关非栈顶、关闭后焦点不回到新的栈顶、
层级排序不生效、栈上限不生效、查询每次扫描全部窗口。
"""


class WindowStack:
    """窗口栈。"""

    def __init__(self, limit=8):
        self.limit = limit
        self.windows = []
        self.by_id = {}
        self.pushed_out = 0
        self.scanned = 0

    def open(self, win_id, layer=0, modal=False):
        """打开一个窗口。"""
        entry = {"id": win_id, "layer": layer, "modal": modal, "open": True}
        self.windows.append(entry)
        self.by_id[win_id] = entry
        return True

    def close(self, win_id):
        """关闭一个窗口。"""
        entry = self.by_id.get(win_id)
        if entry is None or not entry["open"]:
            return False
        entry["open"] = False
        return True

    def order(self):
        """从底到顶的窗口顺序。"""
        self.scanned += len(self.windows)
        return [entry["id"] for entry in self.windows if entry["open"]]

    def focus(self):
        """当前接收输入的窗口。"""
        self.scanned += len(self.windows)
        if not self.windows:
            return None
        return self.windows[-1]["id"]

    def blocked(self, win_id):
        """该窗口是否被模态挡住。"""
        self.scanned += len(self.windows)
        return False
