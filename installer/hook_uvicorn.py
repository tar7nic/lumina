import sys
import os

if not hasattr(sys, 'stdout') or sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if not hasattr(sys, 'stderr') or sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
if not hasattr(sys, 'stdin') or sys.stdin is None:
    sys.stdin = open(os.devnull, 'r')