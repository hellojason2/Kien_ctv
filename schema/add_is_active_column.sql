-- Migration script to add is_active column to commission_settings table
-- Created: January 14, 2026

-- Check if column exists (PostgreSQL 9.5+)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='commission_settings' 
        AND column_name='is_active'
    ) THEN
        -- Add is_active column
        ALTER TABLE commission_settings 
        ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
        
        -- Set all existing levels to active
        UPDATE commission_settings 
        SET is_active = TRUE
        WHERE is_active IS NULL;
        
        RAISE NOTICE 'Successfully added is_active column to commission_settings table';
    ELSE
        RAISE NOTICE 'is_active column already exists in commission_settings table';
    END IF;
END $$;

-- Verify the changes
SELECT level, rate, label, is_active 
FROM commission_settings 
ORDER BY level;
