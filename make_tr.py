#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# The list of source code files and translation files are contained
# in dxf2gcode.pro.
#
# Note if you add .py files to .pro file from the IDE, they will be added
# to the DISTFILES variable. You will have to edit .pro file and move the
# .py files to SOURCES instead.
#

"""
Generates the translation files based on the defined PyQt Project File
"""

import os
import subprocess
import sys
import getopt


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


#
# Linenumbers may be of a little help while doing translations,
# but are a big problem in a multiple-developer environment.
#
# A change to almost any source file will trigger a change in .ts
# files, this leads to many conflicts while merging branches and
# submitting patches.
#
# Thus, the default behavior is to remove <location> tags in all
# .ts files (and keep the Git repository clean of them), but if
# you're going to do translation work, run make_tr.py with the
# --keep-ln option, then translate everythin, and run make_tr.py
# without options again before you commit.
#
def remove_linenumbers(fpath):
    print("    Removing <location> tags from", fpath)

    inf = open(fpath, "r", encoding = "utf8")
    outf = open(fpath + "~", "w", encoding = "utf8")
    for line in inf.readlines():
        if line.find ("<location ") < 0:
            outf.write(line)

    inf.close()
    outf.close()
    os.unlink(fpath)
    os.rename(fpath + "~", fpath)


# Extract the list of .ts files from the QMakefile
def extract_from_pro(qmf, varname):
    inf = open(qmf, "r", encoding = "utf8")
    ts = []
    collect = False
    for line in inf.readlines():
        line = line.strip()
        next_collect = collect
        if collect:
            if line.endswith('\\'):
                line = line[:-1]
            else:
                next_collect = False
        elif line.strip().startswith(varname):
            eq = line.find('=')
            if eq > 0:
                collect = next_collect = True
                line = line[eq + 1:]
                if line.endswith('\\'):
                    line = line[:-1]

        if collect:
            ts += line.split()

        collect = next_collect

    return ts


if "linux" in sys.platform.lower() or "unix" in sys.platform.lower() or "darwin" in sys.platform.lower():
    # On Linux, the executable are normaly on the PATH
    LREPATH = None
    names = ["lrelease-qt5", "lrelease5", "lrelease"]
    for name in names:
        if which(name):
            LREPATH = name
            break

    if not LREPATH:
        print("ERROR: Cannot file lrelease tool.")
        print("Please consider to install lrelease tool - to use this script.")
        sys.exit(1)

    PYLPATH = None
    # using lupdate instead of pylupdate will ruin translation files
    # since it doesn't know Python.
    names = ["pylupdate5"] #, "lupdate-qt5", "lupdate5", "lupdate"
    for name in names:
        if which(name):
            PYLPATH = name
            break

    if not PYLPATH:
        print("ERROR: Cannot file pylupdate5 tool.")
        print("Please consider to install lupdate tool - to use this script.")
        sys.exit(1)

    print("Using platform tools \"%s\" and \"%s\"\n" % (PYLPATH, LREPATH))
else:
    PYTHONPATH = os.path.split(sys.executable)[0]
    # To get pylupdate5.exe use: pip3.exe install PyQt5
    PYLPATH = os.path.join(PYTHONPATH, "Scripts/pylupdate5.exe")
    # To get lrelease.exe use: pip3.exe install pyqt5-tools
    LREPATH = os.path.join(PYTHONPATH, "Scripts/lrelease.exe")
    print("Using Windows platform tools \"%s\" and \"%s\"\n" % (PYLPATH, LREPATH))

# Handle command line options
try:
    (opts, left) = getopt.getopt(sys.argv[1:], "hkU", ["help", "no-pylupdate", "keep-ln"])
except getopt.GetoptError as e:
    print(e)
    sys.exit(1)

if left != list():
    print("unrecognized name on command line:", left [0])
    sys.exit(1)

QMAKEFILE = "py2cv.pro"
SKIP_PYLUPDATE = False
KEEP_LINENUMBERS = False

for opt,val in opts:
    if opt == "-h" or opt == "--help":
        print ("""\
Usage: %s [options]
    -U --no-pylupdate Don't update TS files by running 'pylupdate'
    -k --keep-ln      Keep line numbers in TS files, use this if
                      you're planning to use 'linguist'.
""" % sys.argv[0])
        sys.exit(1)
    elif opt == "--no-pylupdate" or opt == "-U":
        SKIP_PYLUPDATE = True
    elif opt == "--keep-ln" or opt == "-k":
        KEEP_LINENUMBERS = True

TSFILES = extract_from_pro(QMAKEFILE, "TRANSLATIONS")

if SKIP_PYLUPDATE:
    print("skipping pylupdate")
else:
    print("Updating translations from source files...")
    cmd = [PYLPATH, QMAKEFILE]
    print(" ".join(cmd))
    subprocess.check_call(cmd,shell=True)

    if not KEEP_LINENUMBERS:
        print("Removing sourcecode references from translation files...")
        for ts in TSFILES:
            remove_linenumbers(ts)

if not KEEP_LINENUMBERS:
    print("Compiling translation files to binary .qm format...")
    cmd = [LREPATH] + TSFILES
    print(" ".join(cmd))
    subprocess.check_call(cmd,shell=True)

print("\nREADY")
