import streamlit as st
import pandas as pd
import google.generativeai as genai
from PyPDF2 import PdfReader
import os
import glob
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. OREGON BRANDED THEME & PREMIUM UI ---
st.set_page_config(page_title="UO AI Club Treasury Hub", layout="wide", page_icon="🦆")

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

    /* Metric Cards: Glassmorphism */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border-left: 5px solid #fee123;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    
    /* Buttons: UO Yellow */
    .stButton>button {
        background-color: #fee123 !important;
        color: #124734 !important;
        border-radius: 12px;
        font-weight: 800;
        text-transform: uppercase;
        width: 100%;
        transition: 0.3s all;
    }
    .stButton>button:hover {
        background-color: #ffffff !important;
        box-shadow: 0 0 20px #fee123;
    }

    /* Chat Bubbles */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(254, 225, 35, 0.2) !important;
        border-radius: 15px !important;
    }

    /* Markdown Table Styling */
    table { width: 100%; color: white !important; border-collapse: collapse; }
    th { background-color: rgba(254, 225, 35, 0.2); }
    td, th { border: 1px solid rgba(255,255,255,0.1); padding: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA SOURCE CONFIG ---
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

# --- 3. AUTH & SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=100)
    st.markdown("<h2 style='text-align: center; color: #fee123;'>Treasurer Hub</h2>", unsafe_allow_html=True)
    
    access_code = st.text_input("Access Code", type="password")
    
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("API Key missing in Secrets Vault!")
        st.stop()

    st.markdown("---")
    session_files = st.file_uploader("📂 Session Docs", type="pdf", accept_multiple_files=True)
    
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. MAIN APP LOGIC ---
if access_code == "AICLUBTREASURE":
    genai.configure(api_key=api_key)
    if "messages" not in st.session_state: st.session_state.messages = []

    # Background Data Sync
    df_ledger = load_sheet_data(LEDGER_URL)
    df_plan = load_sheet_data(PLANNING_URL)
    kb_text, kb_files = load_permanent_knowledge()
    
    session_text = ""
    if session_files:
        for f in session_files:
            reader = PdfReader(f)
            for page in reader.pages: session_text += page.extract_text() + "\n"

    # MAIN HEADER
    st.markdown("<h1 style='text-align: center; color: #fee123; margin-bottom: 0;'>DUCKS AI TREASURY</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.8;'>University of Oregon AI Club | Strategic Advisor</p>", unsafe_allow_html=True)

    # TOP METRICS
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("LEDGER", "SYNCED 🟢")
    with m2: st.metric("FP&A PLAN", "ACTIVE 🟢")
    with m3: st.metric("KNOWLEDGE", len(kb_files), "DOCS")
    with m4: st.metric("STATUS", "SECURE")

    tab1, tab2, tab3 = st.tabs(["💬 Strategic Chat", "📅 Planning & Deadlines", "🏛️ Repository"])

    # --- TAB 1: STRATEGIC CHAT ---
    with tab1:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if query := st.chat_input("How can I help you grow the club today?"):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)

            try:
                # Select best model
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(available_models[0])
                
                # --- ENHANCED STRATEGIC TREASURER PROMPT ---
                system_prompt = f"""
                ROLE: You are the Strategic Executive Treasurer for the UO AI Club.
                MISSION: Provide advice that anchors member growth and attendance goals in ACTUAL financial data.

                STRICT STRUCTURE:
                1. **Strategic Goal**: Direct answer to the user's question.
                2. **Financial Analysis**: A Markdown Table showing relevant Budget Items, Available Funds, and Proposed Costs based on the LEDGER.
                3. **Treasurer's Advice**: Assess if the move is 'Low Risk' or 'High Risk' based on the surplus/deficit.
                4. **ASUO Compliance**: Point out a specific deadline from the SPRING PLAN (FP&A) or a Rule from the HANDBOOK.

                STRICT FORMATTING:
                - Use Bold Headers.
                - NEVER merge numbers into text (e.g., "$200Available"). Always use clear spacing.
                - Limit total response to 250 words.
                - Use 'Oregon Ducks' terminology when appropriate.

                DATA CONTEXT:
                - LEDGER: {df_ledger.to_string() if df_ledger is not None else "Empty"}
                - SPRING PLAN: {df_plan.to_string() if df_plan is not None else "Empty"}
                - RULES: {kb_text[:10000]}
                """
                
                with st.spinner("Consulting Ledger & ASUO Policies..."):
                    response = model.generate_content(f"{system_prompt}\n\nUSER QUESTION: {query}")
                    ai_resp = response.text
                
                with st.chat_message("assistant"): st.markdown(ai_resp)
                st.session_state.messages.append({"role": "assistant", "content": ai_resp})
            except Exception as e:
                st.error(f"System Error: {e}")

    # --- TAB 2: PLANNING & DEADLINES ---
    with tab2:
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader("🗓️ Spring Term FP&A Tracker")
            st.dataframe(df_plan, use_container_width=True)
            if df_plan is not None:
                num_cols = df_plan.select_dtypes(include=['number']).columns
                if len(num_cols) > 0:
                    fig = px.bar(df_plan, x=df_plan.columns[0], y=num_cols[0], template="plotly_dark", color_discrete_sequence=['#fee123'])
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("🚨 ASUO Priority Alarms")
            if df_plan is not None and 'Date' in df_plan.columns:
                try:
                    for _, row in df_plan.iterrows():
                        ev_date = pd.to_datetime(row['Date'])
                        deadline = ev_date - timedelta(days=14)
                        days_left = (deadline - datetime.now()).days
                        if days_left < 10 and days_left > 0:
                            st.warning(f"**{row['Event']}**\nSubmit RTP by: {deadline.date()} ({days_left} days left!)")
                        elif days_left <= 0:
                            st.error(f"**{row['Event']}**\nDEADLINE PASSED on {deadline.date()}")
                        else:
                            st.success(f"**{row['Event']}**\nDeadline: {deadline.date()}")
                except: st.info("Add 'Date' and 'Event' columns to FP&A sheet to activate Alarms.")

    # --- TAB 3: REPOSITORY ---
    with tab3:
        st.subheader("🏛️ Knowledge Base Documents")
        if kb_files:
            for f in kb_files: st.write(f"✅ **{os.path.basename(f)}**")
        else:
            st.info("No documents found in GitHub 'knowledge_base'.")

else:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=150)
        st.markdown("<h2 style='text-align: center; color: #fee123;'>AUTHENTICATION REQUIRED</h2>", unsafe_allow_html=True)
        st.info("Enter the Treasurer Access Code in the sidebar.")
