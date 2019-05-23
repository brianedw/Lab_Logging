import sys
import os
import glob
from flexnet_history import FlexNetHistory
from comp_history import CompHistory
import datetime
import traceback

dataDir = "C:\\lab_logging\\dump\\"
outDir = "C:\\xampp\\htdocs\\plotly_depot"
outDir = "C:\\Bitnami\\dokuwiki-20180422b-3\\apache2\\htdocs\\plotly_depot"


def buildLUMChart():
    """
    Builds the Lumerical usage chart and places it in the designated directory.
    """
    try:
        moduleList = [
            'FDTD_Solutions_design', 'MODE_Solutions_design']
        history = FlexNetHistory(dataDir, outDir, "LUM", moduleList)
        history.buildAllHistory()
        history.assignLicenseNumbers()
        history.buildGannt()
        print("LUM Chart Success")
    except:
        traceback.print_exc()
        print("LUM Chart Failed")

def buildCOMSOLChart():
    """
    Builds the COMSOL usage chart and places it in the designated directory.
    """
    try:
        moduleList = [
            'COMSOLGUI', 'WAVEOPTICS', 'RF', 'HEATTRANSFER', 'ACOUSTICS',
            'LLMATLAB', 'CADIMPORT', 'OPTIMIZATION']
        history = FlexNetHistory(dataDir, outDir, "COMSOL", moduleList)
        history.buildAllHistory()
        history.assignLicenseNumbers()
        history.buildGannt()
        history.sortLicsByModule()
        history.buildVBarGraphs()
        print("COMSOL Chart Success")
    except:
        traceback.print_exc()
        print("COMSOL Chart Failed")


def buildCSTChart():
    """
    Builds the CST usage chart and places it in the designated directory.
    """
    try:
        moduleList = [
        'frontend', 'Solver_TimeDomain', 'Solver_FrequencyDomain',
            'Solver_Eigenmode', 'Solver_IntegralEquation',
            'Solver_PrintedCircuitBoard']
        history = FlexNetHistory(dataDir, outDir, "CST", moduleList)
        history.buildAllHistory()
        history.assignLicenseNumbers()
        history.buildGannt()
        print("CST Chart Success")
    except:
        traceback.print_exc()
        print("CST Chart Failed")


def buildCompChart(compName):
    """
    Generates a computer usage chart and places it in the designated directory.

    Arguments: compName {str} -- The computer name as it would appear in the
    log files.
    """
    try:
        cHist = CompHistory(dataDir, outDir, compName)
        cHist.buildAllHistory()
        cHist.buildScatterPlot()
        print("Comp Chart Success: "+compName)
    except:
        traceback.print_exc()
        print("Comp Chart Failed: "+compName)


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
