-- Migration 001: Add jobs table for background processing
-- This table tracks background jobs for file processing and other async tasks

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,                    -- UUID for job identification
    job_type TEXT NOT NULL,                 -- Job type (file_processing, batch_processing, investigation)
    status TEXT NOT NULL DEFAULT 'pending', -- Job status (pending, queued, running, completed, failed, cancelled)
    priority TEXT NOT NULL DEFAULT 'normal',-- Job priority (low, normal, high, urgent)

    -- Foreign keys
    project_id INTEGER,                     -- Associated project (optional)
    user_id INTEGER NOT NULL,               -- User who created the job
    source_id INTEGER,                      -- Source being processed (optional)
    investigation_id INTEGER,               -- Investigation being processed (optional)

    -- Job data
    job_data TEXT,                          -- JSON data for job parameters
    result_data TEXT,                       -- JSON result data (if successful)
    error_message TEXT,                     -- Error message (if failed)

    -- Progress tracking
    progress_current INTEGER DEFAULT 0,     -- Current progress count
    progress_total INTEGER DEFAULT 0,       -- Total progress count
    progress_message TEXT,                  -- Progress description

    -- Processing metadata
    worker_id TEXT,                         -- ID of worker processing the job
    retry_count INTEGER DEFAULT 0,          -- Number of retry attempts
    max_retries INTEGER DEFAULT 3,          -- Maximum retry attempts
    timeout_seconds INTEGER DEFAULT 3600,   -- Job timeout in seconds

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    queued_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Foreign key constraints
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE,
    FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_project_id ON jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority);
CREATE INDEX IF NOT EXISTS idx_jobs_source_id ON jobs(source_id);
CREATE INDEX IF NOT EXISTS idx_jobs_investigation_id ON jobs(investigation_id);

-- Create unique constraint for job IDs
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_id ON jobs(id);