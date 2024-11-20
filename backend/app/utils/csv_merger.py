import pandas as pd
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class CSVMerger:
    def __init__(self, output_dir="outputs"):
        self.output_dir = output_dir
        
    def merge_files(self, main_file: str, enriched_file: str) -> str:
        try:
            main_df = pd.read_csv(main_file)
            enriched_df = pd.read_csv(enriched_file)
            
            # Merge on name and website
            merged_df = pd.merge(
                main_df, 
                enriched_df[['name', 'website', 'extracted_email', 'extracted_phone']], 
                on=['name', 'website'], 
                how='left'
            )
            
            # Save merged file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            merged_file = os.path.join(self.output_dir, f"merged_{timestamp}.csv")
            merged_df.to_csv(merged_file, index=False)
            
            return merged_file
            
        except Exception as e:
            logger.error(f"Error merging CSV files: {str(e)}")
            raise