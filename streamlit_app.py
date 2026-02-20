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
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA SOURCE CONFIG ---
SHEET_ID = "1xHaK_bcyCsQButBmceqd2-BippPWVVZYsUbwHlN0jEM"
# Using the specific GID for the Spring Term FP&A tab to be 100% sure
PLANNING_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=2020294064"
LEDGER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=30) # Short TTL for frequent updates
def load_fp_and_a(url):
    try:
        # We skip 3 rows to land on Row 4 (Headers)
        df = pd.read_csv(url, skiprows=3)
        # Force clean column names
        df.columns = [str(c).strip() for c in df.columns]
        # Only keep rows that actually have a Date
        df = df.dropna(subset=['Date'])
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
            for page in reader.pages: text += page.extract_text() + "\n"
        except: pass
    return text

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=100)
    access_code = st.text_input("Access Code", type="password")
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("Missing API Key in Secrets!")
        st.stop()
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. MAIN APP ---
if access_code == "AICLUBTREASURE":
    genai.configure(api_key=api_key)
    if "messages" not in st.session_state: st.session_state.messages = []

    # LOAD DATA
    df_plan = load_fp_and_a(PLANNING_URL)
    df_ledger = pd.read_csv(LEDGER_URL) # Standard ledger
    kb_text = load_kb()

    st.markdown("<h1 style='text-align: center; color: #fee123;'>DUCKS AI TREASURY</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["💬 Strategic Chat", "📅 Live Deadlines"])

    with tab1:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if query := st.chat_input("Ask about a specific deadline..."):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)

            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(available_models[0])
                
                # --- THE "STRICTEST" PROMPT ---
                system_prompt = f"""
                You are the Executive Treasurer for the UO AI Club.
                
                CRITICAL INSTRUCTION: 
                - You MUST use the 'SPRING TERM FP&A' table for all dates.
                - DO NOT calculate dates using rules if a date exists in the table.
                - If the table has a column 'Catering Waiver', THAT DATE is the final answer.
                - The first meeting of Spring Term is in Row 0 of the table below.

                SPRING TERM FP&A TABLE (Current Reality):
                {df_plan.to_string() if df_plan is not None else "Data missing"}

                REFERENCE RULES (Use only for general context):
                {kb_text[:5000]}
                """
                
                with st.spinner("Analyzing Spreadsheet..."):
                    response = model.generate_content(f"{system_prompt}\n\nUSER QUESTION: {query}")
                    ai_resp = response.text
                
                with st.chat_message("assistant"): st.markdown(ai_resp)
                st.session_state.messages.append({"role": "assistant", "content": ai_resp})
            except Exception as e:
                st.error(f"AI Error: {e}")

    with tab2:
        st.subheader("🗓️ Automated Deadline Tracker")
        if df_plan is not None:
            st.dataframe(df_plan, use_container_width=True)
            # This visual alert helps verify the bot sees the same dates you do
            first_row = df_plan.iloc[0]
            st.info(f"**Confirmation:** The system identifies the first meeting as **{first_row['Date']}** with a waiver due date of **{first_row['Catering Waiver']}**.")
        else:
            st.error("Could not load Planning Tab.")

else:
    st.info("Enter Access Code in Sidebar.")
