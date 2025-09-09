-- Migration script to add impact report blob storage columns
-- This script adds columns to store Azure Blob URLs for impact analysis HTML and JSON reports
-- For SQL Server / Azure SQL Database
-- Date: 2025-01-09

-- Check if columns exist before adding them
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'version_comparisons' 
               AND COLUMN_NAME = 'impact_html_blob_url')
BEGIN
    ALTER TABLE version_comparisons ADD impact_html_blob_url NVARCHAR(MAX);
    PRINT 'Added impact_html_blob_url column';
END

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'version_comparisons' 
               AND COLUMN_NAME = 'impact_json_blob_url')
BEGIN
    ALTER TABLE version_comparisons ADD impact_json_blob_url NVARCHAR(MAX);
    PRINT 'Added impact_json_blob_url column';
END

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'version_comparisons' 
               AND COLUMN_NAME = 'impact_analysis_timestamp')
BEGIN
    ALTER TABLE version_comparisons ADD impact_analysis_timestamp DATETIME2;
    PRINT 'Added impact_analysis_timestamp column';
END

-- Add index for better query performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_version_comparisons_impact_timestamp')
BEGIN
    CREATE INDEX idx_version_comparisons_impact_timestamp 
    ON version_comparisons(impact_analysis_timestamp);
    PRINT 'Created index on impact_analysis_timestamp';
END

-- Add extended properties for documentation (SQL Server way)
EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', 
    @value=N'Azure Blob Storage URL for impact analysis HTML report',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'version_comparisons',
    @level2type=N'COLUMN', @level2name=N'impact_html_blob_url';

EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', 
    @value=N'Azure Blob Storage URL for impact analysis JSON report',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'version_comparisons',
    @level2type=N'COLUMN', @level2name=N'impact_json_blob_url';

EXEC sys.sp_addextendedproperty 
    @name=N'MS_Description', 
    @value=N'Timestamp when impact analysis was last performed',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'version_comparisons',
    @level2type=N'COLUMN', @level2name=N'impact_analysis_timestamp';

-- Verify the columns were added successfully
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM 
    INFORMATION_SCHEMA.COLUMNS
WHERE 
    TABLE_NAME = 'version_comparisons'
    AND COLUMN_NAME IN ('impact_html_blob_url', 'impact_json_blob_url', 'impact_analysis_timestamp')
ORDER BY 
    ORDINAL_POSITION;