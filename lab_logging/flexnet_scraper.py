import os
import re
from datetime import datetime
from collections import Counter
from lease_record import LeaseRecord


def readFlexNetFile(fName, moduleList):
    """
    Parses a FlexNet file into a list of LeaseRecords

    Arguments:
        fName (path or string) -- The file to be read.
        moduleList (list(str)) -- The modules for which to find user usage data

    Returns:
        list(LeaseRecord)-- The LeaseRecords for the read file.
    """

    file = open(fName, "r")
    textBlock = file.read()
    file.close()
    readTime = extractReadTime(textBlock)
    leaseRecords = []
    # if lmgrdNotRunning(textBlock):
    #     return []
    for moduleName in moduleList:
        moreRecords = extractX(textBlock, moduleName, readTime)
        leaseRecords.extend(moreRecords)
    return leaseRecords


def extractReadTime(textBlock):
    """
    Extracts the generation date from the FlexNet file block text.

    Arguments:
        textBlock (str) -- The read file as a giant string.

    Returns:
        (datetime) -- The datetime of which the file was generated.
    """
    m = re.search(
        r'status on (?P<dayOfWeek>[\S]*) (?P<datetime>.*)\n', textBlock)
    fileDateTime = m.group('datetime')
    datetimeObject = datetime.strptime(fileDateTime, '%m/%d/%Y %H:%M')
    return datetimeObject


# def lmgrdNotRunning(textBlock):
#     m = re.search(r'lmgrd is not running', textBlock)
#     return m == NoneType


def extractX(textBlock, module, readTime):
    """
    Parses the FlexNet file text for the specified module.

    Arguments:

    textBlock (str) -- The file contents as a giant string module
    (str) -- The module to be searched for readTime (datetime) -- The time the
    file was created.  Used to specifiy the lastSeen attribute of the
    LeaseRecords.

    Returns:

    (list(LeaseRecords)) -- All LeaseRecords associated with the
    specified module.
    """

    opening = r'Users of ' + module
    closing = r'Users of'
    search = opening + r'([\w\W]*?)' + closing
    searchRes = re.search(search, textBlock)
    if not searchRes:
        print(readTime, module, "can't be found")
        return list()
    userBlock = searchRes.group(0)
    lines = userBlock.split('\n')
    nLines = len(lines)
    #   mencagli FW6 FW76 (v5.31) (FW90/1718 3504), start Fri 6/22 10:21
    search = (r'(?:[\s]*)(?P<user>[\S]*) (?P<server>[\S]*) (?P<terminal>[\S]*) ' +
              r'\((?P<version>[\w\W]*?)\) \((?P<licServer>[\w\W]*?)\), ' +
              r'start (?P<dayOfWeek>[\w\W]*?) (?P<partialStartTime>[\w\W]*)')
    regexC = re.compile(search)
    records = list()
    moduleHeaderLineCount = 5
    moduleTailLineCount = 2
    for i in range(moduleHeaderLineCount, nLines - moduleTailLineCount):
        line = lines[i]
        lineResults = regexC.search(line)
        user = lineResults.group('user')
        server = lineResults.group('server')
        terminal = lineResults.group('terminal')
        version = lineResults.group('version')
        licServer = lineResults.group('licServer')
        partialStartTimeStr = lineResults.group('partialStartTime')
        # partialStartTime doesn't supply a year
        startTime = datetime.strptime(partialStartTimeStr, '%m/%d %H:%M')
        # So we guess that it will be the same as the year the file was written
        startTime = startTime.replace(year=readTime.year)
        if startTime > readTime:  # However, this may not be true around NYE.
            startTime = startTime.replace(year=(startTime.year - 1))
        leaseRec = LeaseRecord(user, module, server, terminal, version,
                               licServer, startTime, readTime, True)
        records.append(leaseRec)
    return records
