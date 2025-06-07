from googlesearch import search
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import asyncio
import random

class AdvancedWebScraper:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Enhanced price extraction patterns
        self.price_patterns = [
            r'₹\s*[\d,]+(?:\.\d{2})?', r'Rs\.?\s*[\d,]+(?:\.\d{2})?', r'INR\s*[\d,]+(?:\.\d{2})?',
            r'\$\s*[\d,]+(?:\.\d{2})?', r'USD\s*[\d,]+(?:\.\d{2})?',
            r'€\s*[\d,]+(?:\.\d{2})?', r'EUR\s*[\d,]+(?:\.\d{2})?',
            r'Price[:\s]*₹?\$?€?[\d,]+(?:\.\d{2})?', r'MRP[:\s]*₹?\$?€?[\d,]+(?:\.\d{2})?',
            r'Cost[:\s]*₹?\$?€?[\d,]+(?:\.\d{2})?', r'Sale[:\s]*₹?\$?€?[\d,]+(?:\.\d{2})?'
        ]
        
        # E-commerce selectors for price extraction
        self.ecommerce_selectors = {
            'amazon': {
                'price': ['.a-price-whole', '.a-price .a-offscreen', '#priceblock_dealprice', '#priceblock_ourprice'],
                'title': ['#productTitle', '.product-title', 'h1.a-size-large']
            },
            'flipkart': {
                'price': ['._30jeq3._16Jk6d', '._30jeq3', '.CEmiEU', '._1_WHN1'],
                'title': ['.B_NuCI', '._35KyD6']
            },
            'ebay': {
                'price': ['.notranslate', '.u-flL.condText'],
                'title': ['#x-title-label-lbl', '.x-item-title-label']
            }
        }

    def detect_site_type(self, url):
        url_lower = url.lower()
        if 'amazon.' in url_lower: return 'amazon'
        elif 'flipkart.' in url_lower: return 'flipkart'
        elif 'ebay.' in url_lower: return 'ebay'
        elif any(ecom in url_lower for ecom in ['shop', 'store', 'buy', 'cart', 'product']): return 'ecommerce'
        else: return 'general'

    def extract_prices(self, soup, url):
        prices = {'current_price': None, 'all_prices': []}
        site_type = self.detect_site_type(url)
        
        # Try site-specific selectors
        if site_type in self.ecommerce_selectors:
            for price_sel in self.ecommerce_selectors[site_type].get('price', []):
                price_elem = soup.select_one(price_sel)
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    if price_text and any(char.isdigit() for char in price_text):
                        prices['current_price'] = price_text
                        break
        
        # Regex fallback
        page_text = soup.get_text()
        all_found_prices = []
        for pattern in self.price_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            all_found_prices.extend(matches)
        
        # Clean prices
        cleaned_prices = []
        for price in all_found_prices:
            cleaned = price.strip()
            if cleaned and any(char.isdigit() for char in cleaned):
                cleaned_prices.append(cleaned)
        
        prices['all_prices'] = list(set(cleaned_prices))[:5]
        if not prices['current_price'] and prices['all_prices']:
            prices['current_price'] = prices['all_prices'][0]
        
        return prices

    def clean_text(self, text):
        if not text: return ""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line and len(line) > 3]
        return '\n'.join(lines).strip()

    async def extract_vast_content(self, soup):
        content_parts = []
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'menu']):
            element.decompose()
        
        # Extract from main content areas
        selectors = ['main', 'article', '.main-content', '#main-content', '.content', '#content', '.post-content']
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = self.clean_text(element.get_text())
                if len(text) > 100:
                    content_parts.append(text)
                    if len('\n'.join(content_parts)) > 3000: break
            if len('\n'.join(content_parts)) > 3000: break
        
        # Fallback to paragraphs
        if len('\n'.join(content_parts)) < 800:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                p_text = self.clean_text(p.get_text())
                if len(p_text) > 30:
                    content_parts.append(p_text)
                    if len('\n'.join(content_parts)) > 4000: break
        
        final_content = '\n\n'.join(content_parts)
        if len(final_content) > 5000:
            final_content = final_content[:5000] + "... [content truncated]"
        
        return final_content if final_content else "No substantial content found."

    async def scrape_single_page(self, browser, url):
        page = None
        try:
            page = await browser.new_page()
            await page.set_extra_http_headers({'User-Agent': random.choice(self.user_agents)})
            await page.goto(url, timeout=30000, wait_until='domcontentloaded')
            await asyncio.sleep(2)
            
            # Handle cookie banners
            try:
                for selector in ['button[id*="accept"]', 'button[class*="accept"]', '.cookie-accept']:
                    try:
                        await page.click(selector, timeout=2000)
                        break
                    except: continue
            except: pass
            
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            title_element = soup.find('title')
            title = self.clean_text(title_element.get_text()) if title_element else "No title found"
            
            prices = self.extract_prices(soup, url)
            content = await self.extract_vast_content(soup)
            
            # Add price info to content
            if prices['current_price'] or prices['all_prices']:
                price_info = []
                if prices['current_price']:
                    price_info.append(f"💰 Price: {prices['current_price']}")
                if len(prices['all_prices']) > 1:
                    price_info.append(f"💵 Other Prices: {', '.join(prices['all_prices'][:3])}")
                content = f"{chr(10).join(price_info)}\n\n{content}"
            
            result = {
                'url': url,
                'title': title,
                'author': 'Web Content',
                'content': content,
                'summary': content[:300] + "..." if len(content) > 300 else content,
                'published_date': 'Unknown',
                'source': 'Web Search (Playwright)',
                'site_type': self.detect_site_type(url),
                'prices': prices
            }
            
            await page.close()
            print(f"  ✅ {url} ({len(content)} chars, {len(prices['all_prices'])} prices)")
            return result
            
        except Exception as e:
            print(f"  ❌ {url}: {e}")
            if page:
                try: await page.close()
                except: pass
            return None

async def search_and_scrape_web(query, num_results=3):
    scraper = AdvancedWebScraper()
    scraped_results = []
    
    print(f"🔍 Web search: '{query}'")
    
    try:
        urls_to_scrape = list(search(query, num_results=num_results))
        print(f"Found {len(urls_to_scrape)} URLs")
    except Exception as e:
        print(f"Search error: {e}")
        return []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        
        for i, url in enumerate(urls_to_scrape):
            print(f"Scraping {i+1}/{len(urls_to_scrape)}")
            result = await scraper.scrape_single_page(browser, url)
            if result: scraped_results.append(result)
            if i < len(urls_to_scrape) - 1: await asyncio.sleep(1)
        
        await browser.close()
    
    print(f"✅ Scraped {len(scraped_results)} pages")
    return scraped_results

# Async version
async def search_and_scrape_web_async(query, num_results=3):
    return await search_and_scrape_web(query, num_results)