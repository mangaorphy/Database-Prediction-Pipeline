# 🚀 QUICK START - Which Files to Run

## Step-by-Step Instructions

### ✅ STEP 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### ✅ STEP 2: Configure Database Credentials
```bash
cp .env.example .env
# Edit .env file with your MySQL and MongoDB credentials
```

### ✅ STEP 3: Setup MySQL
```bash
# Create the database
mysql -u root -p -e "CREATE DATABASE agriculture_db;"

# Load the schema (includes stored procedures & triggers)
mysql -u root -p agriculture_db < database/mysql_schema.sql

# Load the data (~139K rows, takes 2-3 minutes)
python3 database/load_mysql.py
```

### ✅ STEP 4: Setup MongoDB
```bash
# Load the data
python3 database/load_mongodb.py
```

### ✅ STEP 5: Test Everything Works
```bash
python3 test_setup.py
```

---

## 📂 Files Explained Simply

### ✅ Files You RUN:
| File | What It Does | When to Run |
|------|-------------|-------------|
| `database/load_mysql.py` | Loads CSV data into MySQL | Step 3 |
| `database/load_mongodb.py` | Loads CSV data into MongoDB | Step 4 |
| `test_setup.py` | Tests if setup worked | Step 5 |

### ⚙️ Files You CONFIGURE:
| File | What It Does |
|------|-------------|
| `.env` | Database passwords & connection strings |
| `requirements.txt` | List of Python packages needed |

### 📄 Files You DON'T Run (Reference Only):
| File | What It Does |
|------|-------------|
| `database/mysql_schema.sql` | MySQL schema definition (loaded via mysql command) |
| `README.md` | Full documentation |
| `QUICKSTART.md` | Alternative guide |

### 🔧 Optional Files:
| File | What It Does | When to Use |
|------|-------------|-------------|
| `database/reset_mysql.py` | Deletes all MySQL data | If you need to start over |
| `setup.sh` | Automated setup script | Alternative to manual steps |

---

## 🎯 Assignment Features Included

### MySQL:
- ✅ 2 Stored Procedures (`validate_agriculture_data`, `get_agriculture_stats`)
- ✅ 3 Triggers (data validation, audit logging)
- ✅ 3NF Schema with proper data types
- ✅ Primary keys and indexes

### MongoDB:
- ✅ Document-based schema
- ✅ Relationship modeling via common fields
- ✅ Compound indexes for performance

---

## 🆘 Having Issues?

**"Connection refused"** → Make sure MySQL/MongoDB is running  
**"Module not found"** → Run `pip install -r requirements.txt`  
**"Access denied"** → Check `.env` file has correct passwords  
**"Table already exists"** → Run `python3 database/reset_mysql.py`  

---

## ✅ Done!

Once all steps complete successfully:
- MySQL will have ~139K rows across 4 tables
- MongoDB will have ~139K documents across 4 collections
- You can test stored procedures and triggers
- Everything is ready for your machine learning pipeline

**Need more details?** See `README.md`
