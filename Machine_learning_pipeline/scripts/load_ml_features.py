"""
Load processed ML features table into MySQL database.
This table contains merged agricultural data ready for machine learning.
"""
import pandas as pd
import pymysql
from pathlib import Path
import sys
from datetime import datetime
import time

sys.path.append(str(Path(__file__).parent.parent))
from config.database import get_mysql_connection, MYSQL_DATABASE


def drop_and_recreate_ml_features_table(connection):
    """Drop and recreate the ML features table to ensure it's clean."""
    print("Ensuring clean table structure...")
    
    cursor = connection.cursor()
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # First, check if table exists and drop it
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = 'ml_features'
            """, (MYSQL_DATABASE,))
            
            table_exists = cursor.fetchone()[0] > 0
            
            if table_exists:
                print(f"Attempt {attempt + 1}: Dropping existing ml_features table...")
                cursor.execute("DROP TABLE IF EXISTS ml_features")
                connection.commit()
                print("✓ Dropped existing ml_features table")
                
                # Small delay to ensure table is fully dropped
                time.sleep(1)
            
            # Create new table with proper structure
            create_table_query = """
            CREATE TABLE ml_features (
                id INT AUTO_INCREMENT PRIMARY KEY,
                area VARCHAR(100) NOT NULL,
                year INT NOT NULL,
                crop_type VARCHAR(100),
                crop_yield DECIMAL(15, 2),
                rainfall DECIMAL(10, 2),
                temperature DECIMAL(6, 2),
                pesticide_usage DECIMAL(12, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_area (area),
                INDEX idx_year (year),
                INDEX idx_crop_type (crop_type),
                INDEX idx_area_year (area, year),
                INDEX idx_area_year_crop (area, year, crop_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            cursor.execute(create_table_query)
            connection.commit()
            print(" Created new ml_features table")
            return True
            
        except pymysql.Error as e:
            print(f" Attempt {attempt + 1} failed: {e}")
            connection.rollback()
            
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("All retry attempts failed")
                return False
        finally:
            cursor.close()


def force_drop_table(connection):
    """Force drop table using different methods."""
    print("Attempting forced table drop...")
    
    cursor = connection.cursor()
    try:
        # Method 1: Standard drop
        cursor.execute("DROP TABLE IF EXISTS ml_features")
        connection.commit()
        print(" Standard drop completed")
        
        # Verify table is gone
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = 'ml_features'
        """, (MYSQL_DATABASE,))
        
        if cursor.fetchone()[0] == 0:
            print(" Table successfully dropped")
            return True
        else:
            print("Table still exists after drop")
            return False
            
    except Exception as e:
        print(f"Force drop failed: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def check_table_exists(connection):
    """Check if ml_features table exists and show its structure."""
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = 'ml_features'
        """, (MYSQL_DATABASE,))
        
        exists = cursor.fetchone()[0] > 0
        print(f"Table exists in information_schema: {exists}")
        
        if exists:
            try:
                cursor.execute("DESCRIBE ml_features")
                print("Table structure:")
                for column in cursor.fetchall():
                    print(f"  {column}")
            except Exception as e:
                print(f"  Could not describe table: {e}")
        
        return exists
    finally:
        cursor.close()


def load_ml_features_csv(csv_file, connection, chunk_size=1000):
    """Load ML features CSV into MySQL table."""
    print(f"\n{'='*60}")
    print(f"Loading ML features from {csv_file}...")
    print(f"{'='*60}")
    
    start_time = datetime.now()
    
    try:
        # Read the entire CSV
        df = pd.read_csv(csv_file)
        print(f" Loaded CSV: {len(df):,} rows, {len(df.columns)} columns")
        print(f"Columns in CSV: {list(df.columns)}")
        
        # Clean the data
        df = df.replace('', None)
        df = df.replace('..', None)
        df = df.where(pd.notnull(df), None)
        
        # Prepare insert query
        available_columns = ['area', 'year', 'crop_type', 'crop_yield', 'rainfall', 'temperature', 'pesticide_usage']
        
        # Check if all required columns exist in the CSV
        missing_columns = [col for col in available_columns if col not in df.columns]
        if missing_columns:
            print(f"Missing columns in CSV: {missing_columns}")
            print(f"  Available columns: {list(df.columns)}")
            # Use only columns that exist in both
            available_columns = [col for col in available_columns if col in df.columns]
        
        placeholders = ', '.join(['%s'] * len(available_columns))
        insert_query = f"INSERT INTO ml_features ({', '.join(available_columns)}) VALUES ({placeholders})"
        
        print(f"Insert query: {insert_query}")
        
        # Convert to list of tuples with proper data types
        data = []
        success_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                data_tuple = []
                for col in available_columns:
                    value = row[col]
                    if pd.isna(value) or value is None:
                        data_tuple.append(None)
                    elif col == 'year':
                        data_tuple.append(int(value))
                    elif col in ['crop_yield', 'rainfall', 'temperature', 'pesticide_usage']:
                        data_tuple.append(float(value))
                    else:
                        data_tuple.append(str(value))
                
                data.append(tuple(data_tuple))
                success_count += 1
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Show first 5 errors
                    print(f"  Data conversion error row {index}: {e}")
                    print(f"  Problematic row: {dict(row)}")
        
        print(f" Data converted: {success_count} successful, {error_count} errors")
        
        if not data:
            print(" No valid data to insert")
            return 0
        
        # Insert in chunks
        cursor = connection.cursor()
        total_rows = 0
        
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            try:
                cursor.executemany(insert_query, chunk)
                connection.commit()
                total_rows += len(chunk)
                
                if (i // chunk_size) % 10 == 0:
                    print(f"  Processed {total_rows:,} rows...")
                    
            except Exception as e:
                print(f"\n  Error inserting chunk {i//chunk_size}: {e}")
                connection.rollback()
                # Try individual inserts for this chunk
                chunk_success = 0
                for j, row_data in enumerate(chunk):
                    try:
                        cursor.execute(insert_query, row_data)
                        chunk_success += 1
                    except Exception as individual_error:
                        if j < 3:  # Show first 3 individual errors
                            print(f"    Row {i+j} failed: {individual_error}")
                connection.commit()
                total_rows += chunk_success
                print(f"    Individual insertion: {chunk_success}/{len(chunk)} successful")
        
        cursor.close()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n Loaded {total_rows:,} rows into ml_features table")
        print(f"  Time: {duration:.2f} seconds")
        if duration > 0:
            print(f"  Rate: {total_rows/duration:.0f} rows/second")
        
        return total_rows
        
    except Exception as e:
        print(f" Error loading ML features: {e}")
        import traceback
        traceback.print_exc()
        return 0


def verify_ml_features(connection):
    """Verify the ML features data."""
    print(f"\n{'='*60}")
    print("VERIFYING ML FEATURES DATA...")
    print(f"{'='*60}")
    
    cursor = connection.cursor()
    
    try:
        # Count total rows
        cursor.execute("SELECT COUNT(*) FROM ml_features")
        total_rows = cursor.fetchone()[0]
        print(f" Total rows in ml_features: {total_rows:,}")
        
        if total_rows == 0:
            print(" Table is empty!")
            return
        
        # Count by crop type
        cursor.execute("""
            SELECT crop_type, COUNT(*) as count 
            FROM ml_features 
            WHERE crop_type IS NOT NULL 
            GROUP BY crop_type 
            ORDER BY count DESC 
            LIMIT 10
        """)
        print(f"\nTop crop types:")
        for crop, count in cursor.fetchall():
            print(f"  {crop}: {count:,} rows")
        
        # Data coverage
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN rainfall IS NOT NULL THEN 1 ELSE 0 END) as has_rainfall,
                SUM(CASE WHEN temperature IS NOT NULL THEN 1 ELSE 0 END) as has_temperature,
                SUM(CASE WHEN pesticide_usage IS NOT NULL THEN 1 ELSE 0 END) as has_pesticides
            FROM ml_features
        """)
        total, has_rainfall, has_temp, has_pesticides = cursor.fetchone()
        
        print(f"\nData Coverage:")
        print(f"  Rainfall: {has_rainfall:,} ({has_rainfall/total*100:.1f}%)")
        print(f"  Temperature: {has_temp:,} ({has_temp/total*100:.1f}%)")
        print(f"  Pesticides: {has_pesticides:,} ({has_pesticides/total*100:.1f}%)")
        
        # Year range
        cursor.execute("SELECT MIN(year), MAX(year) FROM ml_features")
        min_year, max_year = cursor.fetchone()
        print(f"  Year range: {min_year} - {max_year}")
        
        # Show sample data
        cursor.execute("SELECT * FROM ml_features LIMIT 3")
        print(f"\nSample data:")
        columns = [desc[0] for desc in cursor.description]
        print(f"  Columns: {columns}")
        for row in cursor.fetchall():
            print(f"  {row}")
        
    except Exception as e:
        print(f" Error during verification: {e}")
    finally:
        cursor.close()


def main():
    """Main function to load ML features table."""
    print(f"\n{'#'*60}")
    print("# ML Features Table Loading Script")
    print("# Database: agriculture_db")
    print(f"{'#'*60}\n")
    
    # Path to your ML features CSV
    ml_features_csv = Path(__file__).parent.parent / "data" / "ml_features.csv"
    
    if not ml_features_csv.exists():
        print(f"ML features CSV not found: {ml_features_csv}")
        sys.exit(1)
    
    try:
        # Connect to MySQL
        print("Connecting to MySQL...")
        connection = get_mysql_connection()
        print(f"Connected to database: {MYSQL_DATABASE}\n")
        
        # Check current table state
        print("Checking current table state...")
        table_exists = check_table_exists(connection)
        
        if table_exists:
            print("\nForce dropping existing table...")
            if not force_drop_table(connection):
                print("Failed to drop existing table. Please check for locks or permissions.")
                sys.exit(1)
        
        # Create table
        if not drop_and_recreate_ml_features_table(connection):
            print("Failed to create table")
            sys.exit(1)
        
        # Load data
        start_time = datetime.now()
        total_rows = load_ml_features_csv(ml_features_csv, connection)
        
        if total_rows > 0:
            # Verify the data
            verify_ml_features(connection)
            
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            print(f"\n{'='*60}")
            print(f" ML FEATURES TABLE LOADED SUCCESSFULLY!")
            print(f"  Total rows: {total_rows:,}")
            print(f"  Total time: {total_duration:.2f} seconds")
            print(f"{'='*60}\n")
        else:
            print(f"\n Failed to load any data into ml_features table")
        
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        if 'connection' in locals():
            connection.close()
            print("Database connection closed.\n")


if __name__ == "__main__":
    main()