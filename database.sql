CREATE DATABASE IF NOT EXISTS finsight
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE finsight;

CREATE TABLE IF NOT EXISTS users (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(100)  NOT NULL,
  email       VARCHAR(100)  NOT NULL UNIQUE,
  password    VARCHAR(255)  NOT NULL,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS income (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT           NOT NULL,
  source      VARCHAR(100)  NOT NULL,
  amount      DECIMAL(10,2) NOT NULL,
  income_date DATE          NOT NULL,
  notes       VARCHAR(255),
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS expenses (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  user_id      INT           NOT NULL,
  category     VARCHAR(100)  NOT NULL,
  amount       DECIMAL(10,2) NOT NULL,
  expense_date DATE          NOT NULL,
  notes        VARCHAR(255),
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS budget (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  user_id      INT           NOT NULL,
  category     VARCHAR(100)  NOT NULL,
  limit_amount DECIMAL(10,2) NOT NULL,
  month        INT           NOT NULL,
  year         INT           NOT NULL,
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY unique_budget_per_month (user_id, category, month, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO users (name, email, password) VALUES
  (
    'Demo User',
    'demo@finsight.com',
    '$2b$12$KIXxLpf4q1cTaV3sYlQS9.GZtN5f.kFQzPqFdD8Xr1BkW2jH7eIBm'
  );

