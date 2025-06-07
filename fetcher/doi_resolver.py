import requests
from bs4 import BeautifulSoup
import json

def get_abstract_from_doi(doi):
    """
    Try to get abstract from DOI by scraping the publisher's page
    """
    if not doi:
        return None
    
    # Clean DOI
    if doi.startswith('https://doi.org/'):
        clean_doi = doi.replace('https://doi.org/', '')
    elif doi.startswith('http://dx.doi.org/'):
        clean_doi = doi.replace('http://dx.doi.org/', '')
    else:
        clean_doi = doi
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Try the DOI URL
        url = f"https://doi.org/{clean_doi}"
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try different selectors for abstracts
            abstract_selectors = [
                '.abstract',
                '#abstract',
                '.article-abstract',
                '.section-abstract',
                '[data-testid="abstract"]',
                '.abstract-content',
                '.hlFld-Abstract',
                '.abstractSection',
                '.abstract-text'
            ]
            
            for selector in abstract_selectors:
                abstract_elem = soup.select_one(selector)
                if abstract_elem:
                    abstract_text = abstract_elem.get_text(strip=True)
                    if len(abstract_text) > 50:  # Only return if substantial
                        return abstract_text[:1000] + "..." if len(abstract_text) > 1000 else abstract_text
            
            # Try meta tags
            meta_abstract = soup.find('meta', attrs={'name': 'description'})
            if meta_abstract and meta_abstract.get('content'):
                content = meta_abstract.get('content').strip()
                if len(content) > 50:
                    return content[:500] + "..." if len(content) > 500 else content
                    
    except Exception as e:
        print(f"Error fetching abstract for DOI {doi}: {e}")
    
    return None

def enhance_results_with_abstracts(results):
    """
    Enhance results by trying to fetch abstracts for items that don't have them
    """
    enhanced_results = []
    
    for item in results:
        # If content is "No abstract available" or very short, try to get abstract from DOI
        if (item.get('content') in ['No abstract available', 'No information available'] or 
            (item.get('content') and len(item.get('content', '')) < 50)):
            
            doi = item.get('doi')
            if doi:
                print(f"Trying to fetch abstract for: {item.get('title', 'Unknown')}")
                abstract = get_abstract_from_doi(doi)
                if abstract:
                    item['content'] = abstract
                    item['summary'] = abstract[:300] + "..." if len(abstract) > 300 else abstract
                    print(f"  -> Found abstract ({len(abstract)} chars)")
                else:
                    print(f"  -> No abstract found")
        
        enhanced_results.append(item)
    
    return enhanced_results