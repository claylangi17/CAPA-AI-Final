import pymysql
import re
from config import SQLALCHEMY_DATABASE_URI

def add_column_to_root_cause():
    """Add the user_adjusted_whys_json column to the root_causes table"""
    
    # Parse MySQL connection details from SQLAlchemy URI
    # Format: mysql+pymysql://username:password@host/dbname
    match = re.match(r'mysql\+pymysql://([^:]+):([^@]*)@([^/]+)/(.+)', SQLALCHEMY_DATABASE_URI)
    
    if not match:
        print(f"Invalid MySQL URI format: {SQLALCHEMY_DATABASE_URI}")
        return False
    
    username, password, host, dbname = match.groups()
    
    try:
        # Connect to the MySQL database
        conn = pymysql.connect(
            host=host,
            user=username,
            password=password,
            database=dbname
        )
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("SHOW COLUMNS FROM root_causes LIKE 'user_adjusted_whys_json'")
        column_exists = cursor.fetchone() is not None
        
        if not column_exists:
            print("Adding user_adjusted_whys_json column to root_causes table...")
            cursor.execute('ALTER TABLE root_causes ADD COLUMN user_adjusted_whys_json TEXT')
            conn.commit()
            print("Column added successfully!")
        else:
            print("Column user_adjusted_whys_json already exists in root_causes table.")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating database schema: {e}")
        return False

if __name__ == '__main__':
    add_column_to_root_cause()
