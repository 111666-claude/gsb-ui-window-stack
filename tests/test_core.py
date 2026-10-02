import time
import unittest

from winstack.core import WindowStack


class OpenTest(unittest.TestCase):
    def test_empty_stack_has_no_focus(self):
        self.assertIsNone(WindowStack().focus())

    def test_open_adds_window(self):
        stack = WindowStack()
        stack.open("a")
        self.assertEqual(stack.order(), ["a"])

    def test_close_unknown_window_fails(self):
        self.assertFalse(WindowStack().close("ghost"))


class OrderTest(unittest.TestCase):
    def test_same_layer_keeps_insertion_order(self):
        stack = WindowStack()
        stack.open("a")
        stack.open("b")
        self.assertEqual(stack.order(), ["a", "b"])

    def test_close_top_window(self):
        stack = WindowStack()
        stack.open("a")
        self.assertTrue(stack.close("a"))
        self.assertEqual(stack.order(), [])

    def test_layer_ordering_takes_precedence(self):
        stack = WindowStack()
        stack.open("a", layer=1)
        stack.open("b", layer=0)
        stack.open("c", layer=2)
        self.assertEqual(stack.order(), ["b", "a", "c"])

    def test_layer_then_insertion_order(self):
        stack = WindowStack()
        stack.open("a", layer=1)
        stack.open("b", layer=0)
        stack.open("c", layer=1)
        stack.open("d", layer=0)
        self.assertEqual(stack.order(), ["b", "d", "a", "c"])

    def test_each_window_appears_once(self):
        stack = WindowStack()
        stack.open("a")
        stack.open("a")
        stack.open("b")
        self.assertEqual(stack.order(), ["a", "b"])


class CloseOrderTest(unittest.TestCase):
    def test_closing_non_top_fails_and_keeps_state(self):
        stack = WindowStack()
        stack.open("a")
        stack.open("b")
        stack.open("c")
        self.assertFalse(stack.close("b"))
        self.assertEqual(stack.order(), ["a", "b", "c"])
        self.assertEqual(stack.focus(), "c")

    def test_closing_bottom_fails(self):
        stack = WindowStack()
        stack.open("a")
        stack.open("b")
        self.assertFalse(stack.close("a"))
        self.assertEqual(stack.order(), ["a", "b"])

    def test_close_is_idempotent(self):
        stack = WindowStack()
        stack.open("a")
        stack.open("b")
        self.assertTrue(stack.close("b"))
        self.assertFalse(stack.close("b"))
        self.assertFalse(stack.close("b"))
        self.assertEqual(stack.order(), ["a"])

    def test_close_unknown_or_closed_returns_false(self):
        stack = WindowStack()
        self.assertFalse(stack.close("ghost"))
        stack.open("a")
        stack.close("a")
        self.assertFalse(stack.close("a"))

    def test_repeated_sequences_match(self):
        def run():
            stack = WindowStack()
            stack.open("a", layer=1)
            stack.open("b", layer=0, modal=True)
            stack.close("b")
            stack.open("c")
            stack.close("c")
            return stack.order(), stack.focus()
        self.assertEqual(run(), run())


class FocusTest(unittest.TestCase):
    def test_focus_follows_top_by_layer(self):
        stack = WindowStack()
        stack.open("a", layer=1)
        stack.open("b", layer=0)
        self.assertEqual(stack.focus(), "a")

    def test_focus_restored_after_top_closed(self):
        stack = WindowStack()
        stack.open("a")
        stack.open("b")
        stack.open("c")
        self.assertEqual(stack.focus(), "c")
        stack.close("c")
        self.assertEqual(stack.focus(), "b")
        stack.close("b")
        self.assertEqual(stack.focus(), "a")
        stack.close("a")
        self.assertIsNone(stack.focus())


class ModalTest(unittest.TestCase):
    def test_modal_blocks_lower_windows(self):
        stack = WindowStack()
        stack.open("a", layer=0)
        stack.open("b", layer=0)
        stack.open("c", layer=0, modal=True)
        self.assertTrue(stack.blocked("a"))
        self.assertTrue(stack.blocked("b"))
        self.assertFalse(stack.blocked("c"))

    def test_window_above_modal_not_blocked(self):
        stack = WindowStack()
        stack.open("a", layer=0, modal=True)
        stack.open("b", layer=2)
        self.assertFalse(stack.blocked("a"))
        self.assertFalse(stack.blocked("b"))

    def test_blocking_tracks_layer_not_opening_order(self):
        stack = WindowStack()
        stack.open("lo", layer=0)
        stack.open("hi", layer=5)
        stack.open("m", layer=2, modal=True)
        self.assertTrue(stack.blocked("lo"))
        self.assertFalse(stack.blocked("hi"))
        self.assertFalse(stack.blocked("m"))

    def test_blocked_closed_or_unknown_window_is_false(self):
        stack = WindowStack()
        stack.open("a", modal=True)
        self.assertFalse(stack.blocked("ghost"))
        stack.close("a")
        self.assertFalse(stack.blocked("a"))

    def test_blocking_lifted_after_modal_closed(self):
        stack = WindowStack()
        stack.open("a")
        stack.open("m", modal=True)
        self.assertTrue(stack.blocked("a"))
        stack.close("m")
        self.assertFalse(stack.blocked("a"))


class LimitTest(unittest.TestCase):
    def test_no_push_out_within_limit(self):
        stack = WindowStack(limit=8)
        for index in range(8):
            stack.open("w%d" % index)
        self.assertEqual(len(stack.order()), 8)
        self.assertEqual(stack.pushed_out, 0)

    def test_bottom_pushed_out_over_limit(self):
        stack = WindowStack(limit=3)
        for index in range(5):
            stack.open("w%d" % index)
        self.assertEqual(stack.order(), ["w2", "w3", "w4"])
        self.assertEqual(len(stack.order()), 3)
        self.assertEqual(stack.pushed_out, 2)

    def test_pushed_out_window_is_closed(self):
        stack = WindowStack(limit=1)
        stack.open("a")
        stack.open("b")
        self.assertEqual(stack.pushed_out, 1)
        self.assertFalse(stack.close("a"))
        self.assertEqual(stack.focus(), "b")

    def test_pushed_out_by_lowest_layer_not_oldest(self):
        stack = WindowStack(limit=2)
        stack.open("a", layer=5)
        stack.open("b", layer=2)
        stack.open("c", layer=9)
        self.assertEqual(stack.order(), ["a", "c"])
        self.assertEqual(stack.pushed_out, 1)


class ScanCostTest(unittest.TestCase):
    def test_scanned_does_not_grow_linearly_with_window_count(self):
        stack = WindowStack(limit=5000)
        for index in range(3000):
            stack.open("w-%d" % index)
        for _ in range(3000):
            stack.blocked("w-0")
        self.assertLessEqual(stack.scanned, 6000)

    def test_100k_windows_100k_queries_per_second(self):
        stack = WindowStack(limit=200000)
        for index in range(100000):
            stack.open("w-%d" % index, layer=index % 10)
        start = time.perf_counter()
        for index in range(100000):
            stack.focus()
            stack.blocked("w-%d" % index)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 2.0)
        self.assertEqual(stack.focus(), "w-99999")


if __name__ == "__main__":
    unittest.main()
