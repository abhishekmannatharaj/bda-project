#!/usr/bin/env python3
"""
Reducer for e-commerce clickstream analysis.
Input:  action/category<TAB>key<TAB>count   (sorted by Hadoop)
Output: action/category<TAB>key<TAB>total_count
"""
import sys

current_type = None
current_key  = None
total        = 0


def emit():
    print(f"{current_type}\t{current_key}\t{total}")


for line in sys.stdin:
    parts = line.strip().split("\t")
    if len(parts) != 3:
        continue
    event_type, key, count = parts
    try:
        count = int(count)
    except ValueError:
        continue

    if event_type == current_type and key == current_key:
        total += count
    else:
        if current_type is not None:
            emit()
        current_type, current_key, total = event_type, key, count

if current_type is not None:
    emit()
