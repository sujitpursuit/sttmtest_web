"""
Database Migration Test Script
Runs the SQL script to add qtest_file column to version_comparisons table
"""

import os
import sys
import pyodbc
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_database_connection():
    """Get database connection using environment variables"""
    connection_string = os.getenv('AZURE_SQL_CONNECTION_STRING')
    if not connection_string:
        raise ValueError("AZURE_SQL_CONNECTION_STRING not found in environment variables")
    
    try:
        conn = pyodbc.connect(connection_string)
        logger.info("Successfully connected to Azure SQL Database")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


def check_column_exists(connection):
    """Check if qtest_file column already exists"""
    try:
        cursor = connection.cursor()
        
        query = """
        SELECT COUNT(*) as column_exists
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'version_comparisons' 
        AND COLUMN_NAME = 'qtest_file'
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        exists = result.column_exists > 0
        logger.info(f"Column 'qtest_file' exists: {exists}")
        
        return exists
        
    except Exception as e:
        logger.error(f"Error checking column existence: {e}")
        return False


def run_migration_sql(connection):
    """Execute the database migration SQL script"""
    try:
        # Read the SQL migration file
        sql_file_path = Path(__file__).parent.parent / "database" / "add_qtest_file_column.sql"
        
        if not sql_file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {sql_file_path}")
        
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        logger.info(f"Reading SQL migration from: {sql_file_path}")
        
        # Split SQL content by individual statements (separated by GO or semicolons)
        sql_statements = []
        current_statement = ""
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if line.startswith('--') or not line:
                continue
            
            # Handle GO statements (batch separator)
            if line.upper() == 'GO':
                if current_statement.strip():
                    sql_statements.append(current_statement.strip())
                    current_statement = ""
                continue
            
            current_statement += line + "\n"
        
        # Add the last statement if it exists
        if current_statement.strip():
            sql_statements.append(current_statement.strip())
        
        logger.info(f"Found {len(sql_statements)} SQL statements to execute")
        
        # Execute each statement
        cursor = connection.cursor()
        
        for i, statement in enumerate(sql_statements, 1):
            try:
                logger.info(f"Executing statement {i}/{len(sql_statements)}")
                logger.debug(f"SQL: {statement[:100]}...")  # Log first 100 chars
                
                cursor.execute(statement)
                connection.commit()
                
                logger.info(f"Statement {i} executed successfully")
                
            except Exception as e:
                logger.error(f"Error executing statement {i}: {e}")
                logger.error(f"Statement: {statement}")
                connection.rollback()
                raise
        
        logger.info("All migration statements executed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def verify_migration(connection):
    """Verify that the migration was successful"""
    try:
        cursor = connection.cursor()
        
        # Check column details
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'version_comparisons' 
        AND COLUMN_NAME = 'qtest_file'
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            logger.info("Migration verification successful!")
            logger.info(f"Column: {result.COLUMN_NAME}")
            logger.info(f"Data Type: {result.DATA_TYPE}")
            logger.info(f"Max Length: {result.CHARACTER_MAXIMUM_LENGTH}")
            logger.info(f"Nullable: {result.IS_NULLABLE}")
            
            # Check if index was created
            index_query = """
            SELECT COUNT(*) as index_exists
            FROM sys.indexes i
            INNER JOIN sys.objects o ON i.object_id = o.object_id
            WHERE o.name = 'version_comparisons' 
            AND i.name = 'IX_version_comparisons_qtest_file'
            """
            
            cursor.execute(index_query)
            index_result = cursor.fetchone()
            
            if index_result.index_exists > 0:
                logger.info("Index 'IX_version_comparisons_qtest_file' created successfully")
            else:
                logger.warning("Index was not created (this might be expected)")
            
            return True
        else:
            logger.error("Column was not created successfully")
            return False
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


def main():
    """Main migration function"""
    try:
        logger.info("Starting database migration for QTest Azure integration")
        logger.info("=" * 60)
        
        # Get database connection
        conn = get_database_connection()
        
        # Check if column already exists
        if check_column_exists(conn):
            logger.warning("Column 'qtest_file' already exists! Migration may have been run before.")
            
            user_input = input("Continue anyway? (y/n): ").lower()
            if user_input != 'y':
                logger.info("Migration cancelled by user")
                return False
        
        # Run the migration
        logger.info("Running database migration...")
        run_migration_sql(conn)
        
        # Verify the migration
        logger.info("Verifying migration...")
        success = verify_migration(conn)
        
        if success:
            logger.info("=" * 60)
            logger.info("✅ DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("The 'qtest_file' column has been added to version_comparisons table")
            logger.info("Ready for Azure QTest upload functionality!")
            return True
        else:
            logger.error("❌ Migration verification failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False
    
    finally:
        try:
            conn.close()
            logger.info("Database connection closed")
        except:
            pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)