import subprocess
import schedule
import yaml
import daemon
from datetime import datetime


def main():
    """
    The main function reads the config and every x seconds saves the log into
    the file.
    """
    with open("config.yml", "r") as ymlf:
        cfg = yaml.safe_load(ymlf)
    refresh = cfg["main"]["refresh"]
    procNum = cfg["main"]["procNum"]
    try:
        schedule.every(refresh).seconds.do(saveLog(procNum))
    except FileNotFoundError:
        print("Please install iotop command on your system.")


def saveLog(num):
    """
    Opens the txt file and saves the log with the current date and time.
    """
    with open("output.txt", "a") as log:
        now = datetime.now()
        time = now.strftime("%d/%m/%Y, %H:%M:%S")
        log.write(time + "\n")
        psCommand(3, num, log)  # CPU
        psCommand(4, num, log)  # MEM
        ioCommand(num, log)


def psCommand(sortBy, num, output):
    """
    Uses the subprocess to proceed the ps aux command with the sort by a
    given parameter and checks the config file for a number of processes to be
    outputted.
    """
    if num > 0:
        p1 = subprocess.Popen(["ps", "aux"],
                              stdout=subprocess.PIPE,  stderr=output)
        p2 = subprocess.Popen(["sort", "-n", "-k", f"{sortBy}"],
                              stdin=p1.stdout, stdout=subprocess.PIPE,
                              stderr=output)
        p3 = subprocess.Popen(["head", f"-{num}"], stdin=p2.stdout,
                              stdout=output)
    else:
        p1 = subprocess.Popen(["ps", "aux"],
                              stdout=subprocess.PIPE, stderr=output)
        p2 = subprocess.Popen(["sort", "-n", "-k", f"{sortBy}"],
                              stdin=p1.stdout, stdout=output, stderr=output)


def ioCommand(num, output):
    """
    Same as the psCommand just with the iotop to list processes with the
    highest I/O.
    """
    if num > 0:
        p1 = subprocess.Popen(["iotop", "-b", "-qqq", "-P", "-n", "1"],
                              stdout=subprocess.PIPE, stderr=output)
        p2 = subprocess.Popen(["head", f"-{num}"], stdin=p1.stdout,
                              stdout=output, stderr=output)
    else:
        p1 = subprocess.Popen(["iotop", "-b", "-qqq", "-P", "-n", "1"],
                              stdout=output, stderr=output)


with daemon.DaemonContext():
    main()
