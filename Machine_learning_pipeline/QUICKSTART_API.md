# FastAPI CRUD API - Quick Start Guide

## Prerequisites

- Python 3.8+
- MySQL Server running
- Git (optional)

## Installation & Startup (5 minutes)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure Database

Create or edit `.env` file in the project root:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=agriculture_db
```

### Step 3: Setup Database (if not already done)

```bash
python database/load_mysql.py
```

### Step 4: Start the API Server

```bash
python main.py
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## Access the API

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Root

- http://localhost:8000/

---

## Quick API Examples

### 1. Check Health

```bash
curl http://localhost:8000/health
```

### 2. Create Rainfall Data

```bash
curl -X POST http://localhost:8000/rainfall \
  -H "Content-Type: application/json" \
  -d '{
    "area": "North India",
    "year": 2020,
    "average_rain_fall_mm_per_year": 1200.5
  }'
```

### 3. Get All Rainfall Data

```bash
curl http://localhost:8000/rainfall?limit=10
```

### 4. Get Specific Record

```bash
curl http://localhost:8000/rainfall/1
```

### 5. Update Record

```bash
curl -X PUT http://localhost:8000/rainfall/1 \
  -H "Content-Type: application/json" \
  -d '{"average_rain_fall_mm_per_year": 1300.0}'
```

### 6. Delete Record

```bash
curl -X DELETE http://localhost:8000/rainfall/1
```

---

## Available Endpoints Summary

### Rainfall

- `POST /rainfall` - Create
- `GET /rainfall` - Read (list)
- `GET /rainfall/{id}` - Read (by ID)
- `PUT /rainfall/{id}` - Update
- `DELETE /rainfall/{id}` - Delete

### Temperature

- `POST /temperature` - Create
- `GET /temperature` - Read (list)
- `GET /temperature/{id}` - Read (by ID)
- `PUT /temperature/{id}` - Update
- `DELETE /temperature/{id}` - Delete

### Pesticides

- `POST /pesticides` - Create
- `GET /pesticides` - Read (list)
- `GET /pesticides/{id}` - Read (by ID)
- `PUT /pesticides/{id}` - Update
- `DELETE /pesticides/{id}` - Delete

### Crop Yield

- `POST /crop-yield` - Create
- `GET /crop-yield` - Read (list)
- `GET /crop-yield/{id}` - Read (by ID)
- `PUT /crop-yield/{id}` - Update
- `DELETE /crop-yield/{id}` - Delete

---

## Running Tests

### Test Script (Python)

```bash
python test_api.py
```

This will test all CRUD operations on all endpoints.

### Manual Testing with Python

```python
import requests

# Create
response = requests.post("http://localhost:8000/rainfall", json={
    "area": "Test",
    "year": 2023,
    "average_rain_fall_mm_per_year": 1000
})
print(response.json())  # {'id': 1, 'area': 'Test', ...}

# Read
response = requests.get("http://localhost:8000/rainfall/1")
print(response.json())

# Update
response = requests.put("http://localhost:8000/rainfall/1", json={
    "average_rain_fall_mm_per_year": 1100
})
print(response.json())

# Delete
response = requests.delete("http://localhost:8000/rainfall/1")
print(response.status_code)  # 204
```

---

## Troubleshooting

### "Connection refused" Error

- Make sure MySQL is running
- Check `.env` credentials
- Verify `MYSQL_HOST` and `MYSQL_PORT`

### "Database not found" Error

- Run: `python database/load_mysql.py`
- Or manually create database: `mysql -u root -p -e "CREATE DATABASE agriculture_db;"`

### "Module not found" Error

- Run: `pip install -r requirements.txt`
- Ensure you're in the correct virtual environment

### Port 8000 Already in Use

```bash
# Use a different port
uvicorn main:app --port 8001
```

---

## Database Schema

### Tables

1. **rainfall** - Rainfall data by area and year
2. **temperature** - Temperature data by country and year
3. **pesticides** - Pesticide usage by area and year
4. **crop_yield** - Crop yield data by area, crop, and year

See `database/mysql_schema.sql` for full schema details.

---

## Response Status Codes

| Code | Meaning              |
| ---- | -------------------- |
| 200  | Success (GET/PUT)    |
| 201  | Created (POST)       |
| 204  | Deleted (DELETE)     |
| 400  | Bad Request          |
| 404  | Not Found            |
| 500  | Server Error         |
| 503  | Database Unavailable |

---

## File Structure

```
Machine_learning_pipeline/
├── main.py                    # Main FastAPI application
├── test_api.py               # API test script
├── schemas.py                # Pydantic models (optional)
├── models.py                 # SQLAlchemy models (optional)
├── API_DOCUMENTATION.md      # Detailed API docs
├── QUICKSTART.md             # This file
├── requirements.txt          # Dependencies
├── config/
│   └── database.py          # Database config
└── database/
    └── mysql_schema.sql     # Database schema
```

---

## Next Steps

1. ✅ Start the server: `python main.py`
2. ✅ Visit API docs: http://localhost:8000/docs
3. ✅ Test endpoints using Swagger UI or curl
4. ✅ Run test suite: `python test_api.py`
5. ✅ Read full docs: `API_DOCUMENTATION.md`

---

## Support

For detailed API documentation, visit:

- `/docs` - Swagger UI (interactive)
- `/redoc` - ReDoc (read-only)
- `API_DOCUMENTATION.md` - Full documentation

---

## Environment Variables

Create `.env` file:

```env
# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=agriculture_db
```

---

## Performance Tips

1. Use `limit` parameter (max 100) to avoid loading too much data
2. Use `skip` parameter for pagination
3. Filter by specific fields (area, year, item) to reduce results
4. Indexes are set up on common filter fields

Example:

```bash
# Good - paginated and filtered
curl "http://localhost:8000/rainfall?area=India&year=2020&skip=0&limit=20"

# Avoid - all data at once
curl "http://localhost:8000/rainfall"
```

---

**Happy Testing! 🚀**
