from db_config import get_db_connection

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    IF NOT EXISTS (
        SELECT * FROM sysobjects WHERE name='Users' AND xtype='U'
    )
    CREATE TABLE Users (
        id INT PRIMARY KEY IDENTITY,
        username NVARCHAR(50) UNIQUE,
        password NVARCHAR(100)
    )
    ''')

    cursor.execute('''
    IF NOT EXISTS (
        SELECT * FROM sysobjects WHERE name='History' AND xtype='U'
    )
    CREATE TABLE History (
        id INT PRIMARY KEY IDENTITY,
        user_id INT,
        input_text NVARCHAR(MAX),
        plagiarism_percent FLOAT,
        timestamp DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (user_id) REFERENCES Users(id)
    )
    ''')

    conn.commit()
    conn.close()
