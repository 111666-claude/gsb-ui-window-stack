"""UI 窗口栈：窗口层级、模态阻断、关闭顺序、焦点恢复与栈上限。"""

import heapq


class WindowStack:
    """窗口栈。

    内部只保留当前打开的窗口：每个 layer 一个按打开顺序排列的字典，
    另有 layer 的最小/最大堆与模态窗口的最大堆（懒删除），
    因此 focus 为 O(1)，blocked 摊还 O(1)，不随窗口总数线性扫描。
    """

    def __init__(self, limit=8):
        self.limit = limit
        # layer -> {win_id: entry}，字典序即该层内的打开顺序
        self.layers = {}
        self.by_id = {}
        # 懒删除堆：层为空时弹出；该层重新有窗口时再压入
        self._layer_min = []
        self._layer_max = []
        # (-layer, -seq, entry)：当前最高模态在堆顶
        self._modals = []
        self._top_id = None
        self._size = 0
        self._seq = 0
        self.pushed_out = 0
        self.scanned = 0

    def open(self, win_id, layer=0, modal=False):
        """打开一个窗口；同 id 仍处于打开状态时返回 False 且不改状态。"""
        old = self.by_id.get(win_id)
        if old is not None and old["open"]:
            return False
        self._seq += 1
        entry = {
            "id": win_id,
            "layer": layer,
            "modal": modal,
            "seq": self._seq,
            "open": True,
        }
        bucket = self.layers.setdefault(layer, {})
        if not bucket:
            heapq.heappush(self._layer_min, layer)
            heapq.heappush(self._layer_max, -layer)
        bucket[win_id] = entry
        self.by_id[win_id] = entry
        self._size += 1
        if modal:
            heapq.heappush(self._modals, (-layer, -entry["seq"], entry))
        if self._top_id is None or (layer, entry["seq"]) > self._top_key():
            self._top_id = win_id
        if self._size > self.limit:
            self._push_out_bottom()
        return True

    def close(self, win_id):
        """关闭栈顶窗口；非栈顶、不存在或已关闭返回 False 且不改状态。"""
        entry = self.by_id.get(win_id)
        if entry is None or not entry["open"] or self._top_id != win_id:
            return False
        self._detach(entry)
        entry["open"] = False
        self._refresh_top()
        return True

    def order(self):
        """从底到顶：先按 layer 升序，同 layer 按打开顺序。"""
        result = []
        for layer in sorted(self.layers):
            result.extend(self.layers[layer])
        return result

    def focus(self):
        """当前接收输入的窗口（栈顶）；栈空返回 None。"""
        return self._top_id

    def blocked(self, win_id):
        """窗口上方存在打开的模态窗口时返回 True；已关闭窗口返回 False。"""
        entry = self.by_id.get(win_id)
        if entry is None or not entry["open"]:
            return False
        modal = self._top_modal()
        if modal is None:
            return False
        return (entry["layer"], entry["seq"]) < (modal["layer"], modal["seq"])

    def _top_key(self):
        top = self.by_id[self._top_id]
        return top["layer"], top["seq"]

    def _top_modal(self):
        modals = self._modals
        while modals:
            _, _, entry = modals[0]
            if entry["open"] and self.by_id.get(entry["id"]) is entry:
                return entry
            self.scanned += 1
            heapq.heappop(modals)
        return None

    def _bottom_layer(self):
        while self._layer_min:
            layer = self._layer_min[0]
            if self.layers.get(layer):
                return layer
            self.scanned += 1
            heapq.heappop(self._layer_min)
        return None

    def _refresh_top(self):
        while self._layer_max:
            layer = -self._layer_max[0]
            bucket = self.layers.get(layer)
            if bucket:
                self._top_id = next(reversed(bucket))
                return
            self.scanned += 1
            heapq.heappop(self._layer_max)
        self._top_id = None

    def _push_out_bottom(self):
        layer = self._bottom_layer()
        bucket = self.layers[layer]
        win_id = next(iter(bucket))
        entry = bucket.pop(win_id)
        self._size -= 1
        entry["open"] = False
        self.pushed_out += 1

    def _detach(self, entry):
        del self.layers[entry["layer"]][entry["id"]]
        self._size -= 1
