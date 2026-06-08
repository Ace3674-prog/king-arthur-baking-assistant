BASE_URL = "https://shop.kingarthurbaking.com"

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
     "User-Agent": (
        "Mozilla/5.0"
    )
}

FALLBACK_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
TIMEOUT = 30  # Increased from 10 to 30 seconds for detail page fetches
MAX_PAGES = 100
RETRY_TOTAL = 5  # Increased retries from 3 to 5
RETRY_BACKOFF = 0.5  # Increased backoff from 0.3 to 0.5

EMBEDDING_MODEL = "text-embedding-3-large"
OUTPUT_JSON = "data/processed/products.json"
OUTPUT_CSV = "data/processed/products.csv"
OUTPUT_EMBEDDINGS_JSON = "data/processed/product_embeddings.json"


