import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import redis
from mysql.connector import Error
import mysql.connector
from redis_database import get_redis_connection, create_database_connection, fetch_data_from_mysql


# Constants
KJ_TO_KCAL = 0.239006
REDIS_PORT = 6379
USER_ID=1

MYSQL_HOST = os.getenv("HOST")
MYSQL_DB = os.getenv("DATBASE")
MYSQL_USER = os.getenv("USERNAME")
MYSQL_PASSWORD = os.getenv("PASSWORD")
REDIS_HOST = os.getenv("REDIS_HOST")

# Fetch data from MySQL
def fetch_data_from_mysql(user_id, start_date, end_date, connection):
    query = f"""
    SELECT r.*, d.DeviceModel, d.DeviceManufacturer, hr.HeartRateMin_bpm, hr.HeartRateMax_bpm, hr.HeartRateAvg_bpm
    FROM Reading r
    JOIN Device d ON r.DeviceID = d.DeviceID
    LEFT JOIN HeartRate hr ON r.ReadingID = hr.ReadingID
    WHERE d.UserID = {user_id}
    AND DATE(r.Date) BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}';
    """
    return pd.read_sql(query, connection)

# Function to load data based on date range
def load_data(user_id, start_date, end_date):
    r = get_redis_connection(REDIS_HOST, REDIS_PORT, 0)
    print(r)
    key = f"user_data:{user_id}"
    cached_data = r.get(key)

    if r:
        try:
            cached_data = r.get(key)
            if cached_data:
                print("data retrived from redis successfully")
        except Exception as e:
            print(f"Error loading data from Redis: {e}")

    # Check if the selected dates are within the last 7 days
    if cached_data and (datetime.now().date() - end_date).days <= 7:
        data = pd.read_json(cached_data)
        # Filter data for the given range
        print('data from redis')
        return data[(data['Date'] >= pd.to_datetime(start_date)) & (data['Date'] <= pd.to_datetime(end_date))]
    else:
        # Fetch data directly from MySQL for dates outside the last 7 days
        print('data from mysql')
        connection = create_database_connection(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB)
        return fetch_data_from_mysql(user_id, start_date, end_date, connection)

# Convert kJ to kcal
def convert_kj_to_kcal(data, column):
    if column in data.columns:
        data[column] = data[column] * KJ_TO_KCAL
    return data


# Streamlit user interface function
def main():
    st.title('Health and Activity Dashboard')

    # Sidebar for user inputs
    st.sidebar.header('User Input Features')
    date_option = st.sidebar.selectbox(
        "Select Date Range",
        ('Today', 'Yesterday', 'Last 24 hours', 'Last 3 days', 'Last week', 'Custom')
    )

    if date_option == 'Custom':
        start_date, end_date = st.sidebar.date_input("Select custom date range", [])
    else:
        today = datetime.now().date()
        if date_option == 'Today':
            start_date = end_date = today
        elif date_option == 'Yesterday':
            start_date = end_date = today - timedelta(days=1)
        elif date_option == 'Last 24 hours':
            start_date = datetime.now() - timedelta(days=1)
            end_date = datetime.now()
        elif date_option == 'Last 3 days':
            start_date = today - timedelta(days=3)
            end_date = today
        elif date_option == 'Last week':
            start_date = today - timedelta(weeks=1)
            end_date = today

    data = load_data(USER_ID, start_date, end_date)

    if data.empty:
        st.error("Data not available for the selected dates.")
    else:
        st.write("Filtered Data:", data)

        metric = st.sidebar.selectbox(
            "Choose a metric to display",
            [col for col in data.columns if 'kJ' not in col] + [col.replace(' (kJ)', ' (kcal)') for col in data.columns if 'kJ' in col]
        )

        # Metrics display and other UI elements as before
        display_data(data, metric)

def display_data(data, metric):
    original_metric = metric.replace(' (kcal)', ' (kJ)') if 'kcal' in metric else metric
    if 'kcal' in metric:
        data = convert_kj_to_kcal(data, original_metric)

    if st.sidebar.checkbox('Show raw data'):
        st.write(data[original_metric])

    st.write(f"### {metric}")
    fig, ax = plt.subplots()
    if not data.empty:
        sns.lineplot(data=data, x='Date', y=metric, ax=ax)
    st.pyplot(fig)

    st.write(f"## Summary for {metric}")
    st.write(f"Average: {data[original_metric].mean():.2f}")
    st.write(f"Minimum: {data[original_metric].min()}")
    st.write(f"Maximum: {data[original_metric].max()}")

if __name__ == "__main__":
    main()
