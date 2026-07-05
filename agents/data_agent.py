import yfinance as yf
from google.adk.agents import Agent
from agents.models import RateLimitedGemini

from google.adk.tools import ToolContext

def fetch_financial_data(ticker: str, tool_context: ToolContext = None) -> dict:
    """Fetches key financial metrics for a given stock ticker using yfinance.

    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT').

    Returns:
        A dictionary containing price, market_cap, pe_ratio, fifty_two_week_high,
        fifty_two_week_low, thirty_day_change_percent, sector, and company_name.
        If the ticker is invalid, returns a dict with an 'error' key.
    """
    ticker_clean = ticker.strip().upper()
    try:
        stock = yf.Ticker(ticker_clean)
        info = stock.info
        
        # yfinance returns an empty dict or a dict with just a few keys if the ticker is invalid
        if not info or info.get("marketCap") is None:
            # Try fetching history to see if it exists
            hist = stock.history(period="1d")
            if hist.empty:
                return {"error": f"Invalid ticker '{ticker_clean}' or no financial data available."}
        
        company_name = info.get("longName") or info.get("shortName") or ticker_clean
        sector = info.get("sector") or "Unknown"
        market_cap = info.get("marketCap")
        pe_ratio = info.get("trailingPE") or info.get("forwardPE")
        fifty_two_week_high = info.get("fiftyTwoWeekHigh")
        fifty_two_week_low = info.get("fiftyTwoWeekLow")
        
        # Get current price, fallback to history close if info is missing it
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        if not current_price:
            hist_1d = stock.history(period="1d")
            if not hist_1d.empty:
                current_price = hist_1d["Close"].iloc[-1]
            else:
                current_price = 0.0

        # Calculate 30-day percentage change
        hist_1mo = stock.history(period="1mo")
        thirty_day_change_percent = 0.0
        if not hist_1mo.empty and len(hist_1mo) > 1:
            start_price = hist_1mo["Close"].iloc[0]
            end_price = hist_1mo["Close"].iloc[-1]
            thirty_day_change_percent = ((end_price - start_price) / start_price) * 100

        result = {
            "ticker": ticker_clean,
            "company_name": company_name,
            "sector": sector,
            "current_price": current_price,
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            "fifty_two_week_high": fifty_two_week_high,
            "fifty_two_week_low": fifty_two_week_low,
            "thirty_day_change_percent": thirty_day_change_percent
        }
        
        if tool_context and hasattr(tool_context, "state"):
            tool_context.state["data_metrics"] = result
            
        return result
    except Exception as e:
        return {"error": f"Error fetching financial data for '{ticker_clean}': {str(e)}"}

# Define Data Agent
data_agent = Agent(
    name="data_agent",
    model=RateLimitedGemini(model="gemini-2.5-flash-lite"),
    instruction="""You are the Data Agent for FinSight. Your job is to fetch and report the live stock metrics for a requested ticker.
    Always call the `fetch_financial_data` tool with the provided ticker.
    Return the raw dictionary output from the tool exactly as is, without adding extra commentary or interpretations.""",
    tools=[fetch_financial_data],
    description="Fetches live stock metrics (price, P/E, market cap, 52-week high/low, 30-day % change, sector) using yfinance."
)
