import os
import sys
import numpy as np
import scipy as sp
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..//lab_logging')))
import unittest
from flexnet_history import FlexNetHistory


def vPrint(v, *args, **kwargs):
    if v:
        print(*args, **kwargs)


class Test1(unittest.TestCase):

    def testA(self):
        v = True
        outDir = '..//lab_logging//output'
        dataDir = '..//lab_logging//dump'
        moduleList = [
            'COMSOLGUI', 'WAVEOPTICS', 'RF', 'HEATTRANSFER', 'ACOUSTICS',
            'LLMATLAB', 'CADIMPORT', 'OPTLAB']
        vPrint(v, "FlexNetHistory()...")
        history = FlexNetHistory(dataDir, outDir, "COMSOL", moduleList)
        vPrint(v, "buildAllHistory()...")
        history.buildAllHistory()
        vPrint(v, "   len(closed): ", len(history.closedLicenses))
        vPrint(v, "   len(open): ", len(history.openLicenses))
        vPrint(v, "assignLicenseNumbers()...")
        history.assignLicenseNumbers()
        vPrint(v, "buildGannt()...")
        history.buildGannt()
        history.buildVBarGraphs()
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
