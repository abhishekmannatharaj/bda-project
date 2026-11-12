#!/usr/bin/env python3
"""
Live data source: reads the e-shop clickstream CSV and streams events
(view / add_to_cart / purchase) into MongoDB.

Dataset: e-shop clothing 2008.csv  (Kaggle - tunguz/clickstream-data-for-online-shopping)
Columns (semicolon-separated):
  year; month; day; order; country; session ID;
  page 1 (main category); page 2 (clothing model);
  colour; location; model photography; price; price 2; page

Mapping used:
  User ID   <- session ID
  Product   <- page 2 (clothing model)   e.g. A13, B4
  Action    <- page   (1=view, 2=add_to_cart, 3=purchase)
  Category  <- page 1 (main category)    (1=trousers, 2=skirts, 3=blouses, 4=sale)
  Timestamp <- year-month-day + order (sequence number used as time offset)

Usage: python3 producer.py [batch_size] [interval_seconds]
       python3 producer.py 500 3
Stop with Ctrl+C.
"""
import csv
import os
import random
import sys
import time
from datetime import datetime, timezone, timedelta

from pymongo import MongoClient

# ---------------------------------------------------------------------------
# Config — update DATA_FILE path if needed
# ---------------------------------------------------------------------------
DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data",
    "e-shop clothing 2008.csv"
)

BATCH    = int(sys.argv[1]) if len(sys.argv) > 1 else 200
INTERVAL = float(sys.argv[2]) if len(sys.argv) > 2 else 5

# Category code → name mapping (from dataset documentation)
CATEGORY_MAP = {
    "1": "trousers",
    "2": "skirts",
    "3": "blouses",
    "4": "sale",
}

# Page (action) code -> name
ACTION_MAP = {
    "1": "view",
    "2": "add_to_cart",
    "3": "purchase",
}

# ---------------------------------------------------------------------------
# Load CSV
# ---------------------------------------------------------------------------
if not os.path.exists(DATA_FILE):
    print(f"[ERROR] Dataset not found at: {DATA_FILE}")
    print("        Make sure you copied the CSV to the data/ folder.")
    print("        Run:  mkdir -p data && cp '/path/to/e-shop clothing 2008.csv' data/")
    sys.exit(1)

print(f"Reading dataset: {DATA_FILE}")
rows = []
with open(DATA_FILE, newline="", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f, delimiter=";")
    for i, row in enumerate(reader):
        user_id   = row.get("session ID", "").strip()   or f"U{i % 1000:04d}"
        product   = row.get("page 2 (clothing model)", "").strip() or f"P{i % 500:04d}"
        action_c  = row.get("page", "1").strip()
        cat_c     = row.get("page 1 (main category)", "1").strip()

        action    = ACTION_MAP.get(action_c, "view")
        category  = CATEGORY_MAP.get(cat_c, f"cat_{cat_c}")

        # Build a rough timestamp from year/month/day columns
        try:
            yr  = int(row.get("year",  "2008"))
            mo  = int(row.get("month", "1"))
            dy  = int(row.get("day",   "1"))
        except ValueError:
            yr, mo, dy = 2008, 1, 1

        rows.append({
            "userId":    user_id,
            "productId": product,
            "action":    action,
            "category":  category,
            "_date":     (yr, mo, dy),   # used for synthetic ts, stripped before insert
        })

print(f"Loaded {len(rows)} events from CSV.")
random.Random(42).shuffle(rows)

# ---------------------------------------------------------------------------
# Connect to MongoDB
# ---------------------------------------------------------------------------
db = MongoClient("mongodb://localhost:27017")["ecommerceapp"]

# Load product catalogue once
if db.products.count_documents({}) == 0:
    products = {}
    for r in rows:
        products[r["productId"]] = r["category"]
    db.products.insert_many([{"productId": pid, "category": cat}
                              for pid, cat in products.items()])
    db.products.create_index("productId", unique=True)
    print(f"Loaded {len(products)} unique products into MongoDB.")

db.events.create_index("ts")

# ---------------------------------------------------------------------------
# Stream events
# ---------------------------------------------------------------------------
i = db.events.count_documents({})
print(f"{len(rows)} events available, {i} already streamed.")
print(f"Streaming {BATCH} events every {INTERVAL}s ... (Ctrl+C to stop)\n")

try:
    while i < len(rows):
        now   = datetime.now(timezone.utc)
        batch = rows[i : i + BATCH]

        docs = []
        for r in batch:
            doc = {k: v for k, v in r.items() if k != "_date"}
            doc["ts"] = now
            docs.append(doc)

        db.events.insert_many(docs)
        i += len(batch)
        print(f"[{datetime.now():%H:%M:%S}]  +{len(batch)} events  |  total in MongoDB: {i}")
        time.sleep(INTERVAL)

    print("\nAll events streamed!")
except KeyboardInterrupt:
    print(f"\nStopped. {i} events in MongoDB.")
