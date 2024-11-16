from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
from app.scraper.places_scraper import GooglePlacesScraper
from app.scraper.website_scraper import WebsiteScraper
from app.services.enrichment_service import EnrichmentService
import asyncio
import os

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scraper = GooglePlacesScraper()
website_scraper = WebsiteScraper()
enrichment_service = EnrichmentService()

@app.route('/api/search', methods=['POST'])
async def search():
    search_query = request.json.get('query', '')
    
    if ' in ' in search_query.lower():
        query, location = search_query.lower().split(' in ', 1)
    else:
        query = search_query
        location = "United States"
    
    try:
        logger.info(f"Starting search for query: {query} in {location}")
        results = await scraper.search(query, location)
        
        if results:
            file_path = scraper.export_to_csv(search_query)
            logger.info(f"CSV exported to: {file_path}")
            return jsonify({
                'results': results,
                'file_path': file_path,
                'message': 'Search completed successfully'
            })
        return jsonify({'results': [], 'message': 'No results found'})
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export():
    try:
        return scraper.export_to_csv()
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/enrich', methods=['POST'])
async def enrich():
    try:
        file_path = request.json.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'Invalid file path'}), 400
            
        enriched_file = await enrichment_service.enrich_csv(file_path)
        return jsonify({
            'status': 'success',
            'file_path': enriched_file
        })
    except Exception as e:
        logger.error(f"Enrichment error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<path:filename>')
def download_file(filename):
    try:
        file_path = os.path.join('outputs', filename)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
