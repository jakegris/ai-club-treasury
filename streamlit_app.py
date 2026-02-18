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
    /* Main Background: Oregon Green Gradient */
    .stApp {
        background: linear-gradient(135deg, #124734 0%, #072219 100%);
        color: #f0f0f0;
    }
    
    /* Sidebar: Frosted Glass Look */
    [data-testid="stSidebar"] {
        background-color: rgba(10, 40, 30, 0.8) !important;
        backdrop-filter: blur(12px);
        border-right: 2px solid #fee123;
    }

    /* Metric Cards: Premium FinTech Look */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border-left: 5px solid #fee123;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    
    /* Buttons: Fighting Ducks Yellow */
    .stButton>button {
        background-color: #fee123 !important;
        color: #124734 !important;
        border-radius: 12px;
        border: none;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        width: 100%;
        transition: 0.3s all;
    }
    .stButton>button:hover {
        background-color: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(254, 225, 35, 0.4);
    }

    /* Chat Bubbles: Custom UO Colors */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(254, 225, 35, 0.2) !important;
        border-radius: 15px !important;
    }
    
    /* Tab Headers */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent !important;
        border-radius: 4px 4px 0px 0px;
        color: white;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 3px solid #fee123 !important;
        color: #fee123 !important;
    }

    /* Input Box */
    .stChatInputContainer {
        padding-bottom: 20px;
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
        return "", [], f"Knowledge folder not found."
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
        except Exception as e:
            st.error(f"Error reading {file_path}: {e}")
    return combined_text, knowledge_files, "Success"

@st.cache_data(ttl=60)
def load_sheet_data(url):
    try:
        df = pd.read_csv(url)
        return df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    except: return None

# --- 3. SIDEBAR ---
with st.sidebar:
    # Oregon Logo
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=100)
    st.markdown("<h2 style='text-align: center; color: #fee123;'>Treasurer Admin</h2>", unsafe_allow_html=True)
    
    password = st.text_input("Access Code", type="password")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.markdown("---")
    session_files = st.file_uploader("📂 Temporary Docs", type="pdf", accept_multiple_files=True)
    
    if st.button("Reset Session"):
        st.session_state.messages = []
        st.rerun()

# --- 4. APP INTERFACE ---
if password == "AICLUBTREASURE" and api_key:
    genai.configure(api_key=api_key)
    if "messages" not in st.session_state: st.session_state.messages = []

    # Background Processing
    df_ledger = load_sheet_data(LEDGER_URL)
    perm_text, perm_files, debug_msg = load_permanent_knowledge()
    
    session_text = ""
    if session_files:
        for f in session_files:
            reader = PdfReader(f)
            for page in reader.pages:
                session_text += page.extract_text() + "\n"

    # MAIN HEADER
    st.markdown("<h1 style='text-align: center; color: #fee123; font-size: 3rem; margin-bottom: 0;'>DUCKS AI TREASURY</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #ffffff; opacity: 0.8;'>University of Oregon AI Club Financial Hub</p>", unsafe_allow_html=True)

    # METRICS ROW
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("LEDGER", "SYNCED", "LIVE")
    with m2: st.metric("ENTRIES", len(df_ledger) if df_ledger is not None else 0)
    with m3: st.metric("KNOWLEDGE", len(perm_files), "FILES")
    with m4: st.metric("STATUS", "SECURE", "AUTH")

    tab1, tab2, tab3 = st.tabs(["💬 Financial Chat", "📊 Budget Analytics", "🧠 Knowledge Base"])

    # --- TAB 1: CHAT ---
    with tab1:
        # Custom scrolling chat window
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if query := st.chat_input("How can I help you today, Treasurer?"):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)

            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(available_models[0])
                
                # Combine Ledger + KB + Session Docs
                combined_kb = f"PERMANENT:\n{perm_text}\n\nTEMPORARY:\n{session_text}"
                context = f"LEDGER:\n{df_ledger.to_string()}\n\nRULES:\n{combined_kb[:25000]}"
                full_prompt = f"System: You are the UO AI Club Treasurer Advisor. Use the UO Duck brand voice (helpful, focused, and professional). {context}\nUser: {query}"
                
                with st.spinner("Analyzing..."):
                    response = model.generate_content(full_prompt)
                    ai_resp = response.text
                
                with st.chat_message("assistant"):
                    st.markdown(ai_resp)
                st.session_state.messages.append({"role": "assistant", "content": ai_resp})
            except Exception as e:
                st.error(f"AI System Error: {e}")

    # --- TAB 2: ANALYTICS ---
    with tab2:
        st.subheader("Interactive Budget Overview")
        st.dataframe(df_ledger, use_container_width=True)
        
        if df_ledger is not None:
            num_cols = df_ledger.select_dtypes(include=['number']).columns
            if len(num_cols) > 0:
                # Custom Oregon Chart
                fig = px.bar(
                    df_ledger, 
                    x=df_ledger.columns[0], 
                    y=num_cols[0], 
                    template="plotly_dark", 
                    color_discrete_sequence=['#fee123'],
                    title="Spending by Category"
                )
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)

    # --- TAB 3: KNOWLEDGE ---
    with tab3:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("### 🏛️ Permanent Repository")
            if perm_files:
                for f in perm_files:
                    st.write(f"✅ **{os.path.basename(f)}**")
            else:
                st.info("No files found in GitHub 'knowledge_base'.")
        
        with col_right:
            st.markdown("### 📝 Session Documents")
            if session_files:
                for f in session_files:
                    st.write(f"📄 {f.name}")
            else:
                st.write("No temporary files uploaded.")

else:
    # Centered Login Box for better UI
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=150)
        st.markdown("<h2 style='text-align: center; color: #fee123;'>TREASURY AUTHENTICATION</h2>", unsafe_allow_html=True)
        st.info("Please enter credentials in the sidebar to enter the hub.")
