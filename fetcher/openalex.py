import pyalex
import json

def search_openalex(query, max_results=5):
    """
    Searches OpenAlex for a given query and returns the results.
    """
    results_data = []
    # Good practice to provide an email for the 'polite' pool of API clients
    pyalex.config.email = "transformtrails@gmail.com"
    try:
        works = pyalex.Works().search(query).get(per_page=max_results)
        
        for work in works:
            # The abstract is inverted index format, so we reconstruct it.
            abstract = ""
            if work.get('abstract_inverted_index'):
                abstract = pyalex.invert_abstract(work['abstract_inverted_index'])

            # Format authors as a string
            authors_list = [author.get('author', {}).get('display_name') for author in work.get('authorships', []) if author.get('author')]
            authors_str = ', '.join(authors_list) if authors_list else 'Unknown'
            
            # Try to get content from multiple sources
            content = ""
            if abstract:
                content = abstract.replace('\n', ' ').strip()
            else:
                # Try to get content from other fields if abstract is not available
                concepts = work.get('concepts', [])
                if concepts:
                    concept_names = [concept.get('display_name', '') for concept in concepts[:5]]
                    content = f"Research concepts: {', '.join(concept_names)}. "
                
                # Add journal/venue information
                venue = work.get('primary_location', {}).get('source', {})
                if venue and venue.get('display_name'):
                    content += f"Published in: {venue.get('display_name')}. "
                
                # Add type information
                work_type = work.get('type', '')
                if work_type:
                    content += f"Type: {work_type.replace('https://openalex.org/types/', '')}. "
                
                # If still no content, use title as content
                if not content:
                    content = work.get('title', 'No information available')
            
            if len(content) > 1500:
                content = content[:1500] + "..."
            
            # Get URL from DOI or OpenAlex ID
            url = work.get('doi') if work.get('doi') else work.get('id')
            
            results_data.append({
                'url': url,
                'title': work.get('title', 'No title available'),
                'author': authors_str,
                'content': content,
                'summary': content,  # Using abstract as summary
                'published_date': str(work.get('publication_year', 'Unknown')),
                'source': 'OpenAlex',
                'doi': work.get('doi'),
                'cited_by_count': work.get('cited_by_count', 0),
                'openalex_id': work.get('id')
            })
    except Exception as e:
        print(f"An error occurred while searching OpenAlex: {e}")
        return []
    return results_data

if __name__ == "__main__":
    search_query = "transformer architecture"
    scraped_works = search_openalex(search_query, max_results=5)

    if scraped_works:
        filename = "openalex_results.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(scraped_works, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(scraped_works)} results to {filename}")

        for work in scraped_works:
            print(f"\nTitle: {work['title']}\nAuthors: {', '.join(work['authors'])}\nYear: {work['publication_year']}") 