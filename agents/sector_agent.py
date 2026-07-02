import yfinance as yf
from google.adk.agents import Agent

PEER_MAP = {
    "technology": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL"],
    "financial services": ["JPM", "BAC", "MS", "GS", "WFC"],
    "healthcare": ["JNJ", "LLY", "UNH", "PFE", "ABBV"],
    "consumer cyclical": ["AMZN", "TSLA", "HD", "NKE", "MCD"],
    "consumer defensive": ["PG", "KO", "PEP", "WMT", "COST"],
    "energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
    "industrials": ["CAT", "GE", "UNP", "HON", "LMT"],
    "basic materials": ["LIN", "APD", "SHW", "FCX", "NEM"],
    "utilities": ["NEE", "DUKE", "SO", "AEP", "D"],
    "real estate": ["PLD", "AMT", "EQIX", "CCI", "WY"],
    "communication services": ["META", "GOOGL", "NFLX", "DIS", "TMUS"]
}

from google.adk.tools import ToolContext

def fetch_sector_relative_strength(ticker: str, tool_context: ToolContext = None) -> dict:
    """Pulls peer tickers in the same sector and ranks the input stock on P/E and 30-day return.

    Args:
        ticker: The stock ticker symbol.

    Returns:
        A dictionary containing rankings and metrics for the stock and its sector peers.
    """
    ticker_clean = ticker.strip().upper()
    
    # Helper to save results to state and return
    def _ret(res):
        if tool_context and hasattr(tool_context, "state"):
            tool_context.state["sector_data"] = res
        return res

    try:
        # 1. Fetch info for target stock
        stock = yf.Ticker(ticker_clean)
        info = stock.info
        
        sector_raw = info.get("sector", "Technology")
        sector_key = sector_raw.lower().strip()
        
        # Find matching peer list
        peers = PEER_MAP.get(sector_key, PEER_MAP["technology"])
        
        # Ensure target stock is part of the comparison but not duplicated in the peer list
        comparison_tickers = list(peers)
        if ticker_clean not in comparison_tickers:
            comparison_tickers.append(ticker_clean)
            
        # Limit to 5 total tickers for comparison to keep yfinance fetches fast
        if len(comparison_tickers) > 5:
            if ticker_clean in comparison_tickers[:5]:
                comparison_tickers = comparison_tickers[:5]
            else:
                comparison_tickers = comparison_tickers[:4] + [ticker_clean]
                
        metrics_list = []
        for t in comparison_tickers:
            try:
                t_stock = yf.Ticker(t)
                t_info = t_stock.info
                
                # Fetch price and 30-day return
                hist_1mo = t_stock.history(period="1mo")
                thirty_day_change = 0.0
                if not hist_1mo.empty and len(hist_1mo) > 1:
                    start_price = hist_1mo["Close"].iloc[0]
                    end_price = hist_1mo["Close"].iloc[-1]
                    thirty_day_change = ((end_price - start_price) / start_price) * 100
                
                pe = t_info.get("trailingPE") or t_info.get("forwardPE")
                
                metrics_list.append({
                    "ticker": t,
                    "company_name": t_info.get("shortName", t),
                    "pe_ratio": pe,
                    "thirty_day_change_percent": thirty_day_change
                })
            except Exception:
                # If a peer fails to fetch, skip it or insert placeholder
                continue
                
        # If we failed to get data for the target stock, return an error
        target_data = next((m for m in metrics_list if m["ticker"] == ticker_clean), None)
        if not target_data:
            return _ret({"error": f"Failed to fetch comparison metrics for target ticker '{ticker_clean}'"})
            
        # Filter out peers without P/E for P/E ranking, but keep them in return ranking
        pe_valid = [m for m in metrics_list if m["pe_ratio"] is not None]
        pe_sorted = sorted(pe_valid, key=lambda x: x["pe_ratio"])  # sorted ascending (cheapest first)
        
        # Sort by 30-day return descending (best performance first)
        return_sorted = sorted(metrics_list, key=lambda x: x["thirty_day_change_percent"], reverse=True)
        
        # Compute ranks (1-indexed)
        pe_rank = None
        if target_data["pe_ratio"] is not None:
            pe_rank = next((i + 1 for i, m in enumerate(pe_sorted) if m["ticker"] == ticker_clean), None)
            
        return_rank = next((i + 1 for i, m in enumerate(return_sorted) if m["ticker"] == ticker_clean), 1)
        
        return _ret({
            "ticker": ticker_clean,
            "sector": sector_raw,
            "pe_rank": pe_rank,
            "pe_total": len(pe_sorted),
            "return_rank": return_rank,
            "return_total": len(metrics_list),
            "comparison_metrics": metrics_list
        })
    except Exception as e:
        return _ret({"error": f"Error computing sector relative strength: {str(e)}"})

# Define Sector Agent
sector_agent = Agent(
    name="sector_agent",
    model="gemini-2.0-flash",
    instruction="""You are the Sector Agent for FinSight. Your job is to fetch and report the relative strength of a stock compared to its sector peers.
    Always call the `fetch_sector_relative_strength` tool with the provided ticker.
    Return the raw dictionary output from the tool exactly as is, without adding extra commentary or interpretations.""",
    tools=[fetch_sector_relative_strength],
    description="Pulls peer tickers and ranks the input stock within its sector on P/E and 30-day return."
)
