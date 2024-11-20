from typing import List, Dict
import os
import logging
import asyncio
from datetime import datetime
from app.utils.constants import US_STATES, INDIAN_STATES
from app.scraper.places_scraper import GooglePlacesScraper

logger = logging.getLogger(__name__)

class BatchService:
    def __init__(self, concurrent_searches=5):
        self.concurrent_searches = concurrent_searches
        
    async def process_state_batch(self, states: List[str], base_query: str, client_dir: str) -> List[Dict]:
        results = []
        scrapers = []
        
        try:
            # Create separate scraper instance for each concurrent search
            for _ in range(len(states)):
                scraper = GooglePlacesScraper()
                scraper.output_dir = client_dir
                scrapers.append(scraper)
            
            # Process states concurrently
            tasks = []
            for state, scraper in zip(states, scrapers):
                logger.info(f"Starting search for {base_query} in {state}")
                task = asyncio.create_task(scraper.search(base_query, state))
                tasks.append((state, task))
                
            # Wait for all searches to complete
            for state, task in tasks:
                try:
                    state_results = await task
                    if state_results:
                        for result in state_results:
                            result['state'] = state
                        results.extend(state_results)
                        
                        # Export state results
                        scraper = scrapers[tasks.index((state, task))]
                        scraper.results = state_results
                        scraper.export_to_csv(f"{base_query}_{state}")
                        
                except Exception as e:
                    logger.error(f"Failed to search {state}: {str(e)}")
                    
            return results
            
        finally:
            # Cleanup scrapers
            for scraper in scrapers:
                await scraper.cleanup()

    async def batch_search(self, query: str, client_name: str) -> Dict:
        try:
            # Setup
            output_dir = os.path.join("outputs", client_name)
            os.makedirs(output_dir, exist_ok=True)
            
            # Determine country and clean query
            is_india = "india" in query.lower()
            states_list = INDIAN_STATES if is_india else US_STATES
            base_query = query.replace(" in USA", "").replace(" in India", "").strip()
            
            # Process states in batches
            all_results = []
            for i in range(0, len(states_list), self.concurrent_searches):
                state_batch = states_list[i:i + self.concurrent_searches]
                batch_results = await self.process_state_batch(state_batch, base_query, output_dir)
                all_results.extend(batch_results)
                
            if all_results:
                # Save combined results
                final_scraper = GooglePlacesScraper()
                final_scraper.output_dir = output_dir
                final_scraper.results = all_results
                country = "INDIA" if is_india else "USA"
                final_filepath = final_scraper.export_to_csv(f"{base_query}_{country}_COMBINED")
                
            return {
                'total_results': len(all_results),
                'message': f'Completed batch search across {len(states_list)} states'
            }
            
        except Exception as e:
            logger.error(f"Batch search error: {str(e)}")
            raise