import os
import sys
import glob
from flexnet_scraper import readFlexNetFile
from sorter_allocator import SorterAllocator
import datetime
from math import floor, ceil

import plotly
plotly.__version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.graph_objs as go
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
        self.openLicenses = list()
        self.closedLicenses = list()
        self.licByModule = dict()

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
        currentLics = recordList.copy()
        openLics = self.openLicenses
        recentlyClosed = listDifference(openLics, currentLics)
        self.closedLicenses.extend(recentlyClosed)
        recentlyOpened = listDifference(currentLics, openLics)
        newOpenLics = listDifference(openLics, recentlyClosed)
        newOpenLics = listDifference(newOpenLics, recentlyOpened)
        listUpdate(newOpenLics, currentLics, {'lastSeen'})
        newOpenLics.extend(recentlyOpened)
        self.openLicenses = newOpenLics

    def sortLicsByModule(self):
        self.licByModule = dict()
        for lic in self.closedLicenses:
            module = lic.module
            if module not in self.licByModule:
                self.licByModule[module] = []
            self.licByModule[module].append(lic)
        for lic in self.openLicenses:
            module = lic.module
            if module not in self.licByModule:
                self.licByModule[module] = []
            self.licByModule[module].append(lic)

    def gatherFileNames(self):
        """
        Creates a sorted list of all files in the target directory that begin
        with the target program name.

        Assuming that the files were created with the accompanying CMD scripts,
        the filenames should follow the convention [prog]_[YYYY]_[MM]_[DD].txt
        and therefore, the canonical order will be equal to the chronological
        one.
        """
        targetPath = os.path.join(
            self.dataDirectory, self.targetProgram + "*.txt")
        fileList = glob.glob(targetPath)
        if len(fileList) == 0:
            print("Warning:", targetPath, "does not match any files.")
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

        records = self.closedLicenses.copy()
        records.extend(self.openLicenses)
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

    def makeLicString(self, record):
        r = record
        nSpaces = len(self.modules) - self.modules.index(r.module)
        orderingString = ' ' * nSpaces
        licNumString = '(' + '{0:2d}'.format(r.licNumber) + ')'
        return orderingString + r.module + licNumString

    def buildGannt(self):
        """ Iterates through all of the open and closed records and builds the
        Gannt figure.
        """

        # dict(Task="Job-1", Start='2017-01-01', Finish='2017-02-02',
        # Resource='Abe', Name='Abe(FW1)')
        allRecords = self.closedLicenses.copy()
        allRecords.extend(self.openLicenses)
        allRecords.sort(key=self.makeLicString)
        ganntList = list()

        for r in allRecords:

            newBar = dict(
                Task=self.makeLicString(r),
                Start=r.start,
                Finish=r.lastSeen,
                Resource=r.user,
                Name=r.user + '(' + r.server + ')'
            )
            ganntList.append(newBar)
        colors = dict()
        for bar in ganntList:
            user = bar['Resource']
            red = (hash(user + 'r') % 256) / 256.
            grn = (hash(user + 'g') % 256) / 256.
            blu = (hash(user + 'b') % 256) / 256.
            colors[user] = (red, grn, blu)
        fig = ff.create_gantt(
            ganntList, index_col='Resource', show_colorbar=True,
            group_tasks=True, colors=colors)
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
        plot(fig, filename=outPath, auto_open=False,
             include_plotlyjs=False)
        addPlotlyScriptCall(outPath)

    def buildVBarGraphs(self):
        for module in self.modules:
            now = datetime.datetime.today()
            moduleDict = dict() # {-16: {'Nasim': 0.22, 'yasaman': 0.45}, -15: {'Nasim': 0.8, ...}}
            for lic in self.licByModule[module]:
                user = lic.user.lower()
                # print(lic)
                if user not in moduleDict:
                    moduleDict[user] = dict() #{week: value, week: value}
                licAllocDict = weekAllocDict(lic.start, lic.lastSeen, now)
                userModuleDict = moduleDict[user]
                for week, value in licAllocDict.items():
                    if week not in userModuleDict:
                        userModuleDict[week] = 0.
                    userModuleDict[week] += value
            data = []
            for user, usage in moduleDict.items():
                bar = go.Bar(
                    name=user,
                    x=list(usage.keys()),
                    y=list(usage.values())
                )
                data.append(bar)
            layout = go.Layout(barmode='stack', title=module)
            fig = go.Figure(data=data, layout=layout)
            outPath = os.path.join(self.outDirectory, self.targetProgram +
                                    '_' + module + '.html')
            # The 'plot' command generates a file at 'outPath'
            plot(fig, filename=outPath, auto_open=False,
                include_plotlyjs=False)
            addPlotlyScriptCall(outPath)

def addPlotlyScriptCall(fName):
    str1 = open(fName, mode='r')
    text = str1.read()
    str1.close()
    pHeadEnd = text.find("</head>") + 7
    scriptCall = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'
    textSequence = (text[0:pHeadEnd], scriptCall, text[pHeadEnd:])
    newHTML = "".join(textSequence)
    str2 = open(fName,mode='w')
    str2.write(newHTML)
    str2.close()

def listDifference(aList, bList):
    """
    Returns the set difference between aList and bList

    Creates a copy of aList.  Looks for each element of bList in aList and removes it from aList. 
    """
    aCopy = aList.copy()
    for bElem in bList:
        if bElem in aCopy:
            aCopy.remove(bElem)
    return aCopy


def listUpdate(aList, bList, attributes):
    virginIndices = set(range(len(aList)))
    for bElem in bList:
        for i in virginIndices:
            aElem = aList[i]
            if aElem == bElem:
                for att in attributes:
                    aElem.__setattr__(att, bElem.__getattribute__(att))
                virginIndices.remove(i)
                break

def weeksPast(then, now):
    delta = (now - then)
    weeks = delta.total_seconds()/(60*60*24*7)
    return weeks

def weekAllocDict(startDate, endDate, now):
    weeksStart = -weeksPast(startDate, now)
    weeksEnd = -weeksPast(endDate, now)
    allocDict = dict()
    for i in range(floor(weeksStart), floor(weeksEnd)+1):
        bucket = i
        allocDict[bucket] = 1
    # print(allocDict)
    allocDict[floor(weeksStart)] -= weeksStart - floor(weeksStart)
    allocDict[floor(weeksEnd)] -= ceil(weeksEnd) - weeksEnd
    return allocDict