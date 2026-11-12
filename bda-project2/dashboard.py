#!/usr/bin/env python3
"""
Live dashboard for the E-Commerce Clickstream Big Data pipeline.
  Live (MongoDB)    : totals, events per minute, latest events   -> refreshes every 5 s
  MapReduce results : action_stats collection in MongoDB          -> after each pipeline run
  Hive results      : latest results/hive_*.txt                  -> after each pipeline run

Run: python3 -m streamlit run dashboard.py --server.headless true
"""
import glob
import os
import time
from datetime import timedelta

import pandas as pd
import streamlit as st
from pymongo import MongoClient

BASE    = os.path.dirname(os.path.abspath(__file__))
REFRESH = 5
IST     = timedelta(hours=5, minutes=30)

st.set_page_config(page_title="Live E-Commerce Clickstream", layout="wide")


@st.cache_resource
def get_db():
    return MongoClient("mongodb://localhost:27017")["ecommerceapp"]


def latest_hive():
    files = sorted(glob.glob(os.path.join(BASE, "results", "hive_*.txt")), key=os.path.getmtime)
    if not files:
        return None, {}
    # Section headers as they appear in the HQL output
    HEADERS = {"total_events", "product_id", "category", "user_id", "minute"}
    sections, cur = {}, None
    with open(files[-1], encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            # A header row: first cell matches a known header word
            if p[0].lower() in HEADERS:
                label = p[0].lower()
                # Distinguish multiple product_id sections by appending a counter
                key = label
                n = 1
                while key in sections:
                    n += 1
                    key = f"{label}_{n}"
                cur = key
                sections[cur] = {"cols": p, "rows": []}
                continue
            if cur and len(p) == len(sections[cur]["cols"]):
                sections[cur]["rows"].append(p)
    tables = {k: pd.DataFrame(v["rows"], columns=v["cols"]) for k, v in sections.items()}
    return os.path.basename(files[-1]), tables


db = get_db()

st.title("🛒 Live E-Commerce Clickstream — Big Data Pipeline")
st.caption("Kaggle Clickstream → MongoDB (live) → HDFS → MapReduce + Hive on YARN → MongoDB → Dashboard")

# ---- KPIs ----
total        = db.events.estimated_document_count()
users        = len(db.events.distinct("userId"))
products     = len(db.events.distinct("productId"))
last_stat    = db.action_stats.find_one(sort=[("updated_at", -1)])
last_run     = (last_stat["updated_at"] + IST).strftime("%H:%M:%S") if last_stat else "not yet"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Events in MongoDB",  f"{total:,}")
c2.metric("Unique Users",        f"{users:,}")
c3.metric("Unique Products",     f"{products:,}")
c4.metric("Last pipeline run",   last_run)

# ---- Live Events ----
st.subheader("Live events arriving (MongoDB)")
left, right = st.columns([2, 1])

per_min = list(db.events.aggregate([
    {"$group": {"_id": {"$dateToString": {"format": "%H:%M", "date": "$ts", "timezone": "+05:30"}},
                "events": {"$sum": 1}}},
    {"$sort": {"_id": 1}}]))
if per_min:
    df = pd.DataFrame(per_min).rename(columns={"_id": "minute"}).set_index("minute")
    left.markdown("**Events received per minute**")
    left.bar_chart(df["events"])

recent = list(db.events.find({}, {"_id": 0}).sort("ts", -1).limit(10))
if recent:
    r = pd.DataFrame(recent)
    r["time"] = (r["ts"] + IST).dt.strftime("%H:%M:%S")
    right.markdown("**Latest 10 events**")
    right.dataframe(r[["time", "userId", "productId", "action", "category"]], hide_index=True)

# ---- MapReduce Results ----
st.subheader("MapReduce results (action_stats in MongoDB)")
stats = pd.DataFrame(list(db.action_stats.find({}, {"_id": 0})))
if stats.empty:
    st.info("Run ./run_pipeline.sh to see MapReduce results.")
else:
    a, b, c = st.columns(3)

    views = (stats[stats["eventType"] == "view"]
             .sort_values("total", ascending=False).head(10))
    a.markdown("**Top 10 Most Viewed Products**")
    a.dataframe(views[["keyId", "total"]].rename(columns={"keyId": "product_id", "total": "views"}),
                hide_index=True)

    purchases = (stats[stats["eventType"] == "purchase"]
                 .sort_values("total", ascending=False).head(10))
    b.markdown("**Top 10 Most Purchased Products**")
    b.dataframe(purchases[["keyId", "total"]].rename(columns={"keyId": "product_id", "total": "purchases"}),
                hide_index=True)

    categories = (stats[stats["eventType"] == "category"]
                  .sort_values("total", ascending=False))
    c.markdown("**Category-wise Activity (MapReduce)**")
    c.dataframe(categories[["keyId", "total"]].rename(columns={"keyId": "category", "total": "events"}),
                hide_index=True,
                column_config={"events": st.column_config.ProgressColumn(
                    "Events", format="%d",
                    min_value=0, max_value=int(categories["total"].max()) if not categories.empty else 1)})

# ---- Hive Results ----
name, hive = latest_hive()
st.subheader(f"Hive analysis (from {name})" if name else "Hive analysis")
if not hive:
    st.info("Run ./run_pipeline.sh to see Hive results.")
else:
    # Show category-wise activity table
    cat_key = next((k for k in hive if "category" in k), None)
    view_key  = next((k for k in hive if k.startswith("product_id")), None)

    row1a, row1b = st.columns(2)

    if cat_key and not hive[cat_key].empty:
        df_cat = hive[cat_key]
        for col in df_cat.columns[1:]:
            df_cat[col] = pd.to_numeric(df_cat[col], errors="coerce")
        df_cat = df_cat.sort_values(df_cat.columns[1], ascending=False)
        row1a.markdown("**Category-wise Activity (Hive)**")
        row1a.dataframe(df_cat, hide_index=True)

    if view_key and not hive[view_key].empty:
        df_v = hive[view_key]
        for col in df_v.columns[1:]:
            df_v[col] = pd.to_numeric(df_v[col], errors="coerce")
        row1b.markdown("**Top Viewed Products (Hive)**")
        row1b.dataframe(df_v, hide_index=True)

    # Conversion funnel if present
    conv_key = next((k for k in hive if "conversion" in str(hive[k].columns.tolist()).lower()), None)
    if conv_key:
        df_conv = hive[conv_key]
        for col in df_conv.columns[1:]:
            df_conv[col] = pd.to_numeric(df_conv[col], errors="coerce")
        st.markdown("**Conversion Funnel by Category (Hive)**")
        st.dataframe(df_conv, hide_index=True)

st.caption(f"Live section refreshes every {REFRESH} seconds.")
time.sleep(REFRESH)
st.rerun()
