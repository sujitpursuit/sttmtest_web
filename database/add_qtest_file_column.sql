-- Add qtest_file column to version_comparisons table
-- This column will store the Azure Blob URL for QTest files associated with comparisons

-- Step 1: Add the column
ALTER TABLE version_comparisons 
ADD qtest_file NVARCHAR(500) NULL;
GO

-- Step 2: Add index for faster lookups
CREATE INDEX IX_version_comparisons_qtest_file 
ON version_comparisons(qtest_file) 
WHERE qtest_file IS NOT NULL;
GO

-- Step 3: Add a comment to document the column
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Azure Blob Storage URL for the QTest file used in this comparison', 
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'version_comparisons',
    @level2type = N'COLUMN', @level2name = 'qtest_file';
GO