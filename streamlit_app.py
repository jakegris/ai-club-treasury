import streamlit as st
import pandas as pd
import google.generativeai as genai
from PyPDF2 import PdfReader
import os
import glob
import plotly.express as px
from datetime import datetime

# --- 1. THEME & UI ---
st.set_page_config(page_title="UO AI Club Treasury Hub", layout="wide", page_icon="🦆")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #124734 0%, #072219 100%); color: #f0f0f0; }
    [data-testid="stSidebar"] { background-color: rgba(10, 40, 30, 0.8) !important; backdrop-filter: blur(12px); border-right: 2px solid #fee123; }
    div[data-testid="stMetric"] { background: rgba(255, 255, 255, 0.05); border-left: 5px solid #fee123; padding: 20px; border-radius: 10px; }
    .stButton>button { background-color: #fee123 !important; color: #124734 !important; border-radius: 12px; font-weight: 800; text-transform: uppercase; width: 100%; }
    [data-testid="stChatMessage"] { background: rgba(255, 255, 255, 0.04) !important; border: 1px solid rgba(254, 225, 35, 0.2) !important; border-radius: 15px !important; }
    table { width: 100%; color: white !important; border-collapse: collapse; }
    th { background-color: rgba(254, 225, 35, 0.2); }
    td, th { border: 1px solid rgba(255,255,255,0.1); padding: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA SOURCE CONFIG ---
SHEET_ID = "1xHaK_bcyCsQButBmceqd2-BippPWVVZYsUbwHlN0jEM"
LEDGER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=0"
PLANNING_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=2020294064"

@st.cache_data(ttl=30)
def load_ledger_pro(url):
    try:
        # Load raw
        df_raw = pd.read_csv(url, header=None)
        
        # Search for the row containing "Administrative" or "Advertising" to find the header start
        header_idx = 0
        for i, row in df_raw.iterrows():
            if any(x in str(row.values) for x in ["Administrative", "Advertising", "AI workshops"]):
                header_idx = i - 1 if i > 0 else 0
                break
        
        # Reload with proper headers
        df = pd.read_csv(url, skiprows=header_idx)
        df.columns = [str(c).strip() for c in df.columns]
        
        # CLEANING: Find the 'Category' column (it's the one with text names)
        # Find the 'Budget' columns (they have numbers or $)
        for col in df.columns:
            if df[col].dtype == 'object':
                # Convert currency strings "$3,000.00" -> 3000.0
                clean_col = df[col].replace(r'[\$,\s]', '', regex=True)
                df[col + "_NUM"] = pd.to_numeric(clean_col, errors='coerce')
        
        return df.dropna(how='all', axis=0)
    except:
        return None

@st.cache_data(ttl=30)
def load_fp_and_a(url):
    try:
        # Your planning tab starts at row 4
        df = pd.read_csv(url, skiprows=3) 
        df.columns = [str(c).strip() for c in df.columns]
        return df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    except:
        return None

# --- 3. MAIN APP LOGIC ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=100)
    access_code = st.text_input("Access Code", type="password")
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("Missing API Key!"); st.stop()
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()

if access_code == "AICLUBTREASURE":
    genai.configure(api_key=api_key)
    if "messages" not in st.session_state: st.session_state.messages = []

    # DATA SYNC
    df_ledger = load_ledger_pro(LEDGER_URL)
    df_plan = load_fp_and_a(PLANNING_URL)
    
    st.markdown("<h1 style='text-align: center; color: #fee123; margin-bottom: 0;'>DUCKS AI TREASURY</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["💬 Strategic Chat", "📅 Live Planning"])

    with tab1:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if query := st.chat_input("Ex: Calculate budget per meeting for AI Workshops"):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)

            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(available_models[0])
                
                # --- DATA FLATTENING FOR AI ---
                # We extract the specific row for AI workshops to make it impossible to miss
                if df_ledger is not None:
                    # Look for row containing AI workshops
                    mask = df_ledger.apply(lambda row: row.astype(str).str.contains('AI workshop', case=False).any(), axis=1)
                    ai_row = df_ledger[mask]
                    ledger_context = ai_row.to_string() if not ai_row.empty else df_ledger.to_string()
                else:
                    ledger_context = "Ledger not found."

                system_prompt = f"""
                ROLE: UO AI Club Executive Treasurer Advisor.
                
                LEDGER DATA (CRITICAL): 
                {ledger_context}
                
                PLANNING DATA: 
                {df_plan.to_string() if df_plan is not None else "Plan not found."}

                INSTRUCTIONS:
                - ALWAYS perform the math. If you see a number like 3055.88 associated with 'AI workshops', use it.
                - STEP 1: Identify the total budget for the category mentioned.
                - STEP 2: Count the unique meeting dates in the Planning Data.
                - STEP 3: Divide the budget by the count. 
                - Format your answer with a Markdown table and a 'Treasurer's Recommendation'.
                - Be a proud Oregon Duck!
                """
                
                with st.spinner("Quacking the numbers..."):
                    response = model.generate_content(f"{system_prompt}\n\nUSER QUESTION: {query}")
                    ai_resp = response.text
                
                with st.chat_message("assistant"): st.markdown(ai_resp)
                st.session_state.messages.append({"role": "assistant", "content": ai_resp})
            except Exception as e:
                st.error(f"AI System Error: {e}")

    with tab2:
        st.subheader("🗓️ Current FP&A Schedule")
        if df_plan is not None:
            st.dataframe(df_plan, use_container_width=True)
            with st.expander("📂 Ledger Raw View (Search for AI workshops)"):
                st.dataframe(df_ledger)
        else:
            st.error("Connection Error.")
else:
    st.info("Enter Access Code in the sidebar.")
