-- ================================================================================================
-- PostgreSQL Initialization Script for Elderly Welfare Chatbot
-- ================================================================================================
-- This script runs automatically when the PostgreSQL container is first created
-- ================================================================================================

-- Create extensions (if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- Grant all privileges on database
GRANT ALL PRIVILEGES ON DATABASE elderly_rag_db TO elderly_rag_user;

-- Grant privileges on schema
GRANT ALL ON SCHEMA public TO elderly_rag_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO elderly_rag_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON SEQUENCES TO elderly_rag_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON FUNCTIONS TO elderly_rag_user;

-- Create custom types or functions if needed
-- (Add any custom SQL here)

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL initialization complete for elderly_rag_db';
END $$;
