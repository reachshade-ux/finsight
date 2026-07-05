import streamlit as st

def apply_bloomberg_theme():
    """Injects custom CSS to style the Streamlit app with a Bloomberg Terminal dark aesthetic."""
    bloomberg_css = """
    <style>
        /* Base page styling */
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap');

        /* Background and text */
        .stApp {
            background-color: #0b0c10;
            color: #c5c6c7;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        /* Smooth transition for hover states */
        .terminal-container, .stButton>button, .stTabs [data-baseweb="tab"], .metric-card {
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* Monospace font styling for numbers and metrics */
        .mono-text {
            font-family: 'Roboto Mono', monospace;
            font-weight: 700;
        }

        /* Headings */
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            font-weight: 700 !important;
        }
        
        .title-text {
            font-family: 'Inter', sans-serif;
            color: #ffb000 !important; /* Bloomberg neon amber */
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        /* Neon status indicators */
        .status-bullish {
            color: #39ff14 !important; /* Neon green */
            font-weight: bold;
        }
        
        .status-bearish {
            color: #ff3333 !important; /* Neon red */
            font-weight: bold;
        }
        
        .status-mixed {
            color: #ffb000 !important; /* Neon amber */
            font-weight: bold;
        }

        /* Metric card styling */
        .metric-card {
            background-color: #161a22;
            border: 1px solid #2d3748;
            border-radius: 6px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        }

        .metric-card:hover {
            transform: translateY(-2px);
            border-color: #ffb000;
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.4);
        }
        
        .metric-card-title {
            font-size: 0.85rem;
            color: #8f94a5;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        
        .metric-card-value {
            font-family: 'Roboto Mono', monospace;
            font-size: 1.6rem;
            font-weight: 700;
            color: #ffffff;
        }

        /* Bloomberg style terminal border containers */
        .terminal-container {
            background-color: #11141a;
            border: 1px solid #222733;
            border-left: 4px solid #ffb000;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
        }

        .terminal-container:hover {
            transform: translateY(-2px);
            border-color: #2d3748;
            border-left-color: #ffb000;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35);
        }
        
        .terminal-container.alert {
            border-left: 4px solid #ff3333;
        }
        
        .terminal-container.success {
            border-left: 4px solid #39ff14;
        }

        /* Custom styling for tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: #0b0c10;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #161a22;
            border-radius: 6px 6px 0px 0px;
            color: #c5c6c7;
            font-weight: 600;
            border: 1px solid #222733;
            border-bottom: none;
            padding: 10px 20px;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: #ffb000;
            background-color: #1e2530;
        }

        .stTabs [aria-selected="true"] {
            background-color: #222733 !important;
            color: #ffb000 !important;
            border-top: 3px solid #ffb000 !important;
        }
        
        /* Custom buttons styling */
        .stButton>button {
            background-color: #161a22;
            color: #ffffff;
            border: 1px solid #2d3748;
            border-radius: 6px;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            padding: 8px 16px;
        }
        
        .stButton>button:hover {
            background-color: #ffb000;
            color: #0b0c10;
            border-color: #ffb000;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(255, 176, 0, 0.2);
        }

        /* Disclaimer footer styles */
        .disclaimer-footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #2d3748;
            text-align: center;
            font-size: 0.8rem;
            color: #6b7280;
        }
    </style>
    """
    st.markdown(bloomberg_css, unsafe_allow_html=True)
