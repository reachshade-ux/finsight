import streamlit as st

def apply_bloomberg_theme():
    """Injects custom CSS to style the Streamlit app with a futuristic glassmorphic dark terminal aesthetic."""
    bloomberg_css = """
    <style>
        /* Base page styling */
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Inter:wght@400;500;600;700&display=swap');

        /* Background and text with a subtle radial gradient for depth */
        .stApp {
            background: radial-gradient(circle at 50% 50%, #0d121f 0%, #06080e 100%) !important;
            color: #e2e8f0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
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
            letter-spacing: -0.02em;
        }
        
        .title-text {
            font-family: 'Inter', sans-serif;
            color: #ffb000 !important; /* Bloomberg neon amber */
            letter-spacing: 0.05em;
            text-transform: uppercase;
            text-shadow: 0 0 12px rgba(255, 176, 0, 0.35);
        }

        /* Neon status indicators */
        .status-bullish {
            color: #39ff14 !important; /* Neon green */
            font-weight: bold;
            text-shadow: 0 0 8px rgba(57, 255, 20, 0.4);
        }
        
        .status-bearish {
            color: #ff3333 !important; /* Neon red */
            font-weight: bold;
            text-shadow: 0 0 8px rgba(255, 51, 51, 0.4);
        }
        
        .status-mixed {
            color: #ffb000 !important; /* Neon amber */
            font-weight: bold;
            text-shadow: 0 0 8px rgba(255, 176, 0, 0.4);
        }

        /* Keyframes for loading animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(12px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Keyframes for pulsing warnings */
        @keyframes pulseGlowRed {
            0% { box-shadow: 0 0 8px rgba(255, 51, 51, 0.15); border-color: rgba(255, 51, 51, 0.3); }
            50% { box-shadow: 0 0 20px rgba(255, 51, 51, 0.4); border-color: rgba(255, 51, 51, 0.6); }
            100% { box-shadow: 0 0 8px rgba(255, 51, 51, 0.15); border-color: rgba(255, 51, 51, 0.3); }
        }

        @keyframes pulseGlowAmber {
            0% { box-shadow: 0 0 8px rgba(255, 176, 0, 0.15); border-color: rgba(255, 176, 0, 0.3); }
            50% { box-shadow: 0 0 20px rgba(255, 176, 0, 0.4); border-color: rgba(255, 176, 0, 0.6); }
            100% { box-shadow: 0 0 8px rgba(255, 176, 0, 0.15); border-color: rgba(255, 176, 0, 0.3); }
        }

        /* Glassmorphic Metric card styling with high depth */
        .metric-card {
            background-color: rgba(18, 24, 38, 0.6) !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            padding: 18px !important;
            text-align: center;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
            transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
            animation: fadeInUp 0.5s ease-out forwards;
        }

        .metric-card:hover {
            transform: translateY(-3px) scale(1.01);
            border-color: rgba(255, 176, 0, 0.4) !important;
            box-shadow: 0 12px 40px rgba(255, 176, 0, 0.12) !important;
        }
        
        .metric-card-title {
            font-size: 0.8rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }
        
        .metric-card-value {
            font-family: 'Roboto Mono', monospace;
            font-size: 1.7rem;
            font-weight: 700;
            color: #ffffff;
            text-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }

        /* Glassmorphic Container panels for high depth */
        .terminal-container {
            background-color: rgba(18, 24, 38, 0.65);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-left: 5px solid #ffb000;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 22px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
            animation: fadeInUp 0.6s ease-out forwards;
        }

        .terminal-container:hover {
            transform: translateY(-3px);
            border-color: rgba(255, 255, 255, 0.18);
            border-left-color: #ffb000;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
        }
        
        /* Alert pulsing glows */
        .terminal-container.alert {
            border-left: 5px solid #ff3333;
            animation: pulseGlowRed 3s infinite;
        }
        
        .terminal-container.success {
            border-left: 5px solid #39ff14;
        }

        /* Smooth inputs override */
        .stSelectbox div[data-baseweb="select"] {
            background-color: rgba(18, 24, 38, 0.75) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            transition: all 0.25s ease;
        }
        
        .stSelectbox div[data-baseweb="select"]:hover {
            border-color: #ffb000 !important;
            box-shadow: 0 0 10px rgba(255, 176, 0, 0.15) !important;
        }
        
        .stTextInput input {
            background-color: rgba(18, 24, 38, 0.75) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            transition: all 0.25s ease;
        }
        
        .stTextInput input:focus {
            border-color: #ffb000 !important;
            box-shadow: 0 0 10px rgba(255, 176, 0, 0.2) !important;
        }

        /* Custom styling for tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background-color: transparent;
            padding: 5px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 48px;
            white-space: pre-wrap;
            background-color: rgba(18, 24, 38, 0.5);
            border-radius: 8px 8px 0px 0px;
            color: #94a3b8;
            font-weight: 600;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-bottom: none;
            padding: 8px 24px;
            transition: all 0.25s ease;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: #ffb000;
            background-color: rgba(30, 41, 59, 0.7);
        }

        .stTabs [aria-selected="true"] {
            background-color: rgba(30, 41, 59, 0.8) !important;
            color: #ffb000 !important;
            border-top: 3px solid #ffb000 !important;
            box-shadow: 0 -4px 15px rgba(255, 176, 0, 0.1) !important;
        }
        
        /* Futuristic gradient button styling */
        .stButton>button {
            background: linear-gradient(135deg, rgba(25, 35, 56, 0.8) 0%, rgba(13, 18, 28, 0.8) 100%) !important;
            backdrop-filter: blur(8px);
            color: #ffffff !important;
            border: 1px solid rgba(255, 176, 0, 0.25) !important;
            border-radius: 8px !important;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            padding: 10px 24px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        }
        
        .stButton>button:hover {
            background: linear-gradient(135deg, #ffb000 0%, #ff8c00 100%) !important;
            color: #06080e !important;
            border-color: #ffb000 !important;
            box-shadow: 0 8px 25px rgba(255, 176, 0, 0.35) !important;
            transform: translateY(-2px);
        }

        /* Expander overrides */
        .streamlit-expanderHeader {
            background-color: rgba(18, 24, 38, 0.5) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 8px !important;
        }

        /* Disclaimer footer styles */
        .disclaimer-footer {
            margin-top: 60px;
            padding-top: 25px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            text-align: center;
            font-size: 0.8rem;
            color: #64748b;
        }
    </style>
    """
    st.markdown(bloomberg_css, unsafe_allow_html=True)

