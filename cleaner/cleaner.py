import json
import sys
import os
import concurrent.futures
import time
import tempfile
from multiprocessing import Process
import uuid

# Add the root project directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fetcher import (
    arxiv_scraper, wikipedia, semantic_scholar, openalex, 
    pubmed, crossref, unpaywall, wikidata, websearch, doi_resolver
)

def web_search_process_wrapper(query, num_results, temp_file_path):
    """
    A wrapper to run the Playwright web scraper in a separate process.
    This isolates it and prevents it from hanging the main application.
    Uses a temporary file to communicate results instead of a queue.
    """
    import os
    print(f"Starting isolated web search process... PID: {os.getpid()}")
    try:
        results = websearch.search_and_scrape_web(query, num_results)
        print(f"Web search completed, writing {len(results)} results to {temp_file_path}")
        # Write results to temporary file
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Isolated web search process finished. PID: {os.getpid()}")
    except Exception as e:
        print(f"Error in web search process: {e}")
        # Write empty results on error
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        print(f"Web search process finished with error. PID: {os.getpid()}")

def run_all_fetchers_with_timeout(topic, doi_example, timeout=20):
    """
    Runs all fetchers concurrently, with the web scraper in a separate process.
    """
    all_results = []
    
    print(f"--- Searching for topic: '{topic}' across all sources ---")

    # --- Start the isolated Web Search Process ---
    # Create a temporary file for communication
    temp_file_path = os.path.join(tempfile.gettempdir(), f"websearch_results_{uuid.uuid4().hex}.json")
    print(f"[DEBUG] Creating web search process with temp file: {temp_file_path}")
    web_search_proc = Process(target=web_search_process_wrapper, args=(topic, 2, temp_file_path))
    print(f"[DEBUG] Starting web search process...")
    web_search_proc.start()
    print(f"[DEBUG] Web search process started with PID: {web_search_proc.pid}")

    # --- Run all other fetchers in a Thread Pool ---
    api_fetcher_jobs = {
        "arXiv": (arxiv_scraper.search_arxiv, topic, 2),  # Reduced from 3 to 2
        "OpenAlex": (openalex.search_openalex, topic, 2),  # Reduced from 3 to 2
        "CrossRef": (crossref.search_crossref, topic, 2),  # Reduced from 3 to 2
        "Wikipedia": (wikipedia.get_wikipedia_articles, [topic]),
        "Wikidata": (wikidata.search_wikidata, topic, 2),  # Reduced from 3 to 2
        # Removed PubMed and Semantic Scholar for speed
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(api_fetcher_jobs)) as executor:
        future_to_source = {executor.submit(func, *args): source for source, (func, *args) in api_fetcher_jobs.items()}

        try:
            for future in concurrent.futures.as_completed(future_to_source, timeout=12):  # Reduced timeout
                source_name = future_to_source[future]
                try:
                    data = future.result(timeout=6)  # Reduced individual timeout
                    if data:
                        print(f"-> Successfully fetched {len(data)} results from {source_name}")
                        all_results.extend(data)
                    else:
                        print(f"-> {source_name} returned no results")
                except concurrent.futures.TimeoutError:
                    print(f"-> {source_name} timed out after 6 seconds")
                except Exception as exc:
                    print(f"-> API fetcher {source_name} generated an exception: {exc}")
        except concurrent.futures.TimeoutError:
            print("-> Some API fetchers timed out, proceeding with available results")
            # Cancel remaining futures
            for future in future_to_source:
                future.cancel()
        
        print("[DEBUG] API fetcher section completed")

    # --- Get results from the Web Search Process ---
    print("\n[DEBUG] Waiting for web search results...")
    web_search_results = []
    
    # Simple approach: just wait a fixed time since we know the process completes quickly
    print("[DEBUG] Waiting 5 seconds for web search to complete...")
    time.sleep(5)
    
    print("[DEBUG] Attempting to clean up web search process...")
    try:
        if hasattr(web_search_proc, 'terminate'):
            web_search_proc.terminate()
        time.sleep(2)
    except:
        print("[DEBUG] Process cleanup had issues, continuing...")
    
    print(f"[DEBUG] Process cleanup completed")
    
    # Read results from temporary file
    print("[DEBUG] Reading results from temporary file...")
    try:
        if os.path.exists(temp_file_path):
            print(f"[DEBUG] Temporary file exists: {temp_file_path}")
            file_size = os.path.getsize(temp_file_path)
            print(f"[DEBUG] File size: {file_size} bytes")
            
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                web_search_results = json.load(f)
            
            if web_search_results:
                print(f"-> Successfully fetched {len(web_search_results)} results from Web Search")
                all_results.extend(web_search_results)
            else:
                print("-> Web search returned empty results")
                
            # Clean up temporary file
            os.remove(temp_file_path)
            print("[DEBUG] Temporary file cleaned up")
        else:
            print("-> SKIPPED: Web search did not create results file")
            print(f"[DEBUG] Expected file path: {temp_file_path}")
    except Exception as e:
        print(f"-> An error occurred reading web search results: {e}")
        import traceback
        traceback.print_exc()
        # Clean up temporary file if it exists
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except:
            pass

    print("-> Web search process cleaned up.")

    # --- Skip Unpaywall Check for Speed ---
    print("-> Skipping Unpaywall check for faster execution")
    
    # --- Enhance results with missing abstracts ---
    print("-> Enhancing results with missing abstracts...")
    try:
        all_results = doi_resolver.enhance_results_with_abstracts(all_results)
        print("-> Abstract enhancement completed")
    except Exception as e:
        print(f"-> Abstract enhancement failed: {e}")

    return all_results

if __name__ == "__main__":
    # This guard is essential for multiprocessing on Windows
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    
    search_topic = "Crop Circle"
    example_doi = "10.1038/s41586-021-03491-6"
    
    print(f"[DEBUG] Main process starting with PID: {os.getpid()}")
    start_time = time.perf_counter()
    consolidated_data = run_all_fetchers_with_timeout(search_topic, example_doi, timeout=10)
    end_time = time.perf_counter()
    
    print(f"\n[DEBUG] Total items collected before writing file: {len(consolidated_data)}")
    print(f"[DEBUG] Sample of collected data types: {[type(item).__name__ for item in consolidated_data[:3]]}")

    if consolidated_data:
        print("[DEBUG] Data found. Proceeding to write 'consolidated_results.json'...")
        filename = "consolidated_results.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(consolidated_data, f, ensure_ascii=False, indent=4)
            print(f"[DEBUG] Successfully wrote {len(consolidated_data)} items to {filename}")
            
            # Verify the file was created and has content
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"[DEBUG] File created successfully. Size: {file_size} bytes")
            else:
                print("[ERROR] File was not created!")
                
        except Exception as e:
            print(f"[ERROR] Failed to write JSON file: {e}")
            
        print(f"\n--- Operation Complete ---")
        print(f"Successfully saved {len(consolidated_data)} results from all sources to '{filename}'")
        print(f"\nTotal execution time: {end_time - start_time:.2f} seconds")
    else:
        print("\n--- No results found from any source. ---")
        print("[DEBUG] Creating empty results file for debugging...")
        filename = "consolidated_results.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            print(f"[DEBUG] Created empty results file: {filename}")
        except Exception as e:
            print(f"[ERROR] Failed to create empty results file: {e}")