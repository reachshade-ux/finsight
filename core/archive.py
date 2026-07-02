import os
import sqlite3
import json
import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "finsight.db")

def init_db():
    """Initializes the SQLite database and creates the briefs table if it doesn't exist."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS briefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            brief TEXT NOT NULL,
            metrics TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            confidence INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_brief(ticker: str, brief: str, metrics: dict, sentiment: dict, confidence: int):
    """Saves a generated brief and its structured metadata to the SQLite database.

    Args:
        ticker: The stock ticker symbol.
        brief: The text content of the generated brief.
        metrics: The stock financial metrics dictionary.
        sentiment: The news sentiment analysis dictionary.
        confidence: The calculated confidence score (0-100).
    """
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()
    metrics_json = json.dumps(metrics)
    sentiment_json = json.dumps(sentiment)
    
    cursor.execute("""
        INSERT INTO briefs (ticker, timestamp, brief, metrics, sentiment, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (ticker.strip().upper(), timestamp, brief, metrics_json, sentiment_json, confidence))
    
    conn.commit()
    conn.close()

def search_briefs(query_ticker: str = None) -> list:
    """Searches and retrieves historical briefs from the SQLite database.

    Args:
        query_ticker: Optional ticker symbol to filter by (case-insensitive). If None, returns all.

    Returns:
        A list of dictionaries representing the historical briefs, ordered by timestamp descending.
    """
    init_db()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # to return rows as dictionary-like objects
    cursor = conn.cursor()
    
    if query_ticker:
        ticker_clean = query_ticker.strip().upper()
        cursor.execute("""
            SELECT * FROM briefs 
            WHERE ticker = ? 
            ORDER BY timestamp DESC
        """, (ticker_clean,))
    else:
        cursor.execute("""
            SELECT * FROM briefs 
            ORDER BY timestamp DESC
        """)
        
    rows = cursor.fetchall()
    
    briefs_list = []
    for row in rows:
        briefs_list.append({
            "id": row["id"],
            "ticker": row["ticker"],
            "timestamp": row["timestamp"],
            "brief": row["brief"],
            "metrics": json.loads(row["metrics"]),
            "sentiment": json.loads(row["sentiment"]),
            "confidence": row["confidence"]
        })
        
    conn.close()
    return briefs_list

def delete_brief(brief_id: int):
    """Deletes a historical brief from the database.

    Args:
        brief_id: The ID of the brief to delete.
    """
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM briefs WHERE id = ?", (brief_id,))
    conn.commit()
    conn.close()
