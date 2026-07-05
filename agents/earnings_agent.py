import datetime
import yfinance as yf
from google.adk.agents import Agent

from google.adk.tools import ToolContext

def fetch_earnings_calendar(ticker: str, tool_context: ToolContext = None) -> dict:
    """Checks if earnings results are due within 30 days for a given stock ticker using yfinance.

    Args:
        ticker: The stock ticker symbol.

    Returns:
        A dictionary containing next_earnings_date (string or None), days_until (int or None),
        is_due_soon (bool), and a message summary.
    """
    ticker_clean = ticker.strip().upper()
    
    # Helper to save results to state and return
    def _ret(res):
        if tool_context and hasattr(tool_context, "state"):
            tool_context.state["earnings_data"] = res
        return res

    try:
        stock = yf.Ticker(ticker_clean)
        cal = stock.calendar
        
        if not cal or "Earnings Date" not in cal:
            return _ret({
                "ticker": ticker_clean,
                "next_earnings_date": None,
                "days_until": None,
                "is_due_soon": False,
                "message": "No upcoming earnings date found in calendar."
            })
            
        earnings_dates = cal.get("Earnings Date")
        if not earnings_dates or not isinstance(earnings_dates, list) or len(earnings_dates) == 0:
            return _ret({
                "ticker": ticker_clean,
                "next_earnings_date": None,
                "days_until": None,
                "is_due_soon": False,
                "message": "No upcoming earnings date found in calendar."
            })
            
        next_earnings = earnings_dates[0]
        # In case yfinance returns a datetime object, convert to date
        if isinstance(next_earnings, datetime.datetime):
            next_earnings = next_earnings.date()
        elif not isinstance(next_earnings, datetime.date):
            # If it's a string, try to parse it, or fallback
            try:
                next_earnings = datetime.datetime.strptime(str(next_earnings), "%Y-%m-%d").date()
            except Exception:
                return _ret({
                    "ticker": ticker_clean,
                    "next_earnings_date": str(next_earnings),
                    "days_until": None,
                    "is_due_soon": False,
                    "message": f"Unable to parse earnings date: {next_earnings}"
                })
                
        today = datetime.date.today()
        days_until = (next_earnings - today).days
        
        is_due_soon = 0 <= days_until <= 30
        
        return _ret({
            "ticker": ticker_clean,
            "next_earnings_date": next_earnings.isoformat(),
            "days_until": days_until,
            "is_due_soon": is_due_soon,
            "message": f"Next earnings date is {next_earnings.isoformat()} ({days_until} days from today)."
        })
    except Exception as e:
        return _ret({
            "ticker": ticker_clean,
            "next_earnings_date": None,
            "days_until": None,
            "is_due_soon": False,
            "message": f"Error fetching earnings calendar for '{ticker_clean}': {str(e)}"
        })

# Define Earnings Agent
earnings_agent = Agent(
    name="earnings_agent",
    model="gemini-2.5-flash",
    instruction="""You are the Earnings Agent for FinSight. Your job is to check if a stock has an upcoming earnings date within 30 days.
    Always call the `fetch_earnings_calendar` tool with the provided ticker.
    Return the raw dictionary output from the tool exactly as is, without adding extra commentary or interpretations.""",
    tools=[fetch_earnings_calendar],
    description="Checks if earnings results are due within 30 days using yfinance."
)
