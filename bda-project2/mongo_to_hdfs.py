#!/usr/bin/env python3
"""
Incremental ingestion: MongoDB -> HDFS.
Each run copies ONLY the events that arrived since the last run into a new
HDFS file.  The product catalogue is copied once.
"""
import os
import subprocess
from datetime import datetime, timedelta, timezone

from pymongo import MongoClient

IST          = timezone(timedelta(hours=5, minutes=30))
HDFS_EVENTS  = "/bda/ecommerce/events"
HDFS_PRODUCTS= "/bda/ecommerce/products"
STATE        = "last_export.txt"
OUT          = "exports"


def hdfs(*args):
    subprocess.run(["hdfs", "dfs", *args], check=True)


db = MongoClient("mongodb://localhost:27017")["ecommerceapp"]
os.makedirs(OUT, exist_ok=True)

# ---- Product catalogue (once) ----
products_file = f"{OUT}/products.tsv"
if not os.path.exists(products_file):
    with open(products_file, "w", encoding="utf-8") as f:
        for p in db.products.find({}, {"_id": 0}).sort("productId"):
            f.write(f"{p['productId']}\t{p['category']}\n")
    hdfs("-mkdir", "-p", HDFS_PRODUCTS)
    hdfs("-put", "-f", products_file, HDFS_PRODUCTS + "/")
    print(f"Product catalogue copied to HDFS {HDFS_PRODUCTS}")

# ---- Incremental events ----
if os.path.exists(STATE):
    with open(STATE) as f:
        last = datetime.fromisoformat(f.read().strip())
else:
    last = datetime(1970, 1, 1, tzinfo=timezone.utc)

cutoff = datetime.now(timezone.utc) - timedelta(seconds=5)
stamp  = cutoff.astimezone(IST).strftime("%Y%m%d_%H%M%S")
path   = f"{OUT}/events_{stamp}.tsv"
n = 0

with open(path, "w") as f:
    for e in db.events.find({"ts": {"$gt": last, "$lte": cutoff}}, {"_id": 0}).sort("ts"):
        ts = e["ts"].replace(tzinfo=timezone.utc).astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{e['userId']}\t{e['productId']}\t{e['action']}\t{e['category']}\t{ts}\n")
        n += 1

if n == 0:
    os.remove(path)
    print("No new events since last export.")
else:
    hdfs("-mkdir", "-p", HDFS_EVENTS)
    hdfs("-put", "-f", path, HDFS_EVENTS + "/")
    print(f"Exported {n} new events -> HDFS {HDFS_EVENTS}/{os.path.basename(path)}")

with open(STATE, "w") as f:
    f.write(cutoff.isoformat())
