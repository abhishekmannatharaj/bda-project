# Running the Project

Copy-paste these commands into Ubuntu. They are the same commands used for the demo.

```text
STEP 0 - START EVERYTHING (every time you open Ubuntu)
---------------------------------------------------------------------
cd ~
sudo service ssh start
start-dfs.sh && start-yarn.sh
jps

  -> jps must show: NameNode, DataNode, SecondaryNameNode,
     ResourceManager, NodeManager

sudo systemctl start mongod
mongosh --quiet --eval "db.runCommand({ping:1})"

  -> must print: { ok: 1 }

hive -e "show databases;"

  -> warms up Hive (takes ~30 sec), must print: default

Browser pages (open in Chrome):
  HDFS : http://localhost:9870
  YARN : http://localhost:8088
```

## Project - Live E-Commerce Clickstream Analysis
```text
PROJECT - LIVE E-COMMERCE CLICKSTREAM (MapReduce + Hive)
=====================================================================

---- 1. CLEAR (start again from zero) ----
cd ~/bda/bda-project2
mongosh ecommerceapp --quiet --eval "db.dropDatabase()"
hdfs dfs -rm -r -f /bda/ecommerce
rm -rf exports last_export.txt results/*
mkdir -p results exports

---- 2. RUN (open 3 Ubuntu tabs, run each line in its own tab) ----

TAB 1 - Dashboard (leave running):
cd ~/bda/bda-project2
python3 -m streamlit run dashboard.py --server.headless true

  -> open http://localhost:8501 in Chrome

TAB 2 - Live data producer (leave running, downloads Kaggle dataset on first run):
cd ~/bda/bda-project2
python3 producer.py 500 3

TAB 3 - Pipeline (wait ~1 minute after starting the producer):
cd ~/bda/bda-project2
./run_pipeline.sh

  -> takes 5-7 min. Run ./run_pipeline.sh AGAIN 2-3 times:
     once more while the producer is running,
     and once after the producer prints "All events streamed."

---- 3. VIEW RESULTS ----
cd ~/bda/bda-project2
ls -lh results/
cat $(ls -t results/hive_*.txt | head -1)
head $(ls -t results/mapreduce_*.tsv | head -1)
hdfs dfs -ls /bda/ecommerce/events
mongosh ecommerceapp --quiet --eval "db.events.countDocuments()"
mongosh ecommerceapp --quiet --eval "db.action_stats.find({eventType:'view'},{_id:0}).sort({total:-1}).limit(5)"
mongosh ecommerceapp --quiet --eval "db.action_stats.find({eventType:'purchase'},{_id:0}).sort({total:-1}).limit(5)"
explorer.exe results

  What to point out:
  - Q1 total_events grows every run     (proof of dynamic/streaming data)
  - Q2 Most Viewed, Q3 Most Purchased   (core analysis answers)
  - Q5 Category-wise breakdown          (with views, add_to_cart, purchases per category)
  - Q7 Conversion funnel per category   (purchase % per view)
  - MapReduce and Hive results agree    (cross-verification of correctness)
```

## Stop
```text
STOP EVERYTHING
=====================================================================
(Ctrl+C in every tab that is running a dashboard or producer)
stop-yarn.sh && stop-dfs.sh

In PowerShell, to shut the whole Ubuntu down:
wsl --shutdown


=====================================================================
 IMPORTANT
=====================================================================
- NEVER run "hdfs namenode -format" again (it erases HDFS).
- Only one Hive session can run at a time (close other hive windows).
- "No new events since last export" = normal, producer is stopped.
- Saved results stay in the results/ folder.
```
