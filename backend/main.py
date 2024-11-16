from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from app.scraper.places_scraper import GooglePlacesScraper
from app.scraper.website_scraper import WebsiteScraper
import asyncio

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scraper = GooglePlacesScraper()
website_scraper = WebsiteScraper()

@app.route('/api/search', methods=['POST'])
async def search():
    search_query = request.json.get('query', '')
    
    # Extract location from query if it contains "in"
    if ' in ' in search_query.lower():
        query, location = search_query.lower().split(' in ', 1)
    else:
        query = search_query
        location = "United States"  # Default location
    
    try:
        logger.info(f"Starting search for query: {query} in {location}")
        results = await scraper.search(query, location)
        logger.info(f"Search completed. Found {len(results)} results")
        return jsonify({'results': [r for r in results if r is not None]})
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export():
    try:
        return scraper.export_to_csv()
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
