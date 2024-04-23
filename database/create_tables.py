import mysql.connector
from mysql.connector import Error

host_name = os.getenv("HOST_NAME")
user_name = os.getenv("USER_NAME")
user_password = os.getenv("PASSWORD")
db_name = os.getenv("DATABASE")

# Function to create a connection to the database
def create_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

# Function to execute a query
def execute_query(connection, query, data):
    cursor = connection.cursor()
    try:
        cursor.execute(query, data)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Connect to the MySQL Database
connection = create_connection(host_name, user_name, user_password, db_name)

# Data to insert - replace with your actual data
user_data = ("Bartosz", "Rzycki", "bartek.rzycki@gmail.com", "2000-09-10", "Male")
device_data = (1, "JPT-B19", "Huawei", "2022-12-27")

# SQL statement for inserting into User table
insert_user_query = """
INSERT INTO User (FirstName, LastName, Email, DateOfBirth, Gender) VALUES (%s, %s, %s, %s, %s);
"""

# SQL statement for inserting into Device table
insert_device_query = """
INSERT INTO Device (UserID, DeviceModel, DeviceManufacturer, PurchaseDate) VALUES (%s, %s, %s, %s);
"""

# Execute SQL queries to insert data
execute_query(connection, insert_user_query, user_data)
execute_query(connection, insert_device_query, device_data)
