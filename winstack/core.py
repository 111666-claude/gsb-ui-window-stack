"""UI 窗口栈：窗口层级、模态阻断、关闭顺序、焦点恢复与栈上限。

实现口径见 README：内部维护按 (layer, 打开序号) 排序的打开窗口列表，
focus / blocked / order 不做全表扫描，单次摊还 O(1)~O(log n)。
"""

from bisect import bisect_left, bisect_right, insort


class WindowStack:
    """窗口栈。"""

    def __init__(self, limit=8):
        self.limit = limit
        self.by_id = {}
        self.pushed_out = 0
        self.scanned = 0
        self._seq = 0
        self._order = []  # 打开的窗口，按 (layer, seq, win_id) 从底到顶排序
        self._modals = []  # 打开的模态窗口的 (layer, seq)，有序

    def open(self, win_id, layer=0, modal=False):
        """打开一个窗口。"""
        old = self.by_id.get(win_id)
        if old is not None and old["open"]:
            self._remove(old)
        self._seq += 1
        key = (layer, self._seq)
        entry = {"id": win_id, "layer": layer, "modal": modal, "open": True,
                 "key": key}
        self.by_id[win_id] = entry
        insort(self._order, (layer, self._seq, win_id))
        if modal:
            insort(self._modals, key)
        while len(self._order) > self.limit:
            bottom = self._order.pop(0)
            victim = self.by_id[bottom[2]]
            victim["open"] = False
            if victim["modal"]:
                self._modals.pop(bisect_left(self._modals, victim["key"]))
            self.pushed_out += 1
        return True

    def _remove(self, entry):
        key = entry["key"]
        index = bisect_left(self._order, (key[0], key[1], entry["id"]))
        self._order.pop(index)
        if entry["modal"]:
            self._modals.pop(bisect_left(self._modals, key))

    def close(self, win_id):
        """关闭一个窗口：只允许关栈顶。"""
        entry = self.by_id.get(win_id)
        if entry is None or not entry["open"]:
            return False
        if not self._order or self._order[-1][2] != win_id:
            return False
        entry["open"] = False
        self._remove(entry)
        return True

    def order(self):
        """从底到顶的窗口顺序。"""
        self.scanned += 1
        return [item[2] for item in self._order]

    def focus(self):
        """当前接收输入的窗口，即栈顶。"""
        self.scanned += 1
        if not self._order:
            return None
        return self._order[-1][2]

    def blocked(self, win_id):
        """该窗口是否被模态挡住。"""
        self.scanned += 1
        entry = self.by_id.get(win_id)
        if entry is None or not entry["open"]:
            return False
        return bisect_right(self._modals, entry["key"]) < len(self._modals)
