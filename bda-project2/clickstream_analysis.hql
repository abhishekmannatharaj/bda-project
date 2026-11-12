CREATE DATABASE IF NOT EXISTS ecommerceapp;
USE ecommerceapp;

-- External tables point at HDFS folders — new files from MongoDB appear automatically
CREATE EXTERNAL TABLE IF NOT EXISTS events (
  user_id    STRING,
  product_id STRING,
  action     STRING,
  category   STRING,
  ts         TIMESTAMP)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE LOCATION '/bda/ecommerce/events';

CREATE EXTERNAL TABLE IF NOT EXISTS products (
  product_id STRING,
  category   STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE LOCATION '/bda/ecommerce/products';

CREATE EXTERNAL TABLE IF NOT EXISTS mr_action_stats (
  event_type STRING,
  key_id     STRING,
  total      INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE LOCATION '/bda/ecommerce/mr_output';

-- Q1: Overall summary — how much data has arrived
SELECT COUNT(*) AS total_events,
       COUNT(DISTINCT user_id)    AS unique_users,
       COUNT(DISTINCT product_id) AS unique_products,
       MIN(ts) AS first_event,
       MAX(ts) AS latest_event
FROM events;

-- Q2: Most viewed products (Top 10)
SELECT product_id,
       COUNT(*) AS view_count
FROM events
WHERE action = 'view'
GROUP BY product_id
ORDER BY view_count DESC
LIMIT 10;

-- Q3: Most purchased products (Top 10)
SELECT product_id,
       COUNT(*) AS purchase_count
FROM events
WHERE action = 'purchase'
GROUP BY product_id
ORDER BY purchase_count DESC
LIMIT 10;

-- Q4: Most add-to-cart products (Top 10)
SELECT product_id,
       COUNT(*) AS cart_count
FROM events
WHERE action = 'add_to_cart'
GROUP BY product_id
ORDER BY cart_count DESC
LIMIT 10;

-- Q5: Category-wise activity (all action types)
SELECT category,
       COUNT(*) AS total_events,
       SUM(CASE WHEN action = 'view'        THEN 1 ELSE 0 END) AS views,
       SUM(CASE WHEN action = 'add_to_cart' THEN 1 ELSE 0 END) AS add_to_cart,
       SUM(CASE WHEN action = 'purchase'    THEN 1 ELSE 0 END) AS purchases
FROM events
GROUP BY category
ORDER BY total_events DESC;

-- Q6: Per-user activity — top 10 most active users
SELECT user_id,
       COUNT(*) AS total_actions,
       COUNT(DISTINCT product_id) AS products_interacted,
       SUM(CASE WHEN action = 'purchase' THEN 1 ELSE 0 END) AS purchases
FROM events
GROUP BY user_id
ORDER BY total_actions DESC
LIMIT 10;

-- Q7: Conversion funnel — view -> add_to_cart -> purchase per category
SELECT category,
       SUM(CASE WHEN action = 'view'        THEN 1 ELSE 0 END) AS views,
       SUM(CASE WHEN action = 'add_to_cart' THEN 1 ELSE 0 END) AS add_to_cart,
       SUM(CASE WHEN action = 'purchase'    THEN 1 ELSE 0 END) AS purchases,
       ROUND(SUM(CASE WHEN action = 'purchase' THEN 1 ELSE 0 END) * 100.0 /
             NULLIF(SUM(CASE WHEN action = 'view' THEN 1 ELSE 0 END), 0), 2) AS conversion_pct
FROM events
GROUP BY category
ORDER BY conversion_pct DESC;

-- Q8: Live arrival trend — events per minute
SELECT DATE_FORMAT(ts, 'yyyy-MM-dd HH:mm') AS minute,
       COUNT(*) AS event_count,
       SUM(CASE WHEN action = 'view'     THEN 1 ELSE 0 END) AS views,
       SUM(CASE WHEN action = 'purchase' THEN 1 ELSE 0 END) AS purchases
FROM events
GROUP BY DATE_FORMAT(ts, 'yyyy-MM-dd HH:mm')
ORDER BY minute;
