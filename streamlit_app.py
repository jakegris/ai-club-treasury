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
# Using GIDs to ensure we hit the right tabs
LEDGER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=0"
PLANNING_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=2020294064"

@st.cache_data(ttl=30)
def smart_load_sheet(url, search_term):
    """Scans the sheet to find where the real data starts based on a search term (e.g. 'Date')"""
    try:
        raw_df = pd.read_csv(url, header=None)
        start_row = 0
        for i, row in raw_df.iterrows():
            if search_term in str(row.values):
                start_row = i
                break
        
        # Reload with proper headers
        df = pd.read_csv(url, skiprows=start_row)
        df.columns = [str(c).strip() for c in df.columns]
        # Drop empty columns and rows
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.dropna(how='all', axis=0)
        
        # Clean currency for ledger
        if search_term != "Date": # This is the Ledger
            for col in df.columns:
                if df[col].dtype == 'object':
                    clean_val = df[col].replace(r'[\$,\s]', '', regex=True)
                    df[col] = pd.to_numeric(clean_val, errors='ignore')
        return df
    except:
        return None

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=100)
    access_code = st.text_input("Access Code", type="password")
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("Missing API Key!"); st.stop()

# --- 4. MAIN APP ---
if access_code == "AICLUBTREASURE":
    genai.configure(api_key=api_key)
    if "messages" not in st.session_state: st.session_state.messages = []

    # LOAD DATA USING SMART SEARCH
    df_ledger = smart_load_sheet(LEDGER_URL, "Advertising") # Ledger usually has Advertising
    df_plan = smart_load_sheet(PLANNING_URL, "Date") # Planning has Date
    
    st.markdown("<h1 style='text-align: center; color: #fee123; margin-bottom: 0;'>DUCKS AI TREASURY</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["💬 Strategic Chat", "📅 Live Planning"])

    with tab1:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if query := st.chat_input("Ex: Calculate budget for all spring meetings..."):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)

            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(available_models[0])
                
                # --- STRATEGIC PROMPT ---
                system_prompt = f"""
                ROLE: UO AI Club Executive Treasurer Advisor.
                
                TRUTH CHECK:
                - The Spring Term officially begins with the meeting on 4/6/2026.
                - DO NOT skip the first rows of the data. 
                - Count EVERY meeting listed in the FP&A table below, starting from the very first row.

                SPRING TERM FP&A (Event Schedule): 
                {df_plan.to_string() if df_plan is not None else "Plan Error"}

                LEDGER DATA (Budgets): 
                {df_ledger.to_string() if df_ledger is not None else "Ledger Error"}

                INSTRUCTIONS:
                1. Look at the FIRST ROW of the FP&A table. Is it 4/6/2026? Use it.
                2. Count the total number of meetings (it should be 9 meetings total).
                3. Find the 'AI Workshops' budget in the Ledger (Approx $3,055).
                4. Divide that budget by the TOTAL number of meetings.
                5. Show your math in a table.
                """
                
                with st.spinner("Analyzing full term schedule..."):
                    response = model.generate_content(f"{system_prompt}\n\nUSER QUESTION: {query}")
                    ai_resp = response.text
                
                with st.chat_message("assistant"): st.markdown(ai_resp)
                st.session_state.messages.append({"role": "assistant", "content": ai_resp})
            except Exception as e:
                st.error(f"AI System Error: {e}")

    with tab2:
        st.subheader("🗓️ Spring Term Schedule")
        if df_plan is not None:
            st.dataframe(df_plan, use_container_width=True)
            # Display a confirmation so you know it sees row 1
            st.success(f"**Confirmation:** The bot detects the first meeting is on **{df_plan.iloc[0].get('Date', 'Unknown')}**.")
        else:
            st.error("Check Google Sheet Connection.")
else:
    st.info("Enter Access Code in the sidebar.")
