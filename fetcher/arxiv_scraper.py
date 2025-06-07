import arxiv
from arxiv import Client, Search, SortCriterion
import textwrap
import json

def search_arxiv(query, max_results=5):
    """
    Searches arXiv for a given query and returns the results.
    """
    papers = []
    try:
        # The timeout argument was causing an error, so it has been removed.
        # The new cleaner script will handle timeouts globally.
        client = arxiv.Client()

        # Search for articles
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=SortCriterion.SubmittedDate
        )
        
        results = client.results(search)
        
        for result in results:
            # Format authors as a string
            authors_str = ', '.join([author.name for author in result.authors])
            
            # Clean and truncate summary, with fallback
            if result.summary:
                summary = result.summary.replace('\n', ' ').strip()
            else:
                # Fallback: create summary from available metadata
                summary = f"arXiv preprint in category {result.primary_category}. "
                if result.categories:
                    summary += f"Categories: {', '.join(result.categories[:3])}. "
                summary += f"Submitted on {result.published.strftime('%Y-%m-%d')}."
            
            if len(summary) > 1000:
                summary = summary[:1000] + "..."
            
            papers.append({
                'url': result.entry_id,
                'title': result.title,
                'author': authors_str,
                'content': summary,  # Using summary as content for arXiv
                'summary': summary,
                'published_date': result.published.strftime('%Y-%m-%d'),
                'source': 'arXiv',
                'pdf_url': result.pdf_url,
                'doi': None  # arXiv papers don't have DOIs initially
            })
            
    except Exception as e:
        print(f"An error occurred while searching arXiv: {e}")
        return []
        
    return papers

if __name__ == "__main__":
    search_query = "quantum entanglement"
    scraped_papers = search_arxiv(search_query, max_results=5)

    if scraped_papers:
        # Save to a file
        filename = "arxiv_results.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(scraped_papers, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(scraped_papers)} results to {filename}")

        # Also print to console
        for i, paper in enumerate(scraped_papers, 1):
            print(f"\n--- Result {i} ---")
            print(f"Title: {paper['title']}")
            authors = paper['authors']
            print(f"Authors: {', '.join(authors)}")
            print(f"Published: {paper['published_date']}")
            summary = textwrap.fill(paper['summary'], width=100)
            print(f"Summary:\n{summary}")
            print(f"PDF Link: {paper['pdf_url']}")
            print(f"Article Page: {paper['url']}")
    else:
        print("No papers found.") 