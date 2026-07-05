import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from agents.models import RateLimitedGemini, RateLimitedAgentTool
from google.adk.apps import App
from google.adk.tools import AgentTool

# Load environment variables
load_dotenv()

# Set Google AI Studio API key environment variables for ADK
# Automatically route AQ. keys to Vertex AI, and AIzaSy keys to AI Studio
api_key = os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "")

if use_vertex == "True" or (api_key.startswith("AQ.") and use_vertex != "False"):
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
else:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

# Import sub-agents
from agents.data_agent import data_agent
from agents.news_agent import news_agent
from agents.sentiment_agent import sentiment_agent
from agents.earnings_agent import earnings_agent
from agents.sector_agent import sector_agent
from agents.contrarian_agent import contrarian_agent

# Define Orchestrator Agent
orchestrator = Agent(
    name="orchestrator",
    model=RateLimitedGemini(model="gemini-2.5-flash"),
    instruction="""You are the lead financial analyst and Orchestrator of FinSight.
    Your objective is to coordinate a thorough equity analysis of the requested stock ticker.
    
    You must execute the analysis in the following strict order using the sub-agent tools:
    1. Call data_agent to fetch live stock metrics.
    2. Call news_agent to fetch recent news.
    3. Call sentiment_agent to analyze the news headlines. You must feed the news headlines fetched by news_agent into this tool.
    4. Call earnings_agent to check for upcoming earnings date catalysts.
    5. Call sector_agent to pull relative sector ranks and comparison metrics.
    6. Call contrarian_agent to detect if there is any divergence between price performance and news sentiment. You must pass both the price change (from data_agent) and news sentiment (from sentiment_agent) to the contrarian_agent.
    
    After receiving all analysis results, synthesize a 200-300 word professional analyst brief.
    The brief must be professional, clear, and structured with the following sections:
    - Executive Summary: A concise overview of the stock's current situation.
    - Financial Metrics: Key metrics (price, P/E, market cap) with sector context (ranking relative to peers).
    - News & Sentiment: Highlight key themes and aggregate signal.
    - Catalyst Warning: Warn the user if earnings are due within 30 days.
    - Contrarian Alert: Flag any divergence between price action and news sentiment.
    
    Always maintain a neutral, analytical tone. Do not make buy/sell recommendations.""",
    tools=[
        RateLimitedAgentTool(data_agent),
        RateLimitedAgentTool(news_agent),
        RateLimitedAgentTool(sentiment_agent),
        RateLimitedAgentTool(earnings_agent),
        RateLimitedAgentTool(sector_agent),
        RateLimitedAgentTool(contrarian_agent)
    ]
)

# Define the App, setting the name to match the directory 'agents'
app = App(
    name="agents",
    root_agent=orchestrator
)
