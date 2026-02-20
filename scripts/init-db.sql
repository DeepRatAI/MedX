-- =============================================================================
-- MedeX - PostgreSQL Database Initialization Script
-- =============================================================================
-- This script is executed on first container startup
-- Creates extensions and initial configuration
-- Tables are managed by Alembic migrations
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- Create schemas if needed
-- (using public schema by default)

-- Grant permissions (for containerized deployment)
GRANT ALL PRIVILEGES ON DATABASE medex TO medex;
GRANT ALL PRIVILEGES ON SCHEMA public TO medex;

-- Create initial configuration table for app settings
CREATE TABLE IF NOT EXISTS app_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default configuration values
INSERT INTO app_config (key, value, description) VALUES
    ('version', '"2.0.0"', 'MedeX application version'),
    ('initialized_at', 'null', 'Database initialization timestamp'),
    ('features', '{"memory_enabled": true, "rag_enabled": true, "tools_enabled": true}', 'Feature flags'),
    ('limits', '{"rate_limit_per_minute": 60, "context_window_messages": 50, "max_conversation_age_days": 90}', 'System limits')
ON CONFLICT (key) DO NOTHING;

-- Update initialization timestamp
UPDATE app_config SET value = to_jsonb(NOW()) WHERE key = 'initialized_at';

-- Create function for updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'MedeX database initialized successfully at %', NOW();
END $$;
