# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Jörgen Stenarson. <>
from __future__ import print_function, unicode_literals, absolute_import

try:
    from test.support import unlink
except ImportError:
    from test.test_support import unlink

import tempfile
import os
import unittest2

from pyreadline.lineeditor import lineobj
from pyreadline.lineeditor.history import LineHistory

import readline

import pyreadline.logger
pyreadline.logger.sock_silent = False

# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
RL = lineobj.ReadLineTextBuffer


class Test_prev_next_history(unittest2.TestCase):
    t = "test text"

    def setUp(self):
        self.q = q = LineHistory()
        for x in ["aaaa", "aaba", "aaca", "akca", "bbb", "ako"]:
            q.add_history(RL(x))

    def test_previous_history(self):
        hist = self.q
        assert hist.history_cursor == 6
        l = RL("")
        hist.previous_history(l)
        assert l.get_line_text() == "ako"
        hist.previous_history(l)
        assert l.get_line_text() == "bbb"
        hist.previous_history(l)
        assert l.get_line_text() == "akca"
        hist.previous_history(l)
        assert l.get_line_text() == "aaca"
        hist.previous_history(l)
        assert l.get_line_text() == "aaba"
        hist.previous_history(l)
        assert l.get_line_text() == "aaaa"
        hist.previous_history(l)
        assert l.get_line_text() == "aaaa"

    def test_next_history(self):
        hist = self.q
        hist.beginning_of_history()
        assert hist.history_cursor == 0
        l = RL("")
        hist.next_history(l)
        assert l.get_line_text() == "aaba"
        hist.next_history(l)
        assert l.get_line_text() == "aaca"
        hist.next_history(l)
        assert l.get_line_text() == "akca"
        hist.next_history(l)
        assert l.get_line_text() == "bbb"
        hist.next_history(l)
        assert l.get_line_text() == "ako"
        hist.next_history(l)
        assert l.get_line_text() == "ako"


class TestSearchHistory(unittest2.TestCase):
    t = "test text"

    def setUp(self):
        self.q = q = LineHistory()
        for x in ["aaaa", "aaba", "aaca", "akca", "bbb", "ako"]:
            q.add_history(RL(x))

    def test_history_search_backward(self):
        q = LineHistory()
        for x in ["aaaa", "aaba", "aaca", "    aacax", "akca", "bbb", "ako"]:
            q.add_history(RL(x))
        a = RL("aa", point=2)
        for x in ["aaca", "aaba", "aaaa", "aaaa"]:
            res = q.history_search_backward(a)
            assert res.get_line_text() == x

    def test_history_search_forward(self):
        q = LineHistory()
        for x in ["aaaa", "aaba", "aaca", "    aacax", "akca", "bbb", "ako"]:
            q.add_history(RL(x))
        q.beginning_of_history()
        a = RL("aa", point=2)
        for x in ["aaba", "aaca", "aaca"]:
            res = q.history_search_forward(a)
            assert res.get_line_text() == x


class Test_history_search_incr_fwd_backwd(unittest2.TestCase):
    def setUp(self):
        self.q = q = LineHistory()
        for x in ["aaaa", "aaba", "aaca", "akca", "bbb", "ako"]:
            q.add_history(RL(x))

    def test_backward_1(self):
        q = self.q
        self.assertEqual(q.reverse_search_history("b"), "bbb")
        self.assertEqual(q.reverse_search_history("b"), "aaba")
        self.assertEqual(q.reverse_search_history("bb"), "aaba")

    def test_backward_2(self):
        q = self.q
        self.assertEqual(q.reverse_search_history("a"), "ako")
        self.assertEqual(q.reverse_search_history("aa"), "aaca")
        self.assertEqual(q.reverse_search_history("a"), "aaca")
        self.assertEqual(q.reverse_search_history("ab"), "aaba")

    def test_forward_1(self):
        q = self.q
        self.assertEqual(q.forward_search_history("a"), "ako")

    def test_forward_2(self):
        q = self.q
        q.history_cursor = 0
        self.assertEqual(q.forward_search_history("a"), "aaaa")
        self.assertEqual(q.forward_search_history("a"), "aaba")
        self.assertEqual(q.forward_search_history("ak"), "akca")
        self.assertEqual(q.forward_search_history("akl"), "akca")
        self.assertEqual(q.forward_search_history("ak"), "akca")
        self.assertEqual(q.forward_search_history("ako"), "ako")


class Test_empty_history_search_incr_fwd_backwd(unittest2.TestCase):
    def setUp(self):
        self.q = q = LineHistory()

    def test_backward_1(self):
        q = self.q
        self.assertEqual(q.reverse_search_history("b"), "")

    def test_forward_1(self):
        q = self.q
        self.assertEqual(q.forward_search_history("a"), "")


class TestHistoryManipulation(unittest2.TestCase):
    """These tests were added to check that the libedit emulation on OSX and
    the "real" readline have the same interface for history manipulation.
    That's why the tests cover only a small subset of the interface.
    """

    @unittest2.skipUnless(hasattr(readline, "clear_history"),
        "The history update test cannot be run because the "
        "clear_history method is not available.")
    def testHistoryUpdates(self):
        readline.clear_history()

        readline.add_history("first line")
        readline.add_history("second line")

        self.assertEqual(readline.get_history_item(0), None)
        self.assertEqual(readline.get_history_item(1), "first line")
        self.assertEqual(readline.get_history_item(2), "second line")

        readline.replace_history_item(0, "replaced line")
        self.assertEqual(readline.get_history_item(0), None)
        self.assertEqual(readline.get_history_item(1), "replaced line")
        self.assertEqual(readline.get_history_item(2), "second line")

        self.assertEqual(readline.get_current_history_length(), 2)

        readline.remove_history_item(0)
        self.assertEqual(readline.get_history_item(0), None)
        self.assertEqual(readline.get_history_item(1), "second line")

        self.assertEqual(readline.get_current_history_length(), 1)

    @unittest2.skipUnless(hasattr(readline, "append_history_file"),
                          "append_history not available")
    def test_write_read_append(self):
        hfile = tempfile.NamedTemporaryFile(delete=False)
        hfile.close()
        hfilename = hfile.name
        self.addCleanup(unlink, hfilename)

        # test write-clear-read == nop
        readline.clear_history()
        readline.add_history("first line")
        readline.add_history("second line")
        readline.write_history_file(hfilename)

        readline.clear_history()
        self.assertEqual(readline.get_current_history_length(), 0)

        readline.read_history_file(hfilename)
        self.assertEqual(readline.get_current_history_length(), 2)
        self.assertEqual(readline.get_history_item(1), "first line")
        self.assertEqual(readline.get_history_item(2), "second line")

        # test append
        readline.append_history_file(1, hfilename)
        readline.clear_history()
        readline.read_history_file(hfilename)
        self.assertEqual(readline.get_current_history_length(), 3)
        self.assertEqual(readline.get_history_item(1), "first line")
        self.assertEqual(readline.get_history_item(2), "second line")
        self.assertEqual(readline.get_history_item(3), "second line")

        # test 'no such file' behaviour
        os.unlink(hfilename)
        with self.assertRaises(OSError):
            readline.append_history_file(1, hfilename)

        # write_history_file can create the target
        readline.write_history_file(hfilename)

