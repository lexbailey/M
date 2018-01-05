#!/usr/bin/env python

from copy import copy
import argparse
from itertools import chain
import operator

parser = argparse.ArgumentParser()
parser.add_argument("File")
args = parser.parse_args()

filename = args.File

def labels(line):
    ls = line.split(":")
    return [l.strip() for l in ls[0:-1]]

def instr(line):
    return line.split(":")[-1].strip()

def labels_to_map(label_lines):
    return {
        label: i
        for i, (labels, _) in enumerate(label_lines)
            for label in labels
    }

def ass(d, key, val):
    md = copy(d)
    md[key] = val
    return md

conds = {cond: getattr(operator, cond) for cond in ["eq", "ne", "lt", "ge"]}

def runfile(f):
    lines = [l.strip() for l in f.read().split(";")]
    label_lines = [(labels(line), instr(line)) for line in lines]
    label_map = labels_to_map(label_lines)
    k = 0
    M = {}
    regs = {}
    try:
        while k != None:
            lk, line_k = label_lines[k]
            c = [p.strip() for p in line_k.split(" ")]
            command = c[0]
            try:
                args = c[1:]
            except IndexError:
                args = []
            M, k, regs = {
                "": lambda M, k, r: (M, k+1, r),
                "nop": lambda M, k, r: (M, k+1, r),
                "hlt": lambda M, k, r: (M, None, r),
                "prn": lambda M, k, r, s: (print(r[s]), (M, k+1, r))[-1],
                "mov": lambda M, k, r, dest, src: (M, k+1, ass(r, dest, r[src])),
                "movi": lambda M, k, r, dest, i: (M, k+1, ass(r, dest, int(i))),
                "add": lambda M, k, r, dest, a, b: (M, k+1, ass(r, dest, r[a] + r[b])),
                "addi": lambda M, k, r, dest, a, b: (M, k+1, ass(r, dest, r[a] + int(b))),
                "mul": lambda M, k, r, dest, a, b: (M, k+1, ass(r, dest, r[a] * r[b])),
                "muli": lambda M, k, r, dest, a, b: (M, k+1, ass(r, dest, r[a] * int(b))),
                "neg": lambda M, k, r, dest, a: (M, k+1, ass(r, dest, -r[a])),
                "negi": lambda M, k, r, dest, a: (M, k+1, ass(r, dest, -int(a))),
                "jmp": lambda M, k, r, target: (M, r[target], r),
                "jmpi": lambda M, k, r, target: (M, label_map[target], r),
                **dict.fromkeys(
                    list(chain(*[[pattern % (cond) for pattern in ["b%s", "b%si"]] for cond in conds.keys()])),
                    lambda M, k, r, target, a, b: (M,
                        label_map[target]
                        if conds[command[1:-1]](r[a],
                            int(b) if command[-1]=='i' else r[b]
                            )
                        else k+1,
                        r)
                ),
                "laddr": lambda M, k, r, dest, label: (M, k, ass(r, dest, label_map[label])),
                "load": lambda M, k, r, a, b: (M, k+1, ass(r, a, M[r[b]])),
                "loadi": lambda M, k, r, a, b: (M, k+1, ass(r, a, M[int(b)])),
                "store": lambda M, k, r, a, b: (ass(M, r[b], r[a]), k+1, r),
                "storei": lambda M, k, r, a, b: (ass(M, int(b), r[a]), k+1, r),
                "": lambda M, k, r: (M, k+1, r),
            }[command](M, k, regs, *args)
    except KeyError:
        print("Error: some sort of undefined behaviour on line %d. Regs: %r, Mem: %r" % (k+1, regs, M))

try:
    with open(filename) as f:
        runfile(f)
except IOError as e:
    print("Unable to open file.", e.strerror)
