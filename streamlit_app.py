import streamlit as st
import pandas as pd
import google.generativeai as genai
from PyPDF2 import PdfReader
import os
import glob
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. OREGON BRANDED THEME & UI ---
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
LEDGER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"
PLANNING_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Spring+term+FP%26A"

@st.cache_data(ttl=60)
def load_sheet_data(url, skip=0):
    try:
        df = pd.read_csv(url, skiprows=skip)
        df.columns = [str(col).strip() for col in df.columns]
        return df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    except:
        return None

def load_permanent_knowledge():
    combined_text = ""
    kb_path = "knowledge_base"
    if not os.path.exists(kb_path): return "", []
    files = [os.path.join(kb_path, f) for f in os.listdir(kb_path) if f.lower().endswith(('.pdf', '.txt'))]
    for f_path in files:
        try:
            if f_path.endswith(".pdf"):
                reader = PdfReader(f_path)
                combined_text += "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
            else:
                with open(f_path, "r", encoding="utf-8") as f: combined_text += f.read()
        except: pass
    return combined_text, files

# --- 3. AUTH & SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=100)
    st.markdown("<h2 style='text-align: center; color: #fee123;'>Treasurer Hub</h2>", unsafe_allow_html=True)
    access_code = st.text_input("Access Code", type="password")
    
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("API Key missing!")
        st.stop()

    st.markdown("---")
    session_files = st.file_uploader("📂 Session Docs", type="pdf", accept_multiple_files=True)
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. MAIN APP ---
if access_code == "AICLUBTREASURE":
    genai.configure(api_key=api_key)
    if "messages" not in st.session_state: st.session_state.messages = []

    # Load Data (Spring term FP&A needs to skip 3 rows to reach headers on Row 4)
    df_ledger = load_sheet_data(LEDGER_URL, skip=0)
    df_plan = load_sheet_data(PLANNING_URL, skip=3)
    kb_text, kb_files = load_permanent_knowledge()
    
    session_text = ""
    if session_files:
        for f in session_files:
            reader = PdfReader(f)
            for page in reader.pages: session_text += (page.extract_text() or "") + "\n"

    st.markdown("<h1 style='text-align: center; color: #fee123; margin-bottom: 0;'>DUCKS AI TREASURY</h1>", unsafe_allow_html=True)

    # TOP METRICS
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("LEDGER", "SYNCED 🟢")
    with m2: st.metric("FP&A PLAN", "ACTIVE 🟢")
    with m3: st.metric("KNOWLEDGE", len(kb_files), "DOCS")
    with m4: st.metric("STATUS", "AUTH VERIFIED")

    tab1, tab2, tab3 = st.tabs(["💬 Strategic Chat", "📅 Planning & Deadlines", "🏛️ Repository"])

    with tab1:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if query := st.chat_input("Ask a strategic question..."):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)

            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(available_models[0])
                
                # --- NEW STRICT HIERARCHY PROMPT ---
                system_prompt = f"""
                ROLE: Strategic Executive Treasurer for UO AI Club.
                
                DATA HIERARCHY (Follow strictly):
                1. PRIORITY 1: The 'Spring term FP&A' Spreadsheet. If a date is written here (e.g. Catering Waiver column), THIS IS THE ONLY TRUTH.
                2. PRIORITY 2: The 'Sheet1' Ledger for current balances.
                3. PRIORITY 3: Uploaded Handbook PDFs. Use these ONLY for general advice or if the spreadsheet is missing a date.

                INSTRUCTIONS:
                - If asked about a deadline, find the 'Event' in the FP&A sheet first. 
                - Look for the column 'Catering Waiver' or 'Long Form PO due date' for that event.
                - DO NOT calculate a date if one is already provided in the spreadsheet.
                - If the spreadsheet says the first meeting is 4/6/2026, then 4/6/2026 is the date. 

                CONTEXT:
                - LEDGER: {df_ledger.to_string() if df_ledger is not None else "Empty"}
                - SPRING PLAN (FP&A): {df_plan.to_string() if df_plan is not None else "Empty"}
                - HANDBOOK RULES: {kb_text[:8000]}
                """
                
                with st.spinner("Checking Spreadsheet..."):
                    response = model.generate_content(f"{system_prompt}\n\nUSER QUESTION: {query}")
                    ai_resp = response.text
                
                with st.chat_message("assistant"): st.markdown(ai_resp)
                st.session_state.messages.append({"role": "assistant", "content": ai_resp})
            except Exception as e:
                st.error(f"System Error: {e}")

    with tab2:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader("🗓️ Spring Term FP&A Tracker")
            if df_plan is not None:
                st.dataframe(df_plan, use_container_width=True)
                num_cols = df_plan.select_dtypes(include=['number']).columns
                if 'Event' in df_plan.columns and len(num_cols) > 0:
                    fig = px.bar(df_plan, x='Event', y=num_cols[0], template="plotly_dark", color_discrete_sequence=['#fee123'])
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("🚨 ASUO Priority Alarms")
            if df_plan is not None:
                try:
                    for _, row in df_plan.iterrows():
                        po_col = 'Long Form PO due date'
                        if po_col in df_plan.columns and pd.notnull(row[po_col]):
                            po_date = pd.to_datetime(row[po_col])
                            days_to_po = (po_date - datetime.now()).days
                            if days_to_po < 10 and days_to_po >= 0:
                                st.warning(f"**{row.get('Event', 'Meeting')}**\nPO DUE: {po_date.date()} ({days_to_po} days!)")
                            elif days_to_po < 0:
                                st.error(f"**{row.get('Event', 'Meeting')}**\nPO OVERDUE: {po_date.date()}")
                except: pass

    with tab3:
        st.subheader("🏛️ Knowledge Base")
        if kb_files:
            for f in kb_files: st.write(f"✅ **{os.path.basename(f)}**")

else:
    st.info("Enter the Access Code in the sidebar.")
