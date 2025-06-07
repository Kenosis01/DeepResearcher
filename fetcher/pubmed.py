from Bio import Entrez
import json

def search_pubmed(query, max_results=5):
    """
    Searches PubMed for a given query and returns the results.
    """
    # Always tell NCBI who you are
    Entrez.email = "transformtrails@gmail.com" 
    
    results_data = []
    try:
        # Search PubMed for article IDs
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        
        id_list = record["IdList"]
        if not id_list:
            return []
            
        # Fetch the full records for the IDs
        handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="xml")
        records = Entrez.read(handle)
        handle.close()
        
        for record in records.get('PubmedArticle', []):
            article = record.get('MedlineCitation', {}).get('Article', {})
            authors_list = article.get('AuthorList', [])
            authors = [f"{author.get('ForeName', '')} {author.get('LastName', '')}".strip() for author in authors_list]
            
            # Format authors as string
            authors_str = ', '.join(authors) if authors else 'Unknown'
            
            # Get abstract and clean it
            abstract_parts = article.get('Abstract', {}).get('AbstractText', [])
            abstract = 'No abstract available'
            if abstract_parts:
                try:
                    # Handle both string and dict elements
                    text_parts = []
                    for part in abstract_parts:
                        if isinstance(part, str):
                            text_parts.append(part)
                        elif hasattr(part, 'get'):
                            # It's a dict-like object, try to get text content
                            text_parts.append(str(part))
                        else:
                            # Convert to string as fallback
                            text_parts.append(str(part))
                    abstract = ' '.join(text_parts)
                except Exception as e:
                    print(f"Error processing abstract: {e}")
                    abstract = 'Abstract processing error'
            
            abstract = abstract.replace('\n', ' ').strip()
            if len(abstract) > 1200:
                abstract = abstract[:1200] + "..."
            
            # Get DOI and create URL
            doi_info = None
            elocation_ids = article.get('ELocationID', [])
            for eloc in elocation_ids:
                if eloc.get('@EIdType') == 'doi':
                    doi_info = eloc.get('#text')
                    break
            
            pmid = record.get('MedlineCitation', {}).get('PMID', 'N/A')
            url = f"https://doi.org/{doi_info}" if doi_info else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            
            # Get publication year
            pub_date = article.get('Journal', {}).get('JournalIssue', {}).get('PubDate', {})
            year = pub_date.get('Year') or pub_date.get('MedlineDate', 'Unknown')
            
            results_data.append({
                'url': url,
                'title': article.get('ArticleTitle', 'No title available'),
                'author': authors_str,
                'content': abstract,
                'summary': abstract,
                'published_date': str(year),
                'source': 'PubMed',
                'journal': article.get('Journal', {}).get('Title', 'Unknown'),
                'pmid': str(pmid),
                'doi': doi_info
            })

    except Exception as e:
        print(f"An error occurred while searching PubMed: {e}")
        return []
    
    return results_data

if __name__ == "__main__":
    search_query = "crispr gene editing"
    scraped_articles = search_pubmed(search_query, max_results=5)
    
    if scraped_articles:
        filename = "pubmed_results.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(scraped_articles, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(scraped_articles)} results to {filename}")

        for article in scraped_articles:
            print(f"\nTitle: {article['title']}\nJournal: {article['journal']}\nYear: {article['publication_year']}") 