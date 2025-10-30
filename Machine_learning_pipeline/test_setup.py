"""
Test script to verify the database setup
Run this after setting up databases and loading data
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

print("="*70)
print("AGRICULTURE DATABASE SETUP - SYSTEM TEST")
print("="*70)

# Test 1: Check imports
print("\n[1/5] Testing imports...")
try:
    import pandas as pd
    import pymysql
    from pymongo import MongoClient
    print("✓ All required packages are installed")
except ImportError as e:
    print(f"✗ Missing package: {e}")
    print("  Run: pip install -r requirements.txt")
    sys.exit(1)

# Test 2: Check environment configuration
print("\n[2/5] Testing environment configuration...")
try:
    from config.database import MYSQL_HOST, MONGO_HOST, MYSQL_DATABASE
    print(f"✓ Configuration loaded")
    print(f"  MySQL Host: {MYSQL_HOST}")
    print(f"  MongoDB Host: {MONGO_HOST}")
    print(f"  Database Name: {MYSQL_DATABASE}")
except Exception as e:
    print(f"✗ Configuration error: {e}")
    print("  Make sure .env file exists with correct settings")
    sys.exit(1)

# Test 3: Check MySQL connection and data
print("\n[3/5] Testing MySQL connection...")
try:
    from config.database import get_mysql_connection
    conn = get_mysql_connection()
    cursor = conn.cursor()
    
    # Check tables exist
    tables = ['rainfall', 'temperature', 'pesticides', 'crop_yield']
    table_counts = {}
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        table_counts[table] = count
        print(f"  ✓ {table}: {count:,} rows")
    
    total = sum(table_counts.values())
    print(f"  ✓ Total: {total:,} rows")
    
    if total < 100000:
        print(f"  ⚠ Warning: Expected ~139,000 rows, found {total:,}")
        print(f"    Run: python3 database/load_mysql.py")
    
    cursor.close()
    conn.close()
    print("✓ MySQL connection successful")
    
except Exception as e:
    print(f"✗ MySQL connection failed: {e}")
    print("  Make sure MySQL is running and data is loaded")
    print("  Run: python3 database/load_mysql.py")

# Test 4: Check MongoDB connection and data
print("\n[4/5] Testing MongoDB connection...")
try:
    from config.database import get_mongodb
    db = get_mongodb()
    
    collections = ['rainfall', 'temperature', 'pesticides', 'crop_yield']
    coll_counts = {}
    
    for coll_name in collections:
        count = db[coll_name].count_documents({})
        coll_counts[coll_name] = count
        print(f"  ✓ {coll_name}: {count:,} documents")
    
    total = sum(coll_counts.values())
    print(f"  ✓ Total: {total:,} documents")
    
    if total < 100000:
        print(f"  ⚠ Warning: Expected ~139,000 documents, found {total:,}")
        print(f"    Run: python3 database/load_mongodb.py")
    
    print("✓ MongoDB connection successful")
    
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
    print("  Make sure MongoDB is running and data is loaded")
    print("  Run: python3 database/load_mongodb.py")

# Test 5: Check CSV files
print("\n[5/5] Testing CSV files...")
csv_files = ['data/rainfall.csv', 'data/temp.csv', 'data/pesticides.csv', 'data/yield.csv']
base_path = Path(__file__).parent

for csv_file in csv_files:
    csv_path = base_path / csv_file
    if csv_path.exists():
        # Count lines
        with open(csv_path, 'r') as f:
            line_count = sum(1 for _ in f) - 1  # Exclude header
        print(f"  ✓ {csv_file}: {line_count:,} rows")
    else:
        print(f"  ✗ {csv_file}: Not found")

# Summary
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print("\nSystem Status:")
print("  ✓ Python packages: OK")
print("  ✓ Configuration: OK")

try:
    conn = get_mysql_connection()
    conn.close()
    print("  ✓ MySQL: OK")
except:
    print("  ✗ MySQL: FAILED")

try:
    db = get_mongodb()
    print("  ✓ MongoDB: OK")
except:
    print("  ✗ MongoDB: FAILED")

print("\nNext Steps:")
print("1. If databases are empty, load data:")
print("   python3 database/load_mysql.py")
print("   python3 database/load_mongodb.py")
print("2. Verify data with queries:")
print("   MySQL: SELECT * FROM data_summary;")
print("   MongoDB: db.rainfall.countDocuments({})")
print("\n" + "="*70 + "\n")
