# Quick Start Guide - Agriculture Database Setup

## Overview
This project sets up MySQL and MongoDB databases with agricultural data consisting of **~139,000 rows** across 4 CSV files.

## Data Summary
| Dataset | Rows | Columns |
|---------|------|---------|
| rainfall.csv | 6,728 | 3 (Area, Year, Rainfall) |
| temp.csv | 71,312 | 3 (Year, Country, Temperature) |
| pesticides.csv | 4,350 | 7 (Area, Year, Value, etc.) |
| yield.csv | 56,718 | 13 (Area, Year, Item, Value, etc.) |

## Quick Setup (4 Steps)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Setup MySQL Database

```bash
# Create database
mysql -u root -p -e "CREATE DATABASE agriculture_db;"

# Load schema
mysql -u root -p agriculture_db < database/mysql_schema.sql

# Load data (~2-3 minutes for 139k rows)
python3 database/load_mysql.py
```

### 4. Setup MongoDB

```bash
# Ensure MongoDB is running
# mongod --dbpath /path/to/data

# Load data
python3 database/load_mongodb.py
```

## Expected Row Counts

### MySQL Tables
After loading, verify counts with:
```sql
USE agriculture_db;
SELECT * FROM data_summary;
```

Expected counts:
- `rainfall`: ~6,727 rows
- `temperature`: ~71,311 rows
- `pesticides`: ~4,349 rows
- `crop_yield`: ~56,717 rows
- **Total**: ~139,104 rows

### MongoDB Collections
Verify with:
```javascript
use agriculture_db
db.rainfall.countDocuments({})
db.temperature.countDocuments({})
db.pesticides.countDocuments({})
db.crop_yield.countDocuments({})
```

## Testing the Setup

### Test Database Connections
```bash
python3 test_setup.py
```

### Test MySQL Queries
```sql
-- Count all rows
SELECT COUNT(*) FROM rainfall;

-- Sample data
SELECT * FROM rainfall WHERE area = 'India' LIMIT 10;
```

### Test MongoDB Queries
```javascript
// Count documents
db.rainfall.countDocuments({})

// Sample data
db.rainfall.find({ Area: "India" }).limit(10)
```

## Project Structure
```
archive/
├── README.md                    # Main documentation
├── QUICKSTART.md               # This file
├── requirements.txt            # Python dependencies
├── setup.sh                    # Setup script
├── test_setup.py               # Verification script
├── .env.example                # Environment template
├── config/
│   └── database.py            # Database connections
├── database/
│   ├── mysql_schema.sql       # MySQL schema (4 tables)
│   ├── load_mysql.py          # Load ~139k rows to MySQL
│   └── load_mongodb.py        # Load ~139k docs to MongoDB
└── CSV files                  # 4 data files
```

## Common Issues

### Issue: Import errors when running scripts
**Solution**: Ensure dependencies are installed: `pip install -r requirements.txt`

### Issue: MySQL connection refused
**Solution**: Check MySQL is running and credentials in .env are correct

### Issue: MongoDB connection timeout
**Solution**: Ensure MongoDB is running: `mongod --dbpath /your/data/path`

## Performance Notes

- **MySQL Loading**: ~139k rows take 2-3 minutes
- **MongoDB Loading**: ~139k documents take 1-2 minutes
- Both loaders show progress and verify counts

## Summary

✅ **MySQL**: 4 tables with indexes for 139,104 rows  
✅ **MongoDB**: 4 collections with indexes for 139,104 documents  
✅ **Automated**: Scripts handle loading with progress tracking  
✅ **Verified**: Test scripts confirm successful loading  
