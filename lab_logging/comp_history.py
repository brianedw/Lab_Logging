import os
import sys
import glob
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.graph_objs as go
from comp_snapshot import Comp_Snapshot


class CompHistory:
    """
    CompHistory generates a Plotly line chart showing CPU and RAM usage for a
    computer.

    CompHistory operates by iterating through a directory of text files.  Each
    text file is to be generated using the 'tasklist' command and represents a
    snapshot of the processes currently running.

    Each process has an associated memory usage and 'cpu time' since its
    inception.  By comparing two chronologically adjacent snapshots, we can
    determine the incremental CPU usage.  The processes are pooled by user,
    with all 'system' users being pooled under 'system'.

    Traces in the scatterplot should not be continuous as users will login and
    log out of the computers.  Plotly would visually interpolate the missing
    data.  We employ two helper classes (Trace and TraceBank) to solve this.
    The TraceBank maintains open and closed traces such that if there is no
    information about a user in the latest snapshot that trace can be closed.
    """

    def __init__(self, dataDirectory, outDirectory, compName):
        """
        CompHistory plots computer usage by processing

        Args:
            dataDirectory: The directory where the data files live.  (ie '.\\dump\\'.)
            outDirectory: The directory where the output files go. (ie 'c:\\bleh')
            compName: Computer name as it appears in the files.  (ie 'FW7')

        Returns:
            Nothing.  File generated.

        Raises:
            KeyError: Raises an exception.
        """
        self.memTraceBank = TraceBank()
        self.cpuTraceBank = TraceBank()
        self.dataDirectory = dataDirectory
        self.outDirectory = outDirectory
        self.compName = compName

    def buildAllHistory(self):
        """
        Gathers the files.  Imports the files as Comp_Snapshots.  Uses the
        Comp_Snapshots to generate memory and CPU usage.

        In order to generate CPU usage, two Comp_Snapshots must be compared.
        """
        baseDir = os.getcwd()
        os.chdir(self.dataDirectory)
        fNames = glob.glob(self.compName + "_20*.*")
        os.chdir(baseDir)
        fNames.sort()
        csOld = Comp_Snapshot.fromFile(self.dataDirectory, fNames[0])
        for i in range(2, len(fNames)):
            csNew = Comp_Snapshot.fromFile(self.dataDirectory, fNames[i])
            csNew.computeCPUUsage(csOld)
            # print(csNew.memUsage)
            date = csNew.date
            self.cpuTraceBank.addValues(csNew.cpuUsage, date)
            self.memTraceBank.addValues(csNew.memUsage, date)
            csOld = csNew
        os.chdir(baseDir)

    def buildScatterPlot(self):
        """
        Generates an Plotly figure at the locaton specified.
        """
        data = self.buildPlotlyData()
        maxes = self.getTraceMaxes(data)
        layout = self.buildPlotlyLayout(maxes)
        fig = dict(data=data, layout=layout)
        outPath = os.path.join(self.outDirectory, self.compName + '.html')
        plot(fig, filename=outPath, auto_open=False)

    def buildPlotlyData(self):
        """
        Builds a collection of Plotly Scatter objects and returns them.

        CPU and Memeroy are each put on different overlapping axes.  The trace
        colors are calculated based on a hash of the user name.

        Returns:
            list(Plotly.graph_objs.Scatter) -- The list of scatter plots.
        """
        cpuTraces = self.cpuTraceBank.getAllTraces()
        memTraces = self.memTraceBank.getAllTraces()
        plotDataCPU = []
        plotDataMem = []
        for trace in cpuTraces:
            user = trace.name
            red = str(hash(user + 'r') % 256)
            grn = str(hash(user + 'g') % 256)
            blu = str(hash(user + 'b') % 256)
            color = "rgb(" + red + ", " + grn + ", " + blu + ")"
            scat = go.Scatter(
                x=trace.x,
                y=trace.y,
                name=user,
                mode='lines',
                line=dict(color=color, width=1),
                yaxis='y',
                showlegend=False)
            plotDataCPU.append(scat)
        for trace in memTraces:
            user = trace.name
            red = str(hash(user + 'r') % 256)
            grn = str(hash(user + 'g') % 256)
            blu = str(hash(user + 'b') % 256)
            color = "rgb(" + red + ", " + grn + ", " + blu + ")"
            scat = go.Scatter(
                x=trace.x,
                y=trace.y,
                name=user,
                mode='lines',
                line=dict(color=color, width=1),
                yaxis='y2',
                showlegend=False)
            plotDataMem.append(scat)
        inLegend = set()
        for scatter in plotDataCPU:
            if scatter['name'] not in inLegend:
                scatter['showlegend'] = True
                inLegend.add(scatter['name'])
        data = list()
        data.extend(plotDataMem)
        data.extend(plotDataCPU)
        return data

    def getTraceMaxes(self, data):
        maxes = dict()
        for scatter in data:
            traceMax = max(scatter.y)
            axisName = scatter.yaxis
            if axisName in maxes.keys():
                newMax = max(maxes[axisName], traceMax)
                maxes[axisName] = newMax
            else:
                maxes[axisName] = traceMax
        return maxes

    def buildPlotlyLayout(self, maxes):
        """
        Generates the plot layout.  Layout is dual overlapping y-axis with
        dates on the x-axis.  Button selectors and slide are also used.

        Arguments: maxes {dict(str = num)} -- The maximum value found in all
        traces that will use that plot axis.

        Returns:
            Plotly layout -- The nested data structures as specified by plotly.
        """
        maxMemDict = dict(FW3=48e6, FW4=48e6, FW5=192e6, FW6=64e6, FW7=64e6)
        maxMem = maxMemDict[self.compName]
        plotCPUMax = max(1.0, maxes['y'])
        plotMemMax = max(maxMem, maxes['y2'])
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
        layout = dict(
            title=self.compName,
            hovermode='closest',
            xaxis=dict(
                rangeslider=dict(),
                type='date',
                rangeselector=dict(buttons=buttons)
            ),
            yaxis=dict(
                title='CPU',
                range=[-0.01 * plotCPUMax, plotCPUMax]),
            yaxis2=dict(
                title='Memory',
                overlaying='y',
                side='right',
                range=[-0.01 * plotMemMax, plotMemMax]))
        return layout


class Trace:
    """
    POPO for holding trace data.
    """

    def __init__(self, name):
        self.x = list()
        self.y = list()
        self.name = name

    def __repr__(self):
        return "Trace" + str((self.name, self.x, self.y))


class TraceBank:
    """
    A collection of traces with intelligent updating.

    If upon updating, there is no information regarding an existing open trace,
    it is closed.  If there information references a trace which is not
    existing it is created.
    """

    def __init__(self):
        """
        Standard init.  Creates instance variables.
        """

        self.openTraces = dict()
        self.closedTraces = list()
        self.cpuMax = 0
        self.memMax = 0

    def addValues(self, usage, date):
        """
        Intelligently adds information to the TraceBank,

        Arguments:

        `usage (dict(str=number, ...))` -- A dict where the keys are the trace
        identifiers and the values are the values to be appended to trace 'y'
        data.

        `date (datetime.datetime)` -- The x value associated with all y-values in
        usage dict.
        """

        for (user, value) in usage.items():
            if user in self.openTraces.keys():
                trace = self.openTraces[user]
                trace.x.append(date)
                trace.y.append(value)
            else:
                trace = Trace(user)
                trace.x.append(date)
                trace.y.append(value)
                self.openTraces[user] = trace
        retiredUsers = self.openTraces.keys() - usage.keys()
        for user in retiredUsers:
            trace = self.openTraces.pop(user)
            self.closedTraces.append(trace)

    def getAllTraces(self):
        """
        Returns a list of all open and closed traces.

        Returns:
            list(Trace) -- list of all open and closed traces.
        """

        allTraces = self.closedTraces.copy()
        allTraces.extend(self.openTraces.values())
        return allTraces
