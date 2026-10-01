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


if __name__ == "__main__":
    unittest.main()
