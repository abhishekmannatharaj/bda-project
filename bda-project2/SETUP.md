# SETUP & PRESENTATION GUIDE
## BDA Project 12 — E-Commerce Clickstream Analytics

---

## WHAT THIS PROJECT DOES (explain to ma'am in 1 minute)

> "We have an e-commerce clickstream dataset from Kaggle. It records every action a user does — viewing a product, adding to cart, or purchasing. We stream this data live into MongoDB, push it to HDFS, run a MapReduce job to count actions per product and category, then run 8 Hive queries to find the most viewed products, most purchased products, and category-wise activity. Results are shown on a live Streamlit dashboard."

---

## THE PIPELINE (what happens behind the scenes)

```
Kaggle CSV (e-shop clothing 2008.csv)
         │
         ▼
   producer.py              ← reads CSV, streams batches of 500 events every 3s
         │                     into MongoDB  (ecommerceapp.events)
         ▼
   MongoDB                  ← stores: userId, productId, action, category, timestamp
         │
         ▼
   mongo_to_hdfs.py         ← copies ONLY new events to HDFS (incremental)
         │
         ▼
   HDFS  /bda/ecommerce/events   ← distributed file system (like a big hard disk)
         │
         ├──────────────────────────────────────┐
         ▼                                      ▼
   MapReduce                              Hive Queries
   mapper.py + reducer.py                clickstream_analysis.hql
   (counts per product/category)         (8 SQL-like queries)
         │                                      │
         ▼                                      ▼
   MongoDB action_stats              results/hive_HHMMSS.txt
         │
         ▼
   Streamlit Dashboard (http://localhost:8501)
```

### MapReduce Logic (mapper.py → reducer.py)
- **Mapper** reads each event line and emits:
  - `view   <productId>  1`  → to count views per product
  - `purchase <productId> 1` → to count purchases per product
  - `category <category>  1` → to count all activity per category
- **Reducer** groups by key and sums all the 1s → gives total counts

### Hive Queries (clickstream_analysis.hql)
| Query | What it finds |
|---|---|
| Q1 | Total events, unique users, unique products |
| Q2 | **Top 10 most viewed products** ← key answer |
| Q3 | **Top 10 most purchased products** ← key answer |
| Q4 | Top 10 most add-to-cart products |
| Q5 | **Category-wise activity** (views/cart/purchases per category) ← key answer |
| Q6 | Top 10 most active users |
| Q7 | Conversion funnel (purchase % per category) |
| Q8 | Live trend (events per minute) |

---

## HOW TO RUN TOMORROW (step by step)

### STEP 0 — Open Ubuntu (do this first, every time)
In PowerShell:
```powershell
wsl -d Ubuntu-22.04
```

### STEP 1 — Start all services
```bash
sudo service ssh start
start-dfs.sh && start-yarn.sh
jps
```
✅ jps must show 5 things: NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager

```bash
sudo mongod --dbpath /var/lib/mongodb --logpath /var/log/mongodb/mongod.log --fork
mongosh --eval "db.runCommand({ping:1})" 2>/dev/null
```
✅ Must print `{ ok: 1 }`

### STEP 2 — Go to project folder
```bash
cd ~/bda/bda-project2
```

### STEP 3 — Clear old data (fresh demo start)
```bash
mongosh ecommerceapp --quiet --eval "db.dropDatabase()" 2>/dev/null
hdfs dfs -rm -r -f /bda/ecommerce
rm -rf exports last_export.txt results/*
mkdir -p results exports
```

### STEP 4 — Open 3 Ubuntu tabs
Open Ubuntu 3 times (run `wsl -d Ubuntu-22.04` in 3 PowerShell windows)

**TAB 1 — Dashboard:**
```bash
cd ~/bda/bda-project2
python3 -m streamlit run dashboard.py --server.headless true
```
→ Open **http://localhost:8501** in Chrome

**TAB 2 — Producer (live data):**
```bash
cd ~/bda/bda-project2
python3 producer.py 500 3
```
→ Wait until you see events streaming ("+500 events | total: 500")

**TAB 3 — Pipeline (wait 1 min after TAB 2 starts):**
```bash
cd ~/bda/bda-project2
./run_pipeline.sh
```
→ Takes ~5-7 minutes. Run it again 2-3 more times.

### STEP 5 — View results in terminal
```bash
# See Hive output
cat $(ls -t results/hive_*.txt | head -1)

# See MapReduce output
head $(ls -t results/mapreduce_*.tsv | head -1)

# Most viewed products (MongoDB)
mongosh ecommerceapp --quiet --eval "db.action_stats.find({eventType:'view'},{_id:0}).sort({total:-1}).limit(5)" 2>/dev/null

# Most purchased products (MongoDB)
mongosh ecommerceapp --quiet --eval "db.action_stats.find({eventType:'purchase'},{_id:0}).sort({total:-1}).limit(5)" 2>/dev/null
```

---

## WHAT TO POINT OUT TO MA'AM

1. **Live streaming** → Show TAB 2 (producer) printing new events every 3 seconds
2. **Dashboard KPIs** → Show events growing every pipeline run (proof of dynamic data)
3. **Most Viewed Products** → Q2 in Hive output / dashboard top-left table
4. **Most Purchased Products** → Q3 in Hive output / dashboard middle table
5. **Category-wise activity** → Q5 in Hive output / dashboard category table
   - Categories: trousers, skirts, blouses, sale
   - Shows: views, add_to_cart, purchases per category
6. **MapReduce = Hive** → Both give same top products (cross-verification)
7. **Conversion funnel** → Q7 shows which category converts views→purchases best
8. **HDFS files** → `hdfs dfs -ls /bda/ecommerce/events` shows multiple files (one per pipeline run)

---

## QUESTIONS MA'AM MIGHT ASK

**Q: What is the dataset?**
> Kaggle e-shop clothing clickstream dataset (2008). Contains session ID (user), clothing model code (product), page category, and action type (1=view, 2=add_to_cart, 3=purchase).

**Q: Why Hive/Pig?**
> Hive lets us run SQL-like queries on data stored in HDFS. It's ideal for batch analysis of large clickstream logs without writing complex Java code.

**Q: What does MapReduce do here?**
> The mapper emits (action, productId) → 1 for each event. The reducer sums them up to get total views/purchases per product. It's the distributed counting engine.

**Q: What is HDFS?**
> Hadoop Distributed File System — stores the clickstream event files. Every pipeline run adds a new TSV file, showing data growth over time.

**Q: How is it live/streaming?**
> producer.py reads the CSV and inserts 500 events every 3 seconds into MongoDB — simulating a real e-commerce app. Each pipeline run picks up only the NEW events (incremental ingestion via mongo_to_hdfs.py).

**Q: What are the key findings?**
> After running the pipeline: trousers and blouses are the most viewed categories; purchase counts show which products convert best; the conversion funnel shows sale category has highest purchase rate.

---

## IF SOMETHING GOES WRONG

| Problem | Fix |
|---|---|
| `jps` doesn't show 5 processes | `stop-dfs.sh && sudo service ssh start && start-dfs.sh && start-yarn.sh` |
| MongoDB not connecting | `sudo mongod --dbpath /var/lib/mongodb --logpath /var/log/mongodb/mongod.log --fork` |
| `streamlit: command not found` | `source ~/.bashrc` then try again |
| `./run_pipeline.sh: Permission denied` | `chmod +x run_pipeline.sh` |
| Hive Derby lock error | Close all other Hive windows, only 1 at a time |
| Dashboard shows "Run pipeline to see results" | Run `./run_pipeline.sh` in TAB 3 first |
| `hdfs: command not found` | `source ~/.bashrc` then try again |

---

## TECH STACK SUMMARY (for viva)

| Tool | Role |
|---|---|
| **Python (producer.py)** | Simulates live e-commerce app, streams events |
| **MongoDB** | NoSQL database storing live clickstream events |
| **HDFS** | Distributed storage for event files |
| **MapReduce** | Distributed counting of views/purchases per product |
| **Hive** | SQL-like analysis on HDFS data (8 queries) |
| **Streamlit** | Live web dashboard showing results |
| **Hadoop YARN** | Cluster resource manager (runs MapReduce jobs) |
