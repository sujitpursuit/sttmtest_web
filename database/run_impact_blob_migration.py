"""
Script to add impact report blob storage columns to the database
Run this script to add columns for storing Azure Blob URLs for impact analysis reports
"""

import os
import sys
import pyodbc
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import from api
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()


def run_migration():
    """Run the database migration to add impact report blob columns"""
    
    # Get database connection string from environment
    connection_string = os.getenv('AZURE_SQL_CONNECTION_STRING')
    
    if not connection_string:
        print("Error: AZURE_SQL_CONNECTION_STRING environment variable not set")
        print("Please set it in your .env file")
        return False
    
    conn = None
    cursor = None
    
    try:
        # Connect to database
        print("Connecting to Azure SQL Database...")
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # First, check what tables exist in the database
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(tables)} tables in database:")
        for table in tables:
            print(f"  - {table}")
        
        # Check if version_comparisons table exists
        if 'version_comparisons' not in tables:
            print("\n[ERROR] Table 'version_comparisons' does not exist in the database!")
            print("Available tables are:", ", ".join(tables))
            return False
        
        print("\nTable 'version_comparisons' found. Checking existing columns...")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'version_comparisons' 
            AND COLUMN_NAME IN ('impact_html_blob_url', 'impact_json_blob_url', 'impact_analysis_timestamp')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        if len(existing_columns) == 3:
            print("Success: All impact report blob columns already exist:")
            for col in existing_columns:
                print(f"  - {col}")
            print("No migration needed.")
            return
        
        print(f"Adding impact report blob columns to version_comparisons table...")
        
        # Add impact_html_blob_url column
        if 'impact_html_blob_url' not in existing_columns:
            cursor.execute("ALTER TABLE version_comparisons ADD impact_html_blob_url NVARCHAR(MAX)")
            print("  [OK] Added impact_html_blob_url column")
        
        # Add impact_json_blob_url column  
        if 'impact_json_blob_url' not in existing_columns:
            cursor.execute("ALTER TABLE version_comparisons ADD impact_json_blob_url NVARCHAR(MAX)")
            print("  [OK] Added impact_json_blob_url column")
        
        # Add impact_analysis_timestamp column
        if 'impact_analysis_timestamp' not in existing_columns:
            cursor.execute("ALTER TABLE version_comparisons ADD impact_analysis_timestamp DATETIME2")
            print("  [OK] Added impact_analysis_timestamp column")
        
        # Create index for better query performance (check if exists first)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_comparisons_impact_timestamp')
            CREATE INDEX idx_comparisons_impact_timestamp 
            ON version_comparisons(impact_analysis_timestamp)
        """)
        print("  [OK] Created/verified index on impact_analysis_timestamp")
        
        # Add column descriptions using extended properties (SQL Server way)
        try:
            cursor.execute("""
                EXEC sys.sp_addextendedproperty 
                @name=N'MS_Description', 
                @value=N'Azure Blob Storage URL for impact analysis HTML report',
                @level0type=N'SCHEMA', @level0name=N'dbo',
                @level1type=N'TABLE', @level1name=N'version_comparisons',
                @level2type=N'COLUMN', @level2name=N'impact_html_blob_url'
            """)
        except:
            pass  # Property might already exist
        
        try:
            cursor.execute("""
                EXEC sys.sp_addextendedproperty 
                @name=N'MS_Description', 
                @value=N'Azure Blob Storage URL for impact analysis JSON report',
                @level0type=N'SCHEMA', @level0name=N'dbo',
                @level1type=N'TABLE', @level1name=N'version_comparisons',
                @level2type=N'COLUMN', @level2name=N'impact_json_blob_url'
            """)
        except:
            pass
        
        try:
            cursor.execute("""
                EXEC sys.sp_addextendedproperty 
                @name=N'MS_Description', 
                @value=N'Timestamp when impact analysis was last performed',
                @level0type=N'SCHEMA', @level0name=N'dbo',
                @level1type=N'TABLE', @level1name=N'version_comparisons',
                @level2type=N'COLUMN', @level2name=N'impact_analysis_timestamp'
            """)
        except:
            pass
        
        print("  [OK] Added column descriptions")
        
        # Commit the changes
        conn.commit()
        print("\n[SUCCESS] Migration completed successfully!")
        
        # Verify the columns were added
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'version_comparisons'
            AND COLUMN_NAME IN ('impact_html_blob_url', 'impact_json_blob_url', 'impact_analysis_timestamp')
            ORDER BY ORDINAL_POSITION
        """)
        
        print("\nVerification - New columns:")
        print("-" * 60)
        for row in cursor.fetchall():
            print(f"  {row[0]:<30} {row[1]:<20} {'NULL' if row[2] == 'YES' else 'NOT NULL'}")
        
        # Show current table structure
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'version_comparisons'
            ORDER BY ORDINAL_POSITION
        """)
        
        print("\nFull table structure:")
        print("-" * 60)
        for row in cursor.fetchall():
            print(f"  {row[0]:<30} {row[1]:<20} {'NULL' if row[2] == 'YES' else 'NOT NULL'}")
        
    except pyodbc.Error as e:
        print(f"\n[ERROR] Database error: {e}")
        if conn:
            conn.rollback()
        return False
        
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        # Close connections
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("\nDatabase connection closed.")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Impact Report Blob Storage Migration")
    print("=" * 60)
    print()
    
    success = run_migration()
    
    if success:
        print("\n" + "=" * 60)
        print("Next steps:")
        print("1. Update version_tracking_service.py to use new columns")
        print("2. Implement blob upload in output_blob_service.py")
        print("3. Update API endpoints to serve from blob storage")
        print("=" * 60)
    else:
        print("\nMigration failed. Please check the error messages above.")
        sys.exit(1)