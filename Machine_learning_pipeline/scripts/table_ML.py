import pandas as pd
import numpy as np
import os
import logging
from typing import Dict, List, Optional
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# --- Setup logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        
    def validate_environment(self) -> bool:
        """Check if data directory exists and we have required files."""
        try:
            if not os.path.exists(self.data_dir):
                logger.error(f"Data directory '{self.data_dir}' does not exist")
                return False
            
            required_files = ["rainfall.csv", "temp.csv", "pesticides.csv", "yield.csv"]
            missing_files = []
            
            for file in required_files:
                file_path = os.path.join(self.data_dir, file)
                if not os.path.exists(file_path):
                    missing_files.append(file)
            
            if missing_files:
                logger.error(f"Missing required files: {missing_files}")
                return False
                
            logger.info("All required files found")
            return True
            
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            return False

    def load_and_process_rainfall(self) -> Optional[pd.DataFrame]:
        """Load and process rainfall data."""
        try:
            file_path = os.path.join(self.data_dir, "rainfall.csv")
            df = pd.read_csv(file_path)
            
            # Rename columns to match your actual data
            df = df.rename(columns={
                ' Area': 'area',
                'Year': 'year', 
                'average_rain_fall_mm_per_year': 'rainfall'
            })
            
            # Convert rainfall to numeric (handle any non-numeric values)
            df['rainfall'] = pd.to_numeric(df['rainfall'], errors='coerce')
            
            # Remove rows with invalid rainfall
            df = df[df['rainfall'] > 0]
            
            logger.info(f"Processed rainfall data: {len(df)} rows")
            return df[['area', 'year', 'rainfall']]
            
        except Exception as e:
            logger.error(f"Failed to process rainfall data: {e}")
            return None

    def load_and_process_temperature(self) -> Optional[pd.DataFrame]:
        """Load and process temperature data."""
        try:
            file_path = os.path.join(self.data_dir, "temp.csv")
            df = pd.read_csv(file_path)
            
            # Rename columns to standardize
            df = df.rename(columns={
                'country': 'area',
                'avg_temp': 'temperature'
            })
            
            # Temperature is already numeric based on your debug output
            # Remove extreme temperature values
            df = df[(df['temperature'] >= -50) & (df['temperature'] <= 60)]
            
            logger.info(f"Processed temperature data: {len(df)} rows")
            return df[['area', 'year', 'temperature']]
            
        except Exception as e:
            logger.error(f"Failed to process temperature data: {e}")
            return None

    def load_and_process_pesticides(self) -> Optional[pd.DataFrame]:
        """Load and process pesticides data."""
        try:
            file_path = os.path.join(self.data_dir, "pesticides.csv")
            df = pd.read_csv(file_path)
            
            # Rename columns and select relevant ones
            df = df.rename(columns={
                'Area': 'area',
                'Year': 'year',
                'Value': 'pesticide_usage'
            })
            
            # Filter for relevant data (total pesticides)
            df = df[df['Item'] == 'Pesticides (total)']
            
            # Remove negative values
            df = df[df['pesticide_usage'] >= 0]
            
            logger.info(f"Processed pesticides data: {len(df)} rows")
            return df[['area', 'year', 'pesticide_usage']]
            
        except Exception as e:
            logger.error(f"Failed to process pesticides data: {e}")
            return None

    def load_and_process_yield(self) -> Optional[pd.DataFrame]:
        """Load and process crop yield data."""
        try:
            file_path = os.path.join(self.data_dir, "yield.csv")
            df = pd.read_csv(file_path)
            
            # Rename columns and select relevant ones
            df = df.rename(columns={
                'Area': 'area',
                'Year': 'year',
                'Item': 'crop_type',
                'Value': 'crop_yield'
            })
            
            # Filter for yield data only (not production)
            df = df[df['Element'] == 'Yield']
            
            # Remove invalid yield values
            df = df[df['crop_yield'] > 0]
            
            logger.info(f"Processed yield data: {len(df)} rows")
            return df[['area', 'year', 'crop_type', 'crop_yield']]
            
        except Exception as e:
            logger.error(f"Failed to process yield data: {e}")
            return None

    def merge_datasets(self, datasets: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        """Merge all datasets on area and year."""
        try:
            if not datasets:
                logger.error("No datasets to merge")
                return None
            
            # Start with yield data as base (since it's our target variable)
            if 'yield' in datasets and not datasets['yield'].empty:
                merged_df = datasets['yield'].copy()
                logger.info(f"Starting with yield data: {len(merged_df)} rows")
            else:
                # If no yield data, start with the first available dataset
                first_key = list(datasets.keys())[0]
                merged_df = datasets[first_key].copy()
                logger.info(f"Starting with {first_key} data: {len(merged_df)} rows")
            
            # Merge other datasets
            for name, df in datasets.items():
                if name == 'yield':  # Skip since we started with it
                    continue
                    
                if df is None or df.empty:
                    logger.warning(f"Skipping empty dataset: {name}")
                    continue
                
                initial_rows = len(merged_df)
                merged_df = merged_df.merge(
                    df, 
                    on=['area', 'year'], 
                    how='left',
                    suffixes=('', f'_{name}')
                )
                
                logger.info(f"Merged {name}: {initial_rows} → {len(merged_df)} rows")
            
            return merged_df
            
        except Exception as e:
            logger.error(f"Error during dataset merging: {e}")
            return None

    def create_final_ml_table(self, merged_df: pd.DataFrame) -> pd.DataFrame:
        """Create final ML-ready table with proper formatting."""
        if merged_df is None or merged_df.empty:
            return merged_df
        
        # Select and order columns for ML
        priority_columns = ['area', 'year', 'crop_type', 'crop_yield', 'rainfall', 'temperature', 'pesticide_usage']
        available_columns = [col for col in priority_columns if col in merged_df.columns]
        
        ml_table = merged_df[available_columns].copy()
        
        # Ensure numeric columns are properly typed
        numeric_columns = ['crop_yield', 'rainfall', 'temperature', 'pesticide_usage']
        for col in numeric_columns:
            if col in ml_table.columns:
                ml_table[col] = pd.to_numeric(ml_table[col], errors='coerce')
        
        # Drop rows where target variable is missing
        if 'crop_yield' in ml_table.columns:
            initial_count = len(ml_table)
            ml_table = ml_table.dropna(subset=['crop_yield'])
            if len(ml_table) < initial_count:
                logger.info(f"Removed {initial_count - len(ml_table)} rows with missing crop_yield")
        
        # Remove duplicate rows
        initial_count = len(ml_table)
        ml_table = ml_table.drop_duplicates()
        if len(ml_table) < initial_count:
            logger.info(f"Removed {initial_count - len(ml_table)} duplicate rows")
        
        return ml_table

    def process_data(self) -> Optional[pd.DataFrame]:
        """Main method to process all data and create ML features table."""
        try:
            logger.info("Starting agricultural data processing...")
            
            # Step 1: Validate environment
            if not self.validate_environment():
                return None
            
            # Step 2: Load and process all datasets
            logger.info("Loading and processing datasets...")
            
            rainfall_df = self.load_and_process_rainfall()
            temperature_df = self.load_and_process_temperature()
            pesticides_df = self.load_and_process_pesticides()
            yield_df = self.load_and_process_yield()
            
            datasets = {
                'rainfall': rainfall_df,
                'temperature': temperature_df,
                'pesticides': pesticides_df,
                'yield': yield_df
            }
            
            # Remove None datasets
            datasets = {k: v for k, v in datasets.items() if v is not None}
            
            if not datasets:
                logger.error(" No valid datasets after processing")
                return None
            
            logger.info(f"Successfully loaded {len(datasets)} datasets")
            
            # Step 3: Merge datasets
            logger.info("Merging datasets...")
            merged_df = self.merge_datasets(datasets)
            
            if merged_df is None or merged_df.empty:
                logger.error("Failed to merge datasets or merged data is empty")
                return None
            
            # Step 4: Create final ML table
            logger.info("Creating final ML features table...")
            ml_table = self.create_final_ml_table(merged_df)
            
            if ml_table is None or ml_table.empty:
                logger.error("Final ML table is empty")
                return None
            
            # Final summary
            logger.info(f"Final ML features table created with {len(ml_table)} rows")
            logger.info(f"Columns: {list(ml_table.columns)}")
            
            if 'year' in ml_table.columns:
                logger.info(f"Year range: {ml_table['year'].min()} - {ml_table['year'].max()}")
            
            if 'area' in ml_table.columns:
                logger.info(f"Number of areas: {ml_table['area'].nunique()}")
            
            if 'crop_type' in ml_table.columns:
                logger.info(f"Number of crop types: {ml_table['crop_type'].nunique()}")
            
            # Data quality report
            logger.info("\n Data Quality Report:")
            for col in ml_table.columns:
                non_null = ml_table[col].notna().sum()
                pct = (non_null / len(ml_table)) * 100
                dtype = ml_table[col].dtype
                logger.info(f"  {col}: {non_null}/{len(ml_table)} ({pct:.1f}%) - {dtype}")
            
            return ml_table
            
        except Exception as e:
            logger.error(f"Unexpected error in process_data: {e}")
            return None

def main():
    """Main execution function."""
    processor = DataProcessor(data_dir="data")
    
    # Process data
    ml_table = processor.process_data()
    
    if ml_table is not None and not ml_table.empty:
        # Save output
        output_path = os.path.join(processor.data_dir, "ml_features.csv")
        try:
            ml_table.to_csv(output_path, index=False)
            logger.info(f"ML features table saved successfully → {output_path}")
            
            # Print sample data
            print("\n" + "="*60)
            print("SAMPLE OF PROCESSED DATA (First 10 rows):")
            print("="*60)
            print(ml_table.head(10))
            
            print("\n" + "="*60)
            print("SUMMARY STATISTICS:")
            print("="*60)
            numeric_cols = ml_table.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if col in ml_table.columns:
                    mean_val = ml_table[col].mean()
                    std_val = ml_table[col].std()
                    non_null = ml_table[col].notna().sum()
                    print(f"{col}: Mean = {mean_val:.2f}, Std = {std_val:.2f} ({non_null} values)")
            
            # Show data distribution
            print(f"\nDataset shape: {ml_table.shape}")
            if 'crop_type' in ml_table.columns:
                print(f"Top 5 crops: {ml_table['crop_type'].value_counts().head(5).to_dict()}")
                
        except Exception as e:
            logger.error(f"Failed to save output file: {e}")
    else:
        logger.error("Failed to create ML features table")

if __name__ == "__main__":
    main()
    