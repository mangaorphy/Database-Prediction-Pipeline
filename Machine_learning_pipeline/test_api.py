"""
Test script for FastAPI CRUD endpoints.
Run this script to test all CRUD operations.
"""

import requests
import json
from typing import Dict, Any

# Base URL
BASE_URL = "http://localhost:8000"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{YELLOW}ℹ {text}{RESET}")


def print_response(response: requests.Response):
    """Print formatted response."""
    try:
        print(json.dumps(response.json(), indent=2, default=str))
    except:
        print(response.text)


# =====================
# RAINFALL TESTS
# =====================

def test_rainfall_crud():
    """Test Rainfall CRUD operations."""
    print_header("TESTING RAINFALL ENDPOINTS")
    
    # CREATE
    print_info("Creating rainfall record...")
    rainfall_data = {
        "area": "Test Area",
        "year": 2023,
        "average_rain_fall_mm_per_year": 1234.5
    }
    response = requests.post(f"{BASE_URL}/rainfall", json=rainfall_data)
    
    if response.status_code == 201:
        print_success(f"Created rainfall record")
        rainfall_id = response.json()["id"]
        print_response(response)
    else:
        print_error(f"Failed to create rainfall record: {response.status_code}")
        print_response(response)
        return
    
    # READ (by ID)
    print_info(f"\nReading rainfall record (ID: {rainfall_id})...")
    response = requests.get(f"{BASE_URL}/rainfall/{rainfall_id}")
    
    if response.status_code == 200:
        print_success("Retrieved rainfall record")
        print_response(response)
    else:
        print_error(f"Failed to retrieve rainfall record: {response.status_code}")
        return
    
    # READ (list with filters)
    print_info("\nReading rainfall records with filters...")
    response = requests.get(f"{BASE_URL}/rainfall", params={"area": "Test", "limit": 10})
    
    if response.status_code == 200:
        print_success(f"Retrieved {len(response.json())} rainfall records")
        print_response(response)
    else:
        print_error(f"Failed to retrieve rainfall records: {response.status_code}")
    
    # UPDATE
    print_info(f"\nUpdating rainfall record (ID: {rainfall_id})...")
    update_data = {
        "average_rain_fall_mm_per_year": 1500.0
    }
    response = requests.put(f"{BASE_URL}/rainfall/{rainfall_id}", json=update_data)
    
    if response.status_code == 200:
        print_success("Updated rainfall record")
        print_response(response)
    else:
        print_error(f"Failed to update rainfall record: {response.status_code}")
        print_response(response)
    
    # DELETE
    print_info(f"\nDeleting rainfall record (ID: {rainfall_id})...")
    response = requests.delete(f"{BASE_URL}/rainfall/{rainfall_id}")
    
    if response.status_code == 204:
        print_success("Deleted rainfall record")
    else:
        print_error(f"Failed to delete rainfall record: {response.status_code}")


# =====================
# TEMPERATURE TESTS
# =====================

def test_temperature_crud():
    """Test Temperature CRUD operations."""
    print_header("TESTING TEMPERATURE ENDPOINTS")
    
    # CREATE
    print_info("Creating temperature record...")
    temp_data = {
        "year": 2023,
        "country": "Test Country",
        "avg_temp": 25.5
    }
    response = requests.post(f"{BASE_URL}/temperature", json=temp_data)
    
    if response.status_code == 201:
        print_success("Created temperature record")
        temp_id = response.json()["id"]
        print_response(response)
    else:
        print_error(f"Failed to create temperature record: {response.status_code}")
        print_response(response)
        return
    
    # READ (by ID)
    print_info(f"\nReading temperature record (ID: {temp_id})...")
    response = requests.get(f"{BASE_URL}/temperature/{temp_id}")
    
    if response.status_code == 200:
        print_success("Retrieved temperature record")
        print_response(response)
    else:
        print_error(f"Failed to retrieve temperature record: {response.status_code}")
    
    # READ (list)
    print_info("\nReading temperature records...")
    response = requests.get(f"{BASE_URL}/temperature", params={"limit": 10})
    
    if response.status_code == 200:
        print_success(f"Retrieved {len(response.json())} temperature records")
    else:
        print_error(f"Failed to retrieve temperature records: {response.status_code}")
    
    # UPDATE
    print_info(f"\nUpdating temperature record (ID: {temp_id})...")
    update_data = {"avg_temp": 26.8}
    response = requests.put(f"{BASE_URL}/temperature/{temp_id}", json=update_data)
    
    if response.status_code == 200:
        print_success("Updated temperature record")
        print_response(response)
    else:
        print_error(f"Failed to update temperature record: {response.status_code}")
    
    # DELETE
    print_info(f"\nDeleting temperature record (ID: {temp_id})...")
    response = requests.delete(f"{BASE_URL}/temperature/{temp_id}")
    
    if response.status_code == 204:
        print_success("Deleted temperature record")
    else:
        print_error(f"Failed to delete temperature record: {response.status_code}")


# =====================
# PESTICIDES TESTS
# =====================

def test_pesticides_crud():
    """Test Pesticides CRUD operations."""
    print_header("TESTING PESTICIDES ENDPOINTS")
    
    # CREATE
    print_info("Creating pesticides record...")
    pest_data = {
        "domain": "Agriculture",
        "area": "Test Area",
        "element": "Insecticide",
        "item": "Pesticide A",
        "year": 2023,
        "unit": "kg/ha",
        "value": 5.5
    }
    response = requests.post(f"{BASE_URL}/pesticides", json=pest_data)
    
    if response.status_code == 201:
        print_success("Created pesticides record")
        pest_id = response.json()["id"]
        print_response(response)
    else:
        print_error(f"Failed to create pesticides record: {response.status_code}")
        print_response(response)
        return
    
    # READ (by ID)
    print_info(f"\nReading pesticides record (ID: {pest_id})...")
    response = requests.get(f"{BASE_URL}/pesticides/{pest_id}")
    
    if response.status_code == 200:
        print_success("Retrieved pesticides record")
        print_response(response)
    else:
        print_error(f"Failed to retrieve pesticides record: {response.status_code}")
    
    # UPDATE
    print_info(f"\nUpdating pesticides record (ID: {pest_id})...")
    update_data = {"value": 6.0}
    response = requests.put(f"{BASE_URL}/pesticides/{pest_id}", json=update_data)
    
    if response.status_code == 200:
        print_success("Updated pesticides record")
        print_response(response)
    else:
        print_error(f"Failed to update pesticides record: {response.status_code}")
    
    # DELETE
    print_info(f"\nDeleting pesticides record (ID: {pest_id})...")
    response = requests.delete(f"{BASE_URL}/pesticides/{pest_id}")
    
    if response.status_code == 204:
        print_success("Deleted pesticides record")
    else:
        print_error(f"Failed to delete pesticides record: {response.status_code}")


# =====================
# CROP YIELD TESTS
# =====================

def test_crop_yield_crud():
    """Test Crop Yield CRUD operations."""
    print_header("TESTING CROP YIELD ENDPOINTS")
    
    # CREATE
    print_info("Creating crop yield record...")
    yield_data = {
        "area": "Test Area",
        "item": "Test Crop",
        "year": 2023,
        "value": 5.2,
        "unit": "tonnes/ha"
    }
    response = requests.post(f"{BASE_URL}/crop-yield", json=yield_data)
    
    if response.status_code == 201:
        print_success("Created crop yield record")
        yield_id = response.json()["id"]
        print_response(response)
    else:
        print_error(f"Failed to create crop yield record: {response.status_code}")
        print_response(response)
        return
    
    # READ (by ID)
    print_info(f"\nReading crop yield record (ID: {yield_id})...")
    response = requests.get(f"{BASE_URL}/crop-yield/{yield_id}")
    
    if response.status_code == 200:
        print_success("Retrieved crop yield record")
        print_response(response)
    else:
        print_error(f"Failed to retrieve crop yield record: {response.status_code}")
    
    # UPDATE
    print_info(f"\nUpdating crop yield record (ID: {yield_id})...")
    update_data = {"value": 5.5}
    response = requests.put(f"{BASE_URL}/crop-yield/{yield_id}", json=update_data)
    
    if response.status_code == 200:
        print_success("Updated crop yield record")
        print_response(response)
    else:
        print_error(f"Failed to update crop yield record: {response.status_code}")
    
    # DELETE
    print_info(f"\nDeleting crop yield record (ID: {yield_id})...")
    response = requests.delete(f"{BASE_URL}/crop-yield/{yield_id}")
    
    if response.status_code == 204:
        print_success("Deleted crop yield record")
    else:
        print_error(f"Failed to delete crop yield record: {response.status_code}")


# =====================
# HEALTH CHECK
# =====================

def test_health_check():
    """Test health check endpoint."""
    print_header("TESTING HEALTH CHECK")
    
    print_info("Checking API health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            print_success("API is healthy")
            print_response(response)
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print_response(response)
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API. Make sure the server is running at http://localhost:8000")
    except Exception as e:
        print_error(f"Error: {str(e)}")


# =====================
# MAIN
# =====================

if __name__ == "__main__":
    print(f"\n{YELLOW}{'='*60}")
    print("Agricultural Database API - CRUD Test Suite")
    print(f"{'='*60}{RESET}")
    
    try:
        # Test health
        test_health_check()
        
        # Test CRUD operations
        test_rainfall_crud()
        test_temperature_crud()
        test_pesticides_crud()
        test_crop_yield_crud()
        
        print_header("ALL TESTS COMPLETED")
        print_success("Test suite finished successfully!")
        
    except Exception as e:
        print_error(f"Test suite failed with error: {str(e)}")
