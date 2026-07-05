import os
import json
import datetime
import requests
from dotenv import load_dotenv
from google.adk.agents import Agent
from agents.models import RateLimitedGemini

# Load environment variables
load_dotenv()

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "news_cache.json")
CACHE_EXPIRY_HOURS = 4

from google.adk.tools import ToolContext

def fetch_stock_news(ticker: str, tool_context: ToolContext = None) -> dict:
    """Pulls the 5 most recent headlines for a stock ticker via NewsAPI.org.
    Uses a local JSON cache to prevent rate-limiting. Falls back to mock headlines on failure.

    Args:
        ticker: The stock ticker symbol.

    Returns:
        A dictionary with a 'ticker' key and an 'articles' list (each article containing
        title, source, url, and published_at).
    """
    ticker_clean = ticker.strip().upper()
    now = datetime.datetime.now(datetime.UTC)
    
    # Helper to save results to state and return
    def _ret(res):
        if tool_context and hasattr(tool_context, "state"):
            tool_context.state["news_data"] = res
        return res

    # Ensure data directory exists for the cache
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

    # Initialize cache dict
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    # Check cache validity
    if ticker_clean in cache:
        entry = cache[ticker_clean]
        try:
            cached_time = datetime.datetime.fromisoformat(entry["timestamp"])
            if (now - cached_time) < datetime.timedelta(hours=CACHE_EXPIRY_HOURS):
                return _ret({"ticker": ticker_clean, "articles": entry["articles"], "source": "cache"})
        except Exception:
            pass

    # Call NewsAPI
    news_api_key = os.getenv("NEWS_API_KEY", "").strip()
    articles = []
    
    # If the API key is present and not a placeholder, try to fetch
    if news_api_key and "your_news_api_key" not in news_api_key.lower():
        try:
            # We search for the ticker symbol in articles to get high relevance
            url = f"https://newsapi.org/v2/everything?q={ticker_clean}&pageSize=5&sortBy=publishedAt&language=en&apiKey={news_api_key}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                raw_articles = data.get("articles", [])[:5]
                for art in raw_articles:
                    articles.append({
                        "title": art.get("title", "No Title"),
                        "source": art.get("source", {}).get("name", "Unknown Source"),
                        "url": art.get("url", ""),
                        "published_at": art.get("publishedAt", now.isoformat())
                    })
            else:
                print(f"NewsAPI error: HTTP {response.status_code}")
        except Exception as e:
            print(f"NewsAPI fetch exception: {str(e)}")

    # Update cache if we successfully retrieved articles
    if articles:
        cache[ticker_clean] = {
            "timestamp": now.isoformat(),
            "articles": articles
        }
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"Failed to write news cache: {str(e)}")
        return _ret({"ticker": ticker_clean, "articles": articles, "source": "api"})

    # Fallback to expired cache if available
    if ticker_clean in cache:
        return _ret({
            "ticker": ticker_clean,
            "articles": cache[ticker_clean]["articles"],
            "source": "expired_cache_fallback"
        })

    # Generate mock news if everything else fails (to prevent crashes and allow local dev without keys)
    mock_articles = [
        {
            "title": f"{ticker_clean} Analyst Consensus Upgraded as Institutional Flow Increases",
            "source": "MarketWatch",
            "url": "https://www.marketwatch.com",
            "published_at": (now - datetime.timedelta(hours=2)).isoformat()
        },
        {
            "title": f"Why Investors Are Closely Watching {ticker_clean} Options Activity This Week",
            "source": "Bloomberg",
            "url": "https://www.bloomberg.com",
            "published_at": (now - datetime.timedelta(hours=5)).isoformat()
        },
        {
            "title": f"{ticker_clean} Faces Headwinds Amid Evolving Regulatory Environment",
            "source": "Reuters",
            "url": "https://www.reuters.com",
            "published_at": (now - datetime.timedelta(hours=12)).isoformat()
        },
        {
            "title": f"Inside {ticker_clean}'s Long-Term Growth Strategy: Growth Drivers to Watch",
            "source": "CNBC",
            "url": "https://www.cnbc.com",
            "published_at": (now - datetime.timedelta(days=1)).isoformat()
        },
        {
            "title": f"{ticker_clean} Technical Analysis: Key Resistance and Support Levels to Watch",
            "source": "Investing.com",
            "url": "https://www.investing.com",
            "published_at": (now - datetime.timedelta(days=1, hours=4)).isoformat()
        }
    ]
    
    # Store mock articles in cache as a temporary placeholder so we don't spam mock generation
    cache[ticker_clean] = {
        "timestamp": now.isoformat(),
        "articles": mock_articles
    }
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass

    return _ret({"ticker": ticker_clean, "articles": mock_articles, "source": "mock"})

# Define News Agent
news_agent = Agent(
    name="news_agent",
    model=RateLimitedGemini(model="gemini-2.5-flash-lite"),
    instruction="""You are the News Agent for FinSight. Your job is to pull the latest headlines for a requested stock ticker.
    Always call the `fetch_stock_news` tool with the provided ticker.
    Return the raw dictionary output from the tool exactly as is, without adding extra commentary or interpretations.""",
    tools=[fetch_stock_news],
    description="Pulls the 5 most recent headlines for a stock ticker via NewsAPI.org with caching."
)
