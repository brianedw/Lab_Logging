import re
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
from collections import namedtuple


_systemUsers = {'local service', 'maxwell', 'n/a', 'network service', 'system'}

Process = namedtuple('Process', ['imageName', 'pid', 'mem', 'user', 'time'])
Process.imageName.__doc__ = "str: The name of the running process (ie notepad.exe)"
Process.pid.__doc__ = "int: The unique process identification number"
Process.mem.__doc__ = "float: The amount of memory in kB that is currently used by the process"
Process.user.__doc__ = "str: The user name of the process owner (ie maxwell)"
Process.time.__doc__ = "float: The total number of seconds the process has been running"


# class Process:

#     def __init__(self, imageName, pid, user, mem, time):
#         self.imageName = imageName
#         self.pid = pid
#         self.mem = mem
#         self.user = user
#         self.time = time


class Comp_Snapshot:

    def __init__(self, date, tasks, memUsage, cpuUsage=None):
        self.date = date
        self.tasks = tasks
        self.memUsage = memUsage
        self.cpuUsage = cpuUsage

    @classmethod
    def fromFile(cls, directory, fName):
        date = extractDateFromFileName(fName)
        tasks = importFile(directory, fName)
        memUsage = buildMemUsage(tasks)
        return cls(date, tasks, memUsage)

    def computeCPUUsage(self, older):
        self.cpuUsage = buildCPUUsage(self.tasks, older.tasks)

    def getSnapshot(self):
        return {'time': self.date, 'mem': self.memUsage, 'cpu': cpuUsage}

    def __repr__(self):
        reprList = []
        reprList.append('comp_snapshot.comp_snapshot(date:')
        reprList.append(repr(self.date))
        reprList.append(')')
        return ''.join(reprList)


def extractDateFromFileName(fName):
    """
    file names are of the form: FW7_2018_06_26_20_05_00.txt
    """
    timeStrArray = fName.replace('.', '_').split('_')[slice(1, -1)]
    timeIntArray = map(int, timeStrArray)
    dt = datetime.datetime(*timeIntArray)
    return dt


def importFile(targetDir, fName):
    """
    fname generated with windows cmd 'tasklist /nh /v /fo csv > fname.txt'
    typical output looks like:
        "System Idle Process","0","Services","0","24 K","Unknown","NT AUTHORITY\SYSTEM","3751:56:47","N/A"
        "System","4","Services","0","26,376 K","Unknown","N/A","1:30:10","N/A"
        "smss.exe","392","Services","0","1,836 K","Unknown","NT AUTHORITY\SYSTEM","0:00:00","N/A"
    """
    processes = list()
    # print("os.getcwd:", os.getcwd())
    # print("Opening ", fName)
    fPath = os.path.join(targetDir, fName)
    file = open(fPath, "r")
    textBlock = file.read().lower()
    lines = textBlock.split('\n')
    slice(1, -1, 2)
    for line in lines:
        if line == '':  # blank lines
            continue
        parts = line.split(r'"')[slice(1, -1, 2)]
        imageName = parts[0]  # str
        # if imageName == "System Idle Process":
        #     continue
        pid = int(parts[1])
        mem = float(parts[4].replace("k", "").replace(",", "").strip())
        # FW7\\name, n/a, nt authority\\system
        user = (parts[6].split("\\"))[-1]  # str
        (h, m, s) = parts[7].split(":")
        time = float(h) * 360 + float(m) * 60 + float(s)
        process = Process(
            imageName=imageName, pid=pid,
            user=user, mem=mem, time=time)
        processes.append(process)
    file.close()
    return processes


def computeTotTime(tasks):
    totTime = 0.
    for process in tasks.values():
        totTime += process.time
    return totTime


def computeTotMem(tasks):
    totMem = 0.
    for process in tasks.values():
        totMem += process.mem
    return totMem


def buildMemUsage(processes):
    """
    Computes the total memory being used by each human user and the system
    and returns a dictionary with this information.
    """
    memUsage = dict()
    for process in processes:
        user = process.user
        if user in _systemUsers:
            user = 'system'
        mem = process.mem
        if user in memUsage:
            memUsage[user] += mem
        else:
            memUsage[user] = mem
    return memUsage


def buildCPUUsage(processesNew, processesOld):
    """
    Totals the processor seconds for each user between this snapshot and a previous one.
    """
    cpuUsage = dict()
    timeDiff = computeTotTime(processesNew) - computeTotTime(processesOld)
    if timeDiff <= 0.:  # Computer Reboot likely
        return cpuUsage
    pDictOld = buildProcessDict(processesOld)
    for pNew in processesNew:
        pid = pNew.pid
        if pid == 0:  # Don't count 'System Idle Process' toward System use
            continue
        if pid in pDictOld:
            pOld = pDictOld[pid]
            sameProcess = sameProcQ(pNew, pOld)
            if not sameProcess:
                pOld = None
        else:
            pOld = None
        attribUser = pNew.user
        if pNew.user in _systemUsers:
            attribUser = 'system'
        else:
            attribUser = pNew.user
        if pOld is None:
            timeChange = pNew.time
        else:
            timeChange = pNew.time - pOld.time
        if attribUser in cpuUsage:
            cpuUsage[attribUser] += timeChange
        else:
            cpuUsage[attribUser] = timeChange
    for attribUser in cpuUsage.keys():
        cpuUsage[attribUser] = cpuUsage[attribUser] / timeDiff
    return cpuUsage


def buildProcessDict(processList):
    procDict = dict()
    for p in processList:
        key = p.pid
        procDict[key] = p
    return procDict


def computeTotTime(processList):
    time = 0.
    for p in processList:
        time += p.time
    return time


def sameProcQ(pNew, pOld):
    samePID = pNew.pid == pOld.pid
    sameUser = pNew.user == pOld.user
    sameImageName = pNew.imageName == pOld.imageName
    greaterTime = pNew.time >= pOld.time
    return (samePID and sameUser and sameImageName and greaterTime)
