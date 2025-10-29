# Agriculture Database Setup

A database setup project for agricultural data with MySQL and MongoDB integration.

## Data Overview

| File | Rows | Description |
|------|------|-------------|
| rainfall.csv | 6,728 | Rainfall data by area and year |
| temp.csv | 71,312 | Temperature data by country and year |
| pesticides.csv | 4,350 | Pesticide usage data |
| yield.csv | 56,718 | Crop yield data |
| **Total** | **~139,000** | Total rows across all datasets |

## Project Structure

```
archive/
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   └── database.py          # Database connection configurations
├── database/
│   ├── mysql_schema.sql     # MySQL schema definition
│   ├── load_mysql.py        # Script to load data into MySQL
│   └── load_mongodb.py      # Script to load data into MongoDB
└── data/                    # CSV files (existing)
```

## Setup Instructions

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

# Load data (this will take a few minutes for ~139k rows)
python3 database/load_mysql.py
```

### 4. Setup MongoDB

```bash
# Start MongoDB (if not running)
# mongod --dbpath /path/to/data

# Load data into MongoDB
python3 database/load_mongodb.py
```

## Expected Row Counts in Databases

### MySQL Tables:
- `rainfall`: 6,727 rows
- `temperature`: 71,311 rows
- `pesticides`: 4,349 rows
- `crop_yield`: 56,717 rows
- **Total**: ~139,104 rows

### MongoDB Collections:
- `rainfall`: 6,727 documents
- `temperature`: 71,311 documents
- `pesticides`: 4,349 documents
- `crop_yield`: 56,717 documents
- **Total**: ~139,104 documents

## Verification

### Verify MySQL Data:
```sql
USE agriculture_db;
SELECT * FROM data_summary;
```

### Verify MongoDB Data:
```javascript
use agriculture_db
db.rainfall.countDocuments({})
db.temperature.countDocuments({})
db.pesticides.countDocuments({})
db.crop_yield.countDocuments({})
```

## Notes

- CSV headers are excluded when counting rows
- Some temperature data has missing values
- Data spans from 1849 to 2017
- Multiple countries and crop types included
