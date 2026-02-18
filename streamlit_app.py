import streamlit as st
import pandas as pd
import google.generativeai as genai
from PyPDF2 import PdfReader
import os
import glob
import plotly.express as px

# --- 1. OREGON BRANDED THEME ---
st.set_page_config(page_title="AI Club Treasury Hub", layout="wide", page_icon="🦆")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #124734 0%, #072219 100%);
        color: #f0f0f0;
    }
    [data-testid="stSidebar"] {
        background-color: rgba(10, 40, 30, 0.8) !important;
        backdrop-filter: blur(12px);
        border-right: 2px solid #fee123;
    }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border-left: 5px solid #fee123;
        padding: 20px;
        border-radius: 10px;
    }
    .stButton>button {
        background-color: #fee123 !important;
        color: #124734 !important;
        border-radius: 12px;
        font-weight: 800;
        text-transform: uppercase;
        width: 100%;
    }
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(254, 225, 35, 0.2) !important;
        border-radius: 15px !important;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 3px solid #fee123 !important;
        color: #fee123 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADERS ---
SHEET_ID = "1xHaK_bcyCsQButBmceqd2-BippPWVVZYsUbwHlN0jEM"
LEDGER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"

def load_permanent_knowledge():
    combined_text = ""
    kb_path = "knowledge_base"
    if not os.path.exists(kb_path):
        return "", [], "Knowledge folder not found."
    files = os.listdir(kb_path)
    knowledge_files = [os.path.join(kb_path, f) for f in files if f.lower().endswith(('.pdf', '.txt'))]
    for file_path in knowledge_files:
        try:
            if file_path.lower().endswith(".pdf"):
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text = page.extract_text()
                    if text: combined_text += text + "\n"
            elif file_path.lower().endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    combined_text += f.read() + "\n"
        except: pass
    return combined_text, knowledge_files, "Success"

@st.cache_data(ttl=60)
def load_sheet_data(url):
    try:
        df = pd.read_csv(url)
        return df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    except: return None

# --- 3. SIDEBAR & SECRETS AUTH ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=100)
    st.markdown("<h2 style='text-align: center; color: #fee123;'>Treasurer Admin</h2>", unsafe_allow_html=True)
    
    # User only enters the password
    password = st.text_input("Access Code", type="password")
    
    # System pulls the API key from the "Secrets" vault automatically
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("Missing GEMINI_API_KEY in Streamlit Secrets!")
        st.stop()

    st.markdown("---")
    session_files = st.file_uploader("📂 Temporary Docs", type="pdf", accept_multiple_files=True)
    
    if st.button("Reset Session"):
        st.session_state.messages = []
        st.rerun()

# --- 4. APP INTERFACE ---
if password == "AICLUBTREASURE":
    genai.configure(api_key=api_key)
    if "messages" not in st.session_state: st.session_state.messages = []

    df_ledger = load_sheet_data(LEDGER_URL)
    perm_text, perm_files, _ = load_permanent_knowledge()
    
    session_text = ""
    if session_files:
        for f in session_files:
            reader = PdfReader(f)
            for page in reader.pages:
                session_text += page.extract_text() + "\n"

    st.markdown("<h1 style='text-align: center; color: #fee123; font-size: 2.5rem;'>DUCKS AI TREASURY</h1>", unsafe_allow_html=True)

    # METRICS
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("LEDGER", "SYNCED", "LIVE")
    with m2: st.metric("ENTRIES", len(df_ledger) if df_ledger is not None else 0)
    with m3: st.metric("KNOWLEDGE", len(perm_files), "FILES")
    with m4: st.metric("STATUS", "SECURE", "AUTH")

    tab1, tab2, tab3 = st.tabs(["💬 Financial Chat", "📊 Budget Analytics", "🧠 Knowledge Base"])

    with tab1:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if query := st.chat_input("How can I help you today, Treasurer?"):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)

            try:
                # Automatically pick the best available model
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(available_models[0])
                
                context = f"LEDGER:\n{df_ledger.to_string()}\n\nRULES:\n{perm_text}\n\nSESSION:\n{session_text}"
                full_prompt = f"System: You are the UO AI Club Treasurer Advisor. {context}\nUser: {query}"
                
                with st.spinner("Analyzing..."):
                    response = model.generate_content(full_prompt)
                    ai_resp = response.text
                
                with st.chat_message("assistant"):
                    st.markdown(ai_resp)
                st.session_state.messages.append({"role": "assistant", "content": ai_resp})
            except Exception as e:
                st.error(f"AI System Error: {e}")

    with tab2:
        st.subheader("Interactive Budget Overview")
        st.dataframe(df_ledger, use_container_width=True)
        if df_ledger is not None:
            num_cols = df_ledger.select_dtypes(include=['number']).columns
            if len(num_cols) > 0:
                fig = px.bar(df_ledger, x=df_ledger.columns[0], y=num_cols[0], template="plotly_dark", color_discrete_sequence=['#fee123'])
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("🏛️ Permanent Repository")
        if perm_files:
            for f in perm_files: st.write(f"✅ **{os.path.basename(f)}**")
        else: st.info("No files found in GitHub 'knowledge_base'.")

else:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=150)
        st.markdown("<h2 style='text-align: center; color: #fee123;'>TREASURY AUTHENTICATION</h2>", unsafe_allow_html=True)
        st.info("Enter Access Code in the sidebar.")
