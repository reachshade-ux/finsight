import os
import asyncio
import datetime
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set Google AI Studio API key environment variables for ADK
# ADK uses GOOGLE_API_KEY or GEMINI_API_KEY. We also force non-Vertex local execution.
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

# Import core modules
from ui.theme import apply_bloomberg_theme
from core.confidence import calculate_confidence
from core.archive import init_db, save_brief, search_briefs, delete_brief
from core.pdf_export import generate_brief_pdf

# Import ADK modules and app instance
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google import genai
from agents import app

# Page configuration
st.set_page_config(
    page_title="FinSight — Multi-Agent Research Assistant",
    page_icon="📊",
    layout="wide"
)

# Apply Bloomberg Dark Theme
apply_bloomberg_theme()

# Initialize Database
init_db()

# Helper function to run the ADK Agent pipeline asynchronously
async def run_analyst_agent(ticker: str):
    session_service = InMemorySessionService()
    session_id = f"sess_{int(datetime.datetime.now().timestamp())}"
    
    # Create the session
    await session_service.create_session(app_name="agents", user_id="user", session_id=session_id)
    
    # Create runner
    runner = Runner(agent=app.root_agent, app_name="agents", session_service=session_service)
    
    brief_text = ""
    # Execute the orchestrator
    async for event in runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=f"Analyze {ticker}")]),
    ):
        if event.is_final_response():
            if event.content and event.content.parts and len(event.content.parts) > 0:
                brief_text = event.content.parts[0].text or ""
            
    # Load session to inspect the captured state
    session = await session_service.get_session(app_name="agents", user_id="user", session_id=session_id)
    state = session.state
    
    return brief_text, state

# Helper to invoke Gemini for Tab 2 Verdict
def generate_comparison_verdict(ticker_summaries: list) -> str:
    try:
        client = genai.Client()
        prompt = f"""You are a senior equity analyst comparing multiple stocks.
        Here is the financial data for the compared companies:
        {ticker_summaries}
        
        Provide a sharp, clear, and professional one-line comparative verdict (max 30 words) summarizing which stock stands out and why.
        Do not offer any disclaimers or formatting. Just output the verdict sentence directly."""
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return f"Verdict generation unavailable: {str(e)}"

# Main App Header
st.markdown("<h1 class='title-text'>📊 FinSight Terminal</h1>", unsafe_allow_html=True)
st.write("Multi-Agent AI Financial Research Assistant powered by Google ADK & Gemini 2.0")

# Onboarding expander guide
with st.expander("📖 New to FinSight? Click for Onboarding & How-To Guide", expanded=False):
    st.markdown("""
    ### Welcome to FinSight Terminal!
    FinSight is an advanced multi-agent framework designed to automate equity research.
    
    #### 🤖 Cooperating Sub-Agents:
    * **Data Agent:** Pulls live stock performance and fundamental ratios from `yfinance`.
    * **News Agent:** Fetches recent headlines and manages a local cache with a 4-hour expiry.
    * **Sentiment Agent:** Performs sentiment classification on headlines using Gemini.
    * **Earnings Agent:** Identifies if corporate earnings are due in the next 30 days.
    * **Sector Agent:** Ranks the stock's metrics against standard sector peers.
    * **Contrarian Agent:** Detects price-news divergence to spot contrarian signals.
    * **Orchestrator Agent:** Coordinates sub-agent runs and synthesizes a 200–300 word professional brief.
    
    #### 🚀 How to use the app:
    1. **🔍 Analyse Stock (Tab 1):** Select one of the **dropdown stocks** or choose 'Custom Ticker...' to type any symbol, then click **Run Multi-Agent Analysis**.
    2. **⚔️ Compare Tickers (Tab 2):** Compare 3 to 5 tickers side-by-side and get a comparative verdict.
    3. **📂 Brief Archive (Tab 3):** Explore and manage past research or download report PDFs.
    """)

# Setup Streamlit Tabs
tab1, tab2, tab3 = st.tabs(["🔍 Analyse Stock", "⚔️ Compare Tickers", "📂 Brief Archive"])

# ==================== TAB 1: ANALYSE ====================
with tab1:
    col_input, col_info = st.columns([1.3, 2.7])
    
    with col_input:
        st.subheader("Select Asset")
        
        # Dropdown options
        ticker_options = [
            "AAPL (Apple)",
            "NVDA (NVIDIA)",
            "MSFT (Microsoft)",
            "TSLA (Tesla)",
            "AMZN (Amazon)",
            "GOOGL (Alphabet)",
            "META (Meta)",
            "NFLX (Netflix)",
            "AMD (Advanced Micro Devices)",
            "PLTR (Palantir)",
            "ORCL (Oracle)",
            "Custom Ticker..."
        ]
        
        selected_dropdown = st.selectbox(
            "Choose a stock ticker:",
            options=ticker_options,
            index=0,
            key="stock_dropdown"
        )
        
        # Determine ticker_input based on selection
        if selected_dropdown == "Custom Ticker...":
            ticker_input = st.text_input("Enter Ticker (e.g. BABA, JPM):", "").strip().upper()
        else:
            ticker_input = selected_dropdown.split(" ")[0].strip().upper()
            
        analyse_btn = st.button("Run Multi-Agent Analysis", use_container_width=True)
        
    with col_info:
        if analyse_btn:
            with st.spinner(f"Orchestrating FinSight agents to analyze {ticker_input}..."):
                try:
                    # Run the async ADK pipeline
                    brief, state = asyncio.run(run_analyst_agent(ticker_input))
                    
                    # Extract captured state metrics
                    data_metrics = state.get("data_metrics")
                    news_data = state.get("news_data")
                    sentiment_analysis = state.get("sentiment_analysis")
                    earnings_data = state.get("earnings_data")
                    sector_data = state.get("sector_data")
                    contrarian_analysis = state.get("contrarian_analysis")
                    
                    # 1. Error Check
                    if not data_metrics or "error" in data_metrics:
                        error_msg = data_metrics.get("error") if data_metrics else f"No data found for ticker '{ticker_input}'"
                        st.error(f"Analysis Failed: {error_msg}")
                    else:
                        # 2. Compute Confidence Score
                        confidence = calculate_confidence(news_data, sentiment_analysis)
                        
                        # 3. Save to Archive SQLite
                        sentiment_dict = {}
                        if sentiment_analysis:
                            if hasattr(sentiment_analysis, "model_dump"):
                                sentiment_dict = sentiment_analysis.model_dump()
                            elif isinstance(sentiment_analysis, dict):
                                sentiment_dict = sentiment_analysis
                        
                        save_brief(ticker_input, brief, data_metrics, sentiment_dict, confidence)
                        
                        # Store in session state for instant PDF generation/downloads
                        st.session_state["current_analysis"] = {
                            "ticker": ticker_input,
                            "brief": brief,
                            "metrics": data_metrics,
                            "sentiment": sentiment_dict,
                            "confidence": confidence,
                            "sector": sector_data
                        }
                except Exception as e:
                    st.error(f"Orchestration Error: {str(e)}")
                    
        # Render the Analysis Output if present
        if "current_analysis" in st.session_state and st.session_state["current_analysis"]["ticker"] == ticker_input:
            analysis = st.session_state["current_analysis"]
            metrics = analysis["metrics"]
            sentiment = analysis["sentiment"]
            brief = analysis["brief"]
            confidence = analysis["confidence"]
            sector = analysis["sector"]
            
            # Create sub-columns for layout
            col_metrics, col_brief = st.columns([1.5, 2.5])
            
            with col_metrics:
                st.markdown("### Executive Metrics")
                
                # Format Market Cap
                mc = metrics.get("market_cap")
                mc_formatted = "N/A"
                if mc:
                    if mc >= 1e12:
                        mc_formatted = f"${mc/1e12:.2f}T"
                    elif mc >= 1e9:
                        mc_formatted = f"${mc/1e9:.2f}B"
                    elif mc >= 1e6:
                        mc_formatted = f"${mc/1e6:.2f}M"
                        
                price = metrics.get("current_price", 0.0)
                pe = metrics.get("pe_ratio")
                pe_formatted = f"{pe:.2f}" if pe else "N/A"
                change_30d = metrics.get("thirty_day_change_percent", 0.0)
                
                # HTML Metric Panels
                st.markdown(f"""
                <div class='terminal-container'>
                    <div class='metric-card-title'>Company Name</div>
                    <div class='metric-card-value' style='font-size: 1.25rem; font-family: inherit;'>{metrics.get('company_name', ticker_input)}</div>
                    <div style='margin-top: 10px;'>
                        <span class='metric-card-title'>Sector: </span>
                        <span>{metrics.get('sector', 'Unknown')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class='terminal-container'>
                    <div class='metric-card-title'>Price & Performance</div>
                    <div class='metric-card-value'>${price:.2f}</div>
                    <div class='mono-text {"status-bullish" if change_30d >= 0 else "status-bearish"}' style='font-size: 1rem;'>
                        30-Day Return: {change_30d:+.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class='terminal-container'>
                    <div class='metric-card-title'>Key Ratios</div>
                    <div style='display: flex; justify-content: space-around; margin-top: 10px;'>
                        <div>
                            <div class='metric-card-title'>P/E Ratio</div>
                            <div class='mono-text' style='color:#ffffff; font-size:1.1rem;'>{pe_formatted}</div>
                        </div>
                        <div>
                            <div class='metric-card-title'>Market Cap</div>
                            <div class='mono-text' style='color:#ffffff; font-size:1.1rem;'>{mc_formatted}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Confidence Meter
                st.markdown("### Confidence Meter")
                st.progress(confidence / 100.0)
                st.markdown(f"<div class='mono-text' style='text-align: right; color:#ffffff;'>{confidence}/100</div>", unsafe_allow_html=True)

            with col_brief:
                st.markdown("### Analyst Brief")
                st.markdown(brief)
                
                # PDF Export button
                pdf_data = generate_brief_pdf(
                    ticker=analysis["ticker"],
                    brief=brief,
                    metrics=metrics,
                    sentiment=sentiment,
                    confidence=confidence,
                    sector_data=sector
                )
                
                st.download_button(
                    label="📥 Download Formatted Brief (PDF)",
                    data=pdf_data,
                    file_name=f"FinSight_{analysis['ticker']}_Brief.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                # Earnings Catalyst Alert
                if earnings_data and earnings_data.get("is_due_soon"):
                    st.markdown(f"""
                    <div class='terminal-container alert'>
                        <h4 style='color:#ff3333; margin:0 0 5px 0;'>⚠️ Upcoming Earnings Catalyst</h4>
                        <p style='margin:0; font-size:0.9rem;'>
                            {earnings_data.get('message')}
                            Earnings results are expected in less than 30 days. High volatility expected.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                # Contrarian Divergence Alert
                if contrarian_analysis and contrarian_analysis.get("is_divergent"):
                    st.markdown(f"""
                    <div class='terminal-container alert'>
                        <h4 style='color:#ffb000; margin:0 0 5px 0;'>⚠️ Contrarian Signal Detected</h4>
                        <p style='margin:0; font-size:0.9rem;'>
                            <strong>{contrarian_analysis.get('divergence_type')}</strong><br/>
                            {contrarian_analysis.get('details')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

            # Sector Comparison Panel (rendered below columns)
            if sector and "comparison_metrics" in sector:
                st.markdown("### Sector Peers Comparison")
                df_sector = pd.DataFrame(sector["comparison_metrics"])
                
                # Format peer table
                df_sector.columns = ["Ticker", "Company Name", "P/E Ratio", "30-Day Return (%)"]
                
                # Display Rank Summary
                pe_rank = sector.get("pe_rank")
                pe_total = sector.get("pe_total")
                ret_rank = sector.get("return_rank")
                ret_total = sector.get("return_total")
                
                rank_str = f"**P/E Value Rank:** {pe_rank}/{pe_total} (Cheapest to Most Expensive) | " if pe_rank else ""
                rank_str += f"**30-Day Return Rank:** {ret_rank}/{ret_total} (Best to Worst)"
                st.markdown(rank_str)
                st.dataframe(df_sector.style.format({
                    "P/E Ratio": lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A",
                    "30-Day Return (%)": "{:+.2f}%"
                }), use_container_width=True, hide_index=True)

# ==================== TAB 2: COMPARE ====================
with tab2:
    st.subheader("Multi-Ticker Side-by-Side Comparison")
    st.write("Compare 3 to 5 stock tickers on core metrics with a Gemini-generated comparative verdict.")
    
    tickers_input = st.text_input(
        "Enter tickers separated by commas (e.g., AAPL, MSFT, GOOGL, NVDA):", 
        "AAPL, MSFT, GOOGL"
    )
    
    compare_btn = st.button("Compare Securities", use_container_width=True)
    
    if compare_btn:
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        
        if len(tickers) < 3 or len(tickers) > 5:
            st.error("Please enter between 3 and 5 tickers.")
        else:
            with st.spinner("Fetching financial metrics for comparison..."):
                comparison_list = []
                ticker_summaries = []
                
                # Import fetch tool directly from data agent to run in a fast loop
                from agents.data_agent import fetch_financial_data
                
                for t in tickers:
                    res = fetch_financial_data(t)
                    if "error" not in res:
                        comparison_list.append(res)
                        cap_val = res.get('market_cap', 0)
                        if cap_val >= 1e12:
                            cap_fmt = f"${cap_val/1e12:.2f}T"
                        elif cap_val >= 1e9:
                            cap_fmt = f"${cap_val/1e9:.2f}B"
                        else:
                            cap_fmt = f"${cap_val/1e6:.2f}M"
                        
                        ticker_summaries.append(
                            f"{t}: Price=${res.get('current_price')}, P/E={res.get('pe_ratio')}, 30-Day Return={res.get('thirty_day_change_percent'):+.2f}%, Market Cap={cap_fmt}"
                        )
                        
                if not comparison_list:
                    st.error("Could not fetch metrics for any of the provided tickers.")
                else:
                    # Construct DataFrame
                    df_comp = pd.DataFrame(comparison_list)
                    df_comp_display = df_comp[[
                        "ticker", "company_name", "sector", "current_price", "pe_ratio", "market_cap", "thirty_day_change_percent"
                    ]]
                    
                    df_comp_display.columns = [
                        "Ticker", "Company Name", "Sector", "Price ($)", "P/E Ratio", "Market Cap ($)", "30-Day Return (%)"
                    ]
                    
                    # Display Side-by-side Table
                    st.dataframe(df_comp_display.style.format({
                        "Price ($)": "${:.2f}",
                        "P/E Ratio": lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A",
                        "Market Cap ($)": lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A",
                        "30-Day Return (%)": "{:+.2f}%"
                    }), use_container_width=True, hide_index=True)
                    
                    # Generate Verdict
                    st.markdown("### Gemini Analyst Verdict")
                    with st.spinner("Generating comparative verdict..."):
                        verdict = generate_comparison_verdict(ticker_summaries)
                        st.markdown(f"<div class='terminal-container success'><p style='margin:0; font-size:1.1rem; font-family: Courier, monospace; color:#39ff14;'>{verdict}</p></div>", unsafe_allow_html=True)

# ==================== TAB 3: ARCHIVE ====================
with tab3:
    st.subheader("Searchable Analyst Brief Archive")
    
    col_search, _ = st.columns([2, 2])
    with col_search:
        search_query = st.text_input("Search Archive by Ticker Symbol:", "").strip().upper()
        
    # Get archived briefs
    archive_list = search_briefs(search_query if search_query else None)
    
    if not archive_list:
        st.info("No research briefs found in archive.")
    else:
        # Render each brief as an expander
        for item in archive_list:
            timestamp_parsed = datetime.datetime.fromisoformat(item["timestamp"])
            date_str = timestamp_parsed.strftime("%Y-%m-%d %H:%M:%S UTC")
            
            header = f"[{item['ticker']}] — Analysis on {date_str} (Confidence: {item['confidence']}/100)"
            
            with st.expander(header):
                st.markdown(f"### {item['ticker']} Analyst Brief")
                st.markdown(item["brief"])
                
                # Metadata block for historical context
                metrics_hist = item.get("metrics", {})
                sentiment_hist = item.get("sentiment", {})
                
                st.markdown("#### Saved Financial Metrics")
                st.json(metrics_hist)
                
                # Regenerate PDF from archive data
                pdf_data = generate_brief_pdf(
                    ticker=item["ticker"],
                    brief=item["brief"],
                    metrics=metrics_hist,
                    sentiment=sentiment_hist,
                    confidence=item["confidence"]
                )
                
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    st.download_button(
                        label="📥 Download Brief (PDF)",
                        data=pdf_data,
                        file_name=f"FinSight_{item['ticker']}_Archive_{item['id']}.pdf",
                        mime="application/pdf",
                        key=f"dl_{item['id']}"
                    )
                with col_btn2:
                    if st.button("🗑️ Delete from Archive", key=f"del_{item['id']}"):
                        delete_brief(item["id"])
                        st.success("Brief deleted successfully. Refreshing archive...")
                        st.rerun()

# Disclaimer Footer
st.markdown("""
<div class='disclaimer-footer'>
    <p>FinSight is an educational project. This is not financial advice. All yfinance and NewsAPI data is for demonstration purposes only.</p>
</div>
""", unsafe_allow_html=True)
