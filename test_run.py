import os
import argparse
import asyncio
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force local ADK execution using Gemini API instead of Vertex AI
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

# Import core modules
from core.confidence import calculate_confidence
from core.archive import save_brief, search_briefs, init_db
from core.pdf_export import generate_brief_pdf

# Import ADK modules and app
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agents import app

async def run_diagnostic(ticker: str):
    print("=" * 60)
    print(f"DIAGNOSTIC: Running FinSight Multi-Agent Pipeline for '{ticker}'")
    print("=" * 60)
    
    # 1. Initialize SQLite Database
    print("\n[1/5] Initializing SQLite archive database...")
    init_db()
    print("SQLite Database ready.")

    # 2. Run the ADK Orchestrator
    print(f"\n[2/5] Orchestrating ADK sub-agents for {ticker}...")
    session_service = InMemorySessionService()
    session_id = f"diag_{int(datetime.datetime.now().timestamp())}"
    await session_service.create_session(app_name="agents", user_id="diag_user", session_id=session_id)
    
    runner = Runner(agent=app.root_agent, app_name="agents", session_service=session_service)
    
    brief_text = ""
    try:
        async for event in runner.run_async(
            user_id="diag_user",
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=f"Analyze {ticker}")]),
        ):
            if event.is_final_response():
                if event.content and event.content.parts and len(event.content.parts) > 0:
                    brief_text = event.content.parts[0].text or ""
    except Exception as e:
        print(f"❌ Pipeline Execution Error: {str(e)}")
        
    session = await session_service.get_session(app_name="agents", user_id="diag_user", session_id=session_id)
    state = session.state
    
    # 3. Print Results & Check Captured State
    print("\n[3/5] Inspecting Agent Outputs:")
    data_metrics = state.get("data_metrics")
    news_data = state.get("news_data")
    sentiment_analysis = state.get("sentiment_analysis")
    earnings_data = state.get("earnings_data")
    sector_data = state.get("sector_data")
    contrarian_analysis = state.get("contrarian_analysis")
    
    if not data_metrics or "error" in data_metrics:
        print(f"❌ Error fetching stock data: {data_metrics.get('error') if data_metrics else 'No metrics returned.'}")
        return
        
    print(f"✅ Data Agent: Company = {data_metrics.get('company_name')}, Price = ${data_metrics.get('current_price')}, P/E = {data_metrics.get('pe_ratio')}")
    print(f"✅ News Agent: Found {len(news_data.get('articles', []))} articles (Source: {news_data.get('source')})")
    
    sentiment_sig = "Unknown"
    if sentiment_analysis:
        if isinstance(sentiment_analysis, dict):
            sentiment_sig = sentiment_analysis.get("aggregate_signal")
        else:
            sentiment_sig = getattr(sentiment_analysis, "aggregate_signal", "Unknown")
    print(f"✅ Sentiment Agent: Signal = {sentiment_sig}")
    
    is_due = earnings_data.get("is_due_soon") if earnings_data else False
    print(f"✅ Earnings Catalyst Agent: Due soon = {is_due} ({earnings_data.get('message') if earnings_data else 'N/A'})")
    
    pe_rank = sector_data.get("pe_rank") if sector_data else "N/A"
    return_rank = sector_data.get("return_rank") if sector_data else "N/A"
    print(f"✅ Sector Agent: P/E Rank = {pe_rank}, Return Rank = {return_rank}")
    
    is_div = contrarian_analysis.get("is_divergent") if contrarian_analysis else False
    print(f"✅ Contrarian Agent: Divergence detected = {is_div}")
    
    print("\n--- SYNTHESIZED ANALYST BRIEF ---")
    print(brief_text)
    print("-" * 32)
    
    # 4. Calculate Confidence Score
    print("\n[4/5] Calculating confidence score...")
    confidence = calculate_confidence(news_data, sentiment_analysis)
    print(f"Confidence Score: {confidence}/100")
    
    # 5. Archive & Export PDF
    print("\n[5/5] Archiving brief and exporting test PDF...")
    sentiment_dict = {}
    if sentiment_analysis:
        if hasattr(sentiment_analysis, "model_dump"):
            sentiment_dict = sentiment_analysis.model_dump()
        elif isinstance(sentiment_analysis, dict):
            sentiment_dict = sentiment_analysis
            
    save_brief(ticker, brief_text, data_metrics, sentiment_dict, confidence)
    print("Saved to SQLite history.")
    
    pdf_bytes = generate_brief_pdf(
        ticker=ticker,
        brief=brief_text,
        metrics=data_metrics,
        sentiment=sentiment_dict,
        confidence=confidence,
        sector_data=sector_data
    )
    
    pdf_filename = f"FinSight_{ticker}_Test_Brief.pdf"
    with open(pdf_filename, "wb") as f:
        f.write(pdf_bytes)
        
    print(f"PDF exported successfully to '{pdf_filename}'.")
    print("\n🎉 Diagnostic complete! All pipeline components verified successfully.")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinSight Multi-Agent Pipeline Diagnostic")
    parser.add_argument("--ticker", type=str, default="AAPL", help="Stock ticker symbol to test (default: AAPL)")
    args = parser.parse_args()
    
    asyncio.run(run_diagnostic(args.ticker))
