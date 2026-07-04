-- Schema for CareerConnect

CREATE DATABASE IF NOT EXISTS careerconnect;
USE careerconnect;

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  fullname VARCHAR(255),
  email VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  phone VARCHAR(32),
  location VARCHAR(255),
  skills TEXT,
  education TEXT,
  experience TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Resumes table
CREATE TABLE IF NOT EXISTS resumes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  resume_path VARCHAR(1024),
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Jobs table (basic seed)
CREATE TABLE IF NOT EXISTS jobs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  company_name VARCHAR(255),
  location VARCHAR(255),
  salary VARCHAR(255),
  experience VARCHAR(255),
  category VARCHAR(100),
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Saved jobs
CREATE TABLE IF NOT EXISTS saved_jobs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  job_id INT NOT NULL,
  saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_saved (user_id, job_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- Applications
CREATE TABLE IF NOT EXISTS applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  job_id INT NOT NULL,
  status VARCHAR(50) DEFAULT 'applied',
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- User settings (notifications + job preferences)
CREATE TABLE IF NOT EXISTS user_settings (
  id                   INT AUTO_INCREMENT PRIMARY KEY,
  user_id              INT NOT NULL UNIQUE,
  notif_job_alerts     TINYINT(1) DEFAULT 1,
  notif_app_status     TINYINT(1) DEFAULT 1,
  notif_weekly_digest  TINYINT(1) DEFAULT 0,
  notif_profile_views  TINYINT(1) DEFAULT 0,
  pref_category        VARCHAR(100) DEFAULT '',
  pref_location        VARCHAR(255) DEFAULT '',
  pref_salary          VARCHAR(100) DEFAULT '',
  pref_experience      VARCHAR(100) DEFAULT '',
  pref_job_type        VARCHAR(100) DEFAULT '',
  updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Sample jobs
INSERT INTO jobs (title, company_name, location, salary, experience, category, description)
VALUES
('Python Developer','Google','Mountain View, CA','$120k - $140k','2-4 years','IT','Build backend services and APIs using Python.'),
('Frontend Developer','Microsoft','Redmond, WA','$110k - $130k','2-4 years','IT','Create responsive UI components with React.'),
('Data Analyst','Amazon','Seattle, WA','$95k - $115k','1-3 years','Finance','Analyze business metrics and build dashboards.')
ON DUPLICATE KEY UPDATE id=id;
