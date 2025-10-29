"""
Load CSV data into MySQL database.
Expected rows: ~139,000 total
- rainfall: 6,727
- temperature: 71,311
- pesticides: 4,349
- crop_yield: 56,717
"""
import pandas as pd
import pymysql
from pathlib import Path
import sys
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))
from config.database import get_mysql_connection, MYSQL_DATABASE


def load_csv_to_mysql(csv_file, table_name, connection, chunk_size=1000):
    """Load CSV data into MySQL table in chunks."""
    print(f"\n{'='*60}")
    print(f"Loading {csv_file} into {table_name}...")
    print(f"{'='*60}")
    
    start_time = datetime.now()
    
    # Read CSV in chunks for memory efficiency
    total_rows = 0
    
    for i, chunk in enumerate(pd.read_csv(csv_file, chunksize=chunk_size)):
        # Strip whitespace from column names
        chunk.columns = chunk.columns.str.strip()
        
        # Convert column names with spaces to lowercase with underscores
        # E.g., "Domain Code" -> "domain_code"
        chunk.columns = chunk.columns.str.replace(' ', '_').str.lower()
        
        # Clean data: replace empty strings and '..' with None
        chunk = chunk.replace('', None)
        chunk = chunk.replace('..', None)
        chunk = chunk.replace('  ', None)
        
        # Prepare data for insertion with backticks for column names
        columns = ', '.join([f'`{col}`' for col in chunk.columns])
        placeholders = ', '.join(['%s'] * len(chunk.columns))
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        # Convert DataFrame to list of tuples, replacing NaN with None
        data = []
        for row in chunk.values:
            # Convert each value, replacing NaN with None
            clean_row = tuple(None if pd.isna(val) else val for val in row)
            data.append(clean_row)
        
        # Execute batch insert
        cursor = connection.cursor()
        try:
            cursor.executemany(insert_query, data)
            connection.commit()
            total_rows += len(data)
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Processed {total_rows:,} rows...", end='\r')
        except Exception as e:
            print(f"\n  Error inserting chunk {i}: {e}")
            connection.rollback()
        finally:
            cursor.close()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n✓ Loaded {total_rows:,} rows in {duration:.2f} seconds")
    print(f"  Rate: {total_rows/duration:.0f} rows/second\n")
    
    return total_rows


def verify_data_load(connection):
    """Verify loaded data counts."""
    print(f"\n{'='*60}")
    print("VERIFICATION: Checking row counts...")
    print(f"{'='*60}\n")
    
    cursor = connection.cursor()
    tables = ['rainfall', 'temperature', 'pesticides', 'crop_yield']
    
    total = 0
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        total += count
        print(f"  {table:15s}: {count:>7,} rows")
    
    print(f"  {'-'*25}")
    print(f"  {'TOTAL':15s}: {total:>7,} rows\n")
    
    # Show data summary
    cursor.execute("SELECT * FROM data_summary")
    print(f"{'='*60}")
    print("DATA SUMMARY:")
    print(f"{'='*60}")
    print(f"{'Table':<15} {'Rows':>10} {'Min Year':>10} {'Max Year':>10} {'Areas':>10}")
    print(f"{'-'*60}")
    
    for row in cursor.fetchall():
        print(f"{row[0]:<15} {row[1]:>10,} {row[2]:>10} {row[3]:>10} {row[4]:>10}")
    
    cursor.close()
    print(f"{'='*60}\n")


def main():
    """Main function to load all CSV files into MySQL."""
    print(f"\n{'#'*60}")
    print("# MySQL Data Loading Script")
    print("# Database: agriculture_db")
    print("# Expected Total: ~139,000 rows")
    print(f"{'#'*60}\n")
    
    # Base path for CSV files
    base_path = Path(__file__).parent.parent
    
    # CSV to table mapping
    csv_mappings = [
        ('rainfall.csv', 'rainfall'),
        ('temp.csv', 'temperature'),
        ('pesticides.csv', 'pesticides'),
        ('yield.csv', 'crop_yield')
    ]
    
    try:
        # Connect to MySQL
        print("Connecting to MySQL...")
        connection = get_mysql_connection()
        print(f"✓ Connected to database: {MYSQL_DATABASE}\n")
        
        # Load each CSV file
        total_start = datetime.now()
        
        for csv_file, table_name in csv_mappings:
            csv_path = base_path / csv_file
            
            if not csv_path.exists():
                print(f"⚠ Warning: {csv_file} not found, skipping...")
                continue
            
            load_csv_to_mysql(csv_path, table_name, connection)
        
        total_end = datetime.now()
        total_duration = (total_end - total_start).total_seconds()
        
        # Verify the loaded data
        verify_data_load(connection)
        
        print(f"{'='*60}")
        print(f"✓ ALL DATA LOADED SUCCESSFULLY!")
        print(f"  Total time: {total_duration:.2f} seconds")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    
    finally:
        if 'connection' in locals():
            connection.close()
            print("Database connection closed.\n")


if __name__ == "__main__":
    main()
