"""命令行入口：跑窗口栈样例。"""

import argparse

from .core import WindowStack


def build_parser():
    parser = argparse.ArgumentParser(prog="ui-window-stack", description="UI 窗口栈")
    parser.add_argument("--sample", default="modal",
                        help="modal / close / focus / layer / limit / scan")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "modal":
        stack = WindowStack()
        stack.open("a", layer=0)
        stack.open("b", layer=0)
        stack.open("c", layer=0, modal=True)
        print("blocked_a=%s" % str(stack.blocked("a")).lower())
    elif args.sample == "close":
        stack = WindowStack()
        stack.open("a")
        stack.open("b")
        stack.open("c")
        ok = stack.close("b")
        print("ok=%s order=%s" % (str(ok).lower(), ",".join(stack.order())))
    elif args.sample == "focus":
        stack = WindowStack()
        stack.open("a")
        stack.open("b")
        stack.close("b")
        print("focus=%s" % stack.focus())
    elif args.sample == "layer":
        stack = WindowStack()
        stack.open("a", layer=1)
        stack.open("b", layer=0)
        stack.open("c", layer=2)
        print("order=%s" % ",".join(stack.order()))
    elif args.sample == "limit":
        stack = WindowStack(limit=3)
        for index in range(5):
            stack.open("w%d" % index)
        print("size=%d pushed_out=%d" % (len(stack.order()), stack.pushed_out))
    elif args.sample == "scan":
        stack = WindowStack(limit=5000)
        for index in range(3000):
            stack.open("w-%d" % index)
        for _ in range(3000):
            stack.blocked("w-0")
        print("scanned=%d" % stack.scanned)
    else:
        raise SystemExit("需要 --sample modal|close|focus|layer|limit|scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
