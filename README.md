# DeepResearcher API 🔍

A powerful FastAPI-based research tool that provides comprehensive academic search, web scraping with price extraction, and image URL collection.

## Features

- **Web-Only Search** (`/deepsearch`): Deep web crawling with vast data collection and price extraction
- **Comprehensive Research** (`/deepresearch`): Search across academic databases + web
- **Image Search** (`/imagesearch`): Extract image URLs from web pages
- **Price Extraction**: Automatically detect and extract product prices from e-commerce sites
- **Vast Data Collection**: Extract up to 5000+ characters per page
- **E-commerce Support**: Specialized scraping for Amazon, Flipkart, eBay, and other shopping sites

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Start the API
```bash
python api.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc

## API Endpoints

### 🌐 Web-Only Deep Search (`/deepsearch`)

Deep web crawling with vast data collection and price extraction.

**GET Request:**
```bash
curl "http://localhost:8000/deepsearch?query=iPhone 15 price&num_results=5"
```

**Features:**
- Vast data collection (up to 5000+ chars per page)
- Automatic price extraction from e-commerce sites
- Support for Amazon, Flipkart, eBay, and other shopping platforms
- Cookie banner handling
- Dynamic content loading

### 🔍 Comprehensive Research (`/deepresearch`)

Search across academic databases + web crawling.

**GET Request:**
```bash
curl "http://localhost:8000/deepresearch?query=machine learning&num_results=3"
```

**Sources included:**
- arXiv (academic preprints)
- OpenAlex (academic papers)
- CrossRef (academic publications)
- Wikipedia (encyclopedia)
- Wikidata (structured data)
- Web Search (live web content with prices)

### 🖼️ Image Search (`/imagesearch`)

Extract image URLs from web pages.

**GET Request:**
```bash
curl "http://localhost:8000/imagesearch?query=nature photography&num_results=3"
```

**Features:**
- Extract images from img tags and CSS backgrounds
- Support for lazy-loaded images
- Alt text and title extraction
- Duplicate removal
- Multiple image formats (JPG, PNG, WebP, SVG, etc.)

## Response Formats

### Web Search Response
```json
{
  "query": "iPhone 15 price",
  "total_results": 3,
  "execution_time": 12.45,
  "total_content_length": 15420,
  "total_prices_found": 8,
  "results": [
    {
      "url": "https://amazon.com/iphone-15",
      "title": "iPhone 15 - Amazon",
      "author": "Web Content",
      "content": "💰 Price: $799\n💵 Other Prices: $799, $829, $899\n\nApple iPhone 15 features...",
      "summary": "💰 Price: $799...",
      "published_date": "Unknown",
      "source": "Web Search (Playwright)",
      "site_type": "amazon",
      "prices": {
        "current_price": "$799",
        "all_prices": ["$799", "$829", "$899"]
      }
    }
  ]
}
```

### Image Search Response
```json
{
  "query": "nature photography",
  "total_images": 45,
  "pages_scraped": 3,
  "execution_time": 8.23,
  "all_images": [
    {
      "image_url": "https://example.com/nature1.jpg",
      "alt_text": "Beautiful mountain landscape",
      "title": "Mountain Photography",
      "source_page": "https://example.com/gallery",
      "source_title": "Nature Photography Gallery",
      "image_type": "img_tag"
    }
  ]
}
```

## Usage Examples

### Web Search with Price Extraction
```bash
# Search for product prices
curl "http://localhost:8000/deepsearch?query=laptop deals&num_results=5"

# Search for specific products
curl "http://localhost:8000/deepsearch?query=iPhone 15 Amazon&num_results=3"
```

### Academic Research
```bash
# Comprehensive academic + web search
curl "http://localhost:8000/deepresearch?query=machine learning&num_results=3"

# Research specific topics
curl "http://localhost:8000/deepresearch?query=climate change&num_results=5"
```

### Image Collection
```bash
# Find images related to a topic
curl "http://localhost:8000/imagesearch?query=architecture&num_results=5"

# Product images
curl "http://localhost:8000/imagesearch?query=modern furniture&num_results=3"
```

### Python Client
```python
import requests

# Web search with price extraction
response = requests.get(
    "http://localhost:8000/deepsearch",
    params={"query": "gaming laptop price", "num_results": 5}
)
data = response.json()

print(f"Found {data['total_results']} results with {data['total_prices_found']} prices")
for result in data['results']:
    if result.get('prices', {}).get('current_price'):
        print(f"- {result['title']}: {result['prices']['current_price']}")

# Image search
img_response = requests.get(
    "http://localhost:8000/imagesearch",
    params={"query": "nature photography", "num_results": 3}
)
img_data = img_response.json()

print(f"Found {img_data['total_images']} images from {img_data['pages_scraped']} pages")
for img in img_data['all_images'][:5]:
    print(f"- {img['image_url']} ({img['alt_text']})")
```

## Key Features

### 🛒 E-commerce Price Extraction
- **Supported Sites**: Amazon, Flipkart, eBay, and general e-commerce
- **Price Detection**: Current prices, original prices, discounts
- **Multiple Currencies**: ₹, $, €, and more
- **Price Patterns**: MRP, Sale Price, Offer Price detection

### 📊 Vast Data Collection
- **Content Length**: Up to 5000+ characters per page
- **Smart Extraction**: Headings, paragraphs, lists, and structured content
- **Dynamic Loading**: Handles JavaScript-rendered content
- **Cookie Handling**: Automatic cookie banner acceptance

### 🖼️ Advanced Image Extraction
- **Multiple Sources**: IMG tags, CSS backgrounds, lazy-loaded images
- **Metadata**: Alt text, titles, and source page information
- **Format Support**: JPG, PNG, WebP, SVG, GIF, and more
- **Deduplication**: Removes duplicate image URLs

## Performance & Limits

| Endpoint | Max Results | Avg Time | Features |
|----------|-------------|----------|----------|
| `/deepsearch` | 20 pages | 10-25s | Price extraction, vast content |
| `/deepresearch` | 10 per source | 15-35s | Academic + web search |
| `/imagesearch` | 10 pages | 8-20s | Image URL extraction |

## Project Structure
```
DeepResearcher/
├── api.py                    # Main FastAPI application
├── requirements.txt          # Dependencies
├── README.md                # Documentation
└── fetcher/                 # Scraping modules
    ├── websearch.py         # Web scraping with price extraction
    ├── image_scraper.py     # Image URL extraction
    ├── arxiv_scraper.py     # Academic paper search
    ├── openalex.py          # Academic database
    ├── crossref.py          # Academic publications
    ├── wikipedia.py         # Wikipedia articles
    └── wikidata.py          # Structured data
```

## Installation & Setup

```bash
# Clone the repository
git clone https://github.com/libdo96/DeepResearcher.git
cd DeepResearcher

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Start the API
python api.py
```

## License

MIT License - Feel free to use and modify for your research needs!