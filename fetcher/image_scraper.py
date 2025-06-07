from googlesearch import search
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import asyncio
import random
from urllib.parse import urljoin, urlparse

class ImageScraper:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Image file extensions
        self.image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico']
        
        # Common image selectors
        self.image_selectors = [
            'img[src]', 'img[data-src]', 'img[data-lazy-src]',
            '[style*="background-image"]', '.image img', '.photo img',
            '.gallery img', '.slider img', '.carousel img'
        ]

    def is_valid_image_url(self, url):
        """Check if URL is a valid image URL"""
        if not url or len(url) < 10:
            return False
        
        # Remove query parameters for extension check
        clean_url = url.split('?')[0].lower()
        
        # Check for image extensions
        if any(clean_url.endswith(ext) for ext in self.image_extensions):
            return True
        
        # Check for common image hosting patterns
        image_patterns = [
            'image', 'img', 'photo', 'pic', 'thumb', 'avatar',
            'logo', 'banner', 'gallery', 'media'
        ]
        
        return any(pattern in url.lower() for pattern in image_patterns)

    def extract_images_from_soup(self, soup, base_url):
        """Extract image URLs from BeautifulSoup object"""
        images = []
        
        # Extract from img tags
        img_tags = soup.find_all('img')
        for img in img_tags:
            # Try different src attributes
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
            
            if src:
                # Convert relative URLs to absolute
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(base_url, src)
                elif not src.startswith('http'):
                    src = urljoin(base_url, src)
                
                if self.is_valid_image_url(src):
                    alt_text = img.get('alt', '').strip()
                    title = img.get('title', '').strip()
                    
                    images.append({
                        'url': src,
                        'alt_text': alt_text,
                        'title': title,
                        'type': 'img_tag'
                    })
        
        # Extract from CSS background images
        elements_with_bg = soup.find_all(attrs={'style': re.compile(r'background-image')})
        for element in elements_with_bg:
            style = element.get('style', '')
            bg_match = re.search(r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
            if bg_match:
                bg_url = bg_match.group(1)
                if bg_url.startswith('//'):
                    bg_url = 'https:' + bg_url
                elif bg_url.startswith('/'):
                    bg_url = urljoin(base_url, bg_url)
                elif not bg_url.startswith('http'):
                    bg_url = urljoin(base_url, bg_url)
                
                if self.is_valid_image_url(bg_url):
                    images.append({
                        'url': bg_url,
                        'alt_text': element.get('alt', '').strip(),
                        'title': element.get('title', '').strip(),
                        'type': 'background_image'
                    })
        
        return images

    async def scrape_images_from_page(self, browser, url):
        """Scrape images from a single page"""
        page = None
        try:
            page = await browser.new_page()
            await page.set_extra_http_headers({'User-Agent': random.choice(self.user_agents)})
            
            # Navigate to page
            await page.goto(url, timeout=30000, wait_until='domcontentloaded')
            await asyncio.sleep(2)
            
            # Scroll to load lazy images
            try:
                for i in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1)
            except:
                pass
            
            # Get page content
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract page title
            title_element = soup.find('title')
            page_title = title_element.get_text().strip() if title_element else "No title"
            
            # Extract images
            images = self.extract_images_from_soup(soup, url)
            
            # Remove duplicates
            unique_images = []
            seen_urls = set()
            for img in images:
                if img['url'] not in seen_urls:
                    seen_urls.add(img['url'])
                    unique_images.append(img)
            
            await page.close()
            
            result = {
                'page_url': url,
                'page_title': page_title,
                'images_found': len(unique_images),
                'images': unique_images[:50]  # Limit to 50 images per page
            }
            
            print(f"  ✅ {url} - Found {len(unique_images)} images")
            return result
            
        except Exception as e:
            print(f"  ❌ {url}: {e}")
            if page:
                try:
                    await page.close()
                except:
                    pass
            return None

async def search_and_scrape_images(query, num_results=3):
    """
    Search for images across web pages
    """
    scraper = ImageScraper()
    scraped_results = []
    
    print(f"🖼️ Image search: '{query}'")
    
    try:
        # Get URLs from Google search
        urls_to_scrape = list(search(query, num_results=num_results))
        print(f"Found {len(urls_to_scrape)} URLs to scrape for images")
        
    except Exception as e:
        print(f"Search error: {e}")
        return []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        
        for i, url in enumerate(urls_to_scrape):
            print(f"Scraping images {i+1}/{len(urls_to_scrape)}")
            result = await scraper.scrape_images_from_page(browser, url)
            if result:
                scraped_results.append(result)
            
            # Rate limiting
            if i < len(urls_to_scrape) - 1:
                await asyncio.sleep(1)
        
        await browser.close()
    
    # Flatten all images into a single list with source info
    all_images = []
    for page_result in scraped_results:
        for img in page_result['images']:
            all_images.append({
                'image_url': img['url'],
                'alt_text': img['alt_text'],
                'title': img['title'],
                'source_page': page_result['page_url'],
                'source_title': page_result['page_title'],
                'image_type': img['type']
            })
    
    print(f"✅ Total images found: {len(all_images)}")
    
    return {
        'query': query,
        'total_images': len(all_images),
        'pages_scraped': len(scraped_results),
        'page_results': scraped_results,
        'all_images': all_images[:100]  # Limit to 100 total images
    }