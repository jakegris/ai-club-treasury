import streamlit as st
import pandas as pd
import google.generativeai as genai
from PyPDF2 import PdfReader
import trafilatura
import plotly.express as px

# --- 1. PAGE CONFIG & MODERN THEMING ---
st.set_page_config(page_title="AI Club Treasury Hub", layout="wide", page_icon="🦆")

# Custom CSS for the "Cool" FinTech Look
st.markdown("""
    <style>
    /* Main App Background */
    .stApp {
        background: linear-gradient(135deg, #0a0c10 0%, #1a1d23 100%);
        color: #e0e0e0;
    }
    
    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(22, 27, 34, 0.7) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* Duck Green Accents */
    .stButton>button {
        background-color: #124734 !important; /* UO Green */
        color: #fee123 !important; /* UO Yellow */
        border-radius: 8px;
        border: none;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 15px #fee123;
    }

    /* Chat Bubble Styling */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        margin-bottom: 10px;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA SOURCE CONFIG ---
SHEET_ID = "1xHaK_bcyCsQButBmceqd2-BippPWVVZYsUbwHlN0jEM"
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- 3. FUNCTIONS ---
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    return text

def get_web_text(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        return trafilatura.extract(downloaded) or ""
    except:
        return ""

# --- 4. SIDEBAR ADMIN PANEL ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Oregon_Ducks_logo.svg/1200px-Oregon_Ducks_logo.svg.png", width=80)
    st.title("Admin Portal")
    password = st.text_input("Treasurer Code", type="password")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.markdown("---")
    st.subheader("📁 Brain Uploads")
    uploaded_docs = st.file_uploader("Policy PDFs", type="pdf", accept_multiple_files=True)
    website_url = st.text_input("Study URL", placeholder="https://...")
    
    if st.button("Clear Memory"):
        st.session_state.messages = []
        st.rerun()

# --- 5. APP LOGIC ---
if password == "AICLUBTREASURE" and api_key:
    genai.configure(api_key=api_key)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Fetch Data
    try:
        df = pd.read_csv(GSHEET_URL)
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    except:
        df = None

    # UI HEADER
    st.markdown("<h1 style='text-align: center; color: #fee123;'>🦆 AI Club Treasury Hub</h1>", unsafe_allow_html=True)
    
    # BIG METRICS ROW
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Ledger Status", "LIVE 🟢")
    with m2:
        st.metric("Total Line Items", len(df) if df is not None else 0)
    with m3:
        st.metric("Knowledge Base", "Active" if uploaded_docs or website_url else "Empty")
    with m4:
        st.metric("Role", "Treasurer")

    # TABS FOR COOLER NAVIGATION
    tab1, tab2, tab3 = st.tabs(["💬 Advisor Chat", "📊 Analytics & Ledger", "🧠 Knowledge Base"])

    # --- TAB 1: CHAT ---
    with tab1:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if query := st.chat_input("Ask anything..."):
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)

            # Knowledge processing
            kb_text = get_pdf_text(uploaded_docs) if uploaded_docs else ""
            if website_url: kb_text += f"\nWeb Info: {get_web_text(website_url)}"

            # AI Processing
            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(available_models[0])
                
                context = f"LEDGER:\n{df.to_string()}\n\nRULES:\n{kb_text[:10000]}"
                full_prompt = f"System: You are the UO AI Club Treasurer Bot. {context}\nUser: {query}"
                
                with st.spinner("Analyzing..."):
                    response = model.generate_content(full_prompt)
                    ai_resp = response.text
                
                with st.chat_message("assistant"):
                    st.markdown(ai_resp)
                st.session_state.messages.append({"role": "assistant", "content": ai_resp})
            except Exception as e:
                st.error(f"Error: {e}")

    # --- TAB 2: LEDGER ---
    with tab2:
        st.subheader("Current Spreadsheet Data")
        st.dataframe(df, use_container_width=True, height=400)
        
        # Add a quick visual if numbers exist
        if df is not None:
            try:
                # This tries to find a column with numbers to graph
                num_cols = df.select_dtypes(include=['number']).columns
                if len(num_cols) > 0:
                    st.subheader("Quick Spending Chart")
                    fig = px.bar(df, x=df.columns[1], y=num_cols[0], template="plotly_dark", color_discrete_sequence=['#fee123'])
                    st.plotly_chart(fig, use_container_width=True)
            except:
                st.info("No chartable data found. Add numerical columns to see graphs!")

    # --- TAB 3: BRAIN ---
    with tab3:
        st.subheader("Studied Documents")
        if uploaded_docs:
            for d in uploaded_docs:
                st.write(f"✅ PDF Loaded: {d.name}")
        if website_url:
            st.write(f"✅ Website Studied: {website_url}")
        if not (uploaded_docs or website_url):
            st.write("No external knowledge added yet. Use the sidebar to upload PDFs or URLs.")

else:
    st.warning("🔒 Please authenticate in the sidebar with your Treasurer Code.")
