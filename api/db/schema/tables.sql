-- Complete Database Schema Reference
-- This file represents the current complete database schema
-- It's generated from the migration files and serves as documentation
-- DO NOT RUN THIS FILE DIRECTLY - use migrations instead

-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Projects table
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    repository_paths TEXT,  -- JSON array of repository paths
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE
);

-- Project users table (many-to-many relationship)
CREATE TABLE project_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, user_id),
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Sources table (for uploaded files)
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_type TEXT NOT NULL,
    content_type TEXT NOT NULL,
    data_lake_entry_id TEXT NOT NULL,
    metadata TEXT, -- JSON metadata for user comments, etc.
    uploaded_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users (id) ON DELETE CASCADE
);

-- Investigations table
CREATE TABLE investigations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_id INTEGER,
    query TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    impact_data TEXT,
    component_count INTEGER,
    knowledge_gap_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_ms INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL
);

-- Knowledge gaps table
CREATE TABLE knowledge_gaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id INTEGER NOT NULL,
    component_name TEXT NOT NULL,
    gap_type TEXT NOT NULL,
    description TEXT NOT NULL,
    suggested_action TEXT NOT NULL,
    confidence_score REAL,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (investigation_id) REFERENCES investigations (id) ON DELETE CASCADE
);

-- System config table
CREATE TABLE system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Nodes table
CREATE TABLE nodes (
    id TEXT PRIMARY KEY,
    project_id INTEGER,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    path TEXT,
    source_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    metadata TEXT,  -- JSON string
    investigation_id INTEGER,
    source_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    FOREIGN KEY (investigation_id) REFERENCES investigations (id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources (id) ON DELETE CASCADE
);

-- Node metadata table
CREATE TABLE node_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_investigations_user_id ON investigations (user_id);
CREATE INDEX idx_investigations_project_id ON investigations (project_id);
CREATE INDEX idx_investigations_status ON investigations (status);
CREATE INDEX idx_knowledge_gaps_investigation_id ON knowledge_gaps (investigation_id);
CREATE INDEX idx_sessions_token ON sessions (session_token);
CREATE INDEX idx_sessions_user_id ON sessions (user_id);
CREATE INDEX idx_projects_created_by ON projects (created_by);
CREATE INDEX idx_projects_is_active ON projects (is_active);
CREATE INDEX idx_project_users_project_id ON project_users (project_id);
CREATE INDEX idx_project_users_user_id ON project_users (user_id);
CREATE INDEX idx_sources_project_id ON sources (project_id);
CREATE INDEX idx_sources_uploaded_by ON sources (uploaded_by);
CREATE INDEX idx_nodes_project_id ON nodes (project_id);
CREATE INDEX idx_nodes_investigation_id ON nodes (investigation_id);
CREATE INDEX idx_nodes_source_id ON nodes (source_id);
CREATE INDEX idx_node_metadata_node_id ON node_metadata (node_id);
