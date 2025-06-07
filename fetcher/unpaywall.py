import requests
import json

def find_unpaywall_version(doi):
    """
    Finds a free-to-read version of a paper using its DOI via Unpaywall.
    
    Args:
        doi (str): The Digital Object Identifier of the paper.
        
    Returns:
        A dictionary with the OA location if found, otherwise None.
    """
    # Unpaywall asks for an email in the User-Agent to help them get in touch.
    email = "transformtrails@gmail.com"
    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
    
    result_data = None
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if data and data.get('is_oa'):
             result_data = {
                'source': 'Unpaywall',
                'doi': data.get('doi'),
                'title': data.get('title'),
                'is_oa': data.get('is_oa'),
                'oa_status': data.get('oa_status'),
                'best_oa_location': data.get('best_oa_location', {})
             }
        else:
            print(f"--- No open access version found for DOI: {doi} ---")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while checking Unpaywall for DOI {doi}: {e}")
        return None
        
    return result_data

if __name__ == "__main__":
    # Example DOI of a known open-access paper
    doi_to_check = "10.1038/nature12373" 
    oa_version = find_unpaywall_version(doi_to_check)
    
    if oa_version:
        filename = "unpaywall_result.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(oa_version, f, ensure_ascii=False, indent=4)
        print(f"Saved result to {filename}")
        print(f"\nTitle: {oa_version['title']}\nStatus: {oa_version['oa_status']}\nURL: {oa_version['best_oa_location'].get('url')}")
    else:
        print(f"Could not find an open access version for DOI: {doi_to_check}") 