"""
Fix missing blob columns in version_comparisons table
"""
import os
import sys
import pyodbc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

def fix_missing_columns():
    """Add missing columns to version_comparisons table"""
    
    connection_string = os.getenv('AZURE_SQL_CONNECTION_STRING')
    if not connection_string:
        print("[ERROR] AZURE_SQL_CONNECTION_STRING not configured")
        return False
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        print("Checking for missing columns...")
        
        # Check which columns exist
        check_query = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'version_comparisons' 
        AND COLUMN_NAME IN (
            'delta_json_url', 'delta_excel_url', 'delta_generated_at',
            'inplace_json_url', 'inplace_excel_url', 'inplace_generated_at'
        )
        """
        cursor.execute(check_query)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        required_columns = [
            'delta_json_url', 'delta_excel_url', 'delta_generated_at',
            'inplace_json_url', 'inplace_excel_url', 'inplace_generated_at'
        ]
        
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            print(f"Missing columns: {', '.join(missing_columns)}")
            
            # Add missing columns
            for col in missing_columns:
                try:
                    if col.endswith('_url'):
                        sql = f"ALTER TABLE version_comparisons ADD {col} NVARCHAR(500) NULL"
                    else:  # _generated_at
                        sql = f"ALTER TABLE version_comparisons ADD {col} DATETIME NULL"
                    
                    print(f"Adding column: {col}")
                    cursor.execute(sql)
                    conn.commit()
                    print(f"  [OK] Added {col}")
                except pyodbc.Error as e:
                    if 'already exists' in str(e):
                        print(f"  [SKIP] {col} already exists")
                    else:
                        print(f"  [ERROR] Failed to add {col}: {e}")
        else:
            print("All columns already exist")
        
        # Verify all columns now exist
        cursor.execute(check_query)
        final_columns = [row[0] for row in cursor.fetchall()]
        
        if len(final_columns) == 6:
            print(f"\n[SUCCESS] All 6 columns verified: {', '.join(final_columns)}")
            return True
        else:
            print(f"\n[WARNING] Only {len(final_columns)} columns exist: {', '.join(final_columns)}")
            return False
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_missing_columns()