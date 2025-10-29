-- MySQL Schema for Agriculture Database
-- Database: agriculture_db
-- Expected total rows: ~139,000

DROP DATABASE IF EXISTS agriculture_db;
CREATE DATABASE agriculture_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE agriculture_db;

-- Table 1: Rainfall Data (6,727 rows)
CREATE TABLE rainfall (
    id INT AUTO_INCREMENT PRIMARY KEY,
    area VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    average_rain_fall_mm_per_year DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_area (area),
    INDEX idx_year (year),
    INDEX idx_area_year (area, year),
    UNIQUE KEY uk_area_year (area, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 2: Temperature Data (71,311 rows)
CREATE TABLE temperature (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year INT NOT NULL,
    country VARCHAR(100) NOT NULL,
    avg_temp DECIMAL(6, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_country (country),
    INDEX idx_year (year),
    INDEX idx_country_year (country, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 3: Pesticides Data (4,349 rows)
CREATE TABLE pesticides (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domain VARCHAR(100),
    area VARCHAR(100) NOT NULL,
    element VARCHAR(100),
    item VARCHAR(100),
    year INT NOT NULL,
    unit VARCHAR(100),
    value DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_area (area),
    INDEX idx_year (year),
    INDEX idx_area_year (area, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table 4: Crop Yield Data (56,717 rows)
CREATE TABLE crop_yield (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domain_code VARCHAR(10),
    domain VARCHAR(100),
    area_code INT,
    area VARCHAR(100) NOT NULL,
    element_code INT,
    element VARCHAR(100),
    item_code INT,
    item VARCHAR(100) NOT NULL,
    year_code INT,
    year INT NOT NULL,
    unit VARCHAR(50),
    value DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_area (area),
    INDEX idx_year (year),
    INDEX idx_item (item),
    INDEX idx_area_year_item (area, year, item)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Summary Statistics View
CREATE VIEW data_summary AS
SELECT 
    'rainfall' AS table_name,
    COUNT(*) AS row_count,
    MIN(year) AS min_year,
    MAX(year) AS max_year,
    COUNT(DISTINCT area) AS unique_areas
FROM rainfall
UNION ALL
SELECT 
    'temperature' AS table_name,
    COUNT(*) AS row_count,
    MIN(year) AS min_year,
    MAX(year) AS max_year,
    COUNT(DISTINCT country) AS unique_areas
FROM temperature
UNION ALL
SELECT 
    'pesticides' AS table_name,
    COUNT(*) AS row_count,
    MIN(year) AS min_year,
    MAX(year) AS max_year,
    COUNT(DISTINCT area) AS unique_areas
FROM pesticides
UNION ALL
SELECT 
    'crop_yield' AS table_name,
    COUNT(*) AS row_count,
    MIN(year) AS min_year,
    MAX(year) AS max_year,
    COUNT(DISTINCT area) AS unique_areas
FROM crop_yield;

-- View for ML features (joining all tables)
CREATE VIEW ml_features AS
SELECT 
    r.area,
    r.year,
    r.average_rain_fall_mm_per_year AS rainfall,
    t.avg_temp AS temperature,
    p.value AS pesticide_usage,
    y.item AS crop_type,
    y.value AS crop_yield
FROM rainfall r
LEFT JOIN temperature t ON LOWER(r.area) = LOWER(t.country) AND r.year = t.year
LEFT JOIN pesticides p ON r.area = p.area AND r.year = p.year
LEFT JOIN crop_yield y ON r.area = y.area AND r.year = y.year
WHERE y.value IS NOT NULL;
