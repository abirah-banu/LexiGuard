import pyodbc

def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 18 for SQL Server};'
        'SERVER=DESKTOP-V5E9VUI\\SQLEXPRESS;'
        'DATABASE=LexiGuardDB;'
        'Trusted_Connection=yes;'
        'Encrypt=no;'
    )
    return conn
