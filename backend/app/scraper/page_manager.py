from playwright.async_api import Page
import asyncio
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class PageManager:
    def __init__(self, page: Page):
        self.page = page
        
    async def wait_for_network_idle(self, timeout: int = 5000):
        try:
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
            return True
        except Exception as e:
            logger.debug(f"Network idle timeout: {str(e)}")
            return False

    async def try_selectors(self, selectors: List[str], timeout: int = 5000) -> Optional[str]:
        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=timeout)
                return selector
            except:
                continue
        return None

    async def safe_click(self, element_selector: str, retries: int = 3) -> bool:
        for attempt in range(retries):
            try:
                # Wait for element to be visible and stable
                element = await self.page.wait_for_selector(element_selector, state='visible')
                if not element:
                    continue
                    
                # Ensure element is in viewport
                await element.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)  # Stability delay
                
                # Click with retry for intercepted clicks
                await element.click(delay=50, timeout=5000)
                return True
                
            except Exception as e:
                logger.debug(f"Click attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(1)
                
        return False