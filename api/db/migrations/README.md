# Database Migrations

This directory contains database schema migrations for the Enterprise Code Archaeologist.

## Migration System

Our migration system is designed to be **idempotent** - migrations can be run multiple times without causing issues. This simplifies deployment and reduces the need for complex version tracking.

## File Naming Convention

Migration files should follow the pattern: `XXX_description.sql`

- `XXX` - Three-digit, zero-padded sequential number (001, 002, 003, etc.)
- `description` - Brief, descriptive name of what the migration does
- `.sql` - File extension

Example: `002_add_sources_metadata.sql`

## Migration Content

Each migration file should:

1. **Use `IF NOT EXISTS`** for CREATE statements
2. **Include comments** explaining the purpose
3. **Be idempotent** - safe to run multiple times
4. **Handle errors gracefully** - some statements may fail if already applied

### Example Migration

```sql
-- Migration: 003_add_user_avatar.sql
-- Description: Add avatar_url column to users table
-- Note: This migration is idempotent

-- Add avatar_url column if it doesn't exist
ALTER TABLE users ADD COLUMN avatar_url TEXT;
```

## Running Migrations

Migrations are automatically run when the database is initialized:

```python
# In SQLiteDatabase.initialize()
await self._run_database_migrations()
```

The system will:
1. Discover all migration files in this directory
2. Sort them by filename (numerical order)
3. Execute each migration in sequence
4. Continue on errors (idempotent design)

## Current Migrations

- `001_initial_schema.sql` - Creates all base tables and indexes
- `002_add_sources_metadata.sql` - Adds metadata column to sources table

## Adding New Migrations

1. Create new file with next sequential number
2. Write idempotent SQL statements
3. Test the migration
4. Update this README

## Notes

- **No version tracking**: Since migrations are idempotent, we don't track which migrations have been applied
- **No rollback**: Simplified system without rollback capability (can be added later if needed)
- **Error handling**: Failed statements are logged but don't stop the migration process
- **Production ready**: This system is suitable for production use with proper testing

## Future Improvements

For production scaling, consider adding:
- Version tracking table
- Rollback capability
- Migration dependencies
- Dry-run mode
- Migration validation
