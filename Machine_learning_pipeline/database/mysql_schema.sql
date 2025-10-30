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

-- ============================================================================
-- STORED PROCEDURES & TRIGGERS
-- ============================================================================

-- Table for logging data changes (audit trail)
CREATE TABLE data_audit_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    record_id INT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(50) DEFAULT USER(),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_table_name (table_name),
    INDEX idx_operation (operation),
    INDEX idx_changed_at (changed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table for data validation errors
CREATE TABLE data_validation_errors (
    error_id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INT,
    error_message TEXT NOT NULL,
    error_type VARCHAR(50),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_table_name (table_name),
    INDEX idx_detected_at (detected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- STORED PROCEDURE 1: Data Validation and Quality Check
-- ============================================================================
-- Purpose: Validates data quality across all tables and logs issues
-- Usage: CALL validate_agriculture_data();

DELIMITER //

CREATE PROCEDURE validate_agriculture_data()
BEGIN
    DECLARE validation_count INT DEFAULT 0;
    
    -- Clear previous validation results for today
    DELETE FROM data_validation_errors WHERE DATE(detected_at) = CURDATE();
    
    -- Validate Rainfall Data
    -- Check for negative rainfall values
    INSERT INTO data_validation_errors (table_name, record_id, error_message, error_type)
    SELECT 'rainfall', id, 
           CONCAT('Invalid rainfall value: ', average_rain_fall_mm_per_year, ' mm for ', area, ' in ', year),
           'NEGATIVE_VALUE'
    FROM rainfall
    WHERE average_rain_fall_mm_per_year < 0;
    
    -- Check for unrealistic rainfall values (> 15000 mm/year)
    INSERT INTO data_validation_errors (table_name, record_id, error_message, error_type)
    SELECT 'rainfall', id, 
           CONCAT('Unrealistic rainfall value: ', average_rain_fall_mm_per_year, ' mm for ', area, ' in ', year),
           'UNREALISTIC_VALUE'
    FROM rainfall
    WHERE average_rain_fall_mm_per_year > 15000;
    
    -- Validate Temperature Data
    -- Check for unrealistic temperature values (< -90°C or > 60°C)
    INSERT INTO data_validation_errors (table_name, record_id, error_message, error_type)
    SELECT 'temperature', id, 
           CONCAT('Unrealistic temperature: ', avg_temp, '°C for ', country, ' in ', year),
           'UNREALISTIC_VALUE'
    FROM temperature
    WHERE avg_temp < -90 OR avg_temp > 60;
    
    -- Validate Pesticides Data
    -- Check for negative pesticide values
    INSERT INTO data_validation_errors (table_name, record_id, error_message, error_type)
    SELECT 'pesticides', id, 
           CONCAT('Negative pesticide value: ', value, ' for ', area, ' in ', year),
           'NEGATIVE_VALUE'
    FROM pesticides
    WHERE value < 0;
    
    -- Validate Crop Yield Data
    -- Check for negative yield values
    INSERT INTO data_validation_errors (table_name, record_id, error_message, error_type)
    SELECT 'crop_yield', id, 
           CONCAT('Negative yield value: ', value, ' for ', item, ' in ', area, ' (', year, ')'),
           'NEGATIVE_VALUE'
    FROM crop_yield
    WHERE value < 0;
    
    -- Check for missing years (data integrity)
    INSERT INTO data_validation_errors (table_name, record_id, error_message, error_type)
    SELECT 'crop_yield', id,
           CONCAT('Invalid year: ', year, ' for ', item, ' in ', area),
           'INVALID_YEAR'
    FROM crop_yield
    WHERE year < 1800 OR year > YEAR(CURDATE());
    
    -- Get total validation errors found
    SELECT COUNT(*) INTO validation_count FROM data_validation_errors;
    
    -- Return summary
    SELECT 
        table_name,
        error_type,
        COUNT(*) as error_count,
        MIN(detected_at) as first_detected
    FROM data_validation_errors
    GROUP BY table_name, error_type
    ORDER BY error_count DESC;
    
    -- Return summary message
    SELECT CONCAT('Validation complete. Found ', validation_count, ' issues.') AS summary;
    
END//

DELIMITER ;

-- ============================================================================
-- STORED PROCEDURE 2: Get Agricultural Summary Statistics
-- ============================================================================
-- Purpose: Generates comprehensive statistics for a specific area and year range
-- Usage: CALL get_agriculture_stats('India', 2010, 2015);

DELIMITER //

CREATE PROCEDURE get_agriculture_stats(
    IN p_area VARCHAR(100),
    IN p_start_year INT,
    IN p_end_year INT
)
BEGIN
    -- Rainfall statistics
    SELECT 
        'Rainfall Statistics' AS metric_type,
        p_area AS area,
        p_start_year AS start_year,
        p_end_year AS end_year,
        COUNT(*) AS data_points,
        ROUND(AVG(average_rain_fall_mm_per_year), 2) AS avg_rainfall,
        ROUND(MIN(average_rain_fall_mm_per_year), 2) AS min_rainfall,
        ROUND(MAX(average_rain_fall_mm_per_year), 2) AS max_rainfall,
        ROUND(STDDEV(average_rain_fall_mm_per_year), 2) AS std_dev
    FROM rainfall
    WHERE area = p_area 
      AND year BETWEEN p_start_year AND p_end_year;
    
    -- Temperature statistics (matching by country name)
    SELECT 
        'Temperature Statistics' AS metric_type,
        p_area AS area,
        p_start_year AS start_year,
        p_end_year AS end_year,
        COUNT(*) AS data_points,
        ROUND(AVG(avg_temp), 2) AS avg_temperature,
        ROUND(MIN(avg_temp), 2) AS min_temperature,
        ROUND(MAX(avg_temp), 2) AS max_temperature,
        ROUND(STDDEV(avg_temp), 2) AS std_dev
    FROM temperature
    WHERE country = p_area 
      AND year BETWEEN p_start_year AND p_end_year;
    
    -- Pesticide usage statistics
    SELECT 
        'Pesticide Statistics' AS metric_type,
        p_area AS area,
        p_start_year AS start_year,
        p_end_year AS end_year,
        COUNT(*) AS data_points,
        ROUND(AVG(value), 2) AS avg_pesticide_use,
        ROUND(MIN(value), 2) AS min_pesticide_use,
        ROUND(MAX(value), 2) AS max_pesticide_use,
        ROUND(SUM(value), 2) AS total_pesticide_use
    FROM pesticides
    WHERE area = p_area 
      AND year BETWEEN p_start_year AND p_end_year;
    
    -- Crop yield statistics by crop type
    SELECT 
        item AS crop_type,
        COUNT(*) AS data_points,
        ROUND(AVG(value), 2) AS avg_yield,
        ROUND(MIN(value), 2) AS min_yield,
        ROUND(MAX(value), 2) AS max_yield,
        ROUND(SUM(value), 2) AS total_yield,
        unit
    FROM crop_yield
    WHERE area = p_area 
      AND year BETWEEN p_start_year AND p_end_year
    GROUP BY item, unit
    ORDER BY avg_yield DESC
    LIMIT 10;
    
END//

DELIMITER ;

-- ============================================================================
-- TRIGGER 1: Audit Trail for Crop Yield Updates
-- ============================================================================
-- Purpose: Automatically logs any changes to crop yield data
-- Triggered: After UPDATE on crop_yield table

DELIMITER //

CREATE TRIGGER trg_crop_yield_update_audit
AFTER UPDATE ON crop_yield
FOR EACH ROW
BEGIN
    -- Only log if the yield value actually changed
    IF OLD.value != NEW.value OR (OLD.value IS NULL AND NEW.value IS NOT NULL) OR (OLD.value IS NOT NULL AND NEW.value IS NULL) THEN
        INSERT INTO data_audit_log (
            table_name,
            operation,
            record_id,
            old_value,
            new_value
        ) VALUES (
            'crop_yield',
            'UPDATE',
            NEW.id,
            CONCAT('area:', OLD.area, ', year:', OLD.year, ', item:', OLD.item, ', value:', IFNULL(OLD.value, 'NULL')),
            CONCAT('area:', NEW.area, ', year:', NEW.year, ', item:', NEW.item, ', value:', IFNULL(NEW.value, 'NULL'))
        );
    END IF;
END//

DELIMITER ;

-- ============================================================================
-- TRIGGER 2: Validate Data on Insert for Rainfall Table
-- ============================================================================
-- Purpose: Prevents insertion of invalid rainfall data (negative or unrealistic values)
-- Triggered: Before INSERT on rainfall table

DELIMITER //

CREATE TRIGGER trg_rainfall_validate_insert
BEFORE INSERT ON rainfall
FOR EACH ROW
BEGIN
    -- Validate rainfall value is not negative
    IF NEW.average_rain_fall_mm_per_year < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Rainfall value cannot be negative';
    END IF;
    
    -- Validate rainfall value is not unrealistically high (> 15000 mm)
    IF NEW.average_rain_fall_mm_per_year > 15000 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Rainfall value exceeds realistic maximum (15000 mm/year)';
    END IF;
    
    -- Validate year is reasonable
    IF NEW.year < 1800 OR NEW.year > YEAR(CURDATE()) + 1 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Year must be between 1800 and current year';
    END IF;
END//

DELIMITER ;

-- ============================================================================
-- TRIGGER 3: Audit Trail for Pesticide Data Deletions
-- ============================================================================
-- Purpose: Logs when pesticide records are deleted (for compliance tracking)
-- Triggered: Before DELETE on pesticides table

DELIMITER //

CREATE TRIGGER trg_pesticides_delete_audit
BEFORE DELETE ON pesticides
FOR EACH ROW
BEGIN
    INSERT INTO data_audit_log (
        table_name,
        operation,
        record_id,
        old_value,
        new_value
    ) VALUES (
        'pesticides',
        'DELETE',
        OLD.id,
        CONCAT('area:', OLD.area, ', year:', OLD.year, ', value:', IFNULL(OLD.value, 'NULL'), ', unit:', IFNULL(OLD.unit, 'NULL')),
        NULL
    );
END//

DELIMITER ;

-- ============================================================================
-- DEMONSTRATION QUERIES
-- ============================================================================

-- Query to demonstrate stored procedure usage:
-- CALL validate_agriculture_data();
-- CALL get_agriculture_stats('India', 2010, 2015);

-- Query to view audit logs:
-- SELECT * FROM data_audit_log ORDER BY changed_at DESC LIMIT 20;

-- Query to view validation errors:
-- SELECT * FROM data_validation_errors ORDER BY detected_at DESC;
