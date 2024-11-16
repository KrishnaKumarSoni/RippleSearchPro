from playwright.async_api import async_playwright
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class WebsiteScraper:
    def __init__(self):
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self.phone_pattern = r'\b(?:\+?1[-.]?)?\s*(?:\([0-9]{3}\)|[0-9]{3})[-.]?\s*[0-9]{3}[-.]?\s*[0-9]{4}\b'

    async def extract_contact_info(self, url: str) -> Dict[str, Optional[str]]:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until='networkidle')
                
                content = await page.content()
                await browser.close()
                
                emails = re.findall(self.email_pattern, content)
                phones = re.findall(self.phone_pattern, content)
                
                return {
                    'email': emails[0] if emails else None,
                    'phone': phones[0] if phones else None
                }
        except Exception as e:
            logger.error(f"Error scraping website {url}: {str(e)}")
            return {'email': None, 'phone': None}
