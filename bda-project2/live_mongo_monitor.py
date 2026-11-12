#!/usr/bin/env python3
"""
live_mongo_monitor.py
Real-time dynamic terminal dashboard for MongoDB processing.
Shows live event stream, dynamic aggregation, and animated charts.
"""
import os
import sys
import time
from datetime import datetime
from pymongo import MongoClient, errors

def clear():
    os.system('clear' if os.name != 'nt' else 'cls')

def main():
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
        db = client["ecommerceapp"]
        db.command("ping")
    except errors.ServerSelectionTimeoutError:
        print("\033[91m[ERROR] Cannot connect to MongoDB on localhost:27017\033[0m")
        print("Start it with: sudo mongod --dbpath /var/lib/mongodb --logpath /var/log/mongodb/mongod.log --fork")
        sys.exit(1)

    print("\033[92mConnected to MongoDB: ecommerceapp\033[0m")
    time.sleep(1)

    last_count = 0
    start_time = time.time()

    while True:
        try:
            total_events = db.events.count_documents({})
            unique_users = len(db.events.distinct("userId"))
            unique_prods = len(db.events.distinct("productId"))
            
            # Action breakdown aggregation
            action_pipeline = [
                {"$group": {"_id": "$action", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            action_counts = {r["_id"]: r["count"] for r in db.events.aggregate(action_pipeline)}
            
            # Category breakdown aggregation
            cat_pipeline = [
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            cat_counts = list(db.events.aggregate(cat_pipeline))

            # Latest 5 events
            recent_events = list(db.events.find().sort("ts", -1).limit(5))

            diff = total_events - last_count if last_count != 0 else 0
            last_count = total_events
            elapsed = int(time.time() - start_time)

            clear()
            print("\033[1;36m================================================================================")
            print("         🟢 MONGODB REAL-TIME STREAMING & AGGREGATION MONITOR")
            print("================================================================================\033[0m")
            print(f"  \033[1;33mCurrent Time:\033[0m {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}   |   \033[1;33mElapsed Monitor Time:\033[0m {elapsed}s")
            print(f"  \033[1;32mDatabase:\033[0m ecommerceapp       |   \033[1;32mCollection:\033[0m events\n")

            # KPI Block
            print("\033[1;37m[1] REAL-TIME COLLECTION METRICS:\033[0m")
            growth_str = f"\033[1;32m(+{diff} new)\033[0m" if diff > 0 else "\033[90m(waiting for batch...)\033[0m"
            print(f"  ▶ Total Ingested Events : \033[1;32m{total_events:,}\033[0m {growth_str}")
            print(f"  ▶ Active User Sessions  : \033[1;34m{unique_users:,}\033[0m")
            print(f"  ▶ Unique Product SKUs   : \033[1;35m{unique_prods:,}\033[0m")
            print("  ------------------------------------------------------------------------------")

            # Dynamic Funnel Aggregation
            print("\n\033[1;37m[2] DYNAMIC CONVERSION FUNNEL (Computed via MongoDB Aggregation Pipeline):\033[0m")
            views = action_counts.get("view", 0)
            carts = action_counts.get("add_to_cart", 0)
            purch = action_counts.get("purchase", 0)

            def bar(val, max_val, length=28):
                if max_val == 0:
                    return ""
                fill = int((val / max_val) * length)
                return "█" * fill + "░" * (length - fill)

            print(f"  • Views        : {views:7,d}  [\033[34m{bar(views, max(total_events, 1))}\033[0m]  {(views/max(total_events,1)*100):.1f}%")
            print(f"  • Add to Cart  : {carts:7,d}  [\033[33m{bar(carts, max(total_events, 1))}\033[0m]  {(carts/max(total_events,1)*100):.1f}%")
            print(f"  • Purchases    : {purch:7,d}  [\033[32m{bar(purch, max(total_events, 1))}\033[0m]  {(purch/max(total_events,1)*100):.1f}%")
            print("  ------------------------------------------------------------------------------")

            # Category Aggregation
            print("\n\033[1;37m[3] LIVE CATEGORY DISTRIBUTION:\033[0m")
            for c in cat_counts:
                name = c["_id"] or "Unknown"
                cnt = c["count"]
                pct = (cnt / max(total_events, 1)) * 100
                print(f"  • {name:<12}: {cnt:6,d}  ({pct:4.1f}%)  [\033[36m{bar(cnt, max(total_events, 1), 20)}\033[0m]")
            print("  ------------------------------------------------------------------------------")

            # Stream Tail
            print("\n\033[1;37m[4] RECENTLY ARRIVED DOCUMENTS (Streaming Tail):\033[0m")
            print(f"  {'SESSION/USER':<14} {'PRODUCT':<10} {'ACTION':<14} {'CATEGORY':<12}")
            for doc in recent_events:
                u = doc.get('userId', 'N/A')
                p = doc.get('productId', 'N/A')
                a = doc.get('action', 'N/A')
                cat = doc.get('category', 'N/A')
                color = "\033[32m" if a == "purchase" else ("\033[33m" if a == "add_to_cart" else "\033[37m")
                print(f"  {u:<14} {p:<10} {color}{a:<14}\033[0m {cat:<12}")

            print("\n\033[90m(Updating dynamically every 1 second... Press Ctrl+C to stop)\033[0m")
            time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n\033[92mMonitor stopped.\033[0m")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
