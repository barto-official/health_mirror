import os
import mysql.connector
import redis
import pandas as pd
import json
from mysql.connector import Error

# Database and Redis configuration
MYSQL_HOST = os.getenv("HOST")
MYSQL_DB = os.getenv("DATABASE")
MYSQL_USER = os.getenv("USER_NAME")
MYSQL_PASSWORD = os.getenv("PASSWORD")
REDIS_HOST = 'localhost'
USER_ID=1

# Connect to MySQL
REDIS_PORT = 6379

# Connect to Redis
def get_redis_connection(REDIS_HOST, REDIS_PORT, db):
    try:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    except redis.RedisError as e:
        print(f"Error connecting to Redis: {e}")
        return None

def create_database_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("MySQL Database connection successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

def fetch_data_from_mysql(user_id):
    connection = create_database_connection()
    if connection is None:
        return None
    query = f"""
        SELECT r.*, d.DeviceModel, d.DeviceManufacturer, hr.HeartRateMin_bpm, hr.HeartRateMax_bpm, hr.HeartRateAvg_bpm
        FROM reading r
        JOIN device d ON r.DeviceID = d.DeviceID
        LEFT JOIN heartrate hr ON r.ReadingID = hr.ReadingID
        WHERE d.UserID = {user_id}
        AND DATE(r.Date) >= NOW() - INTERVAL 7 DAY;
        """
    try:
        data = pd.read_sql(query, connection)
    except Exception as e:
        print(f"Error fetching data from MySQL: {e}")
        return None
    finally:
        connection.close()
    return data

# Store data in Redis
def cache_data_in_redis(key, data):
    r = get_redis_connection()
    if r:
        try:
            r.set(key, data.to_json(), ex=86400)  # Cache for 24 hours
            print("Cache updated in Redis.")
        except Exception as e:
            print(f"Error caching data in Redis: {e}")

# Main function to update cache
def update_cache(user_id):
    key = f"user_data:{user_id}"
    data = fetch_data_from_mysql(user_id)
    if data is not None and not data.empty:
        cache_data_in_redis(key, data)
    else:
        print('No data fetched from MySQL or empty dataset.')

if __name__ == "__main__":
    update_cache(USER_ID)

