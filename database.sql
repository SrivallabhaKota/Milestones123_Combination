-- ============================================================
--  FinSight – Personal Finance & Investment Intelligence Platform
--  Database Schema
--  Ready for phpMyAdmin Import
-- ============================================================

-- Create and select the database
CREATE DATABASE IF NOT EXISTS finsight
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE finsight;

-- ============================================================
--  Table: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(100)  NOT NULL,
  email       VARCHAR(100)  NOT NULL UNIQUE,
  password    VARCHAR(255)  NOT NULL,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
--  Sample Insert  (password = Test@1234 — bcrypt hash)
--  Use this only for testing; real passwords are stored hashed
-- ============================================================
INSERT INTO users (name, email, password) VALUES
  (
    'Demo User',
    'demo@finsight.com',
    '$2b$12$KIXxLpf4q1cTaV3sYlQS9.GZtN5f.kFQzPqFdD8Xr1BkW2jH7eIBm'
  );

-- ============================================================
--  Verify
-- ============================================================
SELECT id, name, email, created_at FROM users;
