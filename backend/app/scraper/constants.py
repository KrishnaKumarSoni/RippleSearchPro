from typing import Dict

SEARCH_SELECTORS = {
    'listing': {
        'container': '.rllt__details',
        'items': '[jscontroller="AtSb"]',
        'name': '.OSrXXb',
        'fallbacks': [
            '.VkpGBb',
            '[jsaction*="click"]',
            '.rllt__link',
            '[role="button"]'
        ]
    },
    'modal': {
        'container': '.xpdopen',
        'name': '.qrShPb',
        'address': '[data-tooltip="Copy address"]',
        'phone': '[data-tooltip="Copy phone number"]',
        'website': 'a[data-tooltip="Open website"]',
        'rating': '.rllt__rating',
        'reviews': 'span.RDApEe',
        'hours': '[jsaction*="hours"]',
        'close': '[jsname="tqp7ud"]'
    },
    'navigation': {
        'next': '#pnnext',
        'no_results': '.gL9Hy'
    }
}

SCRAPER_CONFIG = {
    'base_url': 'https://www.google.com/search',
    'timeout': 30000,
    'stability_delay': 1000,
    'retry_attempts': 3,
    'retry_delay': 1000,
    'max_pages': 20,
    'output_fields': [
        'name', 'phone', 'website', 'address', 
        'rating', 'reviews', 'hours'
    ]
}