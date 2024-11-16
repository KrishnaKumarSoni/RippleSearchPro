import pandas as pd
import asyncio
from typing import List, Dict
import logging
from datetime import datetime
import os
from ..scraper.website_scraper import WebsiteScraper

logger = logging.getLogger(__name__)

class EnrichmentService:
    def __init__(self):
        self.website_scraper = WebsiteScraper()
        self.output_dir = "outputs"
        
    async def enrich_csv(self, input_file: str) -> str:
        try:
            logger.info(f"Starting enrichment for file: {input_file}")
            df = pd.read_csv(input_file)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = os.path.join(self.output_dir, f"{base_name}_enriched_{timestamp}.csv")
            
            # Add new columns if they don't exist
            if 'extracted_email' not in df.columns:
                df['extracted_email'] = None
            if 'extracted_phone' not in df.columns:
                df['extracted_phone'] = None
                
            batch_size = 5
            total = len(df)
            
            for i in range(0, total, batch_size):
                batch = df.iloc[i:i+batch_size]
                tasks = []
                
                for _, row in batch.iterrows():
                    if pd.notna(row.get('website')):
                        logger.info(f"Adding task for website: {row['website']}")
                        tasks.append(self.website_scraper.extract_contact_info(row['website']))
                
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for j, result in enumerate(results):
                        idx = i + j
                        if isinstance(result, dict):
                            # Only update if new value exists and old value is empty
                            if result.get('email') and pd.isna(df.at[idx, 'extracted_email']):
                                df.at[idx, 'extracted_email'] = result['email']
                                logger.info(f"Found new email: {result['email']}")
                            if result.get('phone') and pd.isna(df.at[idx, 'extracted_phone']):
                                df.at[idx, 'extracted_phone'] = result['phone']
                                logger.info(f"Found new phone: {result['phone']}")
                
                logger.info(f"Processed batch {i//batch_size + 1}/{(total-1)//batch_size + 1}")
            
            logger.info(f"Saving enriched file to: {output_file}")
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            return output_file
            
        except Exception as e:
            logger.error(f"Enrichment failed: {str(e)}")
            raise