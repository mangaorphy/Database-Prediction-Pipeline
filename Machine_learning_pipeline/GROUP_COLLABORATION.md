# Group Collaboration Guide

## Problem: Localhost Databases Not Accessible by Group Members

When using `localhost`, databases are only accessible on YOUR computer. Even with credentials, your group members **cannot connect** remotely.

---

## ✅ Solution 1: MongoDB Atlas (FREE & RECOMMENDED)

### Setup Steps:

#### 1. Create MongoDB Atlas Account (One Person)
```
1. Go to: https://www.mongodb.com/cloud/atlas
2. Sign up (free, no credit card required)
3. Create a new cluster (select FREE tier)
4. Wait 3-5 minutes for cluster to deploy
```

#### 2. Configure Database Access
```
1. In Atlas dashboard: Database Access → Add New Database User
2. Create username/password (save these!)
3. Set privileges to "Read and write to any database"
```

#### 3. Configure Network Access
```
1. In Atlas dashboard: Network Access → Add IP Address
2. Click "Allow Access from Anywhere" (for development)
   - This adds 0.0.0.0/0 (all IPs)
   - ⚠️ For production, restrict to specific IPs
```

#### 4. Get Connection String
```
1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Copy the connection string (looks like):
   mongodb+srv://username:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

#### 5. Update Your .env File
```bash
# Replace with your actual connection string
MONGO_URI=url_mongodb_connection_string_here

# Keep MySQL as localhost (each person has their own)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_local_password
MYSQL_DATABASE=agriculture_db
```

#### 6. Share Credentials with Group
Share the `.env` file (or just the MONGO_URI) with your group members via:
- Encrypted message
- Shared password manager
- Private GitHub repository (with .env in .gitignore but share separately)

#### 7. Each Person Loads Data
```bash
# Everyone runs this on their own computer
python3 database/load_mongodb.py
```

### ✅ Benefits:
- ✓ Free tier (512MB)
- ✓ Everyone can access the same database
- ✓ No firewall/network configuration needed
- ✓ Automatic backups
- ✓ Works from anywhere

---

## ✅ Solution 2: MySQL Cloud (If Needed)

For MySQL, you have options:

### Option A: PlanetScale (FREE)
```
1. Go to: https://planetscale.com
2. Sign up (free tier available)
3. Create database
4. Get connection string
5. Update .env:
   MYSQL_HOST=your-db.psdb.cloud
   MYSQL_PORT=3306
   MYSQL_USER=your_username
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=agriculture_db
```

### Option B: Railway.app (Simple)
```
1. Go to: https://railway.app
2. Sign up with GitHub
3. Create new project → Add MySQL
4. Copy connection details
5. Update .env with provided credentials
```

### Option C: Each Person Uses Local MySQL
```
1. One person loads data and exports:
   mysqldump -u root -p agriculture_db > agriculture_backup.sql

2. Share the agriculture_backup.sql file (via Google Drive, Dropbox, etc.)

3. Each person imports:
   mysql -u root -p agriculture_db < agriculture_backup.sql
```

---

## ✅ Solution 3: Hybrid Approach (RECOMMENDED FOR YOUR PROJECT)

**Best practice for group projects:**

### MongoDB: Use Atlas (Cloud)
- All group members connect to same MongoDB Atlas instance
- Everyone sees the same data in real-time
- No sync issues

### MySQL: Local + Export/Import
- Each person has their own local MySQL
- One person exports and shares the backup file
- Everyone imports the same data locally

### Why This Works:
- ✓ MongoDB Atlas is free and easy
- ✓ MySQL local is faster for development
- ✓ No complex networking required
- ✓ Good balance of convenience and simplicity

---

## 🔒 Security Best Practices

### For Cloud Databases:

1. **Use Strong Passwords**
   ```
   ✓ At least 16 characters
   ✓ Mix of letters, numbers, symbols
   ✓ Use password generator
   ```

2. **Restrict IP Access (Production)**
   ```
   # In Atlas Network Access, add only team IPs instead of 0.0.0.0/0
   203.0.113.0/24  (your team's network)
   ```

3. **Don't Commit Credentials to Git**
   ```bash
   # Ensure .env is in .gitignore
   echo ".env" >> .gitignore
   git add .gitignore
   git commit -m "Ensure .env is ignored"
   ```

4. **Use Environment Variables**
   ```bash
   # Never hardcode credentials in your code
   # Always use os.getenv()
   ```

5. **Rotate Credentials Periodically**
   ```
   Change passwords every few months
   Especially after a team member leaves
   ```

---

## 📝 Example Setup for Your Group

### Step-by-Step (Recommended):

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
cd archive

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
```

---

## 🆘 Troubleshooting

### "Can't connect to MongoDB Atlas"
```bash
# Check:
1. Is your IP whitelisted? (0.0.0.0/0 for development)
2. Is the password correct in connection string?
3. Did you replace <password> with actual password?
4. Is your internet connection working?
```

### "MySQL connection refused"
```bash
# Check:
1. Is MySQL running? (mysql -u root -p)
2. Are credentials correct in .env?
3. Does database exist? (SHOW DATABASES;)
```

### "pymongo not installed"
```bash
pip install -r requirements.txt
```

---

## 📊 Summary

| Approach | MongoDB | MySQL | Complexity | Cost |
|----------|---------|-------|------------|------|
| **Recommended** | Atlas (Cloud) | Local | Low | Free |
| Full Cloud | Atlas | PlanetScale | Low | Free |
| Local Only | Local | Local | Medium | Free |
| Network Sharing | Local | Local | High | Free |

**For your group project: Use MongoDB Atlas + Local MySQL** ✅

This gives you the best balance of:
- Easy collaboration (MongoDB in cloud)
- Fast local development (MySQL local)
- No cost (both free)
- Simple setup

---

## 🎯 Final Recommendation

1. **One person** creates MongoDB Atlas cluster
2. **Share the MONGO_URI** with all group members
3. **Everyone** uses local MySQL (import backup file)
4. **Update .env** on each person's computer with their own settings

This way:
- ✓ No localhost access issues
- ✓ Everyone works with the same data
- ✓ Simple and free
- ✓ No complex networking needed
