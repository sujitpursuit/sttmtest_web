-- Migration: Add blob storage columns for test step outputs
-- Date: 2025-09-08
-- Purpose: Store both delta and in-place test generation outputs in Azure Blob

-- Add columns for Delta mode outputs
ALTER TABLE version_comparisons ADD delta_json_url NVARCHAR(500) NULL;
GO
ALTER TABLE version_comparisons ADD delta_excel_url NVARCHAR(500) NULL;
GO
ALTER TABLE version_comparisons ADD delta_generated_at DATETIME NULL;
GO

-- Add columns for In-place mode outputs
ALTER TABLE version_comparisons ADD inplace_json_url NVARCHAR(500) NULL;
GO
ALTER TABLE version_comparisons ADD inplace_excel_url NVARCHAR(500) NULL;
GO
ALTER TABLE version_comparisons ADD inplace_generated_at DATETIME NULL;
GO

-- Add indexes for faster queries
CREATE INDEX idx_version_comparisons_delta_generated ON version_comparisons(delta_generated_at);
GO
CREATE INDEX idx_version_comparisons_inplace_generated ON version_comparisons(inplace_generated_at);
GO

-- Verify the changes
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
ORDER BY ORDINAL_POSITION;