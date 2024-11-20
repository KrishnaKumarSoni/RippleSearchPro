from bs4 import BeautifulSoup
import aiohttp
import re
import logging
import asyncio
from typing import Dict, Optional, List, Set
from urllib.parse import urljoin, urlparse
import tldextract

logger = logging.getLogger(__name__)

class WebsiteScraper:
    def __init__(self):
        self.session = None
        # Multiple email patterns for different formats
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Basic email
            r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',  # Mailto links
            r'[A-Za-z0-9._%+-]+\s*[\[\(]\s*at\s*[\]\)]\s*[A-Za-z0-9.-]+\s*[\[\(]\s*dot\s*[\]\)]\s*[A-Z|a-z]{2,}',  # Obfuscated
        ]
        
        # Multiple phone patterns for different formats
        self.phone_patterns = [
            r'\b(?:\+?1[-.]?)?\s*(?:\([0-9]{3}\)|[0-9]{3})[-.]?\s*[0-9]{3}[-.]?\s*[0-9]{4}\b',  # US/CA
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Simple 10-digit
            r'\b(?:\+\d{1,2}\s?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',  # International
            r'tel:([0-9\-\+\(\)\s\.]+)',  # Tel links
        ]
        
        # Blacklisted domains for third-party aggregators
        self.blacklisted_domains = {
            'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
            'yelp.com', 'yellowpages.com', 'whitepages.com', 'superpages.com',
            'bbb.org', 'manta.com', 'bizapedia.com', 'chamberofcommerce.com'
        }
        
        # Contact page indicators
        self.contact_indicators = [
            'contact', 'about', 'reach', 'connect', 'touch', 'location', 
            'directions', 'find-us', 'where'
        ]

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _validate_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            ext = tldextract.extract(url)
            domain = f"{ext.domain}.{ext.suffix}"
            return (
                parsed.scheme in ('http', 'https') and
                domain not in self.blacklisted_domains
            )
        except:
            return False

    def _clean_phone(self, phone: str) -> Optional[str]:
        if not phone:
            return None
        # Remove all non-numeric characters
        digits = ''.join(filter(str.isdigit, phone))
        # Validate length and format
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        return None

    def _validate_email(self, email: str) -> Optional[str]:
        if not email:
            return None
        # Remove common invalid patterns
        if any(term in email.lower() for term in ['example', 'test', 'sample', 'domain']):
            return None
        # Validate domain
        try:
            _, domain = email.split('@')
            if tldextract.extract(domain).domain in self.blacklisted_domains:
                return None
        except:
            return None
        return email.lower()

    async def _scrape_page(self, url: str, visited: Set[str]) -> Dict[str, Optional[str]]:
        if url in visited:
            return {}
        
        visited.add(url)
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Extract all text content
                text = soup.get_text()
                
                # Find emails
                emails = set()
                for pattern in self.email_patterns:
                    found = re.findall(pattern, text)
                    emails.update(found)
                
                # Find phones
                phones = set()
                for pattern in self.phone_patterns:
                    found = re.findall(pattern, text)
                    phones.update(found)
                
                # Clean and validate findings
                valid_emails = {self._validate_email(e) for e in emails}
                valid_phones = {self._clean_phone(p) for p in phones}
                
                # Remove None values
                valid_emails = {e for e in valid_emails if e}
                valid_phones = {p for p in valid_phones if p}
                
                return {
                    'email': list(valid_emails)[0] if valid_emails else None,
                    'phone': list(valid_phones)[0] if valid_phones else None
                }
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {}

    async def extract_contact_info(self, url: str) -> Dict[str, Optional[str]]:
        if not self._validate_url(url):
            return {'email': None, 'phone': None}
        
        try:
            if not self.session:
                async with self.__class__() as scraper:
                    return await scraper._extract_contact_info_internal(url)
            return await self._extract_contact_info_internal(url)
            
        except Exception as e:
            logger.error(f"Extraction failed for {url}: {str(e)}")
            return {'email': None, 'phone': None}

    async def _extract_contact_info_internal(self, url: str) -> Dict[str, Optional[str]]:
        visited = set()
        results = await self._scrape_page(url, visited)
        
        # If we don't have both email and phone, try contact pages
        if not (results.get('email') and results.get('phone')):
            try:
                async with self.session.get(url) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Find potential contact page links
                    for link in soup.find_all('a', href=True):
                        href = link.get('href')
                        text = link.text.lower()
                        
                        if any(indicator in text for indicator in self.contact_indicators):
                            contact_url = urljoin(url, href)
                            if self._validate_url(contact_url):
                                contact_results = await self._scrape_page(contact_url, visited)
                                
                                # Update results with new findings
                                if contact_results.get('email'):
                                    results['email'] = contact_results['email']
                                if contact_results.get('phone'):
                                    results['phone'] = contact_results['phone']
                                
                                # Stop if we found both
                                if results.get('email') and results.get('phone'):
                                    break
                    
            except Exception as e:
                logger.error(f"Error searching contact pages for {url}: {str(e)}")
        
        return results
