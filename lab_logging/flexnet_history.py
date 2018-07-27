import os
import sys
import glob
from flexnet_scraper import readFlexNetFile
from sorter_allocator import SorterAllocator

import plotly
plotly.__version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.figure_factory as ff


class FlexNetHistory:
    """
    Generates a Gannt chart of the license usage for a program which uses the
    FlexNET license manager software.

    Operates by iterating through a directory of text files which where
    generated using the lmstat command and have a properly formatted filename.
    Currently tested on CST and COMSOL.

    Returns:
        [type] -- [description]
    """

    def __init__(self, dataDirectory, outDirectory, targetProgram, modules):
        """
        Standard initialization.  Simply saves the arguments as instance
        variables.

        Arguments:
            dataDirectory {string} -- The directory where the raw data files
                are being dumped.
            outDirectory {string} -- The directory where the output figure
                file is to be generated
            targetProgram {[type]} -- The program for which the raw data
                files were generated. (ie 'CST' or 'COMSOL')
            modules {[type]} -- A list of the modules
        """

        self.dataDirectory = dataDirectory
        self.outDirectory = outDirectory
        self.targetProgram = targetProgram  # 'COMSOL'
        self.modules = modules
        self.openLicenses = set()
        self.closedLicenses = set()

    def buildAllHistory(self):
        """ Obtains an ordered list of all of the filenames and uses them to
        generate snapshots of license usage
        """
        fileNames = self.gatherFileNames()
        for fName in fileNames:
            recordList = readFlexNetFile(fName, self.modules)
            self.appendHistory(recordList)

    def appendHistory(self, recordList):
        """ Takes a new snap shot (recordList) of open licenses and compares it
        to the current sets of open licenses. If a license in the new snap shot
        appears in the open set, the last seen time is updated to reflect the
        new 'lastSeen' value.  If it does not appear, the item is moved from
        the "open" set to the closed set and set to be no longer checked out.

        Arguments: recordList {collection of Record objects} -- A collection of
        Record objects at some point in the near future from those in both the
        'openRecords' and 'closedRecords' attributes.
        """
        # the recently closed records are those that were previously open, but
        # no longer are.  Of course, we can checkIn these licenses.
        openNow = set(recordList)
        oldOpened = self.openLicenses
        newlyClosed = oldOpened.copy()
        for record in openNow:
            newlyClosed.discard(record)
        for record in newlyClosed:
            record.checkedOut = False
            self.closedLicenses.add(record)
        # the only open records are those that are in the latest file.  These
        # contain the most up to date 'lastSeen' information.
        self.openLicenses = openNow

    def gatherFileNames(self):
        """
        Creates a sorted list of all files in the target directory that begin
        with the target program name.

        Assuming that the files were created with the accompanying CMD scripts,
        the filenames should follow the convention [prog]_[YYYY]_[MM]_[DD].txt
        and therefore, the canonical order will be equal to the chronological
        one.
        """
        fileList = glob.glob(self.dataDirectory +
                             self.targetProgram + "*.txt")
        fileList.sort
        return fileList

    def assignLicenseNumbers(self):
        """
        Assigns a number to each record so that records can be paritioned into
        non-overlapping groups.

        Each license type can have multiple instances such that several people
        could be using at the same time.  This assigns each record a ficticious
        number so that they can be partitioned for display purposes.  The
        license server does not have such a concept, but it is neccessary to
        implement a Gannt chart.
        """

        records = list(self.openLicenses.union(self.closedLicenses))
        fModule = lambda record: record.module
        fStart = lambda record: record.start
        fEnd = lambda record: record.lastSeen
        sa = SorterAllocator(fModule, fStart, fEnd, records)
        sa.partition()
        sa.allocate()
        slotBanks = sa.slotBanks
        for module in self.modules:
            if module in slotBanks:
                slotBank = slotBanks[module]
                for (slotIndex, slot) in enumerate(slotBank):
                    for record in slot:
                        record.licNumber = slotIndex

    def buildGannt(self):
        """ Iterates through all of the open and closed records and builds the
        Gannt figure.
        """

        # dict(Task="Job-1", Start='2017-01-01', Finish='2017-02-02',
        # Resource='Abe', Name='Abe(FW1)')
        allRecords = list(self.closedLicenses.union(self.openLicenses))
        allRecords.sort(key=lambda r: r.module + str(r.licNumber))
        ganntList = list()
        for r in allRecords:
            newBar = dict(
                Task=r.module + "(" + str(r.licNumber) + ")",
                Start=r.start,
                Finish=r.lastSeen,
                Resource=r.user,
                Name=r.user + '(' + r.server + ')'
            )
            ganntList.append(newBar)
        fig = ff.create_gantt(
            ganntList, index_col='Resource', show_colorbar=True,
            group_tasks=True)
        for i in range(len(ganntList)):
            fig['data'][i].update(hoverinfo="text", text=ganntList[i]['Name'])
        buttons = list([
            dict(count=7,
                 label='1w',
                 step='day',
                 stepmode='backward'),
            dict(count=1,
                 label='1m',
                 step='month',
                 stepmode='backward'),
            dict(count=6,
                 label='6m',
                 step='month',
                 stepmode='backward'),
            dict(count=1,
                 label='YTD',
                 step='year',
                 stepmode='todate'),
            dict(count=1,
                 label='1y',
                 step='year',
                 stepmode='backward'),
            dict(step='all')])
        fig['layout'].update(title=self.targetProgram)
        fig['layout'].update(hovermode='closest')
        fig['layout'].update(width=1500, height=800)
        fig['layout'].update(showlegend=False)
        fig['layout']['xaxis']['showgrid'] = True
        fig['layout']['xaxis']['rangeselector']['buttons'] = buttons
        # rangeslider currently does not fit data properly.  Likely fixed in
        # later updates.
        # fig['layout']['xaxis']['rangeslider'] = dict()
        fig['layout']['yaxis']['showgrid'] = True
        fig['layout'].update(margin=dict(l=200))
        outPath = os.path.join(self.outDirectory, self.targetProgram + '.html')
        # The 'plot' command generates a file at 'outPath'
        plot(fig, filename=outPath, auto_open=False)
