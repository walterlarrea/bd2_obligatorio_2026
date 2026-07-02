-- Init script for Postgres container (runs once at DB initialization)
-- This will create a dedicated user for convenience (credentials match docker-compose)
DO
$$
BEGIN
    -- create user if not exists
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mvcc_user') THEN
        CREATE USER mvcc_user WITH PASSWORD 'mvcc_pass';
    END IF;
    -- grant privileges on the database
    GRANT ALL PRIVILEGES ON DATABASE mvcc_db TO mvcc_user;
END
$$;
