import streamlit as st
import pandas as pd
import google.generativeai as genai
from PyPDF2 import PdfReader
import trafilatura

# --- 1. UI SETUP ---
st.set_page_config(page_title="AI Club Treasury Knowledge Hub", layout="wide", page_icon="🏦")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; margin-bottom: 10px; }
    [data-testid="stSidebar"] { background-color: #161b22; }
    </style>
    """, unsafe_allow_html=True)

# Google Sheet Details
SHEET_ID = "1xHaK_bcyCsQButBmceqd2-BippPWVVZYsUbwHlN0jEM"
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- 2. SIDEBAR & KNOWLEDGE SOURCES ---
with st.sidebar:
    st.title("🛡️ Treasury Admin")
    password = st.text_input("Treasurer Password", type="password")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.markdown("---")
    st.header("📚 Knowledge Base")
    
    # PDF Upload
    uploaded_docs = st.file_uploader("Upload Policy PDFs", type="pdf", accept_multiple_files=True)
    
    # WEBSITE Input
    website_url = st.text_input("Website URL to Study", placeholder="https://asuo.uoregon.edu/...")
    
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# Function to extract text from PDFs
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    return text

# Function to extract text from a Website
def get_web_text(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        # extract() removes the navigation/ads and returns clean text
        return trafilatura.extract(downloaded) or ""
    except Exception as e:
        return f"Error reading website: {e}"

# --- 3. MAIN LOGIC ---
if password == "AICLUBTREASURE" and api_key:
    genai.configure(api_key=api_key)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # A. Fetch Live Google Sheet Data
    try:
        df = pd.read_csv(GSHEET_URL)
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    except:
        df = None

    # B. Process Knowledge Base
    kb_content = ""
    
    # Add PDF content
    if uploaded_docs:
        kb_content += "\n--- DOCUMENT CONTENT ---\n" + get_pdf_text(uploaded_docs)
    
    # Add Website content
    if website_url:
        with st.spinner("Reading website..."):
            web_text = get_web_text(website_url)
            kb_content += "\n--- WEBSITE CONTENT ---\n" + web_text
            st.sidebar.success("Website loaded!")

    # C. Dashboard UI
    st.title("🏦 AI Club Treasury Hub")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ledger", "Live Sync Active" if df is not None else "Error")
    with col2:
        st.metric("Docs", len(uploaded_docs) if uploaded_docs else 0)
    with col3:
        st.metric("Website", "Linked" if website_url else "None")

    with st.expander("📂 View Live Spreadsheet"):
        if df is not None: st.dataframe(df)

    st.markdown("---")

    # D. Chat Interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_query := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
        
        system_prompt = f"""
        You are the UO AI Club Treasurer Advisor. Use the data provided below to answer.
        
        1. LIVE LEDGER:
        {df.to_string() if df is not None else "No ledger data."}
        
        2. KNOWLEDGE BASE (PDFs & WEBSITES):
        {kb_content[:15000]} # Gemini can handle more, but we'll start here for speed.
        
        3. HISTORY:
        {history}
        
        INSTRUCTIONS:
        - Prioritize rules found in the KNOWLEDGE BASE.
        - Use the LEDGER for math and budgets.
        - If a website or document provides a specific form link, give it to the user.
        """

        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model_id = available_models[0] if available_models else 'gemini-1.5-flash'
            model = genai.GenerativeModel(model_id)
            
            with st.spinner("Consulting Treasury knowledge..."):
                response = model.generate_content(f"{system_prompt}\n\nQUESTION: {user_query}")
                ai_response = response.text
                
            with st.chat_message("assistant"):
                st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
        except Exception as e:
            st.error(f"AI Error: {e}")

else:
    st.warning("Please sign in to the Treasury Admin sidebar.")
