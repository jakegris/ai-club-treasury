import streamlit as st
import pandas as pd
import google.generativeai as genai
from PyPDF2 import PdfReader
import os
import glob
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. OREGON BRANDED THEME & UI ---
st.set_page_config(page_title="AI Club Treasury Hub", layout="wide", page_icon="🦆")

st.markdown("""
    <style>
    /* Main Background: Oregon Green Gradient */
    .stApp {
        background: linear-gradient(135deg, #124734 0%, #072219 100%);
        color: #f0f0f0;
    }
    
    /* Sidebar: Frosted Glass */
    [data-testid="stSidebar"] {
        background-color: rgba(10, 40, 30, 0.8) !important;
        backdrop-filter: blur(12px);
        border-right: 2px solid #fee123;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border-left: 5px solid #fee123;
        padding: 20px;
        border-radius: 10px;
    }
    
    /* Buttons: UO Yellow */
    .stButton>button {
        background-color: #fee123 !important;
        color: #124734 !important;
        border-radius: 12px;
        font-weight: 800;
        text-transform: uppercase;
        width: 100%;
    }

    /* Chat Bubbles */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(254, 225, 35, 0.2) !important;
        border-radius: 15px !important;
        padding: 15px;
    }
    
    /* Style for AI Tables */
    table { color: white !important; background-color: rgba(255,255,255,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADERS ---
SHEET_ID = "1xHaK_bcyCsQButBmceqd2-BippPWVVZYsUbwHlN0jEM"
LEDGER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"
PLANNING_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Spring+Term+FP%26A"

@st.cache_data(ttl=60)
def load_sheet_data(url):
    try:
        df = pd.read_csv(url)
        return df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    except: return None

def load_permanent_knowledge():
    combined_text = ""
    kb_path = "knowledge_base"
    if not os.path.exists(kb_path): return "", []
    files = [os.path.join(kb_path, f) for f in os.listdir(kb_path) if f.lower().endswith(('.pdf', '.txt'))]
    for f_path in files:
        try:
            if f_path.endswith(".pdf"):
                reader = PdfReader(f_path); combined_text += "\n".join([p.extract_text() for p in reader.pages])
            else:
                with open(f_path, "r") as f: combined_text += f.read()
        except: pass
    return combined_text, files

# --- 3. AUTHENTICATION & SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=100)
    st.markdown("<h2 style='text-align: center; color: #fee123;'>Treasurer Portal</h2>", unsafe_allow_html=True)
    
    access_code = st.text_input("Enter Access Code", type="password")
    
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("API Key missing in Streamlit Secrets!")
        st.stop()

    st.markdown("---")
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. MAIN HUB ---
if access_code == "AICLUBTREASURE":
    genai.configure(api_key=api_key)
    if "messages" not in st.session_state: st.session_state.messages = []

    # Load All Data
    df_ledger = load_sheet_data(LEDGER_URL)
    df_plan = load_sheet_data(PLANNING_URL)
    kb_text, kb_files = load_permanent_knowledge()

    st.markdown("<h1 style='text-align: center; color: #fee123; margin-bottom: 0;'>DUCKS AI TREASURY</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.7;'>Strategic Financial Advisor | University of Oregon</p>", unsafe_allow_html=True)

    # METRICS
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("LEDGER", "SYNCED", "LIVE")
    with m2: st.metric("SPRING PLAN", "ACTIVE", "FP&A")
    with m3: st.metric("KNOWLEDGE", len(kb_files), "DOCS")
    with m4: st.metric("AUTH", "VERIFIED")

    tab1, tab2, tab3 = st.tabs(["💬 Strategy Chat", "📅 Deadlines & FP&A", "🏛️ Repository"])

    # --- TAB 1: EXECUTIVE CHAT ---
    with tab1:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if query := st.chat_input("Ask a strategic question..."):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)

            try:
                # Find available model
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(available_models[0])
                
                # --- THE STRICT SYSTEM PROMPT (Fixes jumbled words/length) ---
                system_prompt = f"""
                ROLE: You are the Executive Treasurer Advisor for the UO AI Club.
                PERSONALITY: Professional, concise, and strategic.
                
                STRICT FORMATTING RULES:
                1. Use **Bold Headers** for different sections.
                2. Use Bullet Points for lists.
                3. If providing numbers, use a Markdown Table.
                4. NEVER merge numbers into text sentences (e.g., instead of "We have $200 for pizza", use "Pizza Budget: $200").
                5. LIMIT: Keep responses under 250 words.
                6. FOCUS: Only answer the specific question asked. Do not list unrelated budget items.

                CONTEXT:
                - LEDGER: {df_ledger.to_string() if df_ledger is not None else "Empty"}
                - SPRING PLAN: {df_plan.to_string() if df_plan is not None else "Empty"}
                - RULES: {kb_text[:5000]}
                """
                
                with st.spinner("Analyzing..."):
                    response = model.generate_content(f"{system_prompt}\n\nUSER QUESTION: {query}")
                    ai_text = response.text
                
                with st.chat_message("assistant"): st.markdown(ai_text)
                st.session_state.messages.append({"role": "assistant", "content": ai_text})
            except Exception as e:
                st.error(f"System Error: {e}")

    # --- TAB 2: PLANNING & DEADLINES ---
    with tab2:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader("🗓️ Spring Term FP&A Sheet")
            st.dataframe(df_plan, use_container_width=True)
        
        with col_right:
            st.subheader("🚨 Priority Deadlines")
            if df_plan is not None and 'Date' in df_plan.columns:
                try:
                    for _, row in df_plan.iterrows():
                        ev_date = pd.to_datetime(row['Date'])
                        deadline = ev_date - timedelta(days=14)
                        days_left = (deadline - datetime.now()).days
                        if days_left < 10:
                            st.error(f"**{row['Event']}**\nSubmit RTP by: {deadline.date()} ({days_left} days left!)")
                        else:
                            st.success(f"**{row['Event']}**\nDeadline: {deadline.date()}")
                except: st.info("Ensure FP&A sheet has 'Date' and 'Event' columns.")

    # --- TAB 3: KNOWLEDGE BASE ---
    with tab3:
        st.subheader("🏛️ Permanent Knowledge Repository")
        if kb_files:
            for f in kb_files: st.write(f"✅ **{os.path.basename(f)}**")
        else:
            st.warning("No documents found in GitHub 'knowledge_base' folder.")

else:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=150)
        st.markdown("<h2 style='text-align: center; color: #fee123;'>TREASURY AUTHENTICATION</h2>", unsafe_allow_html=True)
        st.info("Please enter the Access Code in the sidebar to enter the Treasury Hub.")
