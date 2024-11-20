from playwright.async_api import async_playwright, Browser, Page
from fake_useragent import UserAgent
from typing import Dict, List, Optional
import logging
import asyncio
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context = None
        self.current_page = None
        
    async def setup(self):
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox'],
                slow_mo=50
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=UserAgent().chrome
            )
            return True
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            return False
            
    async def new_page(self) -> Optional[Page]:
        if not self.context:
            if not await self.setup():
                return None
        try:
            page = await self.context.new_page()
            self.current_page = page
            return page
        except Exception as e:
            logger.error(f"Failed to create new page: {str(e)}")
            return None

    async def safe_close(self):
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")

    async def wait_for_page_load(self, page: Page, selectors: List[str], timeout: int = 30000):
        try:
            await page.wait_for_load_state('domcontentloaded')
            await page.wait_for_load_state('networkidle')
            
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=timeout)
                    return True
                except:
                    continue
            return False
        except Exception as e:
            logger.error(f"Page load wait failed: {str(e)}")
            return False

    async def safe_click(self, page: Page, selector: str, retries: int = 3):
        for attempt in range(retries):
            try:
                await page.click(selector)
                return True
            except Exception as e:
                if attempt == retries - 1:
                    logger.error(f"Click failed after {retries} attempts: {str(e)}")
                    return False
                await asyncio.sleep(1)
