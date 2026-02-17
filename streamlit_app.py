import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURATION & UI SETUP ---
st.set_page_config(page_title="AI Club Treasury Bot", layout="wide", page_icon="💰")

# Custom CSS for a professional Dark Mode/Finance look
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4255; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Your specific Google Sheet
SHEET_ID = "1xHaK_bcyCsQButBmceqd2-BippPWVVZYsUbwHlN0jEM"
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- 2. SIDEBAR (Setup & Live Connection) ---
with st.sidebar:
    st.title("🔑 Treasurer Access")
    password = st.text_input("Treasurer Password", type="password")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.markdown("---")
    if st.button("🗑️ Reset Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    st.success("✅ Google Sheet Linked")
    st.info("💡 **Pro-Tip:** Make sure Row 1 of your Google Sheet contains your Column Headers (Date, Amount, etc.) to avoid 'Unnamed' columns.")

# --- 3. HELPER FUNCTIONS ---
def load_live_data():
    try:
        # Fetch data from Google Sheet
        df = pd.read_csv(GSHEET_URL)
        # Clean up: Drop rows/columns that are totally empty
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        return df
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# --- 4. MAIN APP LOGIC ---
if password == "AICLUBTREASURE" and api_key:
    # Configure AI
    genai.configure(api_key=api_key)
    
    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # A. Fetch Live Data
    df = load_live_data()

    if df is not None:
        # B. Model Selector (Avoids the 404 Error)
        with st.sidebar:
            st.markdown("### 🤖 Select AI Brain")
            try:
                # Find only the models your key is authorized to use
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                selected_model_id = st.selectbox("Switch model if you get errors:", available_models, index=0)
                model = genai.GenerativeModel(selected_model_id)
            except Exception as model_err:
                st.error("Could not fetch models. Using default.")
                model = genai.GenerativeModel('gemini-1.5-flash')

        # C. Visual Dashboard Metrics
        st.title("💰 AI Club Treasury Assistant")
        st.markdown("---")
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Ledger Status", "Connected", "Live Sync")
        with m2:
            st.metric("Rows Tracked", len(df))
        with m3:
            st.metric("Active Year", "2025-2026")

        # Expander for Raw Data
        with st.expander("📂 Show Live Spreadsheet Data"):
            st.dataframe(df, use_container_width=True)

        st.markdown("---")

        # D. Chatbot Interface
        st.subheader("💬 Chat with your Ledger")
        
        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input Bar (Standard Chatbot style at bottom)
        if user_query := st.chat_input("Ask a question (e.g., 'Can we afford $200 for pizza?')"):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            # Generate AI Response
            try:
                # Include history context (last 5 messages)
                chat_history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
                
                full_prompt = f"""
                You are the AI Club Treasurer Assistant.
                LATEST LEDGER DATA:
                {df.to_string()}
                
                CONVERSATION HISTORY:
                {chat_history}
                
                INSTRUCTIONS:
                - Use the data above to answer financial questions.
                - If the user asks about affordability, calculate it based on the 'Approved' or 'Adjusted' budget columns.
                - Mention the ASUO 10-day prior approval rule for new requests.
                """
                
                with st.spinner("AI is analyzing your ledger..."):
                    response = model.generate_content(full_prompt)
                    ai_text = response.text
                
                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(ai_text)
                
                # Add to history
                st.session_state.messages.append({"role": "assistant", "content": ai_text})

            except Exception as e:
                st.error(f"AI Error: {e}")

else:
    st.warning("🔒 Please enter your Treasurer Password and Gemini API Key to begin.")
