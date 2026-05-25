#!/usr/bin/env python3
"""Package VistA-M sources for import.

Cleaned merge of WorldVistA Scripts/PackRO.py + PrepareMComponentsForImport.py
(submodule pin b7aecb9), Python 3. Walks one or more M source trees and writes:
  routines.ro   the ^%RO routine-transfer file read by ^%RI
  globals.lst   absolute .zwr paths, one per line, read by LIST^ZGI

Usage:
  python3 prepare.py <M_DIR> [<M_DIR> ...] -o <OUTPUT_DIR>
"""
import argparse
import codecs
import fnmatch
import os


def files_in_tree(pattern, top):
    for dirpath, _dirs, files in os.walk(os.path.abspath(top)):
        for f in fnmatch.filter(files, pattern):
            yield os.path.join(dirpath, f)


def pack_routines(files, out):
    # ^%RO transfer format: "Routines" header, then for each routine a name line
    # (underscore -> percent) followed by its source and a blank separator.
    out.write("Routines\n\n")
    for f in files:
        if not f.endswith(".m"):
            continue
        name = os.path.basename(f)[:-2].replace("_", "%")
        out.write("%s\n" % name)
        with codecs.open(f, "r", "ISO-8859-1", "ignore") as m:
            for line in m:
                out.write("%s\n" % line.rstrip("\r\n"))
        out.write("\n")
    out.write("\n\n")


def main():
    ap = argparse.ArgumentParser(description="Build routines.ro + globals.lst")
    ap.add_argument("mdir", nargs="+", help="M source tree(s) to scan")
    ap.add_argument("-o", "--outputdir", default="", help="output directory")
    args = ap.parse_args()

    if args.outputdir:
        os.makedirs(args.outputdir, exist_ok=True)
    ro_path = os.path.join(args.outputdir, "routines.ro")
    lst_path = os.path.join(args.outputdir, "globals.lst")

    routines, globals_ = [], []
    for d in args.mdir:
        routines += sorted(files_in_tree("*.m", d))
        globals_ += sorted(files_in_tree("*.zwr", d))

    with codecs.open(ro_path, "w", "ISO-8859-1", "ignore") as out:
        pack_routines(routines, out)
    with codecs.open(lst_path, "w", "ISO-8859-1", "ignore") as out:
        for g in globals_:
            out.write(g + "\n")

    print("Packed %d routines -> %s" % (len(routines), ro_path))
    print("Listed %d globals -> %s" % (len(globals_), lst_path))


if __name__ == "__main__":
    main()
