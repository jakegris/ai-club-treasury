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
def load_and_clean_data(url, skip=0):
    try:
        df = pd.read_csv(url, skiprows=skip)
        # 1. Clean Column Names
        df.columns = [str(c).strip() for c in df.columns]
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.dropna(how='all', axis=0)
        
        # 2. Clean Currency Data (Turns "$1,000" into 1000.0)
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if it looks like money
                if df[col].str.contains('\$', na=False).any():
                    df[col] = df[col].replace('[\$,]', '', regex=True).astype(float, errors='ignore')
        return df
    except:
        return None

def load_kb():
    text = ""
    kb_path = "knowledge_base"
    if not os.path.exists(kb_path): return ""
    for f in glob.glob(os.path.join(kb_path, "*.pdf")):
        try:
            reader = PdfReader(f)
            for page in reader.pages:
                content = page.extract_text()
                if content: text += content + "\n"
        except: pass
    return text

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
    df_ledger = load_and_clean_data(LEDGER_URL, skip=0)
    df_plan = load_and_clean_data(PLANNING_URL, skip=3)
    kb_text = load_kb()

    st.markdown("<h1 style='text-align: center; color: #fee123; margin-bottom: 0;'>DUCKS AI TREASURY</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["💬 Strategic Chat", "📅 Live Planning"])

    with tab1:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if query := st.chat_input("Ex: Calculate pizza budget per meeting..."):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)

            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(available_models[0])
                
                system_prompt = f"""
                ROLE: UO AI Club Executive Treasurer.
                
                DATA ASSETS:
                1. LEDGER (Budget Source): 
                {df_ledger.to_string() if df_ledger is not None else "Ledger missing"}
                
                2. SPRING TERM FP&A (Event Schedule): 
                {df_plan.to_string() if df_plan is not None else "Plan missing"}

                INSTRUCTIONS:
                - You are a MATH-FIRST bot. If asked to calculate "per meeting" costs:
                  a) Count the number of meetings in the FP&A table.
                  b) Find the corresponding 'Adjusted Budget' for that line item in the Ledger.
                  c) Perform the division and show your work in a Markdown Table.
                - Never say you don't have the data if it exists in the tables above. Look for 'AI Workshop' or 'AI Workshops'.
                - All currency is in USD. 

                UO BRAND: Professional, strategic, and Ducks-focused.
                """
                
                with st.spinner("Calculating Financial Scenarios..."):
                    response = model.generate_content(f"{system_prompt}\n\nUSER QUESTION: {query}")
                    ai_resp = response.text
                
                with st.chat_message("assistant"): st.markdown(ai_resp)
                st.session_state.messages.append({"role": "assistant", "content": ai_resp})
            except Exception as e:
                st.error(f"AI System Error: {e}")

    with tab2:
        st.subheader("🗓️ Current FP&A Schedule")
        if df_plan is not None and not df_plan.empty:
            st.dataframe(df_plan, use_container_width=True)
            # Display Ledger in Tab 2 so you can verify the numbers are there
            with st.expander("📂 View Ledger (Budget Sources)"):
                st.dataframe(df_ledger)
        else:
            st.error("Could not load Google Sheet data.")

else:
    st.info("Enter Access Code in the sidebar.")
