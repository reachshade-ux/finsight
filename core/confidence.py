import datetime
import json
from pydantic import BaseModel

def calculate_confidence(news_data: dict, sentiment_data) -> int:
    """Calculates a confidence score (0-100) based on news article volume,
    sentiment agreement, and article recency.

    Args:
        news_data: Dict returned by the News Agent containing the articles list.
        sentiment_data: Dict, Pydantic model, or JSON string of the Sentiment Agent's output.

    Returns:
        An integer confidence score from 0 to 100.
    """
    if not news_data or not news_data.get("articles"):
        return 0

    articles = news_data["articles"]
    num_articles = len(articles)
    if num_articles == 0:
        return 0

    # 1. Article Volume Score (Max 40 points: 8 points per article, max 5)
    volume_score = min(num_articles * 8, 40)

    # 2. Sentiment Agreement Score (Max 40 points)
    # Parse sentiment_data if it's a string, dict, or Pydantic model
    sentiment_articles = []
    if sentiment_data:
        try:
            if isinstance(sentiment_data, str):
                sentiment_data = json.loads(sentiment_data)
            
            if isinstance(sentiment_data, dict):
                sentiment_articles = sentiment_data.get("articles", [])
            elif isinstance(sentiment_data, BaseModel):
                # Handle Pydantic object
                sentiment_articles = getattr(sentiment_data, "articles", [])
            elif hasattr(sentiment_data, "get"):
                sentiment_articles = sentiment_data.get("articles", [])
        except Exception:
            sentiment_articles = []

    agreement_score = 0
    if sentiment_articles and len(sentiment_articles) > 0:
        sentiments = []
        for sa in sentiment_articles:
            # sa could be a dict or a Pydantic object
            if isinstance(sa, dict):
                sent = sa.get("sentiment")
            else:
                sent = getattr(sa, "sentiment", None)
            if sent:
                sentiments.append(sent)
        
        if sentiments:
            pos_count = sentiments.count("Positive")
            neu_count = sentiments.count("Neutral")
            neg_count = sentiments.count("Negative")
            
            majority_count = max(pos_count, neu_count, neg_count)
            # Agreement ratio is majority count divided by number of analyzed articles
            agreement_ratio = majority_count / len(sentiments)
            agreement_score = int(agreement_ratio * 40)
    else:
        # Fallback if sentiment_articles is empty: assume neutral/even distribution (50% agreement)
        agreement_score = 20

    # 3. Article Recency Score (Max 20 points)
    # Parse timestamps and compute average age in hours
    total_age_hours = 0
    now = datetime.datetime.now(datetime.UTC)
    parsed_count = 0
    
    for art in articles:
        pub_at = art.get("published_at")
        if not pub_at:
            continue
        try:
            # Remove Z indicator if present and parse
            if pub_at.endswith("Z"):
                pub_at = pub_at[:-1] + "+00:00"
            pub_date = datetime.datetime.fromisoformat(pub_at)
            
            # Make sure both datetimes are timezone aware or both naive
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=datetime.timezone.utc)
                
            age_hours = (now - pub_date).total_seconds() / 3600.0
            # Ensure age is not negative due to clock skew
            total_age_hours += max(0, age_hours)
            parsed_count += 1
        except Exception:
            continue

    recency_score = 0
    if parsed_count > 0:
        avg_age_hours = total_age_hours / parsed_count
        if avg_age_hours < 12:
            recency_score = 20
        elif avg_age_hours < 24:
            recency_score = 15
        elif avg_age_hours < 48:
            recency_score = 10
        elif avg_age_hours < 72:
            recency_score = 5
        else:
            recency_score = 2
    else:
        recency_score = 10  # default middle score if timestamps can't be parsed

    return volume_score + agreement_score + recency_score
