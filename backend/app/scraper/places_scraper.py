import logging
import asyncio
import random
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import quote
import pandas as pd
import os
from playwright.async_api import async_playwright, TimeoutError
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class GooglePlacesScraper:
    def __init__(self, headless=False):
        self.browser = None
        self.results = []
        self.headless = headless
        self.output_dir = "outputs"
        self.current_search_url = None
        self.modal_state = False
        self.current_page = None
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
                
    async def __aenter__(self):
        await self.setup()
        return self
            
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
                
    async def setup(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
            ],
            slow_mo=50
        )
        
    async def search(self, query: str, location: str) -> List[Dict]:
        if not self.browser:
            await self.setup()
            
        context = None
        try:
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=UserAgent().random
            )
            page = await context.new_page()
            self.current_page = page
            detailed_results = []
            seen_names = set()
                
            search_query = f"{query} in {location}"
            self.current_search_url = f"https://www.google.com/search?tbm=lcl&q={quote(search_query)}"
            await page.goto(self.current_search_url)
                
            page_num = 1
            while True:
                logger.info(f"Processing page {page_num}")
                await self._wait_for_page_stable(page)
                
                items = await self._get_page_items(page)
                if not items:
                    logger.warning(f"No items found on page {page_num}")
                    break
                logger.info(f"Found {len(items)} items on page {page_num}")
                
                for index, item in enumerate(items):
                    name = item['name']
                    if name in seen_names:
                        continue
                    seen_names.add(name)
                    # Get fresh element reference for each item
                    current_item = await page.query_selector(
                        f'a[jsname="kj0dLd"][data-cid][role="button"]:has(div[role="heading"] span:text-is("{name}"))'
                    )
                    if not current_item:
                        logger.warning(f"Could not find fresh reference for {name}")
                        continue
                        
                    success = False #track seen and unseen basis of success is true or not
                    for attempt in range(3):
                        try:
                            await item['element'].scroll_into_view_if_needed()
                            await item['element'].click()
                            await self._wait_for_modal(page)
                            
                            details = await self._extract_details(page)
                            if details:
                                details['name'] = name
                                detailed_results.append(details)
                                logger.info(f"Successfully extracted details for {name}")
                            else:
                                logger.error(f"No details extracted for {name}")
                            success = True
                            break
                        except Exception as e:
                            logger.error(f"Attempt {attempt + 1} failed for {name}: {str(e)}")
                            await self._close_modal(page)
                            await asyncio.sleep(1)
                        # Small delay between items
                    await asyncio.sleep(random.uniform(0.5, 1))
                
                # Try next page
                if not await self._goto_next_page(page):
                    logger.info("No more pages")
                    break
                page_num += 1

            self.results = detailed_results
            return detailed_results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            return []
        finally:
            if context:
                await context.close()

    async def _wait_for_page_stable(self, page, timeout=10000):
        try:
            await page.wait_for_load_state('load', timeout=timeout)
            await page.wait_for_selector('div[role="main"]', timeout=timeout)
            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Page stabilization failed: {str(e)}")
            return False

    async def _get_page_items(self, page) -> List[Dict]:
        try:
            # Accurate selector for the business listings
            await page.wait_for_selector('a[jsname="kj0dLd"][data-cid][role="button"]', timeout=10000)
            items = []
            listing_elements = await page.query_selector_all('a[jsname="kj0dLd"][data-cid][role="button"]')
            for element in listing_elements:
                name_element = await element.query_selector('div[role="heading"] span')
                if name_element:
                    name = (await name_element.inner_text()).strip()
                else:
                    # Alternative way to get the name
                    name = (await element.inner_text()).strip().split('\n')[0]
                items.append({'name': name, 'element': element})
            return items
        except Exception as e:
            logger.error(f"Failed to get page items: {str(e)}")
            return []

    async def _wait_for_modal(self, page, timeout=15000):
        try:
            # Wait for any of these selectors to appear
            modal_selectors = [
                'div[jsname="qUvFee"]',  # Main modal container
                'div[role="dialog"]',     # Alternate modal container
                '.dRYYxd'                 # Modal content wrapper
            ]
            
            for selector in modal_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=timeout/len(modal_selectors))
                    return True
                except TimeoutError:
                    continue
                
            return False
        except Exception as e:
            logger.error(f"Modal wait failed: {str(e)}")
            return False

    async def _extract_details(self, page) -> Optional[Dict]:
        try:
            # Wait for modal content to stabilize
            await asyncio.sleep(1)
            
            details = await page.evaluate('''
                () => {
                    function getContent(selectors) {
                        for (const selector of selectors) {
                            const el = document.querySelector(selector);
                            if (el) {
                                const text = el.textContent.trim();
                                if (text) return text;
                            }
                        }
                        return '';
                    }
                    
                    function getAttribute(selectors, attr) {
                        for (const selector of selectors) {
                            const el = document.querySelector(selector);
                            if (el && el.hasAttribute(attr)) {
                                return el.getAttribute(attr);
                            }
                        }
                        return '';
                    }
                    
                    function getWebsite(selectors) {
                        for (const selector of selectors) {
                            const el = document.querySelector(selector);
                            if (el && el.href && !el.href.includes('google.com/search') && !el.href.includes('google.com/webhp')) {
                                return el.href;
                            }
                        }
                        return '';
                    }
                    
                    function getAddress(selectors) {
                        for (const selector of selectors) {
                            const el = document.querySelector(selector);
                            if (el) {
                                const text = el.textContent.trim();
                                // Ensure it's not a price range or rating
                                if (text && text.length > 10 && !text.startsWith('$') && !text.startsWith('₹')) {
                                    return text;
                                }
                            }
                        }
                        return '';
                    }
                    
                    // Updated selectors based on actual Google Places structure
                    const nameSelectors = [
                        'h2[data-attrid="title"]',
                        '.qrShPb',
                        'div[role="heading"] span'
                    ];
                    
                    const phoneSelectors = [
                        'span[aria-label*="phone"]',
                        'a[href^="tel:"]',
                        'span[data-dtype="d3ph"]'
                    ];
                    
                    const websiteSelectors = [
                        'div.bkaPDb a.n1obkb',
                        'div[jsname="UXbvIb"] a',
                        'div.aep93e a[href]',
                        'a[data-action="visit_website"]'
                    ];
                    
                    const addressSelectors = [
                        'span.LrzXr',
                        'span[data-dtype="d3adr"]',
                        // Backup selectors for different variations
                        'div[data-attrid="kc:/location/location:address"] span',
                        'div[jsaction*="address"] span.LrzXr',
                        'div.Z1hOCe span.LrzXr'
                    ];
                    
                    const ratingSelectors = [
                        'span.Aq14fc',
                        'div[aria-label*="stars"]',
                        'span[aria-label*="stars"]'
                    ];
                    
                    const reviews = Array.from(document.querySelectorAll('.Jtu6Td')).slice(0, 5)
                        .map(review => review.textContent.trim())
                        .filter(Boolean);
                    
                    return {
                        name: getContent(nameSelectors),
                        phone: getContent(phoneSelectors) || getAttribute(['a[href^="tel:"]'], 'href')?.replace('tel:', ''),
                        website: getWebsite(websiteSelectors),
                        address: getAddress(addressSelectors),
                        rating: getContent(ratingSelectors),
                        reviews: reviews,
                        timings: getContent(['.t39EBf', '.MxsXJd', 'div[data-attrid*="hours"]']),
                        timestamp: new Date().toISOString()
                    };
                }
            ''')
            
            return details if details.get('name') else None
            
        except Exception as e:
            logger.error(f"Failed to extract details: {str(e)}")
            return None

    async def _close_modal(self, page):
        try:
            # Try to click on the close button in the modal
            close_button_selectors = [
                'button[aria-label="Close"]',
                'button[aria-label="close"]',
                'div[aria-label="Close"]',
                'div[aria-label="close"]',
                'g-dialog div[role="button"]',
                '.VfPpkd-icon-LgbsSe.yHy1rc.eT1oJ.D7QfPd',
                '.M2vV3'  # Close icon class
            ]
            for selector in close_button_selectors:
                close_button = page.locator(selector)
                if await close_button.count() > 0:
                    await close_button.first.click()
                    await asyncio.sleep(0.5)
                    return
            # If no close button, try pressing Escape
            await page.keyboard.press('Escape')
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Failed to close modal: {str(e)}")
            pass

    async def _goto_next_page(self, page) -> bool:
        try:
            next_button = page.locator('a#pnnext, a[aria-label="Next page"], td.d6cvqb a[aria-label="Next page"]')
            if await next_button.count() > 0:
                await next_button.first.click()
                await self._wait_for_page_stable(page)
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Failed to navigate to next page: {str(e)}")
            return False

    def export_to_csv(self, query: str) -> str:
        if not self.results:
            logger.warning("No results to export.")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{query.replace(' ', '_')}_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)

        df = pd.DataFrame(self.results)
        column_order = [
            'name',
            'phone',
            'email',  # Placeholder for potential enrichment
            'website',
            'address',
            'rating',
            'reviews',
            'timings',
            'timestamp'
        ]
        columns = [col for col in column_order if col in df.columns]
        df = df[columns]

        if 'reviews' in df.columns:
            df['reviews'] = df['reviews'].apply(
                lambda x: '; '.join(x) if x else ''
            )

        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        logger.info(f"CSV exported to: {filepath}")
        return filepath
