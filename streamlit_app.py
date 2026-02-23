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
def load_and_clean_ledger(url):
    try:
        # Load raw data
        df = pd.read_csv(url, header=None)
        
        # FIND THE REAL DATA: Look for the row containing "Advertising" or "AI Workshops"
        # This fixes the "Unnamed Column" and "Merged Cell" issues
        data_start_row = 0
        for i, row in df.iterrows():
            row_str = " ".join(map(str, row.values))
            if "Advertising" in row_str or "Administrative" in row_str:
                data_start_row = i
                break
        
        # Re-load from that row
        df = pd.read_csv(url, skiprows=data_start_row)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Clean up empty columns
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Clean currency columns: remove $, commas, and turn to numbers
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].replace(r'[\$,\s]', '', regex=True)
                # Attempt to convert to numeric, ignore errors for category names
                df[col] = pd.to_numeric(df[col], errors='ignore')
        
        return df.dropna(how='all', axis=0)
    except:
        return None

@st.cache_data(ttl=30)
def load_fp_and_a(url):
    try:
        df = pd.read_csv(url, skiprows=3) # Your planning tab starts at row 4
        df.columns = [str(c).strip() for c in df.columns]
        return df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    except:
        return None

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=100)
    access_code = st.text_input("Access Code", type="password")
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("Missing API Key in Secrets Vault!")
        st.stop()
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. MAIN APP ---
if access_code == "AICLUBTREASURE":
    genai.configure(api_key=api_key)
    if "messages" not in st.session_state: st.session_state.messages = []

    # LOAD DATA
    df_ledger = load_and_clean_ledger(LEDGER_URL)
    df_plan = load_fp_and_a(PLANNING_URL)
    
    st.markdown("<h1 style='text-align: center; color: #fee123; margin-bottom: 0;'>DUCKS AI TREASURY</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["💬 Strategic Chat", "📅 Live Planning"])

    with tab1:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if query := st.chat_input("Ex: How much can we spend per meeting on pizza?"):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)

            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(available_models[0])
                
                # --- EXECUTIVE MATH PROMPT ---
                system_prompt = f"""
                ROLE: UO AI Club Executive Treasurer.
                
                DATA:
                1. LEDGER (Budget Sources): 
                {df_ledger.to_string() if df_ledger is not None else "Ledger Error"}
                
                2. FP&A (Spring Event Schedule): 
                {df_plan.to_string() if df_plan is not None else "Plan Error"}

                INSTRUCTIONS:
                - You are an expert at spreadsheet math. 
                - If the user asks for a 'per meeting' calculation:
                    1. Find the Budget Category in the LEDGER (usually in a column like 'Adjusted Budget' or similar).
                    2. Count the number of 'Meetings' or 'Workshops' in the FP&A PLAN.
                    3. DIVIDE the total budget by the number of meetings.
                    4. SHOW THE MATH clearly in a table.
                - Don't give up. If you see 'AI workshops' and a number like '3055.88' anywhere in the same row, USE IT.
                - Use Oregon Ducks terminology.
                """
                
                with st.spinner("Calculating Financial Strategy..."):
                    response = model.generate_content(f"{system_prompt}\n\nUSER QUESTION: {query}")
                    ai_resp = response.text
                
                with st.chat_message("assistant"): st.markdown(ai_resp)
                st.session_state.messages.append({"role": "assistant", "content": ai_resp})
            except Exception as e:
                st.error(f"AI Error: {e}")

    with tab2:
        st.subheader("🗓️ Current FP&A Schedule")
        if df_plan is not None:
            st.dataframe(df_plan, use_container_width=True)
            with st.expander("📂 View Cleaned Ledger (Verify Numbers)"):
                st.dataframe(df_ledger)
        else:
            st.error("Check Google Sheet Connection.")

else:
    st.info("Enter Access Code in the sidebar.")
