# ui-window-stack

UI 窗口栈：管理窗口的层级、模态阻断、关闭顺序与焦点恢复，只用 Python 标准库。

```
python3 -m winstack.cli --sample modal
python3 -m winstack.cli --sample close
python3 -m winstack.cli --sample focus
python3 -m winstack.cli --sample layer
python3 -m winstack.cli --sample limit
python3 -m winstack.cli --sample scan
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **层级顺序**：`order()` 从底到顶列出打开的窗口，先按 `layer` 升序，
  同一 `layer` 按打开顺序；
- **模态阻断**：打开的模态窗口下面（层级低于它）的所有窗口都是被阻断的，
  `blocked` 对它们返回 True；模态窗口自己和它上面的窗口不受影响。
- **关闭顺序**：只能关闭栈顶窗口，关闭非栈顶返回 False 且不改状态；
  关闭不存在的窗口或已关闭的窗口也返回 False。
- **焦点恢复**：`focus()` 返回当前接收输入的窗口，即栈顶窗口；栈顶被关掉以后，
  焦点回到新的栈顶；栈空时返回 None。
- **栈上限**：打开后窗口数超过 `limit` 时，把最底层窗口顶出，`pushed_out` 加一；
  被顶出的窗口视为已关闭。
- **不变量**：`order()` 里每个窗口只出现一次；关闭是幂等的；
  同一串打开与关闭序列重复执行结果相同。
- **查询代价**：`focus`、`blocked`、`order` 不许每次遍历全部窗口，
  `scanned` 不随窗口数线性增长。
- **规模**：10 万个窗口、每秒 10 万次查询，单次摊还 O(1)。

## 输出契约（不改格式）

```
blocked_a=..
ok=.. order=..
focus=..
order=..
size=.. pushed_out=..
scanned=..
```

## 目录

```
winstack/core.py   层级、模态、关闭与上限
winstack/cli.py    命令行入口
tests/             unittest 用例
```
