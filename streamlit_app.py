import streamlit as st
import pandas as pd
import google.generativeai as genai
from PyPDF2 import PdfReader
import os
import glob
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. OREGON BRANDED THEME ---
st.set_page_config(page_title="AI Club Treasury Hub", layout="wide", page_icon="🦆")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #124734 0%, #072219 100%); color: #f0f0f0; }
    [data-testid="stSidebar"] { background-color: rgba(10, 40, 30, 0.8) !important; backdrop-filter: blur(12px); border-right: 2px solid #fee123; }
    div[data-testid="stMetric"] { background: rgba(255, 255, 255, 0.05); border-left: 5px solid #fee123; padding: 20px; border-radius: 10px; }
    .stButton>button { background-color: #fee123 !important; color: #124734 !important; border-radius: 12px; font-weight: 800; text-transform: uppercase; width: 100%; }
    .stChatMessage { background: rgba(255, 255, 255, 0.04) !important; border: 1px solid rgba(254, 225, 35, 0.2) !important; border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA SOURCE CONFIG ---
SHEET_ID = "1xHaK_bcyCsQButBmceqd2-BippPWVVZYsUbwHlN0jEM"
# Ledger Tab
LEDGER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"
# Planning Tab
PLANNING_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Spring+Term+FP%26A"

# --- 3. HELPER FUNCTIONS ---
@st.cache_data(ttl=60)
def load_sheet_data(url):
    try:
        df = pd.read_csv(url)
        return df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    except: return None

def load_permanent_knowledge():
    combined_text = ""
    kb_path = "knowledge_base"
    if not os.path.exists(kb_path): return "", [], "No KB folder."
    files = [os.path.join(kb_path, f) for f in os.listdir(kb_path) if f.lower().endswith(('.pdf', '.txt'))]
    for f_path in files:
        try:
            if f_path.endswith(".pdf"):
                reader = PdfReader(f_path); combined_text += "\n".join([p.extract_text() for p in reader.pages])
            else:
                with open(f_path, "r") as f: combined_text += f.read()
        except: pass
    return combined_text, files, "Success"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=100)
    password = st.text_input("Access Code", type="password")
    if "GEMINI_API_KEY" in st.secrets: api_key = st.secrets["GEMINI_API_KEY"]
    else: st.error("Add GEMINI_API_KEY to Secrets!"); st.stop()
    st.markdown("---")
    if st.button("Reset Session"): st.session_state.messages = []; st.rerun()

# --- 5. APP MAIN ---
if password == "AICLUBTREASURE":
    genai.configure(api_key=api_key)
    if "messages" not in st.session_state: st.session_state.messages = []

    # Load Data
    df_ledger = load_sheet_data(LEDGER_URL)
    df_plan = load_sheet_data(PLANNING_URL)
    perm_text, perm_files, _ = load_permanent_knowledge()

    st.markdown("<h1 style='text-align: center; color: #fee123;'>DUCKS AI TREASURY</h1>", unsafe_allow_html=True)

    # TOP METRICS
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("LEDGER", "SYNCED", "LIVE")
    with m2: st.metric("SPRING PLAN", "ACTIVE", "FP&A")
    with m3: st.metric("KNOWLEDGE", len(perm_files), "FILES")
    with m4: st.metric("STATUS", "SECURE")

    tab1, tab2, tab3 = st.tabs(["💬 Financial Chat", "📅 Planning & Deadlines", "🧠 Knowledge Base"])

    # --- TAB 1: CHAT ---
    with tab1:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if query := st.chat_input("Ask about a deadline or budget..."):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)

            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(available_models[0])
                
                # We feed the AI BOTH the current spending and the future plans
                context = f"""
                LEDGER (Current Spending): {df_ledger.to_string() if df_ledger is not None else 'None'}
                SPRING PLAN (FP&A): {df_plan.to_string() if df_plan is not None else 'None'}
                HANDBOOK RULES: {perm_text[:15000]}
                """
                full_prompt = f"System: You are the UO AI Club Treasurer. Help with Spring Term planning. {context}\nUser: {query}"
                
                with st.spinner("Analyzing Ledger & Plans..."):
                    response = model.generate_content(full_prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    with st.chat_message("assistant"): st.markdown(response.text)
            except Exception as e: st.error(f"Error: {e}")

    # --- TAB 2: PLANNING & DEADLINES ---
    with tab2:
        st.subheader("🗓️ Spring Term Deadline Tracker")
        if df_plan is not None:
            # We assume your sheet has columns like 'Event Name', 'Event Date', 'Needs Catering Waiver?'
            st.dataframe(df_plan, use_container_width=True)
            
            st.markdown("### 🚨 Urgent Actions Required")
            # Logic to calculate deadlines (Customizable based on your sheet's column names)
            try:
                for idx, row in df_plan.iterrows():
                    event_date = pd.to_datetime(row['Date'])
                    rtp_deadline = event_date - timedelta(days=14) # 10 biz days
                    waiver_deadline = event_date - timedelta(days=21) # 15 biz days
                    
                    days_to_rtp = (rtp_deadline - datetime.now()).days
                    
                    if days_to_rtp < 7 and days_to_rtp > 0:
                        st.warning(f"**{row['Event']}**: Submit RTP in {days_to_rtp} days! (Due: {rtp_deadline.date()})")
                    elif days_to_rtp <= 0:
                        st.error(f"**{row['Event']}**: RTP DEADLINE PASSED ({rtp_deadline.date()})")
                    else:
                        st.success(f"**{row['Event']}**: RTP due in {days_to_rtp} days.")
            except:
                st.info("Ensure your 'Spring Term FP&A' tab has columns named 'Date' and 'Event' for auto-deadline tracking.")
        else:
            st.warning("Could not find 'Spring Term FP&A' tab. Check your sheet name!")

    # --- TAB 3: KNOWLEDGE ---
    with tab3:
        st.subheader("🏛️ Knowledge Repository")
        for f in perm_files: st.write(f"✅ {os.path.basename(f)}")

else:
    st.info("Enter Access Code in the sidebar.")
