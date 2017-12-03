# -*- coding: utf-8 -*-
import unittest


class BaseTestCase(unittest.TestCase):

    debug = False

    def setUp(self):
        if self.debug:
            print("setUp")
    # end of setUp

    def tearDown(self):
        if self.debug:
            print("tearDown")
    # end of tearDown

# end of BaseTestCase


class FunctionalTest(BaseTestCase):

    def test_unittest_works(self):
        self.assertEqual(1, 1)
    # end of test_unittest_works

# end of FunctionalTest
