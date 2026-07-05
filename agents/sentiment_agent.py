from pydantic import BaseModel, Field
from typing import List, Literal
from google.adk.agents import Agent

class ArticleSentiment(BaseModel):
    headline: str = Field(description="The news headline analyzed.")
    sentiment: Literal["Positive", "Neutral", "Negative"] = Field(description="Sentiment rating.")
    reason: str = Field(description="Brief reason for the sentiment score (max 15 words).")

class SentimentAnalysis(BaseModel):
    articles: List[ArticleSentiment] = Field(description="List of analyzed articles with their individual sentiment ratings.")
    aggregate_signal: Literal["Bullish", "Mixed", "Bearish"] = Field(description="Overall aggregate sentiment signal based on all headlines.")
    key_themes: List[str] = Field(description="Top 2-3 key themes identified from the news articles.")

# Define Sentiment Agent
sentiment_agent = Agent(
    name="sentiment_agent",
    model="gemini-flash-latest",
    instruction="""You are the Sentiment Agent for FinSight. Your job is to analyze the sentiment of the provided news headlines for a stock.
    Analyze each headline and determine if its tone/impact is Positive, Neutral, or Negative.
    Synthesize all individual sentiments into an aggregate signal: Bullish (mostly Positive), Bearish (mostly Negative), or Mixed (even mix or mostly Neutral).
    Identify 2-3 key themes recurring across the news.
    You must format your entire response to conform precisely to the output schema provided.""",
    output_schema=SentimentAnalysis,
    output_key="sentiment_analysis",
    description="Analyzes news headlines and outputs individual sentiment scores, aggregate signal, and key themes."
)
