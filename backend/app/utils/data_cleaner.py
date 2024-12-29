import re
import pandas as pd
from typing import Dict, List, Union

class DataCleaner:
    def __init__(self):
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,7}$')
        self.phone_pattern = re.compile(r'^\(\d{3}\)\s\d{3}-\d{4}$')
        self.tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'fbclid', 'gclid']
        
    def clean_email(self, email: str) -> str:
        """Clean and validate email addresses."""
        if not email or not isinstance(email, str):
            return ''
            
        email = email.lower().strip()
        if not self.email_pattern.match(email) or 'gmail.com' == email.split('@')[1]:
            return ''
            
        return email
        
    def clean_phone(self, phone: str) -> str:
        """Clean and standardize phone numbers."""
        if not phone or not isinstance(phone, str):
            return ''
            
        # Remove all non-numeric characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Check if we have a valid 10-digit number
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return ''
        
    def clean_website(self, url: str) -> str:
        """Clean website URLs by removing tracking parameters."""
        if not url or not isinstance(url, str):
            return ''
            
        # Remove tracking parameters
        for param in self.tracking_params:
            url = re.sub(f'[?&]{param}=[^&]+', '', url)
            
        # Remove trailing ? or & if present
        url = url.rstrip('?&')
        return url
        
    def clean_company_name(self, name: str) -> str:
        """Clean company names by removing redundant keywords and standardizing format."""
        if not name or not isinstance(name, str):
            return ''
            
        # Remove common suffixes and standardize
        name = re.sub(r'\s*[-|]\s*.*$', '', name)
        name = re.sub(r'\s*\|.*$', '', name)
        
        # Remove redundant keywords
        redundant_terms = [
            'Best', 'Interior Designer in', 'Interior Designers in',
            'Interior Design Company In', 'Best Interior Designers in',
            'Interior Designers', 'Interior Design'
        ]
        
        for term in redundant_terms:
            name = name.replace(term, '').strip()
            
        return name.strip()
        
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean all data in the DataFrame."""
        df_clean = df.copy()
        
        # Clean each column
        df_clean['name'] = df_clean['name'].apply(self.clean_company_name)
        df_clean['website'] = df_clean['website'].apply(self.clean_website)
        df_clean['extracted_email'] = df_clean['extracted_email'].apply(self.clean_email)
        df_clean['extracted_phone'] = df_clean['extracted_phone'].apply(self.clean_phone)
        
        # Remove duplicates
        df_clean = df_clean.drop_duplicates(subset=['name'], keep='first')
        
        # Keep only rows with valid email addresses
        df_clean = df_clean[df_clean['extracted_email'].str.len() > 0]
        
        return df_clean 