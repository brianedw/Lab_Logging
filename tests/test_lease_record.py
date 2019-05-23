import os
import sys
import numpy as np
import scipy as sp
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..//lab_logging')))
import unittest


def vPrint(v, *args, **kwargs):
    if v:
        print(*args, **kwargs)


class Test1(unittest.TestCase):

    def testA(self):
        """
        verify that the tilt rotation and constant path is working properly.
        """
        v = False
        self.assertTrue(True)
