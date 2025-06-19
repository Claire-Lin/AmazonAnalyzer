-- Initialize Amazon Analyzer Database
-- This script sets up the initial database structure

-- Create database if it doesn't exist (handled by Docker)
-- The database is created automatically by the PostgreSQL Docker container

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create initial tables (these will also be created by SQLAlchemy but this ensures they exist)
-- The actual table creation is handled by the backend application

-- Insert initial data or configurations if needed
-- Currently no initial data is required

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE amazon_analyzer TO postgres;