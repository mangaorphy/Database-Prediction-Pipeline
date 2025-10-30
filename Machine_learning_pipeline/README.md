```markdown
# Agriculture Database Setup

A database setup project for agricultural data with MySQL and MongoDB integration.

## 📊 Data Overview

| File | Rows | Description |
|------|------|-------------|
| rainfall.csv | 6,728 | Rainfall data by area and year |
| temp.csv | 71,312 | Temperature data by country and year |
| pesticides.csv | 4,350 | Pesticide usage data |
| yield.csv | 56,718 | Crop yield data |
| **Total** | **~139,000** | Total rows across all datasets |

## 📁 Project Structure

```
Machine_learning_pipeline/
├── README.md                    ← YOU ARE HERE (Read this!)
├── QUICKSTART.md                ← Quick setup guide
├── requirements.txt             ← Python dependencies
├── setup.sh                     ← Automated setup script
├── test_setup.py                ← Test if everything works
├── config/
│   └── database.py              ← Database connection config
├── database/
│   ├── mysql_schema.sql         ← MySQL schema (with procedures & triggers)
│   ├── load_mysql.py            ← RUN THIS to load MySQL data
│   ├── load_mongodb.py          ← RUN THIS to load MongoDB data
│   └── reset_mysql.py           ← RUN THIS to reset MySQL database
└── data/                        ← CSV files location
    ├── rainfall.csv
    ├── temp.csv
    ├── pesticides.csv
    └── yield.csv
```

## 🚀 FILES TO RUN (In Order)

### Step 1: Setup Environment
```bash
# Option A: Automated setup (recommended)
bash setup.sh

# Option B: Manual setup
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database credentials
```

### Step 2: Setup MySQL Database
```bash
# Create database
mysql -u root -p -e "CREATE DATABASE agriculture_db;"

# Load schema (includes stored procedures & triggers)
mysql -u root -p agriculture_db < database/mysql_schema.sql

# Load data (this will take a few minutes for ~139k rows)
python3 database/load_mysql.py
```

### Step 3: Setup MongoDB
```bash
# Make sure MongoDB is running first
# Load data into MongoDB
python3 database/load_mongodb.py
```

### Step 4: Verify Setup
```bash
python3 test_setup.py
```

## 🎯 Important Files Explained

### Files You NEED to Run:
1. **`database/load_mysql.py`** - Loads CSV data into MySQL
2. **`database/load_mongodb.py`** - Loads CSV data into MongoDB
3. **`test_setup.py`** - Verifies everything is working

### Files You NEED to Configure:
1. **`.env`** - Database credentials (copy from .env.example)
2. **`config/database.py`** - Database connection settings (uses .env)

### Files You DON'T Run Directly:
1. **`database/mysql_schema.sql`** - Schema file (loaded via mysql command)
2. **`requirements.txt`** - Dependency list (installed via pip)
3. **`setup.sh`** - Optional automated setup script

### Optional Files:
1. **`database/reset_mysql.py`** - Use if you need to reset MySQL database
2. **`QUICKSTART.md`** - Alternative quick start guide

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

## 📝 Notes

- CSV headers are excluded when counting rows
- Some temperature data has missing values
- Data spans from 1849 to 2017
- Multiple countries and crop types included

## 🎓 Assignment Requirements Implemented

### MySQL Features:
✅ **3NF Schema** - All tables follow Third Normal Form  
✅ **Data Types** - INT, DECIMAL, VARCHAR, TIMESTAMP defined  
✅ **Primary Keys** - All tables have AUTO_INCREMENT id  
✅ **Stored Procedures** - 2 procedures for validation & statistics  
✅ **Triggers** - 3 triggers for data validation & audit logging  

### MongoDB Features:
✅ **Document Schema** - Collections with proper structure  
✅ **Relationships** - Modeled via common fields & aggregation  
✅ **Indexes** - Compound indexes for efficient queries  

### Test the Features:
```sql
-- Test Stored Procedures
CALL validate_agriculture_data();
CALL get_agriculture_stats('India', 2010, 2015);

-- Test Triggers (validation)
INSERT INTO rainfall (area, year, average_rain_fall_mm_per_year) 
VALUES ('Test', 2020, -100);  -- Should FAIL

-- Test Triggers (audit logging)
UPDATE crop_yield SET value = 999 WHERE id = 1;
SELECT * FROM data_audit_log ORDER BY changed_at DESC LIMIT 5;
```

## 👥 Team Collaboration Setup

#### Person 1 (Setup Lead):
```bash
# 1. Create MongoDB Atlas cluster (free)
# 2. Get connection string
# 3. Update .env with MONGO_URI
# 4. Load data to MongoDB Atlas
python3 database/load_mongodb.py

# 5. Setup local MySQL
mysql -u root -p -e "CREATE DATABASE agriculture_db;"
mysql -u root -p agriculture_db < database/mysql_schema.sql
python3 database/load_mysql.py

# 6. Export MySQL data
mysqldump -u root -p agriculture_db > agriculture_backup.sql

# 7. Share with team:
#    - MongoDB Atlas connection string (MONGO_URI)
#    - MySQL backup file (agriculture_backup.sql)
```

#### Other Team Members:
```bash
# 1. Clone the project
git clone <your-repo>
cd Machine_learning_pipeline

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file with shared MongoDB Atlas connection
cp .env.example .env
# Edit .env and add the MONGO_URI from Person 1

# 4. Setup local MySQL
mysql -u root -p -e "CREATE DATABASE agriculture_db;"
mysql -u root -p agriculture_db < database/mysql_schema.sql
mysql -u root -p agriculture_db < agriculture_backup.sql

# 5. Verify setup
python3 test_setup.py