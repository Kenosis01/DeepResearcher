import requests
import json

def search_crossref(query, max_results=5):
    """
    Searches CrossRef for a given query.
    """
    url = f"https://api.crossref.org/works?query.bibliographic={query}&rows={max_results}"
    # It's good practice to identify your client in the User-Agent
    headers = {
        'User-Agent': 'FetcherBot/1.0 (mailto:transformtrails@gmail.com)'
    }
    
    results_data = []
    try:
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        for item in data.get('message', {}).get('items', []):
            authors = []
            if item.get('author'):
                authors = [f"{author.get('given', '')} {author.get('family', '')}".strip() for author in item.get('author')]
            
            # Format authors as string
            authors_str = ', '.join(authors) if authors else 'Unknown'
            
            # Get title
            title = item.get('title', ['No title available'])[0] if item.get('title') else 'No title available'
            
            # Get publication year from multiple possible sources
            year = None
            if item.get('published-print', {}).get('date-parts'):
                year = item.get('published-print', {}).get('date-parts', [[None]])[0][0]
            elif item.get('published-online', {}).get('date-parts'):
                year = item.get('published-online', {}).get('date-parts', [[None]])[0][0]
            elif item.get('created', {}).get('date-parts'):
                year = item.get('created', {}).get('date-parts', [[None]])[0][0]
            
            # Try to get content from multiple sources
            content = ""
            
            # Try abstract first
            if item.get('abstract'):
                content = item.get('abstract')
            else:
                # Build content from available metadata
                content_parts = []
                
                # Add subject/category information
                subjects = item.get('subject', [])
                if subjects:
                    content_parts.append(f"Subject areas: {', '.join(subjects[:3])}")
                
                # Add journal information
                journal = item.get('container-title', [])
                if journal:
                    content_parts.append(f"Published in: {journal[0]}")
                
                # Add publisher information
                publisher = item.get('publisher')
                if publisher:
                    content_parts.append(f"Publisher: {publisher}")
                
                # Add type information
                work_type = item.get('type')
                if work_type:
                    content_parts.append(f"Type: {work_type}")
                
                # Add reference count if available
                ref_count = item.get('reference-count')
                if ref_count:
                    content_parts.append(f"References: {ref_count} citations")
                
                # Add citation count if available
                cited_count = item.get('is-referenced-by-count')
                if cited_count:
                    content_parts.append(f"Cited by: {cited_count} papers")
                
                content = '. '.join(content_parts) if content_parts else f"Research paper: {title}"
            
            if len(content) > 500:
                content = content[:500] + "..."
            
            # Create URL from DOI if available
            doi = item.get('DOI')
            url = f"https://doi.org/{doi}" if doi else item.get('URL', 'No URL available')
            
            results_data.append({
                'url': url,
                'title': title,
                'author': authors_str,
                'content': content,
                'summary': content,
                'published_date': str(year) if year else 'Unknown',
                'source': 'CrossRef',
                'publisher': item.get('publisher', 'Unknown'),
                'doi': doi,
                'journal': item.get('container-title', ['Unknown'])[0] if item.get('container-title') else 'Unknown'
            })

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while searching CrossRef: {e}")
        return []
    
    return results_data 