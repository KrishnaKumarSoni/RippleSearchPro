from fastapi import APIRouter, HTTPException
from app.scraper.places_scraper import GooglePlacesScraper
import asyncio

router = APIRouter()

@router.get("/search")
async def search(query: str, location: str):
    try:
        scraper = GooglePlacesScraper()
        results = await scraper.search(query, location)
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
async def export():
    try:
        scraper = GooglePlacesScraper()
        csv_data = scraper.export_to_csv()
        return {"status": "success", "data": csv_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 