import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="User-12910",
    database="suport_ti"
)

cursor = conn.cursor(dictionary=True)
