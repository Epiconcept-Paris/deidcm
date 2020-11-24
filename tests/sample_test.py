# -*- coding: utf-8 -*-

import unittest


class AdvancedTestSuite(unittest.TestCase):
    """Test cases"""
    def test_something(self):
        self.assertIsNone(None)


if __name__ == '__main__':
    unittest.main()
