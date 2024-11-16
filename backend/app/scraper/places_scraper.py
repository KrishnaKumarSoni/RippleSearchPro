from playwright.async_api import async_playwright, TimeoutError
from fake_useragent import UserAgent
import logging
import asyncio
import random
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import quote

logger = logging.getLogger(__name__)

class GooglePlacesScraper:
    def __init__(self, headless=False):
        self.browser = None
        self.results = []
        self.headless = headless
        
    async def __aenter__(self):
        await self.setup()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
            
    async def setup(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox'],
            slow_mo=50
        )
    
    async def search(self, query: str, location: str) -> List[Dict]:
        if not self.browser:
            await self.setup()
            
        try:
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=UserAgent().random
            )
            page = await context.new_page()
            detailed_results = []
            seen_names = set()
            
            search_query = f"{query} in {location}"
            search_url = f"https://www.google.com/search?tbm=lcl&q={quote(search_query)}"
            await page.goto(search_url)
            
            page_num = 1
            max_pages = 5
            
            while page_num <= max_pages:
                logger.info(f"Processing page {page_num}")
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('.VkpGBb', timeout=30000)
                
                # Get all items on current page
                items = await page.evaluate('''
                    () => {
                        return Array.from(document.querySelectorAll('.VkpGBb')).map(item => {
                            const nameEl = item.querySelector('.OSrXXb');
                            return nameEl ? {
                                name: nameEl.textContent.trim(),
                                element_id: item.closest('[data-ved]')?.getAttribute('data-ved')
                            } : null;
                        }).filter(Boolean);
                    }
                ''')
                
                logger.info(f"Found {len(items)} items on page {page_num}")
                
                # Process each item
                for item in items:
                    if item['name'] in seen_names:
                        continue
                        
                    try:
                        details = await self._extract_details(page, item)
                        if details:
                            seen_names.add(item['name'])
                            detailed_results.append(details)
                            logger.info(f"Processed: {item['name']}")
                        await asyncio.sleep(random.uniform(1, 2))
                    except Exception as e:
                        logger.error(f"Failed to process {item['name']}: {str(e)}")
                        continue
                
                # Check for next page before clicking
                await page.wait_for_load_state('networkidle')
                next_button = await page.query_selector('#pnnext')
                if not next_button:
                    logger.info("No more pages")
                    break
                
                try:
                    await page.wait_for_timeout(1000)  # Add small delay before clicking
                    await next_button.click()
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(2000)  # Add delay after clicking
                    page_num += 1
                except Exception as e:
                    logger.error(f"Failed to navigate to next page: {str(e)}")
                    break
            
            await context.close()
            return detailed_results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            return []
            
    async def _extract_details(self, page, item) -> Dict:
        try:
            # Click the business listing card and wait for modal
            max_retries = 3
            for _ in range(max_retries):
                try:
                    await page.click(f'.VkpGBb:has-text("{item["name"]}")')
                    await page.wait_for_selector('.kp-header', timeout=10000)
                    break
                except:
                    await page.wait_for_timeout(1000)

            details = await page.evaluate('''
                () => {
                    function getTextContent(selector) {
                        const el = document.querySelector(selector);
                        return el ? el.textContent.trim() : null;
                    }
                    
                    function getRating() {
                        // Try multiple rating selectors
                        const ratingSelectors = [
                            'span.Aq14fc',
                            'span.yi40Hd',
                            '[data-attrid*="rating"] span:first-child',
                            'g-review-stars span',
                            '[aria-label*="stars"]'
                        ];
                        
                        for (const selector of ratingSelectors) {
                            const el = document.querySelector(selector);
                            if (el) {
                                const text = el.textContent.trim();
                                const match = text.match(/(\d+(\.\d+)?)/);
                                return match ? match[1] : null;
                            }
                        }
                        return null;
                    }
                    
                    function getTimings() {
                        const hoursContainers = document.querySelectorAll('[jscontroller="MJ14q"], [jscontroller="K3Pgmb"], [aria-label*="hour" i], .t39EBf, [data-type="opening_hours"], table.WgFkxc');
                        
                        for (const container of hoursContainers) {
                            const rows = container.querySelectorAll('tr, [role="row"]');
                            if (rows.length) {
                                const hours = Array.from(rows)
                                    .map(row => row.textContent.trim().replace(/\s+/g, ' '))
                                    .filter(text => text.length > 0)
                                    .join('; ');
                                if (hours) return hours;  // Return first valid result
                            }
                            
                            const text = container.textContent.trim();
                            if (text.match(/(\d{1,2}:\d{2}|AM|PM)/i)) return text;
                        }
                        return null;
                    }
                    
                    function getReviews() {
                        const reviewsContainer = document.querySelector('[jscontroller="fIQYlf"], [jscontroller="LVJlx"]');
                        if (!reviewsContainer) return [];
                        
                        return Array.from(reviewsContainer.querySelectorAll('[jscontroller="qjr3nc"], .WMbnJf')).slice(0, 5).map(review => {
                            const text = review.querySelector('[jscontroller="MZnM8e"], .review-full-text')?.textContent?.trim() || '';
                            const ratingEl = review.querySelector('[role="img"], .lTi8oc');
                            const rating = ratingEl ? ratingEl.getAttribute('aria-label')?.match(/\d+(\.\d+)?/)?.[0] : null;
                            
                            return { text, rating };
                        }).filter(r => r.text || r.rating);
                    }

                    return {
                        name: getTextContent('h2[data-attrid="title"]') || getTextContent('.qrShPb'),
                        phone: getTextContent('[data-dtype="d3ph"]') || document.querySelector('a[href^="tel:"]')?.href.replace('tel:', ''),
                        address: getTextContent('[data-dtype="d3adr"]') || getTextContent('.LrzXr'),
                        website: Array.from(document.querySelectorAll('a')).find(a => 
                            a.href && !a.href.includes('google.com') && 
                            (a.textContent.toLowerCase().includes('website') || a.hasAttribute('data-dtype')))?.href?.split('?')[0],
                        rating: getRating(),
                        reviews: getReviews(),
                        timings: getTimings(),
                        timestamp: new Date().toLocaleString('en-US', { 
                            timeZone: 'UTC',
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                            timeZoneName: 'short'
                        })
                    };
                }
            ''')
            
            return details if details['name'] else None

        except Exception as e:
            logger.error(f"Failed to extract details: {str(e)}")
            return None

