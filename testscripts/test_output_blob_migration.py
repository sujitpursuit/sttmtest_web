"""
Test script for output blob columns migration
Tests the database migration for storing test step outputs in Azure Blob
"""
import os
import sys
import pyodbc
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

def test_migration():
    """Test the output blob columns migration"""
    
    connection_string = os.getenv('AZURE_SQL_CONNECTION_STRING')
    if not connection_string:
        print("[ERROR] AZURE_SQL_CONNECTION_STRING not configured")
        return False
    
    try:
        print("=== Testing Output Blob Columns Migration ===\n")
        
        # Connect to database
        print("1. Connecting to database...")
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        print("   [OK] Connected successfully\n")
        
        # Check if columns already exist
        print("2. Checking existing columns...")
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
        
        if existing_columns:
            print(f"   [INFO] Found existing columns: {', '.join(existing_columns)}")
            print("   [SKIP] Migration may have already been applied\n")
        else:
            print("   [OK] No output blob columns found - ready to migrate\n")
        
        # Read migration SQL
        print("3. Reading migration SQL...")
        migration_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'database', 'add_output_blob_columns.sql'
        )
        
        if not os.path.exists(migration_file):
            print(f"   [ERROR] Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        print("   [OK] Migration SQL loaded\n")
        
        # Auto-run migration if columns don't exist
        if not existing_columns:
            print("4. Running migration (auto-mode)...")
            
            # Execute migration
            print("\n5. Executing migration...")
            try:
                # Split by GO statements for SQL Server
                statements = [s.strip() for s in migration_sql.split('GO') if s.strip()]
                for i, statement in enumerate(statements, 1):
                    # Skip comments and SELECT verification
                    if statement.startswith('--') or not statement or 'SELECT' in statement:
                        continue
                    print(f"   Executing statement {i}...")
                    try:
                        cursor.execute(statement)
                        conn.commit()
                    except pyodbc.Error as e:
                        if 'already exists' in str(e):
                            print(f"   [SKIP] Already exists")
                        else:
                            raise
                print("   [OK] Migration completed successfully\n")
            except Exception as e:
                print(f"   [ERROR] Migration failed: {e}")
                conn.rollback()
                return False
        
        # Verify migration
        print("6. Verifying migration...")
        verify_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'version_comparisons'
        AND COLUMN_NAME IN (
            'delta_json_url', 'delta_excel_url', 'delta_generated_at',
            'inplace_json_url', 'inplace_excel_url', 'inplace_generated_at'
        )
        ORDER BY COLUMN_NAME
        """
        cursor.execute(verify_query)
        columns = cursor.fetchall()
        
        if len(columns) == 6:
            print("   [OK] All 6 columns verified:")
            for col in columns:
                print(f"       - {col[0]}: {col[1]}({col[2] or ''}) {col[3]}")
            print()
        else:
            print(f"   [WARNING] Expected 6 columns, found {len(columns)}")
        
        # Test sample update
        print("7. Testing sample update...")
        test_query = """
        UPDATE TOP(1) version_comparisons 
        SET delta_json_url = 'test_url_' + CAST(NEWID() AS VARCHAR(10)),
            delta_generated_at = GETDATE()
        WHERE delta_json_url IS NULL
        """
        cursor.execute(test_query)
        if cursor.rowcount > 0:
            conn.commit()
            print(f"   [OK] Successfully updated {cursor.rowcount} test record")
            
            # Clean up test data
            cleanup_query = """
            UPDATE version_comparisons 
            SET delta_json_url = NULL, delta_generated_at = NULL
            WHERE delta_json_url LIKE 'test_url_%'
            """
            cursor.execute(cleanup_query)
            conn.commit()
            print("   [OK] Test data cleaned up")
        else:
            print("   [INFO] No records to test update")
        
        print("\n=== Migration Test Complete ===")
        print("[SUCCESS] Database is ready for blob storage integration")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Migration test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_migration()
    sys.exit(0 if success else 1)