from pydantic import BaseModel, Field
from typing import Literal
from google.adk.agents import Agent
from agents.models import RateLimitedGemini

class ContrarianAnalysis(BaseModel):
    is_divergent: bool = Field(description="True if there is a clear divergence between news sentiment and price action.")
    divergence_type: str = Field(description="The type of divergence, e.g., 'Bullish Price / Bearish Sentiment', 'Bearish Price / Bullish Sentiment', or 'None'.")
    details: str = Field(description="Detailed explanation of the divergence (e.g. 'Price is up 8.5% over 30 days despite predominantly bearish headlines') or why there is no divergence.")

# Define Contrarian Agent
contrarian_agent = Agent(
    name="contrarian_agent",
    model=RateLimitedGemini(model="gemini-2.5-flash-lite"),
    instruction="""You are the Contrarian Agent for FinSight. Your job is to identify if there is a divergence between the stock's recent price action (30-day percentage change) and its recent news sentiment.
    
    A divergence occurs in these cases:
    1. Bullish Price / Bearish Sentiment: The 30-day percentage change is positive (especially > 5%) but the news sentiment is predominantly Bearish.
    2. Bearish Price / Bullish Sentiment: The 30-day percentage change is negative (especially < -5%) but the news sentiment is predominantly Bullish.
    
    If either of these conditions are met, set `is_divergent` to True, classify the `divergence_type`, and provide clear, analytical details on the discrepancy.
    Otherwise, set `is_divergent` to False, set `divergence_type` to 'None', and explain that the price action is aligned with the news sentiment.
    
    You must format your entire response to conform precisely to the output schema provided.""",
    output_schema=ContrarianAnalysis,
    output_key="contrarian_analysis",
    description="Detects divergence between recent news sentiment and 30-day price action."
)
