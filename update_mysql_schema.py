import os
from dotenv import load_dotenv
import pymysql
from pymysql.cursors import DictCursor

# Load environment variables
load_dotenv()

# Database configuration
DB_USERNAME = os.getenv('DB_USERNAME', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'capa_ai_system')

def update_schema():
    """Add machine_name and batch_number columns to capa_issues table if they don't exist"""
    # Connect to MySQL database
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USERNAME,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
            # Check if columns exist
            cursor.execute("DESCRIBE capa_issues")
            columns = [column['Field'] for column in cursor.fetchall()]
            
            # Add machine_name column if it doesn't exist
            if 'machine_name' not in columns:
                cursor.execute("ALTER TABLE capa_issues ADD COLUMN machine_name VARCHAR(200)")
                print("Added machine_name column to capa_issues table")
            else:
                print("machine_name column already exists")
                
            # Add batch_number column if it doesn't exist
            if 'batch_number' not in columns:
                cursor.execute("ALTER TABLE capa_issues ADD COLUMN batch_number VARCHAR(100)")
                print("Added batch_number column to capa_issues table")
            else:
                print("batch_number column already exists")
                
            connection.commit()
            print("Schema update completed successfully")
            
    except Exception as e:
        print(f"Error updating schema: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    print("Starting MySQL schema update...")
    update_schema()
    print("Schema update finished.")
