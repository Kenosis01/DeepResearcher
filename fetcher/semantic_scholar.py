import semanticscholar
import json

def search_semantic_scholar(query, limit=5):
    """
    Searches Semantic Scholar for a given query and returns the results.
    """
    papers_data = []
    sch = semanticscholar.SemanticScholar(timeout=20)
    try:
        results = sch.search_paper(query, limit=limit)
        for item in results:
            papers_data.append({
                'source': 'Semantic Scholar',
                'title': item.title,
                'authors': [author['name'] for author in item.authors],
                'year': item.year,
                'abstract': item.abstract,
                'url': item.url,
                'paperId': item.paperId,
                'venue': item.venue
            })
    except Exception as e:
        print(f"An error occurred while searching Semantic Scholar: {e}")
        return []
    return papers_data

if __name__ == "__main__":
    search_query = "large language models"
    scraped_papers = search_semantic_scholar(search_query, limit=5)

    if scraped_papers:
        filename = "semantic_scholar_results.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(scraped_papers, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(scraped_papers)} results to {filename}")

        for paper in scraped_papers:
            print(f"\nTitle: {paper['title']}\nAuthors: {', '.join(paper['authors'])}\nYear: {paper['year']}") 