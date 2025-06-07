from SPARQLWrapper import SPARQLWrapper, JSON
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def search_wikidata(entity_name, limit=5):
    """
    Searches Wikidata for entities with a given name using its SPARQL endpoint.
    """
    # Configure requests session with timeout and retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql",
                           agent='FetcherBot/1.0 (mailto:transformtrails@gmail.com)')
    
    # This query uses the MediaWiki API service to search for entities.
    query = f"""
    SELECT ?item ?itemLabel ?itemDescription WHERE {{
      SERVICE wikibase:mwapi {{
        bd:serviceParam wikibase:api "EntitySearch".
        bd:serviceParam wikibase:endpoint "www.wikidata.org".
        bd:serviceParam mwapi:search "{entity_name}".
        bd:serviceParam mwapi:language "en".
        ?item wikibase:apiOutputItem mwapi:item.
      }}
      ?item wdt:P31 ?type. # To ensure it's an instance of something.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT {limit}
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(5)  # Further reduced timeout to 5 seconds

    results_data = []
    try:
        print(f"Querying Wikidata for: {entity_name}")
        results = sparql.query().convert()

        for result in results["results"]["bindings"]:
            item_id = result.get('item', {}).get('value', '')
            label = result.get('itemLabel', {}).get('value', 'No label')
            description = result.get('itemDescription', {}).get('value', 'No description available')
            
            # Filter out low-quality results
            if (label == 'No label' or 
                label.startswith('Q') and label[1:].isdigit() or  # Skip Q-numbers without proper labels
                description == 'No description available' or
                len(description) < 10):
                continue
            
            results_data.append({
                'url': item_id,
                'title': label,
                'author': 'Wikidata Contributors',
                'content': description,
                'summary': description,
                'published_date': 'Updated continuously',
                'source': 'Wikidata',
                'wikidata_id': item_id
            })

    except Exception as e:
        print(f"An error occurred during Wikidata SPARQL query: {e}")
        # Try a simpler fallback query if the main one fails
        try:
            print("Trying simplified Wikidata query...")
            simple_query = f"""
            SELECT ?item ?itemLabel WHERE {{
              ?item rdfs:label "{entity_name}"@en .
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}
            LIMIT {limit}
            """
            sparql.setQuery(simple_query)
            sparql.setTimeout(5)  # Even shorter timeout for fallback
            results = sparql.query().convert()
            
            for result in results["results"]["bindings"]:
                results_data.append({
                    'source': 'Wikidata (Fallback)',
                    'id': result.get('item', {}).get('value'),
                    'label': result.get('itemLabel', {}).get('value'),
                    'description': 'No description available'
                })
        except Exception as fallback_e:
            print(f"Fallback Wikidata query also failed: {fallback_e}")
            return []

    return results_data

if __name__ == "__main__":
    search_query = "Douglas Adams"
    scraped_entities = search_wikidata(search_query, limit=5)

    if scraped_entities:
        filename = "wikidata_results.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(scraped_entities, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(scraped_entities)} results to {filename}")

        for entity in scraped_entities:
            print(f"\nLabel: {entity['label']}\nDescription: {entity['description']}\nID: {entity['id']}") 