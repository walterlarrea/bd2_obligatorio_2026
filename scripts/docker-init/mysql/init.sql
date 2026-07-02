-- Init script for MySQL container (runs once at DB initialization)
-- Creates user and grants privileges (credentials match docker-compose)
CREATE USER IF NOT EXISTS 'mvcc_user'@'%' IDENTIFIED BY 'mvcc_pass';
GRANT ALL PRIVILEGES ON mvcc_db.* TO 'mvcc_user'@'%';
FLUSH PRIVILEGES;
