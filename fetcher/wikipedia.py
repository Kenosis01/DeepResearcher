import wikipediaapi
import json

def get_wikipedia_articles(queries):
    """
    Fetches Wikipedia articles and returns their data.

    Args:
        queries (list): A list of search terms for Wikipedia articles.
        
    Returns:
        A list of dictionaries, each representing an article.
    """
    wiki_wiki = wikipediaapi.Wikipedia(
        user_agent='MyCoolBot/1.0 (https://example.com/bot; transformtrails@gmail.com)',
        language='en',
        timeout=8
    )
    
    articles = []
    for query in queries:
        page = wiki_wiki.page(query)

        if not page.exists():
            print(f"Wikipedia page '{query}' not found.")
            continue
            
        # Clean and truncate content
        content = page.text.replace('\n\n', '\n').strip()
        if len(content) > 3000:
            content = content[:3000] + "..."
        
        # Clean and truncate summary
        summary = page.summary.replace('\n', ' ').strip()
        if len(summary) > 800:
            summary = summary[:800] + "..."
        
        articles.append({
            'url': page.fullurl,
            'title': page.title,
            'author': 'Wikipedia Contributors',
            'content': content,
            'summary': summary,
            'published_date': 'Updated continuously',
            'source': 'Wikipedia'
        })
            
    return articles
