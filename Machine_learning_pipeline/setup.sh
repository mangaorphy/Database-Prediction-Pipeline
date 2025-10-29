#!/bin/bash
# Setup script for Agriculture Database Setup

echo "=================================="
echo "Agriculture Database Setup"
echo "=================================="

# Check Python version
echo ""
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment file
echo ""
echo "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file. Please edit it with your database credentials."
else
    echo "✓ .env file already exists"
fi

echo ""
echo "=================================="
echo "Setup completed successfully!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your database credentials"
echo "2. Setup MySQL database:"
echo "   mysql -u root -p -e 'CREATE DATABASE agriculture_db;'"
echo "   mysql -u root -p agriculture_db < database/mysql_schema.sql"
echo "3. Load data into MySQL:"
echo "   python3 database/load_mysql.py"
echo "4. Load data into MongoDB:"
echo "   python3 database/load_mongodb.py"
echo ""
