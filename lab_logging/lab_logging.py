import sys
import os
import glob
from flexnet_history import FlexNetHistory
from comp_history import CompHistory
import datetime

dataDir = "C:\\lab_logging\\dump\\"
outDir = "C:\\xampp\\htdocs\\plotly_depot"


def buildLUMChart():
    """
    Builds the Lumerical usage chart and places it in the designated directory.
    """
    moduleList = [
        'FDTD_Solutions_design', 'MODE_Solutions_design']
    history = FlexNetHistory(dataDir, outDir, "LUM", moduleList)
    history.buildAllHistory()
    history.assignLicenseNumbers()
    history.buildGannt()

def buildCOMSOLChart():
    """
    Builds the COMSOL usage chart and places it in the designated directory.
    """
    moduleList = [
        'COMSOLGUI', 'WAVEOPTICS', 'RF', 'HEATTRANSFER', 'ACOUSTICS',
        'LLMATLAB', 'CADIMPORT']
    history = FlexNetHistory(dataDir, outDir, "COMSOL", moduleList)
    history.buildAllHistory()
    history.assignLicenseNumbers()
    history.buildGannt()


def buildCSTChart():
    """
    Builds the CST usage chart and places it in the designated directory.
    """
    moduleList = [
        'frontend', 'Solver_TimeDomain', 'Solver_FrequencyDomain',
        'Solver_Eigenmode', 'Solver_IntegralEquation',
        'Solver_PrintedCircuitBoard']
    history = FlexNetHistory(dataDir, outDir, "CST", moduleList)
    history.buildAllHistory()
    history.assignLicenseNumbers()
    history.buildGannt()


def buildCompChart(compName):
    """
    Generates a computer usage chart and places it in the designated directory.

    Arguments: compName {str} -- The computer name as it would appear in the
    log files.
    """
    cHist = CompHistory(dataDir, outDir, compName)
    cHist.buildAllHistory()
    cHist.buildScatterPlot()


def main():
    buildCOMSOLChart()
    buildCSTChart()
    buildLUMChart()
    buildCompChart("FW7")
    buildCompChart("FW6")
    buildCompChart("FW5")
    buildCompChart("FW4")
    buildCompChart("FW3")

if __name__ == "__main__":
    main()
