#!/usr/bin/env python3
"""
Mapper for e-commerce clickstream analysis.
Input (tab-separated):  userId  productId  action  category  ts
Output:                 action:productId<TAB>1        (for counting actions per product)
                        cat:<category><TAB>1          (for category-wise totals)
"""
import sys

for line in sys.stdin:
    parts = line.strip().split("\t")
    if len(parts) != 5:
        continue
    user_id, product_id, action, category, ts = parts

    # Emit: action type + productId -> 1  (to count views / purchases per product)
    print(f"{action}\t{product_id}\t1")

    # Emit: category activity -> 1
    print(f"category\t{category}\t1")
