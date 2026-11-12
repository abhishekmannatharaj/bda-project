# E-Commerce Clickstream Analytics — Hadoop MapReduce + Hive + MongoDB

Big Data Analytics (BCS714D) project, Gopalan College of Engineering & Management — **Assignment Q12**:
*Given an e-commerce clickstream dataset containing User ID, Product ID, Action, Timestamp and Category, analyze user activity to identify most viewed products, most purchased products and category-wise activity.*

Instead of a static file, clickstream events arrive **live**: a producer downloads the Kaggle clickstream dataset and streams events into **MongoDB**, each pipeline run copies only the new events into **HDFS**, a **Python MapReduce** job (Hadoop Streaming) computes action counts per product and per category on **YARN**, **Hive** runs 8 analysis queries on the same data, and results go back to MongoDB and a **Streamlit** dashboard.

## Documentation
- [Installation guide (requirements + full setup)](docs/INSTALLATION.md)
- [Running, clearing and viewing results](docs/RUNNING.md)

## Tech stack
Hadoop 3.3.6 (HDFS, YARN, MapReduce + Streaming) · Hive 3.1.3 · MongoDB 8.0 · Python 3.10 (PyMongo, kagglehub) · Streamlit · Ubuntu 22.04 on WSL2 · OpenJDK 8

## Files
| File | Purpose |
|---|---|
| `producer.py` | Downloads the Kaggle clickstream dataset via `kagglehub` and streams events (view/add_to_cart/purchase) into MongoDB (`ecommerceapp.events`) |
| `mongo_to_hdfs.py` | Incremental ingestion: copies only new events to HDFS (`/bda/ecommerce/events`) |
| `mapper.py`, `reducer.py` | MapReduce job: counts per (action, productId) and per category |
| `stats_to_mongo.py` | Writes MapReduce results back to MongoDB (`action_stats`) |
| `clickstream_analysis.hql` | 8 Hive queries (summary, top views, top purchases, add-to-cart, category activity, user activity, conversion funnel, live trend) |
| `run_pipeline.sh` | One full cycle: MongoDB → HDFS → MapReduce → MongoDB → Hive |
| `dashboard.py` | Live dashboard (http://localhost:8501) |

## Dataset
[Clickstream Data for Online Shopping](https://www.kaggle.com/datasets/tunguz/clickstream-data-for-online-shopping) (Kaggle - tunguz):
E-commerce clickstream data with session IDs, categories (trousers, skirts, blouses, etc.), and page interactions.

Downloaded automatically on first run via `kagglehub`:
```python
import kagglehub
path = kagglehub.dataset_download("tunguz/clickstream-data-for-online-shopping")
```

## Run
Prerequisites: see [docs/INSTALLATION.md](docs/INSTALLATION.md).
```bash
start-dfs.sh && start-yarn.sh                                   # Hadoop
python3 -m streamlit run dashboard.py --server.headless true    # tab 1: dashboard
python3 producer.py 500 3                                       # tab 2: live data (downloads dataset)
./run_pipeline.sh                                               # tab 3: run, then run again later
```

## Analysis Queries (Hive)
| # | Query | Insight |
|---|---|---|
| Q1 | Total events, unique users, unique products | Dataset overview |
| Q2 | Top 10 most viewed products | Most popular browsed products |
| Q3 | Top 10 most purchased products | Best-selling products |
| Q4 | Top 10 most add-to-cart products | High-interest products |
| Q5 | Category-wise breakdown (views / add_to_cart / purchases) | Category performance |
| Q6 | Top 10 most active users | Power users |
| Q7 | Conversion funnel per category (purchase% of views) | Category conversion rates |
| Q8 | Live arrival trend (events per minute) | Streaming data verification |

## Author
[Your Name] — B.E. CSE, Gopalan College of Engineering & Management, Bengaluru
