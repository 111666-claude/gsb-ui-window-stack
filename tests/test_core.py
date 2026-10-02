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


class LimitTest(unittest.TestCase):
    def test_no_push_out_within_limit(self):
        stack = WindowStack(limit=8)
        for index in range(8):
            stack.open("w%d" % index)
        self.assertEqual(len(stack.order()), 8)
        self.assertEqual(stack.pushed_out, 0)


class LayerOrderTest(unittest.TestCase):
    def test_order_by_layer_then_insertion(self):
        stack = WindowStack()
        stack.open("a", layer=1)
        stack.open("b", layer=0)
        stack.open("c", layer=2)
        self.assertEqual(stack.order(), ["b", "a", "c"])

    def test_higher_layer_is_top_even_when_opened_first(self):
        stack = WindowStack()
        stack.open("hi", layer=2)
        stack.open("lo", layer=0)
        self.assertEqual(stack.focus(), "hi")
        self.assertFalse(stack.close("lo"))
        self.assertTrue(stack.close("hi"))
        self.assertEqual(stack.order(), ["lo"])
        self.assertEqual(stack.focus(), "lo")

    def test_reused_empty_layer_is_ordered_again(self):
        stack = WindowStack()
        stack.open("a", layer=1)
        stack.open("b", layer=0)
        stack.close("a")
        stack.close("b")
        stack.open("c", layer=0)
        stack.open("d", layer=1)
        self.assertEqual(stack.order(), ["c", "d"])
        self.assertEqual(stack.focus(), "d")


class ModalTest(unittest.TestCase):
    def test_modal_blocks_windows_below_only(self):
        stack = WindowStack()
        stack.open("a", layer=0)
        stack.open("b", layer=1)
        stack.open("c", layer=2, modal=True)
        stack.open("d", layer=3)
        self.assertTrue(stack.blocked("a"))
        self.assertTrue(stack.blocked("b"))
        self.assertFalse(stack.blocked("c"))
        self.assertFalse(stack.blocked("d"))

    def test_lower_modal_is_blocked_by_higher_modal(self):
        stack = WindowStack()
        stack.open("m1", layer=1, modal=True)
        stack.open("m2", layer=2, modal=True)
        self.assertTrue(stack.blocked("m1"))
        self.assertFalse(stack.blocked("m2"))

    def test_blocking_lifts_after_modal_closes(self):
        stack = WindowStack()
        stack.open("a")
        stack.open("m", modal=True)
        self.assertTrue(stack.blocked("a"))
        self.assertTrue(stack.close("m"))
        self.assertFalse(stack.blocked("a"))

    def test_blocked_unknown_or_closed_window_is_false(self):
        stack = WindowStack()
        stack.open("a")
        stack.open("m", modal=True)
        self.assertFalse(stack.blocked("ghost"))
        stack.close("m")
        self.assertFalse(stack.blocked("m"))


class CloseOrderTest(unittest.TestCase):
    def test_closing_non_top_does_nothing(self):
        stack = WindowStack()
        stack.open("a")
        stack.open("b")
        stack.open("c")
        self.assertFalse(stack.close("b"))
        self.assertEqual(stack.order(), ["a", "b", "c"])
        self.assertEqual(stack.focus(), "c")

    def test_closing_is_idempotent(self):
        stack = WindowStack()
        stack.open("a")
        self.assertTrue(stack.close("a"))
        self.assertFalse(stack.close("a"))
        self.assertFalse(stack.close("a"))
        self.assertEqual(stack.order(), [])

    def test_close_unknown_window_fails_anytime(self):
        stack = WindowStack()
        stack.open("a")
        self.assertFalse(stack.close("ghost"))

    def test_repeated_sequences_are_deterministic(self):
        def run():
            stack = WindowStack()
            stack.open("a", layer=1)
            stack.open("b", layer=0)
            stack.open("c", modal=True)
            stack.close("c")
            stack.close("a")
            return stack.order(), stack.focus(), stack.pushed_out
        self.assertEqual(run(), run())


class FocusTest(unittest.TestCase):
    def test_focus_follows_top_and_recovers_after_close(self):
        stack = WindowStack()
        self.assertIsNone(stack.focus())
        stack.open("a")
        stack.open("b")
        self.assertEqual(stack.focus(), "b")
        stack.close("b")
        self.assertEqual(stack.focus(), "a")
        stack.close("a")
        self.assertIsNone(stack.focus())

    def test_failed_close_keeps_focus(self):
        stack = WindowStack()
        stack.open("a")
        stack.open("b")
        self.assertFalse(stack.close("a"))
        self.assertEqual(stack.focus(), "b")


class PushOutTest(unittest.TestCase):
    def test_bottom_window_is_pushed_out(self):
        stack = WindowStack(limit=3)
        for index in range(5):
            stack.open("w%d" % index)
        self.assertEqual(len(stack.order()), 3)
        self.assertEqual(stack.order(), ["w2", "w3", "w4"])
        self.assertEqual(stack.pushed_out, 2)
        self.assertEqual(stack.focus(), "w4")

    def test_pushed_out_window_counts_as_closed(self):
        stack = WindowStack(limit=1)
        stack.open("a")
        stack.open("b")
        self.assertEqual(stack.pushed_out, 1)
        self.assertFalse(stack.close("a"))
        self.assertFalse(stack.blocked("a"))


class InvariantTest(unittest.TestCase):
    def test_order_has_no_duplicates(self):
        stack = WindowStack(limit=100)
        for index in range(50):
            stack.open("w%d" % index, layer=index % 4)
        order = stack.order()
        self.assertEqual(len(order), len(set(order)))


class ScanCostTest(unittest.TestCase):
    def test_queries_do_not_scan_all_windows(self):
        stack = WindowStack(limit=5000)
        for index in range(3000):
            stack.open("w-%d" % index)
        for _ in range(3000):
            stack.blocked("w-0")
            stack.focus()
            stack.order()
        self.assertLessEqual(stack.scanned, 6000)

    def test_100k_windows_support_100k_queries_per_second(self):
        import time
        stack = WindowStack(limit=200000)
        for index in range(100000):
            stack.open("w-%d" % index, layer=index % 16)
        start = time.perf_counter()
        for index in range(100000):
            stack.blocked("w-%d" % index)
            stack.focus()
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 1.0)


if __name__ == "__main__":
    unittest.main()
