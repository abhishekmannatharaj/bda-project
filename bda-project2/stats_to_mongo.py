#!/usr/bin/env python3
"""
Stores MapReduce results in MongoDB (action_stats) so the dashboard can show
the most-viewed and most-purchased products.
Usage: hdfs dfs -cat /bda/ecommerce/mr_output/part-* | python3 stats_to_mongo.py
"""
import sys
from datetime import datetime, timezone

from pymongo import MongoClient, UpdateOne

db  = MongoClient("mongodb://localhost:27017")["ecommerceapp"]
now = datetime.now(timezone.utc)
ops = []

for line in sys.stdin:
    parts = line.strip().split("\t")
    if len(parts) != 3:
        continue
    event_type, key_id, total = parts
    ops.append(UpdateOne(
        {"eventType": event_type, "keyId": key_id},
        {"$set": {"total": int(total), "updated_at": now}},
        upsert=True
    ))

if ops:
    db.action_stats.bulk_write(ops)

print(f"Updated {len(ops)} entries in MongoDB collection action_stats")
