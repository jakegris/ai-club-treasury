import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURATION & SETTINGS ---
st.set_page_config(page_title="AI Club Treasury AI", layout="wide", page_icon="💰")

# Your specific Google Sheet ID
SHEET_ID = "1xHaK_bcyCsQButBmceqd2-BippPWVVZYsUbwHlN0jEM"
GSHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# Professional Dark Theme CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 24px; color: #00d4ff; }
    .stChatFloatingInputContainer { background-color: #161b22; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("🔑 Treasurer Access")
    password = st.text_input("Treasurer Password", type="password")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    st.info("💡 **Live Sync Active:** The bot reads your Google Sheet every time you send a message.")

# --- 3. DATA LOADING FUNCTION ---
@st.cache_data(ttl=60) # Refreshes every 60 seconds
def load_live_data():
    try:
        df = pd.read_csv(GSHEET_CSV_URL)
        # Basic cleaning for Google Sheets quirks
        df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
        return df
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {e}")
        return None

# --- 4. MAIN INTERFACE ---
st.title("💰 AI Club Treasury Dashboard")

if password == "AICLUBTREASURE" and api_key:
    genai.configure(api_key=api_key)
    
    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Load the Data
    df = load_live_data()

    if df is not None:
        # Dashboard Summary Cards
        st.subheader("📊 Live Budget Metrics")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Ledger Status", "Connected", "Live")
        with m2:
            st.metric("Latest Update", pd.Timestamp.now().strftime('%H:%M:%S'))
        with m3:
            st.metric("Budget Year", "2025-2026")

        # Hidden Data View
        with st.expander("📂 View Raw Sheet Data"):
            st.dataframe(df, use_container_width=True)

        st.markdown("---")

        # --- CHATBOT SECTION ---
        # Display existing messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("Ask about a budget item or ASUO policy..."):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Prepare the AI Brain
            try:
                # We limit history to last 5 messages to keep it fast/cheap
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
                
                context_prompt = f"""
                You are the AI Club Treasurer Advisor. Use the following live data from Google Sheets to answer.
                
                DATA:
                {df.to_string()}
                
                HISTORY:
                {history}
                
                USER QUESTION:
                {prompt}
                
                INSTRUCTIONS:
                1. Look for 'Approved Budget' vs 'Adjusted Budget'. 
                2. If the user asks if they can afford something, check if the request is < the remaining balance.
                3. Always mention the ASUO 10-day prior approval rule for new purchases.
                4. Be conversational but concise.
                """

                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(context_prompt)
                
                # Add AI response to history
                with st.chat_message("assistant"):
                    st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

            except Exception as e:
                st.error(f"AI Error: {e}")

else:
    st.warning("🔒 Please enter your Password and Gemini API Key in the sidebar to access the treasury.")
