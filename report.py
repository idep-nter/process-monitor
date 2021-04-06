from datetime import datetime
import re
import statistics
import numpy
import yaml
import textwrap


def getPeriod(fmt, reg):
    """
    Asks for a time period until it's given in the correct format.
    """
    while True:
        try:
            time = input("Enter a time period (from - to) in the following"
                         "format: DD/MM/YYYY, HH:MM:SS - DD/MM/YYYY, HH:MM:SS\n")
            mo = reg.search(time)
            if not mo:
                raise ValueError
            else:
                time = time.split("-")
                s1, s2 = time[0], time[1]
                s1, s2 = s1.strip(), s2.strip()
                start = datetime.strptime(s1, fmt)
                stop = datetime.strptime(s2, fmt)
                return start, stop
        except ValueError:
            print("Please enter time period in the correct format.")


def makeList(log, start, stop, fmt, reg):
    """
    Returns two lists from ps aux and iotop logs within the given time
    period.
    """
    psList = []
    ioList = []
    flag = True
    listing = False
    while flag:
        for line in log:
            mo = reg.search(line)
            if mo:
                dt = datetime.strptime(mo.group(), fmt)
                if start <= dt <= stop:
                    listing = True
                    continue
                else:
                    flag = False
                    break
            if listing:
                if line[1] == "'":
                    ioList.append(line)
                else:
                    psList.append(line)
        flag = False
    return psList, ioList


def getHeaders():
    """
    Returns the headers for both ps aux and iotop commands.
    """
    psHeader = ["USER", "PID", "%CPU", "%MEM", "VSZ", "RSS", "TTY", "STAT",
                "START", "TIME", "COMMAND"]
    ioHeader = ["b", "TID", "PRIO", "USER", "DISK READ", "DISK WRITE",
                "SWAPIN", "IO>", "COMMAND"]
    return psHeader, ioHeader


def makePsDict(psList, psHeader):
    """
    Returns a dictionary of processes with a cpu and mem usage from the ps aux.
    It gets the wanted values by splitting the data by a given header.
    """
    psData = list(map(lambda s: s.strip().split(None, len(psHeader) - 1),
                      psList))
    psDict = {}
    for entry in psData:
        proc = entry[-1]
        cpu = float(entry[2])
        mem = float(entry[3])
        psDict.setdefault(proc, {}).setdefault("cpu", []).append(cpu)
        psDict.setdefault(proc, {}).setdefault("mem", []).append(mem)
    return psDict


def makeIoDict(ioList, ioHeader):
    """
    Returns a dictionary of processes with i/o usage from the iotop.
    Also modifies each entry by removing unwanted words to make the split work
    in the right way.
    """
    newIoList = []
    for entry in ioList:
        stopWords = ["B/s", "%"]
        entry = entry.split()
        resultEntry = [word for word in entry if word not in stopWords]
        result = " ".join(resultEntry)
        newIoList.append(result)
    ioData = list(map(lambda s: s.strip().split(None, len(ioHeader) - 1),
                      newIoList))
    ioDict = {}
    for entry in ioData:
        proc = entry[-1]
        io = float(entry[-2])
        ioDict.setdefault(proc, {}).setdefault("io", []).append(io)
    return ioDict


def makeAvg(stat):
    avg = sum(stat) / len(stat)
    return avg


def pAvg(proc, d):
    """
    Calculates averages for a process.
    """
    res = []
    try:
        cpu = makeAvg(d[proc]["cpu"])
        mem = makeAvg(d[proc]["mem"])
        res.append(f"{cpu}")
        res.append(f"{mem}")
    except KeyError:
        io = makeAvg(d[proc]["io"])
        res.append(f"{io}")
    return res


def pMax(proc, d):
    """
    Calculates maxes for a process.
    """
    res = []
    try:
        cpu = max(d[proc]["cpu"])
        mem = max(d[proc]["mem"])
        res.append(f"{cpu}")
        res.append(f"{mem}")
    except KeyError:
        io = max(d[proc]["io"])
        res.append(f"{io}")
    return res


def pMedian(proc, d):
    """
    Calculates medians for a process.
    """
    res = []
    try:
        cpu = statistics.median(d[proc]["cpu"])
        mem = statistics.median(d[proc]["mem"])
        res.append(f"{cpu}")
        res.append(f"{mem}")
    except KeyError:
        io = statistics.median(d[proc]["io"])
        res.append(f"{io}")
    return res


def pPercentile(proc, d):
    """
    Calculates percentiles for a process.
    """
    res = []
    try:
        cpu = numpy.percentile(d[proc]["cpu"], 95)
        mem = numpy.percentile(d[proc]["mem"], 95)
        res.append(f"{cpu}")
        res.append(f"{mem}")
    except KeyError:
        io = numpy.percentile(d[proc]["io"], 95)
        res.append(f"{io}")
    return res


def makeFinalDict(d):
    """
    Returns a dictionary with calculated statistics for each process.
    """
    fDict = {}
    for proc in d:
        avg = pAvg(proc, d)
        max = pMax(proc, d)
        med = pMedian(proc, d)
        perc = pPercentile(proc, d)
        fDict.setdefault(proc, {}).setdefault("avg", avg)
        fDict.setdefault(proc, {}).setdefault("max", max)
        fDict.setdefault(proc, {}).setdefault("med", med)
        fDict.setdefault(proc, {}).setdefault("perc", perc)
    return fDict


def hAvgCpu(num, d):
    """
    Returns n processes with the highest average CPU usage.
    """
    l = []
    for proc in d:
        l.append([proc, d[proc]["avg"][0]])
    l = sorted(l, reverse=True, key=lambda avg: avg[1])
    return l[:num-1]


def hAvgMem(num, d):
    """
    Returns n processes with the highest average MEM usage.
    """
    l = []
    for proc in d:
        l.append([proc, d[proc]["avg"][1]])
    l = sorted(l, reverse=True, key=lambda avg: avg[1])
    return l[:num - 1]


def hAvgIo(num, d):
    """
    Returns n processes with the highest average I/O usage.
    """
    l = []
    for proc in d:
        l.append([proc, d[proc]["avg"][0]])
    l = sorted(l, reverse=True, key=lambda avg: avg[1])
    return l[:num - 1]


def hMaxCpu(num, d):
    """
    Returns n processes with the highest maximum CPU usage.
    """
    l = []
    for proc in d:
        l.append([proc, d[proc]["max"][0]])
    l = sorted(l, reverse=True, key=lambda max: max[1])
    return l[:num - 1]


def hMaxMem(num, d):
    """
    Returns n processes with the highest maximum MEM usage.
    """
    l = []
    for proc in d:
        l.append([proc, d[proc]["max"][1]])
    l = sorted(l, reverse=True, key=lambda max: max[1])
    return l[:num - 1]


def hMaxIo(num, d):
    """
    Returns n processes with the highest maximum I/O usage.
    """
    l = []
    for proc in d:
        l.append([proc, d[proc]["max"][0]])
    l = sorted(l, reverse=True, key=lambda max: max[1])
    return l[:num - 1]


def hMedCpu(num, d):
    """
    Returns n processes with the median of CPU usage.
    """
    l = []
    for proc in d:
        l.append([proc, d[proc]["med"][0]])
    l = sorted(l, reverse=True, key=lambda med: med[1])
    return l[:num - 1]


def hMedMem(num, d):
    """
    Returns n processes with the median of MEM usage.
    """
    l = []
    for proc in d:
        l.append([proc, d[proc]["med"][1]])
    l = sorted(l, reverse=True, key=lambda med: med[1])
    return l[:num - 1]


def hMedIo(num, d):
    """
    Returns n processes with the median of I/O usage.
    """
    l = []
    for proc in d:
        l.append([proc, d[proc]["med"][0]])
    l = sorted(l, reverse=True, key=lambda med: med[1])
    return l[:num - 1]


def hPerCpu(num, d):
    """
    Returns n processes with the percentile of CPU usage.
    """
    l = []
    for proc in d:
        l.append([proc, d[proc]["perc"][0]])
    l = sorted(l, reverse=True, key=lambda per: per[1])
    return l[:num - 1]


def hPerMem(num, d):
    """
    Returns n processes with the percentile of MEM usage.
    """
    l = []
    for proc in d:
        l.append([proc, d[proc]["perc"][1]])
    l = sorted(l, reverse=True, key=lambda per: per[1])
    return l[:num - 1]


def hPerIo(num, d):
    """
    Returns n processes with the percentile of I/O usage.
    """
    l = []
    for proc in d:
        l.append([proc, d[proc]["perc"][0]])
    l = sorted(l, reverse=True, key=lambda per: per[1])
    return l[:num - 1]


def pprintDict(d):
    """
    "Pretty prints" each process with statistics in formatted way.
    """
    for proc in d.keys():
        if len(proc) > 80:
            print("\n" + "\n".join(textwrap.wrap(proc, 80)))
            for stat, val in d[proc].items():
                try:
                    print(f"{stat:5} :   %CPU {val[0]}, %MEM {val[1]}")
                except IndexError:
                    print(f"{stat:5} :   %IO {val[0]}")
        else:
            print(f"\n{proc}")
            for stat, val in d[proc].items():
                try:
                    print(f"{stat:5} :   %CPU {val[0]}, %MEM {val[1]}")
                except IndexError:
                    print(f"{stat:5} :   %IO {val[0]}")


def pprintTop(topProc):
    """
    "Pretty prints" top process for each statistic in formatted way.
    """
    for proc in topProc:
        if len(proc[0]) > 80:
            print("\n".join(textwrap.wrap(proc[0], 80)))
            print(f":{proc[1]}")
        else:
            print(f"{proc[0]:<80} : {proc[1]}")


def printRes(num, psD, ioD):
    """
    Prints all output with headers.
    """
    pprintDict(psD)
    pprintDict(ioD)
    ac = hAvgCpu(num, psD)
    print("\nHighest average %CPU:")
    pprintTop(ac)
    am = hAvgMem(num, psD)
    print("\nHighest average %MEM:")
    pprintTop(am)
    ai = hAvgIo(num, ioD)
    print("\nHighest average %IO:")
    pprintTop(ai)
    mc = hMaxCpu(num, psD)
    print("\nHighest maximum %CPU:")
    pprintTop(mc)
    mm = hMaxMem(num, psD)
    print("\nHighest maximum %MEM:")
    pprintTop(mm)
    mi = hMaxIo(num, ioD)
    print("\nHighest maximum %IO:")
    pprintTop(mi)
    mec = hMedCpu(num, psD)
    print("\nHighest median %CPU:")
    pprintTop(mec)
    mem = hMedMem(num, psD)
    print("\nHighest median %MEM:")
    pprintTop(mem)
    mei = hMedIo(num, ioD)
    print("\nHighest median %IO:")
    pprintTop(mei)
    pc = hPerCpu(num, psD)
    print("\nHighest percentile %CPU:")
    pprintTop(pc)
    pm = hPerMem(num, psD)
    print("\nHighest percentile %MEM:")
    pprintTop(pm)
    pi = hPerIo(num, ioD)
    print("\nHighest percentile %IO:")
    pprintTop(pi)


def main():
    try:
        with open("config.yml", "r") as ymlf:
            cfg = yaml.safe_load(ymlf)
        with open("output.txt", "r") as out:
            log = out.readlines()
        topNum = cfg["report"]["topNum"]
        fmt = "%d/%m/%Y, %H:%M:%S"
        reg = re.compile(r"\d+/\d+/\d+, \d+:\d+:\d+")
        start, stop = getPeriod(fmt, reg)
        psHeader, ioHeader = getHeaders()
        psList, ioList = makeList(log, start, stop, fmt, reg)
        if not psList:
            raise ValueError
        psDict = makePsDict(psList, psHeader)
        ioDict = makeIoDict(ioList, ioHeader)
        fPsDict = makeFinalDict(psDict)
        fIoDict = makeFinalDict(ioDict)
        printRes(topNum, fPsDict, fIoDict)
    except FileNotFoundError:
        print("No file named output.txt founded.")
    except ValueError:
        print("No data founded.")


if __name__ == "__main__":
    main()