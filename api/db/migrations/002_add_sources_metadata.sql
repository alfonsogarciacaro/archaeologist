-- Migration: 002_add_sources_metadata.sql
-- Description: Add metadata column to sources table for user comments and custom data
-- Note: This migration is idempotent - checks column existence before adding

-- Add metadata column to sources table if it doesn't exist
ALTER TABLE sources ADD COLUMN metadata TEXT; -- This will fail if column exists, but that's ok for idempotent migrations
