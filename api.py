from fastapi import FastAPI, Query, HTTPException
from typing import List, Dict, Any
import asyncio
import sys
import os
import time

# Add current directory to path
sys.path.append(os.path.abspath('.'))

from fetcher import arxiv_scraper, wikipedia, openalex, crossref, wikidata, websearch, image_scraper

app = FastAPI(title="Deep Research API", version="1.0.0")

@app.get("/deepsearch")
async def deepsearch(
    query: str = Query(..., description="Search query for web crawling"),
    num_results: int = Query(3, ge=1, le=20, description="Number of web pages to scrape")
):
    """
    Web-only deep search with vast data collection and price extraction
    """
    start_time = time.time()
    
    try:
        results = await websearch.search_and_scrape_web_async(query, num_results)
        execution_time = time.time() - start_time
        
        # Calculate stats
        total_content_length = sum(len(result.get('content', '')) for result in results)
        total_prices_found = sum(len(result.get('prices', {}).get('all_prices', [])) for result in results)
        
        return {
            "query": query,
            "total_results": len(results),
            "execution_time": round(execution_time, 2),
            "total_content_length": total_content_length,
            "total_prices_found": total_prices_found,
            "results": results,
            "sources_used": ["Web Search"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/deepresearch")
async def deepresearch(
    query: str = Query(..., description="Search query"),
    num_results: int = Query(3, ge=1, le=10, description="Number of results per source")
):
    """
    Comprehensive search across academic databases + web with price extraction
    """
    start_time = time.time()
    all_results = []
    sources_used = []
    
    # Academic sources
    try:
        arxiv_results = arxiv_scraper.search_arxiv(query, num_results)
        if arxiv_results:
            all_results.extend(arxiv_results)
            sources_used.append("arXiv")
    except: pass
    
    try:
        openalex_results = openalex.search_openalex(query, num_results)
        if openalex_results:
            all_results.extend(openalex_results)
            sources_used.append("OpenAlex")
    except: pass
    
    try:
        crossref_results = crossref.search_crossref(query, num_results)
        if crossref_results:
            all_results.extend(crossref_results)
            sources_used.append("CrossRef")
    except: pass
    
    try:
        wiki_results = wikipedia.get_wikipedia_articles([query])
        if wiki_results:
            all_results.extend(wiki_results)
            sources_used.append("Wikipedia")
    except: pass
    
    try:
        wikidata_results = wikidata.search_wikidata(query, num_results)
        if wikidata_results:
            all_results.extend(wikidata_results)
            sources_used.append("Wikidata")
    except: pass
    
    # Web search with price extraction
    try:
        web_results = await websearch.search_and_scrape_web_async(query, num_results)
        if web_results:
            all_results.extend(web_results)
            sources_used.append("Web Search")
    except Exception as e:
        print(f"Web search error: {e}")
    
    execution_time = time.time() - start_time
    
    return {
        "query": query,
        "total_results": len(all_results),
        "execution_time": round(execution_time, 2),
        "results": all_results,
        "sources_used": sources_used
    }

@app.get("/imagesearch")
async def imagesearch(
    query: str = Query(..., description="Search query for images"),
    num_results: int = Query(3, ge=1, le=10, description="Number of web pages to scrape for images")
):
    """
    Search and extract image URLs from web pages
    """
    start_time = time.time()
    
    try:
        results = await image_scraper.search_and_scrape_images(query, num_results)
        execution_time = time.time() - start_time
        
        return {
            "query": query,
            "total_images": results['total_images'],
            "pages_scraped": results['pages_scraped'],
            "execution_time": round(execution_time, 2),
            "page_results": results['page_results'],
            "all_images": results['all_images'],
            "sources_used": ["Image Search"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)