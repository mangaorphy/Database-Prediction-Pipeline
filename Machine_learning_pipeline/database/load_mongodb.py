"""
Load CSV data into MongoDB database.
Expected documents: ~139,000 total
- rainfall: 6,727
- temperature: 71,311
- pesticides: 4,349
- crop_yield: 56,717
"""
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))
from config.database import get_mongodb


def load_csv_to_mongodb(csv_file, collection_name, db, chunk_size=1000):
    """Load CSV data into MongoDB collection in chunks."""
    print(f"\n{'='*60}")
    print(f"Loading {csv_file} into {collection_name}...")
    print(f"{'='*60}")
    
    start_time = datetime.now()
    
    # Get or create collection
    collection = db[collection_name]
    
    # Clear existing data (optional - comment out to append)
    # collection.delete_many({})
    
    total_docs = 0
    
    # Read CSV in chunks
    for i, chunk in enumerate(pd.read_csv(csv_file, chunksize=chunk_size)):
        # Strip whitespace from column names
        chunk.columns = chunk.columns.str.strip()
        
        # Convert DataFrame to list of dictionaries
        # Replace NaN with None
        records = chunk.where(pd.notnull(chunk), None).to_dict('records')
        
        # Add metadata
        for record in records:
            record['_loaded_at'] = datetime.now()
        
        # Insert documents
        try:
            result = collection.insert_many(records, ordered=False)
            total_docs += len(result.inserted_ids)
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Processed {total_docs:,} documents...", end='\r')
                
        except Exception as e:
            print(f"\n  Error inserting chunk {i}: {e}")
    
    # Create indexes for better query performance
    create_indexes(collection, collection_name)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n✓ Loaded {total_docs:,} documents in {duration:.2f} seconds")
    print(f"  Rate: {total_docs/duration:.0f} docs/second\n")
    
    return total_docs


def create_indexes(collection, collection_name):
    """Create indexes for efficient querying."""
    print(f"  Creating indexes for {collection_name}...")
    
    try:
        if collection_name == 'rainfall':
            collection.create_index([('area', 1)])
            collection.create_index([('year', 1)])
            collection.create_index([('area', 1), ('year', 1)])
            
        elif collection_name == 'temperature':
            collection.create_index([('country', 1)])
            collection.create_index([('year', 1)])
            collection.create_index([('country', 1), ('year', 1)])
            
        elif collection_name == 'pesticides':
            collection.create_index([('area', 1)])
            collection.create_index([('year', 1)])
            collection.create_index([('area', 1), ('year', 1)])
            
        elif collection_name == 'crop_yield':
            collection.create_index([('area', 1)])
            collection.create_index([('year', 1)])
            collection.create_index([('item', 1)])
            collection.create_index([('area', 1), ('year', 1), ('item', 1)])
        
        print(f"  ✓ Indexes created")
    
    except Exception as e:
        print(f"  ⚠ Index creation warning: {e}")


def verify_data_load(db):
    """Verify loaded data counts."""
    print(f"\n{'='*60}")
    print("VERIFICATION: Checking document counts...")
    print(f"{'='*60}\n")
    
    collections = ['rainfall', 'temperature', 'pesticides', 'crop_yield']
    
    total = 0
    stats = []
    
    for coll_name in collections:
        collection = db[coll_name]
        count = collection.count_documents({})
        total += count
        
        print(f"  {coll_name:15s}: {count:>7,} documents")
        
        # Get year range and unique areas
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'min_year': {'$min': '$year' if coll_name != 'temperature' else '$year'},
                    'max_year': {'$max': '$year' if coll_name != 'temperature' else '$year'},
                    'unique_areas': {
                        '$addToSet': '$area' if coll_name != 'temperature' else '$country'
                    }
                }
            }
        ]
        
        result = list(collection.aggregate(pipeline))
        if result:
            unique_count = len(result[0].get('unique_areas', []))
            min_year = result[0].get('min_year', 'N/A')
            max_year = result[0].get('max_year', 'N/A')
            stats.append((coll_name, count, min_year, max_year, unique_count))
    
    print(f"  {'-'*25}")
    print(f"  {'TOTAL':15s}: {total:>7,} documents\n")
    
    # Show data summary
    print(f"{'='*60}")
    print("DATA SUMMARY:")
    print(f"{'='*60}")
    print(f"{'Collection':<15} {'Docs':>10} {'Min Year':>10} {'Max Year':>10} {'Areas':>10}")
    print(f"{'-'*60}")
    
    for stat in stats:
        print(f"{stat[0]:<15} {stat[1]:>10,} {stat[2]:>10} {stat[3]:>10} {stat[4]:>10}")
    
    print(f"{'='*60}\n")


def main():
    """Main function to load all CSV files into MongoDB."""
    print(f"\n{'#'*60}")
    print("# MongoDB Data Loading Script")
    print("# Database: agriculture_db")
    print("# Expected Total: ~139,000 documents")
    print(f"{'#'*60}\n")
    
    # Base path for CSV files
    base_path = Path(__file__).parent.parent
    
    # CSV to collection mapping
    csv_mappings = [
        ('rainfall.csv', 'rainfall'),
        ('temp.csv', 'temperature'),
        ('pesticides.csv', 'pesticides'),
        ('yield.csv', 'crop_yield')
    ]
    
    try:
        # Connect to MongoDB
        print("Connecting to MongoDB...")
        db = get_mongodb()
        print(f"✓ Connected to database: {db.name}\n")
        
        # Load each CSV file
        total_start = datetime.now()
        
        for csv_file, collection_name in csv_mappings:
            csv_path = base_path / csv_file
            
            if not csv_path.exists():
                print(f"⚠ Warning: {csv_file} not found, skipping...")
                continue
            
            load_csv_to_mongodb(csv_path, collection_name, db)
        
        total_end = datetime.now()
        total_duration = (total_end - total_start).total_seconds()
        
        # Verify the loaded data
        verify_data_load(db)
        
        print(f"{'='*60}")
        print(f"✓ ALL DATA LOADED SUCCESSFULLY!")
        print(f"  Total time: {total_duration:.2f} seconds")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
