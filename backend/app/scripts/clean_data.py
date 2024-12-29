import pandas as pd
import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.utils.data_cleaner import DataCleaner

def clean_enriched_data(input_file: str) -> str:
    """
    Clean the enriched data and save to a new file.
    
    Args:
        input_file: Path to the enriched CSV file
        
    Returns:
        Path to the cleaned CSV file
    """
    # Read the enriched data
    df = pd.read_csv(input_file)
    initial_count = len(df)
    
    # Clean the data
    cleaner = DataCleaner()
    df_clean = cleaner.clean_data(df)
    final_count = len(df_clean)
    
    # Generate output filename
    output_dir = os.path.dirname(input_file)
    base_name = os.path.basename(input_file).split('_enriched_')[0]
    search_query = base_name.replace('_', ' ')
    output_file = os.path.join(output_dir, f"RippleSearch{search_query}Results.csv")
    
    # Save cleaned data
    df_clean.to_csv(output_file, index=False)
    
    # Print performance metrics
    print(f"\nPerformance Metrics:")
    print(f"Total companies found: {initial_count}")
    print(f"Companies with valid email addresses: {final_count}")
    print(f"Success rate: {(final_count/initial_count)*100:.2f}%")
    print(f"\nCleaned data saved to: {output_file}")
    
    return output_file

if __name__ == "__main__":
    # Get the latest enriched file from outputs directory
    outputs_dir = "outputs"
    enriched_files = [f for f in os.listdir(outputs_dir) if f.endswith('.csv') and 'enriched' in f]
    if not enriched_files:
        print("No enriched files found in outputs directory")
        exit(1)
        
    latest_file = max(enriched_files, key=lambda x: os.path.getctime(os.path.join(outputs_dir, x)))
    input_file = os.path.join(outputs_dir, latest_file)
    
    # Clean the data
    clean_enriched_data(input_file) 